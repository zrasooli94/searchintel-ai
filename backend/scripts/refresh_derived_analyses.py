import argparse
import json

from app.db.session import SessionLocal
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
        refreshed = MeasurementDerivationService.backfill_missing(
            db,
            project_id=args.project_id,
        )
    finally:
        db.close()

    print(json.dumps({"project_id": args.project_id, "refreshed": refreshed}))


if __name__ == "__main__":
    main()
