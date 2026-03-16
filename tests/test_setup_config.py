"""
Test suite for setup_config.py

Tests interactive configuration setup functionality.
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, mock_open, Mock, MagicMock
from io import StringIO

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import setup_config


class TestSetupConfiguration(unittest.TestCase):
    """Test setup_configuration function."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'config.py')
        self.env_patcher = patch.dict(os.environ, {'PURE_DOWNLOADER_CONFIG_PATH': self.config_file})
        self.env_patcher.start()
        
        # Create a minimal config.py for testing
        self.config_content = '''
PURE_API_KEY = "test-api-key"
BASE_API_URL = "https://test.elsevierpure.com/ws/api"
CSV_FILE_PATH = "test.csv"
ID_COLUMN = "Pure ID"
OUTPUT_DIRECTORY = "downloads"
MAX_DOWNLOADS = 3
'''

    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_configuration_keep_current(self, mock_file, mock_exists, mock_print, mock_input):
        """Test setup when keeping current configuration."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.config_content
        mock_input.side_effect = ['', '', '', '', 'n']  # Keep all, then cancel
        
        result = setup_config.setup_configuration()
        
        self.assertFalse(result)  # Cancelled, so returns False

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_configuration_new_api_key(self, mock_file, mock_exists, mock_print, mock_input):
        """Test setup with new API key."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.config_content
        
        # Provide new API key, keep others, then apply
        mock_input.side_effect = [
            'new-api-key-12345',  # New API key
            '',  # Keep base URL
            '',  # Keep CSV file
            '',  # Keep max downloads
            'y'  # Apply changes
        ]
        
        result = setup_config.setup_configuration()
        
        self.assertTrue(result)

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_configuration_new_base_url(self, mock_file, mock_exists, mock_print, mock_input):
        """Test setup with new base URL."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.config_content
        
        mock_input.side_effect = [
            '',  # Keep API key
            'https://neworg.elsevierpure.com/ws/api',  # New URL
            '',  # Keep CSV file
            '',  # Keep max downloads
            'y'  # Apply
        ]
        
        result = setup_config.setup_configuration()
        
        self.assertTrue(result)

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    def test_setup_configuration_missing_config(self, mock_exists, mock_print, mock_input):
        """Test setup when config.py doesn't exist."""
        mock_exists.return_value = False
        
        result = setup_config.setup_configuration()
        
        self.assertFalse(result)
        # Should print error about missing config.py
        mock_print.assert_any_call("❌ Error: config.py not found in current directory")

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_configuration_max_downloads_all(self, mock_file, mock_exists, mock_print, mock_input):
        """Test setup with max downloads set to 'all'."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.config_content
        
        mock_input.side_effect = [
            '',  # Keep API key
            '',  # Keep base URL
            '',  # Keep CSV file
            'all',  # Set to download all
            'y'  # Apply
        ]
        
        result = setup_config.setup_configuration()
        
        self.assertTrue(result)

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_configuration_max_downloads_numeric(self, mock_file, mock_exists, mock_print, mock_input):
        """Test setup with numeric max downloads."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.config_content
        
        mock_input.side_effect = [
            '',  # Keep API key
            '',  # Keep base URL
            '',  # Keep CSV file
            '10',  # Set to 10
            'y'  # Apply
        ]
        
        result = setup_config.setup_configuration()
        
        self.assertTrue(result)

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_setup_configuration_invalid_max_downloads(self, mock_file, mock_exists, mock_print, mock_input):
        """Test setup with invalid max downloads input."""
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.config_content
        
        mock_input.side_effect = [
            '',  # Keep API key
            '',  # Keep base URL
            '',  # Keep CSV file
            'invalid',  # Invalid input
            'y'  # Apply
        ]
        
        result = setup_config.setup_configuration()
        
        self.assertTrue(result)

    @patch('builtins.print')
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='PURE_API_KEY = "old-key"')
    def test_setup_configuration_exception(self, mock_file, mock_exists, mock_print):
        """Test setup when an exception occurs."""
        mock_exists.return_value = True
        mock_file.side_effect = [Exception("File error")]
        
        result = setup_config.setup_configuration()
        
        self.assertFalse(result)


class TestValidateCurrentConfig(unittest.TestCase):
    """Test validate_current_config function."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_path = sys.path.copy()
        self.config_file = os.path.join(self.temp_dir, 'config.py')
        self.env_patcher = patch.dict(os.environ, {'PURE_DOWNLOADER_CONFIG_PATH': self.config_file})
        self.env_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        sys.path = self.original_path

    @patch('os.path.exists')
    def test_validate_current_config_missing_file(self, mock_exists):
        """Test validation when config.py doesn't exist."""
        mock_exists.return_value = False
        
        is_valid, message = setup_config.validate_current_config()
        
        self.assertFalse(is_valid)
        self.assertIn("not found", message)

    @patch('os.path.exists')
    @patch('sys.path', new_callable=list)
    def test_validate_current_config_import_error(self, mock_path, mock_exists):
        """Test validation when config import fails."""
        mock_exists.return_value = True
        # Mock import to fail
        with patch('builtins.__import__', side_effect=ImportError("Cannot import config")):
            is_valid, message = setup_config.validate_current_config()
            
            self.assertFalse(is_valid)
            self.assertIn("Error loading config", message)

    @patch('os.path.exists')
    @patch('setup_config.get_config_file_path')
    def test_validate_current_config_generic_error(self, mock_get_config_path, mock_exists):
        """Test validation with generic error."""
        mock_get_config_path.side_effect = Exception("Generic error")
        
        is_valid, message = setup_config.validate_current_config()
        
        self.assertFalse(is_valid)
        self.assertIn("Error", message)


class TestConfigFileOperations(unittest.TestCase):
    """Test configuration file read/write operations."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'config.py')
        self.env_patcher = patch.dict(os.environ, {'PURE_DOWNLOADER_CONFIG_PATH': self.config_file})
        self.env_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('builtins.open', new_callable=mock_open, read_data='PURE_API_KEY = "old-key"')
    @patch('os.path.exists', return_value=True)
    def test_config_read_operations(self, mock_exists, mock_file):
        """Test reading configuration file."""
        with patch('setup_config.input', side_effect=['new-key', '', '', '', 'y']):
            with patch('builtins.print'):
                setup_config.setup_configuration()
                
        # Verify file was read
        mock_file.assert_any_call(self.config_file, 'r', encoding='utf-8')

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open)
    def test_config_write_operations(self, mock_file, mock_exists):
        """Test writing configuration file."""
        mock_file.return_value.read.return_value = 'PURE_API_KEY = "old-key"'
        
        with patch('setup_config.input', side_effect=['new-key', '', '', '', 'y']):
            with patch('builtins.print'):
                setup_config.setup_configuration()
        
        # Verify file was written
        # Check that write was called
        handle = mock_file()
        handle.write.assert_called()


class TestUserInputHandling(unittest.TestCase):
    """Test user input handling."""

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='PURE_API_KEY = "test"\nBASE_API_URL = "https://test.elsevierpure.com/ws/api"\nCSV_FILE_PATH = "test.csv"\nMAX_DOWNLOADS = 3')
    def test_url_validation_warnings(self, mock_file, mock_exists, mock_print, mock_input):
        """Test URL validation warnings."""
        # Test HTTP instead of HTTPS
        mock_input.side_effect = [
            '',  # Keep API key
            'http://test.com/ws/api',  # HTTP URL (should warn)
            '',
            '',
            'n'  # Cancel
        ]
        
        setup_config.setup_configuration()
        
        # Should print warning about HTTPS
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('https://' in str(call).lower() for call in calls))

    @patch('setup_config.input')
    @patch('builtins.print')
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', new_callable=mock_open, read_data='PURE_API_KEY = "test"\nBASE_API_URL = "https://test.elsevierpure.com/ws/api"\nCSV_FILE_PATH = "test.csv"\nMAX_DOWNLOADS = 3')
    def test_url_validation_ending(self, mock_file, mock_exists, mock_print, mock_input):
        """Test URL ending validation."""
        mock_input.side_effect = [
            '',  # Keep API key
            'https://test.com/api',  # Missing /ws/api
            '',
            '',
            'n'  # Cancel
        ]
        
        setup_config.setup_configuration()
        
        # Should print warning about /ws/api
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any('/ws/api' in str(call) for call in calls))


if __name__ == '__main__':
    unittest.main(verbosity=2)
