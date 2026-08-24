from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.geo_opportunity import (
    GeoOpportunitySummary,
)
from app.services.geo_opportunity_service import (
    GeoOpportunityService,
)


router = APIRouter(
    tags=["GEO Opportunities"],
)


@router.post(
    "/geo-experiments/{experiment_id}/opportunities/refresh",
    response_model=GeoOpportunitySummary,
)
def refresh_opportunities(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    return GeoOpportunityService.refresh(
        db,
        experiment_id,
    )


@router.get(
    "/geo-experiments/{experiment_id}/opportunities",
    response_model=GeoOpportunitySummary,
)
def get_opportunities(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    return GeoOpportunityService.summary(
        db,
        experiment_id,
    )
