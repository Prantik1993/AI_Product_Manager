"""SQLAlchemy ORM models.

FIX: Import declarative_base from sqlalchemy.orm (not deprecated ext.declarative).
FIX: Removed CacheEntry model — nobody used it and it created a confusing dead table.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.orm import declarative_base  # FIX: correct import for SQLAlchemy 2.x
from sqlalchemy.sql import func

Base = declarative_base()


class AnalysisReport(Base):
    """Stores every product analysis run."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_input = Column(Text, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False, index=True)
    decision = Column(String(20), nullable=False, index=True)   # GO / NO-GO / PIVOT / ERROR
    confidence_score = Column(Float, nullable=True)

    # FIX: Field names match EXACTLY what agents return in state dict
    # market_analysis, tech_analysis, risk_analysis, user_feedback_analysis
    market_analysis = Column(JSON, nullable=True)
    tech_analysis = Column(JSON, nullable=True)
    risk_analysis = Column(JSON, nullable=True)
    user_feedback_analysis = Column(JSON, nullable=True)

    # Full workflow state snapshot
    full_report = Column(JSON, nullable=True)

    # Metadata
    execution_time_seconds = Column(Float, nullable=True)
    model_name = Column(String(50), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_input": self.user_input,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "decision": self.decision,
            "confidence_score": self.confidence_score,
            "market_analysis": self.market_analysis,
            "tech_analysis": self.tech_analysis,
            "risk_analysis": self.risk_analysis,
            "user_feedback_analysis": self.user_feedback_analysis,
            "full_report": self.full_report,
            "execution_time_seconds": self.execution_time_seconds,
            "model_name": self.model_name,
        }

    def __repr__(self) -> str:
        return f"<AnalysisReport(id={self.id}, decision={self.decision}, ts={self.timestamp})>"


class AgentExecutionLog(Base):
    """Per-agent execution log for monitoring and debugging."""

    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, nullable=True, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)   # success / failed / timeout
    execution_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<AgentExecutionLog(agent={self.agent_name}, status={self.status})>"
