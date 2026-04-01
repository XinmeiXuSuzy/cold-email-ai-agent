import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class SentEmail(Base):
    __tablename__ = "sent_emails"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prospect_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_drafts.id", ondelete="CASCADE"), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(500))
    send_status: Mapped[str] = mapped_column(
        String(50), default="sent"
    )  # sent, failed, bounced
    reply_status: Mapped[str] = mapped_column(
        String(50), default="none"
    )  # none, replied, positive, negative
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    follow_up_scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    follow_up_sent: Mapped[bool] = mapped_column(default=False)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)

    prospect: Mapped["Prospect"] = relationship(back_populates="sent_emails")  # noqa: F821
    draft: Mapped["EmailDraft"] = relationship(back_populates="sent_emails")  # noqa: F821
