"""
Custom Langflow Component for MCP Server Interactions
"""
from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DropdownInput
from langflow.schema import Data
import httpx
import json
import uuid


class MCPServerClientComponent(Component):
    display_name = "MCP Server Client"
    description = "Interact with MCP servers through AgentGateway"
    icon = "server"
    
    inputs = [
        MessageTextInput(
            name="agentgateway_url",
            display_name="AgentGateway MCP URL",
            info="AgentGateway MCP endpoint URL",
            value="http://agentgateway-service.local:8081"
        ),
        DropdownInput(
            name="server_type",
            display_name="MCP Server Type",
            info="Type of MCP server to call",
            options=["finance", "hr", "legal"],
            value="finance"
        ),
        MessageTextInput(
            name="method",
            display_name="MCP Method",
            info="MCP method to call (e.g., tools/list, tools/call, resources/read)",
            value="tools/call",
            options=["tools/list", "tools/call", "resources/list", "resources/read"]
        ),
        MessageTextInput(
            name="tool_name",
            display_name="Tool Name",
            info="Name of the tool to call (for tools/call method)",
        ),
        MessageTextInput(
            name="tool_arguments",
            display_name="Tool Arguments",
            info="JSON arguments for the tool",
            multiline=True
        ),
        SecretStrInput(
            name="service_token",
            display_name="Service Token",
            info="Service token for MCP authentication"
        )
    ]
    
    outputs = [
        Output(display_name="MCP Response", name="response", method="call_mcp_server")
    ]
    
    async def call_mcp_server(self) -> Data:
        """Call MCP server through AgentGateway"""
        url = f"{self.agentgateway_url.rstrip('/')}/mcp"
        
        # Build MCP JSON-RPC request
        mcp_request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": self.method
        }
        
        # Add params for tools/call
        if self.method == "tools/call" and self.tool_name:
            try:
                arguments = json.loads(self.tool_arguments) if self.tool_arguments else {}
            except json.JSONDecodeError:
                return Data(
                    data={
                        "error": "Invalid JSON in tool arguments",
                        "success": False
                    }
                )
            
            mcp_request["params"] = {
                "name": self.tool_name,
                "arguments": arguments
            }
        
        headers = {
            "Content-Type": "application/json",
            "X-MCP-Server-Type": self.server_type
        }
        
        if self.service_token:
            headers["X-Service-Token"] = self.service_token
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=mcp_request, headers=headers)
                response.raise_for_status()
                result = response.json()
                
                # Check for MCP error response
                if "error" in result:
                    return Data(
                        data={
                            "mcp_error": result["error"],
                            "success": False
                        }
                    )
                
                return Data(
                    data={
                        "result": result.get("result", {}),
                        "mcp_id": result.get("id"),
                        "success": True
                    }
                )
            except httpx.HTTPError as e:
                return Data(
                    data={
                        "error": f"HTTP error: {str(e)}",
                        "success": False
                    }
                )
            except json.JSONDecodeError as e:
                return Data(
                    data={
                        "error": f"Invalid JSON response: {str(e)}",
                        "success": False
                    }
                )
