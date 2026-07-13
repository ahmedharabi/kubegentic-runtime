from datetime import datetime,timezone

from .base import Tool


class GetTimeTool(Tool):
    name = "get_current_time"
    description = (
        "Get the current UTC date and time. "
        "Use this whenever the user asks what time or date it is."
    )
    parameters = {"type": "object", "properties": {}, "required": []}

    def execute(self, args: dict) -> str:
        return datetime.now(timezone.utc).isoformat()