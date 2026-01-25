from typing import TypedDict, Optional, Dict, Any

class ProductManagerState(TypedDict):
    """
    State definition for the Product Manager Graph.
    """
    user_input: str
    
    # Analysis Reports (Stored as JSON strings)
    market_analysis: Optional[str]
    tech_analysis: Optional[str]
    risk_analysis: Optional[str]
    user_feedback_analysis: Optional[str]
    
    # Final Output
    final_verdict: Optional[Dict[str, Any]]