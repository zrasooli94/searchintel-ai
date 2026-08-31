from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.operator import require_operator
from app.db.deps import get_db
from app.repositories.client_report_repository import ClientReportRepository
from app.schemas.client_report import ClientReportCreate, ClientReportPublish, ClientReportPublishResult, ClientReportRead
from app.services.client_report_pdf_service import ClientReportPDFService
from app.services.client_report_service import ClientReportService


router = APIRouter(tags=["Client Reports"])


def _report(db: Session, project_id: int, report_id: int):
    report = ClientReportRepository.get(db, project_id, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("/projects/{project_id}/client-reports", response_model=list[ClientReportRead])
def list_reports(project_id: int, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return ClientReportRepository.list_by_project(db, project_id)


@router.get("/projects/{project_id}/client-reports/{report_id}", response_model=ClientReportRead)
def get_report(project_id: int, report_id: int, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return _report(db, project_id, report_id)


@router.post("/projects/{project_id}/client-reports", response_model=ClientReportRead, status_code=201)
def create_report(project_id: int, data: ClientReportCreate, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return ClientReportService.create(db, project_id, data.title, data.period_label)


@router.post("/projects/{project_id}/client-reports/{report_id}/publish", response_model=ClientReportPublishResult)
def publish_report(project_id: int, report_id: int, data: ClientReportPublish, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    report, token = ClientReportService.publish(db, _report(db, project_id, report_id), data.expires_at)
    return {**ClientReportRead.model_validate(report).model_dump(), "share_token": token}


@router.post("/projects/{project_id}/client-reports/{report_id}/unpublish", response_model=ClientReportRead)
def unpublish_report(project_id: int, report_id: int, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return ClientReportService.unpublish(db, _report(db, project_id, report_id))


@router.post("/projects/{project_id}/client-reports/{report_id}/revoke", response_model=ClientReportRead)
def revoke_report(project_id: int, report_id: int, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    return ClientReportService.unpublish(db, _report(db, project_id, report_id), revoked=True)


@router.get("/client-reports/share/{token}", response_model=ClientReportRead)
def shared_report(token: str, db: Session = Depends(get_db)):
    return ClientReportService.shared(db, token)


@router.get("/client-reports/share/{token}/pdf")
def shared_report_pdf(token: str, db: Session = Depends(get_db)):
    report = ClientReportService.shared(db, token)
    return Response(ClientReportPDFService.render(report), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="searchintel-report-{report.id}.pdf"', "X-Report-Content-Hash": report.content_hash})


@router.get("/projects/{project_id}/client-reports/{report_id}/pdf")
def operator_report_pdf(project_id: int, report_id: int, db: Session = Depends(get_db), _operator: None = Depends(require_operator)):
    report = _report(db, project_id, report_id)
    return Response(ClientReportPDFService.render(report), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="searchintel-report-{report.id}.pdf"', "X-Report-Content-Hash": report.content_hash})
