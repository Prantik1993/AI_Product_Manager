"""Decision Agent — synthesizes all reports + RAG company strategy → GO/NO-GO/PIVOT."""

from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import FinalDecision
from src.rag.engine import RAGQueryEngine


class DecisionAgent(BaseAgent):
    def __init__(self, rag_engine: RAGQueryEngine):
        super().__init__("decision")
        # FIX: Use the smarter model for the critical decision step
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )
        self.system_prompt = load_prompt("decision")
        # FIX: RAG engine injected — not created inside __init__ on every request
        self.rag = rag_engine

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("user_input", "")
        self.logger.info("DecisionAgent started")

        # --- Guard: require all agent reports ---
        required = ["market_analysis", "tech_analysis", "risk_analysis", "user_feedback_analysis"]
        missing = [k for k in required if not state.get(k)]
        if missing:
            self.logger.error(f"Missing reports: {missing}")
            return {
                "final_verdict": {
                    "decision": "ERROR",
                    "reasoning": f"Cannot decide — missing reports from: {', '.join(missing)}",
                    "confidence_score": 0.0,
                    "action_items": ["Check agent logs", "Verify API keys", "Retry analysis"],
                    "strategy_conflicts": [],
                }
            }

        # --- Retrieve company strategy via RAG ---
        company_strategy = "Company strategy unavailable — RAG offline."
        if self.rag:
            try:
                company_strategy = self.rag.query(user_input)
                self.logger.info(f"RAG returned {len(company_strategy)} chars of strategy context")
            except Exception as e:
                self.logger.warning(f"RAG query failed: {e}")

        # --- Build messages — all context in HumanMessage ---
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=(
                f"## Product Idea\n{user_input}\n\n"
                f"## COMPANY STRATEGY (HIGHEST PRIORITY — NON-NEGOTIABLE)\n"
                f"{company_strategy}\n\n"
                f"## Market Research Report\n{state.get('market_analysis')}\n\n"
                f"## Technical Feasibility Report\n{state.get('tech_analysis')}\n\n"
                f"## Risk Assessment Report\n{state.get('risk_analysis')}\n\n"
                f"## User Feedback Report\n{state.get('user_feedback_analysis')}\n\n"
                f"Compare the product idea against the company strategy FIRST. "
                f"List every strategy rule violated in `strategy_conflicts`. "
                f"Only consider market/tech/user data if strategy is cleared."
            )),
        ]

        try:
            chain = self.llm.with_structured_output(FinalDecision)
            result: FinalDecision = await chain.ainvoke(messages)
            self.logger.info(
                f"DecisionAgent complete",
                extra={"extra_fields": {
                    "decision": result.decision,
                    "confidence": result.confidence_score,
                    "strategy_conflicts": result.strategy_conflicts,
                }}
            )
            return {"final_verdict": result.model_dump()}
        except Exception as e:
            self.logger.error(f"DecisionAgent LLM failed: {e}", exc_info=True)
            return {
                "final_verdict": {
                    "decision": "ERROR",
                    "reasoning": f"Decision synthesis failed: {str(e)}",
                    "confidence_score": 0.0,
                    "action_items": ["Check OpenAI API key", "Review logs", "Retry"],
                    "strategy_conflicts": [],
                }
            }
