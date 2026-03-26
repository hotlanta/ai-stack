#!/usr/bin/env python3
# gateway.py — Dynamic model + QWED integration

import requests
import json
import re
import os
from fastapi import FastAPI
from pydantic import BaseModel
from qwed_verify import auto_verify

app = FastAPI()

OLLAMA_BASE = os.getenv("OLLAMA_URL", "http://ollama:11434")

# -------------------------------
# Pydantic models
# -------------------------------
class ChatRequest(BaseModel):
    prompt: str
    model: str = "qwen3:4b-q4_K_M"  # default model

# -------------------------------
# Utility functions
# -------------------------------
def clean_math(text: str) -> str:
    """
    Remove extra LaTeX or escape sequences for QWED.
    """
    # Remove double $ math blocks and escaped newlines
    cleaned = re.sub(r"\\\n", "", text)
    cleaned = re.sub(r"\$\$", "", cleaned)
    return cleaned.strip()

def call_ollama(prompt: str, model: str) -> str:
    """
    Send prompt to Ollama API and return aggregated text.
    """
    url = f"{OLLAMA_BASE}/api/generate"
    headers = {"Content-Type": "application/json"}
    payload = {"prompt": prompt, "model": model, "stream": False}

    response_text = ""
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=300)
        data = response.json()
        return data.get("response", "")
    except Exception as e:
        return f"[Error connecting to Ollama] {str(e)}"

# -------------------------------
# Endpoints
# -------------------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/v1/models")
def list_models():
    """
    Returns a list of Ollama models in Open WebUI compatible format.
    """
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        models = r.json().get("models", [])
        
        return {
            "object": "list",
            "data": [
                {"id": m["name"], "object": "model", "owned_by": "ollama"}
                for m in models
            ],
        }
    except Exception as e:
        return {"object": "list", "data": [], "error": str(e)}

@app.get("/api/tags")
def ollama_tags():
    """
    Ollama-compatible model list — used by Open WebUI when connected as an Ollama endpoint.
    """
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5, stream=False)
        data = r.json()
        # Prefix model names to make gateway models identifiable
        for m in data.get("models", []):
            m["name"] = f"[QWED] {m['name']}"
            m["model"] = m["name"]
        return data
    except Exception as e:
        return {"models": [], "error": str(e)}

@app.post("/api/generate")
def ollama_generate(req: dict):
    """
    Ollama-compatible generate endpoint with QWED verification.
    """
    prompt = req.get("prompt", "")
    model = req.get("model", "qwen3:4b-q4_K_M")
    raw_response = call_ollama(prompt, model)
    cleaned = clean_math(raw_response)
    verified = auto_verify(cleaned)
    content = raw_response
    if verified.get("verified") is False:
        content += f"\n\n⚠️ *Verification failed ({verified.get('engine')}): {verified.get('result')}*"
    return {"model": model, "response": content, "done": True}

@app.post("/v1/chat/completions")
def openai_chat(req: dict):
    """
    Open WebUI / OpenAI-style chat endpoint.
    """
    messages = req.get("messages", [])
    prompt = messages[-1].get("content", "") if messages else ""
    model = req.get("model", "qwen3:4b-q4_K_M")
    
    raw_response = call_ollama(prompt, model)
    cleaned = clean_math(raw_response)
    verified = auto_verify(cleaned)
    
    # Flag unverified outputs in the response
    content = raw_response
    if verified.get("verified") is False:
        content += f"\n\n⚠️ *Verification failed ({verified.get('engine')}): {verified.get('result')}*"
 
    return {
       "id": "chatcmpl-qwed",
       "object": "chat.completion",
       "choices": [
           {
               "index": 0,
               "message": {
                   "role": "assistant",
                   "content": content
               },
               "finish_reason": "stop"
           }
       ],
       "usage": {
           "prompt_tokens": 0,
           "completion_tokens": 0,
           "total_tokens": 0
       }
    }

@app.post("/chat")
def chat(req: ChatRequest):
    """
    Direct chat endpoint with QWED verification and cleaned math.
    """
    # Call Ollama
    raw_response = call_ollama(req.prompt, req.model)

    # Clean math/LaTeX for QWED
    cleaned = clean_math(raw_response)

    # Verify with QWED
    verified = auto_verify(cleaned)

    return {
        "original": raw_response,
        "cleaned": cleaned,
        "verified": verified
    }

# -------------------------------
# Run FastAPI
# -------------------------------
if __name__ == "__main__":
    import uvicorn

    # Listen on 0.0.0.0:8001 for Docker container access
    uvicorn.run(app, host="0.0.0.0", port=8001)