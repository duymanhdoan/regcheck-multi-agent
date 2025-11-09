"""Data models for AgentGateway service."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AuditLog(BaseModel):
    """Audit log entry for request tracking."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    username: Optional[str] = None
    department: Optional[str] = None
    method: str
    path: str
    status_code: int
    error: Optional[str] = None
    client_ip: Optional[str] = None


class MCPRequest(BaseModel):
    """MCP JSON-RPC request."""
    jsonrpc: str = "2.0"
    id: str
    method: str
    params: Optional[dict] = None


class MCPResponse(BaseModel):
    """MCP JSON-RPC response."""
    jsonrpc: str = "2.0"
    id: str
    result: Optional[dict] = None
    error: Optional[dict] = None


class ServiceTokenPayload(BaseModel):
    """Service token payload for MCP gateway."""
    service_name: str
    department: Optional[str] = None
