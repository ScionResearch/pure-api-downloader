# Pure API Research Output Workflow

This repository now supports a staged workflow for working with Elsevier Pure research outputs:

1. **search the API with keywords**
2. **generate a review CSV**
3. **edit that CSV if needed**
4. **download files from the reviewed/approved CSV**

It still includes the original direct CSV downloader, but the primary workflow is now the safer discovery → review → download pipeline.

## What the codebase does

- Search Pure research outputs by keyword
- Enrich each result with file metadata from `electronicVersions`
- Generate a CSV you can inspect and edit
- Generate a summary markdown report for quick review
- Download approved PDF files from the reviewed CSV
- Resume interrupted download runs using a checkpoint file
- Skip already downloaded files safely on reruns
- Fall back to the original “download from a CSV of Pure IDs” workflow when needed

## Main workflow

### 1. Configure the project

Use the interactive setup helper:

```bash
python setup_config.py
```

Or edit `config.py` directly.

Important settings in `config.py`:

- `PURE_API_KEY`
- `BASE_API_URL`
- `DISCOVERY_KEYWORD_THEMES`
- `DISCOVERY_PAGE_SIZE`
- `DISCOVERY_MAX_RESULTS_PER_KEYWORD`
- `DISCOVERY_OUTPUT_CSV`
- `DISCOVERY_SUMMARY_REPORT`
- `APPROVED_DOWNLOAD_INPUT_CSV`
- `APPROVED_DOWNLOAD_OUTPUT_DIR`
- `APPROVED_DOWNLOAD_CHECKPOINT_FILE`
- `APPROVED_DOWNLOAD_PILOT_SIZE`

### 2. Generate a discovery CSV from the API

Run the discovery workflow:

```bash
python pure_discovery.py
```

This will:

1. test API connectivity
2. search Pure using the configured keyword themes
3. deduplicate matches
4. enrich results with file metadata
5. classify results such as:
   - `downloadable_pdf`
   - `has_non_pdf_only`
   - `restricted_or_unknown_access`
   - `no_files`
6. write:
   - `discovery_candidates.csv`
   - `discovery_summary.md`

### 3. Edit the generated CSV

Open `discovery_candidates.csv` and review the rows.

Useful columns include:

- `title`
- `year`
- `output_type`
- `match_score`
- `matched_terms`
- `matched_fields`
- `download_status`
- `first_open_pdf_name`
- `first_open_pdf_url`
- `reviewer_decision`
- `reviewer_notes`

You can edit the CSV manually to:

- remove rows you don’t want
- add notes
- explicitly mark rows with `reviewer_decision=approve`

If you don’t mark approvals, the approved downloader can still proceed after explicit confirmation by treating all `downloadable_pdf` rows as the current proceed set.

### 4. Download files from the reviewed CSV

Run the approved downloader:

```bash
python pure_approved_downloader.py
```

This will:

1. read `approved_candidates.csv` if it exists
2. otherwise prepare it from `discovery_candidates.csv`
3. download up to `APPROVED_DOWNLOAD_PILOT_SIZE` items
4. save files into `downloads/approved_pilot`
5. track state in `approved_download_checkpoint.json`

On reruns it will:

- skip completed items already in the checkpoint
- skip existing files when configured to do so
- resume cleanly after interruption

## Alternative workflow: direct Pure ID CSV download

If you already have a CSV containing a `Pure ID` column, you can still use the original downloader:

```bash
python download_pure_file.py
```

That workflow:

- loads a CSV of Pure IDs
- detects whether IDs resolve as research outputs
- fetches `electronicVersions`
- downloads the first suitable file it finds

This is useful for targeted downloads, but for large discovery work the newer staged workflow is strongly recommended.

## Current key files

- `config.py` — live configuration
- `config.template.py` — starter template
- `setup_config.py` — interactive config helper
- `pure_discovery.py` — keyword search and review CSV generation
- `pure_approved_downloader.py` — approved/proceed download workflow with checkpointing
- `download_pure_file.py` — original Pure ID downloader
- `discovery_candidates.csv` — generated discovery CSV
- `discovery_summary.md` — generated summary report
- `approved_candidates.csv` — prepared approved/proceed CSV
- `approved_download_checkpoint.json` — resumable download checkpoint
- `downloads/approved_pilot/` — downloaded pilot files

## Example commands

### Run discovery with configured keywords

```bash
python pure_discovery.py
```

### Run discovery with a temporary focused keyword set

```bash
python -c "import pure_discovery as d; print(d.run_discovery_workflow(keyword_themes={'focus':['decay','durability','cypress']}))"
```

### Run the approved pilot downloader

```bash
python pure_approved_downloader.py
```

### Continue past the pilot size

```bash
python -c "import pure_approved_downloader as p; print(p.run_approved_download_pilot(pilot_size=257))"
```

### Use the original direct CSV downloader

```bash
python download_pure_file.py
```

## Manual configuration reference

If you prefer not to use the interactive setup helper:

1. Copy the template:
   ```bash
   copy config.template.py config.py
   ```
2. Edit `config.py` with your settings.

Minimal example:

```python
PURE_API_KEY = "your-api-key-here"
BASE_API_URL = "https://yourinstitution.elsevierpure.com/ws/api"
CSV_FILE_PATH = "example.csv"
MAX_DOWNLOADS = None
```

### Common configuration options

| Setting | Description | Default |
|---------|-------------|---------|
| `PURE_API_KEY` | Your Pure API key | *Required* |
| `BASE_API_URL` | Your Pure API endpoint | *Required* |
| `CSV_FILE_PATH` | Path to CSV with Pure IDs | `"your_file.csv"` |
| `ID_COLUMN` | CSV column with IDs | `"Pure ID"` |
| `OUTPUT_DIRECTORY` | Where to save files | `"downloads"` |
| `MAX_DOWNLOADS` | Limit for testing | `None` |
| `DOWNLOAD_FILE_TYPES` | Direct-download file filter | configured in `config.py` |
| `REQUEST_TIMEOUT` | Request timeout in seconds | configured in `config.py` |
| `DOWNLOAD_CHUNK_SIZE` | Streaming chunk size | `8192` |

## CSV format for the direct downloader

Your direct-download CSV should contain a `Pure ID` column.

```csv
Pure ID,Title,Year
27139086,"Forest Protection Research",2023
46773789,"Cypress Stakes Study",2022
14344978,"Genetic Resources",2021
```

Supported ID formats:

- numeric Pure IDs such as `27139086`
- UUIDs such as `12345678-1234-5678-1234-567812345678`

## Direct downloader notes

The original downloader still:

1. accepts numeric Pure IDs or UUIDs
2. extracts files from `electronicVersions`
3. streams downloads in chunks
4. saves files using sanitized titles and original extensions

## Configuration notes

### Discovery settings

- `DISCOVERY_KEYWORD_THEMES` controls what gets searched
- `DISCOVERY_PAGE_SIZE` controls API page size
- `DISCOVERY_MAX_RESULTS_PER_KEYWORD` caps search breadth
- `DISCOVERY_ALLOWED_ACCESS_TYPES` determines what counts as safe/open for download

### Approved download settings

- `APPROVED_DOWNLOAD_PILOT_SIZE` controls the default number downloaded per run
- `APPROVED_DOWNLOAD_RETRY_ATTEMPTS` controls retries
- `APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS` controls retry delay
- `APPROVED_DOWNLOAD_SKIP_EXISTING` prevents duplicate file writes

## Testing

Run everything:

```bash
cd tests
python run_tests.py all
```

Run the discovery tests only:

```bash
cd tests
python run_tests.py discovery
```

Run the approved downloader tests only:

```bash
cd tests
python run_tests.py approved
```

Run the direct downloader tests only:

```bash
cd tests
python run_tests.py download
```

## Troubleshooting

### API connection problems

- confirm `PURE_API_KEY`
- confirm `BASE_API_URL` ends with `/ws/api`
- check network access to the Pure instance

### Discovery is too broad

- reduce `DISCOVERY_MAX_RESULTS_PER_KEYWORD`
- narrow `DISCOVERY_KEYWORD_THEMES`
- use more specific terms such as `decay`, `stakes`, `decking`, `heartwood`

### Downloads stop midway

- rerun `pure_approved_downloader.py`
- it will resume using `approved_download_checkpoint.json`

### Wrong files are being prioritized

- adjust keyword themes
- inspect `matched_terms`, `match_score`, and `download_status` in the discovery CSV

## Security

- `config.py` contains secrets and should not be committed
- keep API credentials local
- review discovery results before bulk downloading when possible

## Resources

- `pure_api_cheatsheet.md`

---

**Status:** Active workflow: search → review CSV → approved/proceed download  
**Repository:** `pure-api-downloader`
