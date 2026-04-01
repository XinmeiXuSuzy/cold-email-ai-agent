"""
Smoke tests for email draft and send endpoints.
Email generation is mocked to avoid LLM calls in tests.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_generate():
    """Mock the email generation service to avoid LLM calls."""
    from app.dspy_modules.email_pipeline import GeneratedEmail

    async def fake_generate(db, prospect, tone="concise", additional_context=None):
        from app.models.email_draft import EmailDraft
        draft = EmailDraft(
            id=uuid.uuid4(),
            prospect_id=prospect.id,
            subject="Test subject line",
            opening_line="I noticed your work at their company.",
            body="Here is the email body content.",
            cta="Would you be open to a quick chat?",
            follow_up="Just following up on my earlier email.",
            tone=tone,
            status="draft",
            langfuse_trace_id="mock-trace",
            is_edited=False,
        )
        db.add(draft)
        await db.flush()
        return draft

    return fake_generate


@pytest.mark.asyncio
async def test_list_drafts(client):
    res = await client.get("/emails")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


@pytest.mark.asyncio
async def test_generate_requires_valid_prospect(client):
    res = await client.post(
        "/emails/generate",
        json={"prospect_id": str(uuid.uuid4()), "tone": "concise"},
    )
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_generate_and_send_flow(client, mock_generate):
    # Create a prospect
    create_res = await client.post(
        "/prospects",
        json={
            "name": "Email Test User",
            "email": "emailtest@example.com",
            "company": "TestCo",
        },
    )
    assert create_res.status_code == 201
    prospect_id = create_res.json()["id"]

    # Generate a draft (mocked)
    with patch("app.routers.emails.generate_email", mock_generate), \
         patch("app.routers.emails.evaluate_email", new_callable=AsyncMock) as mock_eval:
        mock_eval.return_value = {
            "personalization": 0.8,
            "clarity": 0.9,
            "spamminess": 0.1,
            "factual_consistency": 0.9,
        }

        gen_res = await client.post(
            "/emails/generate",
            json={"prospect_id": prospect_id, "tone": "concise"},
        )

    assert gen_res.status_code == 201
    draft = gen_res.json()
    assert draft["prospect_id"] == prospect_id
    draft_id = draft["id"]

    # Get draft
    get_res = await client.get(f"/emails/{draft_id}")
    assert get_res.status_code == 200

    # Edit draft
    patch_res = await client.patch(
        f"/emails/{draft_id}",
        json={"subject": "Updated subject"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["subject"] == "Updated subject"
    assert patch_res.json()["is_edited"] is True

    # Send (mock sender)
    with patch("app.routers.emails.send_email", new_callable=AsyncMock) as mock_send:
        from app.models.sent_email import SentEmail
        fake_sent = MagicMock(spec=SentEmail)
        fake_sent.id = uuid.uuid4()
        fake_sent.prospect_id = uuid.UUID(prospect_id)
        fake_sent.draft_id = uuid.UUID(draft_id)
        fake_sent.subject = "Updated subject"
        fake_sent.body = "Test body"
        fake_sent.sent_at = "2024-01-01T00:00:00"
        fake_sent.send_status = "sent"
        fake_sent.reply_status = "none"
        fake_sent.replied_at = None
        fake_sent.follow_up_scheduled_at = None
        fake_sent.follow_up_sent = False
        mock_send.return_value = fake_sent

        send_res = await client.post(
            "/emails/send",
            json={"draft_id": draft_id},
        )
    assert send_res.status_code == 201


@pytest.mark.asyncio
async def test_feedback(client, mock_generate):
    create_res = await client.post(
        "/prospects",
        json={"name": "Feedback User", "email": "feedback@example.com"},
    )
    prospect_id = create_res.json()["id"]

    with patch("app.routers.emails.generate_email", mock_generate), \
         patch("app.routers.emails.evaluate_email", new_callable=AsyncMock) as mock_eval:
        mock_eval.return_value = {
            "personalization": 0.7,
            "clarity": 0.8,
            "spamminess": 0.2,
            "factual_consistency": 0.9,
        }
        gen_res = await client.post(
            "/emails/generate",
            json={"prospect_id": prospect_id, "tone": "warm"},
        )
    draft_id = gen_res.json()["id"]

    res = await client.post(
        f"/emails/{draft_id}/feedback",
        json={"rating": 4, "feedback_text": "Good personalization, CTA could be sharper."},
    )
    assert res.status_code == 201
    assert res.json()["rating"] == 4
