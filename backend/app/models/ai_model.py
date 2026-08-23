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


class AIModel(Base):
    __tablename__ = "ai_models"

    __table_args__ = (
        UniqueConstraint(
            "engine_id",
            "provider_model_id",
            name="uq_engine_provider_model",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    engine_id: Mapped[int] = mapped_column(
        ForeignKey("ai_engines.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    provider_model_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    engine = relationship(
        "AIEngine",
        back_populates="models",
    )

    runs = relationship(
        "AIRun",
        back_populates="model",
    )
