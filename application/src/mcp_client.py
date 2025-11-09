"""MCP client for calling MCP servers via AgentGateway."""

import logging
import uuid
from typing import Dict, Any, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Exception raised for MCP client errors."""
    pass


class MCPClient:
    """Client for calling MCP servers through AgentGateway."""
    
    def __init__(
        self,
        agentgateway_url: str,
        service_token: str,
        timeout: int = 30
    ):
        """Initialize MCP client.
        
        Args:
            agentgateway_url: URL of AgentGateway MCP endpoint
            service_token: Service authentication token
            timeout: Request timeout in seconds
        """
        self.agentgateway_url = agentgateway_url
        self.service_token = service_token
        self.timeout = timeout
        logger.info(f"Initialized MCP client for {agentgateway_url}")
    
    def _create_mcp_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create MCP JSON-RPC request.
        
        Args:
            method: MCP method name (e.g., "tools/call", "resources/read")
            params: Method parameters
            
        Returns:
            MCP request dictionary
        """
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method
        }
        if params:
            request["params"] = params
        return request
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True
    )
    async def call_mcp_server(
        self,
        server_type: str,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call MCP server via AgentGateway with retry logic.
        
        Args:
            server_type: Type of MCP server (finance, hr, legal)
            method: MCP method name
            params: Method parameters
            
        Returns:
            MCP response result
            
        Raises:
            MCPClientError: If MCP call fails
        """
        mcp_request = self._create_mcp_request(method, params)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.service_token}",
            "X-MCP-Server-Type": server_type
        }
        
        try:
            logger.info(
                f"Calling MCP server {server_type} with method {method}"
            )
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.agentgateway_url}/mcp",
                    json=mcp_request,
                    headers=headers
                )
                response.raise_for_status()
                
                mcp_response = response.json()
                
                # Check for MCP error
                if "error" in mcp_response:
                    error = mcp_response["error"]
                    error_msg = (
                        f"MCP error {error.get('code')}: "
                        f"{error.get('message')}"
                    )
                    logger.error(error_msg)
                    raise MCPClientError(error_msg)
                
                logger.info(
                    f"Successfully called MCP server {server_type}"
                )
                return mcp_response.get("result", {})
                
        except httpx.HTTPStatusError as e:
            error_msg = (
                f"HTTP error calling MCP server {server_type}: "
                f"{e.response.status_code}"
            )
            logger.error(error_msg)
            raise MCPClientError(error_msg) from e
        except httpx.TimeoutException as e:
            error_msg = f"Timeout calling MCP server {server_type}"
            logger.error(error_msg)
            raise MCPClientError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error calling MCP server {server_type}: {e}"
            logger.error(error_msg)
            raise MCPClientError(error_msg) from e
    
    async def list_tools(self, server_type: str) -> Dict[str, Any]:
        """List available tools on MCP server.
        
        Args:
            server_type: Type of MCP server
            
        Returns:
            List of available tools
        """
        return await self.call_mcp_server(
            server_type=server_type,
            method="tools/list"
        )
    
    async def call_tool(
        self,
        server_type: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call a tool on MCP server.
        
        Args:
            server_type: Type of MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        return await self.call_mcp_server(
            server_type=server_type,
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
    
    async def list_resources(self, server_type: str) -> Dict[str, Any]:
        """List available resources on MCP server.
        
        Args:
            server_type: Type of MCP server
            
        Returns:
            List of available resources
        """
        return await self.call_mcp_server(
            server_type=server_type,
            method="resources/list"
        )
    
    async def read_resource(
        self,
        server_type: str,
        resource_uri: str
    ) -> Dict[str, Any]:
        """Read a resource from MCP server.
        
        Args:
            server_type: Type of MCP server
            resource_uri: URI of the resource to read
            
        Returns:
            Resource content
        """
        return await self.call_mcp_server(
            server_type=server_type,
            method="resources/read",
            params={"uri": resource_uri}
        )
