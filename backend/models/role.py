"""
backend/models/role.py
"""

from datetime import datetime
import json
from typing import Any, Dict, List

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.connection import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )

    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )

    display_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    permissions: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    users: Mapped[List["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles",
    )

    # ----------------------------------------------------------

    def has_permission(self, perm: str) -> bool:
        if not self.permissions:
            return False

        try:
            perms_list = json.loads(self.permissions)
            if isinstance(perms_list, list):
                return perm in perms_list
        except Exception:
            pass

        return perm in [p.strip() for p in self.permissions.split(",")]

    # ----------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }