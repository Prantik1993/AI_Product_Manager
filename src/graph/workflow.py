"""
LangGraph workflow orchestration.

Key fixes from audit:
- Agents are module-level singletons (not recreated per request)
- No useless barrier node — LangGraph fan-in handles sync natively
- LangGraph checkpointer enabled for fault tolerance
- RAGQueryEngine created once and injected into DecisionAgent
"""

import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.graph.state import ProductManagerState
from src.agents.market import MarketAgent
from src.agents.tech import TechAgent
from src.agents.risk import RiskAgent
from src.agents.user_feedback import UserFeedbackAgent
from src.agents.decision import DecisionAgent
from src.rag.engine import RAGQueryEngine
from src.monitoring.logger import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------
# FIX: Module-level singletons — created ONCE per process, not per request
# DecisionAgent receives the shared RAG engine via dependency injection
# -----------------------------------------------------------------------
try:
    _rag_engine = RAGQueryEngine()
    logger.info("RAGQueryEngine singleton created")
except Exception as e:
    logger.warning(f"RAGQueryEngine failed to initialize: {e}. Decision will run without RAG.")
    _rag_engine = None

_market_agent = MarketAgent()
_tech_agent = TechAgent()
_risk_agent = RiskAgent()
_feedback_agent = UserFeedbackAgent()
_decision_agent = DecisionAgent(rag_engine=_rag_engine)


# -----------------------------------------------------------------------
# Node runner functions — thin wrappers around singleton agents
# -----------------------------------------------------------------------
async def run_market(state: ProductManagerState) -> dict:
    return await _market_agent.run(state)


async def run_tech(state: ProductManagerState) -> dict:
    return await _tech_agent.run(state)


async def run_risk(state: ProductManagerState) -> dict:
    return await _risk_agent.run(state)


async def run_user_feedback(state: ProductManagerState) -> dict:
    return await _feedback_agent.run(state)


async def run_decision(state: ProductManagerState) -> dict:
    return await _decision_agent.run(state)


# -----------------------------------------------------------------------
# Graph factory
# -----------------------------------------------------------------------
def create_graph():

    workflow = StateGraph(ProductManagerState)

    # Register nodes
    workflow.add_node("market_agent", run_market)
    workflow.add_node("tech_agent", run_tech)
    workflow.add_node("risk_agent", run_risk)
    workflow.add_node("user_feedback_agent", run_user_feedback)
    workflow.add_node("decision_agent", run_decision)

    # Fan-out: START → all 4 analysis agents in parallel
    workflow.add_edge(START, "market_agent")
    workflow.add_edge(START, "tech_agent")
    workflow.add_edge(START, "risk_agent")
    workflow.add_edge(START, "user_feedback_agent")

    # Fan-in: all 4 agents → decision (LangGraph waits for all automatically)
    workflow.add_edge("market_agent", "decision_agent")
    workflow.add_edge("tech_agent", "decision_agent")
    workflow.add_edge("risk_agent", "decision_agent")
    workflow.add_edge("user_feedback_agent", "decision_agent")

    workflow.add_edge("decision_agent", END)

    # FIX: Add checkpointer for fault tolerance
    checkpointer = MemorySaver()

    return workflow.compile(checkpointer=checkpointer)
