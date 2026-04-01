"""
Email sending service — supports mock and SMTP providers.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.email_draft import EmailDraft
from app.models.prospect import Prospect
from app.models.sent_email import SentEmail
from app.services.memory_service import memory_service


async def _send_mock(
    to_email: str, subject: str, body: str
) -> dict:
    """Mock send — logs to stdout and returns a fake message ID."""
    print(f"\n[MOCK EMAIL SEND]")
    print(f"  To: {to_email}")
    print(f"  Subject: {subject}")
    print(f"  Body (truncated): {body[:200]}...\n")
    return {"message_id": f"mock-{uuid.uuid4()}", "status": "sent"}


async def _send_smtp(to_email: str, subject: str, body: str) -> dict:
    """Send via SMTP using aiosmtplib."""
    import aiosmtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.from_name} <{settings.from_email}>"
    msg["To"] = to_email

    text_part = MIMEText(body, "plain")
    msg.attach(text_part)

    await aiosmtplib.send(
        msg,
        hostname=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_user,
        password=settings.smtp_password,
        start_tls=True,
    )

    return {"message_id": msg["Message-ID"] or f"smtp-{uuid.uuid4()}", "status": "sent"}


async def send_email(
    db: AsyncSession,
    draft: EmailDraft,
    prospect: Prospect,
    schedule_follow_up_days: Optional[int] = None,
) -> SentEmail:
    """Send an approved email draft and record the result."""

    full_body = (
        f"{draft.opening_line}\n\n{draft.body}\n\n{draft.cta}"
    )

    try:
        if settings.email_provider == "smtp":
            result = await _send_smtp(prospect.email, draft.subject, full_body)
        else:
            result = await _send_mock(prospect.email, draft.subject, full_body)
        send_status = "sent"
        provider_message_id = result.get("message_id")
    except Exception as e:
        print(f"[Email Send Error] {e}")
        send_status = "failed"
        provider_message_id = None

    follow_up_at = None
    if schedule_follow_up_days and send_status == "sent":
        follow_up_at = datetime.now(timezone.utc) + timedelta(days=schedule_follow_up_days)

    sent = SentEmail(
        prospect_id=prospect.id,
        draft_id=draft.id,
        subject=draft.subject,
        body=full_body,
        send_status=send_status,
        provider_message_id=provider_message_id,
        follow_up_scheduled_at=follow_up_at,
    )
    db.add(sent)

    # Update draft status
    draft.status = "sent" if send_status == "sent" else "draft"
    db.add(draft)

    # Update prospect status
    if send_status == "sent":
        prospect.outreach_status = "sent"
        db.add(prospect)

    await db.flush()

    # Save to memory
    await memory_service.save(
        db,
        content=(
            f"Sent cold email to {prospect.name} ({prospect.company}) on "
            f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}. "
            f"Subject: {draft.subject}. "
            f"Body preview: {full_body[:300]}"
        ),
        memory_type="sent_email",
        prospect_id=prospect.id,
        metadata={
            "sent_email_id": str(sent.id),
            "draft_id": str(draft.id),
            "send_status": send_status,
        },
    )

    return sent
