"""
Custom Langflow Component for AgentGateway API Integration
"""
from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput
from langflow.schema import Data
import httpx
import json


class AgentGatewayAPIComponent(Component):
    display_name = "AgentGateway API"
    description = "Call AgentGateway API for file processing operations"
    icon = "cloud"
    
    inputs = [
        MessageTextInput(
            name="api_url",
            display_name="API URL",
            info="AgentGateway API endpoint URL",
            value="http://agentgateway-service.local:8080"
        ),
        MessageTextInput(
            name="endpoint",
            display_name="Endpoint",
            info="API endpoint path (e.g., /api/process, /api/status/{id})",
            required=True
        ),
        MessageTextInput(
            name="method",
            display_name="HTTP Method",
            info="HTTP method to use",
            value="POST",
            options=["GET", "POST", "PUT", "DELETE"]
        ),
        MessageTextInput(
            name="payload",
            display_name="Request Payload",
            info="JSON payload for the request (for POST/PUT)",
            multiline=True
        ),
        SecretStrInput(
            name="auth_token",
            display_name="Auth Token",
            info="JWT token for authentication"
        )
    ]
    
    outputs = [
        Output(display_name="Response", name="response", method="call_api")
    ]
    
    async def call_api(self) -> Data:
        """Call the AgentGateway API"""
        url = f"{self.api_url.rstrip('/')}/{self.endpoint.lstrip('/')}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if self.method == "GET":
                    response = await client.get(url, headers=headers)
                elif self.method == "POST":
                    payload = json.loads(self.payload) if self.payload else {}
                    response = await client.post(url, json=payload, headers=headers)
                elif self.method == "PUT":
                    payload = json.loads(self.payload) if self.payload else {}
                    response = await client.put(url, json=payload, headers=headers)
                elif self.method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                response.raise_for_status()
                result = response.json()
                
                return Data(
                    data={
                        "status_code": response.status_code,
                        "response": result,
                        "success": True
                    }
                )
            except httpx.HTTPError as e:
                return Data(
                    data={
                        "error": str(e),
                        "success": False
                    }
                )
            except json.JSONDecodeError as e:
                return Data(
                    data={
                        "error": f"Invalid JSON payload: {str(e)}",
                        "success": False
                    }
                )
