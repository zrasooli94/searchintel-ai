from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TechnicalRecommendation(Base):
    __tablename__ = "technical_recommendations"

    __table_args__ = (
        UniqueConstraint(
            "audit_id",
            "issue_id",
            name="uq_audit_issue_recommendation",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    audit_id: Mapped[int] = mapped_column(
        ForeignKey("technical_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    issue_id: Mapped[int] = mapped_column(
        ForeignKey("technical_issues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    issue_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    priority_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="open",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    audit = relationship(
        "TechnicalAudit",
        back_populates="recommendations",
    )
