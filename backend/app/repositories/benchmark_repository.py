from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.benchmark_job import BenchmarkJob
from app.models.benchmark_job_item import BenchmarkJobItem


class BenchmarkRepository:

    @staticmethod
    def find_active_equivalent(
        db: Session,
        project_id: int,
        experiment_id: int | None,
        benchmark_mode: str,
    ) -> BenchmarkJob | None:
        statement = select(BenchmarkJob).where(
            BenchmarkJob.project_id == project_id,
            BenchmarkJob.benchmark_mode == benchmark_mode,
            BenchmarkJob.status.in_([
                "pending",
                "running",
            ]),
        )

        if experiment_id is None:
            statement = statement.where(
                BenchmarkJob.experiment_id.is_(None)
            )
        else:
            statement = statement.where(
                BenchmarkJob.experiment_id == experiment_id
            )

        return db.scalar(
            statement.order_by(
                BenchmarkJob.id.desc()
            ).limit(1)
        )

    @staticmethod
    def create_job(
        db: Session,
        project_id: int,
        model_id: int,
        total_prompts: int,
        experiment_id: int | None = None,
        benchmark_mode: str = "memory",
        config_snapshot: dict | None = None,
    ) -> BenchmarkJob:
        job = BenchmarkJob(
            project_id=project_id,
            model_id=model_id,
            status="pending",
            total_prompts=total_prompts,
            experiment_id=experiment_id,
            benchmark_mode=benchmark_mode,
            config_snapshot=config_snapshot or {},
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
        prompt_snapshots: list[dict],
    ) -> None:
        items = [
            BenchmarkJobItem(
                benchmark_job_id=benchmark_job_id,
                prompt_id=item["prompt_id"],
                prompt_text_snapshot=item[
                    "prompt_text_snapshot"
                ],
                status="pending",
            )
            for item in prompt_snapshots
        ]

        db.add_all(items)
        db.flush()

    @staticmethod
    def list_jobs_by_project(
        db: Session,
        project_id: int,
    ) -> list[BenchmarkJob]:
        statement = (
            select(BenchmarkJob)
            .where(
                BenchmarkJob.project_id
                == project_id
            )
            .order_by(
                BenchmarkJob.id.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

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
