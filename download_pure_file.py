"""
Legacy compatibility entry point
================================

The repository now uses a staged workflow:

1. run `pure_discovery.py`
2. review the generated CSV
3. run `pure_approved_downloader.py`

The old direct downloader is intentionally retired so the tool stays simpler and
safer for semi-technical users.

This file remains only as a lightweight compatibility module during the
transition. Shared helper functions are re-exported from `pure_api_utils` so
older imports do not fail immediately.
"""

from pure_api_utils import check_api_key, log_debug, test_api_connection, validate_base_url


DEPRECATION_MESSAGE = (
    "The direct downloader workflow has been retired. "
    "Use `python pure_discovery.py` followed by `python pure_approved_downloader.py`."
)


def main() -> int:
    print(DEPRECATION_MESSAGE)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
