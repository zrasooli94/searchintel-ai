from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.action_plan_summary import (
    ActionPlanSummary,
)

from app.schemas.geo_action_plan import (
    GeoActionPlanRead,
    GeoActionPlanRequest,
)
from app.services.action_plan_summary_service import (
    ActionPlanSummaryService,
)

from app.services.geo_action_plan_service import (
    GeoActionPlanService,
)


router = APIRouter(
    tags=["GEO Strategy"],
)


@router.get(
    "/projects/{project_id}/action-plan-summary",
    response_model=ActionPlanSummary,
)
def project_action_plan_summary(
    project_id: int,
    db: Session = Depends(get_db),
):
    return ActionPlanSummaryService.build(
        db=db,
        project_id=project_id,
    )


@router.post(
    "/geo-experiments/{experiment_id}/action-plan",
    response_model=GeoActionPlanRead,
)
def create_action_plan(
    experiment_id: int,
    data: GeoActionPlanRequest,
    db: Session = Depends(get_db),
):
    return GeoActionPlanService.generate(
        db=db,
        experiment_id=experiment_id,
        model_id=data.model_id,
        priorities=data.priorities,
        max_actions=data.max_actions,
    )


@router.get(
    "/geo-experiments/{experiment_id}/action-plan/latest",
    response_model=GeoActionPlanRead,
)
def latest_action_plan(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    return GeoActionPlanService.latest(
        db,
        experiment_id,
    )
