"""
backend/schemas/project.py

Pydantic schemas for Project entity: create/update/read shapes and simple normalization/validation.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, validator


class ProjectBase(BaseModel):
    """
    Base schema for project records containing shared fields.
    Used as foundation for create/update request models.
    """
    name: str = Field(..., max_length=255, description="Project name")
    subsidy_id: Optional[int] = Field(None, ge=1, description="Related subsidy id")
    description: Optional[str] = Field(None, description="Long description")
    metadata: Optional[str] = Field(None, description="Optional JSON string for free-form metadata")
    owner: Optional[str] = Field(None, max_length=255, description="Department or owner identifier")
    start_date: Optional[datetime] = Field(None, description="Start datetime")
    end_date: Optional[datetime] = Field(None, description="End datetime")
    status: str = Field("planned", max_length=50, description="Short status code, e.g., planned, active, completed")


class ProjectCreate(ProjectBase):
    """
    Schema for creating new project records.
    Server normalizes name/status and stores metadata as string for V1.
    Accepts metadata as dict or string; converts dict to compact JSON.
    """
    
    @validator("name")
    def normalize_name(cls, v):
        """Strip whitespace from name and reject empty values."""
        if v is None:
            raise ValueError("Project name cannot be None")
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty after stripping whitespace")
        return stripped
    
    @validator("status")
    def normalize_status(cls, v):
        """Normalize status to lowercase and strip whitespace."""
        if v is None:
            return v
        return v.strip().lower()
    
    @validator("metadata", pre=True)
    def normalize_metadata(cls, v):
        """
        Convert metadata dict to compact JSON string.
        Accepts dict or string input; stores as string.
        """
        if v is None:
            return None
        if isinstance(v, dict):
            import json
            return json.dumps(v, separators=(",", ":"))
        if isinstance(v, str):
            return v.strip()
        return v


class ProjectUpdate(BaseModel):
    """
    Schema for partial updates to project records (PATCH operations).
    All fields optional; same normalization applied when provided.
    """
    name: Optional[str] = Field(None, max_length=255, description="Project name")
    subsidy_id: Optional[int] = Field(None, ge=1, description="Related subsidy id")
    description: Optional[str] = Field(None, description="Long description")
    metadata: Optional[str] = Field(None, description="Optional JSON string for free-form metadata")
    owner: Optional[str] = Field(None, max_length=255, description="Department or owner identifier")
    start_date: Optional[datetime] = Field(None, description="Start datetime")
    end_date: Optional[datetime] = Field(None, description="End datetime")
    status: Optional[str] = Field(None, max_length=50, description="Short status code, e.g., planned, active, completed")
    
    @validator("name")
    def normalize_name(cls, v):
        """Strip whitespace from name and reject empty values if provided."""
        if v is None:
            return None
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty after stripping whitespace")
        return stripped
    
    @validator("status")
    def normalize_status(cls, v):
        """Normalize status to lowercase and strip whitespace if provided."""
        if v is None:
            return None
        return v.strip().lower()
    
    @validator("metadata", pre=True)
    def normalize_metadata(cls, v):
        """
        Convert metadata dict to compact JSON string.
        Accepts dict or string input; stores as string.
        """
        if v is None:
            return None
        if isinstance(v, dict):
            import json
            return json.dumps(v, separators=(",", ":"))
        if isinstance(v, str):
            return v.strip()
        return v


class Project(ProjectBase):
    """
    Full project record schema returned by API endpoints.
    Read-only model with auto-generated fields like id, created_at, and updated_at.
    """
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
        from_attributes = True


__all__ = ["ProjectBase", "ProjectCreate", "ProjectUpdate", "Project"]

# Example: ProjectCreate(name="School Renovation", subsidy_id=1, owner="education-dept")