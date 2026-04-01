"""
DSPy-based email generation pipeline.

Uses DSPy signatures and modules to structure the cold email generation
in a deterministic, composable, and evaluable way.
"""
import dspy
from dataclasses import dataclass
from typing import Optional


# ── DSPy Signatures ──────────────────────────────────────────────────────────

class SubjectLineSignature(dspy.Signature):
    """Generate a compelling, personalized email subject line."""

    prospect_name: str = dspy.InputField(desc="Full name of the prospect")
    prospect_role: str = dspy.InputField(desc="Role or job title")
    company: str = dspy.InputField(desc="Company name")
    research_summary: str = dspy.InputField(desc="Research context about the prospect")
    tone: str = dspy.InputField(desc="Tone: concise, warm, direct, consultative, or casual")

    subject_line: str = dspy.OutputField(
        desc="A short, personalized subject line (under 60 chars). No spam words. No brackets."
    )


class OpeningLineSignature(dspy.Signature):
    """Generate a personalized, non-generic opening line for a cold email."""

    prospect_name: str = dspy.InputField()
    research_summary: str = dspy.InputField()
    tone: str = dspy.InputField()

    opening_line: str = dspy.OutputField(
        desc=(
            "One to two sentences that feel genuinely personalized. "
            "Reference something specific about the prospect. "
            "Do not start with 'I hope this email finds you well' or similar clichés."
        )
    )


class EmailBodySignature(dspy.Signature):
    """Generate the main body of a cold email."""

    prospect_name: str = dspy.InputField()
    prospect_role: str = dspy.InputField()
    company: str = dspy.InputField()
    research_summary: str = dspy.InputField()
    opening_line: str = dspy.InputField(desc="The opening line already written")
    tone: str = dspy.InputField()
    additional_context: str = dspy.InputField(desc="Any extra context from the sender")
    memory_context: str = dspy.InputField(desc="Relevant past outreach or notes")

    body: str = dspy.OutputField(
        desc=(
            "2-3 short paragraphs. Explain the value proposition concisely. "
            "Reference the research. Match the specified tone. "
            "Do not repeat the opening line. Plain text, no markdown."
        )
    )


class CTASignature(dspy.Signature):
    """Generate a clear, low-friction call-to-action."""

    tone: str = dspy.InputField()
    body: str = dspy.InputField(desc="The email body already written")

    cta: str = dspy.OutputField(
        desc=(
            "One sentence CTA. Should be easy to act on — a meeting, a quick reply, "
            "or a resource link. Match the tone."
        )
    )


class FollowUpSignature(dspy.Signature):
    """Generate a short follow-up email for if the prospect doesn't reply."""

    prospect_name: str = dspy.InputField()
    original_email: str = dspy.InputField(desc="The original email body")
    tone: str = dspy.InputField()

    follow_up: str = dspy.OutputField(
        desc=(
            "A short 2-3 sentence follow-up email. "
            "Reference the original email briefly. "
            "Add a slightly different angle or value prop. "
            "Keep it friendly and non-pushy."
        )
    )


# ── DSPy Module ───────────────────────────────────────────────────────────────

@dataclass
class GeneratedEmail:
    subject: str
    opening_line: str
    body: str
    cta: str
    follow_up: Optional[str] = None


class ColdEmailPipeline(dspy.Module):
    """Multi-step DSPy pipeline for generating structured cold emails."""

    def __init__(self):
        super().__init__()
        self.gen_subject = dspy.ChainOfThought(SubjectLineSignature)
        self.gen_opening = dspy.ChainOfThought(OpeningLineSignature)
        self.gen_body = dspy.ChainOfThought(EmailBodySignature)
        self.gen_cta = dspy.ChainOfThought(CTASignature)
        self.gen_followup = dspy.ChainOfThought(FollowUpSignature)

    def forward(
        self,
        prospect_name: str,
        prospect_role: str,
        company: str,
        research_summary: str,
        tone: str = "concise",
        additional_context: str = "",
        memory_context: str = "",
        include_follow_up: bool = True,
    ) -> GeneratedEmail:
        subject_result = self.gen_subject(
            prospect_name=prospect_name,
            prospect_role=prospect_role,
            company=company,
            research_summary=research_summary,
            tone=tone,
        )

        opening_result = self.gen_opening(
            prospect_name=prospect_name,
            research_summary=research_summary,
            tone=tone,
        )

        body_result = self.gen_body(
            prospect_name=prospect_name,
            prospect_role=prospect_role,
            company=company,
            research_summary=research_summary,
            opening_line=opening_result.opening_line,
            tone=tone,
            additional_context=additional_context or "None provided.",
            memory_context=memory_context or "No prior outreach.",
        )

        cta_result = self.gen_cta(
            tone=tone,
            body=body_result.body,
        )

        follow_up = None
        if include_follow_up:
            full_body = f"{opening_result.opening_line}\n\n{body_result.body}\n\n{cta_result.cta}"
            fu_result = self.gen_followup(
                prospect_name=prospect_name,
                original_email=full_body,
                tone=tone,
            )
            follow_up = fu_result.follow_up

        return GeneratedEmail(
            subject=subject_result.subject_line,
            opening_line=opening_result.opening_line,
            body=body_result.body,
            cta=cta_result.cta,
            follow_up=follow_up,
        )
