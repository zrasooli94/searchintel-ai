from pydantic import BaseModel


class ProjectCompetitorSummary(BaseModel):
    brand_id: int
    name: str

    website_id: int | None
    domain: str | None
    base_url: str | None
