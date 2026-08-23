from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.visibility import (
    VisibilityAnalysisRead,
)
from app.services.visibility_analysis_service import (
    VisibilityAnalysisService,
)


router = APIRouter(
    tags=["GEO Visibility"],
)


@router.post(
    "/ai-runs/{run_id}/analyze-visibility",
    response_model=VisibilityAnalysisRead,
)
def analyze_visibility(
    run_id: int,
    db: Session = Depends(get_db),
):
    return VisibilityAnalysisService.analyze(
        db,
        run_id,
    )
