"""Run AgentGateway in dual mode (both API and MCP ports)."""
import asyncio
import logging
import signal
import sys
from multiprocessing import Process
import uvicorn

from .config import settings


def run_api_gateway():
    """Run API Gateway mode on port 8080."""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        access_log=True
    )


def run_mcp_gateway():
    """Run MCP Gateway mode on port 8081."""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.mcp_port,
        log_level=settings.log_level.lower(),
        access_log=True
    )


def main():
    """Run both API and MCP gateway modes."""
    logger = logging.getLogger(__name__)
    logger.info("Starting AgentGateway in dual mode")
    
    # Start API Gateway process
    api_process = Process(target=run_api_gateway, name="API-Gateway")
    api_process.start()
    logger.info(f"API Gateway started on port {settings.api_port}")
    
    # Start MCP Gateway process
    mcp_process = Process(target=run_mcp_gateway, name="MCP-Gateway")
    mcp_process.start()
    logger.info(f"MCP Gateway started on port {settings.mcp_port}")
    
    # Handle shutdown signals
    def signal_handler(signum, frame):
        logger.info("Received shutdown signal, stopping processes...")
        api_process.terminate()
        mcp_process.terminate()
        api_process.join(timeout=5)
        mcp_process.join(timeout=5)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait for processes
    try:
        api_process.join()
        mcp_process.join()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, stopping processes...")
        api_process.terminate()
        mcp_process.terminate()
        api_process.join(timeout=5)
        mcp_process.join(timeout=5)


if __name__ == "__main__":
    main()
