from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.api.operator import require_operator
from app.schemas.candidate_validation import (
    CandidateValidationRequest,
    CandidateValidationResult,
)
from app.schemas.competitor import (
    CompetitorCandidate,
    ResolveCompetitorsRequest,
    ResolveCompetitorsResult,
)
from app.services.candidate_validation_service import (
    CandidateValidationService,
)
from app.services.competitor_resolution_service import (
    CompetitorResolutionService,
)
from app.schemas.competitor_discovery import (
    CompetitorDiscoveryDecisionResult,
    CompetitorDiscoveryGenerateRequest,
    CompetitorDiscoveryResult,
    CompetitorDiscoverySuggestionRead,
)
from app.services.competitor_discovery_service import CompetitorDiscoveryService


router = APIRouter(
    tags=["GEO Competitors"],
)


@router.get(
    "/projects/{project_id}/competitor-discovery-suggestions",
    response_model=list[CompetitorDiscoverySuggestionRead],
)
def list_competitor_discovery_suggestions(
    project_id: int,
    db: Session = Depends(get_db),
):
    return CompetitorDiscoveryService.list(db, project_id)


@router.post(
    "/projects/{project_id}/competitor-discovery-suggestions/generate",
    response_model=CompetitorDiscoveryResult,
)
def generate_competitor_discovery_suggestions(
    project_id: int,
    data: CompetitorDiscoveryGenerateRequest,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return CompetitorDiscoveryService.generate(
        db, project_id, data.max_candidates, data.model_id
    )


@router.post(
    "/projects/{project_id}/competitor-discovery-suggestions/{suggestion_id}/approve",
    response_model=CompetitorDiscoveryDecisionResult,
)
def approve_competitor_discovery_suggestion(
    project_id: int,
    suggestion_id: int,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return CompetitorDiscoveryService.approve(db, project_id, suggestion_id)


@router.post(
    "/projects/{project_id}/competitor-discovery-suggestions/{suggestion_id}/ignore",
    response_model=CompetitorDiscoveryDecisionResult,
)
def ignore_competitor_discovery_suggestion(
    project_id: int,
    suggestion_id: int,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return CompetitorDiscoveryService.ignore(db, project_id, suggestion_id)


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
    "/projects/{project_id}/competitor-candidates/validate",
    response_model=CandidateValidationResult,
)
def validate_competitor_candidates(
    project_id: int,
    data: CandidateValidationRequest,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return CandidateValidationService.validate(
        db=db,
        project_id=project_id,
        model_id=data.model_id,
        limit=data.limit,
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
