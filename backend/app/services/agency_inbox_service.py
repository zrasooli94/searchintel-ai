"""Deterministic Inbox V1. No network calls, metric writes, or GET reconciliation."""
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select

from app.models.inbox_event import InboxCheckpoint, InboxEvent
from app.models.project import Project
from app.models.project_priority import ProjectPriority
from app.models.monitoring_schedule import MonitoringSchedule
from app.models.monitoring_run import MonitoringRun
from app.models.benchmark_job import BenchmarkJob
from app.models.benchmark_job_item import BenchmarkJobItem
from app.models.project_brand import ProjectBrand
from app.models.website import Website
from app.models.technical_audit import TechnicalAudit
from app.models.site_rag_gap import SiteRAGGap
from app.repositories.site_rag_gap_analysis_repository import SiteRAGGapAnalysisRepository


class AgencyInboxService:
    VERSION = "agency-inbox-v1"

    @classmethod
    def compatible_recheck(cls, db, project_id, comparison):
        mode = comparison.get("measurement_mode")
        signatures = []
        for side in ("baseline", "recheck"):
            experiment_id = comparison.get(side, {}).get("experiment_id")
            job = db.scalar(select(BenchmarkJob).where(BenchmarkJob.project_id == project_id,
                BenchmarkJob.experiment_id == experiment_id, BenchmarkJob.benchmark_mode == mode,
                BenchmarkJob.status == "completed").order_by(BenchmarkJob.id.desc()).limit(1))
            if not experiment_id or not job:
                return False
            prompts = list(db.scalars(select(BenchmarkJobItem.prompt_text_snapshot).where(BenchmarkJobItem.benchmark_job_id == job.id)).all())
            if not prompts or any(not text for text in prompts):
                return False
            config = job.config_snapshot or {}
            signatures.append([job.model_id, sorted(prompts), {k: config.get(k) for k in
                ("provider_model_id", "site_rag_retrieval_version", "site_rag_top_k", "web_search_enabled", "tool_choice")}])
        return signatures[0] == signatures[1]

    @staticmethod
    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

    @classmethod
    def observe(cls, db, project_id, key, payload):
        key = f"{project_id}:{key}"
        row = db.get(InboxCheckpoint, key)
        before = row.payload if row else None
        if before == payload:
            return before, None
        if row is None:
            row = InboxCheckpoint(key=key, project_id=project_id, revision=0, payload={})
            db.add(row)
        row.revision += 1
        row.payload = payload
        db.flush()
        return before, f"{key}:{row.revision}"

    @classmethod
    def emit(cls, db, project_id, identity, event_type, severity, mode, title,
             summary, before, after, related, occurred_at, page):
        key = cls.digest([cls.VERSION, project_id, identity, event_type])
        if db.scalar(select(InboxEvent.id).where(InboxEvent.dedup_key == key)):
            return
        db.add(InboxEvent(project_id=project_id, event_type=event_type, severity=severity,
            source_mode=mode, title=title[:255], summary=summary,
            evidence={"before": before, "after": after, "rules_version": cls.VERSION},
            related_ids=related, evidence_path=f"/projects/{project_id}/{page}",
            dedup_key=key, occurred_at=occurred_at or datetime.now(timezone.utc), status="unread",
            origin=db.info.get("inbox_origin", "workflow")))
        db.flush()

    @staticmethod
    def metric_changes(mode, before, after):
        """Internal V1 thresholds; points on a 0–100 scale, never industry standards."""
        changes = []
        fields = {"web_search": [("visibility", "Web Search visibility"), ("target_coverage", "Verified target coverage")],
                  "site_rag": [("answerability", "First-party answerability")],
                  "technical_seo": [("score", "Bounded technical sample score")]}.get(mode, [])
        for field, label in fields:
            old, new = before.get(field), after.get(field)
            if old is None or new is None:
                continue
            delta = new - old
            threshold = 5
            if field == "target_coverage" and ((old == 0) != (new == 0)):
                kind = "target_coverage_gained" if new > old else "target_coverage_lost"
            elif abs(delta) >= threshold:
                kind = f"{field}_{'improved' if delta > 0 else 'declined'}"
            else:
                continue
            changes.append((kind, "low" if delta > 0 else "high" if abs(delta) >= 10 else "medium",
                            f"{label} {'improved' if delta > 0 else 'declined'}",
                            f"{label}: {old} → {new}. This comparison applies only to compatible {mode.replace('_', ' ')} measurements."))
        # Compare the same configured competitor IDs, not retrieved sources or citations.
        for brand in sorted(set(before.get("competitors", {})) & set(after.get("competitors", {}))):
            old, new = before["competitors"][brand], after["competitors"][brand]
            if abs(new - old) >= 10:
                changes.append((f"competitor_position_changed_{brand}", "medium", "Competitor response position changed",
                                f"Competitor #{brand} grounded response share: {old}% → {new}%. This is controlled Web Search response evidence, not market share."))
        return changes

    @classmethod
    def priorities(cls, db, project_id):
        groups = {}
        for p in db.scalars(select(ProjectPriority).where(ProjectPriority.project_id == project_id)).all():
            modes = [m for m in (p.source_modes or []) if m != "readiness"]
            mode = modes[0] if len(modes) == 1 else "multiple"
            active = p.priority == "high" and not p.is_resolved
            before, revision = cls.observe(db, project_id, f"priority:{p.id}", {"active_high": active, "resolved": p.is_resolved})
            if revision and (active or (before and before["active_high"] and p.is_resolved)):
                resolved = p.is_resolved
                source = {k: v for k, v in (p.provenance or {}).items() if k in
                          ("technical_audit_id", "web_experiment_id", "site_rag_experiment_id", "readiness_state")}
                key = cls.digest([mode, resolved, source])
                groups.setdefault(key, []).append((p, revision, before, mode, source))
            comparison = (p.provenance or {}).get("recheck_comparison")
            if p.status.startswith("rechecked_") and comparison and comparison.get("baseline") and comparison.get("recheck") and cls.compatible_recheck(db, project_id, comparison):
                outcome = comparison.get("outcome")
                if outcome not in {"improved", "unchanged", "worsened"}:
                    continue
                identity = cls.digest([p.id, comparison["baseline"], comparison["recheck"], outcome])
                cls.emit(db, project_id, identity, f"priority_rechecked_{outcome}",
                         {"improved": "low", "unchanged": "medium", "worsened": "high"}[outcome],
                         comparison.get("measurement_mode", mode), f"Recheck {outcome}: {p.title}",
                         "The stored compatible recheck found " + outcome + " evidence. Review the before/after details before choosing the next action.",
                         comparison["baseline"], comparison["recheck"], {"priority_id": p.id},
                         datetime.fromisoformat(comparison["compared_at"]) if comparison.get("compared_at") else p.updated_at, "priorities")
        for members in groups.values():
            members.sort(key=lambda item: item[0].id)
            p, _, _, mode, source = members[0]
            resolved = p.is_resolved
            count = len(members)
            label = "Technical audit" if source.get("technical_audit_id") else "Evidence review"
            cls.emit(db, project_id, [item[1] for item in members],
                     "priority_resolved" if resolved else "priority_new_high",
                     "low" if resolved else "high", mode,
                     f"{label}: {count} {'resolved' if resolved else 'new actionable'} work package{'s' if count != 1 else ''}",
                     "Related high-priority work is grouped here. Priority Center retains each item and its evidence.",
                     {str(item.id): previous for item, _, previous, _, _ in members},
                     {"resolved": resolved, "work_packages": [{"priority_id": item.id, "title": item.title,
                       "observed_evidence": item.observed_evidence, "provenance": item.provenance} for item, *_ in members]},
                     {**source, "priority_ids": [item.id for item, *_ in members]},
                     max(item.resolved_at or item.updated_at for item, *_ in members), "priorities")

    @classmethod
    def monitoring(cls, db, project_id, now):
        for schedule in db.scalars(select(MonitoringSchedule).where(MonitoringSchedule.project_id == project_id)).all():
            due = schedule.next_due_at
            if due and due.tzinfo is None:  # SQLite test parity
                due = due.replace(tzinfo=timezone.utc)
            overdue = bool(schedule.enabled and due and due < now)
            before, revision = cls.observe(db, project_id, f"overdue:{schedule.id}", {"overdue": overdue})
            if revision and (overdue or (before and before["overdue"])):
                cls.emit(db, project_id, revision, "monitoring_overdue" if overdue else "monitoring_overdue_resolved",
                         "high" if overdue else "low", schedule.mode,
                         "Monitoring check is overdue" if overdue else "Monitoring overdue condition cleared",
                         "The persisted schedule passed its due time." if overdue else "The schedule is no longer overdue; it may have completed, been paused, or rescheduled.",
                         before, {"overdue": overdue, "next_due_at": due.isoformat() if due else None},
                         {"schedule_id": schedule.id}, now, "monitoring")
        latest_runs = {}
        for run in db.scalars(select(MonitoringRun).where(MonitoringRun.project_id == project_id).order_by(MonitoringRun.id.desc())).all():
            latest_runs.setdefault(run.schedule_id, run)
        for run in latest_runs.values():
            before, revision = cls.observe(db, project_id, f"failure:{run.schedule_id}", {"failed": run.status == "failed"})
            if revision and before and before["failed"] and run.status == "completed":
                cls.emit(db, project_id, revision, "monitoring_failure_resolved", "low", run.mode,
                         "Monitoring recovered", "A later measurement completed successfully after the failed execution.",
                         before, {"status": run.status}, {"execution_id": run.id, "schedule_id": run.schedule_id}, run.completed_at, "monitoring")
            if run.status != "failed":
                continue
            cls.emit(db, project_id, f"execution:{run.id}", "monitoring_failed", "high", run.mode,
                     "Scheduled measurement failed", "The measurement did not complete. Review execution history before retrying.",
                     None, {"status": "failed"}, {"execution_id": run.id, "schedule_id": run.schedule_id}, run.completed_at, "monitoring")

    @classmethod
    def measurements(cls, db, project_id):
        from app.services.visibility_metrics_service import VisibilityMetricsService
        from app.services.site_rag_metrics_service import SiteRAGMetricsService
        # Configuration changes start a new comparison series: never call changed attribution a measured gain.
        brands = list(db.execute(select(ProjectBrand.brand_id, ProjectBrand.role).where(ProjectBrand.project_id == project_id)).all())
        websites = list(db.scalars(select(Website).where(Website.brand_id.in_([b[0] for b in brands]))).all())
        identity = [sorted([list(b) for b in brands]), sorted((w.brand_id, w.domain) for w in websites)]
        for mode in ("web_search", "site_rag"):
            job = db.scalar(select(BenchmarkJob).where(BenchmarkJob.project_id == project_id, BenchmarkJob.benchmark_mode == mode,
                            BenchmarkJob.status == "completed").order_by(BenchmarkJob.completed_at.desc(), BenchmarkJob.id.desc()).limit(1))
            if not job or not job.experiment_id:
                continue
            prompts = list(db.scalars(select(BenchmarkJobItem.prompt_text_snapshot).where(BenchmarkJobItem.benchmark_job_id == job.id)).all())
            if not prompts or any(not p for p in prompts):
                continue  # Missing frozen evidence is not a compatible comparison.
            config = job.config_snapshot or {}
            key = "measurement:" + cls.digest([mode, job.model_id, sorted(prompts), identity,
                {k: config.get(k) for k in ("provider_model_id", "site_rag_retrieval_version", "site_rag_top_k", "web_search_enabled", "tool_choice")}])
            checkpoint = db.get(InboxCheckpoint, f"{project_id}:{key}")
            if checkpoint and checkpoint.payload.get("benchmark_job_id") == job.id:
                continue
            after = {"benchmark_job_id": job.id, "experiment_id": job.experiment_id, "prompt_count": len(prompts)}
            if mode == "site_rag":
                analysis = SiteRAGGapAnalysisRepository.completed_by_experiment(db, job.experiment_id)
                if not analysis:
                    continue  # No analysis is not zero gaps.
                metrics = SiteRAGMetricsService.calculate(db, project_id, job.experiment_id)
                gaps = list(db.scalars(select(SiteRAGGap).where(SiteRAGGap.experiment_id == job.experiment_id)).all())
                after.update(answerability=metrics["site_answerability_rate_v1"], gaps=sorted(g.prompt_text for g in gaps), analysis_id=analysis.id)
            else:
                metrics = VisibilityMetricsService.calculate(db, project_id, job.experiment_id, persist_snapshot=False)
                after.update(visibility=metrics.get("web_visibility_score_v1"), target_coverage=metrics.get("entity_verified_target_prompt_coverage"))
                competitor_ids = {b[0] for b in brands if b[1] == "competitor"}
                after["competitors"] = {str(row["brand_id"]): row["grounded_response_share_of_voice"] for row in metrics.get("grounded_response_share_of_voice", [])
                                        if row.get("brand_id") in competitor_ids and isinstance(row.get("grounded_response_share_of_voice"), (float, int))}
            before, revision = cls.observe(db, project_id, key, after)
            if before and revision:
                for kind, severity, title, summary in cls.metric_changes(mode, before, after):
                    cls.emit(db, project_id, revision, kind, severity, mode, title, summary, before, after,
                             {"benchmark_job_id": job.id, "experiment_id": job.experiment_id}, job.completed_at, "ai-visibility")
                if mode == "site_rag":
                    for kind, values in (("new", set(after["gaps"]) - set(before["gaps"])), ("resolved", set(before["gaps"]) - set(after["gaps"]))):
                        if values:
                            cls.emit(db, project_id, revision, f"site_rag_gap_{kind}", "medium" if kind == "new" else "low", mode,
                                     f"{len(values)} first-party evidence gap(s) {kind}",
                                     "Compared the same frozen prompts. These are first-party answerability gaps, not general SEO or Web Search findings.",
                                     before, {**after, "changed_prompts": sorted(values)}, {"benchmark_job_id": job.id, "analysis_id": analysis.id}, job.completed_at, "prompt-gaps")
        target_ids = {b[0] for b in brands if b[1] == "target"}
        for website in websites:
            if website.brand_id not in target_ids or not website.is_primary:
                continue
            audit = db.scalar(select(TechnicalAudit).where(TechnicalAudit.website_id == website.id).order_by(TechnicalAudit.id.desc()).limit(1))
            if not audit or not audit.pages_checked:
                continue
            after = {"audit_id": audit.id, "score": audit.score, "pages_checked": audit.pages_checked, "issue_count": audit.issue_count}
            before, revision = cls.observe(db, project_id, f"technical:{website.id}", after)
            # Changed sample size cannot substantiate a directional score claim.
            if before and revision and before["pages_checked"] == after["pages_checked"]:
                for kind, severity, title, summary in cls.metric_changes("technical_seo", before, after):
                    cls.emit(db, project_id, revision, kind, severity, "technical_seo", title,
                             summary + " Equal page counts do not guarantee identical crawl coverage; inspect both audits.",
                             before, after, {"technical_audit_id": audit.id}, audit.created_at, "technical-seo")

    @classmethod
    def reconcile(cls, db, project_id=None, *, backfill=False):
        ids = [project_id] if project_id else list(db.scalars(select(Project.id).order_by(Project.id)).all())
        for pid in ids:
            # Serialize writers per project, including simultaneous backfill/completion/cron.
            if db.scalar(select(Project).where(Project.id == pid).with_for_update()) is None:
                continue
            previous_origin = db.info.get("inbox_origin", "workflow")
            db.info["inbox_origin"] = "backfill" if backfill else "workflow"
            try:
                cls.priorities(db, pid)
                cls.monitoring(db, pid, datetime.now(timezone.utc))
                cls.measurements(db, pid)
            finally:
                db.info["inbox_origin"] = previous_origin
        db.commit()

    @classmethod
    def reconcile_safely(cls, db, project_id=None):
        try:
            cls.reconcile(db, project_id)
        except Exception:
            db.rollback()
            # Do not turn a completed measurement into a failed job or log provider payloads.
            logging.getLogger(__name__).error("Inbox reconciliation failed; retry through the operator reconciliation endpoint or dispatcher.")

    @classmethod
    def list_events(cls, db):
        rows = db.execute(select(InboxEvent, Project.name).join(Project, Project.id == InboxEvent.project_id).order_by(InboxEvent.occurred_at.desc(), InboxEvent.id.desc())).all()
        priorities = {p.id: p for p in db.scalars(select(ProjectPriority)).all()}
        schedules = {s.id: s for s in db.scalars(select(MonitoringSchedule)).all()}
        latest_runs = {}
        for run in db.scalars(select(MonitoringRun).order_by(MonitoringRun.id.desc())).all():
            latest_runs.setdefault(run.schedule_id, run)
        latest_analyses = {}
        for pid in {event.project_id for event, _ in rows if event.event_type.startswith("priority_rechecked_")}:
            latest_analyses[pid] = SiteRAGGapAnalysisRepository.latest_completed_by_project(db, pid)
        now = datetime.now(timezone.utc)
        return [{**{column.name: getattr(event, column.name) for column in InboxEvent.__table__.columns if column.name != "dedup_key"},
                 "project_name": name, **cls.signal(event, priorities, schedules, latest_runs, latest_analyses, now)} for event, name in rows]

    @staticmethod
    def signal(event, priorities, schedules, latest_runs, latest_analyses, now):
        """Read-only presentation policy. Never rewrite event evidence or lifecycle."""
        kind, related = event.event_type, event.related_ids or {}
        occurred = event.occurred_at
        if occurred.tzinfo is None:
            occurred = occurred.replace(tzinfo=timezone.utc)
        recent = now - timedelta(days=30) <= occurred <= now
        historical = event.origin == "backfill"
        improvement = "improved" in kind or "resolved" in kind or kind == "target_coverage_gained"
        rank, ongoing = 0, False
        reason = "Historical evidence; not a new notification." if historical else "Outside the recent meaningful-change window."
        ids = related.get("priority_ids", [related.get("priority_id")])
        current = [priorities[i] for i in ids if i in priorities and priorities[i].project_id == event.project_id]
        if kind.startswith("priority_rechecked_") and not improvement:
            for p in current:
                comparison = (p.provenance or {}).get("recheck_comparison", {})
                latest = latest_analyses.get(event.project_id)
                if (not p.is_resolved and p.status == kind.removeprefix("priority_")
                        and comparison.get("baseline") == event.evidence.get("before")
                        and comparison.get("recheck") == event.evidence.get("after")
                        and latest and latest.experiment_id == comparison.get("recheck", {}).get("experiment_id")):
                    ongoing = True
                    rank = 4 if kind.endswith("worsened") else 2
                    reason = "The latest persisted compatible recheck still requires follow-up."
        elif kind in {"monitoring_failed", "monitoring_overdue"}:
            schedule = schedules.get(related.get("schedule_id"))
            run = latest_runs.get(related.get("schedule_id"))
            if schedule and schedule.project_id == event.project_id:
                due = schedule.next_due_at
                if due and due.tzinfo is None:
                    due = due.replace(tzinfo=timezone.utc)
                ongoing = bool(schedule.enabled and ((kind == "monitoring_overdue" and due and due < now
                               and event.evidence.get("after", {}).get("next_due_at") == due.isoformat())
                               or (kind == "monitoring_failed" and run and run.status == "failed"
                                   and run.id == related.get("execution_id"))))
                if ongoing:
                    rank, reason = 4, "The current monitoring condition still needs attention."
        elif recent and not historical:
            if kind == "priority_new_high":
                if any(p.priority == "high" and not p.is_resolved and p.status in {"open", "in_progress"} for p in current):
                    rank = 3
            elif improvement:
                rank = 1
            elif kind.endswith("declined") or kind == "target_coverage_lost":
                rank = 4
            elif kind == "site_rag_gap_new" or kind.startswith("competitor_position_changed_"):
                rank = 3
            if rank:
                reason = "Meaningful change observed within the last 30 days."
        return {"default_visible": bool(rank and (ongoing or (recent and not historical))),
                "attention_rank": rank, "attention_reason": reason, "is_improvement": improvement}

    @staticmethod
    def set_status(db, event_id, status):
        if status not in {"unread", "read", "archived"}:
            raise HTTPException(422, "Invalid Inbox status.")
        event = db.get(InboxEvent, event_id)
        if event is None:
            raise HTTPException(404, "Inbox event not found.")
        event.status = status
        db.commit()
        return {"id": event.id, "status": event.status}
