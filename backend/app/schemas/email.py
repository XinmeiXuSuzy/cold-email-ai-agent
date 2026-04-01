import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


VALID_TONES = {"concise", "warm", "direct", "consultative", "casual"}


class EmailGenerateRequest(BaseModel):
    prospect_id: uuid.UUID
    tone: str = "concise"
    additional_context: Optional[str] = None
    regenerate: bool = False

    @field_validator("tone")
    @classmethod
    def validate_tone(cls, v):
        if v not in VALID_TONES:
            raise ValueError(f"Tone must be one of {VALID_TONES}")
        return v


class EmailDraftResponse(BaseModel):
    id: uuid.UUID
    prospect_id: uuid.UUID
    subject: str
    opening_line: str
    body: str
    cta: str
    follow_up: Optional[str] = None
    tone: str
    status: str
    is_edited: bool
    langfuse_trace_id: Optional[str] = None
    generation_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmailDraftUpdate(BaseModel):
    subject: Optional[str] = None
    opening_line: Optional[str] = None
    body: Optional[str] = None
    cta: Optional[str] = None
    follow_up: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        allowed = {"draft", "approved", "sent", "archived"}
        if v and v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class EmailSendRequest(BaseModel):
    draft_id: uuid.UUID
    schedule_follow_up_days: Optional[int] = None


class SentEmailResponse(BaseModel):
    id: uuid.UUID
    prospect_id: uuid.UUID
    draft_id: uuid.UUID
    subject: str
    body: str
    sent_at: datetime
    send_status: str
    reply_status: str
    replied_at: Optional[datetime] = None
    follow_up_scheduled_at: Optional[datetime] = None
    follow_up_sent: bool

    model_config = {"from_attributes": True}
