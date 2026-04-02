"""
Pure API Downloader Configuration
=================================

This module centralises configuration for the downloader workflows.

For day-to-day use, semi-technical users should edit the local `.env` file
rather than this Python module. The `.env` file is easier to understand,
safer for secrets, and keeps credentials out of source code.

What this module does:
- loads `.env` values into the process environment
- exposes strongly named Python constants used across the codebase
- validates required settings before workflows start

What this module does *not* do:
- prompt users for configuration interactively
- download data or call the Pure API directly

If `.env` is missing, the code falls back to safe placeholders so the project
can still be imported in tests and tooling without leaking real credentials.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE_PATH = Path(os.environ.get("PURE_DOWNLOADER_ENV_PATH", SCRIPT_DIR / ".env"))


def _strip_wrapping_quotes(value: str) -> str:
    """Remove matching surrounding quotes from `.env` values."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _load_env_file(file_path: Path) -> None:
    """
    Load simple KEY=VALUE pairs from a local `.env` file.

    We use a lightweight parser here so the project can bootstrap itself without
    requiring extra dependencies before the first install step.
    """
    if not file_path.exists():
        return

    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        cleaned_key = key.strip()
        if not cleaned_key:
            continue

        # `setdefault` lets real process environment variables override local
        # `.env` values. That is helpful in CI and scheduled runs.
        os.environ.setdefault(cleaned_key, _strip_wrapping_quotes(value.strip()))


def _get_env_str(name: str, default: str) -> str:
    return os.environ.get(name, default).strip()


def _get_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        return int(raw_value.strip())
    except ValueError:
        return default


def _get_env_optional_int(name: str, default: Optional[int]) -> Optional[int]:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"none", "all", ""}:
        return None

    try:
        return int(normalized)
    except ValueError:
        return default


def _get_env_list(name: str, default: Iterable[str]) -> list[str]:
    raw_value = os.environ.get(name)
    if raw_value is None or not raw_value.strip():
        return list(default)

    return [item.strip() for item in raw_value.split(",") if item.strip()]


_load_env_file(ENV_FILE_PATH)

# ============================================================================
# API AUTHENTICATION
# ============================================================================

# Your Pure API key (required).
# This should be set in `.env` or the process environment, not committed here.
PURE_API_KEY = _get_env_str("PURE_API_KEY", "YOUR_API_KEY")

# Your institution's Pure API base URL (required)
# Format: https://[institution].elsevierpure.com/ws/api
# Example: "https://scion.elsevierpure.com/ws/api"
BASE_API_URL = _get_env_str("BASE_API_URL", "https://yourinstitution.elsevierpure.com/ws/api")


# ============================================================================
# CSV FILE SETTINGS
# ============================================================================

# Path to your CSV file containing Pure IDs
# Can be relative to script directory or absolute path
# Example: "Pure research outputs - FGR check.csv"
CSV_FILE_PATH = _get_env_str("CSV_FILE_PATH", "your_file.csv")

# Name of the column in CSV that contains Pure IDs
# Must match exactly (case-sensitive)
# Example: "Pure ID"
ID_COLUMN = _get_env_str("ID_COLUMN", "Pure ID")


# ============================================================================
# DOWNLOAD SETTINGS
# ============================================================================

# Directory where downloaded files will be saved
# Will be created if it doesn't exist
# Example: "downloads"
OUTPUT_DIRECTORY = _get_env_str("OUTPUT_DIRECTORY", "downloads")

# Maximum number of entries to download from CSV
# Set to None to download all entries
# Set to a number (e.g., 3, 5, 10) for testing
# Example: 3 (for testing), None (for full download)
MAX_DOWNLOADS = _get_env_optional_int("MAX_DOWNLOADS", None)

# File types to download (checks file extension)
# Files matching these extensions will be downloaded
# Example: ['.pdf', '.docx', '.doc']
DOWNLOAD_FILE_TYPES = _get_env_list("DOWNLOAD_FILE_TYPES", [".pdf", ".docx", ".doc"])


# ============================================================================
# ADVANCED SETTINGS
# ============================================================================

# Request timeout in seconds for API calls
# Increase if you have slow network or large files
# Default: 300 (5 minutes)
REQUEST_TIMEOUT = _get_env_int("REQUEST_TIMEOUT", 300)

# Chunk size for streaming downloads (in bytes)
# Larger chunks = faster download but more memory usage
# Default: 8192 (8 KB)
DOWNLOAD_CHUNK_SIZE = _get_env_int("DOWNLOAD_CHUNK_SIZE", 8192)

# Maximum filename length (characters)
# Filenames longer than this will be truncated
# Default: 50
MAX_FILENAME_LENGTH = _get_env_int("MAX_FILENAME_LENGTH", 50)

# Log level for debugging
# Options: "DEBUG", "INFO", "WARNING", "ERROR"
# Default: "INFO"
LOG_LEVEL = _get_env_str("LOG_LEVEL", "INFO")


# ============================================================================
# OBJECT TYPE SETTINGS (Advanced - rarely needs changing)
# ============================================================================

# Type of Pure object to search for
# Usually "research-outputs" for documents/publications
# Other options: "persons", "organisational-units", "activities", "projects"
DEFAULT_OBJECT_TYPE = _get_env_str("DEFAULT_OBJECT_TYPE", "research-outputs")


# ============================================================================
# DISCOVERY / REVIEW SETTINGS
# ============================================================================

# Output CSV containing discovery candidates for manual review
DISCOVERY_OUTPUT_CSV = _get_env_str("DISCOVERY_OUTPUT_CSV", "discovery_candidates.csv")

# Markdown report summarizing discovery results
DISCOVERY_SUMMARY_REPORT = _get_env_str("DISCOVERY_SUMMARY_REPORT", "discovery_summary.md")

# CSV containing approved rows after manual review
DISCOVERY_APPROVED_OUTPUT_CSV = _get_env_str("DISCOVERY_APPROVED_OUTPUT_CSV", "approved_candidates.csv")

# Page size and result cap for discovery searches
DISCOVERY_PAGE_SIZE = _get_env_int("DISCOVERY_PAGE_SIZE", 25)
DISCOVERY_MAX_RESULTS_PER_KEYWORD = _get_env_int("DISCOVERY_MAX_RESULTS_PER_KEYWORD", 100)

# Primary discovery input. Users should provide a comma-separated list of search
# terms in `.env`, for example:
#   DISCOVERY_SEARCH_TERMS=carbon sequestration,biosecurity,remote sensing
DISCOVERY_SEARCH_TERMS = _get_env_list("DISCOVERY_SEARCH_TERMS", [])

# Conservative access types that are considered safe for automatic PDF download
DISCOVERY_ALLOWED_ACCESS_TYPES = _get_env_list(
    "DISCOVERY_ALLOWED_ACCESS_TYPES",
    ["open", "public", "free", "openaccess", "oa"],
)

# Backward-compatible internal structure used by the discovery workflow.
# Users only need to edit the flat DISCOVERY_SEARCH_TERMS list in `.env`.
DISCOVERY_KEYWORD_THEMES = (
    {"configured_terms": DISCOVERY_SEARCH_TERMS} if DISCOVERY_SEARCH_TERMS else {}
)


# ============================================================================
# APPROVED PILOT DOWNLOAD SETTINGS
# ============================================================================

APPROVED_DOWNLOAD_INPUT_CSV = _get_env_str("APPROVED_DOWNLOAD_INPUT_CSV", "approved_candidates.csv")
APPROVED_DOWNLOAD_OUTPUT_DIR = _get_env_str(
    "APPROVED_DOWNLOAD_OUTPUT_DIR",
    os.path.join("downloads", "approved_pilot"),
)
APPROVED_DOWNLOAD_CHECKPOINT_FILE = _get_env_str(
    "APPROVED_DOWNLOAD_CHECKPOINT_FILE",
    "approved_download_checkpoint.json",
)
APPROVED_DOWNLOAD_PILOT_SIZE = _get_env_int("APPROVED_DOWNLOAD_PILOT_SIZE", 25)
APPROVED_DOWNLOAD_RETRY_ATTEMPTS = _get_env_int("APPROVED_DOWNLOAD_RETRY_ATTEMPTS", 3)
APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS = _get_env_int(
    "APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS",
    1,
)
APPROVED_DOWNLOAD_SKIP_EXISTING = _get_env_str(
    "APPROVED_DOWNLOAD_SKIP_EXISTING",
    "true",
).lower() in {"1", "true", "yes", "y", "on"}


# ============================================================================
# VALIDATION
# ============================================================================

def validate_config():
    """
    Validate the currently loaded configuration settings.

    Returns:
        tuple[bool, str]: A success flag and a human-readable explanation.
    """
    errors = []
    
    # Check API key
    if not PURE_API_KEY or PURE_API_KEY == "YOUR_API_KEY":
        errors.append("API key not set or still using placeholder value")
    elif len(PURE_API_KEY) < 10:
        errors.append("PURE_API_KEY seems too short - check if it's correct")
    
    # Check Base URL
    if not BASE_API_URL:
        errors.append("BASE_API_URL is not set")
    elif "yourinstitution" in BASE_API_URL.lower():
        errors.append("BASE_API_URL contains placeholder 'yourinstitution'")
    elif not BASE_API_URL.startswith("https://"):
        errors.append("BASE_API_URL should use HTTPS and start with https://")
    elif not BASE_API_URL.endswith("/ws/api"):
        errors.append("BASE_API_URL should end with /ws/api")
    
    # Check timeouts
    if REQUEST_TIMEOUT <= 0:
        errors.append("REQUEST_TIMEOUT must be positive")
    
    if DOWNLOAD_CHUNK_SIZE <= 0:
        errors.append("DOWNLOAD_CHUNK_SIZE must be positive")

    if DISCOVERY_PAGE_SIZE <= 0:
        errors.append("DISCOVERY_PAGE_SIZE must be positive")

    if DISCOVERY_MAX_RESULTS_PER_KEYWORD <= 0:
        errors.append("DISCOVERY_MAX_RESULTS_PER_KEYWORD must be positive")

    if APPROVED_DOWNLOAD_PILOT_SIZE <= 0:
        errors.append("APPROVED_DOWNLOAD_PILOT_SIZE must be positive")

    if APPROVED_DOWNLOAD_RETRY_ATTEMPTS <= 0:
        errors.append("APPROVED_DOWNLOAD_RETRY_ATTEMPTS must be positive")

    if APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS < 0:
        errors.append("APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS cannot be negative")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "Configuration valid"


if __name__ == "__main__":
    # Test configuration when run directly
    is_valid, message = validate_config()
    
    if is_valid:
        print("✅ Configuration is valid!")
        print(f"\nSettings:")
        print(f"  API Key: {'*' * 10}...{PURE_API_KEY[-4:]} (length: {len(PURE_API_KEY)})")
        print(f"  Base URL: {BASE_API_URL}")
        print(f"  .env file: {ENV_FILE_PATH}")
        print(
            f"  Search Terms: {', '.join(DISCOVERY_SEARCH_TERMS) if DISCOVERY_SEARCH_TERMS else '(not set)'}"
        )
        print(f"  Approved Pilot Size: {APPROVED_DOWNLOAD_PILOT_SIZE}")
    else:
        print(f"❌ Configuration errors:")
        print(f"  {message}")
        exit(1)
