from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.entity import (
    EntityCandidateRead,
    EntityClassificationRequest,
    EntityClassificationResult,
)
from app.services.entity_classification_service import (
    EntityClassificationService,
)


router = APIRouter(
    tags=["Search Entities"],
)


@router.post(
    "/projects/{project_id}/entities/classify-candidates",
    response_model=EntityClassificationResult,
)
def classify_entity_candidates(
    project_id: int,
    data: EntityClassificationRequest,
    db: Session = Depends(get_db),
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
