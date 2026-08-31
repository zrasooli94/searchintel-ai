from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.benchmark_job import BenchmarkJob
from app.models.monitoring_run import MonitoringRun
from app.models.monitoring_schedule import MonitoringSchedule
from app.models.project_brand import ProjectBrand
from app.models.technical_audit import TechnicalAudit
from app.models.website import Website
from app.repositories.benchmark_repository import BenchmarkRepository
from app.repositories.project_repository import ProjectRepository
from app.services.benchmark_service import BenchmarkService
from app.services.crawler_service import CrawlerService
from app.services.geo_experiment_service import GeoExperimentService
from app.services.project_priority_service import ProjectPriorityService
from app.services.technical_audit_service import TechnicalAuditService
from app.services.visibility_metrics_service import VisibilityMetricsService
from app.services.site_rag_metrics_service import SiteRAGMetricsService
from app.repositories.site_rag_gap_analysis_repository import SiteRAGGapAnalysisRepository


class MonitoringService:
    MODES = {"technical_seo", "memory", "web_search", "site_rag"}

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    @classmethod
    def _serialize_schedule(cls, schedule, now=None):
        now = now or cls._now()
        overdue = bool(schedule.enabled and schedule.next_due_at and schedule.next_due_at < now)
        monthly = round((24 * 30 / schedule.cadence_hours) * (schedule.prompt_count or 0)) if schedule.mode != "technical_seo" else 0
        return {
            "id": schedule.id, "project_id": schedule.project_id, "mode": schedule.mode,
            "enabled": schedule.enabled, "cadence_hours": schedule.cadence_hours,
            "next_due_at": schedule.next_due_at, "last_attempted_at": schedule.last_attempted_at,
            "last_successful_at": schedule.last_successful_at, "last_result": schedule.last_result or {},
            "source_benchmark_job_id": schedule.source_benchmark_job_id, "model_id": schedule.model_id,
            "prompt_count": schedule.prompt_count, "run_after_crawl": schedule.run_after_crawl,
            "failure_message": schedule.failure_message, "overdue": overdue,
            "state": "failed" if schedule.failure_message else "overdue" if overdue else "due" if schedule.enabled and schedule.next_due_at and schedule.next_due_at <= now + timedelta(hours=24) else "scheduled" if schedule.enabled else "paused",
            "estimated_monthly_runs": monthly,
        }

    @staticmethod
    def _serialize_run(run):
        return {key: getattr(run, key) for key in (
            "id", "schedule_id", "project_id", "mode", "status", "benchmark_job_id",
            "technical_audit_id", "change_classification", "change_evidence", "error_message",
            "started_at", "completed_at",
        )}

    @classmethod
    def summary(cls, db: Session, project_id: int):
        if ProjectRepository.get_by_id(db, project_id) is None:
            raise HTTPException(404, "Project not found.")
        schedules = list(db.scalars(select(MonitoringSchedule).where(MonitoringSchedule.project_id == project_id).order_by(MonitoringSchedule.mode)).all())
        runs = list(db.scalars(select(MonitoringRun).where(MonitoringRun.project_id == project_id).order_by(MonitoringRun.id.desc()).limit(50)).all())
        sources = list(db.scalars(select(BenchmarkJob).where(
            BenchmarkJob.project_id == project_id,
            BenchmarkJob.status == "completed",
            BenchmarkJob.benchmark_mode.in_(["memory", "web_search", "site_rag"]),
        ).order_by(BenchmarkJob.id.desc())).all())
        by_mode = {item.mode: item for item in schedules}
        all_schedules = list(db.scalars(select(MonitoringSchedule)).all())
        serialized_all = [cls._serialize_schedule(item) for item in all_schedules]
        recent_improved = db.scalar(select(func.count()).select_from(MonitoringRun).where(
            MonitoringRun.change_classification == "improved",
            MonitoringRun.completed_at >= cls._now() - timedelta(days=30),
        )) or 0
        return {
            "project_id": project_id,
            "agency": {
                "needs_attention": sum(item["state"] in {"failed", "overdue"} for item in serialized_all),
                "due": sum(item["state"] == "due" for item in serialized_all),
                "overdue": sum(item["state"] == "overdue" for item in serialized_all),
                "failed": sum(item["state"] == "failed" for item in serialized_all),
                "recently_improved": recent_improved,
            },
            "schedules": [cls._serialize_schedule(by_mode[mode]) if mode in by_mode else {"id": None, "project_id": project_id, "mode": mode, "enabled": False, "cadence_hours": 168, "next_due_at": None, "last_attempted_at": None, "last_successful_at": None, "last_result": {}, "source_benchmark_job_id": None, "model_id": None, "prompt_count": None, "run_after_crawl": False, "failure_message": None, "overdue": False, "state": "not_configured", "estimated_monthly_runs": 0} for mode in ("technical_seo", "memory", "web_search", "site_rag")],
            "runs": [cls._serialize_run(run) for run in runs],
            "compatible_sources": [{"id": job.id, "mode": job.benchmark_mode, "model_id": job.model_id, "prompt_count": job.total_prompts, "completed_at": job.completed_at, "config_snapshot": job.config_snapshot or {}} for job in sources],
        }

    @classmethod
    def configure(cls, db: Session, project_id: int, mode: str, data: dict):
        if mode not in cls.MODES:
            raise HTTPException(422, "Unsupported monitoring mode.")
        if ProjectRepository.get_by_id(db, project_id) is None:
            raise HTTPException(404, "Project not found.")
        cadence = int(data.get("cadence_hours", 168))
        if cadence < 24 or cadence > 24 * 365:
            raise HTTPException(422, "Cadence must be between 24 hours and one year.")
        enabled = bool(data.get("enabled", False))
        source_id = data.get("source_benchmark_job_id")
        source = None
        if mode != "technical_seo":
            if source_id is None:
                raise HTTPException(422, "Select an approved frozen benchmark snapshot.")
            source = BenchmarkRepository.get_job(db, int(source_id))
            if source is None or source.project_id != project_id or source.status != "completed" or source.benchmark_mode != mode:
                raise HTTPException(422, "Frozen benchmark source must be a compatible completed project measurement.")
            if enabled and mode in {"memory", "web_search"} and data.get("paid_execution_confirmed") is not True:
                raise HTTPException(422, "Explicit paid scheduled-execution confirmation is required.")
        schedule = db.scalar(select(MonitoringSchedule).where(MonitoringSchedule.project_id == project_id, MonitoringSchedule.mode == mode))
        if schedule is None:
            schedule = MonitoringSchedule(project_id=project_id, mode=mode)
            db.add(schedule)
        schedule.enabled = enabled
        schedule.cadence_hours = cadence
        schedule.source_benchmark_job_id = source.id if source else None
        schedule.model_id = source.model_id if source else None
        schedule.prompt_count = source.total_prompts if source else None
        schedule.run_after_crawl = bool(data.get("run_after_crawl", False)) if mode == "site_rag" else False
        if enabled and (schedule.next_due_at is None or data.get("resume_now")):
            schedule.next_due_at = cls._now() + timedelta(hours=cadence)
        if not enabled:
            schedule.next_due_at = None
        schedule.failure_message = None
        db.commit()
        db.refresh(schedule)
        return cls._serialize_schedule(schedule)

    @classmethod
    def _technical_snapshot(cls, db, project_id):
        website = db.scalar(select(Website).join(ProjectBrand, ProjectBrand.brand_id == Website.brand_id).where(ProjectBrand.project_id == project_id, ProjectBrand.role == "target", Website.is_primary.is_(True)).order_by(Website.id).limit(1))
        if website is None:
            raise RuntimeError("No primary target website is configured.")
        previous = db.scalar(select(TechnicalAudit).where(TechnicalAudit.website_id == website.id).order_by(TechnicalAudit.id.desc()).limit(1))
        return website, previous

    @staticmethod
    def _classification(before: dict | None, after: dict, lower_is_better=False):
        if before is None:
            return "new_issue" if after.get("issue_count", after.get("failed_runs", 0)) else "stable"
        key = "issue_count" if "issue_count" in after else "completed_runs"
        old, new = before.get(key, 0), after.get(key, 0)
        if old == new:
            return "stable"
        improved = new < old if lower_is_better else new > old
        return "improved" if improved else "declined"

    @classmethod
    def _benchmark_evidence(cls, db, project_id, mode, experiment_id):
        if mode == "site_rag":
            metrics = SiteRAGMetricsService.calculate(db, project_id, experiment_id)
            analysis = SiteRAGGapAnalysisRepository.completed_by_experiment(db, experiment_id)
            return {
                "answerability_rate": metrics.get("site_answerability_rate_v1"),
                "evidence_coverage": metrics.get("evidence_coverage_rate"),
                "source_reference_rate": metrics.get("source_reference_rate"),
                "gap_count": analysis.gap_count if analysis else None,
            }
        metrics = VisibilityMetricsService.calculate(db, project_id, experiment_id, persist_snapshot=False)
        if mode == "web_search":
            return {
                "visibility": metrics.get("web_visibility_score_v1"),
                "verified_coverage": metrics.get("entity_verified_target_prompt_coverage"),
                "retrieved_coverage": metrics.get("target_source_prompt_coverage"),
                "cited_coverage": metrics.get("target_cited_response_coverage"),
            }
        return {
            "visibility": metrics.get("visibility_score_v1"),
            "target_coverage": metrics.get("target_response_coverage"),
        }

    @staticmethod
    def _benchmark_classification(before, after):
        if not before:
            return "new_issue" if (after.get("gap_count") or 0) > 0 else "stable"
        if "gap_count" in after and before.get("gap_count") is not None and after.get("gap_count") is not None:
            if before["gap_count"] > 0 and after["gap_count"] == 0:
                return "resolved_issue"
            if after["gap_count"] > before["gap_count"]:
                return "new_issue"
            if after["gap_count"] < before["gap_count"]:
                return "improved"
        key = "answerability_rate" if "answerability_rate" in after else "visibility"
        old, new = before.get(key), after.get(key)
        if old is None or new is None or old == new:
            return "stable"
        return "improved" if new > old else "declined"

    @classmethod
    def execute(cls, db: Session, schedule_id: int):
        schedule = db.scalar(select(MonitoringSchedule).where(MonitoringSchedule.id == schedule_id).with_for_update())
        if schedule is None or not schedule.enabled:
            return None
        active = db.scalar(select(MonitoringRun).where(MonitoringRun.schedule_id == schedule.id, MonitoringRun.status.in_(["pending", "running"])).limit(1))
        if active:
            return cls._serialize_run(active)
        now = cls._now()
        run = MonitoringRun(schedule_id=schedule.id, project_id=schedule.project_id, mode=schedule.mode, status="running", started_at=now)
        schedule.last_attempted_at = now
        db.add(run)
        db.commit()
        db.refresh(run)
        followup_site_rag_id = None
        try:
            if schedule.mode == "technical_seo":
                website, previous = cls._technical_snapshot(db, schedule.project_id)
                CrawlerService.crawl(db, website.id, max_pages=25)
                audit = TechnicalAuditService.run(db, website.id)
                before = {"score": previous.score, "issue_count": previous.issue_count, "pages_checked": previous.pages_checked} if previous else None
                after = {"score": audit.score, "issue_count": audit.issue_count, "pages_checked": audit.pages_checked}
                run.technical_audit_id = audit.id
                run.change_classification = cls._classification(before, after, lower_is_better=True)
                followup_site_rag_id = db.scalar(select(MonitoringSchedule.id).where(
                    MonitoringSchedule.project_id == schedule.project_id,
                    MonitoringSchedule.mode == "site_rag",
                    MonitoringSchedule.enabled.is_(True),
                    MonitoringSchedule.run_after_crawl.is_(True),
                ).limit(1))
            else:
                source = BenchmarkRepository.get_job(db, schedule.source_benchmark_job_id)
                previous = db.scalar(select(BenchmarkJob).where(BenchmarkJob.project_id == schedule.project_id, BenchmarkJob.benchmark_mode == schedule.mode, BenchmarkJob.status.in_(["completed", "completed_with_errors"])).order_by(BenchmarkJob.id.desc()).limit(1))
                experiment = GeoExperimentService.create(db, schedule.project_id, f"Scheduled {schedule.mode.replace('_', ' ').title()} {now:%Y-%m-%d %H:%M:%S} UTC", "monitoring", "Created by durable scheduled monitoring from an approved frozen prompt snapshot.")
                job = BenchmarkService.create(db, schedule.project_id, source.model_id, experiment.id, schedule.mode, source_benchmark_job_id=source.id)
                run.benchmark_job_id = job["id"]
                db.commit()
                BenchmarkService.run_job(job["id"])
                completed = BenchmarkRepository.get_job(db, job["id"])
                if completed.status not in {"completed", "completed_with_errors"}:
                    raise RuntimeError(completed.error_message or "Scheduled benchmark did not complete.")
                before = cls._benchmark_evidence(db, schedule.project_id, schedule.mode, previous.experiment_id) if previous and previous.experiment_id else None
                after = cls._benchmark_evidence(db, schedule.project_id, schedule.mode, completed.experiment_id)
                after.update({"completed_runs": completed.completed_runs, "failed_runs": completed.failed_runs, "total_prompts": completed.total_prompts})
                run.change_classification = cls._benchmark_classification(before, after)
            run.change_evidence = {"before": before, "after": after, "mode": schedule.mode, "compatible": True}
            run.status = "completed"
            run.completed_at = cls._now()
            schedule.last_successful_at = run.completed_at
            schedule.last_result = {"classification": run.change_classification, **after}
            schedule.failure_message = None
            schedule.next_due_at = run.completed_at + timedelta(hours=schedule.cadence_hours)
            ProjectPriorityService.refresh(db, schedule.project_id)
        except Exception as exc:
            db.rollback()
            run = db.get(MonitoringRun, run.id)
            schedule = db.get(MonitoringSchedule, schedule.id)
            run.status = "failed"
            run.error_message = str(exc)[:2000]
            run.completed_at = cls._now()
            schedule.failure_message = run.error_message
            schedule.next_due_at = run.completed_at + timedelta(hours=schedule.cadence_hours)
        db.commit()
        db.refresh(run)
        result = cls._serialize_run(run)
        if run.status == "completed" and followup_site_rag_id is not None:
            cls.execute(db, followup_site_rag_id)
        return result

    @classmethod
    def process_due(cls, db: Session, limit=10):
        now = cls._now()
        stale = list(db.scalars(select(MonitoringRun).where(
            MonitoringRun.status.in_(["pending", "running"]),
            MonitoringRun.started_at < now - timedelta(hours=2),
        )).all())
        for run in stale:
            run.status = "failed"
            run.completed_at = now
            run.error_message = "Scheduled execution was interrupted and recovered by the durable dispatcher."
            schedule = db.get(MonitoringSchedule, run.schedule_id)
            if schedule:
                schedule.failure_message = run.error_message
                schedule.next_due_at = now
        if stale:
            db.commit()
        ids = list(db.scalars(select(MonitoringSchedule.id).where(MonitoringSchedule.enabled.is_(True), MonitoringSchedule.next_due_at <= now).order_by(MonitoringSchedule.next_due_at).limit(limit)).all())
        return [result for schedule_id in ids if (result := cls.execute(db, schedule_id))]
