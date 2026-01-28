"""Production-ready database layer with SQLAlchemy.

Provides async database operations with:
- Connection pooling
- Transaction management
- Type-safe queries
- Migration support
"""

import os
from typing import List, Optional, Dict
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.config.settings import settings
from src.monitoring.logger import get_logger
from src.core.exceptions import DatabaseError
from src.storage.models import Base, AnalysisReport, AgentExecutionLog

logger = get_logger(__name__)


class DatabaseManager:
    """Production database manager with connection pooling."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager.

        Args:
            database_url: Database URL (SQLite or Postgres)
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialize()

    def _get_database_url(self) -> str:
        """Get database URL from settings."""
        if settings.DATABASE_URL:
            return settings.DATABASE_URL

        # Default to SQLite
        db_path = settings.DB_PATH
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        return f"sqlite:///{db_path}"

    def _initialize(self):
        """Initialize database engine and session factory."""
        try:
            logger.info(f"Initializing database: {self.database_url}")

            # Create engine with appropriate settings
            if self.database_url.startswith("sqlite"):
                # SQLite-specific settings
                self.engine = create_engine(
                    self.database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                # PostgreSQL/MySQL settings
                self.engine = create_engine(
                    self.database_url,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_pre_ping=True,  # Verify connections
                )

            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )

            # Create tables
            Base.metadata.create_all(bind=self.engine)

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}", exc_info=True)
            raise DatabaseError(f"Database initialization failed: {str(e)}")

    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic cleanup.

        Yields:
            SQLAlchemy session

        Example:
            with db_manager.get_session() as session:
                report = session.query(AnalysisReport).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise DatabaseError(f"Database operation failed: {str(e)}")
        finally:
            session.close()

    def save_report(
        self,
        user_input: str,
        decision: str,
        full_state: dict,
        execution_time: Optional[float] = None,
        confidence_score: Optional[float] = None
    ) -> int:
        """Save analysis report to database.

        Args:
            user_input: User's product idea
            decision: Final decision (GO/NO-GO/PIVOT)
            full_state: Complete analysis state
            execution_time: Total execution time in seconds
            confidence_score: Decision confidence score

        Returns:
            Report ID
        """
        try:
            with self.get_session() as session:
                report = AnalysisReport(
                    user_input=user_input,
                    decision=decision,
                    confidence_score=confidence_score,
                    market_analysis=full_state.get("market_report"),
                    tech_analysis=full_state.get("tech_report"),
                    risk_analysis=full_state.get("risk_report"),
                    user_feedback_analysis=full_state.get("user_feedback_report"),
                    full_report=full_state,
                    execution_time_seconds=execution_time,
                    model_name=settings.MODEL_NAME,
                )
                session.add(report)
                session.flush()  # Get ID before commit
                report_id = report.id

            logger.info(
                f"Report saved",
                extra={
                    "extra_fields": {
                        "report_id": report_id,
                        "decision": decision,
                        "user_input": user_input[:50],
                    }
                },
            )
            return report_id

        except Exception as e:
            logger.error(f"Failed to save report: {e}", exc_info=True)
            raise DatabaseError(f"Failed to save report: {str(e)}")

    def get_reports(
        self,
        limit: int = 100,
        offset: int = 0,
        decision_filter: Optional[str] = None
    ) -> List[AnalysisReport]:
        """Get analysis reports with optional filtering.

        Args:
            limit: Maximum number of reports to return
            offset: Number of reports to skip
            decision_filter: Filter by decision type (GO/NO-GO/PIVOT)

        Returns:
            List of AnalysisReport objects
        """
        try:
            with self.get_session() as session:
                query = session.query(AnalysisReport).order_by(
                    desc(AnalysisReport.timestamp)
                )

                if decision_filter:
                    query = query.filter(
                        AnalysisReport.decision == decision_filter
                    )

                reports = query.limit(limit).offset(offset).all()

            logger.info(
                f"Retrieved {len(reports)} reports",
                extra={
                    "extra_fields": {
                        "limit": limit,
                        "offset": offset,
                        "filter": decision_filter,
                    }
                },
            )
            return reports

        except Exception as e:
            logger.error(f"Failed to get reports: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get reports: {str(e)}")

    def get_report_by_id(self, report_id: int) -> Optional[AnalysisReport]:
        """Get a specific report by ID.

        Args:
            report_id: Report ID

        Returns:
            AnalysisReport or None if not found
        """
        try:
            with self.get_session() as session:
                report = session.query(AnalysisReport).filter(
                    AnalysisReport.id == report_id
                ).first()

            return report

        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}", exc_info=True)
            raise DatabaseError(f"Failed to get report: {str(e)}")

    def log_agent_execution(
        self,
        agent_name: str,
        status: str,
        execution_time: Optional[float] = None,
        error_message: Optional[str] = None,
        report_id: Optional[int] = None
    ):
        """Log agent execution for monitoring.

        Args:
            agent_name: Name of the agent
            status: Execution status (success/failed/timeout)
            execution_time: Execution time in seconds
            error_message: Error message if failed
            report_id: Associated report ID
        """
        try:
            with self.get_session() as session:
                log = AgentExecutionLog(
                    agent_name=agent_name,
                    status=status,
                    execution_time_seconds=execution_time,
                    error_message=error_message,
                    report_id=report_id,
                )
                session.add(log)

            logger.debug(
                f"Agent execution logged: {agent_name} - {status}",
                extra={
                    "extra_fields": {
                        "agent": agent_name,
                        "status": status,
                        "execution_time": execution_time,
                    }
                },
            )

        except Exception as e:
            logger.error(f"Failed to log agent execution: {e}", exc_info=True)
            # Don't raise - logging failures shouldn't break the app

    def get_statistics(self) -> Dict:
        """Get database statistics.

        Returns:
            Dictionary with statistics
        """
        try:
            with self.get_session() as session:
                total_reports = session.query(AnalysisReport).count()
                go_count = session.query(AnalysisReport).filter(
                    AnalysisReport.decision == "GO"
                ).count()
                no_go_count = session.query(AnalysisReport).filter(
                    AnalysisReport.decision == "NO-GO"
                ).count()
                pivot_count = session.query(AnalysisReport).filter(
                    AnalysisReport.decision == "PIVOT"
                ).count()

            return {
                "total_reports": total_reports,
                "decisions": {
                    "GO": go_count,
                    "NO-GO": no_go_count,
                    "PIVOT": pivot_count,
                },
                "database_url": self.database_url.split("@")[-1],  # Hide credentials
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {"error": str(e)}


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create global database manager instance.

    Returns:
        DatabaseManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
