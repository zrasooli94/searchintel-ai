import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from pydantic import SecretStr

import app.models
from app.db.base import Base
from app.models.project import Project
from app.models.inbox_event import InboxEvent, InboxCheckpoint
from app.models.monitoring_schedule import MonitoringSchedule
from app.models.monitoring_run import MonitoringRun
from app.models.project_priority import ProjectPriority
from app.models.benchmark_job import BenchmarkJob
from app.models.benchmark_job_item import BenchmarkJobItem
from app.models.site_rag_gap import SiteRAGGap
from app.models.site_rag_gap_analysis import SiteRAGGapAnalysis
from app.services.agency_inbox_service import AgencyInboxService as Inbox
from app.api.routes.agency_inbox import router
from app.db.deps import get_db


class AgencyInboxTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(Project(id=1, name="Client", measurement_scope="brand_wide"))
        self.db.commit()
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def events(self):
        return list(self.db.scalars(select(InboxEvent).order_by(InboxEvent.id)).all())

    def schedule(self):
        s = MonitoringSchedule(project_id=1, mode="technical_seo", enabled=True, cadence_hours=168,
                               next_due_at=self.now - timedelta(hours=1), run_after_crawl=False)
        self.db.add(s); self.db.commit()
        return s

    def test_overdue_five_checks_one_event_resolution_and_recurrence(self):
        s = self.schedule()
        for _ in range(5):
            Inbox.monitoring(self.db, 1, self.now)
        self.assertEqual([e.event_type for e in self.events()], ["monitoring_overdue"])
        s.enabled = False; self.db.flush()
        Inbox.monitoring(self.db, 1, self.now)
        self.assertEqual(self.events()[-1].event_type, "monitoring_overdue_resolved")
        s.enabled = True; self.db.flush()
        Inbox.monitoring(self.db, 1, self.now)
        self.assertEqual(len(self.events()), 3)

    def test_failure_dedup_recovery_no_raw_error_secrets(self):
        s = self.schedule(); s.next_due_at = self.now + timedelta(days=1)
        self.db.add(MonitoringRun(schedule_id=s.id, project_id=1, mode="technical_seo", status="failed", error_message="secret-provider-value", started_at=self.now, completed_at=self.now))
        self.db.commit()
        for _ in range(3): Inbox.monitoring(self.db, 1, self.now)
        self.assertEqual(len(self.events()), 1)
        self.assertNotIn("secret-provider-value", str(Inbox.list_events(self.db)))
        self.db.add(MonitoringRun(schedule_id=s.id, project_id=1, mode="technical_seo", status="completed", started_at=self.now, completed_at=self.now))
        self.db.commit(); Inbox.monitoring(self.db, 1, self.now)
        self.assertEqual(self.events()[-1].event_type, "monitoring_failure_resolved")

    def test_lifecycle_persists_and_evidence_is_immutable(self):
        self.schedule(); Inbox.monitoring(self.db, 1, self.now); self.db.commit()
        event = self.events()[0]; original = event.evidence.copy()
        for status in ("read", "unread", "archived"):
            Inbox.set_status(self.db, event.id, status); self.db.expire_all()
            self.assertEqual(self.db.get(InboxEvent, event.id).status, status)
            self.assertEqual(self.db.get(InboxEvent, event.id).evidence, original)
        Inbox.monitoring(self.db, 1, self.now)
        self.assertEqual(len(self.events()), 1)

    def test_get_is_read_only(self):
        self.schedule(); Inbox.monitoring(self.db, 1, self.now); self.db.commit()
        with patch.object(self.db, "commit") as commit, patch.object(self.db, "add") as add, patch.object(self.db, "flush") as flush:
            self.db.autoflush = False
            self.assertEqual(len(Inbox.list_events(self.db)), 1)
            commit.assert_not_called(); add.assert_not_called(); flush.assert_not_called()

    def test_internal_thresholds_stable_null_and_mode_separation(self):
        self.assertEqual(Inbox.metric_changes("web_search", {"visibility": 90}, {"visibility": 92}), [])
        self.assertEqual(Inbox.metric_changes("memory", {"visibility": 90}, {"visibility": 50}), [])
        self.assertEqual(Inbox.metric_changes("site_rag", {"answerability": None}, {"answerability": 0}), [])
        event = Inbox.metric_changes("web_search", {"visibility": 90}, {"visibility": 75})[0]
        self.assertEqual(event[:2], ("visibility_declined", "high"))
        self.assertEqual(Inbox.metric_changes("site_rag", {"answerability": 80}, {"answerability": 90})[0][1], "low")
        self.assertEqual(Inbox.metric_changes("web_search", {"target_coverage": 1}, {"target_coverage": 0})[0][0], "target_coverage_lost")

    def test_checkpoint_seed_retry_and_distinct_compatible_series(self):
        before, revision = Inbox.observe(self.db, 1, "web-model1-promptsA", {"visibility": 90})
        self.assertIsNone(before)
        self.assertIsNotNone(revision)
        self.assertIsNone(Inbox.observe(self.db, 1, "web-model1-promptsA", {"visibility": 90})[1])
        self.assertIsNone(Inbox.observe(self.db, 1, "rag-model1-promptsA", {"answerability": 50})[0])
        self.assertIsNone(Inbox.observe(self.db, 1, "web-model2-promptsA", {"visibility": 40})[0])
        self.assertEqual(len(self.events()), 0)

    def test_public_get_and_operator_mutations(self):
        app = FastAPI(); app.include_router(router)
        app.dependency_overrides[get_db] = lambda: MagicMock()
        client = TestClient(app)
        with patch("app.api.operator.settings") as settings, patch.object(Inbox, "list_events", return_value=[]), patch.object(Inbox, "set_status", return_value={"id": 1, "status": "read"}) as change:
            settings.api_token = SecretStr("test-only-operator")
            self.assertEqual(client.get("/agency-inbox").status_code, 200)
            self.assertEqual(client.patch("/agency-inbox/1", json={"status": "read"}).status_code, 403)
            self.assertEqual(client.post("/agency-inbox/reconcile").status_code, 403)
            change.assert_not_called()
            self.assertEqual(client.patch("/agency-inbox/1", json={"status": "read"}, headers={"X-SearchIntel-Operator": "test-only-operator"}).status_code, 200)

    def job(self, number, mode="web_search", prompt="Frozen original", model=1):
        job = BenchmarkJob(id=number, project_id=1, experiment_id=number, model_id=model,
            benchmark_mode=mode, status="completed", completed_at=self.now + timedelta(minutes=number), total_prompts=1)
        self.db.add(job)
        self.db.add(BenchmarkJobItem(benchmark_job_id=number, prompt_id=1, prompt_text_snapshot=prompt, status="completed"))
        self.db.commit()
        return job

    def test_completed_measurements_generate_once_only_when_compatible(self):
        self.job(1)
        with patch("app.services.visibility_metrics_service.VisibilityMetricsService.calculate") as metrics:
            metrics.return_value = {"web_visibility_score_v1": 90, "entity_verified_target_prompt_coverage": 100}
            Inbox.measurements(self.db, 1)
            self.assertEqual(len(self.events()), 0)  # Backfill seeds, no historical flood.
            self.job(2)
            metrics.return_value = {"web_visibility_score_v1": 70, "entity_verified_target_prompt_coverage": 100}
            Inbox.measurements(self.db, 1)
            self.assertEqual(len(self.events()), 1)
            self.assertEqual(self.events()[0].evidence["before"]["visibility"], 90)
            Inbox.measurements(self.db, 1)
            self.assertEqual(len(self.events()), 1)
            self.job(3, prompt="Different snapshot")
            metrics.return_value = {"web_visibility_score_v1": 10}
            Inbox.measurements(self.db, 1)
            self.assertEqual(len(self.events()), 1)
            for call in metrics.call_args_list:
                self.assertFalse(call.kwargs["persist_snapshot"])

    def test_recheck_requires_same_mode_model_and_exact_frozen_prompts(self):
        self.job(1, mode="site_rag"); second = self.job(2, mode="site_rag")
        comparison = {"measurement_mode": "site_rag", "baseline": {"experiment_id": 1}, "recheck": {"experiment_id": 2}}
        self.assertTrue(Inbox.compatible_recheck(self.db, 1, comparison))
        second.model_id = 2; self.db.commit()
        self.assertFalse(Inbox.compatible_recheck(self.db, 1, comparison))
        second.model_id = 1; second.benchmark_mode = "memory"; self.db.commit()
        self.assertFalse(Inbox.compatible_recheck(self.db, 1, comparison))

    def test_site_gap_replacement_then_zero_gaps_preserves_events(self):
        def analysis(number, prompts):
            self.job(number, mode="site_rag")
            self.db.add(SiteRAGGapAnalysis(experiment_id=number, project_id=1, target_brand_id=1,
                gap_version="v1", status="completed", total_prompts=1, gap_count=len(prompts), refreshed_at=self.now))
            for index, text in enumerate(prompts):
                self.db.add(SiteRAGGap(experiment_id=number, project_id=1, prompt_id=index + 1, target_brand_id=1,
                    prompt_text=text, category="comparison", run_count=1, answerable_runs=0, unsupported_runs=1,
                    answerability_rate=0, unsupported_rate=100, gap_type="competitive_evidence_gap", gap_score=90,
                    priority="high", evidence={}, recommendation="Add factual evidence"))
            self.db.commit()
        with patch("app.services.site_rag_metrics_service.SiteRAGMetricsService.calculate", return_value={"site_answerability_rate_v1": 90}):
            analysis(1, ["Prompt A"]); Inbox.measurements(self.db, 1)
            analysis(2, ["Prompt B"]); Inbox.measurements(self.db, 1)
            self.assertEqual({e.event_type for e in self.events()}, {"site_rag_gap_new", "site_rag_gap_resolved"})
            analysis(3, []); Inbox.measurements(self.db, 1)
            self.assertEqual(len(self.events()), 3)
            self.assertEqual(self.events()[-1].evidence["after"]["gaps"], [])
            Inbox.measurements(self.db, 1)
            self.assertEqual(len(self.events()), 3)

    def test_current_high_priority_backfill_dedup_resolution(self):
        priority = ProjectPriority(project_id=1, stable_key="evidence:comparison", title="Add comparison evidence",
            priority="high", priority_score=80, impact="high", effort="medium", confidence="high", status="open",
            observed_evidence=["Two stored gaps"], interpretation="First-party evidence is missing", recommended_action="Add factual comparisons",
            affected_prompts=[], affected_pages=[], affected_entities=[], source_modes=["site_rag"], score_components={},
            provenance={}, evidence_fingerprint="a" * 64, is_resolved=False)
        self.db.add(priority); self.db.commit()
        for _ in range(3): Inbox.priorities(self.db, 1)
        self.assertEqual(len(self.events()), 1)
        priority.is_resolved = True; priority.resolved_at = self.now; self.db.flush()
        Inbox.priorities(self.db, 1)
        self.assertEqual(self.events()[-1].event_type, "priority_resolved")


if __name__ == "__main__":
    unittest.main()
