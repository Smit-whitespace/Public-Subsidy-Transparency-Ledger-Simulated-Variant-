from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.models.user import User
from backend.models.role import Role
from backend.core.permissions import Permissions
from backend.core.security import require_permission

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================
# LIST USERS WITH ROLES
# ============================================================

@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission(Permissions.ADMIN_MANAGE_USERS)),
):
    users = db.query(User).all()

    return [
        {
            "id": user.id,
            "username": user.username,
            "roles": [role.name for role in user.roles],
        }
        for user in users
    ]


# ============================================================
# LIST ALL ROLES
# ============================================================

@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    _: None = Depends(require_permission(Permissions.ADMIN_MANAGE_USERS)),
):
    roles = db.query(Role).all()

    return [
        {
            "id": role.id,
            "name": role.name,
            "permissions": role.permissions,
        }
        for role in roles
    ]


# ============================================================
# ASSIGN ROLE
# ============================================================

@router.post("/assign-role")
def assign_role(
    username: str,
    role_name: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission(Permissions.ADMIN_MANAGE_USERS)),
):
    user = db.query(User).filter(User.username == username).first()
    role = db.query(Role).filter(Role.name == role_name).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role in user.roles:
        return {"message": "Role already assigned"}

    user.roles.append(role)
    db.commit()

    return {"message": f"Role '{role_name}' assigned to '{username}'"}


# ============================================================
# REMOVE ROLE
# ============================================================

@router.post("/remove-role")
def remove_role(
    username: str,
    role_name: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_permission(Permissions.ADMIN_MANAGE_USERS)),
):
    user = db.query(User).filter(User.username == username).first()
    role = db.query(Role).filter(Role.name == role_name).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role not in user.roles:
        return {"message": "Role not assigned"}

    user.roles.remove(role)
    db.commit()

    return {"message": f"Role '{role_name}' removed from '{username}'"}