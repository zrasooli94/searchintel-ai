from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.entity_summary import (
    EntitiesSummary,
)

from app.schemas.entity import (
    EntityCandidateRead,
    EntityClassificationRequest,
    EntityClassificationResult,
    ResolveEntitiesRequest,
    ResolveEntitiesResult,
)
from app.services.entity_summary_service import (
    EntitySummaryService,
)

from app.services.entity_classification_service import (
    EntityClassificationService,
)
from app.services.entity_resolution_service import (
    EntityResolutionService,
)
from app.api.operator import require_operator


router = APIRouter(
    tags=["Search Entities"],
)


@router.get(
    "/projects/{project_id}/entities-summary",
    response_model=EntitiesSummary,
)
def entities_summary(
    project_id: int,
    db: Session = Depends(get_db),
):
    return EntitySummaryService.build(
        db=db,
        project_id=project_id,
    )


@router.post(
    "/projects/{project_id}/entities/classify-candidates",
    response_model=EntityClassificationResult,
)
def classify_entity_candidates(
    project_id: int,
    data: EntityClassificationRequest,
    db: Session = Depends(get_db),
    _operator: None = Depends(require_operator),
):
    return EntityClassificationService.classify(
        db=db,
        project_id=project_id,
        model_id=data.model_id,
        limit=data.limit,
    )


@router.get(
    "/projects/{project_id}/entities/candidates",
    response_model=list[EntityCandidateRead],
)
def list_entity_candidates(
    project_id: int,
    db: Session = Depends(get_db),
):
    return (
        EntityClassificationService
        .list_candidates(
            db,
            project_id,
        )
    )



@router.post(
    "/projects/{project_id}/entities/resolve",
    response_model=ResolveEntitiesResult,
)
def resolve_entities(
    project_id: int,
    data: ResolveEntitiesRequest,
    db: Session = Depends(get_db),
):
    return EntityResolutionService.resolve(
        db=db,
        project_id=project_id,
        items=data.items,
    )
