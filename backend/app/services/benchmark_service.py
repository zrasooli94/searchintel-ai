from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.retrieval_versions import (
    SITE_RAG_RETRIEVAL_VERSION,
)
from app.db.session import SessionLocal
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
from app.services.ai_model_service import AIModelService
from app.services.ai_run_service import AIRunService
from app.services.site_rag_retrieval_service import (
    SiteRAGRetrievalService,
)
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
        model_id: int | None,
        experiment_id: int | None = None,
        benchmark_mode: str = "memory",
        source_benchmark_job_id: int | None = None,
        prompt_source_benchmark_job_id: int | None = None,
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

        if benchmark_mode not in {
            "memory",
            "web_search",
            "site_rag",
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

        if (
            source_benchmark_job_id is not None
            and prompt_source_benchmark_job_id is not None
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Use either source_benchmark_job_id "
                    "or prompt_source_benchmark_job_id, "
                    "not both."
                ),
            )

        source_job = None
        prompt_source_job = None
        source_items = None

        if source_benchmark_job_id is not None:
            source_job = BenchmarkRepository.get_job(
                db,
                source_benchmark_job_id,
            )

            if source_job is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Source benchmark job "
                        "not found."
                    ),
                )

            if source_job.project_id != project_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Source benchmark job does "
                        "not belong to this project."
                    ),
                )

            if source_job.status != "completed":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Source benchmark job must "
                        "be completed."
                    ),
                )

            if (
                source_job.benchmark_mode
                != benchmark_mode
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Optimization benchmark mode "
                        "must match the source "
                        "benchmark mode."
                    ),
                )

            if (
                model_id is not None
                and model_id
                != source_job.model_id
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Optimization model must "
                        "match the source benchmark "
                        "model."
                    ),
                )

            model_id = source_job.model_id

            source_items = (
                BenchmarkRepository.list_items(
                    db,
                    source_job.id,
                )
            )

            if not source_items:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Source benchmark has no "
                        "prompt snapshots."
                    ),
                )

            if any(
                item.prompt_text_snapshot is None
                for item in source_items
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Source benchmark contains "
                        "missing prompt snapshots."
                    ),
                )

            prompt_snapshots = [
                {
                    "prompt_id":
                        item.prompt_id,
                    "prompt_text_snapshot":
                        item.prompt_text_snapshot,
                }
                for item in source_items
            ]

        elif prompt_source_benchmark_job_id is not None:
            prompt_source_job = (
                BenchmarkRepository.get_job(
                    db,
                    prompt_source_benchmark_job_id,
                )
            )

            if prompt_source_job is None:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Prompt source benchmark job "
                        "not found."
                    ),
                )

            if prompt_source_job.project_id != project_id:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Prompt source benchmark job "
                        "does not belong to this project."
                    ),
                )

            if prompt_source_job.status != "completed":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Prompt source benchmark job "
                        "must be completed."
                    ),
                )

            source_items = (
                BenchmarkRepository.list_items(
                    db,
                    prompt_source_job.id,
                )
            )

            if not source_items:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Prompt source benchmark has no "
                        "prompt snapshots."
                    ),
                )

            if any(
                item.prompt_text_snapshot is None
                for item in source_items
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Prompt source benchmark contains "
                        "missing prompt snapshots."
                    ),
                )

            prompt_snapshots = [
                {
                    "prompt_id":
                        item.prompt_id,
                    "prompt_text_snapshot":
                        item.prompt_text_snapshot,
                }
                for item in source_items
            ]

        else:
            prompts = (
                PromptRepository
                .list_active_by_project(
                    db,
                    project_id,
                )
            )

            if not prompts:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Project has no active "
                        "prompts."
                    ),
                )

            prompt_snapshots = [
                {
                    "prompt_id":
                        prompt.id,
                    "prompt_text_snapshot":
                        prompt.text,
                }
                for prompt in prompts
            ]

        model = (
            AIModelService.resolve_execution_model(
                db,
                model_id,
            )
        )

        model_id = model.id

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

            "site_rag_enabled":
                benchmark_mode
                == "site_rag",

            "site_rag_retrieval_version":
                (
                    SITE_RAG_RETRIEVAL_VERSION
                    if benchmark_mode
                    == "site_rag"
                    else None
                ),

            "site_rag_top_k":
                (
                    SiteRAGRetrievalService
                    .DEFAULT_TOP_K
                    if benchmark_mode
                    == "site_rag"
                    else None
                ),

            "prompt_count":
                len(prompt_snapshots),

            "prompt_source": (
                "benchmark_snapshot"
                if source_job is not None
                else (
                    "benchmark_snapshot_cross_mode"
                    if prompt_source_job is not None
                    else "active_prompts"
                )
            ),

            "source_benchmark_job_id": (
                source_job.id
                if source_job is not None
                else None
            ),

            "source_experiment_id": (
                source_job.experiment_id
                if source_job is not None
                else None
            ),

            "prompt_source_benchmark_job_id": (
                prompt_source_job.id
                if prompt_source_job is not None
                else None
            ),

            "prompt_source_experiment_id": (
                prompt_source_job.experiment_id
                if prompt_source_job is not None
                else None
            ),
        }

        job = BenchmarkRepository.create_job(
            db=db,
            project_id=project_id,
            model_id=model_id,
            total_prompts=len(
                prompt_snapshots
            ),
            experiment_id=experiment_id,
            benchmark_mode=benchmark_mode,
            config_snapshot=config_snapshot,
        )

        BenchmarkRepository.create_items(
            db=db,
            benchmark_job_id=job.id,
            prompt_snapshots=
                prompt_snapshots,
        )

        db.commit()
        db.refresh(job)

        return cls.serialize_job(job)

    @classmethod
    def list_for_project(
        cls,
        db: Session,
        project_id: int,
    ) -> list[dict]:
        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        jobs = (
            BenchmarkRepository
            .list_jobs_by_project(
                db,
                project_id,
            )
        )

        return [
            cls.serialize_job(job)
            for job in jobs
        ]

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
