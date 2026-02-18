"""
Single database layer — replaces both the old db_manager.py and database.py.

FIX: Removed split-brain dual DB layer (db_manager.py is deleted).
FIX: save_report() field names now match EXACTLY what agents return:
     state["market_analysis"], state["tech_analysis"], etc.
"""

import os
import json
import time
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Dict

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.core.exceptions import DatabaseError
from src.storage.models import Base, AnalysisReport, AgentExecutionLog

logger = get_logger(__name__)


class DatabaseManager:
    """Thread-safe database manager with connection pooling."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or self._resolve_url()
        self._init_engine()

    def _resolve_url(self) -> str:
        if settings.DATABASE_URL:
            return settings.DATABASE_URL
        db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data", "app.db"
        )
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"

    def _init_engine(self):
        try:
            if self.database_url.startswith("sqlite"):
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self.engine = create_engine(
                    self.database_url,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True,
                )

            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info(f"Database initialized: {self.database_url.split('@')[-1]}")

        except Exception as e:
            raise DatabaseError(f"Database initialization failed: {e}")

    @contextmanager
    def get_session(self):
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"DB session error: {e}", exc_info=True)
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            session.close()

    def save_report(
        self,
        user_input: str,
        decision: str,
        full_state: dict,
        execution_time: Optional[float] = None,
    ) -> int:
        """
        Save a complete analysis report to the database.

        FIX: Field names use EXACT state keys from agents:
             full_state["market_analysis"], full_state["tech_analysis"], etc.
             Previously was using wrong keys like "market_report" — saving None every time.
        """
        verdict = full_state.get("final_verdict", {})
        confidence = verdict.get("confidence_score") if isinstance(verdict, dict) else None

        # Parse JSON strings from agents back to dicts for JSON column storage
        def _parse(key: str):
            raw = full_state.get(key)
            if not raw:
                return None
            if isinstance(raw, dict):
                return raw
            try:
                return json.loads(raw)
            except Exception:
                return {"raw": str(raw)}

        try:
            with self.get_session() as session:
                report = AnalysisReport(
                    user_input=user_input,
                    decision=decision,
                    confidence_score=confidence,
                    # FIX: Correct field names matching agent state keys
                    market_analysis=_parse("market_analysis"),
                    tech_analysis=_parse("tech_analysis"),
                    risk_analysis=_parse("risk_analysis"),
                    user_feedback_analysis=_parse("user_feedback_analysis"),
                    full_report=full_state,
                    execution_time_seconds=execution_time,
                    model_name=settings.MODEL_NAME,
                )
                session.add(report)
                session.flush()
                report_id = report.id

            logger.info(
                "Report saved",
                extra={"extra_fields": {"report_id": report_id, "decision": decision}}
            )
            return report_id

        except Exception as e:
            logger.error(f"Failed to save report: {e}", exc_info=True)
            raise DatabaseError(f"Failed to save report: {e}")

    def get_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_filter: Optional[str] = None,
        search_term: Optional[str] = None,
    ) -> List[AnalysisReport]:
        """Get reports with optional filtering and search."""
        try:
            with self.get_session() as session:
                query = session.query(AnalysisReport).order_by(desc(AnalysisReport.timestamp))
                if decision_filter and decision_filter != "All":
                    query = query.filter(AnalysisReport.decision == decision_filter)
                if search_term:
                    query = query.filter(AnalysisReport.user_input.ilike(f"%{search_term}%"))
                reports = query.limit(limit).offset(offset).all()
                # Detach from session so they can be used outside context
                session.expunge_all()
            return reports
        except Exception as e:
            logger.error(f"Failed to get reports: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get reports: {e}")

    def get_statistics(self) -> Dict:
        """Return aggregate statistics for the stats dashboard."""
        try:
            with self.get_session() as session:
                total = session.query(AnalysisReport).count()
                go = session.query(AnalysisReport).filter(AnalysisReport.decision == "GO").count()
                no_go = session.query(AnalysisReport).filter(AnalysisReport.decision == "NO-GO").count()
                pivot = session.query(AnalysisReport).filter(AnalysisReport.decision == "PIVOT").count()
                error = session.query(AnalysisReport).filter(AnalysisReport.decision == "ERROR").count()

            return {
                "total_reports": total,
                "decisions": {"GO": go, "NO-GO": no_go, "PIVOT": pivot, "ERROR": error},
                "database_url": self.database_url.split("@")[-1],
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e), "total_reports": 0, "decisions": {}}

    def log_agent_execution(
        self,
        agent_name: str,
        status: str,
        execution_time: Optional[float] = None,
        error_message: Optional[str] = None,
        report_id: Optional[int] = None,
    ):
        """Log individual agent execution — non-critical, never raises."""
        try:
            with self.get_session() as session:
                session.add(AgentExecutionLog(
                    report_id=report_id,
                    agent_name=agent_name,
                    status=status,
                    execution_time_seconds=execution_time,
                    error_message=error_message,
                ))
        except Exception as e:
            logger.warning(f"Agent log write failed (non-critical): {e}")


# --- Module-level singleton ---
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create the global DatabaseManager singleton."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
