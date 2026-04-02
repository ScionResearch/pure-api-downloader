"""
Test suite for config.py

Tests configuration validation and settings.
"""

import unittest
import sys
import os
import importlib
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation functions."""

    def test_validate_config_with_valid_settings(self):
        """Test validation with valid configuration."""
        # Temporarily modify config values for testing
        original_api_key = config.PURE_API_KEY
        original_base_url = config.BASE_API_URL
        original_csv_file = config.CSV_FILE_PATH
        
        try:
            config.PURE_API_KEY = "valid-api-key-12345"
            config.BASE_API_URL = "https://test.elsevierpure.com/ws/api"
            config.CSV_FILE_PATH = "test_file.csv"
            
            is_valid, message = config.validate_config()
            
            self.assertTrue(is_valid)
            self.assertEqual(message, "Configuration valid")
            
        finally:
            # Restore original values
            config.PURE_API_KEY = original_api_key
            config.BASE_API_URL = original_base_url
            config.CSV_FILE_PATH = original_csv_file

    def test_validate_config_missing_api_key(self):
        """Test validation with missing API key."""
        original_api_key = config.PURE_API_KEY
        
        try:
            config.PURE_API_KEY = "YOUR_API_KEY"
            
            is_valid, message = config.validate_config()
            
            self.assertFalse(is_valid)
            self.assertIn("API key not set", message)
            
        finally:
            config.PURE_API_KEY = original_api_key

    def test_validate_config_placeholder_url(self):
        """Test validation with placeholder URL."""
        original_base_url = config.BASE_API_URL
        
        try:
            config.BASE_API_URL = "https://yourinstitution.elsevierpure.com/ws/api"
            
            is_valid, message = config.validate_config()
            
            self.assertFalse(is_valid)
            self.assertIn("yourinstitution", message)
            
        finally:
            config.BASE_API_URL = original_base_url

    def test_validate_config_invalid_url_scheme(self):
        """Test validation with HTTP instead of HTTPS."""
        original_base_url = config.BASE_API_URL
        
        try:
            config.BASE_API_URL = "http://test.elsevierpure.com/ws/api"
            
            is_valid, message = config.validate_config()
            
            self.assertFalse(is_valid)
            self.assertIn("HTTPS", message)
            
        finally:
            config.BASE_API_URL = original_base_url

    def test_validate_config_invalid_url_ending(self):
        """Test validation with wrong URL ending."""
        original_base_url = config.BASE_API_URL
        
        try:
            config.BASE_API_URL = "https://test.elsevierpure.com/api"
            
            is_valid, message = config.validate_config()
            
            self.assertFalse(is_valid)
            self.assertIn("/ws/api", message)
            
        finally:
            config.BASE_API_URL = original_base_url

    def test_validate_config_short_api_key(self):
        """Test validation with too short API key."""
        original_api_key = config.PURE_API_KEY
        
        try:
            config.PURE_API_KEY = "abc"
            
            is_valid, message = config.validate_config()
            
            self.assertFalse(is_valid)
            self.assertIn("too short", message)
            
        finally:
            config.PURE_API_KEY = original_api_key

    def test_validate_config_ignores_legacy_direct_download_placeholders(self):
        """Legacy direct-download placeholders should not block the staged workflow."""
        original_api_key = config.PURE_API_KEY
        original_base_url = config.BASE_API_URL
        original_csv = config.CSV_FILE_PATH

        try:
            config.PURE_API_KEY = "valid-api-key-12345"
            config.BASE_API_URL = "https://test.elsevierpure.com/ws/api"
            config.CSV_FILE_PATH = "your_file.csv"

            is_valid, message = config.validate_config()

            self.assertTrue(is_valid)
            self.assertEqual(message, "Configuration valid")

        finally:
            config.PURE_API_KEY = original_api_key
            config.BASE_API_URL = original_base_url
            config.CSV_FILE_PATH = original_csv


class TestConfigSettings(unittest.TestCase):
    """Test configuration settings existence."""

    def test_api_key_exists(self):
        """Test that API key is defined."""
        self.assertTrue(hasattr(config, 'PURE_API_KEY'))
        self.assertIsInstance(config.PURE_API_KEY, str)

    def test_base_url_exists(self):
        """Test that base URL is defined."""
        self.assertTrue(hasattr(config, 'BASE_API_URL'))
        self.assertIsInstance(config.BASE_API_URL, str)

    def test_csv_file_path_exists(self):
        """Test that CSV file path is defined."""
        self.assertTrue(hasattr(config, 'CSV_FILE_PATH'))
        self.assertIsInstance(config.CSV_FILE_PATH, str)

    def test_id_column_exists(self):
        """Test that ID column is defined."""
        self.assertTrue(hasattr(config, 'ID_COLUMN'))
        self.assertIsInstance(config.ID_COLUMN, str)

    def test_output_directory_exists(self):
        """Test that output directory is defined."""
        self.assertTrue(hasattr(config, 'OUTPUT_DIRECTORY'))
        self.assertIsInstance(config.OUTPUT_DIRECTORY, str)

    def test_max_downloads_exists(self):
        """Test that max downloads is defined."""
        self.assertTrue(hasattr(config, 'MAX_DOWNLOADS'))
        self.assertTrue(isinstance(config.MAX_DOWNLOADS, (int, type(None))))

    def test_download_file_types_exists(self):
        """Test that download file types is defined."""
        self.assertTrue(hasattr(config, 'DOWNLOAD_FILE_TYPES'))
        self.assertIsInstance(config.DOWNLOAD_FILE_TYPES, list)

    def test_request_timeout_exists(self):
        """Test that request timeout is defined."""
        self.assertTrue(hasattr(config, 'REQUEST_TIMEOUT'))
        self.assertIsInstance(config.REQUEST_TIMEOUT, int)
        self.assertGreater(config.REQUEST_TIMEOUT, 0)

    def test_discovery_search_terms_exists(self):
        """Test that discovery search terms are available as a list."""
        self.assertTrue(hasattr(config, 'DISCOVERY_SEARCH_TERMS'))
        self.assertIsInstance(config.DISCOVERY_SEARCH_TERMS, list)

    def test_download_chunk_size_exists(self):
        """Test that download chunk size is defined."""
        self.assertTrue(hasattr(config, 'DOWNLOAD_CHUNK_SIZE'))
        self.assertIsInstance(config.DOWNLOAD_CHUNK_SIZE, int)
        self.assertGreater(config.DOWNLOAD_CHUNK_SIZE, 0)


class TestConfigDefaults(unittest.TestCase):
    """Test configuration default values."""

    def test_default_id_column(self):
        """Test default ID column has correct spacing."""
        # Default column name for Pure IDs
        self.assertEqual(config.ID_COLUMN, "Pure ID")

    def test_default_output_directory(self):
        """Test default output directory."""
        self.assertEqual(config.OUTPUT_DIRECTORY, "downloads")

    def test_default_download_file_types(self):
        """Test download file types configuration is a list of extensions."""
        self.assertIsInstance(config.DOWNLOAD_FILE_TYPES, list)
        for item in config.DOWNLOAD_FILE_TYPES:
            self.assertTrue(item.startswith('.'))

    def test_default_request_timeout(self):
        """Test request timeout is positive and not absurdly low."""
        self.assertGreaterEqual(config.REQUEST_TIMEOUT, 10)
        self.assertLessEqual(config.REQUEST_TIMEOUT, 600)

    def test_default_chunk_size(self):
        """Test default chunk size is reasonable."""
        # Common chunk sizes are 4KB, 8KB, or 16KB
        self.assertIn(config.DOWNLOAD_CHUNK_SIZE, [4096, 8192, 16384])


class TestEnvironmentLoading(unittest.TestCase):
    """Test that config can load values from a local .env file."""

    def test_env_file_override_is_loaded(self):
        env_content = (
            "PURE_API_KEY=env-api-key-12345\n"
            "BASE_API_URL=https://env.elsevierpure.com/ws/api\n"
            "DISCOVERY_SEARCH_TERMS=carbon,remote sensing\n"
            "APPROVED_DOWNLOAD_PILOT_SIZE=12\n"
        )

        with patch.dict(os.environ, {"PURE_DOWNLOADER_ENV_PATH": "test.env"}, clear=True):
            with patch("pathlib.Path.exists", return_value=True), patch(
                "pathlib.Path.read_text",
                return_value=env_content,
            ):
                reloaded = importlib.reload(config)

        self.assertEqual(reloaded.PURE_API_KEY, "env-api-key-12345")
        self.assertEqual(reloaded.BASE_API_URL, "https://env.elsevierpure.com/ws/api")
        self.assertEqual(reloaded.DISCOVERY_SEARCH_TERMS, ["carbon", "remote sensing"])
        self.assertEqual(reloaded.APPROVED_DOWNLOAD_PILOT_SIZE, 12)

        importlib.reload(config)


if __name__ == '__main__':
    unittest.main(verbosity=2)
