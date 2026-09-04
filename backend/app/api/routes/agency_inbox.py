from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.operator import require_operator
from app.db.deps import get_db
from app.services.agency_inbox_service import AgencyInboxService

router = APIRouter(prefix="/agency-inbox", tags=["Agency Inbox"])


class InboxStatus(BaseModel):
    status: Literal["unread", "read", "archived"]


@router.get("")
def list_inbox(db: Session = Depends(get_db)):
    return AgencyInboxService.list_events(db)


@router.patch("/{event_id}")
def update_inbox(event_id: int, data: InboxStatus, db: Session = Depends(get_db), _operator=Depends(require_operator)):
    return AgencyInboxService.set_status(db, event_id, data.status)


@router.post("/reconcile")
def reconcile_inbox(backfill: bool = False, db: Session = Depends(get_db), _operator=Depends(require_operator)):
    AgencyInboxService.reconcile(db, backfill=backfill)
    return {"status": "reconciled"}
