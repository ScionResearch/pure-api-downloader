"""Tests for pure_approved_downloader.py."""

import csv
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pure_approved_downloader


class TestApprovedDownloader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "downloads")
        self.checkpoint_path = os.path.join(self.temp_dir, "checkpoint.json")
        self.approved_csv = os.path.join(self.temp_dir, "approved.csv")

        self.api_key_patcher = patch.object(
            pure_approved_downloader, "PURE_API_KEY", "test-api-key-12345"
        )
        self.base_url_patcher = patch.object(
            pure_approved_downloader, "BASE_API_URL", "https://test.elsevierpure.com/ws/api"
        )
        self.output_dir_patcher = patch.object(
            pure_approved_downloader, "APPROVED_DOWNLOAD_OUTPUT_DIR", self.output_dir
        )
        self.checkpoint_patcher = patch.object(
            pure_approved_downloader, "APPROVED_DOWNLOAD_CHECKPOINT_FILE", self.checkpoint_path
        )
        self.pilot_size_patcher = patch.object(
            pure_approved_downloader, "APPROVED_DOWNLOAD_PILOT_SIZE", 2
        )

        self.api_key_patcher.start()
        self.base_url_patcher.start()
        self.output_dir_patcher.start()
        self.checkpoint_patcher.start()
        self.pilot_size_patcher.start()

    def tearDown(self):
        self.api_key_patcher.stop()
        self.base_url_patcher.stop()
        self.output_dir_patcher.stop()
        self.checkpoint_patcher.stop()
        self.pilot_size_patcher.stop()
        shutil.rmtree(self.temp_dir)

    def approved_row(self, uuid="uuid-1", pure_id="123", title="Forest report"):
        return {
            "uuid": uuid,
            "pure_id": pure_id,
            "title": title,
            "download_status": "downloadable_pdf",
            "first_open_pdf_name": "forest-report.pdf",
            "first_open_pdf_url": f"https://test.elsevierpure.com/ws/api/research-outputs/{uuid}/files/999/forest-report.pdf",
            "reviewer_decision": "approve",
        }

    def write_approved_csv(self, rows):
        fieldnames = sorted({key for row in rows for key in row.keys()})
        with open(self.approved_csv, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)


class TestApprovedDownloaderHelpers(TestApprovedDownloader):
    def test_build_output_path(self):
        path = pure_approved_downloader.build_output_path(self.approved_row(), self.output_dir)
        self.assertTrue(path.endswith("Forest_report_123.pdf"))

    def test_load_and_save_checkpoint(self):
        checkpoint = {"completed": {"uuid-1": {"status": "completed"}}, "failed": {}, "skipped": {}}
        pure_approved_downloader.save_checkpoint(checkpoint, self.checkpoint_path)
        loaded = pure_approved_downloader.load_checkpoint(self.checkpoint_path)
        self.assertEqual(loaded["completed"]["uuid-1"]["status"], "completed")

    def test_load_approved_candidates(self):
        rows = [self.approved_row(), {**self.approved_row(uuid="uuid-2"), "reviewer_decision": "no"}]
        self.write_approved_csv(rows)
        candidates = pure_approved_downloader.load_approved_candidates(self.approved_csv)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["uuid"], "uuid-1")

    def test_load_approved_candidates_accepts_approve_auto(self):
        rows = [{**self.approved_row(), "reviewer_decision": "approve_auto"}]
        self.write_approved_csv(rows)
        candidates = pure_approved_downloader.load_approved_candidates(self.approved_csv)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["reviewer_decision"], "approve_auto")

    def test_create_proceed_candidates_from_review_csv_uses_downloadable_rows_when_no_explicit_approval(self):
        review_csv = os.path.join(self.temp_dir, "review.csv")
        rows = [
            {**self.approved_row(uuid="uuid-1"), "reviewer_decision": ""},
            {**self.approved_row(uuid="uuid-2"), "download_status": "has_non_pdf_only", "reviewer_decision": ""},
            {**self.approved_row(uuid="uuid-3"), "reviewer_decision": ""},
        ]
        fieldnames = sorted({key for row in rows for key in row.keys()})
        with open(review_csv, "w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        output_path = pure_approved_downloader.create_proceed_candidates_from_review_csv(
            review_csv, self.approved_csv
        )
        self.assertEqual(output_path, self.approved_csv)

        with open(self.approved_csv, "r", encoding="utf-8-sig", newline="") as handle:
            approved_rows = list(csv.DictReader(handle))
        self.assertEqual(len(approved_rows), 2)
        self.assertEqual(approved_rows[0]["reviewer_decision"], "approve_auto")


class TestApprovedDownloaderWorkflow(TestApprovedDownloader):
    def make_response(self, status_code=200, content=b"pdf-bytes"):
        response = Mock()
        response.status_code = status_code
        response.iter_content.return_value = [content]
        return response

    def test_download_candidate_success(self):
        candidate = self.approved_row()
        checkpoint = pure_approved_downloader.load_checkpoint(self.checkpoint_path)
        mock_http = Mock()
        mock_http.get.return_value = self.make_response()

        result = pure_approved_downloader.download_candidate(
            candidate,
            checkpoint,
            output_dir=self.output_dir,
            checkpoint_path=self.checkpoint_path,
            http_client=mock_http,
        )

        self.assertEqual(result["status"], "completed")
        self.assertTrue(os.path.exists(result["output_path"]))
        with open(self.checkpoint_path, "r", encoding="utf-8") as handle:
            saved = json.load(handle)
        self.assertIn("uuid-1", saved["completed"])

    def test_download_candidate_skips_existing(self):
        candidate = self.approved_row()
        output_path = pure_approved_downloader.build_output_path(candidate, self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        with open(output_path, "wb") as handle:
            handle.write(b"existing")

        checkpoint = pure_approved_downloader.load_checkpoint(self.checkpoint_path)
        result = pure_approved_downloader.download_candidate(
            candidate,
            checkpoint,
            output_dir=self.output_dir,
            checkpoint_path=self.checkpoint_path,
            http_client=Mock(),
        )
        self.assertEqual(result["status"], "existing_file")

    @patch("pure_approved_downloader.test_api_connection")
    def test_run_approved_download_pilot_limits_pilot_size(self, mock_connection):
        rows = [
            self.approved_row(uuid="uuid-1", pure_id="1"),
            self.approved_row(uuid="uuid-2", pure_id="2"),
            self.approved_row(uuid="uuid-3", pure_id="3"),
        ]
        self.write_approved_csv(rows)
        mock_connection.return_value = True

        mock_http = Mock()
        mock_http.get.return_value = self.make_response()

        summary = pure_approved_downloader.run_approved_download_pilot(
            review_csv_path=os.path.join(self.temp_dir, "review.csv"),
            approved_csv_path=self.approved_csv,
            output_dir=self.output_dir,
            checkpoint_path=self.checkpoint_path,
            pilot_size=2,
            http_client=mock_http,
        )

        self.assertEqual(summary["requested_candidates"], 3)
        self.assertEqual(summary["processed_candidates"], 2)
        self.assertEqual(summary["completed"], 2)
