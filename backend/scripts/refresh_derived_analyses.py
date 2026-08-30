import argparse
import json

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.ai_run import AIRun
from app.models.geo_experiment import GeoExperiment
from app.services.measurement_derivation_service import MeasurementDerivationService


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh deterministic derived analyses without running AI.",
    )
    parser.add_argument("--project-id", type=int, required=True)
    args = parser.parse_args()

    db = SessionLocal()
    refreshed = []
    try:
        experiments = list(db.scalars(
            select(GeoExperiment)
            .where(
                GeoExperiment.project_id == args.project_id,
                GeoExperiment.status == "completed",
            )
            .order_by(GeoExperiment.id)
        ).all())

        for experiment in experiments:
            modes = set(db.scalars(
                select(AIRun.benchmark_mode)
                .where(
                    AIRun.experiment_id == experiment.id,
                    AIRun.include_in_metrics.is_(True),
                    AIRun.status == "completed",
                )
                .distinct()
            ).all())
            if len(modes) != 1:
                continue
            mode = next(iter(modes))
            result = MeasurementDerivationService.refresh(
                db,
                experiment.id,
                mode,
            )
            if result is not None:
                refreshed.append({
                    "experiment_id": experiment.id,
                    "benchmark_mode": mode,
                    "total_prompts": result["total_prompts"],
                    "derived_items": len(
                        result.get("opportunities", result.get("gaps", []))
                    ),
                })
    finally:
        db.close()

    print(json.dumps({"project_id": args.project_id, "refreshed": refreshed}))


if __name__ == "__main__":
    main()
