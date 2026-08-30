from sqlalchemy.orm import Session

from app.services.geo_opportunity_service import GeoOpportunityService
from app.services.site_rag_gap_service import SiteRAGGapService


class MeasurementDerivationService:
    @staticmethod
    def refresh(
        db: Session,
        experiment_id: int,
        benchmark_mode: str,
    ) -> dict | None:
        if benchmark_mode == "web_search":
            return GeoOpportunityService.refresh(db, experiment_id)

        if benchmark_mode == "site_rag":
            return SiteRAGGapService.refresh(db, experiment_id)

        return None
