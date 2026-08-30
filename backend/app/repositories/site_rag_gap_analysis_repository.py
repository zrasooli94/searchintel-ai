from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.site_rag_gap_analysis import (
    SiteRAGGapAnalysis,
)


class SiteRAGGapAnalysisRepository:

    @staticmethod
    def completed_by_experiment(
        db: Session,
        experiment_id: int,
    ) -> SiteRAGGapAnalysis | None:
        return db.scalar(
            select(SiteRAGGapAnalysis).where(
                SiteRAGGapAnalysis.experiment_id == experiment_id,
                SiteRAGGapAnalysis.status == "completed",
            )
        )

    @staticmethod
    def record_completed(
        db: Session,
        experiment_id: int,
        project_id: int,
        target_brand_id: int,
        gap_version: str,
        total_prompts: int,
        gap_count: int,
        refreshed_at: datetime,
    ) -> SiteRAGGapAnalysis:
        record = db.scalar(
            select(SiteRAGGapAnalysis).where(
                SiteRAGGapAnalysis.experiment_id
                == experiment_id
            )
        )

        if record is None:
            record = SiteRAGGapAnalysis(
                experiment_id=experiment_id,
                project_id=project_id,
                target_brand_id=target_brand_id,
            )
            db.add(record)

        record.gap_version = gap_version
        record.status = "completed"
        record.total_prompts = total_prompts
        record.gap_count = gap_count
        record.refreshed_at = refreshed_at

        db.flush()

        return record

    @staticmethod
    def latest_completed_by_project(
        db: Session,
        project_id: int,
    ) -> SiteRAGGapAnalysis | None:
        statement = (
            select(SiteRAGGapAnalysis)
            .where(
                SiteRAGGapAnalysis.project_id
                == project_id,
                SiteRAGGapAnalysis.status
                == "completed",
            )
            .order_by(
                SiteRAGGapAnalysis.refreshed_at.desc(),
                SiteRAGGapAnalysis.id.desc(),
            )
            .limit(1)
        )

        return db.scalar(statement)
