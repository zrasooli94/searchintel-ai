from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GeoContentDiagnosisRequest(BaseModel):
    model_id: int


class GeoContentDiagnosisRead(BaseModel):
    id: int
    opportunity_id: int
    experiment_id: int
    project_id: int
    target_brand_id: int
    model_id: int

    status: str
    confidence: float

    analysis: dict

    evidence_page_ids: list[int]
    evidence_run_ids: list[int]

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
