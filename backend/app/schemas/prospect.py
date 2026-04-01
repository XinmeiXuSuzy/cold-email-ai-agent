import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator


class ProspectCreate(BaseModel):
    name: str
    email: EmailStr
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []


class ProspectUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    outreach_status: Optional[str] = None

    @field_validator("outreach_status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"new", "researched", "drafted", "sent", "replied", "archived"}
        if v and v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class ResearchSummaryResponse(BaseModel):
    id: uuid.UUID
    prospect_id: uuid.UUID
    content: str
    sources: Optional[List[str]] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class ProspectResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = []
    outreach_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProspectListResponse(BaseModel):
    items: List[ProspectResponse]
    total: int
    page: int
    page_size: int
