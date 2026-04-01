import csv
import io
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.prospect import Prospect, ResearchSummary
from app.schemas.prospect import (
    ProspectCreate,
    ProspectUpdate,
    ProspectResponse,
    ProspectListResponse,
    ResearchSummaryResponse,
)
from app.services.research_service import build_research_summary
from app.services.langfuse_service import TraceContext

router = APIRouter(prefix="/prospects", tags=["prospects"])


@router.post("", response_model=ProspectResponse, status_code=201)
async def create_prospect(data: ProspectCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Prospect).where(Prospect.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, f"Prospect with email {data.email} already exists")

    prospect = Prospect(**data.model_dump())
    db.add(prospect)
    await db.flush()
    return prospect


@router.post("/upload", status_code=201)
async def upload_prospects_csv(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """Upload prospects from a CSV file. Required columns: name, email. Optional: role, company, industry, website, linkedin_url, notes."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "File must be a CSV")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    required = {"name", "email"}
    fieldnames = set(reader.fieldnames or [])
    if not required.issubset(fieldnames):
        raise HTTPException(400, f"CSV must contain columns: {required}")

    created, skipped = [], []
    for row in reader:
        email = row.get("email", "").strip().lower()
        name = row.get("name", "").strip()
        if not email or not name:
            skipped.append(row)
            continue

        existing = await db.execute(select(Prospect).where(Prospect.email == email))
        if existing.scalar_one_or_none():
            skipped.append(email)
            continue

        prospect = Prospect(
            name=name,
            email=email,
            role=row.get("role", "").strip() or None,
            company=row.get("company", "").strip() or None,
            industry=row.get("industry", "").strip() or None,
            website=row.get("website", "").strip() or None,
            linkedin_url=row.get("linkedin_url", "").strip() or None,
            notes=row.get("notes", "").strip() or None,
        )
        db.add(prospect)
        created.append(email)

    await db.flush()
    return {"created": len(created), "skipped": len(skipped), "emails": created}


@router.get("", response_model=ProspectListResponse)
async def list_prospects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Prospect)
    if status:
        query = query.where(Prospect.outreach_status == status)
    if search:
        term = f"%{search}%"
        query = query.where(
            Prospect.name.ilike(term)
            | Prospect.email.ilike(term)
            | Prospect.company.ilike(term)
        )

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.order_by(Prospect.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    return ProspectListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(404, "Prospect not found")
    return prospect


@router.patch("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: uuid.UUID, data: ProspectUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(404, "Prospect not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(prospect, field, value)
    db.add(prospect)
    await db.flush()
    return prospect


@router.delete("/{prospect_id}", status_code=204)
async def delete_prospect(prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(404, "Prospect not found")
    await db.delete(prospect)


@router.post("/{prospect_id}/research", response_model=ResearchSummaryResponse)
async def research_prospect(
    prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Trigger research enrichment for a prospect."""
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(404, "Prospect not found")

    trace = TraceContext(
        name="prospect_research",
        metadata={"prospect_id": str(prospect_id)},
    )
    trace.start()

    try:
        summary = await build_research_summary(db, prospect, trace)
    except Exception as e:
        err_str = str(e)
        logger.error(f"[Research] Failed for prospect {prospect_id}: {err_str}")
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
        raise HTTPException(500, f"Research failed: {err_str[:200]}")

    prospect.outreach_status = "researched"
    db.add(prospect)
    await db.flush()

    trace.flush()
    return summary


@router.get("/{prospect_id}/research", response_model=ResearchSummaryResponse)
async def get_research(prospect_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchSummary)
        .where(ResearchSummary.prospect_id == prospect_id)
        .order_by(ResearchSummary.created_at.desc())
        .limit(1)
    )
    summary = result.scalar_one_or_none()
    if not summary:
        raise HTTPException(404, "No research found. Run POST /research first.")
    return summary
