from .config import Config
from openai import OpenAI
import os



class Agent:
    def __init__(self,config:Config):
        self.config = config
        self.client =OpenAI(
                    api_key=os.environ.get("GROQ_API_KEY"),
                    base_url="https://api.groq.com/openai/v1",
                    )
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


    def invoke(self,prompt:str,session_id:str)->str:
        messages=self.build_messages(session_id,prompt)

        response =  self.client.responses.create(
            input=messages,
            model="openai/gpt-oss-20b",
        )
        assistant_msg=response.output_text

        self.save_messages(session_id,assistant_msg)
        return assistant_msg