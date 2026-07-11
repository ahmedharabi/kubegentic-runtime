import os


def _require(name:str)->str:
    value=os.environ.get(name)
    if not value:
        raise RuntimeError(f"required env var {name!r} is not set -- "
            f"check that the operator injects it into the pod spec")
    return value

class Config:
    def __init__(
        self,
        agent_name: str,
        model: str,
        provider: str,
        system_prompt: str,
        max_history_messages: int = 20,
    ):
        self.agent_name = agent_name
        self.model = model
        self.provider = provider
        self.system_prompt = system_prompt
        self.max_history_messages = max_history_messages

def load_config()->Config:
    return Config(
        agent_name=_require("AGENT_NAME"),
        model=_require("AGENT_MODEL"),
        provider=_require("AGENT_PROVIDER"),
        system_prompt=_require("AGENT_SYSTEM_PROMPT"),

    )
