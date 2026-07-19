import os
from dataclasses import dataclass, field


def _require(name:str)->str:
    value=os.environ.get(name)
    if not value:
        raise RuntimeError(f"required env var {name!r} is not set -- "
            f"check that the operator injects it into the pod spec")
    return value

def _load_tools() -> dict[str, str]:
    """Parse TOOL_LIST + TOOL_<NAME>_ENDPOINT into {name: endpoint}."""
    raw = os.environ.get("TOOL_LIST", "")
    names = [n.strip() for n in raw.split(",") if n.strip()]
    tools: dict[str, str] = {}
    for name in names:
        env_key = f"TOOL_{name.upper()}_ENDPOINT"
        endpoint = os.environ.get(env_key)
        if not endpoint:
            raise RuntimeError(f"{env_key} not set for tool {name!r} listed in TOOL_LIST")
        tools[name] = endpoint
    return tools

class Config:
    def __init__(
        self,
        agent_name: str,
        model: str,
        provider: str,
        system_prompt: str,
        llm_api_key: str,
        tools: dict[str, str] = field(default_factory=dict),

        max_history_messages: int = 20,
    ):
        self.tools = tools
        self.agent_name = agent_name
        self.model = model
        self.provider = provider
        self.system_prompt = system_prompt
        self.llm_api_key = llm_api_key
        self.max_history_messages = max_history_messages

def load_config()->Config:
    return Config(
        agent_name=_require("AGENT_NAME"),
        model=_require("AGENT_MODEL"),
        provider=_require("AGENT_PROVIDER"),
        system_prompt=_require("AGENT_SYSTEM_PROMPT"),
        llm_api_key=_require("LLM_API_KEY"),
        tools=_load_tools(),
    )
