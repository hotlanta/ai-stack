# =============================================================================
# build/nemo-guardrails/server.py
# FastAPI server wrapping NeMo Guardrails
# Exposes OpenAI-compatible /v1/chat/completions endpoint
# Place at: D:\hotlanta_git\ai-stack\build\nemo-guardrails\server.py
# =============================================================================

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from nemoguardrails import RailsConfig, LLMRails

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NeMo Guardrails API", version="1.0.0")

# Load config from mounted volume
CONFIG_PATH = os.getenv("GUARDRAILS_CONFIG_PATH", "/app/config")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
GUARDRAILS_MODEL = os.getenv("GUARDRAILS_MODEL", "phi4-mini:3.8b-q4_K_M")
MAIN_MODEL = os.getenv("MAIN_MODEL", "qwen3:4b-q4_K_M")

# Initialize rails on startup
rails: Optional[LLMRails] = None

@app.on_event("startup")
async def startup():
    global rails
    try:
        config = RailsConfig.from_path(CONFIG_PATH)
        rails = LLMRails(config)
        logger.info(f"NeMo Guardrails loaded from {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Failed to load guardrails config: {e}")
        logger.info("Starting without guardrails — check config path")

# ── Models ────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str = MAIN_MODEL
    messages: List[Message]
    temperature: Optional[float] = 0.1
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False

# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "guardrails_loaded": rails is not None,
        "config_path": CONFIG_PATH,
        "ollama_url": OLLAMA_BASE_URL,
    }

@app.post("/v1/chat/completions")
async def chat(request: ChatRequest):
    """OpenAI-compatible chat endpoint with NeMo Guardrails applied."""

    if not rails:
        raise HTTPException(
            status_code=503,
            detail="Guardrails not loaded. Check config at /app/config/"
        )

    # Extract the last user message
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    try:
        # Run through NeMo Guardrails
        # Input rails check the user query
        # Output rails check the LLM response for groundedness
        response = await rails.generate_async(
            messages=[{"role": m.role, "content": m.content} for m in request.messages]
        )

        return {
            "id": "guardrails-response",
            "object": "chat.completion",
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": -1,    # not tracked at guardrails layer
                "completion_tokens": -1,
                "total_tokens": -1
            }
        }

    except Exception as e:
        logger.error(f"Guardrails error: {e}")
        # Return a safe refusal rather than crashing
        return {
            "id": "guardrails-blocked",
            "object": "chat.completion",
            "model": request.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I cannot provide a response to that query. "
                               "Please rephrase or ask about a different topic."
                },
                "finish_reason": "content_filter"
            }]
        }

@app.get("/v1/models")
async def list_models():
    """OpenAI-compatible models list."""
    return {
        "object": "list",
        "data": [{
            "id": MAIN_MODEL,
            "object": "model",
            "owned_by": "ollama-local"
        }]
    }
