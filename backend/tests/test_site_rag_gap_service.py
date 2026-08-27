import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.services.site_rag_gap_service import SiteRAGGapService


class SiteRAGGapServiceTests(unittest.TestCase):
    @patch.object(SiteRAGGapService, "summary")
    @patch.object(SiteRAGGapService, "_context")
    @patch(
        "app.services.site_rag_gap_service."
        "SiteRAGMetricsService.is_unsupported_answer"
    )
    @patch(
        "app.services.site_rag_gap_service."
        "SiteRAGGapAnalysisRepository.record_completed"
    )
    @patch(
        "app.services.site_rag_gap_service."
        "SiteRAGGapRepository.create"
    )
    @patch(
        "app.services.site_rag_gap_service."
        "SiteRAGGapRepository.clear_experiment"
    )
    def test_zero_gap_refresh_records_completed_analysis(
        self,
        clear_gaps,
        create_gap,
        record_analysis,
        is_unsupported,
        context,
        summary,
    ):
        db = Mock()
        experiment = SimpleNamespace(id=13, project_id=4)
        target = SimpleNamespace(id=27)
        row = SimpleNamespace(
            run_id=101,
            prompt_id=56,
            response_id=201,
            response_text="Grounded answer [Source 1]",
        )
        prompt = SimpleNamespace(
            id=56,
            text="A fully supported prompt",
            category="comparison",
            intent="commercial",
        )
        context.return_value = (experiment, target, [row])
        db.scalars.return_value.all.return_value = [prompt]
        db.execute.return_value.all.return_value = []
        is_unsupported.return_value = False
        summary.return_value = {"gap_prompts": 0}

        result = SiteRAGGapService.refresh(
            db=db,
            experiment_id=13,
        )

        clear_gaps.assert_called_once_with(db, 13)
        create_gap.assert_not_called()
        record_analysis.assert_called_once()
        arguments = record_analysis.call_args.kwargs
        self.assertEqual(arguments["experiment_id"], 13)
        self.assertEqual(arguments["project_id"], 4)
        self.assertEqual(arguments["target_brand_id"], 27)
        self.assertEqual(arguments["total_prompts"], 1)
        self.assertEqual(arguments["gap_count"], 0)
        self.assertEqual(
            arguments["gap_version"],
            SiteRAGGapService.GAP_VERSION,
        )
        db.commit.assert_called_once_with()
        summary.assert_called_once_with(db, 13)
        self.assertEqual(result, {"gap_prompts": 0})


if __name__ == "__main__":
    unittest.main()
