from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
)


class ProjectCompetitorCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=255,
    )

    website_url: HttpUrl | None = None


class ProjectCompetitorRead(BaseModel):
    brand_id: int
    name: str

    role: str

    website_id: int | None
    domain: str | None
    base_url: str | None

    brand_created: bool
    website_created: bool
    canonical_entity_created: bool
