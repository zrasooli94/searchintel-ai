from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PromptSetProposal(Base):
    __tablename__ = "prompt_set_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed", index=True)
    generator_version: Mapped[str] = mapped_column(String(50), nullable=False)
    measurement_scope: Mapped[str] = mapped_column(String(20), nullable=False)
    focus_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_website_id: Mapped[int | None] = mapped_column(
        ForeignKey("websites.id", ondelete="SET NULL"), nullable=True
    )
    source_page_count: Mapped[int] = mapped_column(nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    topic_clusters: Mapped[list] = mapped_column(JSON, nullable=False)
    coverage_blueprint: Mapped[dict] = mapped_column(JSON, nullable=False)
    prompts: Mapped[list] = mapped_column(JSON, nullable=False)
    warnings: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
