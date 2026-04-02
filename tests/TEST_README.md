# Test suite guide

This repository now focuses on the staged workflow rather than the retired direct downloader.

## Current test modules

| Module | Purpose |
|--------|---------|
| `test_config.py` | configuration loading and validation |
| `test_setup_config.py` | interactive `.env` setup flow |
| `test_pure_api_utils.py` | shared logging and API validation helpers |
| `test_pure_discovery.py` | discovery workflow and review artifact generation |
| `test_pure_approved_downloader.py` | approved download workflow and checkpointing |

## Run all tests

```text
python tests/run_tests.py all
```

## Run one suite

```text
python tests/run_tests.py config
python tests/run_tests.py setup
python tests/run_tests.py api
python tests/run_tests.py discovery
python tests/run_tests.py approved
```

## Why the suite is smaller now

The old direct downloader path has been retired, so its dedicated tests were removed as part of the simplification work.

That keeps the suite aligned with the supported workflow and makes maintenance easier.
