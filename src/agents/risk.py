from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
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
            model=settings.MODEL_NAME, 
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt_template = load_prompt("risk")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Analyzing risks...")
        user_input = state.get("user_input", "")
        
        # 1. Search for Legal/PR Risks
        self.log(f"Searching legal risks for: {user_input}...")
        search_query = f"{user_input} legal risks controversy lawsuits regulation"
        search_results = perform_web_search(search_query)
        
        # 2. Inject
        system_prompt = (
            f"{self.prompt_template}\n\n"
            f"--- LIVE LEGAL & NEWS DATA ---\n{search_results}\n"
            f"------------------------------"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        chain = prompt | self.llm.with_structured_output(RiskReport)
        
        try:
            result = await chain.ainvoke({"input": user_input})
            return {"risk_analysis": result.model_dump_json()}
        except Exception as e:
            self.log_error(f"Risk analysis failed: {e}")
            return {"risk_analysis": "Error in risk analysis."}