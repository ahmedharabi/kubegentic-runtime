"""RemoteTool: implements the Tool interface but calls an HTTP tool service."""

import httpx

from .base import Tool


class RemoteTool(Tool):
    def __init__(self, name: str, description: str, parameters: dict, endpoint: str):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.endpoint = endpoint.rstrip("/")

    async def execute(self, args: dict) -> str:
        url = f"{self.endpoint}/execute"
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(url, json={"args": args})
                resp.raise_for_status()
                return resp.json().get("result", "")
        except httpx.HTTPError as e:
            return f"error: tool {self.name!r} call failed: {e}"


def build_remote_tool(endpoint: str) -> RemoteTool:
    """Fetch the tool's schema from /describe at startup and build a RemoteTool."""
    endpoint = endpoint.rstrip("/")
    resp = httpx.get(f"{endpoint}/describe", timeout=10)
    resp.raise_for_status()
    d = resp.json()
    return RemoteTool(
        name=d["name"],
        description=d["description"],
        parameters=d["parameters"],
        endpoint=endpoint,
    )
