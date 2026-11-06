import os
import shutil
import logging
import asyncio
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(
level=logging.INFO,
format=”%(asctime)s %(levelname)s %(name)s: %(message)s”
)

logger = logging.getLogger(“salmark”)

app = FastAPI(
title=“Salmark Neshan Bridge”,
version=“1.2.1”
)

TOKEN = os.environ.get(“SALMARK_TOKEN”, “”).strip()

def check_auth(authorization: str | None):
if not TOKEN:
logger.error(“SALMARK_TOKEN is not configured”)
raise HTTPException(
status_code=503,
detail=“SALMARK_TOKEN is not configured”
)

if authorization != f"Bearer {TOKEN}":
    logger.warning("Unauthorized request")
    raise HTTPException(
        status_code=401,
        detail="Unauthorized"
    )

def server_params():
logger.info(“Checking Neshan executable”)

executable = shutil.which("neshan-mcp")
if not executable:
    raise RuntimeError("neshan-mcp executable was not found")
logger.info("Neshan executable found: %s", executable)
return StdioServerParameters(
    command=executable,
    args=[],
    env=os.environ.copy()
)

@app.get(”/”)
async def root():
return {
“ok”: True,
“service”: “salmark-neshan-bridge”,
“version”: “1.2.1”
}

@app.get(”/health”)
async def health():
return {
“ok”: True,
“service”: “salmark-neshan-bridge”,
“version”: “1.2.1”
}

@app.get(”/tools”)
async def list_tools(
authorization: str | None = Header(default=None)
):
check_auth(authorization)

logger.info("TOOLS REQUEST RECEIVED")
try:
    async with stdio_client(server_params()) as (
        read_stream,
        write_stream
    ):
        logger.info("MCP process started")
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            logger.info("Initializing MCP session")
            await asyncio.wait_for(
                session.initialize(),
                timeout=30
            )
            logger.info("MCP session initialized")
            result = await asyncio.wait_for(
                session.list_tools(),
                timeout=30
            )
            logger.info(
                "Tools loaded successfully: %s",
                len(result.tools)
            )
            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.input_schema
                    }
                    for tool in result.tools
                ]
            }
except HTTPException:
    raise
except Exception as error:
    logger.exception("NESHAN MCP TOOLS ERROR")
    raise HTTPException(
        status_code=502,
        detail=(
            f"MCP tools error: "
            f"{type(error).__name__}: {str(error)[:300]}"
        )
    )

class ToolCall(BaseModel):
tool: str = Field(min_length=1)
arguments: dict[str, Any] = Field(default_factory=dict)

@app.post(”/call”)
async def call_tool(
payload: ToolCall,
authorization: str | None = Header(default=None)
):
check_auth(authorization)

logger.info(
    "CALL REQUEST RECEIVED | tool=%s",
    payload.tool
)
try:
    async with stdio_client(server_params()) as (
        read_stream,
        write_stream
    ):
        logger.info("MCP process started for tool call")
        async with ClientSession(
            read_stream,
            write_stream
        ) as session:
            logger.info("Initializing MCP session")
            await asyncio.wait_for(
                session.initialize(),
                timeout=30
            )
            logger.info("MCP session initialized successfully")
            logger.info(
                "Calling Neshan tool: %s",
                payload.tool
            )
            result = await asyncio.wait_for(
                session.call_tool(
                    payload.tool,
                    arguments=payload.arguments
                ),
                timeout=90
            )
            logger.info(
                "Neshan tool completed | isError=%s",
                result.isError
            )
            content = []
            for item in (result.content or []):
                if getattr(item, "type", None) == "text":
                    content.append({
                        "type": "text",
                        "text": item.text
                    })
                else:
                    content.append({
                        "type": getattr(
                            item,
                            "type",
                            "unknown"
                        )
                    })
            return {
                "isError": bool(result.isError),
                "content": content,
                "structuredContent": getattr(
                    result,
                    "structuredContent",
                    None
                )
            }
except HTTPException:
    raise
except asyncio.TimeoutError:
    logger.exception("NESHAN REQUEST TIMED OUT")
    raise HTTPException(
        status_code=504,
        detail="Neshan request timed out"
    )
except Exception as error:
    logger.exception("NESHAN MCP CALL ERROR")
    raise HTTPException(
        status_code=502,
        detail=(
            f"Neshan MCP call failed: "
            f"{type(error).__name__}: {str(error)[:300]}"
        )
    )
