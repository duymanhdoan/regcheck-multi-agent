"""
Custom Langflow Component for S3 File Operations
"""
from langflow.custom import Component
from langflow.io import MessageTextInput, Output, FileInput
from langflow.schema import Data
import boto3
from botocore.exceptions import ClientError
import os


class S3OperationsComponent(Component):
    display_name = "S3 File Operations"
    description = "Upload and download files from S3"
    icon = "database"
    
    inputs = [
        MessageTextInput(
            name="bucket_name",
            display_name="S3 Bucket Name",
            info="Name of the S3 bucket",
            required=True
        ),
        MessageTextInput(
            name="operation",
            display_name="Operation",
            info="S3 operation to perform",
            value="upload",
            options=["upload", "download", "list", "delete"]
        ),
        FileInput(
            name="file_path",
            display_name="File Path",
            info="Local file path for upload/download operations"
        ),
        MessageTextInput(
            name="s3_key",
            display_name="S3 Key",
            info="S3 object key (path in bucket)",
            required=True
        ),
        MessageTextInput(
            name="prefix",
            display_name="Prefix",
            info="Prefix for list operations (e.g., uploads/, processed/)",
            value="uploads/"
        )
    ]
    
    outputs = [
        Output(display_name="Result", name="result", method="perform_operation")
    ]
    
    def perform_operation(self) -> Data:
        """Perform S3 operation"""
        try:
            # Initialize S3 client (uses IAM role credentials from ECS task)
            s3_client = boto3.client('s3', region_name=os.getenv('AWS_REGION', 'ap-southeast-1'))
            
            if self.operation == "upload":
                return self._upload_file(s3_client)
            elif self.operation == "download":
                return self._download_file(s3_client)
            elif self.operation == "list":
                return self._list_objects(s3_client)
            elif self.operation == "delete":
                return self._delete_object(s3_client)
            else:
                return Data(
                    data={
                        "error": f"Unknown operation: {self.operation}",
                        "success": False
                    }
                )
        except ClientError as e:
            return Data(
                data={
                    "error": f"S3 error: {str(e)}",
                    "success": False
                }
            )
        except Exception as e:
            return Data(
                data={
                    "error": f"Unexpected error: {str(e)}",
                    "success": False
                }
            )
    
    def _upload_file(self, s3_client) -> Data:
        """Upload file to S3"""
        if not self.file_path:
            return Data(data={"error": "File path required for upload", "success": False})
        
        s3_client.upload_file(self.file_path, self.bucket_name, self.s3_key)
        
        return Data(
            data={
                "message": f"File uploaded successfully to s3://{self.bucket_name}/{self.s3_key}",
                "bucket": self.bucket_name,
                "key": self.s3_key,
                "success": True
            }
        )
    
    def _download_file(self, s3_client) -> Data:
        """Download file from S3"""
        if not self.file_path:
            return Data(data={"error": "File path required for download", "success": False})
        
        s3_client.download_file(self.bucket_name, self.s3_key, self.file_path)
        
        return Data(
            data={
                "message": f"File downloaded successfully from s3://{self.bucket_name}/{self.s3_key}",
                "local_path": self.file_path,
                "success": True
            }
        )
    
    def _list_objects(self, s3_client) -> Data:
        """List objects in S3 bucket"""
        response = s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=self.prefix,
            MaxKeys=100
        )
        
        objects = []
        if 'Contents' in response:
            objects = [
                {
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "last_modified": obj['LastModified'].isoformat()
                }
                for obj in response['Contents']
            ]
        
        return Data(
            data={
                "objects": objects,
                "count": len(objects),
                "success": True
            }
        )
    
    def _delete_object(self, s3_client) -> Data:
        """Delete object from S3"""
        s3_client.delete_object(Bucket=self.bucket_name, Key=self.s3_key)
        
        return Data(
            data={
                "message": f"Object deleted successfully: s3://{self.bucket_name}/{self.s3_key}",
                "success": True
            }
        )
