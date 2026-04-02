"""Tests for setup_config.py."""

import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import mock_open, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import setup_config


class TestSetupConfiguration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, ".env")
        self.env_patcher = patch.dict(os.environ, {"PURE_DOWNLOADER_ENV_PATH": self.env_file})
        self.env_patcher.start()
        self.env_content = "\n".join(
            [
                "PURE_API_KEY=test-api-key",
                "BASE_API_URL=https://test.elsevierpure.com/ws/api",
                "DISCOVERY_SEARCH_TERMS=forest genetics,wood quality",
                "APPROVED_DOWNLOAD_PILOT_SIZE=25",
            ]
        )

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)

    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_setup_configuration_keep_current(self, mock_file, mock_exists, mock_print, mock_input):
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.env_content
        mock_input.side_effect = ["", "", "", "", "n"]

        result = setup_config.setup_configuration()

        self.assertFalse(result)

    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_setup_configuration_new_api_key(self, mock_file, mock_exists, mock_print, mock_input):
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.env_content
        mock_input.side_effect = ["new-api-key-12345", "", "", "", "y"]

        self.assertTrue(setup_config.setup_configuration())

    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_setup_configuration_new_search_terms(self, mock_file, mock_exists, mock_print, mock_input):
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.env_content
        mock_input.side_effect = ["", "", "carbon,remote sensing", "", "y"]

        self.assertTrue(setup_config.setup_configuration())

    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists")
    def test_setup_configuration_missing_env_creates_new(self, mock_exists, mock_print, mock_input):
        mock_exists.return_value = False
        mock_input.side_effect = [
            "new-api-key-12345",
            "https://test.elsevierpure.com/ws/api",
            "carbon,remote sensing",
            "10",
            "y",
        ]

        self.assertTrue(setup_config.setup_configuration())

    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open)
    def test_setup_configuration_invalid_pilot_size(self, mock_file, mock_exists, mock_print, mock_input):
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = self.env_content
        mock_input.side_effect = ["", "", "", "invalid", "y"]

        self.assertTrue(setup_config.setup_configuration())

    @patch("builtins.print")
    @patch("os.path.exists")
    @patch("builtins.open", new_callable=mock_open, read_data='PURE_API_KEY=test')
    def test_setup_configuration_exception(self, mock_file, mock_exists, mock_print):
        mock_exists.return_value = True
        mock_file.side_effect = [Exception("File error")]

        self.assertFalse(setup_config.setup_configuration())


class TestValidateCurrentConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, ".env")
        self.env_patcher = patch.dict(os.environ, {"PURE_DOWNLOADER_ENV_PATH": self.env_file})
        self.env_patcher.start()
        self.original_path = sys.path.copy()

    def tearDown(self):
        self.env_patcher.stop()
        sys.path = self.original_path
        shutil.rmtree(self.temp_dir)

    @patch("os.path.exists")
    def test_validate_current_config_missing_file(self, mock_exists):
        mock_exists.return_value = False
        is_valid, message = setup_config.validate_current_config()
        self.assertFalse(is_valid)
        self.assertIn("not found", message)

    @patch("os.path.exists")
    @patch("sys.path", new_callable=list)
    def test_validate_current_config_import_error(self, mock_path, mock_exists):
        mock_exists.return_value = True
        with patch("builtins.__import__", side_effect=ImportError("Cannot import config")):
            is_valid, message = setup_config.validate_current_config()
            self.assertFalse(is_valid)
            self.assertIn("Error loading config", message)

    @patch("setup_config.get_env_file_path")
    def test_validate_current_config_generic_error(self, mock_get_env_path):
        mock_get_env_path.side_effect = Exception("Generic error")
        is_valid, message = setup_config.validate_current_config()
        self.assertFalse(is_valid)
        self.assertIn("Error", message)


class TestConfigFileOperations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = os.path.join(self.temp_dir, ".env")
        self.env_patcher = patch.dict(os.environ, {"PURE_DOWNLOADER_ENV_PATH": self.env_file})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()
        shutil.rmtree(self.temp_dir)

    @patch("builtins.open", new_callable=mock_open, read_data="PURE_API_KEY=test-key")
    @patch("os.path.exists", return_value=True)
    def test_config_read_operations(self, mock_exists, mock_file):
        with patch("setup_config.input", side_effect=["new-key", "", "", "", "y"]):
            with patch("builtins.print"):
                setup_config.setup_configuration()
        mock_file.assert_any_call(self.env_file, "r", encoding="utf-8")

    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=mock_open)
    def test_config_write_operations(self, mock_file, mock_exists):
        mock_file.return_value.read.return_value = "PURE_API_KEY=test-key"
        with patch("setup_config.input", side_effect=["new-key", "", "", "", "y"]):
            with patch("builtins.print"):
                setup_config.setup_configuration()
        mock_file().write.assert_called()


class TestUserInputHandling(unittest.TestCase):
    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="PURE_API_KEY=test\nBASE_API_URL=https://test.elsevierpure.com/ws/api\nDISCOVERY_SEARCH_TERMS=topic one\nAPPROVED_DOWNLOAD_PILOT_SIZE=25",
    )
    def test_url_validation_warnings(self, mock_file, mock_exists, mock_print, mock_input):
        mock_input.side_effect = ["", "http://test.com/ws/api", "", "", "n"]
        setup_config.setup_configuration()
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("https://" in call.lower() for call in calls))

    @patch("setup_config.input")
    @patch("builtins.print")
    @patch("os.path.exists", return_value=True)
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="PURE_API_KEY=test\nBASE_API_URL=https://test.elsevierpure.com/ws/api\nDISCOVERY_SEARCH_TERMS=topic one\nAPPROVED_DOWNLOAD_PILOT_SIZE=25",
    )
    def test_url_validation_ending(self, mock_file, mock_exists, mock_print, mock_input):
        mock_input.side_effect = ["", "https://test.com/api", "", "", "n"]
        setup_config.setup_configuration()
        calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("/ws/api" in call for call in calls))


if __name__ == "__main__":
    unittest.main(verbosity=2)
