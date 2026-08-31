from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientReportCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    period_label: str | None = Field(default=None, max_length=120)


class ClientReportPublish(BaseModel):
    expires_at: datetime | None = None


class ClientReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    title: str
    period_label: str | None
    status: str
    snapshot_version: str
    snapshot: dict
    content_hash: str
    share_token_hint: str | None
    expires_at: datetime | None
    published_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ClientReportPublishResult(ClientReportRead):
    share_token: str
