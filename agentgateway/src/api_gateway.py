"""API Gateway mode for routing authenticated requests to Application service."""
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from fastapi.responses import JSONResponse
import httpx
from circuitbreaker import circuit
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .auth.jwt_validator import jwt_validator
from .models import AuditLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api-gateway"])


async def validate_jwt_token(authorization: Optional[str] = Header(None)) -> dict:
    """Dependency to validate JWT token from Authorization header.
    
    Args:
        authorization: Authorization header value
        
    Returns:
        User information dict
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    if not authorization:
        logger.warning("Missing Authorization header")
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    
    token = jwt_validator.extract_token(authorization)
    if not token:
        logger.warning("Invalid Authorization header format")
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    
    claims = await jwt_validator.validate_token(token)
    if not claims:
        logger.warning("Invalid or expired JWT token")
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_info = jwt_validator.extract_user_info(claims)
    return user_info


@circuit(failure_threshold=5, recovery_timeout=60)
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5)
)
async def forward_to_application(
    method: str,
    path: str,
    headers: dict,
    body: Optional[bytes] = None,
    params: Optional[dict] = None
) -> httpx.Response:
    """Forward request to Application service with circuit breaker and retry.
    
    Args:
        method: HTTP method
        path: Request path
        headers: Request headers
        body: Request body
        params: Query parameters
        
    Returns:
        Response from Application service
    """
    url = f"{settings.application_service_url}{path}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(
            method=method,
            url=url,
            headers=headers,
            content=body,
            params=params
        )
        return response


def create_audit_log(
    user_info: dict,
    request: Request,
    response_status: int,
    error: Optional[str] = None
) -> AuditLog:
    """Create audit log entry.
    
    Args:
        user_info: User information from JWT
        request: FastAPI request object
        response_status: HTTP response status code
        error: Error message if any
        
    Returns:
        AuditLog object
    """
    return AuditLog(
        user_id=user_info.get("user_id"),
        username=user_info.get("username"),
        department=user_info.get("department"),
        method=request.method,
        path=str(request.url.path),
        status_code=response_status,
        error=error,
        client_ip=request.client.host if request.client else None
    )


@router.post("/process")
async def process_file(
    request: Request,
    user_info: dict = Depends(validate_jwt_token)
):
    """Route file processing request to Application service.
    
    Args:
        request: FastAPI request object
        user_info: User information from JWT validation
        
    Returns:
        Response from Application service
    """
    try:
        # Read request body
        body = await request.body()
        
        # Forward to Application service
        response = await forward_to_application(
            method="POST",
            path="/process",
            headers=dict(request.headers),
            body=body
        )
        
        # Create audit log
        audit_log = create_audit_log(user_info, request, response.status_code)
        logger.info(f"API Gateway: {audit_log.model_dump_json()}")
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error forwarding request: {str(e)}")
        audit_log = create_audit_log(user_info, request, 502, str(e))
        logger.error(f"API Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=502, detail="Backend service unavailable")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        audit_log = create_audit_log(user_info, request, 500, str(e))
        logger.error(f"API Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status/{job_id}")
async def get_status(
    job_id: str,
    request: Request,
    user_info: dict = Depends(validate_jwt_token)
):
    """Route status request to Application service.
    
    Args:
        job_id: Processing job ID
        request: FastAPI request object
        user_info: User information from JWT validation
        
    Returns:
        Response from Application service
    """
    try:
        # Forward to Application service
        response = await forward_to_application(
            method="GET",
            path=f"/status/{job_id}",
            headers=dict(request.headers)
        )
        
        # Create audit log
        audit_log = create_audit_log(user_info, request, response.status_code)
        logger.info(f"API Gateway: {audit_log.model_dump_json()}")
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error forwarding request: {str(e)}")
        audit_log = create_audit_log(user_info, request, 502, str(e))
        logger.error(f"API Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=502, detail="Backend service unavailable")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        audit_log = create_audit_log(user_info, request, 500, str(e))
        logger.error(f"API Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/download/{job_id}")
async def get_download_url(
    job_id: str,
    request: Request,
    user_info: dict = Depends(validate_jwt_token)
):
    """Route download URL request to Application service.
    
    Args:
        job_id: Processing job ID
        request: FastAPI request object
        user_info: User information from JWT validation
        
    Returns:
        Response from Application service
    """
    try:
        # Forward to Application service
        response = await forward_to_application(
            method="GET",
            path=f"/download/{job_id}",
            headers=dict(request.headers)
        )
        
        # Create audit log
        audit_log = create_audit_log(user_info, request, response.status_code)
        logger.info(f"API Gateway: {audit_log.model_dump_json()}")
        
        # Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error forwarding request: {str(e)}")
        audit_log = create_audit_log(user_info, request, 502, str(e))
        logger.error(f"API Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=502, detail="Backend service unavailable")
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        audit_log = create_audit_log(user_info, request, 500, str(e))
        logger.error(f"API Gateway Error: {audit_log.model_dump_json()}")
        raise HTTPException(status_code=500, detail="Internal server error")
