import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import litellm

from app.config import settings
from app.models.prospect import Prospect, ResearchSummary
from app.models.memory import MemoryItem
from app.services.embedding import get_embedding
from app.services.memory_service import memory_service
from app.services.langfuse_service import TraceContext

logger = logging.getLogger(__name__)


RESEARCH_PROMPT = """You are a research assistant helping to craft personalized cold emails.

Given the following prospect information, produce a concise research summary that will help
write a highly personalized cold email. Focus on:
1. What the prospect likely cares about based on their role/industry
2. Potential pain points or goals relevant to an outreach
3. Any interesting angles for personalization
4. Key facts to reference in the email

Prospect Information:
Name: {name}
Role: {role}
Company: {company}
Industry: {industry}
Website: {website}
LinkedIn: {linkedin_url}
Notes: {notes}

Relevant past context from memory:
{memory_context}

Write a 3-5 sentence research summary that captures the most useful context for writing the email.
Be specific and factual. Do not make up information."""


async def build_research_summary(
    db: AsyncSession,
    prospect: Prospect,
    trace: Optional[TraceContext] = None,
) -> ResearchSummary:
    """Build a research summary for a prospect using LLM + memory retrieval."""

    query = f"{prospect.name} {prospect.role} {prospect.company} {prospect.industry}"
    memory_items = await memory_service.search(
        db, query=query, top_k=3, prospect_id=prospect.id
    )

    general_memories = await memory_service.search(
        db,
        query=f"{prospect.industry} cold email outreach",
        top_k=2,
        memory_type="sent_email",
    )

    all_memories = memory_items + [m for m in general_memories if m not in memory_items]
    memory_context = (
        "\n\n".join(f"- {m.content[:300]}" for m in all_memories[:5])
        if all_memories
        else "No prior context available."
    )

    prompt = RESEARCH_PROMPT.format(
        name=prospect.name or "",
        role=prospect.role or "Unknown",
        company=prospect.company or "Unknown",
        industry=prospect.industry or "Unknown",
        website=prospect.website or "N/A",
        linkedin_url=prospect.linkedin_url or "N/A",
        notes=prospect.notes or "None",
        memory_context=memory_context,
    )

    response = await litellm.acompletion(
        model=settings.litellm_model,
        messages=[{"role": "user", "content": prompt}],
        api_key=settings.openai_api_key,
        temperature=0.3,
        max_tokens=500,
    )

    content = response.choices[0].message.content.strip()

    if trace:
        trace.generation(
            name="research_summary",
            model=settings.litellm_model,
            prompt=prompt,
            completion=content,
            usage={
                "input": response.usage.prompt_tokens,
                "output": response.usage.completion_tokens,
            },
        )

    # Embedding is best-effort — research still saves even if the API is unavailable
    try:
        embedding = await get_embedding(content)
    except Exception as e:
        logger.warning(f"[ResearchService] Embedding failed, saving without vector: {e}")
        embedding = None

    existing = await db.execute(
        select(ResearchSummary)
        .where(ResearchSummary.prospect_id == prospect.id)
        .order_by(ResearchSummary.created_at.desc())
        .limit(1)
    )
    old = existing.scalar_one_or_none()
    if old:
        await db.delete(old)

    summary = ResearchSummary(
        prospect_id=prospect.id,
        content=content,
        sources=[],
        embedding=embedding,
    )
    db.add(summary)
    await db.flush()

    await memory_service.save(
        db,
        content=f"Research for {prospect.name} ({prospect.company}): {content}",
        memory_type="research",
        prospect_id=prospect.id,
        metadata={"prospect_email": prospect.email},
    )

    return summary
