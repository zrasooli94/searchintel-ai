import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.site_rag_action_bridge_service import (
    SiteRAGActionBridgeService,
)


class SiteRAGActionBridgeServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.project_id = 4

    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGMetricsService.calculate"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGGapRepository.list_by_experiment"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "GeoExperimentRepository.get"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGGapAnalysisRepository.latest_completed_by_project"
    )
    def test_latest_analysis_with_gaps_builds_actions(
        self,
        latest_analysis,
        get_experiment,
        list_gaps,
        calculate_metrics,
    ):
        latest_analysis.return_value = SimpleNamespace(
            experiment_id=12,
            gap_count=1,
        )
        get_experiment.return_value = SimpleNamespace(
            id=12,
            name="Newest Site RAG analysis",
        )
        list_gaps.return_value = [
            SimpleNamespace(
                id=21,
                prompt_id=56,
                gap_type="competitive_evidence_gap",
                gap_score=100.0,
                priority="high",
            )
        ]
        calculate_metrics.return_value = {
            "site_rag_analyzed_prompts": 20,
            "site_answerability_rate_v1": 95.0,
            "unsupported_answer_rate_v1": 5.0,
            "evidence_coverage_rate": 100.0,
            "evidence_utilization_rate": 75.0,
        }

        result = SiteRAGActionBridgeService.build(
            db=self.db,
            project_id=self.project_id,
        )

        self.assertEqual(result["experiment_id"], 12)
        self.assertEqual(result["gap_prompts"], 1)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(
            result["actions"][0]["impacted_prompt_ids"],
            [56],
        )
        latest_analysis.assert_called_once_with(
            self.db,
            self.project_id,
        )
        list_gaps.assert_called_once_with(self.db, 12)

    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGMetricsService.calculate"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGGapRepository.list_by_experiment"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "GeoExperimentRepository.get"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGGapAnalysisRepository.latest_completed_by_project"
    )
    def test_latest_zero_gap_analysis_supersedes_older_gaps(
        self,
        latest_analysis,
        get_experiment,
        list_gaps,
        calculate_metrics,
    ):
        latest_analysis.return_value = SimpleNamespace(
            experiment_id=13,
            gap_count=0,
        )
        result = SiteRAGActionBridgeService.build(
            db=self.db,
            project_id=self.project_id,
        )

        self.assertIsNone(result)
        get_experiment.assert_not_called()
        list_gaps.assert_not_called()
        calculate_metrics.assert_not_called()

    @patch(
        "app.services.site_rag_action_bridge_service."
        "GeoExperimentRepository.get"
    )
    @patch(
        "app.services.site_rag_action_bridge_service."
        "SiteRAGGapAnalysisRepository.latest_completed_by_project"
    )
    def test_project_without_gap_analysis_has_no_bridge(
        self,
        latest_analysis,
        get_experiment,
    ):
        latest_analysis.return_value = None

        result = SiteRAGActionBridgeService.build(
            db=self.db,
            project_id=self.project_id,
        )

        self.assertIsNone(result)
        get_experiment.assert_not_called()


if __name__ == "__main__":
    unittest.main()
