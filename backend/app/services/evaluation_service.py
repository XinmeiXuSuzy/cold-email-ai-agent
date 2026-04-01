"""
Automated evaluation of generated emails using LLM-as-judge.
Scores are 0.0–1.0 for each dimension.
"""
import json
from typing import Optional
import litellm

from app.config import settings
from app.services.langfuse_service import TraceContext


EVAL_PROMPT = """You are evaluating a cold email draft. Score the email on four dimensions.
Return ONLY a valid JSON object with the keys below.

Email to evaluate:
Subject: {subject}
Opening: {opening_line}
Body: {body}
CTA: {cta}

Scores (0.0 to 1.0):
- personalization: How specific and tailored is this to the recipient? (1.0 = very personalized)
- clarity: Is the message clear, well-structured, and easy to read? (1.0 = very clear)
- spamminess: How spammy or salesy does this feel? (1.0 = very spammy, 0.0 = natural)
- factual_consistency: Are there any made-up facts or contradictions? (1.0 = fully consistent)

Respond with only JSON:
{{"personalization": 0.0, "clarity": 0.0, "spamminess": 0.0, "factual_consistency": 0.0}}"""


async def evaluate_email(
    subject: str,
    opening_line: str,
    body: str,
    cta: str,
    trace: Optional[TraceContext] = None,
) -> dict:
    """Run LLM-as-judge evaluation on an email draft."""
    prompt = EVAL_PROMPT.format(
        subject=subject,
        opening_line=opening_line,
        body=body,
        cta=cta,
    )

    try:
        response = await litellm.acompletion(
            model=settings.litellm_model,
            messages=[{"role": "user", "content": prompt}],
            api_key=settings.openai_api_key,
            temperature=0.0,
            max_tokens=150,
        )
        content = response.choices[0].message.content.strip()

        # Extract JSON even if wrapped in markdown code fences
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        scores = json.loads(content)

        if trace:
            for name, value in scores.items():
                trace.score(name=f"eval_{name}", value=float(value))

        return {
            "personalization": float(scores.get("personalization", 0.5)),
            "clarity": float(scores.get("clarity", 0.5)),
            "spamminess": float(scores.get("spamminess", 0.5)),
            "factual_consistency": float(scores.get("factual_consistency", 0.5)),
        }
    except Exception as e:
        print(f"[Evaluation Error] {e}")
        return {
            "personalization": 0.5,
            "clarity": 0.5,
            "spamminess": 0.5,
            "factual_consistency": 0.5,
        }
