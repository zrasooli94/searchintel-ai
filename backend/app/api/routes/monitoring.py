from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.operator import require_operator
from app.db.deps import get_db
from app.services.monitoring_service import MonitoringService

router = APIRouter(tags=["Monitoring"])


class MonitoringConfiguration(BaseModel):
    enabled: bool
    cadence_hours: int = 168
    source_benchmark_job_id: int | None = None
    run_after_crawl: bool = False
    paid_execution_confirmed: bool = False
    resume_now: bool = False


@router.get("/projects/{project_id}/monitoring")
def monitoring_summary(project_id: int, db: Session = Depends(get_db)):
    return MonitoringService.summary(db, project_id)


@router.put("/projects/{project_id}/monitoring/{mode}")
def configure_monitoring(project_id: int, mode: str, data: MonitoringConfiguration, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return MonitoringService.configure(db, project_id, mode, data.model_dump())


@router.post("/projects/{project_id}/monitoring/{mode}/run-now")
def run_monitoring_now(project_id: int, mode: str, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    schedule = next((item for item in MonitoringService.summary(db, project_id)["schedules"] if item["mode"] == mode), None)
    if not schedule or not schedule["id"]:
        from fastapi import HTTPException
        raise HTTPException(404, "Monitoring schedule not found.")
    return MonitoringService.execute(db, schedule["id"])


@router.post("/monitoring/process-due")
def process_due_monitoring(db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return {"processed": MonitoringService.process_due(db)}
