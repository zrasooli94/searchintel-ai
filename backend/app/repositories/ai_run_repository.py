from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_response import AIResponse
from app.models.ai_run import AIRun


class AIRunRepository:

    @staticmethod
    def create(
        db: Session,
        project_id: int,
        prompt_id: int,
        model_id: int,
        run_type: str = "ad_hoc",
        include_in_metrics: bool = True,
    ) -> AIRun:

        run = AIRun(
            project_id=project_id,
            prompt_id=prompt_id,
            model_id=model_id,
            run_type=run_type,
            include_in_metrics=include_in_metrics,
            status="pending",
        )

        db.add(run)
        db.flush()

        return run

    @staticmethod
    def get_by_id(
        db: Session,
        run_id: int,
    ) -> AIRun | None:
        return db.get(
            AIRun,
            run_id,
        )

    @staticmethod
    def create_response(
        db: Session,
        run_id: int,
        response_text: str,
        raw_response: dict | None,
    ) -> AIResponse:

        response = AIResponse(
            run_id=run_id,
            response_text=response_text,
            raw_response=raw_response,
        )

        db.add(response)
        db.flush()

        return response

    @staticmethod
    def list_by_project(
        db: Session,
        project_id: int,
    ) -> list[AIRun]:

        statement = (
            select(AIRun)
            .where(
                AIRun.project_id
                == project_id
            )
            .order_by(
                AIRun.id.desc()
            )
        )

        return list(
            db.scalars(statement).all()
        )
