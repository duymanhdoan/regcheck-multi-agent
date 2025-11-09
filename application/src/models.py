"""Data models for the application service."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ProcessingJob(BaseModel):
    """Processing job model."""
    
    processing_id: str = Field(..., description="Unique processing job ID")
    file_id: str = Field(..., description="File identifier")
    user_id: str = Field(..., description="User identifier")
    status: str = Field(
        default="pending",
        description="Job status: pending, processing, completed, failed"
    )
    input_s3_key: str = Field(..., description="Input file S3 key")
    output_s3_key: Optional[str] = Field(
        None,
        description="Output file S3 key"
    )
    mcp_server_type: str = Field(
        ...,
        description="MCP server type: finance, hr, legal"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Processing parameters"
    )
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Processing start time"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Processing completion time"
    )
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error message if processing failed"
    )
    download_url: Optional[str] = Field(
        None,
        description="Presigned download URL for result"
    )
    download_url_expires_at: Optional[datetime] = Field(
        None,
        description="Download URL expiration time"
    )


class ProcessRequest(BaseModel):
    """Request to start file processing."""
    
    file_id: str = Field(..., description="File identifier")
    user_id: str = Field(..., description="User identifier")
    input_s3_key: str = Field(..., description="Input file S3 key")
    mcp_server_type: str = Field(
        ...,
        description="MCP server type: finance, hr, legal"
    )
    mcp_tool_name: str = Field(..., description="MCP tool to call")
    mcp_arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for MCP tool"
    )


class ProcessResponse(BaseModel):
    """Response from processing request."""
    
    processing_id: str = Field(..., description="Processing job ID")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")


class StatusResponse(BaseModel):
    """Response for status check."""
    
    processing_id: str = Field(..., description="Processing job ID")
    status: str = Field(..., description="Job status")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    processing_time_ms: Optional[int] = Field(
        None,
        description="Processing time in milliseconds"
    )
    error_message: Optional[str] = Field(None, description="Error message")


class DownloadResponse(BaseModel):
    """Response for download URL request."""
    
    processing_id: str = Field(..., description="Processing job ID")
    download_url: str = Field(..., description="Presigned download URL")
    expires_at: datetime = Field(..., description="URL expiration time")
    output_s3_key: str = Field(..., description="Output file S3 key")
