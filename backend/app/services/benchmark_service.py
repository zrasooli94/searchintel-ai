from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.ai_model_repository import (
    AIModelRepository,
)
from app.repositories.ai_run_repository import (
    AIRunRepository,
)
from app.repositories.benchmark_repository import (
    BenchmarkRepository,
)
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.prompt_repository import (
    PromptRepository,
)
from app.services.ai_run_service import AIRunService
from app.services.visibility_analysis_service import (
    VisibilityAnalysisService,
)


class BenchmarkService:

    @staticmethod
    def serialize_job(
        job,
    ) -> dict:
        processed = (
            job.completed_runs
            + job.failed_runs
        )

        progress = 0.0

        if job.total_prompts:
            progress = round(
                processed
                / job.total_prompts
                * 100,
                2,
            )

        return {
            "id": job.id,
            "project_id": job.project_id,
            "model_id": job.model_id,
            "experiment_id":
                job.experiment_id,
            "benchmark_mode":
                job.benchmark_mode,
            "config_snapshot":
                job.config_snapshot or {},
            "status": job.status,
            "total_prompts":
                job.total_prompts,
            "completed_runs":
                job.completed_runs,
            "failed_runs":
                job.failed_runs,
            "progress_percentage":
                progress,
            "started_at":
                job.started_at,
            "completed_at":
                job.completed_at,
            "error_message":
                job.error_message,
            "created_at":
                job.created_at,
        }

    @classmethod
    def create(
        cls,
        db: Session,
        project_id: int,
        model_id: int,
        experiment_id: int | None = None,
        benchmark_mode: str = "memory",
    ) -> dict:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        model = AIModelRepository.get_by_id(
            db,
            model_id,
        )

        if model is None:
            raise HTTPException(
                status_code=404,
                detail="AI model not found.",
            )

        if not model.is_active:
            raise HTTPException(
                status_code=400,
                detail="AI model is inactive.",
            )

        if benchmark_mode not in {
            "memory",
            "web_search",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported benchmark mode: "
                    f"{benchmark_mode}"
                ),
            )

        if experiment_id is not None:
            experiment = (
                GeoExperimentRepository.get(
                    db,
                    experiment_id,
                )
            )

            if experiment is None:
                raise HTTPException(
                    status_code=404,
                    detail="Experiment not found.",
                )

            if experiment.project_id != project_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Experiment does not belong "
                        "to this project."
                    ),
                )

        prompts = (
            PromptRepository.list_active_by_project(
                db,
                project_id,
            )
        )

        if not prompts:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Project has no active prompts."
                ),
            )

        config_snapshot = {
            "benchmark_mode":
                benchmark_mode,

            "provider_model_id":
                model.provider_model_id,

            "web_search_enabled":
                benchmark_mode
                == "web_search",

            "tool_choice": (
                "required"
                if benchmark_mode
                == "web_search"
                else "none"
            ),

            "capture_web_sources":
                benchmark_mode
                == "web_search",

            "prompt_count":
                len(prompts),
        }

        job = BenchmarkRepository.create_job(
            db=db,
            project_id=project_id,
            model_id=model_id,
            total_prompts=len(prompts),
            experiment_id=experiment_id,
            benchmark_mode=benchmark_mode,
            config_snapshot=config_snapshot,
        )

        BenchmarkRepository.create_items(
            db=db,
            benchmark_job_id=job.id,
            prompt_snapshots=[
                {
                    "prompt_id":
                        prompt.id,
                    "prompt_text_snapshot":
                        prompt.text,
                }
                for prompt in prompts
            ],
        )

        db.commit()
        db.refresh(job)

        return cls.serialize_job(job)

    @classmethod
    def status(
        cls,
        db: Session,
        job_id: int,
    ) -> dict:
        job = BenchmarkRepository.get_job(
            db,
            job_id,
        )

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Benchmark job not found.",
            )

        return cls.serialize_job(job)

    @staticmethod
    def items(
        db: Session,
        job_id: int,
    ):
        job = BenchmarkRepository.get_job(
            db,
            job_id,
        )

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Benchmark job not found.",
            )

        return BenchmarkRepository.list_items(
            db,
            job_id,
        )

    @staticmethod
    def run_job(
        job_id: int,
    ) -> None:
        db = SessionLocal()

        try:
            job = BenchmarkRepository.get_job(
                db,
                job_id,
            )

            if job is None:
                return

            job.status = "running"
            job.started_at = datetime.now(
                timezone.utc
            )
            job.error_message = None

            if job.experiment_id is not None:
                experiment = (
                    GeoExperimentRepository.get(
                        db,
                        job.experiment_id,
                    )
                )

                if experiment is not None:
                    experiment.status = "running"
                    experiment.started_at = (
                        job.started_at
                    )
                    experiment.completed_at = None

            db.commit()

            items = BenchmarkRepository.list_items(
                db,
                job_id,
            )

            for original_item in items:

                item = BenchmarkRepository.get_item(
                    db,
                    original_item.id,
                )

                job = BenchmarkRepository.get_job(
                    db,
                    job_id,
                )

                if item is None or job is None:
                    continue

                item.status = "running"
                item.started_at = datetime.now(
                    timezone.utc
                )

                db.commit()

                try:
                    run = AIRunRepository.create(
                        db=db,
                        project_id=job.project_id,
                        prompt_id=item.prompt_id,
                        model_id=job.model_id,
                        run_type="benchmark",
                        include_in_metrics=True,
                        experiment_id=job.experiment_id,
                        benchmark_mode=
                            job.benchmark_mode,
                        config_snapshot=
                            dict(
                                job.config_snapshot
                                or {}
                            ),
                    )

                    item = BenchmarkRepository.get_item(
                        db,
                        item.id,
                    )

                    if item is None:
                        raise RuntimeError(
                            "Benchmark item disappeared."
                        )

                    item.ai_run_id = run.id
                    db.commit()

                    AIRunService.execute(
                        db,
                        run.id,
                        prompt_override=(
                            item.prompt_text_snapshot
                        ),
                    )

                    VisibilityAnalysisService.analyze(
                        db,
                        run.id,
                    )

                    item = BenchmarkRepository.get_item(
                        db,
                        item.id,
                    )

                    job = BenchmarkRepository.get_job(
                        db,
                        job_id,
                    )

                    if item is None or job is None:
                        raise RuntimeError(
                            "Benchmark state missing."
                        )

                    item.status = "completed"
                    item.completed_at = datetime.now(
                        timezone.utc
                    )

                    job.completed_runs += 1

                    db.commit()

                except Exception as exc:
                    db.rollback()

                    item = BenchmarkRepository.get_item(
                        db,
                        original_item.id,
                    )

                    job = BenchmarkRepository.get_job(
                        db,
                        job_id,
                    )

                    if item is not None:
                        item.status = "failed"
                        item.completed_at = datetime.now(
                            timezone.utc
                        )
                        item.error_message = str(
                            exc
                        )[:2000]

                    if job is not None:
                        job.failed_runs += 1

                    db.commit()

            job = BenchmarkRepository.get_job(
                db,
                job_id,
            )

            if job is None:
                return

            job.completed_at = datetime.now(
                timezone.utc
            )

            if job.failed_runs:
                job.status = (
                    "completed_with_errors"
                )
            else:
                job.status = "completed"

            if job.experiment_id is not None:
                experiment = (
                    GeoExperimentRepository.get(
                        db,
                        job.experiment_id,
                    )
                )

                if experiment is not None:
                    experiment.status = (
                        job.status
                    )

                    experiment.completed_at = (
                        job.completed_at
                    )

                    if (
                        experiment.started_at
                        is None
                    ):
                        experiment.started_at = (
                            job.started_at
                        )

            db.commit()

        except Exception as exc:
            db.rollback()

            job = BenchmarkRepository.get_job(
                db,
                job_id,
            )

            if job is not None:
                job.status = "failed"
                job.completed_at = datetime.now(
                    timezone.utc
                )
                job.error_message = str(
                    exc
                )[:2000]

                if (
                    job.experiment_id
                    is not None
                ):
                    experiment = (
                        GeoExperimentRepository.get(
                            db,
                            job.experiment_id,
                        )
                    )

                    if experiment is not None:
                        experiment.status = "failed"
                        experiment.completed_at = (
                            job.completed_at
                        )

                        if (
                            experiment.started_at
                            is None
                        ):
                            experiment.started_at = (
                                job.started_at
                            )

                db.commit()

        finally:
            db.close()
