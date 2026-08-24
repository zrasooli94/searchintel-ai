from pydantic import BaseModel


class ProjectWorkspaceRead(BaseModel):
    id: int
    name: str
    description: str | None

    target_brand_id: int | None
    target_brand: str | None

    website_id: int | None
    domain: str | None
    base_url: str | None

    competitor_count: int

    experiment_count: int
    completed_experiment_count: int

    latest_completed_experiment_id: int | None
    latest_completed_experiment_name: str | None
