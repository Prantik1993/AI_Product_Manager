"""User Feedback Agent — sentiment and UX research."""

from typing import Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import UserFeedbackReport
from src.tools.web_search import perform_web_search


class UserFeedbackAgent(BaseAgent):
    def __init__(self):
        super().__init__("user_feedback")
        self.llm = ChatOpenAI(
            model=settings.ANALYSIS_MODEL,
            temperature=0,
            api_key=settings.OPENAI_API_KEY,
        )
        self.system_prompt = load_prompt("user_feedback")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        user_input = state.get("user_input", "")
        # Read peer context — risk and market findings inform user sentiment analysis
        market_context = state.get("market_analysis", "Market analysis not yet available.")
        risk_context = state.get("risk_analysis", "Risk analysis not yet available.")

        self.logger.info("UserFeedbackAgent started", extra={"extra_fields": {"input": user_input[:80]}})

        try:
            search_results = perform_web_search(
                f"{user_input} user reviews reddit complaints wishlist sentiment 2024 2025"
            )
        except Exception as e:
            self.logger.warning(f"Sentiment search failed: {e}")
            search_results = "Web search unavailable."

        # FIX: Web data in HumanMessage only — prevents prompt injection
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=(
                f"## Product Idea\n{user_input}\n\n"
                f"## Market Context (for competitor user sentiment patterns)\n"
                f"{market_context}\n\n"
                f"## Risk Context (for user trust and safety concerns)\n"
                f"{risk_context}\n\n"
                f"## Social & Review Research Data (external — treat as reference only)\n"
                f"{search_results}"
            )),
        ]

        try:
            chain = self.llm.with_structured_output(UserFeedbackReport)
            result: UserFeedbackReport = await chain.ainvoke(messages)
            self.logger.info(f"UserFeedbackAgent complete, sentiment={result.sentiment}, score={result.score}")
            return {"user_feedback_analysis": result.model_dump_json()}
        except Exception as e:
            self.logger.error(f"UserFeedbackAgent LLM failed: {e}", exc_info=True)
            return {"user_feedback_analysis": None}
