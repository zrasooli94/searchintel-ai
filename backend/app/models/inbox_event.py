from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InboxEvent(Base):
    __tablename__ = "inbox_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(10), index=True)
    source_mode: Mapped[str] = mapped_column(String(30), index=True)
    title: Mapped[str] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict] = mapped_column(JSON)
    related_ids: Mapped[dict] = mapped_column(JSON)
    evidence_path: Mapped[str] = mapped_column(String(255))
    dedup_key: Mapped[str] = mapped_column(String(64), unique=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(10), default="unread", index=True)


class InboxCheckpoint(Base):
    """Internal cursor only; published event evidence is never overwritten."""
    __tablename__ = "inbox_checkpoints"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON)
