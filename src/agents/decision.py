from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import FinalDecision
from src.rag.engine import RAGQueryEngine  # <--- NEW: The Company Brain

class DecisionAgent(BaseAgent):
    def __init__(self):
        super().__init__("decision")
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME, 
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt_template = load_prompt("decision")
        
        # Initialize RAG Engine
        self.rag = RAGQueryEngine()

    def _get_agent_output(self, state: Dict[str, Any], key: str, default: str = "Data unavailable") -> str:
        data = state.get(key)
        return data if data else default

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # --- 🛡️ BARRIER CHECK ---
        required_keys = ["market_analysis", "tech_analysis", "risk_analysis", "user_feedback_analysis"]
        if not all(state.get(k) for k in required_keys):
            return {}

        self.log("All reports received. Consulting Company Strategy (RAG)...")
        
        # 1. RETRIEVE COMPANY KNOWLEDGE
        user_input = state.get('user_input')
        # We ask the DB: "What are our rules about [user idea]?"
        company_context = self.rag.query(user_input)
        
        self.log(f"Retrieved Company Strategy: {len(company_context)} chars")

        # 2. SYNTHESIZE EVERYTHING
        # We inject 'company_context' at the very top so it takes priority
        context = (
            f"User Product Request: {user_input}\n\n"
            f"=== 🏢 INTERNAL COMPANY STRATEGY (STRICTLY FOLLOW) ===\n{company_context}\n"
            f"======================================================\n\n"
            f"--- Market Research ---\n{self._get_agent_output(state, 'market_analysis')}\n\n"
            f"--- Tech Feasibility ---\n{self._get_agent_output(state, 'tech_analysis')}\n\n"
            f"--- Risk Analysis ---\n{self._get_agent_output(state, 'risk_analysis')}\n\n"
            f"--- User Feedback ---\n{self._get_agent_output(state, 'user_feedback_analysis')}\n"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_template),
            ("user", "Here is the data. Compare the Idea against our Company Strategy FIRST. \n\n{context}")
        ])
        
        chain = prompt | self.llm.with_structured_output(FinalDecision)
        
        try:
            result = await chain.ainvoke({"context": context})
            self.log(f"Decision: {result.decision}")
            return {"final_verdict": result.model_dump()}
            
        except Exception as e:
            self.log_error(f"Synthesis failed: {e}")
            return {
                "final_verdict": {
                    "decision": "ERROR",
                    "reasoning": f"System failure: {str(e)}",
                    "action_items": ["Check logs", "Retry"]
                }
            }