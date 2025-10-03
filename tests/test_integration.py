"""
Integration tests for Pure API downloader

These tests verify that multiple components work together correctly.
They use mocking to avoid actual API calls.
"""

import unittest
import sys
import os
import tempfile
import shutil
import csv
from unittest.mock import patch, Mock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import download_pure_file


class TestEndToEndDownload(unittest.TestCase):
    """Test complete download workflow from CSV to file download."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_file = os.path.join(self.temp_dir, 'test.csv')
        self.output_dir = os.path.join(self.temp_dir, 'downloads')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create test CSV
        csv_data = [
            ["Year", "Title", "Pure ID"],
            ["2020", "Research Paper 1", "27139086"],
            ["2021", "Research Paper 2", "46773789"],
        ]
        
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)

        # Mock config
        self.config_patcher = patch.multiple(
            'download_pure_file',
            PURE_API_KEY="test-key",
            BASE_API_URL="https://test.elsevierpure.com/ws/api"
        )
        self.config_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_full_workflow_numeric_id_to_download(self, mock_get, mock_log):
        """Test complete workflow: CSV → numeric ID → UUID → files → download."""
        
        # Mock API responses
        # 1. Identify Pure ID (numeric to UUID)
        identify_response = Mock()
        identify_response.status_code = 200
        identify_response.json.return_value = {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "title": {"value": "Research Paper 1"},
            "electronicVersions": [
                {
                    "file": {
                        "fileId": 98765,
                        "fileName": "document.pdf",
                        "mimeType": "application/pdf",
                        "size": 1024000
                    }
                }
            ]
        }
        
        # 2. Download file
        download_response = Mock()
        download_response.status_code = 200
        download_response.headers = {
            'Content-Disposition': 'attachment; filename="document.pdf"',
            'Content-Type': 'application/pdf',
            'Content-Length': '1024000'
        }
        download_response.iter_content = Mock(return_value=[b'PDF content here'])
        
        mock_get.side_effect = [identify_response, download_response]
        
        # Run batch download (limited to 1 for this test)
        result = download_pure_file.batch_download_from_csv(
            self.csv_file,
            self.output_dir,
            max_downloads=1
        )
        
        # Verify results
        self.assertEqual(result['total_entries'], 1)
        self.assertEqual(result['successful_downloads'], 1)
        self.assertEqual(result['failed_downloads'], 0)

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_full_workflow_with_file_filtering(self, mock_get, mock_log):
        """Test workflow with file type filtering."""
        
        # Mock response with multiple file types
        identify_response = Mock()
        identify_response.status_code = 200
        identify_response.json.return_value = {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "title": {"value": "Research Paper"},
            "electronicVersions": [
                {
                    "file": {
                        "fileId": 1,
                        "fileName": "data.xlsx",
                        "mimeType": "application/vnd.ms-excel",
                        "size": 512000
                    }
                },
                {
                    "file": {
                        "fileId": 2,
                        "fileName": "document.pdf",
                        "mimeType": "application/pdf",
                        "size": 1024000
                    }
                }
            ]
        }
        
        download_response = Mock()
        download_response.status_code = 200
        download_response.headers = {'Content-Disposition': 'attachment; filename="document.pdf"'}
        download_response.iter_content = Mock(return_value=[b'PDF'])
        
        mock_get.side_effect = [identify_response, download_response]
        
        # Test with file type filter
        with patch.object(download_pure_file, 'DOWNLOAD_FILE_TYPES', ['.pdf']):
            result = download_pure_file.batch_download_from_csv(
                self.csv_file,
                self.output_dir,
                max_downloads=1
            )
        
        # Should only download PDF, not XLSX
        self.assertEqual(result['successful_downloads'], 1)

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_full_workflow_with_errors(self, mock_get, mock_log):
        """Test workflow with various error conditions."""
        
        # First entry: 404 (not found)
        not_found_response = Mock()
        not_found_response.status_code = 404
        not_found_response.text = "Not found"
        
        # Second entry: 200 but no files
        no_files_response = Mock()
        no_files_response.status_code = 200
        no_files_response.json.return_value = {
            "uuid": "12345678-1234-5678-1234-567812345678",
            "title": {"value": "Research Paper 2"},
            "electronicVersions": []  # No files
        }
        
        mock_get.side_effect = [not_found_response, no_files_response]
        
        result = download_pure_file.batch_download_from_csv(
            self.csv_file,
            self.output_dir,
            max_downloads=2
        )
        
        # Both should fail
        self.assertEqual(result['total_entries'], 2)
        self.assertEqual(result['successful_downloads'], 0)
        self.assertEqual(result['failed_downloads'], 2)


class TestCSVToAPIIntegration(unittest.TestCase):
    """Test integration between CSV loading and API calls."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        self.config_patcher = patch.multiple(
            'download_pure_file',
            PURE_API_KEY="test-key",
            BASE_API_URL="https://test.elsevierpure.com/ws/api"
        )
        self.config_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('download_pure_file.log_debug')
    def test_csv_loading_to_id_identification(self, mock_log):
        """Test CSV loading followed by ID identification."""
        
        # Create CSV
        csv_file = os.path.join(self.temp_dir, 'test.csv')
        csv_data = [
            ["Pure ID", "Title"],
            ["12345", "Test 1"],
            ["67890", "Test 2"],
        ]
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
        
        # Load CSV
        entries = download_pure_file.load_pure_ids_from_csv(csv_file)
        
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]['pure_id'], '12345')
        self.assertEqual(entries[1]['pure_id'], '67890')
        
        # Test ID identification for each
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "uuid": "test-uuid",
                "title": {"value": "Test"}
            }
            mock_get.return_value = mock_response
            
            for entry in entries:
                result = download_pure_file.identify_pure_id_type(entry['pure_id'])
                self.assertTrue(result['is_object_id'])


class TestErrorRecovery(unittest.TestCase):
    """Test error recovery and resilience."""

    def setUp(self):
        """Set up test environment."""
        self.config_patcher = patch.multiple(
            'download_pure_file',
            PURE_API_KEY="test-key",
            BASE_API_URL="https://test.elsevierpure.com/ws/api"
        )
        self.config_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_network_error_recovery(self, mock_get, mock_log):
        """Test recovery from network errors."""
        
        # Simulate network error
        mock_get.side_effect = Exception("Network error")
        
        result = download_pure_file.identify_pure_id_type("12345")
        
        # Should return gracefully with error info
        self.assertFalse(result['is_object_id'])
        self.assertIn('error', result)

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_partial_batch_failure(self, mock_get, mock_log):
        """Test batch processing continues after individual failures."""
        
        # First call succeeds, second fails, third succeeds
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "uuid": "test-uuid",
            "title": {"value": "Test"},
            "electronicVersions": [
                {
                    "file": {
                        "fileId": 1,
                        "fileName": "test.pdf",
                        "mimeType": "application/pdf",
                        "size": 1000
                    }
                }
            ]
        }
        
        download_success = Mock()
        download_success.status_code = 200
        download_success.headers = {'Content-Disposition': 'attachment; filename="test.pdf"'}
        download_success.iter_content = Mock(return_value=[b'content'])
        
        fail_response = Mock()
        fail_response.status_code = 404
        
        mock_get.side_effect = [
            success_response, download_success,  # First entry succeeds
            fail_response,  # Second entry fails
            success_response, download_success,  # Third entry succeeds
        ]
        
        # Create CSV with 3 entries
        temp_dir = tempfile.mkdtemp()
        try:
            csv_file = os.path.join(temp_dir, 'test.csv')
            csv_data = [
                ["Pure ID"], ["1"], ["2"], ["3"]
            ]
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            result = download_pure_file.batch_download_from_csv(
                csv_file,
                temp_dir
            )
            
            # Should have processed all 3, with 2 successes and 1 failure
            self.assertEqual(result['total_entries'], 3)
            self.assertEqual(result['successful_downloads'], 2)
            self.assertEqual(result['failed_downloads'], 1)
            
        finally:
            shutil.rmtree(temp_dir)


class TestAPIConnectionIntegration(unittest.TestCase):
    """Test API connection and authentication integration."""

    def setUp(self):
        """Set up test environment."""
        self.config_patcher = patch.multiple(
            'download_pure_file',
            PURE_API_KEY="test-key",
            BASE_API_URL="https://test.elsevierpure.com/ws/api"
        )
        self.config_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.config_patcher.stop()

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_api_connection_test_success(self, mock_get, mock_log):
        """Test successful API connection test."""
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = download_pure_file.test_api_connection()
        
        self.assertTrue(result)
        
        # Verify API key was passed
        call_kwargs = mock_get.call_args[1]
        self.assertIn('params', call_kwargs)
        self.assertIn('apiKey', call_kwargs['params'])

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_api_connection_test_auth_failure(self, mock_get, mock_log):
        """Test API connection with authentication failure."""
        
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response
        
        result = download_pure_file.test_api_connection()
        
        self.assertFalse(result)

    @patch('download_pure_file.log_debug')
    @patch('requests.get')
    def test_api_key_passed_correctly(self, mock_get, mock_log):
        """Test that API key is passed correctly in requests."""
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": []}
        mock_get.return_value = mock_response
        
        download_pure_file.list_pure_files("research-outputs", "test-uuid")
        
        # Verify API key was in params
        call_kwargs = mock_get.call_args[1]
        self.assertEqual(call_kwargs['params']['apiKey'], "test-key")


if __name__ == '__main__':
    unittest.main(verbosity=2)
