"""Configuration management for AgentGateway service."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service configuration
    service_name: str = "agentgateway"
    api_port: int = 8080
    mcp_port: int = 8081
    
    # AWS configuration
    aws_region: str = "ap-southeast-1"
    cognito_user_pool_id: str
    cognito_region: str = "ap-southeast-1"
    
    # Feature flags
    rbac_enabled: bool = True
    department_isolation: bool = True
    
    # Backend service URLs
    application_service_url: str = "http://application-service.local:8000"
    mcp_finance_url: str = "http://mcp-finance-service.local:8080"
    mcp_hr_url: str = "http://mcp-hr-service.local:8080"
    mcp_legal_url: str = "http://mcp-legal-service.local:8080"
    
    # Service token for MCP gateway
    service_token: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
