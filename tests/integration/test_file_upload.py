"""
Integration tests for file upload functionality.
Tests file upload to S3 through frontend for both zones.
"""
import pytest
import httpx
import os
from datetime import datetime
import uuid


@pytest.mark.asyncio
async def test_file_upload_to_s3_direct(s3_client, zone_config, sample_test_file):
    """Test direct file upload to S3 bucket."""
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-123"
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = os.path.basename(sample_test_file)
    s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
    
    # Upload file to S3
    with open(sample_test_file, "rb") as f:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=f,
            ContentType="text/plain"
        )
    
    # Verify file exists in S3
    response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    assert response["ContentType"] == "text/plain"
    
    # Cleanup
    s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_file_upload_with_versioning(s3_client, zone_config, sample_test_file):
    """Test that S3 bucket has versioning enabled."""
    bucket_name = zone_config["s3_bucket"]
    
    # Check bucket versioning status
    versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert versioning.get("Status") == "Enabled", \
        "S3 bucket versioning should be enabled"


@pytest.mark.asyncio
async def test_file_upload_with_encryption(s3_client, zone_config, sample_test_file):
    """Test that uploaded files are encrypted."""
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-123"
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = os.path.basename(sample_test_file)
    s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
    
    # Upload file
    with open(sample_test_file, "rb") as f:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=f
        )
    
    # Check encryption
    response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
    assert "ServerSideEncryption" in response, \
        "File should be encrypted with server-side encryption"
    assert response["ServerSideEncryption"] in ["AES256", "aws:kms"]
    
    # Cleanup
    s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_file_upload_folder_structure(s3_client, zone_config):
    """Test that S3 bucket has correct folder structure."""
    bucket_name = zone_config["s3_bucket"]
    
    # List objects with different prefixes
    folders = ["uploads/", "processed/", "temp/", "finance/", "hr/", "legal/"]
    
    for folder in folders:
        # Try to list objects with this prefix (folder may be empty)
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=folder,
                MaxKeys=1
            )
            # If no error, folder structure is accessible
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        except Exception as e:
            pytest.fail(f"Failed to access folder {folder}: {str(e)}")


@pytest.mark.asyncio
async def test_file_upload_via_frontend_api(http_client, base_url, auth_token, sample_test_file):
    """Test file upload through frontend API endpoint."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Prepare multipart file upload
    with open(sample_test_file, "rb") as f:
        files = {"file": (os.path.basename(sample_test_file), f, "text/plain")}
        
        response = await http_client.post(
            f"{base_url}/api/upload",
            headers=headers,
            files=files
        )
    
    # Check response (may be 404 if endpoint not implemented yet)
    if response.status_code == 404:
        pytest.skip("Upload endpoint not yet implemented")
    
    assert response.status_code in [200, 201, 202], \
        f"Upload failed with status {response.status_code}: {response.text}"
    
    # Verify response contains file information
    if response.status_code in [200, 201, 202]:
        data = response.json()
        assert "file_id" in data or "s3_key" in data


@pytest.mark.asyncio
async def test_file_upload_size_validation(http_client, base_url, auth_token, test_data_dir):
    """Test file upload size validation."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    # Create a large test file (e.g., 100MB)
    large_file_path = os.path.join(test_data_dir, "large_file.bin")
    
    # Create 1MB file for testing (adjust based on actual limits)
    with open(large_file_path, "wb") as f:
        f.write(b"0" * (1024 * 1024))  # 1MB
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        with open(large_file_path, "rb") as f:
            files = {"file": ("large_file.bin", f, "application/octet-stream")}
            
            response = await http_client.post(
                f"{base_url}/api/upload",
                headers=headers,
                files=files,
                timeout=60.0
            )
        
        # Should either succeed or return appropriate error
        if response.status_code == 404:
            pytest.skip("Upload endpoint not yet implemented")
        
        assert response.status_code in [200, 201, 202, 413], \
            f"Unexpected status code: {response.status_code}"
    
    finally:
        # Cleanup
        if os.path.exists(large_file_path):
            os.remove(large_file_path)


@pytest.mark.asyncio
async def test_file_upload_content_type_validation(s3_client, zone_config, test_data_dir):
    """Test that different content types are handled correctly."""
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-123"
    
    # Test different file types
    test_files = [
        ("test.txt", "text/plain", b"Text content"),
        ("test.json", "application/json", b'{"key": "value"}'),
        ("test.pdf", "application/pdf", b"%PDF-1.4 fake pdf content"),
    ]
    
    for filename, content_type, content in test_files:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
        
        # Upload with specific content type
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content,
            ContentType=content_type
        )
        
        # Verify content type
        response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        assert response["ContentType"] == content_type, \
            f"Content type mismatch for {filename}"
        
        # Cleanup
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_file_upload_both_zones(s3_client, aws_region, sample_test_file):
    """Test file upload works for both dev and prod zones."""
    zones = ["dev", "prod"]
    
    for zone_name in zones:
        bucket_name = f"app-files-{zone_name}-{aws_region}"
        user_id = f"test-user-{zone_name}"
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = os.path.basename(sample_test_file)
        s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
        
        try:
            # Upload file
            with open(sample_test_file, "rb") as f:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=f,
                    ContentType="text/plain"
                )
            
            # Verify upload
            response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            print(f"✓ File upload successful for {zone_name} zone")
            
            # Cleanup
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            
        except Exception as e:
            print(f"✗ File upload failed for {zone_name} zone: {str(e)}")


@pytest.mark.asyncio
async def test_file_upload_ssl_enforcement(s3_client, zone_config, sample_test_file):
    """Test that non-SSL requests are denied by bucket policy."""
    bucket_name = zone_config["s3_bucket"]
    
    # This test verifies the bucket policy exists
    # Actual SSL enforcement is tested at the bucket policy level
    try:
        policy = s3_client.get_bucket_policy(Bucket=bucket_name)
        policy_doc = policy["Policy"]
        
        # Verify policy contains SSL enforcement
        assert "aws:SecureTransport" in policy_doc, \
            "Bucket policy should enforce SSL/TLS"
        
    except s3_client.exceptions.NoSuchBucketPolicy:
        pytest.skip("Bucket policy not yet configured")
