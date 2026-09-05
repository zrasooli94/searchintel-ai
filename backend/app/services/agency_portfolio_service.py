"""Read-only agency portfolio projection from durable SearchIntel evidence."""

from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_model import AIModel
from app.models.benchmark_job import BenchmarkJob
from app.models.benchmark_job_item import BenchmarkJobItem
from app.models.brand import Brand
from app.models.client_report import ClientReport
from app.models.geo_experiment import GeoExperiment
from app.models.monitoring_run import MonitoringRun
from app.models.monitoring_schedule import MonitoringSchedule
from app.models.project import Project
from app.models.project_brand import ProjectBrand
from app.models.project_priority import ProjectPriority
from app.models.prompt import Prompt
from app.models.technical_audit import TechnicalAudit
from app.models.website import Website
from app.services.agency_inbox_service import AgencyInboxService
from app.services.monitoring_service import MonitoringService
from app.services.site_rag_metrics_service import SiteRAGMetricsService
from app.services.visibility_metrics_service import VisibilityMetricsService


class AgencyPortfolioService:
    """Builds an agency overview without reconciling or persisting anything."""

    MODES = ("memory", "web_search", "site_rag")
    CONFIG_KEYS = (
        "provider_model_id", "site_rag_retrieval_version", "site_rag_top_k",
        "web_search_enabled", "tool_choice",
    )

    @staticmethod
    def _aware(value):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @classmethod
    def _signature(cls, job, prompts):
        config = job.config_snapshot or {}
        frozen = sorted(text for text in prompts if text)
        if len(frozen) != job.total_prompts or not frozen:
            return None
        return (
            job.model_id, tuple(frozen),
            tuple((key, str(config.get(key))) for key in cls.CONFIG_KEYS),
        )

    @staticmethod
    def _trend(current, previous):
        if current is None or previous is None:
            return None
        delta = round(current - previous, 2)
        return {
            "state": "improved" if delta > 0 else "declined" if delta < 0 else "stable",
            "delta": delta,
            "previous": previous,
            "compatible": True,
        }

    @staticmethod
    def _report_state(report, now):
        if report is None:
            return "missing"
        expires_at = AgencyPortfolioService._aware(report.expires_at)
        if report.status == "published" and expires_at and expires_at <= now:
            return "expired"
        return report.status

    @classmethod
    def build(cls, db: Session) -> dict:
        now = datetime.now(timezone.utc)
        projects = list(db.scalars(select(Project).order_by(Project.name, Project.id)).all())
        project_ids = [project.id for project in projects]
        if not project_ids:
            return {"summary": cls._summary([]), "clients": [], "generated_at": now,
                    "provenance_note": cls._provenance_note()}

        target_rows = db.execute(
            select(ProjectBrand.project_id, Brand.id, Brand.name)
            .join(Brand, Brand.id == ProjectBrand.brand_id)
            .where(ProjectBrand.project_id.in_(project_ids), ProjectBrand.role == "target")
            .order_by(ProjectBrand.id)
        ).all()
        targets = defaultdict(list)
        for row in target_rows:
            targets[row.project_id].append(row)

        target_brand_ids = [rows[0].id for rows in targets.values() if len(rows) == 1]
        websites = list(db.scalars(
            select(Website).where(Website.brand_id.in_(target_brand_ids), Website.is_primary.is_(True))
            .order_by(Website.id)
        ).all()) if target_brand_ids else []
        websites_by_brand = defaultdict(list)
        for website in websites:
            websites_by_brand[website.brand_id].append(website)

        active_prompt_counts = dict(db.execute(
            select(Prompt.project_id, func.count(Prompt.id))
            .where(Prompt.project_id.in_(project_ids), Prompt.is_active.is_(True))
            .group_by(Prompt.project_id)
        ).all())

        audits_by_website = defaultdict(list)
        website_ids = [website.id for website in websites]
        if website_ids:
            for audit in db.scalars(
                select(TechnicalAudit).where(TechnicalAudit.website_id.in_(website_ids))
                .order_by(TechnicalAudit.created_at.desc(), TechnicalAudit.id.desc())
            ).all():
                audits_by_website[audit.website_id].append(audit)

        jobs = list(db.scalars(
            select(BenchmarkJob).join(GeoExperiment, GeoExperiment.id == BenchmarkJob.experiment_id)
            .where(BenchmarkJob.project_id.in_(project_ids), BenchmarkJob.status == "completed",
                   BenchmarkJob.benchmark_mode.in_(cls.MODES), GeoExperiment.status == "completed")
            .order_by(BenchmarkJob.completed_at.desc(), BenchmarkJob.id.desc())
        ).all())
        job_ids = [job.id for job in jobs]
        prompts_by_job = defaultdict(list)
        if job_ids:
            for job_id, text in db.execute(
                select(BenchmarkJobItem.benchmark_job_id, BenchmarkJobItem.prompt_text_snapshot)
                .where(BenchmarkJobItem.benchmark_job_id.in_(job_ids))
            ).all():
                prompts_by_job[job_id].append(text)
        models = {model.id: model for model in db.scalars(select(AIModel)).all()}
        jobs_by_project_mode = defaultdict(list)
        for job in jobs:
            jobs_by_project_mode[(job.project_id, job.benchmark_mode)].append(job)

        priorities_by_project = defaultdict(list)
        for priority in db.scalars(select(ProjectPriority).where(ProjectPriority.project_id.in_(project_ids))).all():
            priorities_by_project[priority.project_id].append(priority)

        inbox_by_project = defaultdict(list)
        for event in AgencyInboxService.list_events(db):
            inbox_by_project[event["project_id"]].append(event)

        schedules_by_project = defaultdict(list)
        for schedule in db.scalars(select(MonitoringSchedule).where(MonitoringSchedule.project_id.in_(project_ids))).all():
            schedule_now = now if schedule.next_due_at is None or schedule.next_due_at.tzinfo else now.replace(tzinfo=None)
            schedules_by_project[schedule.project_id].append(MonitoringService._serialize_schedule(schedule, schedule_now))
        latest_run_by_project = {}
        for run in db.scalars(
            select(MonitoringRun).where(MonitoringRun.project_id.in_(project_ids))
            .order_by(MonitoringRun.completed_at.desc(), MonitoringRun.id.desc())
        ).all():
            latest_run_by_project.setdefault(run.project_id, run)

        reports_by_project = defaultdict(list)
        for report in db.scalars(
            select(ClientReport).where(ClientReport.project_id.in_(project_ids))
            .order_by(ClientReport.created_at.desc(), ClientReport.id.desc())
        ).all():
            reports_by_project[report.project_id].append(report)

        clients = []
        for project in projects:
            target = targets.get(project.id, [])
            target_brand = target[0] if len(target) == 1 else None
            primary_websites = websites_by_brand.get(target_brand.id, []) if target_brand else []
            website = primary_websites[0] if len(primary_websites) == 1 else None
            setup_required = target_brand is None or website is None or active_prompt_counts.get(project.id, 0) == 0

            technical = cls._technical(website, audits_by_website, setup_required)
            measurements = {
                mode: cls._measurement(db, project.id, mode, jobs_by_project_mode, prompts_by_job, models)
                for mode in cls.MODES
            }
            priorities = [item for item in priorities_by_project[project.id] if not item.is_resolved]
            high_priorities = sum(item.priority == "high" for item in priorities)
            open_priorities = sum(item.status in {"open", "in_progress", "implemented", "ready_to_recheck",
                                                   "rechecked_unchanged", "rechecked_worsened"} for item in priorities)

            active_events = [event for event in inbox_by_project[project.id]
                             if event["status"] != "archived" and event["default_visible"]]
            needs_attention = sum(event["attention_rank"] >= 2 for event in active_events)
            high_alerts = sum(event["severity"] == "high" and event["attention_rank"] >= 2 for event in active_events)
            schedules = schedules_by_project[project.id]
            enabled = [item for item in schedules if item["enabled"]]
            monitoring_problems = [item for item in enabled if item["state"] in {"failed", "overdue"}]
            next_due = min((cls._aware(item["next_due_at"]) for item in enabled if item["next_due_at"]), default=None)
            monitoring_state = "problem" if monitoring_problems else "monitoring" if enabled else "not_configured"

            report = reports_by_project[project.id][0] if reports_by_project[project.id] else None
            latest_event = next((event for event in inbox_by_project[project.id] if event["origin"] != "backfill"), None)
            latest_run = latest_run_by_project.get(project.id)
            last_change = cls._last_change(latest_event, latest_run)

            status = cls._status(setup_required, high_priorities, needs_attention,
                                 bool(monitoring_problems), bool(enabled))
            clients.append({
                "project_id": project.id, "project_name": project.name,
                "target_brand": target_brand.name if target_brand else None,
                "status": status,
                "status_reason": cls._status_reason(status, high_priorities, needs_attention, len(monitoring_problems)),
                "technical_seo": technical,
                "web_search": measurements["web_search"],
                "memory": measurements["memory"],
                "site_rag": measurements["site_rag"],
                "priorities": {"open": open_priorities, "high": high_priorities},
                "inbox": {"needs_attention": needs_attention, "high": high_alerts},
                "monitoring": {"state": monitoring_state, "enabled_modes": len(enabled),
                               "problem_count": len(monitoring_problems), "next_due_at": next_due},
                "report": {"status": cls._report_state(report, now),
                           "created_at": report.created_at if report else None,
                           "title": report.title if report else None},
                "last_meaningful_change": last_change,
                "links": {"project": f"/projects/{project.id}", "priorities": f"/projects/{project.id}/priorities",
                          "monitoring": f"/projects/{project.id}/monitoring", "inbox": f"/agency-inbox?project={project.id}",
                          "reports": f"/projects/{project.id}/client-reports"},
            })

        clients.sort(key=cls._sort_key)
        return {"summary": cls._summary(clients), "clients": clients, "generated_at": now,
                "provenance_note": cls._provenance_note()}

    @classmethod
    def _measurement(cls, db, project_id, mode, jobs_by_project_mode, prompts_by_job, models):
        jobs = jobs_by_project_mode[(project_id, mode)]
        if not jobs:
            return {"status": "not_measured", "value": None, "trend": None,
                    "completed_at": None, "benchmark_job_id": None, "model": None}
        latest = jobs[0]
        value = None
        if latest.experiment_id and mode == "web_search":
            value = VisibilityMetricsService.calculate(
                db, project_id, latest.experiment_id, persist_snapshot=False
            ).get("web_visibility_score_v1")
        elif latest.experiment_id and mode == "site_rag":
            value = SiteRAGMetricsService.calculate(db, project_id, latest.experiment_id).get("site_answerability_rate_v1")
        signature = cls._signature(latest, prompts_by_job[latest.id])
        previous = next((job for job in jobs[1:] if signature and cls._signature(job, prompts_by_job[job.id]) == signature), None)
        previous_value = None
        if previous and previous.experiment_id and mode == "web_search":
            previous_value = VisibilityMetricsService.calculate(
                db, project_id, previous.experiment_id, persist_snapshot=False
            ).get("web_visibility_score_v1")
        elif previous and previous.experiment_id and mode == "site_rag":
            previous_value = SiteRAGMetricsService.calculate(db, project_id, previous.experiment_id).get("site_answerability_rate_v1")
        model = models.get(latest.model_id)
        return {"status": "completed", "value": value, "trend": cls._trend(value, previous_value),
                "completed_at": latest.completed_at, "benchmark_job_id": latest.id,
                "model": model.name if model else None, "prompt_count": latest.total_prompts}

    @staticmethod
    def _technical(website, audits_by_website, setup_required):
        if website is None:
            return {"status": "setup_required" if setup_required else "not_measured", "score": None,
                    "pages_checked": None, "audit_id": None}
        audits = audits_by_website.get(website.id, [])
        if not audits:
            crawl = website.last_crawl_summary or {}
            if int(crawl.get("pages_blocked_by_robots", 0) or 0) > 0:
                return {"status": "limited", "score": None, "pages_checked": 0, "audit_id": None}
            return {"status": "not_measured", "score": None, "pages_checked": None, "audit_id": None}
        audit = audits[0]
        return {"status": "limited" if audit.pages_checked <= 1 else "completed", "score": audit.score,
                "pages_checked": audit.pages_checked, "audit_id": audit.id}

    @staticmethod
    def _last_change(event, run):
        if event:
            return {"title": event["title"], "summary": event["summary"], "source_mode": event["source_mode"],
                    "occurred_at": event["occurred_at"], "path": event["evidence_path"]}
        if run and run.change_classification and run.change_classification != "stable":
            return {"title": f"Monitoring {run.change_classification.replace('_', ' ')}",
                    "summary": "The latest compatible scheduled measurement recorded a meaningful change.",
                    "source_mode": run.mode, "occurred_at": run.completed_at, "path": f"/projects/{run.project_id}/monitoring"}
        return None

    @staticmethod
    def _status(setup_required, high_priorities, attention, monitoring_problem, monitoring_enabled):
        if setup_required:
            return "setup_required"
        if monitoring_problem or high_priorities or attention:
            return "needs_attention"
        if monitoring_enabled:
            return "monitoring"
        return "healthy"

    @staticmethod
    def _status_reason(status, high_priorities, attention, monitoring_problems):
        if status == "setup_required":
            return "Target identity, primary website, or active prompts still need configuration."
        if status == "needs_attention":
            parts = []
            if monitoring_problems:
                parts.append(f"{monitoring_problems} monitoring problem(s)")
            if high_priorities:
                parts.append(f"{high_priorities} high priority item(s)")
            if attention:
                parts.append(f"{attention} Inbox signal(s)")
            return "; ".join(parts) + "."
        if status == "monitoring":
            return "No current attention signal; scheduled monitoring is active."
        return "No current setup blocker or durable attention signal."

    @staticmethod
    def _sort_key(client):
        rank = {"needs_attention": 0, "setup_required": 1, "monitoring": 2, "healthy": 3}
        urgency = client["monitoring"]["problem_count"] * 100 + client["inbox"]["high"] * 20 + client["priorities"]["high"] * 10 + client["inbox"]["needs_attention"]
        changed = client["last_meaningful_change"]
        timestamp = AgencyPortfolioService._aware(changed["occurred_at"]).timestamp() if changed and changed["occurred_at"] else 0
        return (rank[client["status"]], -urgency, -timestamp, client["project_name"].lower(), client["project_id"])

    @staticmethod
    def _summary(clients):
        return {
            "clients": len(clients),
            "needs_attention": sum(item["status"] == "needs_attention" for item in clients),
            "high_severity_alerts": sum(item["inbox"]["high"] for item in clients),
            "high_priorities": sum(item["priorities"]["high"] for item in clients),
            "monitoring_problems": sum(item["monitoring"]["problem_count"] for item in clients),
            "reports_missing": sum(item["report"]["status"] == "missing" for item in clients),
        }

    @staticmethod
    def _provenance_note():
        return ("Read-only projection of stored SearchIntel evidence. Technical SEO, Memory, Web Search, and "
                "Site RAG remain separate measurements; no synthetic portfolio score is calculated.")
