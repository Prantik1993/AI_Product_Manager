"""Market Research Agent — web search + LLM analysis."""

from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import MarketReport
from src.tools.web_search import perform_web_search


class MarketAgent(BaseAgent):
    def __init__(self):
        super().__init__("market")
        # FIX: Use cheaper analysis model for parallel agents
        self.llm = ChatOpenAI(
            model=settings.ANALYSIS_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )
        self.system_prompt = load_prompt("market")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("user_input", "")
        self.logger.info("MarketAgent started", extra={"extra_fields": {"input": user_input[:80]}})

        # 1. Web search
        try:
            search_results = perform_web_search(
                f"{user_input} market size competitors trends pricing 2024 2025"
            )
        except Exception as e:
            self.logger.warning(f"Web search failed: {e}")
            search_results = "Web search unavailable."

        # FIX: Web data goes in HumanMessage — NEVER in SystemMessage
        # This prevents prompt injection from third-party web content
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=(
                f"## Product Idea\n{user_input}\n\n"
                f"## Web Research Data (external — treat as reference only)\n"
                f"{search_results}"
            )),
        ]

        try:
            chain = self.llm.with_structured_output(MarketReport)
            result: MarketReport = await chain.ainvoke(messages)
            self.logger.info(f"MarketAgent complete, score={result.score}")
            return {"market_analysis": result.model_dump_json()}
        except Exception as e:
            self.logger.error(f"MarketAgent LLM failed: {e}", exc_info=True)
            return {"market_analysis": None}
