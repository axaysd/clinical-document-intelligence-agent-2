"""
MCP server implementation using simple JSON-RPC over HTTP.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from mcp.tools import TOOLS
from utils.logger import get_logger
import uvicorn

logger = get_logger(__name__)

# MCP server app
mcp_app = FastAPI(title="MCP Tool Server")


class ToolRequest(BaseModel):
    """Request to execute a tool."""
    tool_name: str
    arguments: Dict[str, Any]


class ToolResponse(BaseModel):
    """Response from tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


@mcp_app.get("/tools")
async def list_tools():
    """List available tools."""
    tools_info = []
    for name, tool in TOOLS.items():
        tools_info.append({
            'name': name,
            'description': tool.description,
        })
    return {'tools': tools_info}


@mcp_app.post("/tools/execute", response_model=ToolResponse)
async def execute_tool(request: ToolRequest):
    """Execute a tool with given arguments."""
    logger.info("mcp_tool_execution", tool=request.tool_name)
    
    tool = TOOLS.get(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {request.tool_name}")
    
    try:
        result = tool.execute(**request.arguments)
        
        # Check if tool returned an error
        if isinstance(result, dict) and result.get('error'):
            return ToolResponse(
                success=False,
                result=result.get('result'),
                error=result['error']
            )
        
        return ToolResponse(success=True, result=result, error=None)
    
    except Exception as e:
        logger.error("tool_execution_error", tool=request.tool_name, error=str(e))
        return ToolResponse(success=False, result=None, error=str(e))


@mcp_app.get("/health")
async def health():
    """Health check endpoint."""
    return {'status': 'healthy', 'tools': len(TOOLS)}


def start_mcp_server(host: str = "localhost", port: int = 50051):
    """Start the MCP server."""
    logger.info("starting_mcp_server", host=host, port=port)
    uvicorn.run(mcp_app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    from config import get_settings
    settings = get_settings()
    start_mcp_server(host=settings.mcp_server_host, port=settings.mcp_server_port)
