"""Ollama adapter. Implements the ALI interface with its own code."""

from openai import AsyncOpenAI

from .base import LLMProvider


class OllamaProvider(LLMProvider):
    def __init__(self, model: str):
        self.model = model
        # Ollama's OpenAI-compatible endpoint lives under /v1. It ignores the api
        # key, but the SDK requires a non-empty string, so we pass a throwaway.
        # base_url is not hardcoded because it varies by environment.
        self.client = AsyncOpenAI(api_key="ollama", base_url=f"{ll}/v1")

    async def complete(self, messages: list[dict]) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        return response.choices[0].message.content or ""