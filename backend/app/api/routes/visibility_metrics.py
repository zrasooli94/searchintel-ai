from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.visibility_metrics import (
    AIVisibilityMetrics,
)
from app.services.visibility_metrics_service import (
    VisibilityMetricsService,
)


router = APIRouter(
    tags=["GEO Metrics"],
)


@router.post(
    "/projects/{project_id}/visibility-metrics",
    response_model=AIVisibilityMetrics,
)
def calculate_visibility_metrics(
    project_id: int,
    db: Session = Depends(get_db),
):
    return VisibilityMetricsService.calculate(
        db,
        project_id,
    )
