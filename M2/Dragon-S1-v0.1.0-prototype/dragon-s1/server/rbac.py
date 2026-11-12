from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, status

logger = logging.getLogger("dragon.rbac")


class Role(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {"*"},
    Role.MANAGER: {
        "requests.view", "requests.decide",
        "devices.view", "devices.manage",
        "sessions.view", "sessions.revoke",
        "users.view",
        "reports.view", "reports.generate",
        "audit.view",
        "notifications.view", "notifications.manage",
    },
    Role.OPERATOR: {
        "requests.view", "requests.decide",
        "devices.view",
        "sessions.view",
        "audit.view",
        "notifications.view",
    },
    Role.VIEWER: {
        "requests.view",
        "devices.view",
        "sessions.view",
        "audit.view",
    },
}


def has_permission(role: str | Role, permission: str) -> bool:
    try:
        r = Role(role) if isinstance(role, str) else role
    except ValueError:
        return False
    perms = PERMISSIONS.get(r, set())
    return "*" in perms or permission in perms


def require_permission(permission: str):
    """FastAPI dependency that checks role-based permission."""
    from dependencies import get_current_user
    
    async def _checker(user=Depends(get_current_user)):
        user_role = getattr(user, 'role', 'viewer')
        if not has_permission(user_role, permission):
            logger.warning("User %s (role=%s) denied permission: %s", getattr(user, 'username', '?'), user_role, permission)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission} requires higher role",
            )
        return user
    return _checker
