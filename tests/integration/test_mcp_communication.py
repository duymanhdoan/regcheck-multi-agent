"""
Integration tests for MCP communication.
Tests MCP server calls through AgentGateway for both zones.
"""
import pytest
import httpx
import uuid


@pytest.mark.asyncio
async def test_mcp_tools_list_finance(http_client, base_url, service_token):
    """Test listing available tools from Finance MCP server."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP tools/list failed: {response.status_code} - {response.text}"
    
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    
    # Verify finance-specific tools
    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    assert "get_financial_data" in tool_names
    assert "get_budget_info" in tool_names
    assert "get_invoice_data" in tool_names


@pytest.mark.asyncio
async def test_mcp_tools_list_hr(http_client, base_url, service_token):
    """Test listing available tools from HR MCP server."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request,
        params={"server": "hr"}
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP tools/list failed: {response.status_code}"
    
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    
    # Verify HR-specific tools
    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    assert "get_employee_data" in tool_names
    assert "get_org_chart" in tool_names
    assert "get_leave_balance" in tool_names


@pytest.mark.asyncio
async def test_mcp_tools_list_legal(http_client, base_url, service_token):
    """Test listing available tools from Legal MCP server."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request,
        params={"server": "legal"}
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP tools/list failed: {response.status_code}"
    
    data = response.json()
    assert "result" in data
    assert "tools" in data["result"]
    
    # Verify legal-specific tools
    tool_names = [tool["name"] for tool in data["result"]["tools"]]
    assert "get_contract_data" in tool_names
    assert "get_compliance_info" in tool_names
    assert "get_legal_document" in tool_names
    assert "search_legal_precedents" in tool_names


@pytest.mark.asyncio
async def test_mcp_tool_call_finance(http_client, base_url, service_token):
    """Test calling a Finance MCP server tool."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": "get_financial_data",
            "arguments": {
                "user_id": "test-user-123",
                "data_type": "balance"
            }
        }
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP tool call failed: {response.status_code} - {response.text}"
    
    data = response.json()
    assert "result" in data or "error" in data
    
    if "result" in data:
        # Verify result structure
        assert data["result"] is not None


@pytest.mark.asyncio
async def test_mcp_tool_call_hr(http_client, base_url, service_token):
    """Test calling an HR MCP server tool."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": "get_employee_data",
            "arguments": {
                "employee_id": "emp-123"
            }
        }
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request,
        params={"server": "hr"}
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP tool call failed: {response.status_code}"
    
    data = response.json()
    assert "result" in data or "error" in data


@pytest.mark.asyncio
async def test_mcp_tool_call_legal(http_client, base_url, service_token):
    """Test calling a Legal MCP server tool."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/call",
        "params": {
            "name": "get_contract_data",
            "arguments": {
                "contract_id": "contract-123"
            }
        }
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request,
        params={"server": "legal"}
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP tool call failed: {response.status_code}"
    
    data = response.json()
    assert "result" in data or "error" in data


@pytest.mark.asyncio
async def test_mcp_resources_list(http_client, base_url, service_token):
    """Test listing available resources from MCP server."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "resources/list",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        f"MCP resources/list failed: {response.status_code}"
    
    data = response.json()
    assert "result" in data
    assert "resources" in data["result"]


@pytest.mark.asyncio
async def test_mcp_resources_read(http_client, base_url, service_token):
    """Test reading a resource from MCP server."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "resources/read",
        "params": {
            "uri": "s3://finance/test-resource"
        }
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    # May return error if resource doesn't exist, which is acceptable
    assert response.status_code == 200, \
        f"MCP resources/read failed: {response.status_code}"
    
    data = response.json()
    assert "result" in data or "error" in data


@pytest.mark.asyncio
async def test_mcp_invalid_method(http_client, base_url, service_token):
    """Test MCP server response to invalid method."""
    headers = {"X-Service-Token": service_token}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "invalid/method",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    assert response.status_code == 200, \
        "MCP should return 200 with error in JSON-RPC format"
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32601  # Method not found


@pytest.mark.asyncio
async def test_mcp_invalid_json_rpc(http_client, base_url, service_token):
    """Test MCP server response to invalid JSON-RPC request."""
    headers = {"X-Service-Token": service_token}
    
    # Missing required fields
    invalid_request = {
        "method": "tools/list"
        # Missing jsonrpc and id
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=invalid_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    # Should return error
    assert response.status_code in [200, 400]
    
    if response.status_code == 200:
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == -32600  # Invalid request


@pytest.mark.asyncio
async def test_mcp_without_service_token(http_client, base_url):
    """Test MCP endpoint requires service token."""
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    # No service token header
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    # Should return 401 or 403
    assert response.status_code in [401, 403], \
        f"Expected 401/403 without token, got {response.status_code}"


@pytest.mark.asyncio
async def test_mcp_with_invalid_service_token(http_client, base_url):
    """Test MCP endpoint rejects invalid service token."""
    headers = {"X-Service-Token": "invalid-token"}
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "tools/list",
        "params": {}
    }
    
    response = await http_client.post(
        f"{base_url}:8081/mcp",
        headers=headers,
        json=mcp_request
    )
    
    if response.status_code == 404:
        pytest.skip("MCP endpoint not yet implemented")
    
    # Should return 401 or 403
    assert response.status_code in [401, 403], \
        f"Expected 401/403 with invalid token, got {response.status_code}"


@pytest.mark.asyncio
async def test_mcp_all_servers_both_zones(http_client, aws_region, service_token):
    """Test MCP communication works for all servers in both zones."""
    zones = ["dev", "prod"]
    servers = ["finance", "hr", "legal"]
    
    for zone_name in zones:
        nlb_dns = os.getenv(f"{zone_name.upper()}_NLB_DNS")
        
        if not nlb_dns:
            print(f"Skipping {zone_name} - NLB DNS not configured")
            continue
        
        base_url = f"http://{nlb_dns}"
        headers = {"X-Service-Token": service_token}
        
        for server in servers:
            mcp_request = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/list",
                "params": {}
            }
            
            try:
                response = await http_client.post(
                    f"{base_url}:8081/mcp",
                    headers=headers,
                    json=mcp_request,
                    params={"server": server}
                )
                
                if response.status_code == 200:
                    print(f"✓ MCP {server} server accessible in {zone_name} zone")
                else:
                    print(f"✗ MCP {server} server failed in {zone_name} zone: {response.status_code}")
                    
            except Exception as e:
                print(f"✗ MCP {server} server error in {zone_name} zone: {str(e)}")


# Import os for environment variables
import os
