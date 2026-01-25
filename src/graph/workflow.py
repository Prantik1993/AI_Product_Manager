from langgraph.graph import StateGraph, START, END
from src.graph.state import ProductManagerState

# Import Agent Runners
from src.agents.market import MarketAgent
from src.agents.tech import TechAgent
from src.agents.risk import RiskAgent
from src.agents.user_feedback import UserFeedbackAgent
from src.agents.decision import DecisionAgent

# --- Agent Runners ---
async def run_market_agent(state: ProductManagerState):
    agent = MarketAgent()
    return await agent.run(state)

async def run_tech_agent(state: ProductManagerState):
    agent = TechAgent()
    return await agent.run(state)

async def run_risk_agent(state: ProductManagerState):
    agent = RiskAgent()
    return await agent.run(state)

async def run_user_feedback_agent(state: ProductManagerState):
    agent = UserFeedbackAgent()
    return await agent.run(state)

async def run_decision_agent(state: ProductManagerState):
    agent = DecisionAgent()
    return await agent.run(state)

def create_graph():
    workflow = StateGraph(ProductManagerState)

    # 1. Add Nodes
    workflow.add_node("market_agent", run_market_agent)
    workflow.add_node("tech_agent", run_tech_agent)
    workflow.add_node("risk_agent", run_risk_agent)
    workflow.add_node("user_feedback_agent", run_user_feedback_agent)
    workflow.add_node("decision_agent", run_decision_agent)

    # 2. Start Parallel Execution
    # Kick off all 4 agents immediately
    workflow.add_edge(START, "market_agent")
    workflow.add_edge(START, "tech_agent")
    workflow.add_edge(START, "risk_agent")
    workflow.add_edge(START, "user_feedback_agent")

    # 3. Direct Fan-In
    # Point everyone to the Decision Agent.
    # The Decision Agent will handle the "waiting" logic internally.
    workflow.add_edge("market_agent", "decision_agent")
    workflow.add_edge("tech_agent", "decision_agent")
    workflow.add_edge("risk_agent", "decision_agent")
    workflow.add_edge("user_feedback_agent", "decision_agent")

    # 4. End
    workflow.add_edge("decision_agent", END)

    return workflow.compile()