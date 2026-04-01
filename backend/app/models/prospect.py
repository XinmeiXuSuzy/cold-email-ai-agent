import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base


class Prospect(Base):
    __tablename__ = "prospects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    industry: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    tags: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    outreach_status: Mapped[str] = mapped_column(
        String(50), default="new"
    )  # new, researched, drafted, sent, replied, archived
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    research_summaries: Mapped[list["ResearchSummary"]] = relationship(
        back_populates="prospect", cascade="all, delete-orphan"
    )
    email_drafts: Mapped[list["EmailDraft"]] = relationship(  # noqa: F821
        back_populates="prospect", cascade="all, delete-orphan"
    )
    sent_emails: Mapped[list["SentEmail"]] = relationship(  # noqa: F821
        back_populates="prospect", cascade="all, delete-orphan"
    )


class ResearchSummary(Base):
    __tablename__ = "research_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prospect_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[dict]] = mapped_column(JSONB, default=list)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    prospect: Mapped["Prospect"] = relationship(back_populates="research_summaries")
