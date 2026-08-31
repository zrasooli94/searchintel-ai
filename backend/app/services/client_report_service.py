import hashlib
import json
import secrets
from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel
from app.models.benchmark_job import BenchmarkJob
from app.models.client_report import ClientReport
from app.models.geo_experiment import GeoExperiment
from app.models.site_rag_gap import SiteRAGGap
from app.repositories.client_report_repository import ClientReportRepository
from app.repositories.project_brand_repository import ProjectBrandRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.site_rag_gap_analysis_repository import SiteRAGGapAnalysisRepository
from app.services.project_priority_service import ProjectPriorityService
from app.services.site_rag_metrics_service import SiteRAGMetricsService
from app.services.technical_seo_summary_service import TechnicalSEOSummaryService
from app.services.visibility_summary_service import VisibilitySummaryService


class ClientReportService:
    SNAPSHOT_VERSION = "client-report-v1"

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def _latest_measurement(cls, db: Session, project_id: int, mode: str):
        return db.execute(
            select(GeoExperiment, BenchmarkJob, AIModel)
            .join(BenchmarkJob, BenchmarkJob.experiment_id == GeoExperiment.id)
            .join(AIModel, AIModel.id == BenchmarkJob.model_id)
            .where(
                GeoExperiment.project_id == project_id,
                GeoExperiment.status == "completed",
                BenchmarkJob.status == "completed",
                BenchmarkJob.benchmark_mode == mode,
            )
            .order_by(BenchmarkJob.id.desc()).limit(1)
        ).first()

    @classmethod
    def build_snapshot(cls, db: Session, project_id: int) -> dict:
        project = ProjectRepository.get_by_id(db, project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Project not found.")
        roles = ProjectBrandRepository.list_brand_roles(db, project_id)
        target = next((brand for brand, role in roles if role == "target"), None)
        competitors = [brand.name for brand, role in roles if role == "competitor"]
        try:
            technical = TechnicalSEOSummaryService.build(db, project_id)
        except HTTPException as error:
            if error.status_code not in {400, 404}:
                raise
            technical = {"measurement_state": "unavailable", "measurement_reason": error.detail, "audit": None, "issues": [], "recommendations": []}

        measurements = {}
        provenance = []
        for mode in ("memory", "web_search", "site_rag"):
            row = cls._latest_measurement(db, project_id, mode)
            if row is None:
                measurements[mode] = None
                continue
            experiment, job, model = row
            metrics = (
                SiteRAGMetricsService.calculate(db, project_id, experiment.id)
                if mode == "site_rag"
                else VisibilitySummaryService.build(db, experiment.id)
            )
            measurements[mode] = {"experiment": {"id": experiment.id, "name": experiment.name, "phase": experiment.phase, "completed_at": experiment.completed_at}, "benchmark": {"id": job.id, "prompt_count": job.total_prompts, "model": model.name, "provider_model_id": model.provider_model_id}, "metrics": metrics}
            provenance.append({"mode": mode, "experiment_id": experiment.id, "benchmark_job_id": job.id, "model": model.name, "prompt_count": job.total_prompts, "completed_at": experiment.completed_at})

        priority_summary = ProjectPriorityService.summary(db, project_id)
        priorities = list(priority_summary["priorities"])
        active = [p for p in priorities if not p.is_resolved]
        top = sorted(active, key=lambda p: (-p.priority_score, p.id))[:5]
        completed = [p for p in priorities if p.status in {"implemented", "ready_to_recheck", "rechecked_improved", "rechecked_unchanged", "rechecked_worsened"}]
        rechecks = []
        for priority in priorities:
            comparison = (priority.provenance or {}).get("recheck_comparison")
            if not comparison:
                continue
            baseline_id = comparison.get("baseline", {}).get("experiment_id")
            recheck_id = comparison.get("recheck", {}).get("experiment_id")
            before = SiteRAGMetricsService.calculate(db, project_id, baseline_id) if baseline_id else None
            after = SiteRAGMetricsService.calculate(db, project_id, recheck_id) if recheck_id else None
            before_gaps = list(db.scalars(select(SiteRAGGap).where(SiteRAGGap.experiment_id == baseline_id)).all()) if baseline_id else []
            after_gaps = list(db.scalars(select(SiteRAGGap).where(SiteRAGGap.experiment_id == recheck_id)).all()) if recheck_id else []
            before_prompts = {g.prompt_id for g in before_gaps}
            after_prompts = {g.prompt_id for g in after_gaps}
            rechecks.append({"priority_id": priority.id, "title": priority.title, "status": priority.status, "outcome": comparison.get("outcome"), "baseline": {"experiment_id": baseline_id, "metrics": before, "gap_count": len(before_gaps)}, "recheck": {"experiment_id": recheck_id, "metrics": after, "gap_count": len(after_gaps)}, "improved_prompt_count": len(before_prompts - after_prompts), "new_gap_prompt_count": len(after_prompts - before_prompts), "explanation": "One measured prompt improved while another gap appeared, so aggregate performance remained unchanged." if comparison.get("outcome") == "unchanged" and before_prompts != after_prompts else comparison.get("note")})

        snapshot = {
            "snapshot_version": cls.SNAPSHOT_VERSION,
            "generated_at": datetime.now(timezone.utc),
            "project": {"id": project.id, "name": project.name, "target_brand": target.name if target else None, "competitors": competitors},
            "executive_summary": {"headline": f"Search intelligence summary for {target.name if target else project.name}", "note": "Each measurement is reported independently; Memory, Web Search, Site RAG, and Technical SEO are not combined into a synthetic score."},
            "technical_seo": technical,
            "measurements": measurements,
            "competitor_position": {"configured_competitors": competitors, "web_leaders": ((measurements.get("web_search") or {}).get("metrics") or {}).get("leaders", {})},
            "priorities": [{"id": p.id, "title": p.title, "status": p.status, "priority": p.priority, "recommended_action": p.recommended_action, "source_modes": p.source_modes} for p in top],
            "work_completed": [{"id": p.id, "title": p.title, "status": p.status} for p in completed],
            "compatible_rechecks": rechecks,
            "outstanding_issues": [{"title": p.title, "status": p.status, "priority": p.priority} for p in active if p.status in {"open", "in_progress"}],
            "recommended_next_actions": [p.recommended_action for p in top[:3]],
            "scope_and_provenance": {"technical_audit_id": (technical.get("audit") or {}).get("id"), "measurements": provenance, "priority_generator": ProjectPriorityService.GENERATOR_VERSION, "snapshot_note": "Derived only from stored SearchIntel evidence. Creating this report did not run AI, Web Search, crawls, or benchmarks."},
        }
        return jsonable_encoder(snapshot)

    @classmethod
    def create(cls, db: Session, project_id: int, title: str, period_label: str | None) -> ClientReport:
        snapshot = cls.build_snapshot(db, project_id)
        canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        report = ClientReport(project_id=project_id, title=title.strip(), period_label=period_label, snapshot_version=cls.SNAPSHOT_VERSION, snapshot=snapshot, content_hash=hashlib.sha256(canonical.encode()).hexdigest())
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def publish(cls, db: Session, report: ClientReport, expires_at: datetime | None) -> tuple[ClientReport, str]:
        now = datetime.now(timezone.utc)
        if expires_at is not None and expires_at <= now:
            raise HTTPException(status_code=422, detail="Expiration must be in the future.")
        token = secrets.token_urlsafe(32)
        report.status = "published"
        report.share_token_hash = cls._token_hash(token)
        report.share_token_hint = token[-6:]
        report.expires_at = expires_at
        report.published_at = now
        report.revoked_at = None
        db.commit()
        db.refresh(report)
        return report, token

    @staticmethod
    def unpublish(db: Session, report: ClientReport, revoked: bool = False) -> ClientReport:
        report.status = "revoked" if revoked else "draft"
        report.share_token_hash = None
        report.share_token_hint = None
        report.revoked_at = datetime.now(timezone.utc) if revoked else None
        db.commit()
        db.refresh(report)
        return report

    @classmethod
    def shared(cls, db: Session, token: str) -> ClientReport:
        report = ClientReportRepository.by_token_hash(db, cls._token_hash(token))
        if report is None or report.status != "published":
            raise HTTPException(status_code=404, detail="Report not found.")
        if report.expires_at is not None and report.expires_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Report link has expired.")
        return report
