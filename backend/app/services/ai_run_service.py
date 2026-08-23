from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

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
from app.schemas.ai_run import (
    AIRunCreate,
    AIResponseCreate,
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

        return AIRunRepository.create(
            db=db,
            project_id=project_id,
            prompt_id=data.prompt_id,
            model_id=data.model_id,
        )

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

        try:
            result = provider.execute(
                prompt=prompt.text,
                model_id=model.provider_model_id,
            )

            AIRunRepository.create_response(
                db=db,
                run_id=run.id,
                response_text=result.response_text,
                raw_response=result.raw_response,
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
                "response_text": result.response_text,
                "latency_ms": result.latency_ms,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
            }

        except Exception as exc:
            run.status = "failed"
            run.completed_at = datetime.now(
                timezone.utc
            )
            run.error_message = str(exc)[:2000]

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
