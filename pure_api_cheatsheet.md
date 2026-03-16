# Pure API Cheatsheet

A concise reference for this repository's Pure API workflows.

## Core ideas

- Research outputs are fetched from `research-outputs`
- File metadata is typically embedded in `electronicVersions`
- Open/downloadable files are detected from `accessType` plus file extension
- The staged workflow is:
  1. search with keywords
  2. generate a review CSV
  3. edit/review the CSV
  4. download approved rows

## Important endpoints

- `GET /ws/api/research-outputs`
  - keyword search
- `GET /ws/api/research-outputs/{id_or_uuid}`
  - fetch a single research output and its `electronicVersions`
- `GET /ws/api/research-outputs/{uuid}/files/{fileId}/{filename}`
  - download a file

## Repository scripts

- `pure_discovery.py`
  - keyword-based discovery and review CSV generation
- `pure_approved_downloader.py`
  - approved/proceed downloader with checkpointing
- `download_pure_file.py`
  - direct downloader for a CSV with a `Pure ID` column
- `setup_config.py`
  - interactive configuration helper

## Common file outputs

- `discovery_candidates.csv`
- `discovery_summary.md`
- `approved_candidates.csv`
- `approved_download_checkpoint.json`
- `downloads/approved_pilot/`

These are generated artifacts and are ignored by git.

## Typical usage

### Discovery

```text
python pure_discovery.py
```

### Approved download

```text
python pure_approved_downloader.py
```

### Direct CSV download

```text
python download_pure_file.py
```

## Notes

- Numeric Pure IDs can often be queried directly
- Prefer review-first discovery before bulk downloading
- Keep `config.py` local because it contains secrets
