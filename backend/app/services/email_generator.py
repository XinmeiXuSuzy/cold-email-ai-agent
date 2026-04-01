"""
Email generation service — wires DSPy pipeline with LiteLLM and Langfuse.
"""
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import dspy

from app.config import settings
from app.models.prospect import Prospect, ResearchSummary
from app.models.email_draft import EmailDraft
from app.dspy_modules.email_pipeline import ColdEmailPipeline
from app.services.memory_service import memory_service
from app.services.langfuse_service import TraceContext


def _configure_dspy():
    """Configure DSPy with LiteLLM backend."""
    lm = dspy.LM(
        model=settings.litellm_model,
        api_key=settings.openai_api_key,
        temperature=0.7,
        max_tokens=1000,
    )
    dspy.configure(lm=lm)


_pipeline: Optional[ColdEmailPipeline] = None


def get_pipeline() -> ColdEmailPipeline:
    global _pipeline
    if _pipeline is None:
        _configure_dspy()
        _pipeline = ColdEmailPipeline()
    return _pipeline


async def generate_email(
    db: AsyncSession,
    prospect: Prospect,
    tone: str = "concise",
    additional_context: Optional[str] = None,
) -> EmailDraft:
    """Generate a personalized cold email draft for a prospect."""

    trace = TraceContext(
        name="email_generation",
        metadata={
            "prospect_id": str(prospect.id),
            "prospect_email": prospect.email,
            "tone": tone,
            "model": settings.litellm_model,
        },
    )
    trace_id = trace.start()

    # Get latest research summary
    result = await db.execute(
        select(ResearchSummary)
        .where(ResearchSummary.prospect_id == prospect.id)
        .order_by(ResearchSummary.created_at.desc())
        .limit(1)
    )
    research = result.scalar_one_or_none()
    research_content = research.content if research else (
        f"{prospect.name} works as {prospect.role or 'unknown role'} "
        f"at {prospect.company or 'unknown company'} in the {prospect.industry or 'unknown'} industry."
    )

    trace.span(name="research_loaded", input={"has_research": research is not None})

    # Retrieve memory context
    memory_items = await memory_service.search(
        db,
        query=f"cold email {prospect.company} {prospect.industry} {prospect.role}",
        top_k=3,
    )
    memory_context = (
        "\n".join(f"- {m.content[:200]}" for m in memory_items)
        if memory_items
        else ""
    )

    trace.span(name="memory_retrieved", output={"items": len(memory_items)})

    # Run DSPy pipeline (sync call inside async context)
    import asyncio
    pipeline = get_pipeline()

    generated = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: pipeline(
            prospect_name=prospect.name,
            prospect_role=prospect.role or "Professional",
            company=prospect.company or "their company",
            research_summary=research_content,
            tone=tone,
            additional_context=additional_context or "",
            memory_context=memory_context,
            include_follow_up=True,
        ),
    )

    trace.generation(
        name="cold_email",
        model=settings.litellm_model,
        prompt=f"prospect={prospect.email}, tone={tone}",
        completion={
            "subject": generated.subject,
            "body": generated.body,
        },
    )

    # Persist draft
    draft = EmailDraft(
        prospect_id=prospect.id,
        subject=generated.subject,
        opening_line=generated.opening_line,
        body=generated.body,
        cta=generated.cta,
        follow_up=generated.follow_up,
        tone=tone,
        status="draft",
        langfuse_trace_id=trace_id,
        generation_metadata={
            "model": settings.litellm_model,
            "tone": tone,
            "had_research": research is not None,
            "memory_items_used": len(memory_items),
        },
    )
    db.add(draft)
    await db.flush()

    # Save to memory
    full_email = f"Subject: {generated.subject}\n\n{generated.opening_line}\n\n{generated.body}\n\n{generated.cta}"
    await memory_service.save(
        db,
        content=f"Draft email for {prospect.name} ({prospect.company}): {full_email[:500]}",
        memory_type="draft",
        prospect_id=prospect.id,
        metadata={"draft_id": str(draft.id), "tone": tone},
    )

    trace.flush()
    return draft
