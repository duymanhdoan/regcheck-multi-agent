"""MCP protocol models."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""
    
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Union[str, int] = Field(..., description="Request ID")
    method: str = Field(..., description="Method name")
    params: Optional[Dict[str, Any]] = Field(None, description="Method parameters")


class MCPError(BaseModel):
    """MCP error object."""
    
    code: int = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    data: Optional[Any] = Field(None, description="Additional error data")


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""
    
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    id: Union[str, int] = Field(..., description="Request ID")
    result: Optional[Any] = Field(None, description="Result data")
    error: Optional[MCPError] = Field(None, description="Error object")


class Tool(BaseModel):
    """MCP tool definition."""
    
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    inputSchema: Dict[str, Any] = Field(..., description="JSON Schema for tool input")


class Resource(BaseModel):
    """MCP resource definition."""
    
    uri: str = Field(..., description="Resource URI")
    name: str = Field(..., description="Resource name")
    description: str = Field(..., description="Resource description")
    mimeType: Optional[str] = Field(None, description="MIME type")


class ToolsListResponse(BaseModel):
    """Response for tools/list method."""
    
    tools: List[Tool] = Field(..., description="List of available tools")


class ToolCallParams(BaseModel):
    """Parameters for tools/call method."""
    
    name: str = Field(..., description="Tool name")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class ToolCallResponse(BaseModel):
    """Response for tools/call method."""
    
    content: List[Dict[str, Any]] = Field(..., description="Tool execution results")
    isError: bool = Field(default=False, description="Whether execution resulted in error")


class ResourcesListResponse(BaseModel):
    """Response for resources/list method."""
    
    resources: List[Resource] = Field(..., description="List of available resources")


class ResourceReadParams(BaseModel):
    """Parameters for resources/read method."""
    
    uri: str = Field(..., description="Resource URI")


class ResourceReadResponse(BaseModel):
    """Response for resources/read method."""
    
    contents: List[Dict[str, Any]] = Field(..., description="Resource contents")
