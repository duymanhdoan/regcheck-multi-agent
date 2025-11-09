"""RBAC engine for role-based access control."""
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Permission(BaseModel):
    """Permission model."""
    resource: str
    actions: List[str]


class Role(BaseModel):
    """Role model."""
    name: str
    description: str
    permissions: List[Permission]


class RBACPolicy(BaseModel):
    """RBAC policy model."""
    roles: List[Role]


class RBACEngine:
    """RBAC engine for enforcing role-based access control."""
    
    def __init__(self, policy_file: Optional[str] = None):
        """Initialize RBAC engine.
        
        Args:
            policy_file: Path to RBAC policy YAML file
        """
        if policy_file is None:
            policy_file = Path(__file__).parent / "policies.yaml"
        
        self.policy = self._load_policy(policy_file)
        self._role_map = {role.name: role for role in self.policy.roles}
        logger.info(f"Loaded RBAC policy with {len(self.policy.roles)} roles")
    
    def _load_policy(self, policy_file: str) -> RBACPolicy:
        """Load RBAC policy from YAML file.
        
        Args:
            policy_file: Path to policy file
            
        Returns:
            RBACPolicy object
        """
        try:
            with open(policy_file, 'r') as f:
                policy_data = yaml.safe_load(f)
            return RBACPolicy(**policy_data)
        except Exception as e:
            logger.error(f"Failed to load RBAC policy: {str(e)}")
            # Return empty policy on error
            return RBACPolicy(roles=[])
    
    def check_permission(
        self,
        roles: List[str],
        resource: str,
        action: str = "read"
    ) -> bool:
        """Check if any of the user's roles has permission for the resource.
        
        Args:
            roles: List of user roles
            resource: Resource identifier (e.g., "mcp-finance-server")
            action: Action to perform (e.g., "read", "write")
            
        Returns:
            True if permission granted, False otherwise
        """
        for role_name in roles:
            role = self._role_map.get(role_name)
            if not role:
                continue
            
            for permission in role.permissions:
                if permission.resource == resource and action in permission.actions:
                    logger.info(
                        f"Permission granted: role={role_name}, "
                        f"resource={resource}, action={action}"
                    )
                    return True
        
        logger.warning(
            f"Permission denied: roles={roles}, "
            f"resource={resource}, action={action}"
        )
        return False
    
    def get_accessible_resources(self, roles: List[str]) -> List[str]:
        """Get list of resources accessible by the user's roles.
        
        Args:
            roles: List of user roles
            
        Returns:
            List of accessible resource identifiers
        """
        resources = set()
        for role_name in roles:
            role = self._role_map.get(role_name)
            if role:
                for permission in role.permissions:
                    resources.add(permission.resource)
        
        return list(resources)
    
    def map_department_to_server(self, department: str) -> Optional[str]:
        """Map department name to MCP server resource identifier.
        
        Args:
            department: Department name (e.g., "finance", "hr", "legal")
            
        Returns:
            MCP server resource identifier or None
        """
        mapping = {
            "finance": "mcp-finance-server",
            "hr": "mcp-hr-server",
            "legal": "mcp-legal-server",
        }
        return mapping.get(department.lower())


# Global RBAC engine instance
rbac_engine = RBACEngine()
