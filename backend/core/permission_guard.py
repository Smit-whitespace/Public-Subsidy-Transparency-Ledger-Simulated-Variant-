# backend/core/permission_guard.py

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.models.role import Role
from backend.core.security import get_current_user

def require_roles(*allowed_roles: str):
    """
    Dependency factory enforcing role-based access control.
    Usage:
        Depends(require_roles("admin"))
        Depends(require_roles("admin", "auditor"))
    """

    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):

        roles = (
            db.query(Role)
            .join(Role.users)
            .filter(Role.users.any(id=current_user.id))
            .all()
        )

        user_role_names = {r.name for r in roles}

        if not user_role_names.intersection(set(allowed_roles)):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker