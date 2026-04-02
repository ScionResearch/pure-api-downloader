"""Tests for shared helpers in pure_api_utils.py."""

import os
import sys
import unittest
from unittest.mock import Mock, patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pure_api_utils


class TestApiUtils(unittest.TestCase):
    def test_check_api_key_valid(self):
        self.assertTrue(pure_api_utils.check_api_key("valid-api-key-123"))

    def test_check_api_key_placeholder(self):
        with patch("pure_api_utils.log_debug"):
            self.assertFalse(pure_api_utils.check_api_key("YOUR_API_KEY"))

    def test_validate_base_url_valid(self):
        self.assertTrue(pure_api_utils.validate_base_url("https://test.elsevierpure.com/ws/api"))

    def test_validate_base_url_empty(self):
        with patch("pure_api_utils.log_debug"):
            self.assertFalse(pure_api_utils.validate_base_url(""))

    def test_test_api_connection_success(self):
        mock_response = Mock(status_code=200)
        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("pure_api_utils.log_debug"):
            result = pure_api_utils.test_api_connection(
                http_client=mock_http,
                api_key="test-api-key-12345",
                base_api_url="https://test.elsevierpure.com/ws/api",
            )

        self.assertTrue(result)

    def test_test_api_connection_failure(self):
        mock_response = Mock(status_code=401)
        mock_http = Mock()
        mock_http.get.return_value = mock_response

        with patch("pure_api_utils.log_debug"):
            result = pure_api_utils.test_api_connection(
                http_client=mock_http,
                api_key="test-api-key-12345",
                base_api_url="https://test.elsevierpure.com/ws/api",
            )

        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
