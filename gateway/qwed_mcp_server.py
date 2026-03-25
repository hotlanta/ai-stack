from fastapi import FastAPI
from pydantic import BaseModel
from qwed_verify import auto_verify

app = FastAPI(title="QWED MCP Tool")

class ToolCall(BaseModel):
    llm_output: str

@app.post("/mcp/qwed_verify")
async def qwed_verify_tool(call: ToolCall):
    """MCP-compatible tool: deterministic verification"""
    result = auto_verify(call.llm_output)
    return {
        "content": str(result),
        "is_error": not result.get("verified", False)
    }

@app.get("/health")
async def health():
    return {"status": "ok", "tool": "qwed_verify"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
