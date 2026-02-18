"""LangGraph state definition for the Product Manager workflow."""

from typing import TypedDict, Optional, Dict, Any


class ProductManagerState(TypedDict):
    """
    Shared state passed between all nodes in the LangGraph workflow.
    All agent outputs use consistent key names that match database field names.
    """
    user_input: str

    # Analysis outputs — keys match exactly what agents return AND what database stores
    market_analysis: Optional[str]       # JSON string from MarketAgent
    tech_analysis: Optional[str]         # JSON string from TechAgent
    risk_analysis: Optional[str]         # JSON string from RiskAgent
    user_feedback_analysis: Optional[str]  # JSON string from UserFeedbackAgent

    # Final output
    final_verdict: Optional[Dict[str, Any]]
