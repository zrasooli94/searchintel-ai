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
    @patch("app.services.project_priority_service.TechnicalSEOSummaryService.build")
    def test_technical_findings_consolidate_without_persisted_recommendations(self, build):
        build.return_value = {
            "audit": {"id": 7}, "recommendations": [], "pages": [],
            "issues": [
                {"id": 1, "code": "MISSING_TITLE", "page_url": "https://example.com/a", "message": "Missing title"},
                {"id": 2, "code": "MISSING_TITLE", "page_url": "https://example.com/b", "message": "Missing title"},
            ],
        }
        items = ProjectPriorityService._technical_candidates(MagicMock(), 8)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Add a descriptive title")
        self.assertEqual(len(items[0]["affected_pages"]), 2)

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

    def test_new_compatible_site_rag_analysis_classifies_fewer_gaps_as_improved(self):
        record = ProjectPriority(
            project_id=4,
            stable_key="evidence:comparison",
            status="ready_to_recheck",
            provenance={
                "site_rag_experiment_id": 10,
                "site_rag_gap_ids": [6, 7],
            },
        )
        latest = MagicMock(
            id=9,
            experiment_id=21,
            total_prompts=20,
        )
        result = ProjectPriorityService._site_rag_recheck(
            record,
            {
                "provenance": {
                    "site_rag_experiment_id": 21,
                    "site_rag_gap_ids": [30],
                }
            },
            latest,
        )
        self.assertEqual(record.status, "rechecked_improved")
        self.assertEqual(result["baseline"]["gap_count"], 2)
        self.assertEqual(result["recheck"]["gap_count"], 1)

    def test_new_zero_gap_analysis_resolves_ready_priority_as_improved(self):
        record = ProjectPriority(
            project_id=4,
            stable_key="evidence:comparison",
            status="ready_to_recheck",
            provenance={
                "site_rag_experiment_id": 10,
                "site_rag_gap_ids": [6, 7],
            },
        )
        result = ProjectPriorityService._site_rag_recheck(
            record,
            None,
            MagicMock(id=10, experiment_id=22, total_prompts=20),
        )
        self.assertEqual(record.status, "rechecked_improved")
        self.assertEqual(result["recheck"]["gap_count"], 0)

    def test_same_site_rag_analysis_does_not_classify_recheck(self):
        record = ProjectPriority(
            project_id=4,
            stable_key="evidence:comparison",
            status="ready_to_recheck",
            provenance={
                "site_rag_experiment_id": 10,
                "site_rag_gap_ids": [6, 7],
            },
        )
        result = ProjectPriorityService._site_rag_recheck(
            record,
            None,
            MagicMock(id=8, experiment_id=10, total_prompts=20),
        )
        self.assertIsNone(result)
        self.assertEqual(record.status, "ready_to_recheck")

    @patch("app.services.project_priority_service.ProjectPriorityRepository.list_by_project", return_value=[])
    @patch("app.services.project_priority_service.ProjectRepository.get_by_id", return_value=object())
    def test_summary_get_is_read_only(self, _project, _list):
        db = MagicMock()
        result = ProjectPriorityService.summary(db, 8)
        self.assertEqual(result["priorities"], [])
        db.commit.assert_not_called()
        db.add.assert_not_called()

    @patch("app.services.project_priority_service.ProjectPriorityService.refresh")
    @patch("app.services.project_priority_service.ProjectPriorityService.build_candidates")
    @patch("app.services.project_priority_service.ProjectPriorityRepository.list_by_project")
    @patch("app.services.project_priority_service.ProjectRepository.list_all")
    def test_startup_backfill_only_populates_projects_without_priority_history(
        self, list_projects, list_priorities, build, refresh
    ):
        list_projects.return_value = [MagicMock(id=1), MagicMock(id=8)]
        current = MagicMock(provenance={"generator_version": ProjectPriorityService.GENERATOR_VERSION})
        list_priorities.side_effect = [[current], []]
        build.return_value = [candidate("web_search", "Production troubleshooting")]
        result = ProjectPriorityService.backfill_missing(MagicMock())
        self.assertEqual(result, [8])
        refresh.assert_called_once()
        self.assertEqual(refresh.call_args.args[1], 8)


if __name__ == "__main__":
    unittest.main()
