"""S3 client for file operations with retry logic."""

import logging
from typing import Optional
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client with download, upload, and presigned URL generation."""
    
    def __init__(self, bucket_name: str, region: str = "ap-southeast-1"):
        """Initialize S3 client.
        
        Args:
            bucket_name: Name of the S3 bucket
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = boto3.client("s3", region_name=region)
        logger.info(f"Initialized S3 client for bucket: {bucket_name}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    async def download_file(self, s3_key: str) -> bytes:
        """Download file from S3 with retry logic.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            File content as bytes
            
        Raises:
            ClientError: If download fails after retries
        """
        try:
            logger.info(f"Downloading file from S3: {s3_key}")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            content = response["Body"].read()
            logger.info(f"Successfully downloaded {len(content)} bytes from {s3_key}")
            return content
        except ClientError as e:
            logger.error(f"Failed to download file {s3_key}: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    async def upload_file(
        self,
        content: bytes,
        s3_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """Upload file to S3 with retry logic.
        
        Args:
            content: File content as bytes
            s3_key: S3 object key
            content_type: MIME type of the file
            
        Returns:
            S3 key of uploaded file
            
        Raises:
            ClientError: If upload fails after retries
        """
        try:
            logger.info(f"Uploading file to S3: {s3_key}")
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=content,
                ContentType=content_type,
                ServerSideEncryption="AES256"
            )
            logger.info(f"Successfully uploaded {len(content)} bytes to {s3_key}")
            return s3_key
        except ClientError as e:
            logger.error(f"Failed to upload file {s3_key}: {e}")
            raise
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file download.
        
        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Presigned URL
            
        Raises:
            ClientError: If URL generation fails
        """
        try:
            logger.info(f"Generating presigned URL for {s3_key}")
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_key
                },
                ExpiresIn=expiration
            )
            logger.info(f"Generated presigned URL for {s3_key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            raise
    
    async def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking file existence {s3_key}: {e}")
            raise
    
    async def delete_file(self, s3_key: str) -> None:
        """Delete file from S3.
        
        Args:
            s3_key: S3 object key
            
        Raises:
            ClientError: If deletion fails
        """
        try:
            logger.info(f"Deleting file from S3: {s3_key}")
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Successfully deleted {s3_key}")
        except ClientError as e:
            logger.error(f"Failed to delete file {s3_key}: {e}")
            raise
