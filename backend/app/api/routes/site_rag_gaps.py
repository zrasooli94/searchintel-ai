from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.site_rag_gap import (
    SiteRAGGapSummary,
)
from app.services.site_rag_gap_service import (
    SiteRAGGapService,
)


router = APIRouter(
    tags=["Site RAG Gaps"],
)


@router.post(
    "/geo-experiments/{experiment_id}/site-rag-gaps/refresh",
    response_model=SiteRAGGapSummary,
)
def refresh_site_rag_gaps(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    return SiteRAGGapService.refresh(
        db,
        experiment_id,
    )


@router.get(
    "/geo-experiments/{experiment_id}/site-rag-gaps",
    response_model=SiteRAGGapSummary,
)
def get_site_rag_gaps(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    return SiteRAGGapService.summary(
        db,
        experiment_id,
    )
