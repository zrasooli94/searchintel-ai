from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.ai_run import AIRun
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
