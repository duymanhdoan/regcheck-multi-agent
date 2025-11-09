"""File processing logic with MCP data enrichment."""

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from .s3_client import S3Client
from .mcp_client import MCPClient, MCPClientError
from .models import ProcessingJob

logger = logging.getLogger(__name__)


class FileProcessor:
    """File processor with MCP data enrichment."""
    
    def __init__(
        self,
        s3_client: S3Client,
        mcp_client: MCPClient,
        processing_timeout: int = 300
    ):
        """Initialize file processor.
        
        Args:
            s3_client: S3 client instance
            mcp_client: MCP client instance
            processing_timeout: Processing timeout in seconds
        """
        self.s3_client = s3_client
        self.mcp_client = mcp_client
        self.processing_timeout = processing_timeout
        self.jobs: Dict[str, ProcessingJob] = {}
        logger.info("Initialized file processor")
    
    async def start_processing(
        self,
        file_id: str,
        user_id: str,
        input_s3_key: str,
        mcp_server_type: str,
        mcp_tool_name: str,
        mcp_arguments: Dict[str, Any]
    ) -> ProcessingJob:
        """Start file processing job.
        
        Args:
            file_id: File identifier
            user_id: User identifier
            input_s3_key: Input file S3 key
            mcp_server_type: MCP server type (finance, hr, legal)
            mcp_tool_name: MCP tool to call
            mcp_arguments: Arguments for MCP tool
            
        Returns:
            Processing job
        """
        processing_id = str(uuid.uuid4())
        
        job = ProcessingJob(
            processing_id=processing_id,
            file_id=file_id,
            user_id=user_id,
            status="pending",
            input_s3_key=input_s3_key,
            mcp_server_type=mcp_server_type,
            parameters={
                "mcp_tool_name": mcp_tool_name,
                "mcp_arguments": mcp_arguments
            }
        )
        
        self.jobs[processing_id] = job
        logger.info(f"Created processing job {processing_id}")
        
        # Start processing asynchronously
        try:
            await self._process_file(job)
        except Exception as e:
            logger.error(f"Processing failed for job {processing_id}: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
        
        return job
    
    async def _process_file(self, job: ProcessingJob) -> None:
        """Process file with MCP data enrichment.
        
        Args:
            job: Processing job
        """
        start_time = datetime.utcnow()
        job.status = "processing"
        job.started_at = start_time
        
        try:
            logger.info(f"Processing job {job.processing_id}")
            
            # Step 1: Download file from S3
            logger.info(f"Downloading file: {job.input_s3_key}")
            file_content = await self.s3_client.download_file(job.input_s3_key)
            
            # Step 2: Fetch MCP data
            logger.info(
                f"Fetching MCP data from {job.mcp_server_type} server"
            )
            mcp_tool_name = job.parameters.get("mcp_tool_name")
            mcp_arguments = job.parameters.get("mcp_arguments", {})
            
            mcp_data = await self.mcp_client.call_tool(
                server_type=job.mcp_server_type,
                tool_name=mcp_tool_name,
                arguments=mcp_arguments
            )
            
            # Step 3: Process file with MCP data
            logger.info("Processing file with MCP data")
            processed_content = await self._enrich_file(
                file_content=file_content,
                mcp_data=mcp_data,
                job=job
            )
            
            # Step 4: Upload result to S3
            output_s3_key = self._generate_output_key(job)
            logger.info(f"Uploading result to: {output_s3_key}")
            
            await self.s3_client.upload_file(
                content=processed_content,
                s3_key=output_s3_key,
                content_type="application/json"
            )
            
            # Step 5: Generate presigned download URL
            download_url = self.s3_client.generate_presigned_url(
                s3_key=output_s3_key,
                expiration=3600  # 1 hour
            )
            
            # Update job status
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            job.status = "completed"
            job.output_s3_key = output_s3_key
            job.completed_at = end_time
            job.processing_time_ms = int(processing_time)
            job.download_url = download_url
            job.download_url_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            logger.info(
                f"Processing completed for job {job.processing_id} "
                f"in {processing_time:.0f}ms"
            )
            
        except MCPClientError as e:
            logger.error(f"MCP error for job {job.processing_id}: {e}")
            job.status = "failed"
            job.error_message = f"MCP error: {str(e)}"
            job.completed_at = datetime.utcnow()
            raise
        except Exception as e:
            logger.error(f"Processing error for job {job.processing_id}: {e}")
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            raise
    
    async def _enrich_file(
        self,
        file_content: bytes,
        mcp_data: Dict[str, Any],
        job: ProcessingJob
    ) -> bytes:
        """Enrich file content with MCP data.
        
        Args:
            file_content: Original file content
            mcp_data: Data from MCP server
            job: Processing job
            
        Returns:
            Enriched file content as bytes
        """
        # Create enriched result
        result = {
            "processing_id": job.processing_id,
            "file_id": job.file_id,
            "user_id": job.user_id,
            "mcp_server_type": job.mcp_server_type,
            "processed_at": datetime.utcnow().isoformat(),
            "original_file_size": len(file_content),
            "mcp_data": mcp_data,
            "metadata": {
                "input_s3_key": job.input_s3_key,
                "mcp_tool": job.parameters.get("mcp_tool_name"),
                "mcp_arguments": job.parameters.get("mcp_arguments")
            }
        }
        
        # Convert to JSON bytes
        return json.dumps(result, indent=2).encode("utf-8")
    
    def _generate_output_key(self, job: ProcessingJob) -> str:
        """Generate output S3 key.
        
        Args:
            job: Processing job
            
        Returns:
            Output S3 key
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}-result-{job.file_id}.json"
        return f"processed/{job.user_id}/{filename}"
    
    def get_job_status(self, processing_id: str) -> Optional[ProcessingJob]:
        """Get processing job status.
        
        Args:
            processing_id: Processing job ID
            
        Returns:
            Processing job or None if not found
        """
        return self.jobs.get(processing_id)
    
    async def get_download_url(self, processing_id: str) -> Optional[str]:
        """Get download URL for processed file.
        
        Args:
            processing_id: Processing job ID
            
        Returns:
            Download URL or None if job not found or not completed
        """
        job = self.jobs.get(processing_id)
        if not job or job.status != "completed" or not job.output_s3_key:
            return None
        
        # Check if existing URL is still valid
        if (
            job.download_url
            and job.download_url_expires_at
            and job.download_url_expires_at > datetime.utcnow()
        ):
            return job.download_url
        
        # Generate new presigned URL
        download_url = self.s3_client.generate_presigned_url(
            s3_key=job.output_s3_key,
            expiration=3600
        )
        
        job.download_url = download_url
        job.download_url_expires_at = datetime.utcnow() + timedelta(hours=1)
        
        return download_url
