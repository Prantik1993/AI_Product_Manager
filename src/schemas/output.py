from pydantic import BaseModel, Field
from typing import List, Optional

class MarketReport(BaseModel):
    summary: str = Field(..., description="Executive summary of market findings")
    details: List[str] = Field(..., description="Key bullet points on trends and competitors")
    score: int = Field(..., description="Market viability score (1-10)")
    competitors: List[str] = Field(..., description="List of key competitor names")

class TechReport(BaseModel):
    summary: str = Field(..., description="Summary of technical assessment")
    details: List[str] = Field(..., description="Technical requirements and challenges")
    score: int = Field(..., description="Feasibility score (1-10)")
    feasibility: str = Field(..., description="High, Medium, or Low")

class RiskReport(BaseModel):
    summary: str = Field(..., description="Summary of risks")
    details: List[str] = Field(..., description="Detailed risk factors")
    score: int = Field(..., description="Risk severity score (1-10, where 10 is high risk)")
    legal_concerns: List[str] = Field(..., description="Specific legal or compliance issues")

class UserFeedbackReport(BaseModel):
    summary: str = Field(..., description="Summary of user sentiment")
    details: List[str] = Field(..., description="Key user opinions and quotes")
    score: int = Field(..., description="Sentiment score (1-10)")
    sentiment: str = Field(..., description="Positive, Negative, or Mixed")

class FinalDecision(BaseModel):
    decision: str = Field(..., description="GO, NO-GO, or PIVOT")
    reasoning: str = Field(..., description="Comprehensive explanation for the verdict")
    confidence_score: float = Field(..., description="Confidence level (0.0 to 1.0)")
    action_items: List[str] = Field(..., description="Recommended next steps")