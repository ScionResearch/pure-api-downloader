# How the tool works

This document explains the staged workflow in plain language.

## Overview

The tool has one main purpose:

- find research outputs that match configured search terms
- prepare them for review
- download only the approved results

This repository intentionally avoids the old direct-download approach so the workflow stays easier to understand and safer to run.

## Configuration

Configuration comes from `.env`.

The most important setting is:

- `DISCOVERY_SEARCH_TERMS`

It is a comma-separated list of keywords or phrases.

Example:

```text
DISCOVERY_SEARCH_TERMS=carbon sequestration,biosecurity,remote sensing
```

This is the simplest configuration style for semi-technical users because it does not require editing Python dictionaries.

## Discovery workflow

### 1. Validate config and API access

The tool first checks:

- the API key exists
- the base URL looks valid
- the API responds

This gives users a clear failure early if the setup is wrong.

### 2. Search the Pure API

The configured search terms are sent to the `research-outputs` endpoint.

The code flattens and cleans the terms first so the search loop is predictable and easy to log.

### 3. Merge duplicate results

A single research output can match more than one search term.

The tool merges those into one candidate row so the review CSV stays easier to read.

### 4. Enrich each result

For each candidate, the tool fetches the full research output and reads file information from `electronicVersions`.

This step determines:

- whether files exist
- whether any file is a PDF
- whether the access type looks open/public
- which download URL should be used later

### 5. Classify results

Each candidate is classified, for example as:

- `downloadable_pdf`
- `restricted_or_unknown_access`
- `has_non_pdf_only`
- `no_files`

This classification helps the review step move faster.

### 6. Write review artifacts

The discovery workflow writes:

- `discovery_candidates.csv`
- `discovery_summary.md`

## Approved download workflow

### 1. Load approved candidates

The downloader uses `approved_candidates.csv` if it exists.
If it does not, it can derive a proceed set from the reviewed discovery CSV.

### 2. Respect the pilot size

The downloader limits the default run size using `APPROVED_DOWNLOAD_PILOT_SIZE`.

This helps users test safely before downloading a larger batch.

### 3. Resume safely with a checkpoint

The checkpoint file records completed, skipped, and failed items.

That means reruns can continue cleanly after interruptions.

### 4. Download using temporary files

Files are written to a temporary `.part` file first and only moved into place when complete.

This prevents incomplete downloads from looking like valid final files.

## Why the repo is leaner now

The repository no longer needs:

- the old direct downloader workflow
- sample files that only existed for that retired path
- large test suites built around that old approach

That leaves a smaller tool focused on one supported workflow instead of multiple overlapping ones.
