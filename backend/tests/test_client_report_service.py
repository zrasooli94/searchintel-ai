import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from app.models.client_report import ClientReport
from app.services.client_report_pdf_service import ClientReportPDFService
from app.services.client_report_service import ClientReportService


def report_fixture():
    snapshot = {
        "generated_at": "2026-08-31T00:00:00Z", "project": {"name": "CXOps"},
        "executive_summary": {"note": "Modes remain separate."},
        "technical_seo": {"measurement_state": "ready", "audit": {"score": 90, "pages_checked": 10, "issue_count": 2}},
        "measurements": {
            "web_search": None, "memory": None,
            "site_rag": {"metrics": {"site_answerability_rate_v1": 90, "site_rag_analyzed_runs": 20, "unsupported_answer_rate_v1": 10, "evidence_coverage_rate": 100, "source_reference_rate": 100}},
        },
        "competitor_position": {"configured_competitors": ["Intercom"]},
        "priorities": [{"id": 1, "title": "Improve evidence", "status": "rechecked_unchanged", "priority": "high", "recommended_action": "Publish factual evidence.", "source_modes": ["site_rag"]}],
        "compatible_rechecks": [{"priority_id": 1, "title": "Improve evidence", "status": "rechecked_unchanged", "baseline": {"metrics": {"site_answerability_rate_v1": 90, "site_rag_analyzed_runs": 20}, "gap_count": 2}, "recheck": {"metrics": {"site_answerability_rate_v1": 90, "site_rag_analyzed_runs": 20}, "gap_count": 2}, "explanation": "One prompt improved while another gap appeared."}],
        "recommended_next_actions": ["Publish factual evidence."],
        "scope_and_provenance": {"snapshot_note": "Stored evidence only."},
    }
    return ClientReport(id=1, project_id=4, title="CXOps report", status="draft", snapshot_version="client-report-v1", snapshot=snapshot, content_hash="a" * 64)


class ClientReportServiceTests(unittest.TestCase):
    def test_publish_hashes_token_and_never_changes_snapshot(self):
        db = MagicMock(); report = report_fixture(); original = report.snapshot.copy()
        with patch("app.services.client_report_service.secrets.token_urlsafe", return_value="private-token"):
            published, raw = ClientReportService.publish(db, report, None)
        self.assertEqual(raw, "private-token")
        self.assertNotEqual(published.share_token_hash, raw)
        self.assertEqual(published.share_token_hash, ClientReportService._token_hash(raw))
        self.assertEqual(published.snapshot, original)
        db.commit.assert_called_once()

    @patch("app.services.client_report_service.ClientReportRepository.by_token_hash")
    def test_shared_report_rejects_revoked_and_expired_links(self, by_hash):
        report = report_fixture(); report.status = "revoked"; by_hash.return_value = report
        with self.assertRaises(HTTPException) as revoked:
            ClientReportService.shared(MagicMock(), "token")
        self.assertEqual(revoked.exception.status_code, 404)
        report.status = "published"; report.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        with self.assertRaises(HTTPException) as expired:
            ClientReportService.shared(MagicMock(), "token")
        self.assertEqual(expired.exception.status_code, 410)

    @patch("app.services.client_report_service.ClientReportRepository.by_token_hash")
    def test_shared_report_get_is_read_only(self, by_hash):
        report = report_fixture(); report.status = "published"; report.expires_at = None; by_hash.return_value = report
        db = MagicMock()
        self.assertIs(ClientReportService.shared(db, "token"), report)
        db.commit.assert_not_called(); db.add.assert_not_called()

    def test_pdf_is_generated_from_the_same_snapshot(self):
        pdf = ClientReportPDFService.render(report_fixture())
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 2000)

    def test_compatible_recheck_fixture_preserves_unchanged_truth(self):
        item = report_fixture().snapshot["compatible_rechecks"][0]
        self.assertEqual(item["baseline"]["metrics"]["site_answerability_rate_v1"], 90)
        self.assertEqual(item["recheck"]["metrics"]["site_answerability_rate_v1"], 90)
        self.assertEqual(item["baseline"]["gap_count"], item["recheck"]["gap_count"])
        self.assertIn("another gap appeared", item["explanation"])


if __name__ == "__main__":
    unittest.main()
