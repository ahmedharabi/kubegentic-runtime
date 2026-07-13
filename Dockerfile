# Python 3.11 matches the runtime target in the design doc.
# -slim keeps the image small; we do not need a full Debian userland.
FROM python:3.11-slim

# PYTHONDONTWRITEBYTECODE: skip .pyc files (pointless in an ephemeral container).
# PYTHONUNBUFFERED: flush stdout immediately so `kubectl logs` shows output live.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements FIRST, install, THEN copy code. This orders the layers so that
# changing your Python code does not invalidate the dependency-install layer.
# Docker reuses the cached pip layer and rebuilds are fast.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# after the base FROM, before switching to non-root user
RUN apt-get update && apt-get install -y curl && \
    curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && \
    rm kubectl && apt-get purge -y curl && rm -rf /var/lib/apt/lists/*
# Now the application code, in its own layer.
COPY kubegentic_runtime/ ./kubegentic_runtime/

# Run as a non-root user. The runtime never needs root, and if an agent pod is ever
# compromised, it should not be running privileged.
RUN useradd --create-home --uid 1000 appuser
USER appuser

EXPOSE 8000

# uvicorn serves the FastAPI app. host 0.0.0.0 so the container is reachable from
# outside itself (the Kubernetes Service routes traffic to this port).
CMD ["uvicorn", "kubegentic_runtime.main:app", "--host", "0.0.0.0", "--port", "8000"]