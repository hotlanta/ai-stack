#!/usr/bin/env python3
from fastapi import FastAPI
from pydantic import BaseModel
from qwed_verify import auto_verify

app = FastAPI(title="QWED MCP Tool")

class ToolCall(BaseModel):
    name: str
    arguments: dict

@app.get("/tools")
def list_tools():
    return [{
        "name": "qwed_verify",
        "description": "Deterministically verify math, SQL, code, logic, or schema from any LLM output. Returns verified result or clear failure reason.",
        "parameters": {
            "type": "object",
            "properties": {
                "llm_output": {"type": "string", "description": "The exact output from the LLM to verify"}
            },
            "required": ["llm_output"]
        }
    }]

@app.post("/invoke")
async def invoke(call: ToolCall):
    if call.name == "qwed_verify":
        try:
            result = auto_verify(call.arguments["llm_output"])
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Unknown tool"}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8091)
