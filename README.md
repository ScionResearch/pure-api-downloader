# Pure API research output workflow

This repository provides a **simple staged workflow** for finding and downloading research outputs from Elsevier Pure.

The workflow is intentionally designed for **semi-technical users**:

1. search the API with configured terms
2. generate a review CSV
3. review or edit that CSV
4. download only the approved results

## Why this workflow exists

The repository no longer depends on the old direct downloader.

That older approach was more error-prone because it skipped the human review step.
The current workflow is simpler, safer, and easier to explain.

## Quick start

1. Copy `.env.example` to `.env`
2. Edit `.env` with your local settings
3. Set `DISCOVERY_SEARCH_TERMS` to a comma-separated list of keywords or phrases
4. Run the setup helper if you prefer prompts:
   - `python setup_config.py`
5. Run discovery:
   - `python pure_discovery.py`
6. Review `discovery_candidates.csv`
7. Run the approved downloader:
   - `python pure_approved_downloader.py`

## Main configuration values

The main local configuration file is `.env`.

The values most users need are:

- `PURE_API_KEY`
- `BASE_API_URL`
- `DISCOVERY_SEARCH_TERMS`
- `APPROVED_DOWNLOAD_PILOT_SIZE`

### Search terms in `.env`

Search terms are provided as a comma-separated list.

Example:

```text
DISCOVERY_SEARCH_TERMS=carbon sequestration,biosecurity,remote sensing
```

This is simpler than editing Python dictionaries or grouped keyword maps.
If more advanced grouping is ever needed later, it can be added without changing the normal user workflow.

## Key files

- `.env` — local machine-specific settings
- `.env.example` — safe setup template
- `config.py` — loads and validates settings from `.env`
- `setup_config.py` — interactive setup helper
- `pure_api_utils.py` — shared API and logging helpers
- `pure_discovery.py` — discovery and review CSV generation
- `pure_approved_downloader.py` — approved/proceed downloader with checkpointing
- `docs/how_the_tool_works.md` — plain-language explanation of what happens at each step

## Generated files

These are runtime artifacts, not source files:

- `discovery_candidates.csv`
- `discovery_summary.md`
- `approved_candidates.csv`
- `approved_download_checkpoint.json`
- `downloads/approved_pilot/`

## Lean repository guidance

Safe files to remove when they are only generated outputs:

- anything under `downloads/`
- generated review CSVs and summaries
- checkpoint files

Files that are worth keeping:

- `.env.example`
- `docs/how_the_tool_works.md`
- `pure_api_cheatsheet.md`
- `tests/TEST_README.md`

## Testing

Run all tests:

```text
python tests/run_tests.py all
```

Run a specific suite:

```text
python tests/run_tests.py discovery
python tests/run_tests.py approved
python tests/run_tests.py api
```

## Security

- keep `.env` local
- do not commit real API credentials
- review results before downloading approved files

## More detail

- `docs/how_the_tool_works.md`
- `pure_api_cheatsheet.md`
