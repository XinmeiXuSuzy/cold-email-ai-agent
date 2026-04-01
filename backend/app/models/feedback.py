import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_drafts.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[Optional[int]] = mapped_column()  # 1-5
    feedback_text: Mapped[Optional[str]] = mapped_column(Text)
    eval_personalization: Mapped[Optional[float]] = mapped_column(Float)
    eval_clarity: Mapped[Optional[float]] = mapped_column(Float)
    eval_spamminess: Mapped[Optional[float]] = mapped_column(Float)
    eval_factual_consistency: Mapped[Optional[float]] = mapped_column(Float)
    eval_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    draft: Mapped["EmailDraft"] = relationship(back_populates="feedback_events")  # noqa: F821
