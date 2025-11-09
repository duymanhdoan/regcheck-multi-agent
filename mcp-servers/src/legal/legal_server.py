"""Legal MCP server implementation."""

import logging
from typing import Any, Dict, List
from ..base.base_server import BaseMCPServer
from ..base.models import Tool, Resource
from ..base.s3_client import MCPS3Client

logger = logging.getLogger(__name__)


class LegalMCPServer(BaseMCPServer):
    """Legal department MCP server."""
    
    def __init__(self, s3_client: MCPS3Client):
        """Initialize Legal MCP server.
        
        Args:
            s3_client: S3 client for data retrieval
        """
        super().__init__(server_type="legal", s3_client=s3_client)
    
    def _register_tools(self) -> None:
        """Register Legal tools."""
        
        # Tool: get_contract_data
        self.register_tool(Tool(
            name="get_contract_data",
            description="Retrieve contract data by contract ID or search criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "contract_id": {
                        "type": "string",
                        "description": "Contract identifier"
                    },
                    "party_name": {
                        "type": "string",
                        "description": "Name of contracting party for filtering"
                    },
                    "contract_type": {
                        "type": "string",
                        "enum": ["vendor", "customer", "partnership", "employment", "nda"],
                        "description": "Type of contract"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["active", "expired", "pending", "terminated"],
                        "description": "Contract status filter"
                    }
                },
                "required": []
            }
        ))
        
        # Tool: get_compliance_info
        self.register_tool(Tool(
            name="get_compliance_info",
            description="Retrieve compliance information for regulations and requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "regulation_type": {
                        "type": "string",
                        "enum": ["gdpr", "hipaa", "sox", "pci-dss", "iso27001"],
                        "description": "Type of regulation"
                    },
                    "department_id": {
                        "type": "string",
                        "description": "Department identifier for compliance status"
                    },
                    "include_requirements": {
                        "type": "boolean",
                        "description": "Include detailed requirements",
                        "default": True
                    }
                },
                "required": ["regulation_type"]
            }
        ))
        
        # Tool: get_legal_document
        self.register_tool(Tool(
            name="get_legal_document",
            description="Retrieve a specific legal document by ID or reference",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "Document identifier"
                    },
                    "document_type": {
                        "type": "string",
                        "enum": ["policy", "template", "memo", "opinion", "filing"],
                        "description": "Type of legal document"
                    },
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Include document metadata",
                        "default": True
                    }
                },
                "required": ["document_id"]
            }
        ))
        
        # Tool: search_legal_precedents
        self.register_tool(Tool(
            name="search_legal_precedents",
            description="Search legal precedents and case law relevant to a topic",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for legal precedents"
                    },
                    "jurisdiction": {
                        "type": "string",
                        "description": "Legal jurisdiction (e.g., 'US', 'EU', 'UK')"
                    },
                    "case_type": {
                        "type": "string",
                        "enum": ["contract", "employment", "intellectual_property", "regulatory", "corporate"],
                        "description": "Type of legal case"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ))
        
        logger.info("Registered Legal tools")
    
    def _register_resources(self) -> None:
        """Register Legal resources."""
        
        self.register_resource(Resource(
            uri="legal://contracts",
            name="Contract Repository",
            description="Repository of all contracts",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="legal://compliance",
            name="Compliance Database",
            description="Compliance requirements and status",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="legal://documents",
            name="Legal Document Library",
            description="Library of legal documents and templates",
            mimeType="application/json"
        ))
        
        self.register_resource(Resource(
            uri="legal://precedents",
            name="Legal Precedents Database",
            description="Database of legal precedents and case law",
            mimeType="application/json"
        ))
        
        logger.info("Registered Legal resources")
    
    async def _execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute Legal tool.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        if tool_name == "get_contract_data":
            return await self._get_contract_data(arguments)
        elif tool_name == "get_compliance_info":
            return await self._get_compliance_info(arguments)
        elif tool_name == "get_legal_document":
            return await self._get_legal_document(arguments)
        elif tool_name == "search_legal_precedents":
            return await self._search_legal_precedents(arguments)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def _get_contract_data(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get contract data.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Contract data
        """
        contract_id = arguments.get("contract_id")
        party_name = arguments.get("party_name")
        contract_type = arguments.get("contract_type")
        status = arguments.get("status")
        
        logger.info(
            f"Getting contract data - contract_id: {contract_id}, "
            f"party: {party_name}, type: {contract_type}, status: {status}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="legal",
            data_type="contracts"
        )
        
        # Filter contracts
        contracts = data.get("contracts", [])
        filtered_contracts = contracts
        
        if contract_id:
            filtered_contracts = [
                c for c in filtered_contracts
                if c.get("contract_id") == contract_id
            ]
        
        if party_name:
            filtered_contracts = [
                c for c in filtered_contracts
                if party_name.lower() in c.get("party_name", "").lower()
            ]
        
        if contract_type:
            filtered_contracts = [
                c for c in filtered_contracts
                if c.get("contract_type") == contract_type
            ]
        
        if status:
            filtered_contracts = [
                c for c in filtered_contracts
                if c.get("status") == status
            ]
        
        return {
            "filters": {
                "contract_id": contract_id,
                "party_name": party_name,
                "contract_type": contract_type,
                "status": status
            },
            "count": len(filtered_contracts),
            "contracts": filtered_contracts
        }
    
    async def _get_compliance_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get compliance information.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Compliance information
        """
        regulation_type = arguments.get("regulation_type")
        department_id = arguments.get("department_id")
        include_requirements = arguments.get("include_requirements", True)
        
        logger.info(
            f"Getting compliance info for {regulation_type}, "
            f"department: {department_id}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="legal",
            data_type="compliance"
        )
        
        # Get regulation data
        regulation_data = data.get(regulation_type, {})
        
        # Filter by department if specified
        if department_id:
            department_status = regulation_data.get("departments", {}).get(
                department_id, {}
            )
        else:
            department_status = regulation_data.get("departments", {})
        
        result = {
            "regulation_type": regulation_type,
            "department_id": department_id,
            "status": department_status
        }
        
        if include_requirements:
            result["requirements"] = regulation_data.get("requirements", [])
        
        return result
    
    async def _get_legal_document(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get legal document.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Legal document data
        """
        document_id = arguments.get("document_id")
        document_type = arguments.get("document_type")
        include_metadata = arguments.get("include_metadata", True)
        
        logger.info(
            f"Getting legal document {document_id}, type: {document_type}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="legal",
            data_type="documents"
        )
        
        # Find document by ID
        document = data.get(document_id, {})
        
        result = {
            "document_id": document_id,
            "document_type": document_type,
            "content": document.get("content", "")
        }
        
        if include_metadata:
            result["metadata"] = document.get("metadata", {})
        
        return result
    
    async def _search_legal_precedents(
        self,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Search legal precedents.
        
        Args:
            arguments: Tool arguments
            
        Returns:
            Search results
        """
        query = arguments.get("query")
        jurisdiction = arguments.get("jurisdiction")
        case_type = arguments.get("case_type")
        max_results = arguments.get("max_results", 10)
        
        logger.info(
            f"Searching legal precedents - query: {query}, "
            f"jurisdiction: {jurisdiction}, case_type: {case_type}"
        )
        
        # Retrieve data from S3
        data = await self.s3_client.get_json_data(
            department="legal",
            data_type="precedents"
        )
        
        # Search precedents (simplified search)
        precedents = data.get("precedents", [])
        results = []
        
        for precedent in precedents:
            # Simple keyword matching
            if query.lower() in precedent.get("summary", "").lower():
                # Apply filters
                if jurisdiction and precedent.get("jurisdiction") != jurisdiction:
                    continue
                if case_type and precedent.get("case_type") != case_type:
                    continue
                
                results.append(precedent)
                
                if len(results) >= max_results:
                    break
        
        return {
            "query": query,
            "jurisdiction": jurisdiction,
            "case_type": case_type,
            "count": len(results),
            "results": results
        }
    
    async def _read_resource_content(self, uri: str) -> Any:
        """Read Legal resource content.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        if uri == "legal://contracts":
            return await self.s3_client.get_json_data(
                department="legal",
                data_type="contracts"
            )
        elif uri == "legal://compliance":
            return await self.s3_client.get_json_data(
                department="legal",
                data_type="compliance"
            )
        elif uri == "legal://documents":
            return await self.s3_client.get_json_data(
                department="legal",
                data_type="documents"
            )
        elif uri == "legal://precedents":
            return await self.s3_client.get_json_data(
                department="legal",
                data_type="precedents"
            )
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
