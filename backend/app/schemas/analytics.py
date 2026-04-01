from typing import Optional
from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_prospects: int
    prospects_by_status: dict
    total_drafts: int
    total_sent: int
    reply_rate: float
    avg_rating: Optional[float] = None
    emails_sent_last_7_days: int
    emails_sent_last_30_days: int

    model_config = {"from_attributes": True}
