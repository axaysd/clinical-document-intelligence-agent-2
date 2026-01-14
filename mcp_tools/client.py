"""
MCP client for agent to call tools via MCP protocol.
"""

import requests
from typing import Dict, Any, List
from models.schemas import ToolCall
from utils.logger import get_logger
from utils.helpers import get_timestamp
from config import get_settings

logger = get_logger(__name__)


class MCPClient:
    """Client for calling MCP tools."""
    
    def __init__(self):
        """Initialize MCP client."""
        settings = get_settings()
        self.base_url = f"http://{settings.mcp_server_host}:{settings.mcp_server_port}"
        logger.info("mcp_client_initialized", base_url=self.base_url)
    
    def list_tools(self) -> List[Dict[str, str]]:
        """
        List available tools from MCP server.
        
        Returns:
            List of tool definitions
        """
        try:
            response = requests.get(f"{self.base_url}/tools", timeout=5)
            response.raise_for_status()
            return response.json()['tools']
        except Exception as e:
            logger.error("failed_to_list_tools", error=str(e))
            return []
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCall:
        """
        Call a tool via MCP protocol.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            ToolCall record with result or error
        """
        logger.info("calling_mcp_tool", tool=tool_name, args=arguments)
        
        try:
            response = requests.post(
                f"{self.base_url}/tools/execute",
                json={
                    'tool_name': tool_name,
                    'arguments': arguments
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data['success']:
                return ToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=data['result'],
                    error=None,
                    timestamp=get_timestamp()
                )
            else:
                return ToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=None,
                    error=data['error'],
                    timestamp=get_timestamp()
                )
        
        except Exception as e:
            logger.error("mcp_tool_call_failed", tool=tool_name, error=str(e))
            return ToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                error=str(e),
                timestamp=get_timestamp()
            )
