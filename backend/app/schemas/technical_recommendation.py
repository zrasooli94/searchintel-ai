from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TechnicalRecommendationRead(BaseModel):
    id: int
    audit_id: int
    issue_id: int
    page_id: int
    issue_code: str
    priority: str
    priority_score: int
    title: str
    recommendation: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationSummary(BaseModel):
    audit_id: int
    website_id: int
    recommendation_count: int
    recommendations: list[TechnicalRecommendationRead]
