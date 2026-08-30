import unittest
from unittest.mock import MagicMock, patch

from app.models.project_priority import ProjectPriority
from app.services.project_priority_service import ProjectPriorityService


def candidate(mode, prompt, *, monitor=False):
    return {
        "stable_key": f"evidence:{mode}", "title": f"Improve {prompt}",
        "severity": 50, "impact": "medium", "effort": "medium", "confidence": "high",
        "monitor": monitor, "observed_evidence": [f"Stored {mode} evidence."],
        "interpretation": "Stored evidence identifies a gap.", "recommended_action": "Improve the evidence.",
        "affected_prompts": [prompt], "affected_pages": [], "affected_entities": [],
        "source_modes": [mode], "provenance": {f"{mode}_id": 1},
    }


class ProjectPriorityServiceTests(unittest.TestCase):
    def test_cross_mode_prompt_evidence_merges_into_one_priority(self):
        web = candidate("web_search", "How do I troubleshoot production deployments?")
        site = candidate("site_rag", "Production deployment troubleshooting guide")
        merged = ProjectPriorityService._merge([web, site])
        self.assertEqual(len(merged), 1)
        self.assertEqual(set(merged[0]["source_modes"]), {"web_search", "site_rag"})
        self.assertIn("same underlying", merged[0]["interpretation"])

    def test_unmeasured_web_item_is_monitor_not_failure(self):
        item = ProjectPriorityService._finalize(candidate("web_search", "A prompt", monitor=True))
        self.assertEqual(item["priority"], "monitor")
        self.assertEqual(item["priority_score"], 0)

    def test_cross_mode_corroboration_is_explainable_and_increases_score(self):
        single = ProjectPriorityService._finalize(candidate("web_search", "Production troubleshooting"))
        merged = ProjectPriorityService._merge([
            candidate("web_search", "Production troubleshooting"),
            candidate("site_rag", "Production troubleshooting documentation"),
        ])[0]
        combined = ProjectPriorityService._finalize(merged)
        self.assertGreater(combined["priority_score"], single["priority_score"])
        self.assertEqual(combined["score_components"]["cross_mode_corroboration"], 15)
        self.assertTrue(combined["score_components"]["effort_excluded_from_score"])

    @patch("app.services.project_priority_service.ProjectPriorityRepository.by_key")
    @patch("app.services.project_priority_service.ProjectPriorityService.build_candidates")
    @patch("app.services.project_priority_service.ProjectPriorityService.summary")
    def test_refresh_preserves_lifecycle_for_rediscovered_stable_key(self, summary, build, by_key):
        record = ProjectPriority(project_id=8, stable_key="evidence:production", status="in_progress")
        record.is_resolved = False
        by_key.return_value = {record.stable_key: record}
        build.return_value = [ProjectPriorityService._finalize(candidate("web_search", "Production")) | {"stable_key": record.stable_key}]
        summary.return_value = {"project_id": 8}
        db = MagicMock()
        ProjectPriorityService.refresh(db, 8)
        self.assertEqual(record.status, "in_progress")
        self.assertFalse(record.is_resolved)
        db.commit.assert_called_once()

    @patch("app.services.project_priority_service.ProjectPriorityRepository.list_by_project", return_value=[])
    @patch("app.services.project_priority_service.ProjectRepository.get_by_id", return_value=object())
    def test_summary_get_is_read_only(self, _project, _list):
        db = MagicMock()
        result = ProjectPriorityService.summary(db, 8)
        self.assertEqual(result["priorities"], [])
        db.commit.assert_not_called()
        db.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
