from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.config.settings import settings
from src.prompts.manager import load_prompt
from src.schemas.output import TechReport

class TechAgent(BaseAgent):
    def __init__(self):
        super().__init__("tech")
        self.llm = ChatOpenAI(
            model=settings.MODEL_NAME, 
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        self.prompt_template = load_prompt("tech")

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.log("Analyzing technical feasibility...")
        user_input = state.get("user_input", "")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_template),
            ("user", "{input}")
        ])
        
        chain = prompt | self.llm.with_structured_output(TechReport)
        
        try:
            result = await chain.ainvoke({"input": user_input})
            return {"tech_analysis": result.model_dump_json()}
        except Exception as e:
            self.log_error(f"Tech analysis failed: {e}")
            return {"tech_analysis": "Error in tech analysis."}