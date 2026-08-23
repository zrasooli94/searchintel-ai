from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Website(Base):
    __tablename__ = "websites"

    __table_args__ = (
        UniqueConstraint(
            "brand_id",
            "domain",
            name="uq_brand_domain",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    domain: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    base_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    brand = relationship(
        "Brand",
        back_populates="websites",
    )

    pages = relationship(
        "Page",
        back_populates="website",
        cascade="all, delete-orphan",
    )

    technical_audits = relationship(
        "TechnicalAudit",
        back_populates="website",
        cascade="all, delete-orphan",
    )
