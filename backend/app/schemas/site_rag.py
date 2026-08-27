from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


class SiteRAGSourceRead(BaseModel):
    id: int
    response_id: int
    page_id: int | None

    rank: int
    chunk_index: int
    relevance_score: float

    url: str
    title: str | None
    excerpt: str

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
