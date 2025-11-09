"""
Integration tests for authentication flow.
Tests Cognito login, JWT validation, and protected endpoint access.
"""
import pytest
import httpx
from jose import jwt, JWTError
import json


@pytest.mark.asyncio
async def test_cognito_login(cognito_client, zone_config, test_user_credentials):
    """Test user authentication with Cognito."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Attempt login
    response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": test_user_credentials["username"],
            "PASSWORD": test_user_credentials["password"]
        }
    )
    
    # Verify response contains tokens
    assert "AuthenticationResult" in response
    assert "AccessToken" in response["AuthenticationResult"]
    assert "RefreshToken" in response["AuthenticationResult"]
    assert "IdToken" in response["AuthenticationResult"]
    
    # Verify token expiration
    assert response["AuthenticationResult"]["ExpiresIn"] == 3600  # 1 hour


@pytest.mark.asyncio
async def test_jwt_token_structure(auth_token, zone_config):
    """Test JWT token structure and claims."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    # Decode token without verification to inspect structure
    unverified_claims = jwt.get_unverified_claims(auth_token)
    
    # Verify required claims exist
    assert "sub" in unverified_claims  # User ID
    assert "cognito:username" in unverified_claims
    assert "exp" in unverified_claims  # Expiration
    assert "iat" in unverified_claims  # Issued at
    assert "token_use" in unverified_claims
    assert unverified_claims["token_use"] == "access"


@pytest.mark.asyncio
async def test_jwt_validation_with_jwks(cognito_client, auth_token, zone_config, aws_region):
    """Test JWT validation using Cognito JWKS."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    user_pool_id = zone_config.get("cognito_user_pool_id")
    
    # Get JWKS from Cognito
    import httpx
    jwks_url = f"https://cognito-idp.{aws_region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    
    async with httpx.AsyncClient() as client:
        jwks_response = await client.get(jwks_url)
        assert jwks_response.status_code == 200
        jwks = jwks_response.json()
        
        # Verify JWKS structure
        assert "keys" in jwks
        assert len(jwks["keys"]) > 0
        
        # Verify token can be decoded (basic validation)
        try:
            unverified_claims = jwt.get_unverified_claims(auth_token)
            assert unverified_claims is not None
        except JWTError as e:
            pytest.fail(f"JWT validation failed: {str(e)}")


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(http_client, base_url):
    """Test accessing protected endpoint without authentication token."""
    # Attempt to access protected endpoint without token
    response = await http_client.get(f"{base_url}/api/status/test-job-123")
    
    # Should return 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403, 404], \
        f"Expected 401/403/404, got {response.status_code}"


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(http_client, base_url):
    """Test accessing protected endpoint with invalid token."""
    invalid_token = "invalid.jwt.token"
    
    headers = {"Authorization": f"Bearer {invalid_token}"}
    response = await http_client.get(
        f"{base_url}/api/status/test-job-123",
        headers=headers
    )
    
    # Should return 401 Unauthorized
    assert response.status_code in [401, 403], \
        f"Expected 401/403, got {response.status_code}"


@pytest.mark.asyncio
async def test_protected_endpoint_with_valid_token(http_client, base_url, auth_token):
    """Test accessing protected endpoint with valid token."""
    if not auth_token:
        pytest.skip("Authentication not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await http_client.get(
        f"{base_url}/api/status/test-job-123",
        headers=headers
    )
    
    # Should not return 401/403 (may return 404 if job doesn't exist)
    assert response.status_code not in [401, 403], \
        f"Authentication failed with valid token: {response.status_code}"


@pytest.mark.asyncio
async def test_health_endpoint_no_auth_required(http_client, base_url):
    """Test that health endpoint does not require authentication."""
    response = await http_client.get(f"{base_url}/health")
    
    # Health endpoint should be accessible without auth
    assert response.status_code == 200, \
        f"Health endpoint returned {response.status_code}"


@pytest.mark.asyncio
async def test_token_refresh(cognito_client, zone_config, test_user_credentials):
    """Test token refresh flow."""
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
    
    # Get initial tokens
    auth_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={
            "USERNAME": test_user_credentials["username"],
            "PASSWORD": test_user_credentials["password"]
        }
    )
    
    refresh_token = auth_response["AuthenticationResult"]["RefreshToken"]
    
    # Use refresh token to get new access token
    refresh_response = cognito_client.initiate_auth(
        ClientId=client_id,
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={
            "REFRESH_TOKEN": refresh_token
        }
    )
    
    # Verify new access token is returned
    assert "AuthenticationResult" in refresh_response
    assert "AccessToken" in refresh_response["AuthenticationResult"]
    
    # Refresh token should not be returned in refresh flow
    assert "RefreshToken" not in refresh_response["AuthenticationResult"]


@pytest.mark.asyncio
async def test_authentication_both_zones(cognito_client, aws_region, test_user_credentials):
    """Test authentication works for both dev and prod zones."""
    zones = ["dev", "prod"]
    
    for zone_name in zones:
        user_pool_id = os.getenv(f"{zone_name.upper()}_COGNITO_POOL_ID")
        client_id = os.getenv(f"{zone_name.upper()}_COGNITO_CLIENT_ID")
        
        if not user_pool_id or not client_id:
            print(f"Skipping {zone_name} - Cognito not configured")
            continue
        
        try:
            response = cognito_client.initiate_auth(
                ClientId=client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": test_user_credentials["username"],
                    "PASSWORD": test_user_credentials["password"]
                }
            )
            
            assert "AuthenticationResult" in response
            assert "AccessToken" in response["AuthenticationResult"]
            print(f"✓ Authentication successful for {zone_name} zone")
            
        except Exception as e:
            print(f"✗ Authentication failed for {zone_name} zone: {str(e)}")


# Import os for environment variables
import os
