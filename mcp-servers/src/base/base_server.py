"""Base MCP server implementation with protocol handling."""

import logging
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from .models import (
    MCPRequest,
    MCPResponse,
    MCPError,
    Tool,
    Resource,
    ToolsListResponse,
    ToolCallParams,
    ToolCallResponse,
    ResourcesListResponse,
    ResourceReadParams,
    ResourceReadResponse
)
from .s3_client import MCPS3Client

logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """Base MCP server with protocol handling."""
    
    def __init__(
        self,
        server_type: str,
        s3_client: MCPS3Client
    ):
        """Initialize base MCP server.
        
        Args:
            server_type: Server type (finance, hr, legal)
            s3_client: S3 client for data retrieval
        """
        self.server_type = server_type
        self.s3_client = s3_client
        self._tools: Dict[str, Tool] = {}
        self._resources: Dict[str, Resource] = {}
        self._register_tools()
        self._register_resources()
        logger.info(f"Initialized {server_type} MCP server")
    
    @abstractmethod
    def _register_tools(self) -> None:
        """Register available tools. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def _register_resources(self) -> None:
        """Register available resources. Must be implemented by subclasses."""
        pass
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool.
        
        Args:
            tool: Tool definition
        """
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")
    
    def register_resource(self, resource: Resource) -> None:
        """Register a resource.
        
        Args:
            resource: Resource definition
        """
        self._resources[resource.uri] = resource
        logger.debug(f"Registered resource: {resource.uri}")
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle MCP request.
        
        Args:
            request: MCP request
            
        Returns:
            MCP response
        """
        try:
            logger.info(f"Handling MCP request: {request.method}")
            
            if request.method == "tools/list":
                result = await self.list_tools()
            elif request.method == "tools/call":
                params = ToolCallParams(**request.params)
                result = await self.call_tool(params)
            elif request.method == "resources/list":
                result = await self.list_resources()
            elif request.method == "resources/read":
                params = ResourceReadParams(**request.params)
                result = await self.read_resource(params)
            else:
                return MCPResponse(
                    id=request.id,
                    error=MCPError(
                        code=-32601,
                        message=f"Method not found: {request.method}"
                    )
                )
            
            return MCPResponse(id=request.id, result=result.dict())
            
        except Exception as e:
            logger.error(f"Error handling request: {e}", exc_info=True)
            return MCPResponse(
                id=request.id,
                error=MCPError(
                    code=-32603,
                    message=f"Internal error: {str(e)}"
                )
            )
    
    async def list_tools(self) -> ToolsListResponse:
        """List available tools.
        
        Returns:
            List of tools
        """
        logger.info(f"Listing {len(self._tools)} tools")
        return ToolsListResponse(tools=list(self._tools.values()))
    
    async def call_tool(self, params: ToolCallParams) -> ToolCallResponse:
        """Call a tool.
        
        Args:
            params: Tool call parameters
            
        Returns:
            Tool execution result
        """
        tool_name = params.name
        
        if tool_name not in self._tools:
            logger.error(f"Tool not found: {tool_name}")
            return ToolCallResponse(
                content=[{
                    "type": "text",
                    "text": f"Tool not found: {tool_name}"
                }],
                isError=True
            )
        
        try:
            logger.info(f"Calling tool: {tool_name}")
            result = await self._execute_tool(tool_name, params.arguments)
            
            return ToolCallResponse(
                content=[{
                    "type": "text",
                    "text": str(result)
                }],
                isError=False
            )
        except Exception as e:
            logger.error(f"Tool execution failed: {e}", exc_info=True)
            return ToolCallResponse(
                content=[{
                    "type": "text",
                    "text": f"Tool execution failed: {str(e)}"
                }],
                isError=True
            )
    
    @abstractmethod
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool. Must be implemented by subclasses.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        pass
    
    async def list_resources(self) -> ResourcesListResponse:
        """List available resources.
        
        Returns:
            List of resources
        """
        logger.info(f"Listing {len(self._resources)} resources")
        return ResourcesListResponse(resources=list(self._resources.values()))
    
    async def read_resource(self, params: ResourceReadParams) -> ResourceReadResponse:
        """Read a resource.
        
        Args:
            params: Resource read parameters
            
        Returns:
            Resource contents
        """
        uri = params.uri
        
        if uri not in self._resources:
            logger.error(f"Resource not found: {uri}")
            return ResourceReadResponse(
                contents=[{
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": f"Resource not found: {uri}"
                }]
            )
        
        try:
            logger.info(f"Reading resource: {uri}")
            content = await self._read_resource_content(uri)
            
            return ResourceReadResponse(
                contents=[{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": str(content)
                }]
            )
        except Exception as e:
            logger.error(f"Resource read failed: {e}", exc_info=True)
            return ResourceReadResponse(
                contents=[{
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": f"Resource read failed: {str(e)}"
                }]
            )
    
    @abstractmethod
    async def _read_resource_content(self, uri: str) -> Any:
        """Read resource content. Must be implemented by subclasses.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        pass
