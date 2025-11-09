"""Configuration management for MCP servers."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MCP server settings."""
    
    # Server configuration
    server_type: str = ""
    server_port: int = 8082
    
    # AWS configuration
    aws_region: str = "ap-southeast-1"
    s3_bucket_name: str = "app-files-dev-ap-southeast-1"
    s3_data_prefix: str = "mcp-data/"
    
    # Logging configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
