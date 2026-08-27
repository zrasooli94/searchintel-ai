import unittest

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.analysis_versions import (
    VISIBILITY_ANALYSIS_VERSION,
)
from app.services.experiment_reanalysis_service import (
    ExperimentReanalysisService,
)


class ExperimentReanalysisServiceTests(unittest.TestCase):

    @patch.object(
        ExperimentReanalysisService,
        "response_versions",
    )
    @patch(
        "app.services.experiment_reanalysis_service."
        "VisibilityAnalysisService.analyze",
    )
    def test_force_rebuilds_current_analysis_after_config_change(
        self,
        analyze,
        response_versions,
    ):
        current_rows = [
            SimpleNamespace(
                run_id=101,
                visibility_analysis_version=
                    VISIBILITY_ANALYSIS_VERSION,
            ),
            SimpleNamespace(
                run_id=102,
                visibility_analysis_version=
                    VISIBILITY_ANALYSIS_VERSION,
            ),
        ]
        response_versions.side_effect = [
            current_rows,
            current_rows,
        ]
        db = Mock()
        db.get.return_value = SimpleNamespace(
            id=7,
            project_id=5,
        )

        result = ExperimentReanalysisService.reanalyze(
            db,
            project_id=5,
            experiment_id=7,
            force=True,
        )

        self.assertEqual(result["stale_before"], 0)
        self.assertEqual(result["skipped_current"], 0)
        self.assertEqual(result["reanalyzed"], 2)
        self.assertTrue(result["analysis_is_current"])
        self.assertEqual(
            [call.args[1] for call in analyze.call_args_list],
            [101, 102],
        )


if __name__ == "__main__":
    unittest.main()
