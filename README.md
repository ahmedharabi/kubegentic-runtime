# kubegentic-runtime

AI agent runtime for the [kubegentic operator](https://github.com/anomalyco/kubegentic-operator). Each runtime pod serves a single agent over HTTP, processing prompts via an LLM backend with tool-calling and session-based message history.

## Overview

A FastAPI application that:

- Exposes a `POST /invoke` endpoint to process agent prompts with session-based message history
- Provides `GET /health` and `GET /info` endpoints for Kubernetes liveness/readiness probes and discovery
- Connects to an LLM provider (Ollama, OpenAI, DeepSeek, or Groq) to generate responses
- Runs a ReAct (Reasoning + Acting) loop: the LLM can call tools, the results feed back into the conversation, and the loop continues until a final answer is produced
- Includes read-only `kubectl` and `get_current_time` tools out of the box
- Is configured entirely through environment variables injected by the operator

## LLM Providers

| Provider | File | SDK | Base URL | Key Required |
|---|---|---|---|---|
| **Ollama** | `providers/ollama.py` | `AsyncOpenAI` | configurable via `OLLAMA_BASE_URL` | No |
| **OpenAI** | `providers/openai.py` | `OpenAI` (sync) | `https://api.openai.com/v1` | Yes |
| **DeepSeek** | `providers/deepseek.py` | `AsyncOpenAI` | `https://api.deepseek.com` | Yes |
| **Groq** | `providers/groq.py` | `OpenAI` (sync) | `https://api.groq.com/openai/v1` | Yes |

Set `AGENT_PROVIDER` to one of: `ollama`, `openai`, `deepseek`, `groq`.

## Tools

Registered tools are advertised to the LLM via OpenAI-compatible function-calling schemas. The agent executes them and feeds results back into the conversation.

### `get_current_time`
No arguments. Returns the current UTC date and time in ISO 8601 format.

### `kubectl`
**Read-only** kubectl interface. Only `get`, `describe`, and `logs` verbs are allowed. Returns:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `verb` | `string` | yes | `get`, `describe`, or `logs` |
| `resource` | `string` | yes | Resource type (e.g. `pods`, `deployments`) or pod name for logs |
| `name` | `string` | no | Specific resource name |
| `namespace` | `string` | no | Kubernetes namespace (default: `default`) |

**Security model:**
- The tool schema restricts the model to only the three read verbs at the API level
- A runtime guard re-checks the verb before executing (defense in depth)
- Commands are built as argument lists (no `shell=True`), preventing shell injection
- A 15-second timeout prevents hung kubectl from blocking the agent
- Log output is capped at 50 lines

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `AGENT_NAME` | yes | — | Name of the agent |
| `AGENT_MODEL` | yes | — | Model identifier (e.g. `gpt-4o`, `deepseek-chat`, `llama3`) |
| `AGENT_PROVIDER` | yes | — | LLM provider: `ollama`, `openai`, `deepseek`, or `groq` |
| `AGENT_SYSTEM_PROMPT` | yes | — | System prompt for the agent |
| `LLM_API_KEY` | yes* | — | API key (not needed for Ollama) |
| `OLLAMA_BASE_URL` | no | `http://localhost:11434` | Base URL for Ollama (only used when provider is `ollama`) |

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
Response: { "name": "my-agent", "model": "...", "provider": "...", "tools": [ ... ] }
```

## Session & Message History

The agent maintains an in-memory dictionary keyed by `session_id`. Each entry is a list of messages in OpenAI chat format. History persists for the lifetime of the pod and grows unboundedly per session. On each `/invoke` call, the agent prepends the system prompt and prior assistant responses before the new user prompt.

## Running locally

### Prerequisites
- Python 3.11+
- `pip`

### Setup

```bash
# Clone and enter the directory
cd runtime

# (Optional) Create a virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### With Ollama (no API key needed)

```bash
export AGENT_NAME=my-agent
export AGENT_MODEL=llama3
export AGENT_PROVIDER=ollama
export AGENT_SYSTEM_PROMPT="You are a helpful Kubernetes assistant."
export OLLAMA_BASE_URL=http://localhost:11434

uvicorn kubegentic_runtime.main:app --reload
```

### With Groq (API key required)

```bash
export AGENT_NAME=my-agent
export AGENT_MODEL=llama3-70b-8192
export AGENT_PROVIDER=groq
export AGENT_SYSTEM_PROMPT="You are a helpful Kubernetes assistant."
export LLM_API_KEY=gsk_your_key_here

uvicorn kubegentic_runtime.main:app --reload
```

### With DeepSeek

```bash
export AGENT_NAME=my-agent
export AGENT_MODEL=deepseek-chat
export AGENT_PROVIDER=deepseek
export AGENT_SYSTEM_PROMPT="You are a helpful Kubernetes assistant."
export LLM_API_KEY=sk_your_key_here

uvicorn kubegentic_runtime.main:app --reload
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

### Test the server

```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"prompt": "what time is it?", "session_id": "test-1"}'
```

## Docker

```bash
# Build
docker build -t kubegentic-runtime .

# Run with environment file
docker run -p 8000:8000 --env-file .env kubegentic-runtime
```

### Build for minikube

```bash
make build
```

(This runs `eval $(minikube docker-env)` before building so the image lands in minikube's Docker daemon.)

## Project Structure

```
kubegentic_runtime/
├── agent.py              # Agent class: builds messages, runs ReAct loop, manages history
├── config.py             # Configuration from environment variables
├── main.py               # FastAPI application and endpoints
├── providers/
│   ├── base.py           # Abstract LLMProvider base class
│   ├── deepseek.py       # DeepSeek (AsyncOpenAI, Chat Completions API)
│   ├── factory.py        # Provider factory
│   ├── groq.py           # Groq (OpenAI sync client, Responses API)
│   ├── ollama.py         # Ollama (AsyncOpenAI, Chat Completions API)
│   └── openai.py         # OpenAI (OpenAI sync client, Responses API)
└── tools/
    ├── base.py           # Abstract Tool base class
    ├── get_time.py       # get_current_time tool
    ├── kubectl.py        # Read-only kubectl tool
    └── registry.py       # ToolRegistry for tool lookup and execution
```

## Dependencies

- `fastapi` — web framework
- `uvicorn[standard]` — ASGI server with hot-reload
- `openai` — OpenAI Python SDK (used by all providers via OpenAI-compatible APIs)
