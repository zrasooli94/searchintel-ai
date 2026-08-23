from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TechnicalIssue(Base):
    __tablename__ = "technical_issues"

    id: Mapped[int] = mapped_column(primary_key=True)

    audit_id: Mapped[int] = mapped_column(
        ForeignKey("technical_audits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    page_id: Mapped[int] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    audit = relationship(
        "TechnicalAudit",
        back_populates="issues",
    )
