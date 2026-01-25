from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
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
            model=settings.MODEL_NAME, 
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt_template = load_prompt("user_feedback")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Analyzing user sentiment...")
        user_input = state.get("user_input", "")
        
        # 1. Search Social Sentiment
        self.log(f"Searching sentiment for: {user_input}...")
        search_query = f"{user_input} user reviews reddit twitter complaints"
        # Optional: Use 'basic' depth here to save credits if configured in settings
        search_results = perform_web_search(search_query)
        
        # 2. Inject
        system_prompt = (
            f"{self.prompt_template}\n\n"
            f"--- LIVE SOCIAL DATA ---\n{search_results}\n"
            f"------------------------"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        chain = prompt | self.llm.with_structured_output(UserFeedbackReport)
        
        try:
            result = await chain.ainvoke({"input": user_input})
            return {"user_feedback_analysis": result.model_dump_json()}
        except Exception as e:
            self.log_error(f"User feedback analysis failed: {e}")
            return {"user_feedback_analysis": "Error in sentiment analysis."}