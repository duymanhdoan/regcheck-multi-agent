"""JWT validation for Cognito tokens."""
import json
import logging
from typing import Dict, Optional
from jose import jwt, JWTError
import httpx
from functools import lru_cache

from ..config import settings

logger = logging.getLogger(__name__)


class JWTValidator:
    """Validates JWT tokens from Amazon Cognito."""
    
    def __init__(self):
        self.user_pool_id = settings.cognito_user_pool_id
        self.region = settings.cognito_region
        self.jwks_url = (
            f"https://cognito-idp.{self.region}.amazonaws.com/"
            f"{self.user_pool_id}/.well-known/jwks.json"
        )
        self._jwks: Optional[Dict] = None
    
    async def get_jwks(self) -> Dict:
        """Fetch JWKS from Cognito."""
        if self._jwks is None:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.jwks_url, timeout=10.0)
                response.raise_for_status()
                self._jwks = response.json()
                logger.info("Fetched JWKS from Cognito")
        return self._jwks
    
    def extract_token(self, authorization_header: Optional[str]) -> Optional[str]:
        """Extract JWT token from Authorization header.
        
        Args:
            authorization_header: Authorization header value (e.g., "Bearer <token>")
            
        Returns:
            JWT token string or None if invalid format
        """
        if not authorization_header:
            return None
        
        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    async def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token and return claims.
        
        Args:
            token: JWT token string
            
        Returns:
            Token claims dict if valid, None otherwise
        """
        try:
            # Get JWKS
            jwks = await self.get_jwks()
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            if not kid:
                logger.warning("Token missing kid in header")
                return None
            
            # Find the key in JWKS
            key = None
            for jwk_key in jwks.get("keys", []):
                if jwk_key.get("kid") == kid:
                    key = jwk_key
                    break
            
            if not key:
                logger.warning(f"Key {kid} not found in JWKS")
                return None
            
            # Verify and decode token
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": False,  # Cognito doesn't always include aud
                }
            )
            
            # Validate token_use claim
            if claims.get("token_use") != "access":
                logger.warning(f"Invalid token_use: {claims.get('token_use')}")
                return None
            
            logger.info(f"Token validated for user: {claims.get('username')}")
            return claims
            
        except JWTError as e:
            logger.warning(f"JWT validation failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return None
    
    def extract_user_info(self, claims: Dict) -> Dict:
        """Extract user information from token claims.
        
        Args:
            claims: JWT token claims
            
        Returns:
            Dict with user_id, username, roles, and department
        """
        # Extract roles from cognito:groups claim
        roles = claims.get("cognito:groups", [])
        
        # Extract department (assume first role is department)
        department = roles[0] if roles else "unknown"
        
        return {
            "user_id": claims.get("sub"),
            "username": claims.get("username"),
            "roles": roles,
            "department": department,
            "email": claims.get("email"),
        }


# Global validator instance
jwt_validator = JWTValidator()
