import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class EmailDraft(Base):
    __tablename__ = "email_drafts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prospect_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    opening_line: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    cta: Mapped[str] = mapped_column(Text, nullable=False)
    follow_up: Mapped[Optional[str]] = mapped_column(Text)
    tone: Mapped[str] = mapped_column(String(50), default="concise")
    status: Mapped[str] = mapped_column(
        String(50), default="draft"
    )  # draft, approved, sent, archived
    generation_metadata: Mapped[Optional[dict]] = mapped_column(JSONB)
    langfuse_trace_id: Mapped[Optional[str]] = mapped_column(String(255))
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    prospect: Mapped["Prospect"] = relationship(back_populates="email_drafts")  # noqa: F821
    sent_emails: Mapped[list["SentEmail"]] = relationship(  # noqa: F821
        back_populates="draft", cascade="all, delete-orphan"
    )
    feedback_events: Mapped[list["FeedbackEvent"]] = relationship(  # noqa: F821
        back_populates="draft", cascade="all, delete-orphan"
    )
