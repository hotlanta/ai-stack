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

OLLAMA_BASE = os.getenv("OLLAMA_URL", "http://ollama:11434/api/generate")

class ChatRequest(BaseModel):
    prompt: str
    model: str = "qwen3:4b-q4_K_M"  # default model

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
    url = OLLAMA_BASE
    headers = {"Content-Type": "application/json"}
    payload = {"prompt": prompt, "model": model, "stream": True}

    response_text = ""
    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=300) as r:
            for line in r.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        # Partial streaming
                        partial = data.get("response")
                        if partial:
                            response_text += partial
                    except json.JSONDecodeError:
                        continue
        return response_text
    except Exception as e:
        return f"[Error connecting to Ollama] {str(e)}"

@app.post("/v1/chat/completions")
def openai_chat(req: dict):
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
        "choices": [{
            "message": {"role": "assistant", "content": content},
            "finish_reason": "stop"
        }]
    }

@app.post("/chat")
def chat(req: ChatRequest):
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

@app.get("/health")
def health():
    return {"status": "ok"}