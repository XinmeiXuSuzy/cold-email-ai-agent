import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base


class MemoryItem(Base):
    __tablename__ = "memory_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prospect_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("prospects.id", ondelete="SET NULL"), nullable=True
    )
    memory_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # sent_email, reply, note, edit, company_info
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
