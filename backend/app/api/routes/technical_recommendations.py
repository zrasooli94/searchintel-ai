from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.technical_recommendation import (
    RecommendationSummary,
)
from app.services.technical_recommendation_service import (
    TechnicalRecommendationService,
)


router = APIRouter(
    tags=["SEO Recommendations"],
)


@router.post(
    "/websites/{website_id}/seo-recommendations",
    response_model=RecommendationSummary,
)
def generate_recommendations(
    website_id: int,
    db: Session = Depends(get_db),
):
    return TechnicalRecommendationService.generate(
        db,
        website_id,
    )


@router.get(
    "/websites/{website_id}/seo-recommendations/latest",
    response_model=RecommendationSummary,
)
def get_latest_recommendations(
    website_id: int,
    db: Session = Depends(get_db),
):
    return TechnicalRecommendationService.latest(
        db,
        website_id,
    )
