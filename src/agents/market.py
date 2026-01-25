from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Enterprise Imports
from src.agents.base import BaseAgent
from src.config.settings import settings       # <--- NEW: Type-safe settings
from src.prompts.manager import load_prompt    # <--- NEW: Cached prompt loader
from src.schemas.output import MarketReport
from src.tools.web_search import perform_web_search

class MarketAgent(BaseAgent):
    def __init__(self):
        super().__init__("market")
        # Load LLM with settings (Centralized Config)
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME, # e.g. "gpt-4-turbo" defined in settings
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        # Load Prompt (Centralized Manager)
        self.prompt_template = load_prompt("market")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Starting Market Analysis...")
        user_input = state.get("user_input", "")
        
        # 1. Real-Time Search
        self.log(f"Searching web for: {user_input}...")
        try:
            search_query = f"{user_input} market trends competitors price"
            # Use 'advanced' for deep market research
            search_results = perform_web_search(search_query)
        except Exception as e:
            self.log_error(f"Search failed: {e}")
            search_results = "Search unavailable."

        # 2. Context Injection
        system_prompt = (
            f"{self.prompt_template}\n\n"
            f"--- LIVE WEB DATA ---\n{search_results}\n"
            f"---------------------"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        chain = prompt | self.llm.with_structured_output(MarketReport)
        
        try:
            result = await chain.ainvoke({"input": user_input})
            self.log("Analysis complete.")
            return {"market_analysis": result.model_dump_json()}
        except Exception as e:
            self.log_error(f"LLM Inference failed: {e}")
            return {"market_analysis": "Error in market analysis."}