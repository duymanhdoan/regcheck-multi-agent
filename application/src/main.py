"""Main FastAPI application for file processing service."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from .config import settings
from .s3_client import S3Client
from .mcp_client import MCPClient
from .processor import FileProcessor
from .models import (
    ProcessRequest,
    ProcessResponse,
    StatusResponse,
    DownloadResponse
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
s3_client: S3Client = None
mcp_client: MCPClient = None
processor: FileProcessor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global s3_client, mcp_client, processor
    
    # Startup
    logger.info(f"Starting {settings.service_name} service")
    
    # Initialize clients
    s3_client = S3Client(
        bucket_name=settings.s3_bucket_name,
        region=settings.aws_region
    )
    
    mcp_client = MCPClient(
        agentgateway_url=settings.agentgateway_mcp_url,
        service_token=settings.service_token,
        timeout=30
    )
    
    processor = FileProcessor(
        s3_client=s3_client,
        mcp_client=mcp_client,
        processing_timeout=settings.processing_timeout
    )
    
    logger.info("Application initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title="Application Service",
    description="File processing service with MCP data enrichment",
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
        "service": settings.service_name,
        "version": "1.0.0"
    }


@app.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def process_file(request: ProcessRequest):
    """Start file processing.
    
    Args:
        request: Processing request
        
    Returns:
        Processing response with job ID
        
    Raises:
        HTTPException: If processing fails to start
    """
    try:
        logger.info(
            f"Received processing request for file {request.file_id} "
            f"from user {request.user_id}"
        )
        
        # Validate MCP server type
        valid_server_types = ["finance", "hr", "legal"]
        if request.mcp_server_type not in valid_server_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid MCP server type. Must be one of: {valid_server_types}"
            )
        
        # Start processing
        job = await processor.start_processing(
            file_id=request.file_id,
            user_id=request.user_id,
            input_s3_key=request.input_s3_key,
            mcp_server_type=request.mcp_server_type,
            mcp_tool_name=request.mcp_tool_name,
            mcp_arguments=request.mcp_arguments
        )
        
        logger.info(f"Started processing job {job.processing_id}")
        
        return ProcessResponse(
            processing_id=job.processing_id,
            status=job.status,
            message="Processing started successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start processing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )


@app.get("/status/{processing_id}", response_model=StatusResponse)
async def get_status(processing_id: str):
    """Get processing job status.
    
    Args:
        processing_id: Processing job ID
        
    Returns:
        Job status
        
    Raises:
        HTTPException: If job not found
    """
    try:
        logger.info(f"Status check for job {processing_id}")
        
        job = processor.get_job_status(processing_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing job {processing_id} not found"
            )
        
        return StatusResponse(
            processing_id=job.processing_id,
            status=job.status,
            started_at=job.started_at,
            completed_at=job.completed_at,
            processing_time_ms=job.processing_time_ms,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )


@app.get("/download/{processing_id}", response_model=DownloadResponse)
async def get_download_url(processing_id: str):
    """Get presigned download URL for processed file.
    
    Args:
        processing_id: Processing job ID
        
    Returns:
        Download URL
        
    Raises:
        HTTPException: If job not found or not completed
    """
    try:
        logger.info(f"Download URL request for job {processing_id}")
        
        job = processor.get_job_status(processing_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Processing job {processing_id} not found"
            )
        
        if job.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Processing job {processing_id} is not completed. Status: {job.status}"
            )
        
        download_url = await processor.get_download_url(processing_id)
        
        if not download_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate download URL"
            )
        
        return DownloadResponse(
            processing_id=job.processing_id,
            download_url=download_url,
            expires_at=job.download_url_expires_at,
            output_s3_key=job.output_s3_key
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download URL: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler.
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        Error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        log_level=settings.log_level.lower()
    )
