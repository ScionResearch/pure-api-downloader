# Pure API cheatsheet

A short reference for the current staged workflow.

## Main idea

The tool now works in two deliberate stages:

1. discovery and review preparation
2. approved download

This keeps the workflow simple and safer for semi-technical users.

## Important endpoints

- `GET /ws/api/research-outputs`
  - keyword search
- `GET /ws/api/research-outputs/{uuid}`
  - fetch a full research output including `electronicVersions`
- `GET /ws/api/research-outputs/{uuid}/files/{fileId}/{filename}`
  - download a file

## Main scripts

- `setup_config.py`
  - interactive `.env` setup
- `pure_discovery.py`
  - search the API and build review outputs
- `pure_approved_downloader.py`
  - download the approved results with checkpointing
- `pure_api_utils.py`
  - shared logging and API validation helpers

## Main local config

Use `.env` for local settings.

The most important value for search behavior is:

- `DISCOVERY_SEARCH_TERMS`

Example:

```text
DISCOVERY_SEARCH_TERMS=carbon sequestration,biosecurity,remote sensing
```

## Typical usage

### Discovery

```text
python pure_discovery.py
```

### Approved download

```text
python pure_approved_downloader.py
```

## Notes

- prefer the review-first discovery workflow before downloading files
- keep `.env` local because it contains secrets
- see `docs/how_the_tool_works.md` for the detailed explanation
