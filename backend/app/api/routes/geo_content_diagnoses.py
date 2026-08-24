from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.geo_content_diagnosis import (
    GeoContentDiagnosisRead,
    GeoContentDiagnosisRequest,
    GeoDiagnosisBatchRequest,
    GeoDiagnosisBatchResult,
)
from app.services.geo_diagnosis_batch_service import (
    GeoDiagnosisBatchService,
)
from app.services.geo_content_diagnosis_service import (
    GeoContentDiagnosisService,
)


router = APIRouter(
    tags=["GEO Content Intelligence"],
)


@router.post(
    "/geo-opportunities/{opportunity_id}/diagnose",
    response_model=GeoContentDiagnosisRead,
)
def diagnose_opportunity(
    opportunity_id: int,
    data: GeoContentDiagnosisRequest,
    db: Session = Depends(get_db),
):
    return GeoContentDiagnosisService.diagnose(
        db=db,
        opportunity_id=opportunity_id,
        model_id=data.model_id,
    )


@router.get(
    "/geo-opportunities/{opportunity_id}/diagnosis/latest",
    response_model=GeoContentDiagnosisRead,
)
def latest_diagnosis(
    opportunity_id: int,
    db: Session = Depends(get_db),
):
    return GeoContentDiagnosisService.latest(
        db,
        opportunity_id,
    )



@router.post(
    "/geo-experiments/{experiment_id}/diagnoses/refresh",
    response_model=GeoDiagnosisBatchResult,
)
def refresh_experiment_diagnoses(
    experiment_id: int,
    data: GeoDiagnosisBatchRequest,
    db: Session = Depends(get_db),
):
    return GeoDiagnosisBatchService.run(
        db=db,
        experiment_id=experiment_id,
        model_id=data.model_id,
        priorities=data.priorities,
        limit=data.limit,
        force=data.force,
    )
