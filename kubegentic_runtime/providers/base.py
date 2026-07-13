
from abc import ABC,abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self,messages:list[dict],tools: list[dict] ):
        """Send messages (and optionally tool definitions). Return the assistant message.

        The returned message has .content (final text, may be None) and
        .tool_calls (list of requested tool calls, may be empty/None).
        """
