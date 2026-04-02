"""
Shared Pure API helpers
=======================

This module holds the small set of helper functions that are shared by the
staged workflows.

Why this file exists:
- `pure_discovery.py` and `pure_approved_downloader.py` both need the same
  logging and API validation helpers
- keeping those helpers here avoids importing a retired workflow module
- this keeps the project simpler now that the direct downloader is no longer
  the preferred or required path
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import requests

try:
    import config
except ImportError as exc:  # pragma: no cover - matches repo style
    raise SystemExit("config.py not found. Please create or configure it first.") from exc


DEFAULT_OBJECT_TYPE = getattr(config, "DEFAULT_OBJECT_TYPE", "research-outputs")
REQUEST_TIMEOUT = getattr(config, "REQUEST_TIMEOUT", 30)


def log_debug(message: str, level: str = "INFO") -> None:
    """Print a timestamped log message using safe ASCII output when needed."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except UnicodeEncodeError:
        safe_message = message.encode("ascii", "replace").decode("ascii")
        print(f"[{timestamp}] [{level}] {safe_message}")


def check_api_key(api_key: Optional[str], verbose: bool = True) -> bool:
    """Return True when an API key looks usable enough to try a request."""
    if verbose:
        log_debug("Checking API key validity...")

    if not api_key:
        if verbose:
            log_debug("Error: PURE_API_KEY is empty or None", "ERROR")
        return False
    if api_key == "YOUR_API_KEY":
        if verbose:
            log_debug(
                "Error: PURE_API_KEY is still the placeholder value 'YOUR_API_KEY'",
                "ERROR",
            )
        return False
    if len(api_key) < 10:
        if verbose:
            log_debug(
                f"Warning: API key seems short (length: {len(api_key)}). This might not be valid.",
                "WARNING",
            )
    if verbose:
        log_debug(f"API key appears valid (length: {len(api_key)})")
    return True


def validate_base_url(base_url: str) -> bool:
    """Validate the expected Pure API base URL shape."""
    log_debug(f"Validating base URL: {base_url}")
    if not base_url:
        log_debug("Error: BASE_API_URL is empty", "ERROR")
        return False
    if not base_url.startswith("https://"):
        log_debug("Warning: BASE_API_URL should use HTTPS", "WARNING")
    if "elsevierpure.com" not in base_url:
        log_debug(
            "Warning: URL doesn't contain 'elsevierpure.com' - verify this is correct",
            "WARNING",
        )
    if not base_url.endswith("/ws/api"):
        log_debug(
            "Warning: URL should end with '/ws/api' for Pure API endpoints",
            "WARNING",
        )
    log_debug("Base URL validation complete")
    return True


def test_api_connection(
    http_client=requests,
    api_key: Optional[str] = None,
    base_api_url: Optional[str] = None,
    object_type: str = DEFAULT_OBJECT_TYPE,
) -> bool:
    """
    Test basic connectivity to the configured Pure API endpoint.

    The helper accepts explicit `api_key` and `base_api_url` values so the
    staged workflows can pass their module-level settings directly. That keeps
    unit tests simple and avoids hidden cross-module state.
    """
    resolved_api_key = api_key if api_key is not None else getattr(config, "PURE_API_KEY", "")
    resolved_base_api_url = (
        base_api_url if base_api_url is not None else getattr(config, "BASE_API_URL", "")
    )

    log_debug("=== Testing API Connection ===")

    if not check_api_key(resolved_api_key):
        return False

    test_url = f"{resolved_base_api_url}/{object_type}"
    headers = {
        "api-key": resolved_api_key,
        "Accept": "application/json",
        "User-Agent": "Pure-API-Client/1.0",
    }

    try:
        log_debug(f"Testing connection to: {test_url}")
        response = http_client.get(
            test_url,
            headers=headers,
            timeout=10,
            params={"size": 1},
        )

        log_debug(f"Test response status: {response.status_code}")

        if response.status_code == 200:
            log_debug("[OK] API connection test successful!")
            return True
        if response.status_code == 401:
            log_debug("[X] Authentication failed - check your API key", "ERROR")
        elif response.status_code == 403:
            log_debug("[X] Access forbidden - check API permissions", "ERROR")
        else:
            log_debug(f"[X] Unexpected response: {response.status_code}", "ERROR")

        return False

    except requests.exceptions.RequestException as exc:
        log_debug(f"[X] Connection test failed: {exc}", "ERROR")
        return False
