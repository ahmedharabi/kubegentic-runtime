from .config import Config
from openai import OpenAI
import os
from .providers.factory import get_provider

# abstract class or interface that has baseurl and api key attributes and a complemete methode.

class Agent:
    def __init__(self,config:Config):
        self.config = config
        self.client =get_provider(config)
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

        assistant_msg=await self.client.complete(messages)

        self.save_messages(session_id,assistant_msg)
        return assistant_msg