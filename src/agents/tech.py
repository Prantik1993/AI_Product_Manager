"""Technical Feasibility Agent — reads market context from peer agents."""

from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import TechReport


class TechAgent(BaseAgent):
    def __init__(self):
        super().__init__("tech")
        self.llm = ChatOpenAI(
            model=settings.ANALYSIS_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )
        self.system_prompt = load_prompt("tech")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("user_input", "")
        # FIX: Read peer agent context — real multi-agent information sharing
        market_context = state.get("market_analysis", "Market analysis not yet available.")

        self.logger.info("TechAgent started", extra={"extra_fields": {"input": user_input[:80]}})

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=(
                f"## Product Idea\n{user_input}\n\n"
                f"## Market Research Context (from MarketAgent)\n"
                f"{market_context}\n\n"
                f"Use the market context to inform your technical assessment "
                f"(e.g., if competitors use specific tech stacks, factor that in)."
            )),
        ]

        try:
            chain = self.llm.with_structured_output(TechReport)
            result: TechReport = await chain.ainvoke(messages)
            self.logger.info(f"TechAgent complete, feasibility={result.feasibility}, score={result.score}")
            return {"tech_analysis": result.model_dump_json()}
        except Exception as e:
            self.logger.error(f"TechAgent LLM failed: {e}", exc_info=True)
            return {"tech_analysis": None}
