"""MCP Gateway mode for routing MCP protocol requests to MCP servers."""
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header
from fastapi.responses import JSONResponse
import httpx
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .rbac.engine import rbac_engine
from .models import MCPRequest, MCPResponse, AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp-gateway"])


def validate_service_token(x_service_token: Optional[str] = Header(None)) -> dict:
    """Validate service token from X-Service-Token header.
    
    Args:
        x_service_token: Service token from header
        
    Returns:
        Service information dict
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not x_service_token:
        logger.warning("Missing X-Service-Token header")
        raise HTTPException(status_code=401, detail="Missing service token")
    
    # Simple token validation (in production, use proper JWT or API key validation)
    if settings.service_token and x_service_token != settings.service_token:
        logger.warning("Invalid service token")
        raise HTTPException(status_code=401, detail="Invalid service token")
    
    # Extract service information from token
    # In a real implementation, decode JWT or lookup API key
    return {
        "service_name": "application",
        "department": None  # Will be determined from MCP request
    }


def get_mcp_server_url(server_type: str) -> Optional[str]:
    """Get MCP server URL by type.
    
    Args:
        server_type: MCP server type (finance, hr, legal)
        
    Returns:
        MCP server URL or None
    """
    mapping = {
        "finance": settings.mcp_finance_url,
        "hr": settings.mcp_hr_url,
        "legal": settings.mcp_legal_url,
    }
    return mapping.get(server_type.lower())


def extract_department_from_request(mcp_request: MCPRequest) -> Optional[str]:
    """Extract department from MCP request parameters.
    
    Args:
        mcp_request: MCP request object
        
    Returns:
        Department name or None
    """
    if not mcp_request.params:
        return None
    
    # Check for department in params
    department = mcp_request.params.get("department")
    if department:
        return department
    
    # Check for server_type which maps to department
    server_type = mcp_request.params.get("server_type")
    if server_type:
        return server_type
    
    return None


@circuit(failure_threshold=5, recovery_timeout=60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5)
)
async def forward_to_mcp_server(
    server_url: str,
    mcp_request: MCPRequest
) -> httpx.Response:
    """Forward MCP request to MCP server with circuit breaker and retry.
    
    Args:
        server_url: MCP server URL
        mcp_request: MCP request object
        
    Returns:
        Response from MCP server
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            server_url,
            json=mcp_request.model_dump(),
            headers={"Content-Type": "application/json"}
        )
        return response


def create_mcp_audit_log(
    service_info: dict,
    request: Request,
    mcp_request: MCPRequest,
    response_status: int,
    department: Optional[str] = None,
    error: Optional[str] = None
) -> AuditLog:
    """Create audit log entry for MCP request.
    
    Args:
        service_info: Service information from token
        request: FastAPI request object
        mcp_request: MCP request object
        response_status: HTTP response status code
        department: Department name
        error: Error message if any
        
    Returns:
        AuditLog object
    """
    return AuditLog(
        user_id=service_info.get("service_name"),
        username=service_info.get("service_name"),
        department=department,
        method=f"MCP:{mcp_request.method}",
        path=str(request.url.path),
        status_code=response_status,
        error=error,
        client_ip=request.client.host if request.client else None
    )


@router.post("")
async def route_mcp_request(
    request: Request,
    mcp_request: MCPRequest,
    x_service_token: Optional[str] = Header(None),
    x_user_roles: Optional[str] = Header(None)
):
    """Route MCP request to appropriate MCP server.
    
    Args:
        request: FastAPI request object
        mcp_request: MCP request object
        x_service_token: Service token from header
        x_user_roles: User roles from header (comma-separated)
        
    Returns:
        Response from MCP server
    """
    # Validate service token
    service_info = validate_service_token(x_service_token)
    
    # Extract department from request
    department = extract_department_from_request(mcp_request)
    if not department:
        logger.warning("Missing department in MCP request")
        raise HTTPException(status_code=400, detail="Missing department in request")
    
    # Check RBAC permissions if enabled
    if settings.rbac_enabled and x_user_roles:
        roles = [role.strip() for role in x_user_roles.split(",")]
        resource = rbac_engine.map_department_to_server(department)
        
        if not resource:
            logger.warning(f"Unknown department: {department}")
            raise HTTPException(status_code=400, detail="Unknown department")
        
        if not rbac_engine.check_permission(roles, resource, "read"):
            audit_log = create_mcp_audit_log(
                service_info, request, mcp_request, 403, department,
                "RBAC permission denied"
            )
            logger.warning(f"MCP Gateway: {audit_log.model_dump_json()}")
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Enforce department isolation if enabled
    if settings.department_isolation and x_user_roles:
        roles = [role.strip() for role in x_user_roles.split(",")]
        if department.lower() not in [role.lower() for role in roles]:
            audit_log = create_mcp_audit_log(
                service_info, request, mcp_request, 403, department,
                "Department isolation violation"
            )
            logger.warning(f"MCP Gateway: {audit_log.model_dump_json()}")
            raise HTTPException(
                status_code=403,
                detail="Access denied: department isolation"
            )
    
    # Get MCP server URL
    server_url = get_mcp_server_url(department)
    if not server_url:
        logger.error(f"No MCP server configured for department: {department}")
        raise HTTPException(status_code=404, detail="MCP server not found")
    
    try:
        # Forward to MCP server
        response = await forward_to_mcp_server(server_url, mcp_request)
        
        # Create audit log
        audit_log = create_mcp_audit_log(
            service_info, request, mcp_request, response.status_code, department
        )
        logger.info(f"MCP Gateway: {audit_log.model_dump_json()}")
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error forwarding MCP request: {str(e)}")
        audit_log = create_mcp_audit_log(
            service_info, request, mcp_request, 502, department, str(e)
        )
        logger.error(f"MCP Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=502, detail="MCP server unavailable")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        audit_log = create_mcp_audit_log(
            service_info, request, mcp_request, 500, department, str(e)
        )
        logger.error(f"MCP Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/servers")
async def list_mcp_servers(
    x_service_token: Optional[str] = Header(None),
    x_user_roles: Optional[str] = Header(None)
):
    """List available MCP servers based on user roles.
    
    Args:
        x_service_token: Service token from header
        x_user_roles: User roles from header (comma-separated)
        
    Returns:
        List of accessible MCP servers
    """
    # Validate service token
    validate_service_token(x_service_token)
    
    # Get accessible resources based on roles
    if x_user_roles:
        roles = [role.strip() for role in x_user_roles.split(",")]
        accessible_resources = rbac_engine.get_accessible_resources(roles)
        
        # Map resources to server info
        servers = []
        for resource in accessible_resources:
            if resource == "mcp-finance-server":
                servers.append({
                    "type": "finance",
                    "url": settings.mcp_finance_url,
                    "description": "Finance MCP Server"
                })
            elif resource == "mcp-hr-server":
                servers.append({
                    "type": "hr",
                    "url": settings.mcp_hr_url,
                    "description": "HR MCP Server"
                })
            elif resource == "mcp-legal-server":
                servers.append({
                    "type": "legal",
                    "url": settings.mcp_legal_url,
                    "description": "Legal MCP Server"
                })
        
        return {"servers": servers}
    
    # Return all servers if no roles specified
    return {
        "servers": [
            {
                "type": "finance",
                "url": settings.mcp_finance_url,
                "description": "Finance MCP Server"
            },
            {
                "type": "hr",
                "url": settings.mcp_hr_url,
                "description": "HR MCP Server"
            },
            {
                "type": "legal",
                "url": settings.mcp_legal_url,
                "description": "Legal MCP Server"
            }
        ]
    }
