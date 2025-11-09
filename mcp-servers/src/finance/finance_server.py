"""Finance MCP server implementation."""

import logging
from typing import Any, Dict
from ..base.base_server import BaseMCPServer
from ..base.models import Tool, Resource
from ..base.s3_client import MCPS3Client

logger = logging.getLogger(__name__)


class FinanceMCPServer(BaseMCPServer):
    """Finance department MCP server."""
    
    def __init__(self, s3_client: MCPS3Client):
        """Initialize Finance MCP server.
        
        Args:
            s3_client: S3 client for data retrieval
        """
        super().__init__(server_type="finance", s3_client=s3_client)
    
    def _register_tools(self) -> None:
        """Register Finance tools."""
        
        # Tool: get_financial_data
        self.register_tool(Tool(
            name="get_financial_data",
            description="Retrieve financial data for a user including account balances, transactions, and financial summary",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "User identifier"
                    },
                    "data_type": {
                        "type": "string",
                        "enum": ["balance", "transactions", "summary"],
                        "description": "Type of financial data to retrieve"
                    },
                    "date_range": {
                        "type": "object",
                        "properties": {
                            "start_date": {"type": "string", "format": "date"},
                            "end_date": {"type": "string", "format": "date"}
                        },
                        "description": "Optional date range for transactions"
                    }
                },
                "required": ["user_id", "data_type"]
            }
        ))
        
        # Tool: get_budget_info
        self.register_tool(Tool(
            name="get_budget_info",
            description="Retrieve budget information for a department or project",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Department or project identifier"
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": ["department", "project"],
                        "description": "Type of entity"
                    },
                    "fiscal_year": {
                        "type": "string",
                        "description": "Fiscal year (e.g., '2025')"
                    }
                },
                "required": ["entity_id", "entity_type"]
            }
        ))
        
        # Tool: get_invoice_data
        self.register_tool(Tool(
            name="get_invoice_data",
            description="Retrieve invoice data by invoice ID or search criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {
                        "type": "string",
                        "description": "Invoice identifier"
                    },
                    "vendor_id": {
                        "type": "string",
                        "description": "Vendor identifier for filtering"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "paid", "overdue", "cancelled"],
                        "description": "Invoice status filter"
                    }
                },
                "required": []
            }
        ))
        
        logger.info("Registered Finance tools")
    
    def _register_resources(self) -> None:
        """Register Finance resources."""
        
        self.register_resource(Resource(
            uri="finance://accounts",
            name="Account List",
            description="List of all financial accounts",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="finance://budgets",
            name="Budget List",
            description="List of all department and project budgets",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="finance://invoices",
            name="Invoice List",
            description="List of all invoices",
            mimeType="application/json"
        ))
        
        logger.info("Registered Finance resources")
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute Finance tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name == "get_financial_data":
            return await self._get_financial_data(arguments)
        elif tool_name == "get_budget_info":
            return await self._get_budget_info(arguments)
        elif tool_name == "get_invoice_data":
            return await self._get_invoice_data(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _get_financial_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get financial data for a user.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Financial data
        """
        user_id = arguments.get("user_id")
        data_type = arguments.get("data_type")
        date_range = arguments.get("date_range")
        
        logger.info(
            f"Getting financial data for user {user_id}, type: {data_type}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="finance",
            data_type=f"user_{data_type}"
        )
        
        # Filter by user_id
        user_data = data.get(user_id, {})
        
        # Apply date range filter if provided
        if date_range and data_type == "transactions":
            # In a real implementation, filter transactions by date
            pass
        
        return {
            "user_id": user_id,
            "data_type": data_type,
            "data": user_data,
            "date_range": date_range
        }
    
    async def _get_budget_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get budget information.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Budget information
        """
        entity_id = arguments.get("entity_id")
        entity_type = arguments.get("entity_type")
        fiscal_year = arguments.get("fiscal_year", "2025")
        
        logger.info(
            f"Getting budget info for {entity_type} {entity_id}, "
            f"fiscal year: {fiscal_year}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="finance",
            data_type=f"budgets_{entity_type}"
        )
        
        # Filter by entity_id and fiscal_year
        budget_data = data.get(entity_id, {}).get(fiscal_year, {})
        
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "fiscal_year": fiscal_year,
            "budget": budget_data
        }
    
    async def _get_invoice_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get invoice data.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Invoice data
        """
        invoice_id = arguments.get("invoice_id")
        vendor_id = arguments.get("vendor_id")
        status = arguments.get("status")
        
        logger.info(
            f"Getting invoice data - invoice_id: {invoice_id}, "
            f"vendor_id: {vendor_id}, status: {status}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="finance",
            data_type="invoices"
        )
        
        # Filter invoices
        invoices = data.get("invoices", [])
        filtered_invoices = invoices
        
        if invoice_id:
            filtered_invoices = [
                inv for inv in filtered_invoices
                if inv.get("invoice_id") == invoice_id
            ]
        
        if vendor_id:
            filtered_invoices = [
                inv for inv in filtered_invoices
                if inv.get("vendor_id") == vendor_id
            ]
        
        if status:
            filtered_invoices = [
                inv for inv in filtered_invoices
                if inv.get("status") == status
            ]
        
        return {
            "filters": {
                "invoice_id": invoice_id,
                "vendor_id": vendor_id,
                "status": status
            },
            "count": len(filtered_invoices),
            "invoices": filtered_invoices
        }
    
    async def _read_resource_content(self, uri: str) -> Any:
        """Read Finance resource content.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        if uri == "finance://accounts":
            return await self.s3_client.get_json_data(
                department="finance",
                data_type="accounts"
            )
        elif uri == "finance://budgets":
            return await self.s3_client.get_json_data(
                department="finance",
                data_type="budgets"
            )
        elif uri == "finance://invoices":
            return await self.s3_client.get_json_data(
                department="finance",
                data_type="invoices"
            )
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
