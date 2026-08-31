import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.services.monitoring_service import MonitoringService


class MonitoringServiceTests(unittest.TestCase):
    def schedule(self, **values):
        defaults = dict(id=1, project_id=8, mode="web_search", enabled=True, cadence_hours=168,
            next_due_at=datetime.now(timezone.utc) + timedelta(days=7), last_attempted_at=None,
            last_successful_at=None, last_result={}, source_benchmark_job_id=22, model_id=1,
            prompt_count=19, run_after_crawl=False, failure_message=None)
        defaults.update(values)
        return SimpleNamespace(**defaults)

    def test_paid_schedule_requires_explicit_confirmation(self):
        db = MagicMock()
        source = SimpleNamespace(id=22, project_id=8, status="completed", benchmark_mode="web_search", model_id=1, total_prompts=19)
        with patch("app.services.monitoring_service.ProjectRepository.get_by_id", return_value=object()), patch("app.services.monitoring_service.BenchmarkRepository.get_job", return_value=source):
            with self.assertRaises(HTTPException) as raised:
                MonitoringService.configure(db, 8, "web_search", {"enabled": True, "source_benchmark_job_id": 22})
        self.assertEqual(raised.exception.status_code, 422)

    def test_cost_preview_is_deterministic(self):
        result = MonitoringService._serialize_schedule(self.schedule(cadence_hours=168, prompt_count=19))
        self.assertEqual(result["estimated_monthly_runs"], 81)
        self.assertEqual(result["state"], "scheduled")

    def test_overdue_and_failure_states_are_persisted_not_timer_derived(self):
        result = MonitoringService._serialize_schedule(self.schedule(next_due_at=datetime.now(timezone.utc) - timedelta(hours=1)))
        self.assertTrue(result["overdue"])
        self.assertEqual(result["state"], "overdue")
        failed = MonitoringService._serialize_schedule(self.schedule(failure_message="provider unavailable"))
        self.assertEqual(failed["state"], "failed")

    def test_equivalent_running_schedule_is_not_duplicated(self):
        db = MagicMock()
        schedule = self.schedule(mode="technical_seo")
        active = SimpleNamespace(id=7, schedule_id=1, project_id=8, mode="technical_seo", status="running",
            benchmark_job_id=None, technical_audit_id=None, change_classification=None, change_evidence={},
            error_message=None, started_at=datetime.now(timezone.utc), completed_at=None)
        db.scalar.side_effect = [schedule, active]
        result = MonitoringService.execute(db, 1)
        self.assertEqual(result["id"], 7)
        db.add.assert_not_called()

    def test_change_detection_never_compares_modes_and_preserves_direction(self):
        self.assertEqual(MonitoringService._classification({"issue_count": 6}, {"issue_count": 3}, True), "improved")
        self.assertEqual(MonitoringService._classification({"completed_runs": 18}, {"completed_runs": 17}), "declined")
        self.assertEqual(MonitoringService._classification({"completed_runs": 18}, {"completed_runs": 18}), "stable")
        self.assertEqual(MonitoringService._benchmark_classification({"gap_count": 2, "answerability_rate": 90}, {"gap_count": 0, "answerability_rate": 100}), "resolved_issue")
        self.assertEqual(MonitoringService._benchmark_classification({"gap_count": 0, "answerability_rate": 100}, {"gap_count": 1, "answerability_rate": 95}), "new_issue")
        self.assertEqual(MonitoringService._technical_classification({"issue_count": 6, "score": 80}, {"issue_count": 6, "score": 85}), "improved")
        self.assertEqual(MonitoringService._technical_classification({"issue_count": 2, "score": 90}, {"issue_count": 0, "score": 100}), "resolved_issue")


if __name__ == "__main__":
    unittest.main()
