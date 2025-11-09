"""
Pytest configuration and fixtures for integration tests.
"""
import pytest
import os
import httpx
import boto3
from typing import Dict, Optional
from datetime import datetime, timedelta
import json


@pytest.fixture(scope="session")
def zone(request) -> str:
    """Get the zone to test from command line or default to 'dev'."""
    return request.config.getoption("--zone", default="dev")


@pytest.fixture(scope="session")
def aws_region() -> str:
    """AWS region for testing."""
    return os.getenv("AWS_REGION", "ap-southeast-1")


@pytest.fixture(scope="session")
def zone_config(zone: str, aws_region: str) -> Dict[str, str]:
    """Configuration for the specified zone."""
    configs = {
        "dev": {
            "environment": "dev",
            "nlb_dns": os.getenv("DEV_NLB_DNS", "dev-nlb-ap-southeast-1-74695198f37969d8.elb.ap-southeast-1.amazonaws.com"),
            "s3_bucket": f"app-files-dev-{aws_region}",
            "cognito_user_pool_id": os.getenv("DEV_COGNITO_POOL_ID", ""),
            "cognito_client_id": os.getenv("DEV_COGNITO_CLIENT_ID", ""),
            "availability_zone": "ap-southeast-1a"
        },
        "prod": {
            "environment": "prod",
            "nlb_dns": os.getenv("PROD_NLB_DNS", ""),
            "s3_bucket": f"app-files-prod-{aws_region}",
            "cognito_user_pool_id": os.getenv("PROD_COGNITO_POOL_ID", ""),
            "cognito_client_id": os.getenv("PROD_COGNITO_CLIENT_ID", ""),
            "availability_zone": "ap-southeast-1b"
        }
    }
    return configs.get(zone, configs["dev"])


@pytest.fixture(scope="session")
def global_nlb_dns() -> str:
    """Global NLB DNS name."""
    return os.getenv("GLOBAL_NLB_DNS", "")


@pytest.fixture
async def http_client():
    """Async HTTP client for making requests."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def s3_client(aws_region: str):
    """S3 client for file operations."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="session")
def cognito_client(aws_region: str):
    """Cognito client for authentication."""
    return boto3.client("cognito-idp", region_name=aws_region)


@pytest.fixture(scope="session")
def ecs_client(aws_region: str):
    """ECS client for service operations."""
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture
def test_user_credentials() -> Dict[str, str]:
    """Test user credentials for authentication."""
    return {
        "username": os.getenv("TEST_USERNAME", "test-user"),
        "password": os.getenv("TEST_PASSWORD", "TestPassword123"),
        "department": os.getenv("TEST_DEPARTMENT", "finance")
    }


@pytest.fixture
def test_file_path() -> str:
    """Path to test file for upload tests."""
    return os.path.join(os.path.dirname(__file__), "test_data", "sample.txt")


@pytest.fixture(scope="session")
def service_token() -> str:
    """Service token for MCP gateway authentication."""
    return os.getenv("SERVICE_TOKEN", "test-service-token")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--zone",
        action="store",
        default="dev",
        help="Zone to test: dev or prod"
    )
    parser.addoption(
        "--global-nlb",
        action="store_true",
        default=False,
        help="Test through Global NLB instead of zone NLB"
    )


@pytest.fixture
def use_global_nlb(request) -> bool:
    """Whether to use Global NLB for testing."""
    return request.config.getoption("--global-nlb")


@pytest.fixture
def base_url(zone_config: Dict[str, str], global_nlb_dns: str, use_global_nlb: bool) -> str:
    """Base URL for API requests."""
    if use_global_nlb and global_nlb_dns:
        return f"http://{global_nlb_dns}"
    return f"http://{zone_config['nlb_dns']}"


@pytest.fixture
async def auth_token(
    cognito_client,
    zone_config: Dict[str, str],
    test_user_credentials: Dict[str, str]
) -> Optional[str]:
    """
    Authenticate and return JWT token.
    Returns None if Cognito is not configured.
    """
    user_pool_id = zone_config.get("cognito_user_pool_id")
    client_id = zone_config.get("cognito_client_id")
    
    if not user_pool_id or not client_id:
        pytest.skip("Cognito not configured for this zone")
        return None
    
    try:
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": test_user_credentials["username"],
                "PASSWORD": test_user_credentials["password"]
            }
        )
        return response["AuthenticationResult"]["AccessToken"]
    except Exception as e:
        pytest.skip(f"Failed to authenticate: {str(e)}")
        return None


@pytest.fixture
def test_data_dir() -> str:
    """Directory containing test data files."""
    data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_test_file(test_data_dir: str) -> str:
    """Create a sample test file and return its path."""
    file_path = os.path.join(test_data_dir, "sample.txt")
    with open(file_path, "w") as f:
        f.write("This is a test file for integration testing.\n")
        f.write(f"Created at: {datetime.utcnow().isoformat()}\n")
        f.write("Test data content for file processing.\n")
    return file_path
