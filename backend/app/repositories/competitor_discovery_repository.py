from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competitor_discovery_suggestion import (
    CompetitorDiscoverySuggestion,
)


class CompetitorDiscoveryRepository:

    @staticmethod
    def list_by_project(db: Session, project_id: int):
        statement = (
            select(CompetitorDiscoverySuggestion)
            .where(CompetitorDiscoverySuggestion.project_id == project_id)
            .order_by(CompetitorDiscoverySuggestion.id)
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def get(db: Session, project_id: int, suggestion_id: int):
        statement = select(CompetitorDiscoverySuggestion).where(
            CompetitorDiscoverySuggestion.id == suggestion_id,
            CompetitorDiscoverySuggestion.project_id == project_id,
        )
        return db.scalar(statement)

    @staticmethod
    def get_by_domain(db: Session, project_id: int, domain: str):
        statement = select(CompetitorDiscoverySuggestion).where(
            CompetitorDiscoverySuggestion.project_id == project_id,
            CompetitorDiscoverySuggestion.normalized_domain == domain,
        )
        return db.scalar(statement)

    @staticmethod
    def pending_count(db: Session, project_id: int) -> int:
        return sum(
            item.status == "pending"
            for item in CompetitorDiscoveryRepository.list_by_project(db, project_id)
        )
