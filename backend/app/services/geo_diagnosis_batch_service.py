from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.geo_content_diagnosis_repository import (
    GeoContentDiagnosisRepository,
)
from app.repositories.geo_experiment_repository import (
    GeoExperimentRepository,
)
from app.repositories.geo_opportunity_repository import (
    GeoOpportunityRepository,
)
from app.services.geo_content_diagnosis_service import (
    GeoContentDiagnosisService,
)


class GeoDiagnosisBatchService:

    VALID_PRIORITIES = {
        "high",
        "medium",
        "low",
    }

    @classmethod
    def run(
        cls,
        db: Session,
        experiment_id: int,
        model_id: int,
        priorities: list[str],
        limit: int,
        force: bool = False,
    ) -> dict:

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

        normalized_priorities = {
            value.strip().lower()
            for value in priorities
        }

        invalid = (
            normalized_priorities
            - cls.VALID_PRIORITIES
        )

        if invalid:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid priorities: "
                    + ", ".join(sorted(invalid))
                ),
            )

        opportunities = (
            GeoOpportunityRepository
            .list_by_experiment(
                db,
                experiment_id,
            )
        )

        selected = [
            opportunity
            for opportunity in opportunities
            if opportunity.priority
            in normalized_priorities
        ][:limit]

        diagnosed = 0
        reused = 0
        failed = 0

        diagnosis_ids = []
        errors = []

        for opportunity in selected:

            existing = (
                GeoContentDiagnosisRepository.latest(
                    db,
                    opportunity.id,
                )
            )

            if (
                existing is not None
                and not force
            ):
                reused += 1

                diagnosis_ids.append(
                    existing.id
                )

                print(
                    "Reused diagnosis:",
                    existing.id,
                    "| opportunity:",
                    opportunity.id,
                )

                continue

            try:
                diagnosis = (
                    GeoContentDiagnosisService.diagnose(
                        db=db,
                        opportunity_id=
                            opportunity.id,
                        model_id=model_id,
                    )
                )

                diagnosed += 1

                diagnosis_ids.append(
                    diagnosis.id
                )

                print(
                    "Diagnosed opportunity:",
                    opportunity.id,
                    "-> diagnosis:",
                    diagnosis.id,
                )

            except Exception as exc:
                failed += 1

                detail = getattr(
                    exc,
                    "detail",
                    str(exc),
                )

                errors.append(
                    {
                        "opportunity_id":
                            opportunity.id,
                        "error":
                            str(detail)[:1000],
                    }
                )

                print(
                    "FAILED opportunity:",
                    opportunity.id,
                    "|",
                    detail,
                )

        return {
            "experiment_id":
                experiment_id,

            "selected_count":
                len(selected),

            "diagnosed_count":
                diagnosed,

            "reused_count":
                reused,

            "failed_count":
                failed,

            "diagnosis_ids":
                diagnosis_ids,

            "errors":
                errors,
        }
