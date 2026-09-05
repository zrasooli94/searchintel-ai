import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models
from app.db.base import Base
from app.models.benchmark_job import BenchmarkJob
from app.models.benchmark_job_item import BenchmarkJobItem
from app.models.brand import Brand
from app.models.geo_experiment import GeoExperiment
from app.models.monitoring_schedule import MonitoringSchedule
from app.models.project import Project
from app.models.project_brand import ProjectBrand
from app.models.project_priority import ProjectPriority
from app.models.prompt import Prompt
from app.models.technical_audit import TechnicalAudit
from app.models.website import Website
from app.services.agency_portfolio_service import AgencyPortfolioService


class AgencyPortfolioServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.now = datetime.now(timezone.utc)
        for project_id, name in ((1, "Vercel"), (2, "CXOps"), (3, "New Client")):
            self.db.add(Project(id=project_id, name=name, measurement_scope="brand_wide"))
        for brand_id, project_id, name in ((1, 1, "Vercel"), (2, 2, "CXOps")):
            self.db.add(Brand(id=brand_id, name=name, normalized_name=name.lower()))
            self.db.add(ProjectBrand(project_id=project_id, brand_id=brand_id, role="target"))
            self.db.add(Website(id=brand_id, brand_id=brand_id, domain=f"{name.lower()}.example", base_url=f"https://{name.lower()}.example", is_primary=True))
            self.db.add(Prompt(id=brand_id, project_id=project_id, text=f"What is {name}?", category="brand", is_active=True))
        self.db.add(TechnicalAudit(id=1, website_id=1, score=82, pages_checked=10, issue_count=2))
        self.db.add(MonitoringSchedule(project_id=1, mode="technical_seo", enabled=True, cadence_hours=168,
                                       next_due_at=self.now + timedelta(days=4), last_result={}))
        self.db.add(ProjectPriority(project_id=2, stable_key="site-rag:followup", title="Improve comparison evidence",
            priority="high", priority_score=80, impact="high", effort="medium", confidence="high", status="rechecked_unchanged",
            observed_evidence=[], interpretation="Follow-up remains", recommended_action="Improve first-party evidence",
            affected_prompts=[], affected_pages=[], affected_entities=[], source_modes=["site_rag"], score_components={},
            provenance={}, evidence_fingerprint="x", is_resolved=False))
        self._job(1, 1, 1, "web_search", 70)
        self._job(2, 2, 1, "web_search", 80)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _job(self, job_id, experiment_id, project_id, mode, minutes):
        self.db.add(GeoExperiment(id=experiment_id, project_id=project_id, name=f"Experiment {experiment_id}", phase="baseline",
                                  status="completed", completed_at=self.now + timedelta(minutes=minutes)))
        self.db.add(BenchmarkJob(id=job_id, experiment_id=experiment_id, project_id=project_id, model_id=1,
            benchmark_mode=mode, config_snapshot={"provider_model_id": "model-v1", "web_search_enabled": True},
            status="completed", total_prompts=1, completed_runs=1, failed_runs=0,
            completed_at=self.now + timedelta(minutes=minutes)))
        self.db.add(BenchmarkJobItem(benchmark_job_id=job_id, prompt_id=1,
                                     prompt_text_snapshot="What is Vercel?", status="completed"))

    def test_portfolio_separates_setup_attention_and_stable_monitoring(self):
        def metrics(_db, _project_id, experiment_id, persist_snapshot=False):
            self.assertFalse(persist_snapshot)
            return {"web_visibility_score_v1": {1: 70.0, 2: 80.0}[experiment_id]}

        inbox_event = {"project_id": 2, "origin": "backfill", "default_visible": True, "status": "unread",
                       "attention_rank": 2, "severity": "medium", "title": "Recheck unchanged",
                       "summary": "The compatible recheck still needs follow-up.", "source_mode": "site_rag",
                       "occurred_at": self.now, "evidence_path": "/projects/2/priorities"}
        with patch("app.services.agency_portfolio_service.AgencyInboxService.list_events", return_value=[inbox_event]), \
             patch("app.services.agency_portfolio_service.VisibilityMetricsService.calculate", side_effect=metrics):
            result = AgencyPortfolioService.build(self.db)

        by_id = {item["project_id"]: item for item in result["clients"]}
        self.assertEqual(by_id[1]["status"], "monitoring")
        self.assertEqual(by_id[1]["web_search"]["trend"]["state"], "improved")
        self.assertEqual(by_id[2]["status"], "needs_attention")
        self.assertEqual(by_id[2]["priorities"], {"open": 1, "high": 1})
        self.assertEqual(by_id[2]["last_meaningful_change"]["title"], "Recheck unchanged")
        self.assertEqual(by_id[3]["status"], "setup_required")
        self.assertIsNone(by_id[3]["technical_seo"]["score"])
        self.assertIsNone(by_id[3]["web_search"]["value"])
        self.assertEqual([item["project_id"] for item in result["clients"]], [2, 3, 1])

    def test_trend_requires_same_model_and_exact_frozen_prompt_snapshot(self):
        older = self.db.get(BenchmarkJob, 1)
        older.model_id = 2
        self.db.commit()
        with patch("app.services.agency_portfolio_service.AgencyInboxService.list_events", return_value=[]), \
             patch("app.services.agency_portfolio_service.VisibilityMetricsService.calculate", return_value={"web_visibility_score_v1": 80.0}) as metrics:
            result = AgencyPortfolioService.build(self.db)
        vercel = next(item for item in result["clients"] if item["project_id"] == 1)
        self.assertIsNone(vercel["web_search"]["trend"])
        self.assertEqual(metrics.call_count, 1)

    def test_build_is_read_only(self):
        with patch("app.services.agency_portfolio_service.AgencyInboxService.list_events", return_value=[]), \
             patch("app.services.agency_portfolio_service.VisibilityMetricsService.calculate", return_value={"web_visibility_score_v1": 80.0}), \
             patch.object(self.db, "commit") as commit, patch.object(self.db, "add") as add, patch.object(self.db, "flush") as flush:
            self.db.autoflush = False
            AgencyPortfolioService.build(self.db)
            commit.assert_not_called()
            add.assert_not_called()
            flush.assert_not_called()


if __name__ == "__main__":
    unittest.main()
