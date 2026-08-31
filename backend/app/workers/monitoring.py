import logging

from app.db.session import SessionLocal
from app.services.monitoring_service import MonitoringService


def main():
    logging.basicConfig(level=logging.INFO)
    with SessionLocal() as db:
        results = MonitoringService.process_due(db)
    logging.info("Processed %s due monitoring schedule(s).", len(results))


if __name__ == "__main__":
    main()
