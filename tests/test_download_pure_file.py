"""
Test suite for download_pure_file.py

This test suite covers all major functions in the Pure API downloader script
including CSV processing, API calls, file downloads, and error handling.
"""

import unittest
import tempfile
import os
import json
import csv
import shutil
from unittest.mock import Mock, patch, mock_open, MagicMock
from io import StringIO

# Import the module we're testing
import download_pure_file


class TestPureAPIDownloader(unittest.TestCase):
    """Test cases for Pure API downloader functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_api_key = "test-api-key-12345"
        self.test_base_url = "https://test.elsevierpure.com/ws/api"
        self.test_object_type = "research-outputs"
        self.test_object_uuid = "123e4567-e89b-12d3-a456-426614174000"
        self.test_file_uuid = "456e7890-e89b-12d3-a456-426614174000"

        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()

        # Patch the configuration values
        self.api_key_patcher = patch.object(
            download_pure_file, "PURE_API_KEY", self.test_api_key
        )
        self.base_url_patcher = patch.object(
            download_pure_file, "BASE_API_URL", self.test_base_url
        )

        self.api_key_patcher.start()
        self.base_url_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.api_key_patcher.stop()
        self.base_url_patcher.stop()

        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)


class TestLogDebug(TestPureAPIDownloader):
    """Test the logging function."""

    @patch("builtins.print")
    def test_log_debug_basic(self, mock_print):
        """Test basic logging functionality."""
        download_pure_file.log_debug("Test message")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn("[INFO] Test message", call_args)

    @patch("builtins.print")
    def test_log_debug_with_level(self, mock_print):
        """Test logging with different levels."""
        download_pure_file.log_debug("Error message", "ERROR")
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        self.assertIn("[ERROR] Error message", call_args)


class TestCheckApiKey(TestPureAPIDownloader):
    """Test API key validation."""

    def test_check_api_key_valid(self):
        """Test with valid API key."""
        result = download_pure_file.check_api_key("valid-api-key-123")
        self.assertTrue(result)

    def test_check_api_key_empty(self):
        """Test with empty API key."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.check_api_key("")
            self.assertFalse(result)

    def test_check_api_key_none(self):
        """Test with None API key."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.check_api_key(None)
            self.assertFalse(result)

    def test_check_api_key_placeholder(self):
        """Test with placeholder API key."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.check_api_key("YOUR_API_KEY")
            self.assertFalse(result)

    def test_check_api_key_short(self):
        """Test with short API key (should warn but pass)."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.check_api_key("abc")
            self.assertTrue(result)


class TestValidateBaseUrl(TestPureAPIDownloader):
    """Test base URL validation."""

    def test_validate_base_url_valid(self):
        """Test with valid base URL."""
        url = "https://test.elsevierpure.com/ws/api"
        result = download_pure_file.validate_base_url(url)
        self.assertTrue(result)

    def test_validate_base_url_empty(self):
        """Test with empty URL."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.validate_base_url("")
            self.assertFalse(result)

    def test_validate_base_url_http(self):
        """Test with HTTP URL (should warn but pass)."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.validate_base_url(
                "http://test.elsevierpure.com/ws/api"
            )
            self.assertTrue(result)


class TestLoadPureIdsFromCsv(TestPureAPIDownloader):
    """Test CSV loading functionality."""

    def create_test_csv(self, data, filename="test.csv"):
        """Create a test CSV file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return filepath

    def test_load_csv_valid(self):
        """Test loading valid CSV file."""
        csv_data = [
            ["Year", "Title", "Pure ID"],
            ["2020", "Test Paper 1", "12345"],
            ["2021", "Test Paper 2", "67890"],
        ]
        csv_path = self.create_test_csv(csv_data)

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.load_pure_ids_from_csv(csv_path)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["pure_id"], "12345")
        self.assertEqual(result[0]["title"], "Test Paper 1")
        self.assertEqual(result[1]["pure_id"], "67890")

    def test_load_csv_missing_file(self):
        """Test loading non-existent CSV file."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.load_pure_ids_from_csv("nonexistent.csv")

        self.assertEqual(result, [])

    def test_load_csv_missing_column(self):
        """Test loading CSV with missing Pure ID column."""
        csv_data = [
            ["Year", "Title"],
            ["2020", "Test Paper 1"],
        ]
        csv_path = self.create_test_csv(csv_data)

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.load_pure_ids_from_csv(csv_path)

        self.assertEqual(result, [])

    def test_load_csv_empty_ids(self):
        """Test loading CSV with empty Pure IDs."""
        csv_data = [
            ["Year", "Title", "Pure ID"],
            ["2020", "Test Paper 1", "12345"],
            ["2021", "Test Paper 2", ""],  # Empty ID
            ["2022", "Test Paper 3", "67890"],
        ]
        csv_path = self.create_test_csv(csv_data)

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.load_pure_ids_from_csv(csv_path)

        # Should only return entries with valid IDs
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["pure_id"], "12345")
        self.assertEqual(result[1]["pure_id"], "67890")


class TestListPureFiles(TestPureAPIDownloader):
    """Test Pure API file listing functionality."""

    def create_mock_response(self, status_code=200, json_data=None, headers=None):
        """Create a mock HTTP response."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        mock_response.headers = headers or {}
        mock_response.text = json.dumps(json_data) if json_data else ""
        return mock_response

    def test_list_pure_files_success(self):
        """Test successful file listing."""
        mock_files_response = {
            "items": [
                {
                    "uuid": self.test_file_uuid,
                    "fileName": "test_document.pdf",
                    "size": 1024000,
                    "mimeType": "application/pdf",
                }
            ]
        }

        mock_http = Mock()
        mock_http.get.return_value = self.create_mock_response(200, mock_files_response)

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.list_pure_files(
                self.test_object_type, self.test_object_uuid, mock_http
            )

        self.assertIsNotNone(result)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["fileName"], "test_document.pdf")

        # Verify API call was made correctly
        mock_http.get.assert_called_once()
        call_args = mock_http.get.call_args
        expected_url = f"{self.test_base_url}/{self.test_object_type}/{self.test_object_uuid}/files"
        self.assertEqual(call_args[0][0], expected_url)

    def test_list_pure_files_invalid_params(self):
        """Test with invalid parameters."""
        with patch("download_pure_file.log_debug"):
            # Test empty object_type
            result = download_pure_file.list_pure_files("", self.test_object_uuid)
            self.assertIsNone(result)

            # Test empty object_uuid
            result = download_pure_file.list_pure_files(self.test_object_type, "")
            self.assertIsNone(result)

    def test_list_pure_files_api_error(self):
        """Test API error responses."""
        mock_http = Mock()
        mock_http.get.return_value = self.create_mock_response(404, None)

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.list_pure_files(
                self.test_object_type, self.test_object_uuid, mock_http
            )

        self.assertIsNone(result)

    def test_list_pure_files_connection_error(self):
        """Test connection errors."""
        mock_http = Mock()
        mock_http.get.side_effect = Exception("Connection error")

        with patch("download_pure_file.log_debug"):
            with patch("requests.exceptions.RequestException", Exception):
                result = download_pure_file.list_pure_files(
                    self.test_object_type, self.test_object_uuid, mock_http
                )

        self.assertIsNone(result)


class TestGetFirstReportFileUuid(TestPureAPIDownloader):
    """Test file UUID detection functionality."""

    def test_get_first_report_file_uuid_pdf(self):
        """Test finding PDF file."""
        mock_files_data = {
            "items": [
                {"uuid": "file1", "fileName": "document.txt", "mimeType": "text/plain"},
                {
                    "uuid": "file2",
                    "fileName": "report.pdf",
                    "mimeType": "application/pdf",
                },
                {
                    "uuid": "file3",
                    "fileName": "data.xlsx",
                    "mimeType": "application/vnd.ms-excel",
                },
            ]
        }

        with patch("download_pure_file.list_pure_files") as mock_list:
            with patch("download_pure_file.log_debug"):
                mock_list.return_value = mock_files_data

                result = download_pure_file.get_first_report_file_uuid(
                    self.test_object_type, self.test_object_uuid
                )

                self.assertEqual(result, "file2")

    def test_get_first_report_file_uuid_docx(self):
        """Test finding DOCX file."""
        mock_files_data = {
            "items": [
                {"uuid": "file1", "fileName": "document.txt", "mimeType": "text/plain"},
                {
                    "uuid": "file2",
                    "fileName": "report.docx",
                    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                },
            ]
        }

        with patch("download_pure_file.list_pure_files") as mock_list:
            with patch("download_pure_file.log_debug"):
                mock_list.return_value = mock_files_data

                result = download_pure_file.get_first_report_file_uuid(
                    self.test_object_type, self.test_object_uuid
                )

                self.assertEqual(result, "file2")

    def test_get_first_report_file_uuid_none_found(self):
        """Test when no suitable files are found."""
        mock_files_data = {
            "items": [
                {"uuid": "file1", "fileName": "document.txt", "mimeType": "text/plain"},
                {
                    "uuid": "file2",
                    "fileName": "data.xlsx",
                    "mimeType": "application/vnd.ms-excel",
                },
            ]
        }

        with patch("download_pure_file.list_pure_files") as mock_list:
            with patch("download_pure_file.log_debug"):
                mock_list.return_value = mock_files_data

                result = download_pure_file.get_first_report_file_uuid(
                    self.test_object_type, self.test_object_uuid
                )

                self.assertIsNone(result)

    def test_get_first_report_file_uuid_no_files(self):
        """Test when no files are returned."""
        with patch("download_pure_file.list_pure_files") as mock_list:
            with patch("download_pure_file.log_debug"):
                mock_list.return_value = None

                result = download_pure_file.get_first_report_file_uuid(
                    self.test_object_type, self.test_object_uuid
                )

                self.assertIsNone(result)


class TestDownloadPureFile(TestPureAPIDownloader):
    """Test file download functionality."""

    def test_download_pure_file_success(self):
        """Test successful file download."""
        # Mock response with file content
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Disposition": 'attachment; filename="test_document.pdf"',
            "Content-Length": "1024",
            "Content-Type": "application/pdf",
        }

        # Mock the file content chunks
        test_content = b"PDF file content here"
        mock_response.iter_content.return_value = [test_content]

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        output_path = os.path.join(self.temp_dir, "test_output.pdf")

        with patch("download_pure_file.log_debug"):
            download_pure_file.download_pure_file(
                self.test_object_type,
                self.test_object_uuid,
                self.test_file_uuid,
                output_path,
                mock_http,
            )

        # Verify file was created
        self.assertTrue(os.path.exists(output_path))

        # Verify file content
        with open(output_path, "rb") as f:
            content = f.read()
            self.assertEqual(content, test_content)

    def test_download_pure_file_auto_select(self):
        """Test download with automatic file selection."""
        # Mock get_first_report_file_uuid to return a file UUID
        with patch("download_pure_file.get_first_report_file_uuid") as mock_get_file:
            with patch("download_pure_file.log_debug"):
                mock_get_file.return_value = self.test_file_uuid

                # Mock the download response
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.headers = {
                    "Content-Disposition": 'attachment; filename="auto.pdf"'
                }
                mock_response.iter_content.return_value = [b"content"]

                mock_http = Mock()
                mock_http.get.return_value = mock_response

                # Call without file_uuid (should auto-select)
                download_pure_file.download_pure_file(
                    self.test_object_type,
                    self.test_object_uuid,
                    None,  # No file UUID - should auto-select
                    None,  # No output path - should auto-generate
                    mock_http,
                )

                # Verify get_first_report_file_uuid was called
                mock_get_file.assert_called_once()

    def test_download_pure_file_invalid_params(self):
        """Test download with invalid parameters."""
        with patch("download_pure_file.log_debug"):
            # Test empty object_type
            download_pure_file.download_pure_file("", self.test_object_uuid)

            # Test empty object_uuid
            download_pure_file.download_pure_file(self.test_object_type, "")

            # Test invalid file_uuid type
            download_pure_file.download_pure_file(
                self.test_object_type, self.test_object_uuid, 123  # Should be string
            )

    def test_download_pure_file_api_error(self):
        """Test download with API error."""
        mock_http = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_response.headers = {}  # Add empty headers dict
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            download_pure_file.download_pure_file(
                self.test_object_type,
                self.test_object_uuid,
                self.test_file_uuid,
                None,
                mock_http,
            )


class TestIdentifyPureIdType(TestPureAPIDownloader):
    """Test Pure ID type identification."""

    def test_identify_pure_id_type_research_output(self):
        """Test identifying research output ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "uuid": self.test_object_uuid,
            "title": {"value": "Test Research Output"},
        }

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.identify_pure_id_type("12345", mock_http)

        self.assertTrue(result["is_object_id"])
        self.assertEqual(result["object_type"], "research-outputs")
        self.assertEqual(result["title"], "Test Research Output")

    def test_identify_pure_id_type_person(self):
        """Test identifying person ID."""
        # First call (research-outputs) returns 404
        mock_response_404 = Mock()
        mock_response_404.status_code = 404

        # Second call (persons) returns 200
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"uuid": self.test_object_uuid}

        mock_http = Mock()
        mock_http.get.side_effect = [mock_response_404, mock_response_200]

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.identify_pure_id_type("12345", mock_http)

        self.assertTrue(result["is_object_id"])
        self.assertEqual(result["object_type"], "persons")

    def test_identify_pure_id_type_numeric(self):
        """Test identifying numeric ID."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.identify_pure_id_type("12345", mock_http)

        self.assertFalse(result["is_object_id"])
        self.assertTrue(result["test_results"]["numeric_id"])

    def test_identify_pure_id_type_uuid_format(self):
        """Test identifying UUID format ID."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        uuid_id = "123e4567-e89b-12d3-a456-426614174000"

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.identify_pure_id_type(uuid_id, mock_http)

        self.assertFalse(result["is_object_id"])
        self.assertTrue(result["test_results"]["file_uuid_format"])


class TestBatchDownloadFromCsv(TestPureAPIDownloader):
    """Test batch CSV download functionality."""

    def create_test_csv_with_data(self):
        """Create a test CSV file with sample data."""
        csv_data = [
            ["Year", "Title", "Pure ID"],
            ["2020", "Test Paper 1", "12345"],
            ["2021", "Test Paper 2", "67890"],
            ["2022", "Test Paper 3", "11111"],
        ]
        return self.create_test_csv(csv_data)

    def create_test_csv(self, data, filename="test.csv"):
        """Create a test CSV file."""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return filepath

    def test_batch_download_success(self):
        """Test successful batch download."""
        csv_path = self.create_test_csv_with_data()

        with patch("download_pure_file.download_from_csv_entry") as mock_download:
            with patch("download_pure_file.log_debug"):
                mock_download.return_value = True

                result = download_pure_file.batch_download_from_csv(
                    csv_path, self.temp_dir, max_downloads=2
                )

                self.assertEqual(result["total_entries"], 2)  # Limited by max_downloads
                self.assertEqual(result["successful_downloads"], 2)
                self.assertEqual(result["failed_downloads"], 0)

    def test_batch_download_mixed_results(self):
        """Test batch download with mixed success/failure."""
        csv_path = self.create_test_csv_with_data()

        with patch("download_pure_file.download_from_csv_entry") as mock_download:
            with patch("download_pure_file.log_debug"):
                # First call succeeds, second fails, third succeeds
                mock_download.side_effect = [True, False, True]

                result = download_pure_file.batch_download_from_csv(
                    csv_path, self.temp_dir
                )

                self.assertEqual(result["total_entries"], 3)
                self.assertEqual(result["successful_downloads"], 2)
                self.assertEqual(result["failed_downloads"], 1)

    def test_batch_download_no_csv(self):
        """Test batch download with missing CSV."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.batch_download_from_csv(
                "nonexistent.csv", self.temp_dir
            )

            self.assertIn("error", result)


class TestUtilityFunctions(TestPureAPIDownloader):
    """Test utility functions."""

    def test_validate_uuid_format_valid(self):
        """Test valid UUID format."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        result = download_pure_file.validate_uuid_format(valid_uuid)
        self.assertTrue(result)

    def test_validate_uuid_format_invalid(self):
        """Test invalid UUID format."""
        invalid_uuids = [
            "123456",
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",  # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
        ]

        for invalid_uuid in invalid_uuids:
            result = download_pure_file.validate_uuid_format(invalid_uuid)
            self.assertFalse(result, f"UUID {invalid_uuid} should be invalid")

    def test_search_research_outputs(self):
        """Test research outputs search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "count": 1,
            "items": [
                {
                    "uuid": self.test_object_uuid,
                    "title": {"value": "Test Research Output"},
                    "type": {"term": {"text": "Article"}},
                }
            ],
        }

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.search_research_outputs(
                "test query", http_client=mock_http
            )

        self.assertIsNotNone(result)
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["items"]), 1)

    def test_test_api_connection_success(self):
        """Test successful API connection."""
        mock_response = Mock()
        mock_response.status_code = 200

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.test_api_connection(mock_http)

        self.assertTrue(result)

    def test_test_api_connection_failure(self):
        """Test failed API connection."""
        mock_response = Mock()
        mock_response.status_code = 401

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.test_api_connection(mock_http)

        self.assertFalse(result)


if __name__ == "__main__":
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromModule(__import__(__name__))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
