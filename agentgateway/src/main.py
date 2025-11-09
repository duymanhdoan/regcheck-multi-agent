"""Main FastAPI application for AgentGateway with dual mode support."""
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pythonjsonlogger import jsonlogger

from .config import settings
from .api_gateway import router as api_router
from .mcp_gateway import router as mcp_router


# Configure JSON logging
def setup_logging():
    """Configure structured JSON logging."""
    log_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    log_handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Reduce noise from httpx
    logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(
        f"Starting AgentGateway service",
        extra={
            "service_name": settings.service_name,
            "api_port": settings.api_port,
            "mcp_port": settings.mcp_port,
            "rbac_enabled": settings.rbac_enabled,
            "department_isolation": settings.department_isolation
        }
    )
    
    yield
    
    # Shutdown
    logger.info("Shutting down AgentGateway service")


# Create FastAPI application
app = FastAPI(
    title="AgentGateway",
    description="Dual-mode routing and authentication gateway for Internal File Processing System",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router)
app.include_router(mcp_router)


@app.get("/health")
async def health_check():
    """Health check endpoint for both modes.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": settings.service_name,
        "api_port": settings.api_port,
        "mcp_port": settings.mcp_port,
        "rbac_enabled": settings.rbac_enabled,
        "department_isolation": settings.department_isolation
    }


@app.get("/")
async def root():
    """Root endpoint with service information.
    
    Returns:
        Service information
    """
    return {
        "service": "AgentGateway",
        "version": "1.0.0",
        "description": "Dual-mode routing and authentication gateway",
        "modes": {
            "api_gateway": {
                "port": settings.api_port,
                "description": "Routes authenticated requests to Application service",
                "endpoints": ["/api/process", "/api/status/{id}", "/api/download/{id}"]
            },
            "mcp_gateway": {
                "port": settings.mcp_port,
                "description": "Routes MCP protocol requests to MCP servers",
                "endpoints": ["/mcp", "/mcp/servers"]
            }
        },
        "features": {
            "jwt_validation": True,
            "rbac": settings.rbac_enabled,
            "department_isolation": settings.department_isolation,
            "audit_logging": True,
            "circuit_breaker": True,
            "retry_logic": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run on API port (8080) by default
    # For MCP mode, run a separate instance on port 8081
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
