
from abc import ABC,abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def complete(self,messages:list[dict])-> str:
        """Send messages to the model, return the assistant's text reply.

            Every provider implements this itself.
        """
