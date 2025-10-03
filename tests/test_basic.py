"""
Simplified pytest-style tests for download_pure_file.py

These tests can be run with either unittest or pytest.
They focus on the most critical functionality.
"""

import unittest
import tempfile
import os
import csv
import shutil
from unittest.mock import Mock, patch, mock_open

# Import the module we're testing
import download_pure_file


class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality that's most likely to break."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

        # Mock API configuration
        self.api_key_patcher = patch.object(
            download_pure_file, "PURE_API_KEY", "test-key"
        )
        self.base_url_patcher = patch.object(
            download_pure_file, "BASE_API_URL", "https://test.example.com/ws/api"
        )

        self.api_key_patcher.start()
        self.base_url_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.api_key_patcher.stop()
        self.base_url_patcher.stop()

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_api_key_validation(self):
        """Test API key validation works correctly."""
        # Valid key
        self.assertTrue(download_pure_file.check_api_key("valid-key-123"))

        # Invalid keys
        with patch("download_pure_file.log_debug"):
            self.assertFalse(download_pure_file.check_api_key(""))
            self.assertFalse(download_pure_file.check_api_key(None))
            self.assertFalse(download_pure_file.check_api_key("YOUR_API_KEY"))

    def test_csv_loading(self):
        """Test CSV loading functionality."""
        # Create test CSV
        csv_path = os.path.join(self.temp_dir, "test.csv")
        csv_data = [
            ["Year", "Title", "Pure ID"],
            ["2020", "Test Paper", "12345"],
            ["2021", "Another Paper", "67890"],
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        # Test loading
        with patch("download_pure_file.log_debug"):
            results = download_pure_file.load_pure_ids_from_csv(csv_path)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["pure_id"], "12345")
        self.assertEqual(results[1]["pure_id"], "67890")

    def test_file_uuid_detection(self):
        """Test file UUID detection from file listings."""
        mock_files = {
            "items": [
                {"uuid": "file1", "fileName": "document.txt"},
                {"uuid": "file2", "fileName": "report.pdf"},
                {"uuid": "file3", "fileName": "data.docx"},
            ]
        }

        with patch("download_pure_file.list_pure_files") as mock_list:
            with patch("download_pure_file.log_debug"):
                mock_list.return_value = mock_files

                # Should find PDF first
                result = download_pure_file.get_first_report_file_uuid(
                    "research-outputs", "test-uuid"
                )
                self.assertEqual(result, "file2")

    def test_id_type_identification(self):
        """Test Pure ID type identification."""
        # Mock successful research output response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"uuid": "test", "title": {"value": "Test"}}

        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.identify_pure_id_type("12345", mock_http)

        self.assertTrue(result["is_object_id"])
        self.assertEqual(result["object_type"], "research-outputs")

    def test_download_parameter_validation(self):
        """Test download function parameter validation."""
        with patch("download_pure_file.log_debug"):
            # These should not crash and should handle invalid inputs gracefully
            download_pure_file.download_pure_file("", "test-uuid")  # Empty object type
            download_pure_file.download_pure_file("research-outputs", "")  # Empty UUID
            download_pure_file.download_pure_file(
                "research-outputs", "test", 123
            )  # Invalid file UUID type


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def setUp(self):
        """Set up test environment."""
        self.api_key_patcher = patch.object(
            download_pure_file, "PURE_API_KEY", "test-key"
        )
        self.base_url_patcher = patch.object(
            download_pure_file, "BASE_API_URL", "https://test.example.com/ws/api"
        )

        self.api_key_patcher.start()
        self.base_url_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.api_key_patcher.stop()
        self.base_url_patcher.stop()

    def test_missing_csv_file(self):
        """Test handling of missing CSV file."""
        with patch("download_pure_file.log_debug"):
            result = download_pure_file.load_pure_ids_from_csv("nonexistent.csv")
            self.assertEqual(result, [])

    def test_api_error_responses(self):
        """Test handling of various API error responses."""
        error_codes = [401, 403, 404, 429, 500]

        for code in error_codes:
            mock_response = Mock()
            mock_response.status_code = code
            mock_response.text = f"Error {code}"

            mock_http = Mock()
            mock_http.get.return_value = mock_response

            with patch("download_pure_file.log_debug"):
                result = download_pure_file.list_pure_files(
                    "research-outputs", "test-uuid", mock_http
                )
                self.assertIsNone(result, f"Should handle {code} error gracefully")

    def test_network_errors(self):
        """Test handling of network errors."""
        mock_http = Mock()
        mock_http.get.side_effect = Exception("Network error")

        with patch("download_pure_file.log_debug"):
            result = download_pure_file.list_pure_files(
                "research-outputs", "test-uuid", mock_http
            )
            self.assertIsNone(result)


def run_critical_tests():
    """Run only the most critical tests that verify core functionality."""
    print("Running critical functionality tests...")
    print("=" * 50)

    # Create test suite with only critical tests
    suite = unittest.TestSuite()

    # Add critical tests
    suite.addTest(TestBasicFunctionality("test_api_key_validation"))
    suite.addTest(TestBasicFunctionality("test_csv_loading"))
    suite.addTest(TestBasicFunctionality("test_file_uuid_detection"))
    suite.addTest(TestBasicFunctionality("test_id_type_identification"))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\nCritical tests: {'PASSED' if result.wasSuccessful() else 'FAILED'}")
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "critical":
        # Run only critical tests
        success = run_critical_tests()
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        unittest.main(verbosity=2)
