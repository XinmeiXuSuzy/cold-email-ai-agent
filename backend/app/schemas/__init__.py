from app.schemas.prospect import (
    ProspectCreate,
    ProspectUpdate,
    ProspectResponse,
    ProspectListResponse,
    ResearchSummaryResponse,
)
from app.schemas.email import (
    EmailGenerateRequest,
    EmailDraftResponse,
    EmailDraftUpdate,
    EmailSendRequest,
    SentEmailResponse,
)
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.schemas.analytics import AnalyticsSummary

__all__ = [
    "ProspectCreate",
    "ProspectUpdate",
    "ProspectResponse",
    "ProspectListResponse",
    "ResearchSummaryResponse",
    "EmailGenerateRequest",
    "EmailDraftResponse",
    "EmailDraftUpdate",
    "EmailSendRequest",
    "SentEmailResponse",
    "FeedbackCreate",
    "FeedbackResponse",
    "AnalyticsSummary",
]
