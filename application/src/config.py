"""Configuration management for the application service."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service configuration
    service_name: str = "application"
    service_port: int = 8000
    
    # AWS configuration
    aws_region: str = "ap-southeast-1"
    s3_bucket_name: str = "app-files-dev-ap-southeast-1"
    
    # AgentGateway configuration
    agentgateway_mcp_url: str = "http://agentgateway-service.local:8081"
    service_token: str = "default-service-token"
    
    # Processing configuration
    processing_timeout: int = 300
    
    # Logging configuration
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
