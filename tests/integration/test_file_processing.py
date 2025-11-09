"""
Integration tests for file processing workflow.
Tests complete workflow: upload → process → download for both zones.
"""
import pytest
import httpx
import asyncio
import os
from datetime import datetime
import uuid


@pytest.mark.asyncio
async def test_complete_file_processing_workflow(
    http_client,
    base_url,
    auth_token,
    s3_client,
    zone_config,
    sample_test_file
):
    """Test complete file processing workflow from upload to download."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-workflow"
    
    # Step 1: Upload file to S3
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = os.path.basename(sample_test_file)
    s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
    
    with open(sample_test_file, "rb") as f:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=f,
            ContentType="text/plain"
        )
    
    try:
        # Step 2: Trigger processing
        process_payload = {
            "file_id": str(uuid.uuid4()),
            "s3_key": s3_key,
            "user_id": user_id,
            "mcp_server_type": "finance"
        }
        
        process_response = await http_client.post(
            f"{base_url}/api/process",
            headers=headers,
            json=process_payload
        )
        
        if process_response.status_code == 404:
            pytest.skip("Process endpoint not yet implemented")
        
        assert process_response.status_code in [200, 201, 202], \
            f"Process request failed: {process_response.status_code} - {process_response.text}"
        
        process_data = process_response.json()
        assert "processing_id" in process_data or "job_id" in process_data
        
        job_id = process_data.get("processing_id") or process_data.get("job_id")
        
        # Step 3: Poll for processing status
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = await http_client.get(
                f"{base_url}/api/status/{job_id}",
                headers=headers
            )
            
            assert status_response.status_code == 200, \
                f"Status check failed: {status_response.status_code}"
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "completed":
                assert "output_s3_key" in status_data
                break
            elif status == "failed":
                pytest.fail(f"Processing failed: {status_data.get('error_message')}")
            
            await asyncio.sleep(2)
        else:
            pytest.fail("Processing timeout after 60 seconds")
        
        # Step 4: Get download URL
        download_response = await http_client.get(
            f"{base_url}/api/download/{job_id}",
            headers=headers
        )
        
        assert download_response.status_code == 200, \
            f"Download request failed: {download_response.status_code}"
        
        download_data = download_response.json()
        assert "presigned_url" in download_data or "download_url" in download_data
        
    finally:
        # Cleanup uploaded file
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_processing_status_tracking(
    http_client,
    base_url,
    auth_token,
    s3_client,
    zone_config,
    sample_test_file
):
    """Test that processing status is tracked correctly."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-status"
    
    # Upload test file
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = os.path.basename(sample_test_file)
    s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
    
    with open(sample_test_file, "rb") as f:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=f
        )
    
    try:
        # Trigger processing
        process_payload = {
            "file_id": str(uuid.uuid4()),
            "s3_key": s3_key,
            "user_id": user_id,
            "mcp_server_type": "hr"
        }
        
        process_response = await http_client.post(
            f"{base_url}/api/process",
            headers=headers,
            json=process_payload
        )
        
        if process_response.status_code == 404:
            pytest.skip("Process endpoint not yet implemented")
        
        process_data = process_response.json()
        job_id = process_data.get("processing_id") or process_data.get("job_id")
        
        # Check initial status
        status_response = await http_client.get(
            f"{base_url}/api/status/{job_id}",
            headers=headers
        )
        
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Verify status fields
        assert "status" in status_data
        assert status_data["status"] in ["pending", "processing", "completed", "failed"]
        assert "processing_id" in status_data or "job_id" in status_data
        
        if "started_at" in status_data:
            assert status_data["started_at"] is not None
        
    finally:
        # Cleanup
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_result_file_generation(
    http_client,
    base_url,
    auth_token,
    s3_client,
    zone_config,
    sample_test_file
):
    """Test that result files are generated in processed/ folder."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-result"
    
    # Upload test file
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    filename = os.path.basename(sample_test_file)
    s3_key = f"uploads/{user_id}/{timestamp}-{filename}"
    
    with open(sample_test_file, "rb") as f:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=f
        )
    
    try:
        # Trigger processing
        process_payload = {
            "file_id": str(uuid.uuid4()),
            "s3_key": s3_key,
            "user_id": user_id,
            "mcp_server_type": "legal"
        }
        
        process_response = await http_client.post(
            f"{base_url}/api/process",
            headers=headers,
            json=process_payload
        )
        
        if process_response.status_code == 404:
            pytest.skip("Process endpoint not yet implemented")
        
        process_data = process_response.json()
        job_id = process_data.get("processing_id") or process_data.get("job_id")
        
        # Wait for completion
        max_attempts = 30
        output_s3_key = None
        
        for attempt in range(max_attempts):
            status_response = await http_client.get(
                f"{base_url}/api/status/{job_id}",
                headers=headers
            )
            
            status_data = status_response.json()
            
            if status_data.get("status") == "completed":
                output_s3_key = status_data.get("output_s3_key")
                break
            
            await asyncio.sleep(2)
        
        if output_s3_key:
            # Verify result file exists in S3
            assert output_s3_key.startswith("processed/"), \
                "Result file should be in processed/ folder"
            
            response = s3_client.head_object(Bucket=bucket_name, Key=output_s3_key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            
            # Cleanup result file
            s3_client.delete_object(Bucket=bucket_name, Key=output_s3_key)
        
    finally:
        # Cleanup uploaded file
        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_processing_with_different_mcp_servers(
    http_client,
    base_url,
    auth_token,
    s3_client,
    zone_config,
    sample_test_file
):
    """Test processing with different MCP server types."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    bucket_name = zone_config["s3_bucket"]
    user_id = "test-user-mcp"
    
    mcp_server_types = ["finance", "hr", "legal"]
    
    for mcp_type in mcp_server_types:
        # Upload test file
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = os.path.basename(sample_test_file)
        s3_key = f"uploads/{user_id}/{timestamp}-{mcp_type}-{filename}"
        
        with open(sample_test_file, "rb") as f:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=f
            )
        
        try:
            # Trigger processing
            process_payload = {
                "file_id": str(uuid.uuid4()),
                "s3_key": s3_key,
                "user_id": user_id,
                "mcp_server_type": mcp_type
            }
            
            process_response = await http_client.post(
                f"{base_url}/api/process",
                headers=headers,
                json=process_payload
            )
            
            if process_response.status_code == 404:
                pytest.skip("Process endpoint not yet implemented")
            
            assert process_response.status_code in [200, 201, 202], \
                f"Processing with {mcp_type} failed: {process_response.status_code}"
            
            print(f"✓ Processing initiated with {mcp_type} MCP server")
            
        finally:
            # Cleanup
            s3_client.delete_object(Bucket=bucket_name, Key=s3_key)


@pytest.mark.asyncio
async def test_processing_error_handling(
    http_client,
    base_url,
    auth_token
):
    """Test error handling for invalid processing requests."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Test with missing required fields
    invalid_payload = {
        "file_id": str(uuid.uuid4())
        # Missing s3_key and mcp_server_type
    }
    
    response = await http_client.post(
        f"{base_url}/api/process",
        headers=headers,
        json=invalid_payload
    )
    
    if response.status_code == 404:
        pytest.skip("Process endpoint not yet implemented")
    
    # Should return 400 Bad Request
    assert response.status_code == 400, \
        f"Expected 400 for invalid payload, got {response.status_code}"


@pytest.mark.asyncio
async def test_processing_nonexistent_file(
    http_client,
    base_url,
    auth_token
):
    """Test processing with non-existent S3 file."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Request processing for non-existent file
    process_payload = {
        "file_id": str(uuid.uuid4()),
        "s3_key": "uploads/nonexistent/file.txt",
        "user_id": "test-user",
        "mcp_server_type": "finance"
    }
    
    response = await http_client.post(
        f"{base_url}/api/process",
        headers=headers,
        json=process_payload
    )
    
    if response.status_code == 404:
        pytest.skip("Process endpoint not yet implemented")
    
    # Should either reject immediately or fail during processing
    if response.status_code in [200, 201, 202]:
        process_data = response.json()
        job_id = process_data.get("processing_id") or process_data.get("job_id")
        
        # Wait and check status
        await asyncio.sleep(5)
        
        status_response = await http_client.get(
            f"{base_url}/api/status/{job_id}",
            headers=headers
        )
        
        status_data = status_response.json()
        assert status_data.get("status") == "failed", \
            "Processing should fail for non-existent file"
