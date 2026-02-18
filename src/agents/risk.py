"""Risk Analysis Agent — legal, ethical, compliance assessment."""

from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import RiskReport
from src.tools.web_search import perform_web_search


class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__("risk")
        self.llm = ChatOpenAI(
            model=settings.ANALYSIS_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )
        self.system_prompt = load_prompt("risk")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("user_input", "")
        # Read peer market context — competitors' legal issues are relevant
        market_context = state.get("market_analysis", "Market analysis not yet available.")

        self.logger.info("RiskAgent started", extra={"extra_fields": {"input": user_input[:80]}})

        try:
            search_results = perform_web_search(
                f"{user_input} legal risks lawsuit regulation compliance GDPR 2024 2025"
            )
        except Exception as e:
            self.logger.warning(f"Risk search failed: {e}")
            search_results = "Web search unavailable."

        # FIX: Web data in HumanMessage only — prevents prompt injection
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=(
                f"## Product Idea\n{user_input}\n\n"
                f"## Market Context (from MarketAgent — use for competitor risk patterns)\n"
                f"{market_context}\n\n"
                f"## Legal & News Research Data (external — treat as reference only)\n"
                f"{search_results}"
            )),
        ]

        try:
            chain = self.llm.with_structured_output(RiskReport)
            result: RiskReport = await chain.ainvoke(messages)
            self.logger.info(f"RiskAgent complete, score={result.score}")
            return {"risk_analysis": result.model_dump_json()}
        except Exception as e:
            self.logger.error(f"RiskAgent LLM failed: {e}", exc_info=True)
            return {"risk_analysis": None}
