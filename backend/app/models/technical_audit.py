from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TechnicalAudit(Base):
    __tablename__ = "technical_audits"

    id: Mapped[int] = mapped_column(primary_key=True)

    website_id: Mapped[int] = mapped_column(
        ForeignKey("websites.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
    )

    pages_checked: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    issue_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    website = relationship(
        "Website",
        back_populates="technical_audits",
    )

    issues = relationship(
        "TechnicalIssue",
        back_populates="audit",
        cascade="all, delete-orphan",
        order_by="TechnicalIssue.id",
    )

    recommendations = relationship(
        "TechnicalRecommendation",
        back_populates="audit",
        cascade="all, delete-orphan",
        order_by="TechnicalRecommendation.priority_score.desc()",
    )
