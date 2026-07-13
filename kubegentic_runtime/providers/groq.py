from .base import LLMProvider
from openai import OpenAI


class GroqProvider(LLMProvider):
    BASE_URL = "https://api.groq.com/openai/v1"
    def __init__(self,model:str,llm_api_key:str):
        self.model = model
        self.client = OpenAI(llm_api_key,self.BASE_URL,)
    def complete(self,messages:list[dict],tools: list[dict]):
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        response = self.client.responses.create(**kwargs)
        return response.output_text