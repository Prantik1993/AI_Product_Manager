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

# NEW: Synchronization barrier node
async def wait_for_all_agents(state: ProductManagerState):
    """
    This node acts as a synchronization barrier.
    It only proceeds once all agent reports are present.
    """
    required_keys = ["market_analysis", "tech_analysis", "risk_analysis", "user_feedback_analysis"]
    
    # Check if all reports are present
    if all(state.get(k) for k in required_keys):
        # All reports ready, pass through unchanged
        return state
    else:
        # This shouldn't happen with proper graph structure, but safety check
        return state

def create_graph():
    workflow = StateGraph(ProductManagerState)

    # 1. Add Nodes
    workflow.add_node("market_agent", run_market_agent)
    workflow.add_node("tech_agent", run_tech_agent)
    workflow.add_node("risk_agent", run_risk_agent)
    workflow.add_node("user_feedback_agent", run_user_feedback_agent)
    workflow.add_node("barrier", wait_for_all_agents)  # NEW: Synchronization node
    workflow.add_node("decision_agent", run_decision_agent)

    # 2. Start Parallel Execution
    workflow.add_edge(START, "market_agent")
    workflow.add_edge(START, "tech_agent")
    workflow.add_edge(START, "risk_agent")
    workflow.add_edge(START, "user_feedback_agent")

    # 3. All agents converge to barrier
    workflow.add_edge("market_agent", "barrier")
    workflow.add_edge("tech_agent", "barrier")
    workflow.add_edge("risk_agent", "barrier")
    workflow.add_edge("user_feedback_agent", "barrier")

    # 4. Barrier to Decision Agent (executes only once)
    workflow.add_edge("barrier", "decision_agent")

    # 5. End
    workflow.add_edge("decision_agent", END)

    return workflow.compile()