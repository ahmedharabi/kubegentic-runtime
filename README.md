# kubegentic-runtime

AI agent runtime for the [kubegentic operator](https://github.com/anomalyco/kubegentic-operator). Each runtime pod serves a single agent over HTTP, processing prompts via an LLM backend with tool-calling and session-based message history.

## Overview

A FastAPI application that:

- Exposes a `POST /invoke` endpoint to process agent prompts with session-based message history
- Provides `GET /health` and `GET /info` endpoints for Kubernetes liveness/readiness probes and discovery
- Connects to an LLM provider (Ollama, OpenAI, DeepSeek, or Groq) to generate responses
- Runs a ReAct (Reasoning + Acting) loop: the LLM can call tools, results feed back into the conversation, and the loop continues until a final answer is produced
- Supports remote tools loaded dynamically from external HTTP tool services at startup
- Is configured entirely through environment variables injected by the operator

## LLM Providers

| Provider | SDK | Base URL | Key Required |
|---|---|---|---|
| **Ollama** | `AsyncOpenAI` | configurable via `OLLAMA_BASE_URL` | No |
| **OpenAI** | `OpenAI` (sync) | `https://api.openai.com/v1` | Yes |
| **DeepSeek** | `AsyncOpenAI` | `https://api.deepseek.com` | Yes |
| **Groq** | `OpenAI` (sync) | `https://api.groq.com/openai/v1` | Yes |

Set `AGENT_PROVIDER` to one of: `ollama`, `openai`, `deepseek`, `groq`.

## Tools

Tools are advertised to the LLM via OpenAI-compatible function-calling schemas and executed during the ReAct loop.

### Remote Tools

Tools are loaded from external HTTP services at startup. Each tool service must expose:

| Endpoint | Description |
|---|---|
| `GET /describe` | Returns `{"name": "...", "description": "...", "parameters": {...}}` |
| `POST /execute` | Receives `{"args": {...}}`, returns `{"result": "..."}` |

Configure remote tools via environment variables:

| Variable | Description |
|---|---|
| `TOOL_LIST` | Comma-separated tool names (e.g. `my-tool,another-tool`) |
| `TOOL_<NAME>_ENDPOINT` | HTTP endpoint for each tool listed in `TOOL_LIST` |

On startup, the runtime calls `GET /describe` on each endpoint to register the tool's schema. During a ReAct loop, tool calls are forwarded to `POST /execute` on the corresponding endpoint.

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `AGENT_NAME` | yes | — | Name of the agent |
| `AGENT_MODEL` | yes | — | Model identifier (e.g. `gpt-4o`, `deepseek-chat`, `llama3`) |
| `AGENT_PROVIDER` | yes | — | LLM provider |
| `AGENT_SYSTEM_PROMPT` | yes | — | System prompt for the agent |
| `LLM_API_KEY` | yes* | — | API key (not needed for Ollama) |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | Base URL for Ollama |
| `TOOL_LIST` | no | — | Comma-separated remote tool names |
| `TOOL_<NAME>_ENDPOINT` | conditional | — | Endpoint for each tool in `TOOL_LIST` |

## API

### `POST /invoke`

```
Body: { "prompt": "check the cluster status", "session_id": "abc-123" }
Response: { "response": "...", "agent": "my-agent" }
```

The agent runs a ReAct loop (up to 5 tool-call iterations):
1. Sends the system prompt, session history, and new user prompt to the LLM
2. If the LLM calls a tool, executes it and feeds the result back
3. Repeats until the LLM produces a final text answer
4. Returns the final answer and saves it to session history

### `GET /health`

```
Response: { "status": "ok", "agent": "my-agent" }
```

### `GET /info`

```
Response: { "name": "my-agent", "model": "...", "provider": "...", "tools": [] }
```

## Session & Message History

The agent maintains an in-memory dictionary keyed by `session_id`. Each entry is a list of messages in OpenAI chat format. History persists for the lifetime of the pod. On each `/invoke` call, the agent prepends the system prompt and prior assistant responses before the new user prompt.

## Running locally

### Prerequisites
- Python 3.11+

### Setup

```bash
cd runtime
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### With OpenAI

```bash
export AGENT_NAME=my-agent
export AGENT_MODEL=gpt-4o
export AGENT_PROVIDER=openai
export AGENT_SYSTEM_PROMPT="You are a helpful Kubernetes assistant."
export LLM_API_KEY=sk_your_key_here

uvicorn kubegentic_runtime.main:app --reload
```

### Test

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "what time is it?", "session_id": "test-1"}'
```

## Docker

```bash
docker build -t kubegentic-runtime .
docker run -p 8000:8000 --env-file .env kubegentic-runtime
```

### Build for minikube

```bash
make build
```

(Runs `eval $(minikube docker-env)` before building so the image lands in minikube's Docker daemon.)

## Project Structure

```
kubegentic_runtime/
├── __init__.py
├── agent.py              # Agent class: ReAct loop, message history, tool orchestration
├── config.py             # Configuration from environment variables
├── main.py               # FastAPI application and endpoints
├── providers/
│   ├── __init__.py
│   ├── base.py           # Abstract LLMProvider base class
│   ├── deepseek.py       # DeepSeek (AsyncOpenAI)
│   ├── factory.py        # Provider factory
│   ├── groq.py           # Groq (OpenAI sync client)
│   ├── ollama.py         # Ollama (AsyncOpenAI)
│   └── openai.py         # OpenAI (OpenAI sync client)
└── tools/
    ├── __init__.py
    ├── base.py           # Abstract Tool base class
    ├── registry.py       # ToolRegistry: describe, execute, build_registry
    └── remote.py         # RemoteTool: fetches schema via /describe, proxies execution via /execute
```

## Dependencies

- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server
- `openai` — OpenAI Python SDK (used by all providers)
- `httpx` — HTTP client for remote tool calls
- `pydantic` — request/response models
