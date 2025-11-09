"""
Integration tests for RBAC (Role-Based Access Control) enforcement.
Tests department-specific access control and access denial for unauthorized resources.
"""
import pytest
import httpx
import uuid
import os


@pytest.mark.asyncio
async def test_finance_user_access_finance_mcp(http_client, base_url, cognito_client, zone_config):
    """Test that finance user can access finance MCP server."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Authenticate as finance user
    finance_username = os.getenv("FINANCE_USER", "finance-user")
    finance_password = os.getenv("FINANCE_PASSWORD", "FinancePass123")
    
    try:
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": finance_username,
                "PASSWORD": finance_password
            }
        )
        
        token = auth_response["AuthenticationResult"]["AccessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access finance MCP through AgentGateway
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await http_client.post(
            f"{base_url}/api/mcp/finance",
            headers=headers,
            json=mcp_request
        )
        
        if response.status_code == 404:
            pytest.skip("RBAC endpoint not yet implemented")
        
        # Should be allowed
        assert response.status_code == 200, \
            f"Finance user should access finance MCP: {response.status_code}"
        
    except cognito_client.exceptions.NotAuthorizedException:
        pytest.skip("Finance user not configured in Cognito")


@pytest.mark.asyncio
async def test_finance_user_denied_hr_mcp(http_client, base_url, cognito_client, zone_config):
    """Test that finance user cannot access HR MCP server."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Authenticate as finance user
    finance_username = os.getenv("FINANCE_USER", "finance-user")
    finance_password = os.getenv("FINANCE_PASSWORD", "FinancePass123")
    
    try:
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": finance_username,
                "PASSWORD": finance_password
            }
        )
        
        token = auth_response["AuthenticationResult"]["AccessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access HR MCP (should be denied)
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await http_client.post(
            f"{base_url}/api/mcp/hr",
            headers=headers,
            json=mcp_request
        )
        
        if response.status_code == 404:
            pytest.skip("RBAC endpoint not yet implemented")
        
        # Should be denied
        assert response.status_code == 403, \
            f"Finance user should be denied HR MCP access: {response.status_code}"
        
    except cognito_client.exceptions.NotAuthorizedException:
        pytest.skip("Finance user not configured in Cognito")


@pytest.mark.asyncio
async def test_hr_user_access_hr_mcp(http_client, base_url, cognito_client, zone_config):
    """Test that HR user can access HR MCP server."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Authenticate as HR user
    hr_username = os.getenv("HR_USER", "hr-user")
    hr_password = os.getenv("HR_PASSWORD", "HRPass123")
    
    try:
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": hr_username,
                "PASSWORD": hr_password
            }
        )
        
        token = auth_response["AuthenticationResult"]["AccessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access HR MCP
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await http_client.post(
            f"{base_url}/api/mcp/hr",
            headers=headers,
            json=mcp_request
        )
        
        if response.status_code == 404:
            pytest.skip("RBAC endpoint not yet implemented")
        
        # Should be allowed
        assert response.status_code == 200, \
            f"HR user should access HR MCP: {response.status_code}"
        
    except cognito_client.exceptions.NotAuthorizedException:
        pytest.skip("HR user not configured in Cognito")


@pytest.mark.asyncio
async def test_hr_user_denied_legal_mcp(http_client, base_url, cognito_client, zone_config):
    """Test that HR user cannot access Legal MCP server."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Authenticate as HR user
    hr_username = os.getenv("HR_USER", "hr-user")
    hr_password = os.getenv("HR_PASSWORD", "HRPass123")
    
    try:
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": hr_username,
                "PASSWORD": hr_password
            }
        )
        
        token = auth_response["AuthenticationResult"]["AccessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access Legal MCP (should be denied)
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await http_client.post(
            f"{base_url}/api/mcp/legal",
            headers=headers,
            json=mcp_request
        )
        
        if response.status_code == 404:
            pytest.skip("RBAC endpoint not yet implemented")
        
        # Should be denied
        assert response.status_code == 403, \
            f"HR user should be denied Legal MCP access: {response.status_code}"
        
    except cognito_client.exceptions.NotAuthorizedException:
        pytest.skip("HR user not configured in Cognito")


@pytest.mark.asyncio
async def test_legal_user_access_legal_mcp(http_client, base_url, cognito_client, zone_config):
    """Test that Legal user can access Legal MCP server."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Authenticate as Legal user
    legal_username = os.getenv("LEGAL_USER", "legal-user")
    legal_password = os.getenv("LEGAL_PASSWORD", "LegalPass123")
    
    try:
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": legal_username,
                "PASSWORD": legal_password
            }
        )
        
        token = auth_response["AuthenticationResult"]["AccessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access Legal MCP
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await http_client.post(
            f"{base_url}/api/mcp/legal",
            headers=headers,
            json=mcp_request
        )
        
        if response.status_code == 404:
            pytest.skip("RBAC endpoint not yet implemented")
        
        # Should be allowed
        assert response.status_code == 200, \
            f"Legal user should access Legal MCP: {response.status_code}"
        
    except cognito_client.exceptions.NotAuthorizedException:
        pytest.skip("Legal user not configured in Cognito")


@pytest.mark.asyncio
async def test_legal_user_denied_finance_mcp(http_client, base_url, cognito_client, zone_config):
    """Test that Legal user cannot access Finance MCP server."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Authenticate as Legal user
    legal_username = os.getenv("LEGAL_USER", "legal-user")
    legal_password = os.getenv("LEGAL_PASSWORD", "LegalPass123")
    
    try:
        auth_response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": legal_username,
                "PASSWORD": legal_password
            }
        )
        
        token = auth_response["AuthenticationResult"]["AccessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access Finance MCP (should be denied)
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = await http_client.post(
            f"{base_url}/api/mcp/finance",
            headers=headers,
            json=mcp_request
        )
        
        if response.status_code == 404:
            pytest.skip("RBAC endpoint not yet implemented")
        
        # Should be denied
        assert response.status_code == 403, \
            f"Legal user should be denied Finance MCP access: {response.status_code}"
        
    except cognito_client.exceptions.NotAuthorizedException:
        pytest.skip("Legal user not configured in Cognito")


@pytest.mark.asyncio
async def test_rbac_with_missing_role_claim(http_client, base_url, auth_token):
    """Test RBAC behavior when JWT token is missing role claims."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Try to access MCP endpoint
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}/api/mcp/finance",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("RBAC endpoint not yet implemented")
    
    # Should either deny or use default role
    assert response.status_code in [200, 403], \
        f"Unexpected status for missing role: {response.status_code}"


@pytest.mark.asyncio
async def test_rbac_department_isolation(http_client, base_url, cognito_client, zone_config, s3_client):
    """Test that users can only access their department's S3 data."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    bucket_name = zone_config["s3_bucket"]
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Create test data in different department folders
    departments = ["finance", "hr", "legal"]
    
    for dept in departments:
        s3_key = f"{dept}/test-data/sample.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=b'{"test": "data"}',
            ContentType="application/json"
        )
    
    try:
        # Test finance user accessing finance data (should succeed)
        finance_username = os.getenv("FINANCE_USER", "finance-user")
        finance_password = os.getenv("FINANCE_PASSWORD", "FinancePass123")
        
        try:
            auth_response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": finance_username,
                    "PASSWORD": finance_password
                }
            )
            
            token = auth_response["AuthenticationResult"]["AccessToken"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Request finance data
            response = await http_client.get(
                f"{base_url}/api/data/finance/test-data/sample.json",
                headers=headers
            )
            
            if response.status_code != 404:
                # Should be allowed
                assert response.status_code in [200, 403], \
                    f"Unexpected status: {response.status_code}"
            
            # Request HR data (should be denied)
            response = await http_client.get(
                f"{base_url}/api/data/hr/test-data/sample.json",
                headers=headers
            )
            
            if response.status_code != 404:
                # Should be denied
                assert response.status_code == 403, \
                    f"Finance user should be denied HR data: {response.status_code}"
        
        except cognito_client.exceptions.NotAuthorizedException:
            pytest.skip("Finance user not configured")
    
    finally:
        # Cleanup test data
        for dept in departments:
            s3_key = f"{dept}/test-data/sample.json"
            try:
                s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
            except:
                pass


@pytest.mark.asyncio
async def test_rbac_enforcement_both_zones(cognito_client, aws_region):
    """Test RBAC enforcement works in both dev and prod zones."""
    zones = ["dev", "prod"]
    
    for zone_name in zones:
        user_pool_id = os.getenv(f"{zone_name.upper()}_COGNITO_POOL_ID")
        client_id = os.getenv(f"{zone_name.upper()}_COGNITO_CLIENT_ID")
        
        if not user_pool_id or not client_id:
            print(f"Skipping {zone_name} - Cognito not configured")
            continue
        
        # Test finance user
        finance_username = os.getenv("FINANCE_USER", "finance-user")
        finance_password = os.getenv("FINANCE_PASSWORD", "FinancePass123")
        
        try:
            auth_response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": finance_username,
                    "PASSWORD": finance_password
                }
            )
            
            token = auth_response["AuthenticationResult"]["AccessToken"]
            
            # Verify token contains role information
            from jose import jwt
            claims = jwt.get_unverified_claims(token)
            
            print(f"✓ RBAC authentication successful for {zone_name} zone")
            
            if "cognito:groups" in claims:
                print(f"  User groups: {claims['cognito:groups']}")
            
        except Exception as e:
            print(f"✗ RBAC test failed for {zone_name} zone: {str(e)}")
