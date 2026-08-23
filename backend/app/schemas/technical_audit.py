from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TechnicalIssueRead(BaseModel):
    id: int
    page_id: int
    code: str
    severity: str
    message: str

    model_config = ConfigDict(from_attributes=True)


class TechnicalAuditRead(BaseModel):
    id: int
    website_id: int
    score: int
    pages_checked: int
    issue_count: int
    created_at: datetime
    issues: list[TechnicalIssueRead]

    model_config = ConfigDict(from_attributes=True)
