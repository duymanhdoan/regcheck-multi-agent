"""HR MCP server main entry point."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from ..base.config import settings
from ..base.s3_client import MCPS3Client
from ..base.models import MCPRequest, MCPResponse
from .hr_server import HRMCPServer

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
s3_client: MCPS3Client = None
mcp_server: HRMCPServer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global s3_client, mcp_server
    
    # Startup
    logger.info("Starting HR MCP server")
    
    # Initialize S3 client
    s3_client = MCPS3Client(
        bucket_name=settings.s3_bucket_name,
        data_prefix=settings.s3_data_prefix,
        region=settings.aws_region
    )
    
    # Initialize MCP server
    mcp_server = HRMCPServer(s3_client=s3_client)
    
    logger.info("HR MCP server initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down HR MCP server")


# Create FastAPI app
app = FastAPI(
    title="HR MCP Server",
    description="MCP server for HR department data and tools",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "server_type": "hr",
        "version": "1.0.0"
    }


@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
    """Handle MCP JSON-RPC request.
    
    Args:
        request: MCP request
        
    Returns:
        MCP response
    """
    logger.info(f"Received MCP request: {request.method}")
    response = await mcp_server.handle_request(request)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler.
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(exc)}"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.server_port,
        log_level=settings.log_level.lower()
    )
