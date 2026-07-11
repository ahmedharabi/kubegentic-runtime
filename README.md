# kubegentic-runtime

AI agent runtime for the kubegentic operator. Each runtime pod serves a single agent over HTTP, processing prompts via an LLM backend.

## Overview

The runtime is a FastAPI application that:

- Exposes a `/invoke` endpoint to process agent prompts with session-based message history
- Provides `/health` and `/info` endpoints for Kubernetes liveness/readiness probes and discovery
- Connects to Groq (OpenAI-compatible API) to generate responses
- Is configured entirely through environment variables injected by the operator

## Configuration

| Variable                  | Description                    |
| ------------------------- | ------------------------------ |
| `AGENT_NAME`              | Name of the agent              |
| `AGENT_MODEL`             | Model identifier                |
| `AGENT_PROVIDER`          | LLM provider                   |
| `AGENT_SYSTEM_PROMPT`     | System prompt for the agent    |
| `GROQ_API_KEY`            | API key for Groq               |

## Running locally

```bash
export AGENT_NAME=my-agent
export AGENT_MODEL=openai/gpt-oss-20b
export AGENT_PROVIDER=groq
export AGENT_SYSTEM_PROMPT="You are a helpful assistant."
export GROQ_API_KEY=your-api-key

pip install -r requirements.txt
uvicorn kubegentic_runtime.main:app --reload
```

## API

### POST /invoke

```json
{ "prompt": "check the cluster status", "session_id": "abc-123" }
```

Returns `{ "response": "...", "agent": "my-agent" }`.

### GET /health

Returns `{ "status": "ok", "agent": "my-agent" }`.

### GET /info

Returns agent metadata including name, model, and provider.

## Docker

```bash
docker build -t kubegentic-runtime .
docker run -p 8000:8000 --env-file .env kubegentic-runtime
```
