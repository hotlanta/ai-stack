# =============================================================================
# build/nemo-guardrails/Dockerfile
# Builds NeMo Guardrails from source — no pre-built image exists
# Place at: D:\hotlanta_git\ai-stack\build\nemo-guardrails\Dockerfile
# =============================================================================

FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install NeMo Guardrails with Ollama support
RUN pip install --no-cache-dir \
    "nemoguardrails[ollama]" \
    langchain-ollama \
    fastapi \
    uvicorn \
    httpx \
    langfuse

# Config is mounted at runtime via volume: ./config/nemo-guardrails:/app/config

# FastAPI wrapper
COPY server.py /app/server.py

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
