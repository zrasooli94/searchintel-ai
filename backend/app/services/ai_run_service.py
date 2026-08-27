from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.retrieval_versions import (
    SITE_RAG_RETRIEVAL_VERSION,
)
from app.integrations.ai.provider_factory import (
    ProviderFactory,
)
from app.models.ai_run import AIRun
from app.repositories.ai_engine_repository import (
    AIEngineRepository,
)
from app.repositories.ai_model_repository import (
    AIModelRepository,
)
from app.repositories.ai_run_repository import (
    AIRunRepository,
)
from app.repositories.project_repository import (
    ProjectRepository,
)
from app.repositories.prompt_repository import (
    PromptRepository,
)
from app.repositories.site_rag_source_repository import (
    SiteRAGSourceRepository,
)
from app.schemas.ai_run import (
    AIRunCreate,
    AIResponseCreate,
)
from app.services.site_rag_retrieval_service import (
    SiteRAGRetrievalService,
)


class AIRunService:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        data: AIRunCreate,
    ) -> AIRun:

        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        prompt = PromptRepository.get_by_id(
            db,
            data.prompt_id,
        )

        if prompt is None:
            raise HTTPException(
                status_code=404,
                detail="Prompt not found.",
            )

        if prompt.project_id != project_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Prompt does not belong "
                    "to this project."
                ),
            )

        model = AIModelRepository.get_by_id(
            db,
            data.model_id,
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

        config_snapshot = {
            "benchmark_mode":
                data.benchmark_mode,
            "provider_model_id":
                model.provider_model_id,
            "web_search_enabled":
                data.benchmark_mode
                == "web_search",

            "site_rag_enabled":
                data.benchmark_mode
                == "site_rag",

            "site_rag_retrieval_version":
                (
                    SITE_RAG_RETRIEVAL_VERSION
                    if data.benchmark_mode
                    == "site_rag"
                    else None
                ),

            "site_rag_top_k":
                (
                    SiteRAGRetrievalService
                    .DEFAULT_TOP_K
                    if data.benchmark_mode
                    == "site_rag"
                    else None
                ),
        }

        run = AIRunRepository.create(
            db=db,
            project_id=project_id,
            prompt_id=data.prompt_id,
            model_id=data.model_id,
            benchmark_mode=data.benchmark_mode,
            include_in_metrics=
                data.include_in_metrics,
            config_snapshot=config_snapshot,
        )

        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def complete(
        db: Session,
        run_id: int,
        data: AIResponseCreate,
    ) -> AIRun:

        run = AIRunRepository.get_by_id(
            db,
            run_id,
        )

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="AI run not found.",
            )

        if run.response is not None:
            raise HTTPException(
                status_code=409,
                detail="AI run already has a response.",
            )

        AIRunRepository.create_response(
            db=db,
            run_id=run.id,
            response_text=data.response_text,
            raw_response=data.raw_response,
        )

        now = datetime.now(
            timezone.utc
        )

        if run.started_at is None:
            run.started_at = now

        run.completed_at = now
        run.status = "completed"
        run.latency_ms = data.latency_ms
        run.input_tokens = data.input_tokens
        run.output_tokens = data.output_tokens
        run.estimated_cost = data.estimated_cost

        db.commit()
        db.refresh(run)

        return run

    @staticmethod
    def execute(
        db: Session,
        run_id: int,
        prompt_override: str | None = None,
    ) -> dict:

        run = AIRunRepository.get_by_id(
            db,
            run_id,
        )

        if run is None:
            raise HTTPException(
                status_code=404,
                detail="AI run not found.",
            )

        if run.response is not None:
            raise HTTPException(
                status_code=409,
                detail=(
                    "AI run has already been executed."
                ),
            )

        prompt = PromptRepository.get_by_id(
            db,
            run.prompt_id,
        )

        if prompt is None:
            raise HTTPException(
                status_code=404,
                detail="Prompt not found.",
            )

        model = AIModelRepository.get_by_id(
            db,
            run.model_id,
        )

        if model is None:
            raise HTTPException(
                status_code=404,
                detail="AI model not found.",
            )

        if (
            not model.provider_model_id
            or model.provider_model_id
            == "configure-later"
        ):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Configure a real provider model ID "
                    "before executing this run."
                ),
            )

        engine = AIEngineRepository.get_by_id(
            db,
            model.engine_id,
        )

        if engine is None:
            raise HTTPException(
                status_code=404,
                detail="AI engine not found.",
            )

        try:
            provider = ProviderFactory.create(
                engine.slug
            )
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        run.status = "running"
        run.started_at = datetime.now(
            timezone.utc
        )
        run.error_message = None

        db.commit()

        run_id = run.id

        try:
            prompt_text = (
                prompt_override
                if prompt_override is not None
                else prompt.text
            )

            provider_mode = (
                run.benchmark_mode
            )

            site_rag_result = None

            if (
                run.benchmark_mode
                == "site_rag"
            ):
                site_rag_result = (
                    SiteRAGRetrievalService
                    .retrieve(
                        db=db,
                        project_id=
                            run.project_id,
                        query=prompt_text,
                    )
                )

                prompt_text = (
                    SiteRAGRetrievalService
                    .build_grounded_prompt(
                        query=(
                            prompt_override
                            if prompt_override
                            is not None
                            else prompt.text
                        ),
                        sources=
                            site_rag_result[
                                "sources"
                            ],
                    )
                )

                # Site RAG remains an explicit
                # provider execution mode. Only
                # web_search activates the web tool.

            result = provider.execute(
                prompt=prompt_text,
                model_id=model.provider_model_id,
                mode=provider_mode,
            )

            response = (
                AIRunRepository
                .create_response(
                    db=db,
                    run_id=run.id,
                    response_text=
                        result.response_text,
                    raw_response=
                        result.raw_response,
                )
            )

            if site_rag_result is not None:
                (
                    SiteRAGSourceRepository
                    .clear_by_response(
                        db=db,
                        response_id=
                            response.id,
                    )
                )

                for source in (
                    site_rag_result[
                        "sources"
                    ]
                ):
                    (
                        SiteRAGSourceRepository
                        .create(
                            db=db,
                            response_id=
                                response.id,
                            page_id=
                                source[
                                    "page_id"
                                ],
                            rank=
                                source[
                                    "rank"
                                ],
                            chunk_index=
                                source[
                                    "chunk_index"
                                ],
                            relevance_score=
                                source[
                                    "relevance_score"
                                ],
                            url=
                                source[
                                    "url"
                                ],
                            title=
                                source[
                                    "title"
                                ],
                            excerpt=
                                source[
                                    "excerpt"
                                ],
                        )
                    )

                snapshot = dict(
                    run.config_snapshot
                    or {}
                )

                snapshot.update(
                    {
                        "site_rag_website_id":
                            site_rag_result[
                                "website_id"
                            ],

                        "site_rag_domain":
                            site_rag_result[
                                "domain"
                            ],

                        "site_rag_retrieval_version":
                            site_rag_result[
                                "retrieval_version"
                            ],

                        "site_rag_source_count":
                            len(
                                site_rag_result[
                                    "sources"
                                ]
                            ),
                    }
                )

                run.config_snapshot = (
                    snapshot
                )

            run.status = "completed"
            run.completed_at = datetime.now(
                timezone.utc
            )
            run.latency_ms = result.latency_ms
            run.input_tokens = (
                result.input_tokens
            )
            run.output_tokens = (
                result.output_tokens
            )

            db.commit()
            db.refresh(run)

            return {
                "run_id": run.id,
                "status": run.status,
                "model": model.provider_model_id,
                "benchmark_mode":
                    run.benchmark_mode,
                "response_text": result.response_text,
                "latency_ms": result.latency_ms,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            }

        except Exception as exc:
            # Remove any partially flushed response
            # or Site RAG evidence before recording
            # the failed execution.
            db.rollback()

            failed_run = (
                AIRunRepository.get_by_id(
                    db,
                    run_id,
                )
            )

            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.completed_at = datetime.now(
                    timezone.utc
                )
                failed_run.error_message = (
                    str(exc)[:2000]
                )

                db.commit()

            raise HTTPException(
                status_code=502,
                detail=(
                    "AI provider request failed: "
                    f"{exc}"
                ),
            ) from exc

    @staticmethod
    def list_by_project(
        db: Session,
        project_id: int,
    ) -> list[AIRun]:

        project = ProjectRepository.get_by_id(
            db,
            project_id,
        )

        if project is None:
            raise HTTPException(
                status_code=404,
                detail="Project not found.",
            )

        return AIRunRepository.list_by_project(
            db,
            project_id,
        )
