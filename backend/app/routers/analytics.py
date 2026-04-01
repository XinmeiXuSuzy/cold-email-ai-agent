from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.prospect import Prospect
from app.models.email_draft import EmailDraft
from app.models.sent_email import SentEmail
from app.models.feedback import FeedbackEvent
from app.schemas.analytics import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummary)
async def get_analytics(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)

    # Total prospects
    total_prospects_result = await db.execute(select(func.count()).select_from(Prospect))
    total_prospects = total_prospects_result.scalar() or 0

    # Prospects by status
    status_result = await db.execute(
        select(Prospect.outreach_status, func.count())
        .group_by(Prospect.outreach_status)
    )
    prospects_by_status = {row[0]: row[1] for row in status_result.all()}

    # Total drafts
    total_drafts_result = await db.execute(select(func.count()).select_from(EmailDraft))
    total_drafts = total_drafts_result.scalar() or 0

    # Total sent
    total_sent_result = await db.execute(
        select(func.count()).select_from(SentEmail).where(SentEmail.send_status == "sent")
    )
    total_sent = total_sent_result.scalar() or 0

    # Reply rate
    replied_result = await db.execute(
        select(func.count())
        .select_from(SentEmail)
        .where(SentEmail.reply_status.in_(["replied", "positive", "negative"]))
    )
    total_replied = replied_result.scalar() or 0
    reply_rate = (total_replied / total_sent) if total_sent > 0 else 0.0

    # Avg rating
    avg_rating_result = await db.execute(
        select(func.avg(FeedbackEvent.rating)).where(FeedbackEvent.rating.isnot(None))
    )
    avg_rating = avg_rating_result.scalar()

    # Emails sent last 7 days
    seven_days_ago = now - timedelta(days=7)
    sent_7d_result = await db.execute(
        select(func.count())
        .select_from(SentEmail)
        .where(SentEmail.sent_at >= seven_days_ago, SentEmail.send_status == "sent")
    )
    emails_sent_7d = sent_7d_result.scalar() or 0

    # Emails sent last 30 days
    thirty_days_ago = now - timedelta(days=30)
    sent_30d_result = await db.execute(
        select(func.count())
        .select_from(SentEmail)
        .where(SentEmail.sent_at >= thirty_days_ago, SentEmail.send_status == "sent")
    )
    emails_sent_30d = sent_30d_result.scalar() or 0

    return AnalyticsSummary(
        total_prospects=total_prospects,
        prospects_by_status=prospects_by_status,
        total_drafts=total_drafts,
        total_sent=total_sent,
        reply_rate=round(reply_rate, 3),
        avg_rating=round(float(avg_rating), 2) if avg_rating else None,
        emails_sent_last_7_days=emails_sent_7d,
        emails_sent_last_30_days=emails_sent_30d,
    )
