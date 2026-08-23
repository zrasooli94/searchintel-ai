from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.metric_snapshot import MetricSnapshot


class MetricSnapshotRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        brand_id: int | None,
        metric_name: str,
        metric_value: float,
        sample_size: int,
        details: dict | None = None,
    ) -> MetricSnapshot:
        snapshot = MetricSnapshot(
            project_id=project_id,
            brand_id=brand_id,
            metric_name=metric_name,
            metric_value=Decimal(
                str(round(metric_value, 4))
            ),
            sample_size=sample_size,
            details=details,
        )

        db.add(snapshot)
        db.flush()

        return snapshot
