"""Tests for pure_discovery.py."""

import csv
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pure_discovery


class TestPureDiscovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.api_key_patcher = patch.object(pure_discovery, "PURE_API_KEY", "test-api-key-12345")
        self.base_url_patcher = patch.object(
            pure_discovery, "BASE_API_URL", "https://test.elsevierpure.com/ws/api"
        )
        self.page_size_patcher = patch.object(pure_discovery, "DISCOVERY_PAGE_SIZE", 5)
        self.max_results_patcher = patch.object(
            pure_discovery, "DISCOVERY_MAX_RESULTS_PER_KEYWORD", 10
        )

        self.api_key_patcher.start()
        self.base_url_patcher.start()
        self.page_size_patcher.start()
        self.max_results_patcher.start()

    def tearDown(self):
        self.api_key_patcher.stop()
        self.base_url_patcher.stop()
        self.page_size_patcher.stop()
        self.max_results_patcher.stop()
        shutil.rmtree(self.temp_dir)

    def sample_output(self, title="Research output report", abstract="Genetics and remote sensing trials"):
        return {
            "uuid": "uuid-123",
            "pureId": "98765",
            "title": {"value": title},
            "abstract": {"value": abstract},
            "type": {"term": {"text": "Report"}},
            "publicationYear": {"value": "2024"},
            "electronicVersions": [
                {
                    "file": {
                        "fileId": 1001,
                        "fileName": "forest-report.pdf",
                        "mimeType": "application/pdf",
                        "size": 2048,
                    },
                    "accessType": {"value": "Open"},
                }
            ],
        }


class TestHelpers(TestPureDiscovery):
    def test_flatten_keyword_themes_deduplicates(self):
        themes = {
            "a": ["Forest", "cypress"],
            "b": ["forest", "silviculture"],
        }
        result = pure_discovery.flatten_keyword_themes(themes)
        self.assertEqual(result, ["forest", "cypress", "silviculture"])

    def test_build_candidate_record_classifies_downloadable_pdf(self):
        candidate = pure_discovery.build_candidate_record(
            self.sample_output(),
            matched_terms={"forest", "genetics"},
            matched_fields={"title", "abstract"},
            source_queries={"forest", "genetics"},
        )
        self.assertEqual(candidate["download_status"], "downloadable_pdf")
        self.assertEqual(candidate["pdf_count"], 1)
        self.assertEqual(candidate["open_pdf_count"], 1)
        self.assertIn("forest", candidate["matched_terms"])

    def test_build_candidate_record_classifies_non_pdf_only(self):
        output = self.sample_output()
        output["electronicVersions"] = [
            {
                "file": {
                    "fileId": 1002,
                    "fileName": "forest-data.xlsx",
                    "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "size": 1024,
                },
                "accessType": {"value": "Open"},
            }
        ]
        candidate = pure_discovery.build_candidate_record(
            output,
            matched_terms={"forest"},
            matched_fields={"title"},
            source_queries={"forest"},
        )
        self.assertEqual(candidate["download_status"], "has_non_pdf_only")
        self.assertEqual(candidate["pdf_count"], 0)

    def test_build_candidate_record_classifies_restricted_pdf(self):
        output = self.sample_output()
        output["electronicVersions"][0]["accessType"] = {"value": "Campus"}
        candidate = pure_discovery.build_candidate_record(
            output,
            matched_terms={"forest"},
            matched_fields={"title"},
            source_queries={"forest"},
        )
        self.assertEqual(candidate["download_status"], "restricted_or_unknown_access")


class TestDiscoveryWorkflow(TestPureDiscovery):
    @patch("pure_discovery.fetch_research_output_detail")
    @patch("pure_discovery.search_research_outputs_page")
    @patch("pure_discovery.check_api_key")
    def test_discover_candidates_deduplicates_and_merges_matches(self, mock_check_api_key, mock_search_page, mock_detail):
        forest_item = {
            "uuid": "uuid-123",
            "title": {"value": "Research output report"},
            "abstract": {"value": "Genetics and remote sensing trials"},
        }
        cypress_item = {
            "uuid": "uuid-123",
            "title": {"value": "Research output report"},
            "abstract": {"value": "Genetics and remote sensing trials"},
        }
        mock_search_page.side_effect = [
            {"count": 1, "items": [forest_item]},
            {"count": 1, "items": [cypress_item]},
        ]
        mock_detail.return_value = self.sample_output()
        mock_check_api_key.return_value = True

        with patch("pure_discovery.log_debug"):
            candidates = pure_discovery.discover_candidates(
                keyword_themes={"theme": ["genetics", "remote sensing"]},
                http_client=Mock(),
            )

        self.assertEqual(len(candidates), 1)
        self.assertIn("genetics", candidates[0]["matched_terms"])
        self.assertIn("remote sensing", candidates[0]["matched_terms"])
        self.assertEqual(candidates[0]["download_status"], "downloadable_pdf")
        mock_check_api_key.assert_called_once_with(pure_discovery.PURE_API_KEY, verbose=False)

    @patch("pure_discovery.fetch_research_output_detail")
    @patch("pure_discovery.search_research_outputs_page")
    def test_discover_candidates_logs_progress(self, mock_search_page, mock_detail):
        mock_search_page.side_effect = [
            {
                "count": 2,
                "items": [
                    {
                        "uuid": "uuid-123",
                        "title": {"value": "Research output report"},
                        "abstract": {"value": "Genetics and remote sensing trials"},
                    },
                    {
                        "uuid": "uuid-456",
                        "title": {"value": "Research health update"},
                        "abstract": {"value": "Remote sensing and disease overview"},
                    },
                ],
            }
        ]
        mock_detail.side_effect = [self.sample_output(), self.sample_output(title="Research health update")]

        with patch("pure_discovery.check_api_key", return_value=True), patch(
            "pure_discovery.log_debug"
        ) as mock_log_debug:
            pure_discovery.discover_candidates(
                keyword_themes={"theme": ["remote sensing"]},
                http_client=Mock(),
            )

        messages = [call.args[0] for call in mock_log_debug.call_args_list]
        self.assertTrue(any("Discovery search plan" in message for message in messages))
        self.assertTrue(any("[1/1] Searching discovery candidates" in message for message in messages))
        self.assertTrue(any("Page 1: fetched 2 items" in message for message in messages))
        self.assertTrue(any("Enrichment progress: 2/2" in message for message in messages))

    def test_write_candidates_csv_and_export_approved(self):
        candidates = [
            pure_discovery.build_candidate_record(
                self.sample_output(),
                matched_terms={"forest"},
                matched_fields={"title"},
                source_queries={"forest"},
            )
        ]
        csv_path = os.path.join(self.temp_dir, "candidates.csv")
        approved_path = os.path.join(self.temp_dir, "approved.csv")

        pure_discovery.write_candidates_csv(candidates, output_path=csv_path)
        self.assertTrue(os.path.exists(csv_path))

        with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["download_status"], "downloadable_pdf")

        rows[0][pure_discovery.REVIEW_DECISION_COLUMN] = "approve"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        pure_discovery.export_approved_candidates(csv_path, approved_path)
        with open(approved_path, "r", encoding="utf-8-sig", newline="") as handle:
            approved_rows = list(csv.DictReader(handle))
        self.assertEqual(len(approved_rows), 1)
        self.assertEqual(approved_rows[0][pure_discovery.REVIEW_DECISION_COLUMN], "approve")

    def test_generate_summary_report(self):
        candidates = [
            pure_discovery.build_candidate_record(
                self.sample_output(),
                matched_terms={"forest", "cypress"},
                matched_fields={"title", "abstract"},
                source_queries={"forest", "cypress"},
            )
        ]
        report_path = os.path.join(self.temp_dir, "summary.md")
        pure_discovery.generate_summary_report(candidates, report_path)

        self.assertTrue(os.path.exists(report_path))
        with open(report_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("Research Output Discovery Summary", content)
        self.assertIn("downloadable_pdf", content)
        self.assertIn("forest", content)

    @patch("pure_discovery.test_api_connection")
    @patch("pure_discovery.generate_summary_report")
    @patch("pure_discovery.write_candidates_csv")
    @patch("pure_discovery.discover_candidates")
    def test_run_discovery_workflow(self, mock_discover, mock_write_csv, mock_summary, mock_connection):
        candidate = pure_discovery.build_candidate_record(
            self.sample_output(),
            matched_terms={"forest"},
            matched_fields={"title"},
            source_queries={"forest"},
        )
        mock_connection.return_value = True
        mock_discover.return_value = [candidate]
        mock_write_csv.return_value = "candidates.csv"
        mock_summary.return_value = "summary.md"

        result = pure_discovery.run_discovery_workflow(
            output_csv_path="candidates.csv",
            summary_report_path="summary.md",
            http_client=Mock(),
        )

        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["downloadable_pdf_count"], 1)
        self.assertEqual(result["output_csv_path"], "candidates.csv")


if __name__ == "__main__":
    unittest.main(verbosity=2)
