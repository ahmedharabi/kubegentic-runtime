import json

from .base import Tool
from .get_time import GetTimeTool
from .kubectl import KubectlTool

class ToolRegistry:
    def __init__(self, tools: list[Tool]):
        self._tools = {t.name: t for t in tools}

    def describe_all(self) -> list[dict]:
        return [t.describe() for t in self._tools.values()]

    def execute(self, name: str, arguments_json: str) -> str:
        tool = self._tools.get(name)
        if tool is None:
            # The model hallucinated a tool that does not exist. Return an error
            # string instead of crashing -- the model sees it and can recover.
            return f"error: unknown tool {name!r}"

        try:
            args = json.loads(arguments_json) if arguments_json else {}
        except json.JSONDecodeError:
            return f"error: could not parse arguments for tool {name!r}"

        return tool.execute(args)

def default_registry() -> ToolRegistry:
    """The set of tools every agent gets for now. Later this is driven by the
    Agent CR's spec.tools and the Tool CRD."""
    return ToolRegistry([GetTimeTool(),KubectlTool()])