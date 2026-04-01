import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.prospect import Prospect
from app.models.email_draft import EmailDraft
from app.models.sent_email import SentEmail
from app.models.feedback import FeedbackEvent
from app.schemas.email import (
    EmailGenerateRequest,
    EmailDraftResponse,
    EmailDraftUpdate,
    EmailSendRequest,
    SentEmailResponse,
)
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.email_generator import generate_email
from app.services.email_sender import send_email
from app.services.evaluation_service import evaluate_email
from app.services.langfuse_service import TraceContext

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/generate", response_model=EmailDraftResponse, status_code=201)
async def generate_email_draft(
    request: EmailGenerateRequest, db: AsyncSession = Depends(get_db)
):
    """Generate a personalized cold email draft for a prospect."""
    result = await db.execute(
        select(Prospect).where(Prospect.id == request.prospect_id)
    )
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(404, "Prospect not found")

    try:
        draft = await generate_email(
            db=db,
            prospect=prospect,
            tone=request.tone,
            additional_context=request.additional_context,
        )
    except Exception as e:
        err_str = str(e)
        logger.error(f"[EmailGenerate] Failed for prospect {request.prospect_id}: {err_str}")
        if "insufficient_quota" in err_str or "quota" in err_str.lower():
            raise HTTPException(
                402,
                "OpenAI API quota exceeded. Please add credits at platform.openai.com/billing",
            )
        if "AuthenticationError" in err_str or "invalid_api_key" in err_str:
            raise HTTPException(
                401,
                "Invalid OpenAI API key. Check OPENAI_API_KEY in your .env file.",
            )
        if "RateLimitError" in err_str or "rate_limit" in err_str.lower():
            raise HTTPException(429, "OpenAI rate limit hit. Please wait and try again.")
        raise HTTPException(500, f"Email generation failed: {err_str[:200]}")

    # Run evaluation in background (non-blocking)
    try:
        trace = TraceContext(name="email_eval", metadata={"draft_id": str(draft.id)})
        trace.start()
        scores = await evaluate_email(
            subject=draft.subject,
            opening_line=draft.opening_line,
            body=draft.body,
            cta=draft.cta,
            trace=trace,
        )
        feedback = FeedbackEvent(
            draft_id=draft.id,
            eval_personalization=scores["personalization"],
            eval_clarity=scores["clarity"],
            eval_spamminess=scores["spamminess"],
            eval_factual_consistency=scores["factual_consistency"],
            eval_metadata={"auto_eval": True},
        )
        db.add(feedback)
        await db.flush()
        trace.flush()
    except Exception as e:
        print(f"[Auto-eval skipped] {e}")

    return draft


@router.get("", response_model=list[EmailDraftResponse])
async def list_drafts(
    prospect_id: uuid.UUID = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(EmailDraft)
    if prospect_id:
        query = query.where(EmailDraft.prospect_id == prospect_id)
    if status:
        query = query.where(EmailDraft.status == status)
    query = query.order_by(EmailDraft.created_at.desc()).limit(100)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{draft_id}", response_model=EmailDraftResponse)
async def get_draft(draft_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailDraft).where(EmailDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(404, "Draft not found")
    return draft


@router.patch("/{draft_id}", response_model=EmailDraftResponse)
async def update_draft(
    draft_id: uuid.UUID, data: EmailDraftUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(EmailDraft).where(EmailDraft.id == draft_id))
    draft = result.scalar_one_or_none()
    if not draft:
        raise HTTPException(404, "Draft not found")

    updates = data.model_dump(exclude_none=True)
    if updates:
        draft.is_edited = True
    for field, value in updates.items():
        setattr(draft, field, value)

    db.add(draft)
    await db.flush()
    return draft


@router.post("/send", response_model=SentEmailResponse, status_code=201)
async def send_email_endpoint(
    request: EmailSendRequest, db: AsyncSession = Depends(get_db)
):
    """Send an approved email draft."""
    draft_result = await db.execute(
        select(EmailDraft).where(EmailDraft.id == request.draft_id)
    )
    draft = draft_result.scalar_one_or_none()
    if not draft:
        raise HTTPException(404, "Draft not found")

    if draft.status == "sent":
        raise HTTPException(400, "This draft has already been sent")

    prospect_result = await db.execute(
        select(Prospect).where(Prospect.id == draft.prospect_id)
    )
    prospect = prospect_result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(404, "Prospect not found")

    sent = await send_email(
        db=db,
        draft=draft,
        prospect=prospect,
        schedule_follow_up_days=request.schedule_follow_up_days,
    )
    return sent


@router.get("/sent/{sent_id}", response_model=SentEmailResponse)
async def get_sent_email(sent_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SentEmail).where(SentEmail.id == sent_id))
    sent = result.scalar_one_or_none()
    if not sent:
        raise HTTPException(404, "Sent email not found")
    return sent


@router.get("/sent", response_model=list[SentEmailResponse])
async def list_sent_emails(
    prospect_id: uuid.UUID = None, db: AsyncSession = Depends(get_db)
):
    query = select(SentEmail)
    if prospect_id:
        query = query.where(SentEmail.prospect_id == prospect_id)
    query = query.order_by(SentEmail.sent_at.desc()).limit(100)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/{draft_id}/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    draft_id: uuid.UUID, data: FeedbackCreate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(EmailDraft).where(EmailDraft.id == draft_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Draft not found")

    feedback = FeedbackEvent(draft_id=draft_id, **data.model_dump())
    db.add(feedback)
    await db.flush()
    return feedback


@router.patch("/sent/{sent_id}/reply-status", response_model=SentEmailResponse)
async def update_reply_status(
    sent_id: uuid.UUID, reply_status: str, db: AsyncSession = Depends(get_db)
):
    allowed = {"none", "replied", "positive", "negative"}
    if reply_status not in allowed:
        raise HTTPException(400, f"reply_status must be one of {allowed}")

    result = await db.execute(select(SentEmail).where(SentEmail.id == sent_id))
    sent = result.scalar_one_or_none()
    if not sent:
        raise HTTPException(404, "Sent email not found")

    from datetime import datetime, timezone
    sent.reply_status = reply_status
    if reply_status != "none":
        sent.replied_at = datetime.now(timezone.utc)

        # Update prospect status
        p_result = await db.execute(
            select(Prospect).where(Prospect.id == sent.prospect_id)
        )
        prospect = p_result.scalar_one_or_none()
        if prospect:
            prospect.outreach_status = "replied"
            db.add(prospect)

    db.add(sent)
    await db.flush()
    return sent
