"""
Authorization
RBAC (Role-Based Access Control) and permission system
"""

from typing import Dict, List, Set, Optional
from enum import Enum
from fastapi import HTTPException, Depends
from monitoring import get_logger
from security.auth import get_current_user

logger = get_logger(__name__)


class Permission(str, Enum):
    """System permissions"""
    # Task permissions
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_CANCEL = "task:cancel"
    
    # Workflow permissions
    WORKFLOW_CREATE = "workflow:create"
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_UPDATE = "workflow:update"
    WORKFLOW_DELETE = "workflow:delete"
    
    # Agent permissions
    AGENT_REGISTER = "agent:register"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    
    # System permissions
    SYSTEM_ADMIN = "system:admin"
    SYSTEM_MONITOR = "system:monitor"
    
    # Wildcard
    ALL = "*"


class Role(str, Enum):
    """System roles"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    AGENT = "agent"


class RBAC:
    """Role-Based Access Control manager"""
    
    # Role to permissions mapping
    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.ADMIN: {
            Permission.ALL  # Admin has all permissions
        },
        Role.USER: {
            Permission.TASK_CREATE,
            Permission.TASK_READ,
            Permission.TASK_UPDATE,
            Permission.TASK_CANCEL,
            Permission.WORKFLOW_CREATE,
            Permission.WORKFLOW_READ,
            Permission.AGENT_READ,
        },
        Role.VIEWER: {
            Permission.TASK_READ,
            Permission.WORKFLOW_READ,
            Permission.AGENT_READ,
        },
        Role.AGENT: {
            Permission.AGENT_REGISTER,
            Permission.TASK_READ,
        }
    }
    
    def __init__(self):
        """Initialize RBAC"""
        logger.info("RBAC initialized")
    
    def has_permission(
        self,
        user_permissions: List[str],
        required_permission: Permission
    ) -> bool:
        """
        Check if user has required permission
        
        Args:
            user_permissions: List of user permissions
            required_permission: Required permission
            
        Returns:
            True if user has permission
        """
        # Check for wildcard
        if Permission.ALL.value in user_permissions or "*" in user_permissions:
            return True
        
        # Check exact permission
        if required_permission.value in user_permissions:
            return True
        
        # Check permission hierarchy (e.g., task:* includes task:create)
        permission_parts = required_permission.value.split(":")
        if len(permission_parts) > 1:
            wildcard_permission = f"{permission_parts[0]}:*"
            if wildcard_permission in user_permissions:
                return True
        
        return False
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Get permissions for a role"""
        return self.ROLE_PERMISSIONS.get(role, set())
    
    def has_role_permission(
        self,
        role: Role,
        permission: Permission
    ) -> bool:
        """Check if role has permission"""
        role_perms = self.get_role_permissions(role)
        
        if Permission.ALL in role_perms:
            return True
        
        return permission in role_perms
    
    def add_role_permission(self, role: Role, permission: Permission):
        """Add permission to role (runtime modification)"""
        if role not in self.ROLE_PERMISSIONS:
            self.ROLE_PERMISSIONS[role] = set()
        self.ROLE_PERMISSIONS[role].add(permission)
        logger.info("Permission added to role", role=role, permission=permission)


# Global RBAC instance
_rbac: Optional[RBAC] = None


def get_rbac() -> RBAC:
    """Get global RBAC instance"""
    global _rbac
    if _rbac is None:
        _rbac = RBAC()
    return _rbac


def require_permission(permission: Permission):
    """
    FastAPI dependency to require specific permission
    
    Args:
        permission: Required permission
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        user: Dict = Depends(get_current_user)
    ) -> Dict:
        """Check if user has required permission"""
        user_permissions = user.get('permissions', [])
        rbac = get_rbac()
        
        if not rbac.has_permission(user_permissions, permission):
            logger.warning(
                "Permission denied",
                user_id=user.get('user_id'),
                permission=permission,
                user_permissions=user_permissions
            )
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value} required"
            )
        
        return user
    
    return permission_checker


def require_role(role: Role):
    """
    FastAPI dependency to require specific role
    
    Args:
        role: Required role
        
    Returns:
        Dependency function
    """
    async def role_checker(
        user: Dict = Depends(get_current_user)
    ) -> Dict:
        """Check if user has required role"""
        user_role = user.get('role')
        
        if user_role != role.value:
            logger.warning(
                "Role denied",
                user_id=user.get('user_id'),
                required_role=role,
                user_role=user_role
            )
            raise HTTPException(
                status_code=403,
                detail=f"Role denied: {role.value} required"
            )
        
        return user
    
    return role_checker

