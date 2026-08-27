from pydantic import BaseModel, Field, HttpUrl


class ProjectOnboardRequest(BaseModel):
    project_name: str = Field(
        min_length=3,
        max_length=255,
    )

    project_description: str | None = None

    target_brand: str = Field(
        min_length=1,
        max_length=255,
    )

    website_url: HttpUrl


class ProjectOnboardResponse(BaseModel):
    project_id: int
    project_name: str

    target_brand_id: int
    target_brand: str

    website_id: int
    domain: str
    base_url: str

    brand_created: bool
    website_created: bool
    canonical_entity_created: bool

    setup_status: str
