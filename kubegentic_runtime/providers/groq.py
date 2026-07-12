from .base import LLMProvider
from openai import OpenAI


class GroqProvider(LLMProvider):
    BASE_URL = "https://api.groq.com/openai/v1"
    def __init__(self,model:str,llm_api_key:str):
        self.model = model
        self.client = OpenAI(llm_api_key,self.BASE_URL,)
    def complete(self,messages:list[dict]) -> str:
        response = self.client.responses.create(
            input=messages,
            model=self.model,
        )
        return response.output_text