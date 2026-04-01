import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class FeedbackCreate(BaseModel):
    rating: Optional[int] = None
    feedback_text: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        if v is not None and v not in range(1, 6):
            raise ValueError("Rating must be between 1 and 5")
        return v


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    draft_id: uuid.UUID
    rating: Optional[int] = None
    feedback_text: Optional[str] = None
    eval_personalization: Optional[float] = None
    eval_clarity: Optional[float] = None
    eval_spamminess: Optional[float] = None
    eval_factual_consistency: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}
