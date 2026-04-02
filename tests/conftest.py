"""Pytest configuration and shared fixtures for the staged Pure workflows."""

import pytest
import tempfile
import os
import sys
import shutil
import csv
from unittest.mock import Mock, patch

# Ensure project root is on sys.path so 'pure_downloader' is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import the shared helper module used by the staged workflows
from pure_downloader import pure_api_utils


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_api_config():
    """Mock API configuration for testing."""
    test_config = {
        "api_key": "test-api-key-12345",
        "base_url": "https://test.elsevierpure.com/ws/api",
    }

    with patch.object(pure_api_utils.config, "PURE_API_KEY", test_config["api_key"]):
        with patch.object(pure_api_utils.config, "BASE_API_URL", test_config["base_url"]):
            yield test_config


@pytest.fixture
def sample_csv_data():
    """Sample CSV data for testing."""
    return [
        ["Year", "Title", "Pure ID"],
        ["2020", "Test Paper 1", "12345"],
        ["2021", "Test Paper 2", "67890"],
        ["2022", "Test Paper 3", "11111"],
    ]


@pytest.fixture
def create_test_csv(temp_dir):
    """Factory function to create test CSV files."""

    def _create_csv(data, filename="test.csv"):
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(data)
        return filepath

    return _create_csv


@pytest.fixture
def mock_http_response():
    """Factory function to create mock HTTP responses."""

    def _create_response(status_code=200, json_data=None, headers=None, content=None):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        mock_response.headers = headers or {}
        mock_response.text = str(json_data) if json_data else ""

        if content:
            mock_response.iter_content.return_value = [content]

        return mock_response

    return _create_response


@pytest.fixture
def sample_pure_files():
    """Sample Pure API files response."""
    return {
        "items": [
            {
                "uuid": "file1-uuid-here",
                "fileName": "document.pdf",
                "size": 1024000,
                "mimeType": "application/pdf",
                "created": "2023-01-01T00:00:00Z",
            },
            {
                "uuid": "file2-uuid-here",
                "fileName": "spreadsheet.xlsx",
                "size": 512000,
                "mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "created": "2023-01-02T00:00:00Z",
            },
        ]
    }


@pytest.fixture
def sample_research_output():
    """Sample Pure API research output response."""
    return {
        "uuid": "123e4567-e89b-12d3-a456-426614174000",
        "title": {"value": "Sample Research Output Title"},
        "type": {"term": {"text": "Article"}},
        "publicationYear": {"value": "2023"},
        "abstract": {"value": "This is a sample abstract for testing purposes."},
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")


# Custom pytest options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="Run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on options."""
    if config.getoption("--run-slow"):
        # Don't skip slow tests
        return

    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
