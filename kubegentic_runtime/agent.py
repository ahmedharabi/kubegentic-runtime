from .config import Config
from openai import OpenAI
import os
from .providers.factory import get_provider
from .tools.registry import default_registry
# abstract class or interface that has baseurl and api key attributes and a complemete methode.

class Agent:
    MAX_ITERATIONS = 5
    def __init__(self,config:Config):
        self.config = config
        self.client =get_provider(config)
        self.registry = default_registry()
        self.message_history:dict[str, list[dict]] = {}

    def build_messages(self,session_id:str,prompt:str)->str:
        #combine old messages + system prompt + user prompt
        messages:list[dict]=[]
        if self.config.system_prompt:
            messages.append({"role":"system","content":self.config.system_prompt})
        if self.message_history.get(session_id):
            messages.extend(self.message_history.get(session_id))
        messages.append({"role":"user","content":prompt})
        #log the messages
        return messages
    def save_messages(self,session_id:str,assistant_msg:str):
        self.message_history.setdefault(session_id, []).append(
            {"role": "assistant", "content": assistant_msg}
        )


    async def invoke(self,prompt:str,session_id:str)->str:
        messages=self.build_messages(session_id,prompt)
        tools=self.registry.describe_all()
        print(tools)
        print(messages)
        print("hani lenna")
        for _ in range(self.MAX_ITERATIONS):
            message=await self.client.complete(messages,tools)
            messages.append(message)
            self.save_messages(session_id, message.content or "")

            if not message.tool_calls:
                final = message.content or ""
                self.save_messages(session_id, final)
                return final
            for tool_call in message.tool_calls:
                result = self.registry.execute(
                    tool_call.function.name,
                    tool_call.function.arguments,  # JSON string; registry parses it
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
        fallback = "stopped: reached the maximum number of tool-call rounds"
        self.save_messages(session_id, fallback)
        return fallback





        assistant_msg=await self.client.complete(messages)

        self.save_messages(session_id,assistant_msg)
        return assistant_msg