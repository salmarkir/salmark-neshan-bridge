import os
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

app = FastAPI(title="Salmark Neshan Bridge", version="1.0.0")
TOKEN = os.environ.get("SALMARK_TOKEN", "").strip()

def check_auth(authorization: str | None):
    if not TOKEN:
        raise HTTPException(status_code=503, detail="SALMARK_TOKEN is not configured")
    if authorization != f"Bearer {TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

def server_params():
    return StdioServerParameters(command="neshan-mcp", args=[], env=os.environ.copy())

@app.get("/health")
async def health():
    return {"ok": True, "service": "salmark-neshan-bridge"}

@app.get("/tools")
async def list_tools(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    try:
        async with stdio_client(server_params()) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return {"tools": [{"name": t.name, "description": t.description,
                                   "inputSchema": t.inputSchema} for t in result.tools]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Neshan MCP error: {type(exc).__name__}: {exc}")

class ToolCall(BaseModel):
    tool: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)

@app.post("/call")
async def call_tool(payload: ToolCall, authorization: str | None = Header(default=None)):
    check_auth(authorization)
    try:
        async with stdio_client(server_params()) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(payload.tool, arguments=payload.arguments)
                content = []
                for item in (result.content or []):
                    if getattr(item, "type", None) == "text":
                        content.append({"type": "text", "text": item.text})
                    else:
                        content.append({"type": getattr(item, "type", "unknown")})
                return {"isError": bool(result.isError), "content": content,
                        "structuredContent": getattr(result, "structuredContent", None)}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Neshan MCP error: {type(exc).__name__}: {exc}")
