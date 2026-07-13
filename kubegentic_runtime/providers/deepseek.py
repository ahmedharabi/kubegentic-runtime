"""DeepSeek adapter. Implements the ALI interface with its own code.

DeepSeek's API is OpenAI-compatible. Models: deepseek-chat, deepseek-reasoner.
"""

from openai import AsyncOpenAI

from .base import LLMProvider


class DeepSeekProvider(LLMProvider):
    BASE_URL = "https://api.deepseek.com"

    def __init__(self, model: str, llm_api_key: str):
        self.model = model
        self.client = AsyncOpenAI(api_key=llm_api_key, base_url=self.BASE_URL)

    async def complete(self, messages:list[dict],tools: list[dict] ):
        kwargs = {"model": self.model, "messages": messages}
        if tools:
            kwargs["tools"] = tools
        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message