from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.competitor import (
    CompetitorCandidate,
    ResolveCompetitorsRequest,
    ResolveCompetitorsResult,
)
from app.services.competitor_resolution_service import (
    CompetitorResolutionService,
)


router = APIRouter(
    tags=["GEO Competitors"],
)


@router.get(
    "/projects/{project_id}/competitor-candidates",
    response_model=list[CompetitorCandidate],
)
def list_competitor_candidates(
    project_id: int,
    db: Session = Depends(get_db),
):
    return CompetitorResolutionService.list_candidates(
        db,
        project_id,
    )


@router.post(
    "/projects/{project_id}/competitors/resolve",
    response_model=ResolveCompetitorsResult,
)
def resolve_competitors(
    project_id: int,
    data: ResolveCompetitorsRequest,
    db: Session = Depends(get_db),
):
    return CompetitorResolutionService.resolve(
        db,
        project_id,
        data.names,
    )
