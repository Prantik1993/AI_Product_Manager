"""SQLAlchemy database models.

Provides ORM models for database operations with:
- Type-safe model definitions
- Relationship mapping
- Automatic timestamps
- JSON field support
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class AnalysisReport(Base):
    """Model for storing product analysis reports."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_input = Column(Text, nullable=False, index=True)
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
        index=True
    )
    decision = Column(String(20), nullable=False, index=True)  # GO/NO-GO/PIVOT
    confidence_score = Column(Float, nullable=True)

    # Agent outputs
    market_analysis = Column(JSON, nullable=True)
    tech_analysis = Column(JSON, nullable=True)
    risk_analysis = Column(JSON, nullable=True)
    user_feedback_analysis = Column(JSON, nullable=True)

    # Full state for backwards compatibility
    full_report = Column(JSON, nullable=True)

    # Metadata
    execution_time_seconds = Column(Float, nullable=True)
    model_name = Column(String(50), nullable=True)

    def __repr__(self):
        return (
            f"<AnalysisReport(id={self.id}, "
            f"decision={self.decision}, "
            f"timestamp={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
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


class AgentExecutionLog(Base):
    """Model for logging individual agent executions."""

    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, nullable=True, index=True)  # FK to reports
    agent_name = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False)  # success/failed/timeout
    execution_time_seconds = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<AgentExecutionLog(id={self.id}, "
            f"agent={self.agent_name}, "
            f"status={self.status})>"
        )


class CacheEntry(Base):
    """Model for persistent cache storage."""

    __tablename__ = "cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<CacheEntry(key={self.cache_key}, expires={self.expires_at})>"

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
