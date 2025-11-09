"""S3 client for MCP servers to retrieve department data."""

import logging
import json
from typing import Any, Dict, Optional
import boto3
from botocore.exceptions import ClientError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class MCPS3Client:
    """S3 client for MCP server data retrieval."""
    
    def __init__(
        self,
        bucket_name: str,
        data_prefix: str = "mcp-data/",
        region: str = "ap-southeast-1"
    ):
        """Initialize S3 client.
        
        Args:
            bucket_name: Name of the S3 bucket
            data_prefix: Prefix for MCP data files
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.data_prefix = data_prefix
        self.region = region
        self.s3_client = boto3.client("s3", region_name=region)
        logger.info(
            f"Initialized MCP S3 client for bucket: {bucket_name}, "
            f"prefix: {data_prefix}"
        )
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(ClientError),
        reraise=True
    )
    async def get_json_data(
        self,
        department: str,
        data_type: str
    ) -> Dict[str, Any]:
        """Retrieve JSON data from S3.
        
        Args:
            department: Department name (finance, hr, legal)
            data_type: Type of data to retrieve
            
        Returns:
            Parsed JSON data
            
        Raises:
            ClientError: If retrieval fails
        """
        s3_key = f"{self.data_prefix}{department}/{data_type}.json"
        
        try:
            logger.info(f"Retrieving data from S3: {s3_key}")
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            content = response["Body"].read()
            data = json.loads(content)
            logger.info(f"Successfully retrieved data from {s3_key}")
            return data
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning(f"Data not found: {s3_key}")
                return {}
            logger.error(f"Failed to retrieve data {s3_key}: {e}")
            raise
    
    async def list_data_files(self, department: str) -> list:
        """List available data files for a department.
        
        Args:
            department: Department name
            
        Returns:
            List of data file keys
        """
        prefix = f"{self.data_prefix}{department}/"
        
        try:
            logger.info(f"Listing data files with prefix: {prefix}")
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if "Contents" in response:
                files = [obj["Key"] for obj in response["Contents"]]
            
            logger.info(f"Found {len(files)} data files for {department}")
            return files
        except ClientError as e:
            logger.error(f"Failed to list data files: {e}")
            raise
    
    async def data_exists(self, department: str, data_type: str) -> bool:
        """Check if data file exists.
        
        Args:
            department: Department name
            data_type: Type of data
            
        Returns:
            True if file exists, False otherwise
        """
        s3_key = f"{self.data_prefix}{department}/{data_type}.json"
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking data existence {s3_key}: {e}")
            raise
