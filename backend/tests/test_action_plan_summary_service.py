import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.services.action_plan_summary_service import (
    ActionPlanSummaryService,
)


class ActionPlanSummaryServiceTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.project_id = 4
        self.project = SimpleNamespace(id=self.project_id)
        self.site_rag = {
            "experiment_id": 10,
            "total_actions": 1,
            "actions": [
                {
                    "title": (
                        "Create a factual comparison "
                        "and evaluation resource"
                    ),
                    "priority": "high",
                }
            ],
        }

    @patch(
        "app.services.action_plan_summary_service."
        "GeoActionPlanRepository.latest_by_project"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "SiteRAGActionBridgeService.build"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "ProjectRepository.get_by_id"
    )
    def test_no_historical_plan_keeps_current_site_rag_actions(
        self,
        get_project,
        build_site_rag,
        latest_plan,
    ):
        get_project.return_value = self.project
        build_site_rag.return_value = self.site_rag
        latest_plan.return_value = None

        result = ActionPlanSummaryService.build(
            db=self.db,
            project_id=self.project_id,
        )

        expected_values = {
            "project_id": self.project_id,
            "has_historical_plan": False,
            "plan_id": None,
            "experiment_id": None,
            "benchmark_mode": None,
            "target_brand_id": None,
            "target_brand": None,
            "plan_status": None,
            "created_at": None,
            "strategy_summary": None,
            "baseline_metrics": {},
            "recommended_sequence": [],
            "risks_and_limits": [],
            "total_actions": 0,
            "open_actions": 0,
            "completed_actions": 0,
            "high_priority_actions": 0,
            "medium_priority_actions": 0,
            "low_priority_actions": 0,
            "action_type_counts": {},
            "provenance_note": None,
            "actions": [],
        }
        for key, expected in expected_values.items():
            self.assertEqual(result[key], expected)

        self.assertIs(result["site_rag"], self.site_rag)
        build_site_rag.assert_called_once_with(
            db=self.db,
            project_id=self.project_id,
        )
        latest_plan.assert_called_once_with(
            self.db,
            self.project_id,
        )
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.flush.assert_not_called()

    @patch(
        "app.services.action_plan_summary_service."
        "GeoActionPlanRepository.latest_by_project"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "SiteRAGActionBridgeService.build"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "ProjectRepository.get_by_id"
    )
    def test_missing_project_stops_before_summary_dependencies(
        self,
        get_project,
        build_site_rag,
        latest_plan,
    ):
        get_project.return_value = None

        with self.assertRaises(HTTPException) as context:
            ActionPlanSummaryService.build(
                db=self.db,
                project_id=self.project_id,
            )

        self.assertEqual(context.exception.status_code, 404)
        self.assertEqual(
            context.exception.detail,
            "Project not found.",
        )
        build_site_rag.assert_not_called()
        latest_plan.assert_not_called()

    @patch(
        "app.services.action_plan_summary_service."
        "GeoActionPlanRepository.list_items"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "GeoExperimentRepository.get"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "GeoActionPlanRepository.latest_by_project"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "SiteRAGActionBridgeService.build"
    )
    @patch(
        "app.services.action_plan_summary_service."
        "ProjectRepository.get_by_id"
    )
    def test_historical_plan_and_current_site_rag_are_both_returned(
        self,
        get_project,
        build_site_rag,
        latest_plan,
        get_experiment,
        list_items,
    ):
        created_at = datetime.now(timezone.utc)
        plan = SimpleNamespace(
            id=7,
            experiment_id=8,
            target_brand_id=27,
            status="completed",
            created_at=created_at,
            strategy_summary="Historical strategy",
            baseline_metrics={"visibility_rate": 25.0},
            recommended_sequence=["Update evidence"],
            risks_and_limits=["Historical snapshot"],
        )
        experiment = SimpleNamespace(
            id=8,
            name="Historical baseline",
            phase="baseline",
            status="completed",
        )
        action = SimpleNamespace(
            id=11,
            sort_order=1,
            priority="high",
            action_type="content",
            title="Improve historical evidence",
            rationale="Historical evidence was incomplete.",
            target_page="/platform",
            impacted_prompt_ids=[52],
            impacted_opportunity_ids=[3],
            implementation_steps=["Add verified evidence"],
            evidence=["Baseline finding"],
            success_metrics=["Improved answerability"],
            dependencies=["Verified product documentation"],
            effort="medium",
            status="open",
        )

        get_project.return_value = self.project
        build_site_rag.return_value = self.site_rag
        latest_plan.return_value = plan
        get_experiment.return_value = experiment
        list_items.return_value = [action]
        self.db.get.return_value = SimpleNamespace(
            id=27,
            name="CxOps-Ai",
        )
        self.db.scalars.return_value.all.return_value = [
            "web_search"
        ]

        result = ActionPlanSummaryService.build(
            db=self.db,
            project_id=self.project_id,
        )

        self.assertTrue(result["has_historical_plan"])
        self.assertEqual(result["plan_id"], 7)
        self.assertEqual(result["experiment_id"], 8)
        self.assertEqual(
            result["experiment_name"],
            "Historical baseline",
        )
        self.assertEqual(result["experiment_phase"], "baseline")
        self.assertEqual(result["experiment_status"], "completed")
        self.assertEqual(result["benchmark_mode"], "web_search")
        self.assertEqual(result["target_brand_id"], 27)
        self.assertEqual(result["target_brand"], "CxOps-Ai")
        self.assertEqual(result["total_actions"], 1)
        self.assertEqual(result["high_priority_actions"], 1)
        self.assertEqual(result["open_actions"], 1)
        self.assertEqual(result["actions"][0]["id"], 11)
        self.assertEqual(
            result["actions"][0]["title"],
            "Improve historical evidence",
        )
        self.assertIs(result["site_rag"], self.site_rag)
        build_site_rag.assert_called_once_with(
            db=self.db,
            project_id=self.project_id,
        )
        latest_plan.assert_called_once_with(
            self.db,
            self.project_id,
        )
        get_experiment.assert_called_once_with(self.db, 8)
        list_items.assert_called_once_with(self.db, 7)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.flush.assert_not_called()


if __name__ == "__main__":
    unittest.main()
