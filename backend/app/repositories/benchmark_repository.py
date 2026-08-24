from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark_job import BenchmarkJob
from app.models.benchmark_job_item import BenchmarkJobItem


class BenchmarkRepository:

    @staticmethod
    def create_job(
        db: Session,
        project_id: int,
        model_id: int,
        total_prompts: int,
    ) -> BenchmarkJob:
        job = BenchmarkJob(
            project_id=project_id,
            model_id=model_id,
            status="pending",
            total_prompts=total_prompts,
            completed_runs=0,
            failed_runs=0,
        )

        db.add(job)
        db.flush()

        return job

    @staticmethod
    def create_items(
        db: Session,
        benchmark_job_id: int,
        prompt_ids: list[int],
    ) -> None:
        items = [
            BenchmarkJobItem(
                benchmark_job_id=benchmark_job_id,
                prompt_id=prompt_id,
                status="pending",
            )
            for prompt_id in prompt_ids
        ]

        db.add_all(items)
        db.flush()

    @staticmethod
    def get_job(
        db: Session,
        job_id: int,
    ) -> BenchmarkJob | None:
        return db.get(
            BenchmarkJob,
            job_id,
        )

    @staticmethod
    def get_item(
        db: Session,
        item_id: int,
    ) -> BenchmarkJobItem | None:
        return db.get(
            BenchmarkJobItem,
            item_id,
        )

    @staticmethod
    def list_items(
        db: Session,
        job_id: int,
    ) -> list[BenchmarkJobItem]:
        statement = (
            select(BenchmarkJobItem)
            .where(
                BenchmarkJobItem.benchmark_job_id
                == job_id
            )
            .order_by(
                BenchmarkJobItem.id
            )
        )

        return list(
            db.scalars(statement).all()
        )
