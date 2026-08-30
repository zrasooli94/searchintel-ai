from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProjectPriority(Base):
    __tablename__ = "project_priorities"
    __table_args__ = (
        UniqueConstraint("project_id", "stable_key", name="uq_project_priority_stable_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stable_key: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    priority_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    impact: Mapped[str] = mapped_column(String(20), nullable=False)
    effort: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="open", index=True)
    observed_evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    affected_prompts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    affected_pages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    affected_entities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_modes: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    score_components: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    provenance: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    evidence_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

