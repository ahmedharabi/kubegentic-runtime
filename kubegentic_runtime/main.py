
from .config import load_config

from .agent import Agent
from fastapi import FastAPI
from pydantic import BaseModel
config = load_config()
agent = Agent(config)


app = FastAPI(title=f"kubegentic-runtime:{config.agent_name}")

class InvokeRequest(BaseModel):
    prompt:str
    session_id: str

class InvokeResponse(BaseModel):
    response:str
    agent:str



@app.post("/invoke")
async def invoke(request: InvokeRequest):
    answer=agent.invoke(request.prompt,request.session_id )
    return InvokeResponse(response=answer,agent=config.agent_name)

@app.get("/health")
async def health()->dict:
    return {"status": "ok", "agent": config.agent_name}

@app.get("/info")
async def info() -> dict:
    return {
        "name": config.agent_name,
        "model": config.model,
        "provider": config.provider,
        "tools": [],
    }