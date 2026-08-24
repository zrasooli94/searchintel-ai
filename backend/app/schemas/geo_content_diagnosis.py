from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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



class GeoDiagnosisBatchRequest(BaseModel):
    model_id: int

    priorities: list[str] = [
        "high",
        "medium",
    ]

    limit: int = Field(
        default=20,
        ge=1,
        le=50,
    )

    force: bool = False


class GeoDiagnosisBatchResult(BaseModel):
    experiment_id: int
    selected_count: int

    diagnosed_count: int
    reused_count: int
    failed_count: int

    diagnosis_ids: list[int]
    errors: list[dict]
