"""HR MCP server implementation."""

import logging
from typing import Any, Dict
from ..base.base_server import BaseMCPServer
from ..base.models import Tool, Resource
from ..base.s3_client import MCPS3Client

logger = logging.getLogger(__name__)


class HRMCPServer(BaseMCPServer):
    """HR department MCP server."""
    
    def __init__(self, s3_client: MCPS3Client):
        """Initialize HR MCP server.
        
        Args:
            s3_client: S3 client for data retrieval
        """
        super().__init__(server_type="hr", s3_client=s3_client)
    
    def _register_tools(self) -> None:
        """Register HR tools."""
        
        # Tool: get_employee_data
        self.register_tool(Tool(
            name="get_employee_data",
            description="Retrieve employee data including personal information, job details, and employment history",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee identifier"
                    },
                    "data_type": {
                        "type": "string",
                        "enum": ["profile", "job_details", "history", "performance"],
                        "description": "Type of employee data to retrieve"
                    }
                },
                "required": ["employee_id", "data_type"]
            }
        ))
        
        # Tool: get_org_chart
        self.register_tool(Tool(
            name="get_org_chart",
            description="Retrieve organizational chart for a department or team",
            inputSchema={
                "type": "object",
                "properties": {
                    "department_id": {
                        "type": "string",
                        "description": "Department identifier"
                    },
                    "include_subordinates": {
                        "type": "boolean",
                        "description": "Include all subordinates in hierarchy",
                        "default": True
                    },
                    "depth": {
                        "type": "integer",
                        "description": "Maximum depth of hierarchy to retrieve",
                        "default": 3
                    }
                },
                "required": ["department_id"]
            }
        ))
        
        # Tool: get_leave_balance
        self.register_tool(Tool(
            name="get_leave_balance",
            description="Retrieve leave balance and history for an employee",
            inputSchema={
                "type": "object",
                "properties": {
                    "employee_id": {
                        "type": "string",
                        "description": "Employee identifier"
                    },
                    "leave_type": {
                        "type": "string",
                        "enum": ["annual", "sick", "personal", "all"],
                        "description": "Type of leave to query",
                        "default": "all"
                    },
                    "year": {
                        "type": "string",
                        "description": "Year for leave balance (e.g., '2025')"
                    }
                },
                "required": ["employee_id"]
            }
        ))
        
        logger.info("Registered HR tools")
    
    def _register_resources(self) -> None:
        """Register HR resources."""
        
        self.register_resource(Resource(
            uri="hr://employees",
            name="Employee Directory",
            description="Complete employee directory",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="hr://departments",
            name="Department List",
            description="List of all departments and organizational structure",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="hr://policies",
            name="HR Policies",
            description="HR policies and procedures",
            mimeType="application/json"
        ))
        
        logger.info("Registered HR resources")
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute HR tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name == "get_employee_data":
            return await self._get_employee_data(arguments)
        elif tool_name == "get_org_chart":
            return await self._get_org_chart(arguments)
        elif tool_name == "get_leave_balance":
            return await self._get_leave_balance(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _get_employee_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get employee data.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Employee data
        """
        employee_id = arguments.get("employee_id")
        data_type = arguments.get("data_type")
        
        logger.info(
            f"Getting employee data for {employee_id}, type: {data_type}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="hr",
            data_type=f"employee_{data_type}"
        )
        
        # Filter by employee_id
        employee_data = data.get(employee_id, {})
        
        return {
            "employee_id": employee_id,
            "data_type": data_type,
            "data": employee_data
        }
    
    async def _get_org_chart(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get organizational chart.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Organizational chart data
        """
        department_id = arguments.get("department_id")
        include_subordinates = arguments.get("include_subordinates", True)
        depth = arguments.get("depth", 3)
        
        logger.info(
            f"Getting org chart for department {department_id}, "
            f"depth: {depth}, include_subordinates: {include_subordinates}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="hr",
            data_type="org_chart"
        )
        
        # Filter by department_id
        org_data = data.get(department_id, {})
        
        # In a real implementation, apply depth and subordinate filtering
        if not include_subordinates:
            # Remove subordinate information
            pass
        
        return {
            "department_id": department_id,
            "include_subordinates": include_subordinates,
            "depth": depth,
            "org_chart": org_data
        }
    
    async def _get_leave_balance(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get leave balance for an employee.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Leave balance data
        """
        employee_id = arguments.get("employee_id")
        leave_type = arguments.get("leave_type", "all")
        year = arguments.get("year", "2025")
        
        logger.info(
            f"Getting leave balance for employee {employee_id}, "
            f"type: {leave_type}, year: {year}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="hr",
            data_type="leave_balances"
        )
        
        # Filter by employee_id and year
        employee_leaves = data.get(employee_id, {}).get(year, {})
        
        # Filter by leave type if not "all"
        if leave_type != "all":
            employee_leaves = {
                leave_type: employee_leaves.get(leave_type, {})
            }
        
        return {
            "employee_id": employee_id,
            "leave_type": leave_type,
            "year": year,
            "balances": employee_leaves
        }
    
    async def _read_resource_content(self, uri: str) -> Any:
        """Read HR resource content.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        if uri == "hr://employees":
            return await self.s3_client.get_json_data(
                department="hr",
                data_type="employees"
            )
        elif uri == "hr://departments":
            return await self.s3_client.get_json_data(
                department="hr",
                data_type="departments"
            )
        elif uri == "hr://policies":
            return await self.s3_client.get_json_data(
                department="hr",
                data_type="policies"
            )
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
