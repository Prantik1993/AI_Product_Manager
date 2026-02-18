"""Pydantic v2 output schemas for all agents."""

from pydantic import BaseModel, Field
from typing import List


class MarketReport(BaseModel):
    summary: str = Field(..., description="Executive summary of market findings")
    key_findings: List[str] = Field(..., description="Specific data points on trends and competitors")
    competitors: List[str] = Field(..., description="Direct and indirect competitor names")
    market_size_estimate: str = Field(..., description="Estimated market size and growth rate")
    score: int = Field(..., ge=1, le=10, description="Market viability score 1-10")


class TechReport(BaseModel):
    summary: str = Field(..., description="Technical feasibility summary")
    required_stack: List[str] = Field(..., description="Required technologies and services")
    challenges: List[str] = Field(..., description="Key technical challenges")
    feasibility: str = Field(..., description="HIGH, MEDIUM, or LOW")
    score: int = Field(..., ge=1, le=10, description="Feasibility score 1-10")


class RiskReport(BaseModel):
    summary: str = Field(..., description="Risk overview")
    legal_concerns: List[str] = Field(..., description="Legal, regulatory, and compliance issues")
    ethical_risks: List[str] = Field(..., description="Ethical and reputational risks")
    mitigation_strategies: List[str] = Field(..., description="How to mitigate top risks")
    score: int = Field(..., ge=1, le=10, description="Risk severity 1-10 (10=highest risk)")


class UserFeedbackReport(BaseModel):
    summary: str = Field(..., description="User sentiment summary")
    pain_points: List[str] = Field(..., description="Validated user pain points from research")
    positive_signals: List[str] = Field(..., description="Positive user signals and desires")
    sentiment: str = Field(..., description="POSITIVE, NEGATIVE, or MIXED")
    score: int = Field(..., ge=1, le=10, description="User appetite score 1-10")


class FinalDecision(BaseModel):
    decision: str = Field(..., description="GO, NO-GO, or PIVOT")
    reasoning: str = Field(..., description="Full explanation citing strategy + agent reports")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence 0.0-1.0")
    action_items: List[str] = Field(..., description="Concrete next steps")
    strategy_conflicts: List[str] = Field(
        default_factory=list,
        description="Specific company strategy rules that were violated, if any"
    )
