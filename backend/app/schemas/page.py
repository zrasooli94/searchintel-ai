from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageRead(BaseModel):
    id: int
    website_id: int
    url: str
    canonical_url: str | None
    status_code: int | None
    title: str | None
    meta_description: str | None
    h1: str | None
    robots_meta: str | None
    word_count: int
    internal_link_count: int
    external_link_count: int
    last_crawled_at: datetime | None

    model_config = ConfigDict(from_attributes=True)