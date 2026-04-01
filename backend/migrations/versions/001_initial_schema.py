"""initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "prospects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("role", sa.String(255)),
        sa.Column("company", sa.String(255)),
        sa.Column("industry", sa.String(255)),
        sa.Column("website", sa.String(500)),
        sa.Column("linkedin_url", sa.String(500)),
        sa.Column("notes", sa.Text),
        sa.Column("tags", JSONB, default=list),
        sa.Column("outreach_status", sa.String(50), default="new"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "research_summaries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", UUID(as_uuid=True), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("sources", JSONB, default=list),
        sa.Column("embedding", Vector(1536)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "email_drafts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", UUID(as_uuid=True), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("opening_line", sa.Text, nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("cta", sa.Text, nullable=False),
        sa.Column("follow_up", sa.Text),
        sa.Column("tone", sa.String(50), default="concise"),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("generation_metadata", JSONB),
        sa.Column("langfuse_trace_id", sa.String(255)),
        sa.Column("is_edited", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "sent_emails",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", UUID(as_uuid=True), sa.ForeignKey("prospects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("draft_id", UUID(as_uuid=True), sa.ForeignKey("email_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("provider_message_id", sa.String(500)),
        sa.Column("send_status", sa.String(50), default="sent"),
        sa.Column("reply_status", sa.String(50), default="none"),
        sa.Column("replied_at", sa.DateTime(timezone=True)),
        sa.Column("follow_up_scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("follow_up_sent", sa.Boolean, default=False),
        sa.Column("metadata", JSONB),
    )

    op.create_table(
        "memory_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("prospect_id", UUID(as_uuid=True), sa.ForeignKey("prospects.id", ondelete="SET NULL"), nullable=True),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", Vector(1536)),
        sa.Column("metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "feedback_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("draft_id", UUID(as_uuid=True), sa.ForeignKey("email_drafts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer),
        sa.Column("feedback_text", sa.Text),
        sa.Column("eval_personalization", sa.Float),
        sa.Column("eval_clarity", sa.Float),
        sa.Column("eval_spamminess", sa.Float),
        sa.Column("eval_factual_consistency", sa.Float),
        sa.Column("eval_metadata", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Indexes
    op.create_index("ix_prospects_email", "prospects", ["email"])
    op.create_index("ix_prospects_status", "prospects", ["outreach_status"])
    op.create_index("ix_email_drafts_prospect", "email_drafts", ["prospect_id"])
    op.create_index("ix_sent_emails_prospect", "sent_emails", ["prospect_id"])
    op.create_index("ix_memory_items_prospect", "memory_items", ["prospect_id"])
    op.create_index("ix_memory_items_type", "memory_items", ["memory_type"])


def downgrade() -> None:
    op.drop_table("feedback_events")
    op.drop_table("memory_items")
    op.drop_table("sent_emails")
    op.drop_table("email_drafts")
    op.drop_table("research_summaries")
    op.drop_table("prospects")
