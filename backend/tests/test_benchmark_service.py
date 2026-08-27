import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from app.services.benchmark_service import BenchmarkService


class BenchmarkServicePromptSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.project = SimpleNamespace(id=4)

    @staticmethod
    def make_job(**overrides):
        values = {
            "id": 99,
            "project_id": 4,
            "model_id": 2,
            "experiment_id": 10,
            "benchmark_mode": "site_rag",
            "config_snapshot": {},
            "status": "pending",
            "total_prompts": 2,
            "completed_runs": 0,
            "failed_runs": 0,
            "started_at": None,
            "completed_at": None,
            "error_message": None,
            "created_at": datetime.now(timezone.utc),
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    @patch(
        "app.services.benchmark_service."
        "AIModelService.resolve_execution_model"
    )
    @patch(
        "app.services.benchmark_service."
        "BenchmarkRepository.create_items"
    )
    @patch(
        "app.services.benchmark_service."
        "BenchmarkRepository.create_job"
    )
    @patch(
        "app.services.benchmark_service."
        "BenchmarkRepository.list_items"
    )
    @patch(
        "app.services.benchmark_service."
        "BenchmarkRepository.get_job"
    )
    @patch(
        "app.services.benchmark_service."
        "ProjectRepository.get_by_id"
    )
    def test_cross_mode_prompt_source_copies_frozen_snapshots_exactly(
        self,
        get_project,
        get_job,
        list_items,
        create_job,
        create_items,
        resolve_model,
    ):
        get_project.return_value = self.project
        get_job.return_value = SimpleNamespace(
            id=4,
            project_id=4,
            model_id=1,
            experiment_id=4,
            benchmark_mode="web_search",
            status="completed",
        )
        list_items.return_value = [
            SimpleNamespace(
                prompt_id=52,
                prompt_text_snapshot="Frozen prompt one",
            ),
            SimpleNamespace(
                prompt_id=53,
                prompt_text_snapshot="Frozen prompt two",
            ),
        ]
        resolve_model.return_value = SimpleNamespace(
            id=2,
            provider_model_id="gpt-test",
        )
        created_job = self.make_job()
        create_job.return_value = created_job

        result = BenchmarkService.create(
            db=self.db,
            project_id=4,
            model_id=2,
            experiment_id=None,
            benchmark_mode="site_rag",
            prompt_source_benchmark_job_id=4,
        )

        expected_snapshots = [
            {
                "prompt_id": 52,
                "prompt_text_snapshot": "Frozen prompt one",
            },
            {
                "prompt_id": 53,
                "prompt_text_snapshot": "Frozen prompt two",
            },
        ]
        create_items.assert_called_once_with(
            db=self.db,
            benchmark_job_id=99,
            prompt_snapshots=expected_snapshots,
        )
        create_job.assert_called_once()
        job_arguments = create_job.call_args.kwargs
        self.assertEqual(job_arguments["benchmark_mode"], "site_rag")
        self.assertEqual(job_arguments["model_id"], 2)
        self.assertEqual(
            job_arguments["config_snapshot"]["benchmark_mode"],
            "site_rag",
        )
        self.assertTrue(
            job_arguments["config_snapshot"]["site_rag_enabled"]
        )
        self.assertFalse(
            job_arguments["config_snapshot"]["web_search_enabled"]
        )
        self.assertEqual(
            job_arguments["config_snapshot"]["prompt_source"],
            "benchmark_snapshot_cross_mode",
        )
        self.assertEqual(
            job_arguments["config_snapshot"][
                "prompt_source_benchmark_job_id"
            ],
            4,
        )
        resolve_model.assert_called_once_with(self.db, 2)
        self.db.commit.assert_called_once_with()
        self.db.refresh.assert_called_once_with(created_job)
        self.assertEqual(result["benchmark_mode"], "site_rag")

    @patch(
        "app.services.benchmark_service."
        "BenchmarkRepository.get_job"
    )
    @patch(
        "app.services.benchmark_service."
        "ProjectRepository.get_by_id"
    )
    def test_optimization_source_still_rejects_mode_mismatch(
        self,
        get_project,
        get_job,
    ):
        get_project.return_value = self.project
        get_job.return_value = SimpleNamespace(
            id=4,
            project_id=4,
            model_id=2,
            benchmark_mode="web_search",
            status="completed",
        )

        with self.assertRaises(HTTPException) as context:
            BenchmarkService.create(
                db=self.db,
                project_id=4,
                model_id=2,
                benchmark_mode="site_rag",
                source_benchmark_job_id=4,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.detail,
            "Optimization benchmark mode must match the source "
            "benchmark mode.",
        )
        self.db.commit.assert_not_called()

    @patch(
        "app.services.benchmark_service."
        "ProjectRepository.get_by_id"
    )
    def test_rejects_both_source_types(self, get_project):
        get_project.return_value = self.project

        with self.assertRaises(HTTPException) as context:
            BenchmarkService.create(
                db=self.db,
                project_id=4,
                model_id=2,
                benchmark_mode="site_rag",
                source_benchmark_job_id=4,
                prompt_source_benchmark_job_id=4,
            )

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(
            context.exception.detail,
            "Use either source_benchmark_job_id or "
            "prompt_source_benchmark_job_id, not both.",
        )
        self.db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
