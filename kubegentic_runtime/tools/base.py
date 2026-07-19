from abc import ABC, abstractmethod

class Tool(ABC):
    name:str
    description:str
    parameters:dict

    @abstractmethod
    async def execute(self,args:dict) -> str:
        """Run the tool. args is the JSON the model produced. Return a string result."""

    def describe(self) -> str:
        """Return this tool in the format the LLM API expects in its `tools` list."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }