from ..config import Config
from .base import LLMProvider
from .deepseek import DeepSeekProvider
from .groq import GroqProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

def get_provider(config: Config) -> LLMProvider:
    provider = config.provider.lower()

    if provider == "ollama":
        return OllamaProvider(model=config.model)

    if provider == "openai":
        _require_key(config, "openai")
        return OpenAIProvider(model=config.model, llm_api_key=config.llm_api_key)

    if provider == "deepseek":
        _require_key(config, "deepseek")
        return DeepSeekProvider(model=config.model, llm_api_key=config.llm_api_key)

    if provider == "groq":
        _require_key(config, "groq")
        return GroqProvider(model=config.model, llm_api_key=config.llm_api_key)

    # No fallback, by design. An unknown provider is a configuration error
    # we do not guess a default (e.g. Ollama), because we cannot assume the user has any
    # particular backend running. Fail loudly at startup instead.
    raise RuntimeError(
        f"unsupported provider {config.provider!r} -- "
        f"supported providers are: ollama, openai, deepseek, groq"
    )

def _require_key(config: Config, provider_name: str) -> None:
    """Cloud providers need a key. Ollama does not, so it never calls this."""
    if not config.llm_api_key:
        raise RuntimeError(
            f"provider {provider_name!r} requires an API key but none was provided -- "
            f"set spec.apiKeySecretRef on the Agent so LLM_API_KEY is injected"
        )