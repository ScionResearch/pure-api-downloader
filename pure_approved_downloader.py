"""
Pure API Approved Candidate Downloader
=====================================

Consumes approved discovery CSV rows and downloads a small pilot batch of PDFs
with checkpointing, duplicate detection, and atomic writes.
"""

from __future__ import annotations

import csv
import json
import os
import tempfile
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

try:
    import config
except ImportError as exc:  # pragma: no cover - align with repo style
    raise SystemExit("config.py not found. Please create or configure it first.") from exc

from download_pure_file import check_api_key, log_debug, test_api_connection
from pure_discovery import (
    APPROVED_DECISIONS,
    DISCOVERY_APPROVED_OUTPUT_CSV,
    DISCOVERY_OUTPUT_CSV,
    REVIEW_DECISION_COLUMN,
    export_approved_candidates,
)

LOADABLE_APPROVAL_DECISIONS = set(APPROVED_DECISIONS) | {"approve_auto"}

PURE_API_KEY = config.PURE_API_KEY
BASE_API_URL = config.BASE_API_URL
REQUEST_TIMEOUT = getattr(config, "REQUEST_TIMEOUT", 300)
DOWNLOAD_CHUNK_SIZE = getattr(config, "DOWNLOAD_CHUNK_SIZE", 8192)
MAX_FILENAME_LENGTH = getattr(config, "MAX_FILENAME_LENGTH", 80)
APPROVED_DOWNLOAD_INPUT_CSV = getattr(
    config, "APPROVED_DOWNLOAD_INPUT_CSV", DISCOVERY_APPROVED_OUTPUT_CSV
)
APPROVED_DOWNLOAD_OUTPUT_DIR = getattr(
    config, "APPROVED_DOWNLOAD_OUTPUT_DIR", os.path.join("downloads", "approved_pilot")
)
APPROVED_DOWNLOAD_CHECKPOINT_FILE = getattr(
    config, "APPROVED_DOWNLOAD_CHECKPOINT_FILE", "approved_download_checkpoint.json"
)
APPROVED_DOWNLOAD_PILOT_SIZE = getattr(config, "APPROVED_DOWNLOAD_PILOT_SIZE", 25)
APPROVED_DOWNLOAD_RETRY_ATTEMPTS = getattr(config, "APPROVED_DOWNLOAD_RETRY_ATTEMPTS", 3)
APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS = getattr(
    config, "APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS", 1
)
APPROVED_DOWNLOAD_SKIP_EXISTING = getattr(config, "APPROVED_DOWNLOAD_SKIP_EXISTING", True)


def sanitize_filename_component(value: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    cleaned = "".join(char for char in (value or "") if char.isalnum() or char in (" ", "-", "_"))
    cleaned = "_".join(cleaned.split())
    cleaned = cleaned.strip("_-")
    if not cleaned:
        cleaned = "pure_output"
    return cleaned[:max_length].rstrip("_-") or "pure_output"


def infer_extension(candidate: dict) -> str:
    name = candidate.get("first_open_pdf_name", "") or ""
    if "." in name:
        extension = os.path.splitext(name)[1].lower()
        if extension:
            return extension

    url = candidate.get("first_open_pdf_url", "") or ""
    parsed = urlparse(url)
    extension = os.path.splitext(os.path.basename(parsed.path))[1].lower()
    return extension or ".pdf"


def build_output_path(candidate: dict, output_dir: str = APPROVED_DOWNLOAD_OUTPUT_DIR) -> str:
    os.makedirs(output_dir, exist_ok=True)
    title_part = sanitize_filename_component(candidate.get("title", ""))
    identity = candidate.get("pure_id") or candidate.get("uuid") or "unknown"
    identity_part = sanitize_filename_component(str(identity), max_length=32)
    extension = infer_extension(candidate)
    filename = f"{title_part}_{identity_part}{extension}"
    return os.path.join(output_dir, filename)


def load_approved_candidates(csv_path: str = APPROVED_DOWNLOAD_INPUT_CSV) -> List[dict]:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Approved candidate CSV not found: {csv_path}")

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            decision = (row.get(REVIEW_DECISION_COLUMN, "") or "").strip().lower()
            if decision and decision not in LOADABLE_APPROVAL_DECISIONS:
                continue
            if row.get("download_status") != "downloadable_pdf":
                continue
            if not row.get("first_open_pdf_url"):
                continue
            rows.append(row)
    return rows


def create_proceed_candidates_from_review_csv(
    review_csv_path: str = DISCOVERY_OUTPUT_CSV,
    output_path: str = APPROVED_DOWNLOAD_INPUT_CSV,
) -> str:
    """
    Create an approved candidate CSV from the discovery review CSV.

    If explicit approval decisions are present, use only those rows.
    If no approval decisions are present, treat all downloadable PDF rows as the
    confirmed proceed set for the current run.
    """
    if not os.path.exists(review_csv_path):
        raise FileNotFoundError(f"Review CSV not found: {review_csv_path}")

    with open(review_csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    explicitly_approved = []
    downloadable_rows = []
    for row in rows:
        if row.get("download_status") != "downloadable_pdf":
            continue
        if not row.get("first_open_pdf_url"):
            continue

        downloadable_rows.append(row)
        decision = (row.get(REVIEW_DECISION_COLUMN, "") or "").strip().lower()
        if decision in APPROVED_DECISIONS:
            explicitly_approved.append(row)

    rows_to_write = explicitly_approved or downloadable_rows
    if not rows_to_write:
        raise ValueError("No downloadable PDF rows found in review CSV")

    for row in rows_to_write:
        if not (row.get(REVIEW_DECISION_COLUMN, "") or "").strip():
            row[REVIEW_DECISION_COLUMN] = "approve_auto"

    with open(output_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows_to_write[0].keys()))
        writer.writeheader()
        writer.writerows(rows_to_write)

    log_debug(
        f"Prepared proceed candidate CSV with {len(rows_to_write)} rows at {output_path}"
    )
    return output_path


def load_checkpoint(checkpoint_path: str = APPROVED_DOWNLOAD_CHECKPOINT_FILE) -> dict:
    if not os.path.exists(checkpoint_path):
        return {"completed": {}, "failed": {}, "skipped": {}}

    with open(checkpoint_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {
        "completed": data.get("completed", {}),
        "failed": data.get("failed", {}),
        "skipped": data.get("skipped", {}),
    }


def save_checkpoint(checkpoint: dict, checkpoint_path: str = APPROVED_DOWNLOAD_CHECKPOINT_FILE) -> str:
    with open(checkpoint_path, "w", encoding="utf-8") as handle:
        json.dump(checkpoint, handle, indent=2, sort_keys=True)
    return checkpoint_path


def make_checkpoint_entry(candidate: dict, output_path: str = "", status: str = "completed", error: str = "") -> dict:
    return {
        "uuid": candidate.get("uuid", ""),
        "pure_id": candidate.get("pure_id", ""),
        "title": candidate.get("title", ""),
        "status": status,
        "output_path": output_path,
        "source_url": candidate.get("first_open_pdf_url", ""),
        "error": error,
    }


def should_skip_candidate(candidate: dict, checkpoint: dict, output_path: str) -> Optional[str]:
    uuid = candidate.get("uuid", "")
    if uuid and uuid in checkpoint.get("completed", {}):
        return "already_completed"
    if APPROVED_DOWNLOAD_SKIP_EXISTING and os.path.exists(output_path):
        return "existing_file"
    return None


def download_candidate(
    candidate: dict,
    checkpoint: dict,
    output_dir: str = APPROVED_DOWNLOAD_OUTPUT_DIR,
    checkpoint_path: str = APPROVED_DOWNLOAD_CHECKPOINT_FILE,
    http_client=requests,
) -> dict:
    url = candidate.get("first_open_pdf_url", "")
    uuid = candidate.get("uuid", "") or candidate.get("pure_id", "unknown")
    output_path = build_output_path(candidate, output_dir=output_dir)

    skip_reason = should_skip_candidate(candidate, checkpoint, output_path)
    if skip_reason:
        checkpoint["skipped"][uuid] = make_checkpoint_entry(
            candidate, output_path=output_path, status=skip_reason
        )
        save_checkpoint(checkpoint, checkpoint_path)
        return {"status": skip_reason, "output_path": output_path}

    headers = {
        "api-key": PURE_API_KEY,
        "Accept": "application/octet-stream",
        "User-Agent": "Pure-API-ApprovedDownloader/1.0",
    }

    last_error = ""
    for attempt in range(1, APPROVED_DOWNLOAD_RETRY_ATTEMPTS + 1):
        try:
            response = http_client.get(
                url,
                headers=headers,
                stream=True,
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, dir=output_dir, suffix=".part") as temp_handle:
                    temp_path = temp_handle.name
                    for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        if chunk:
                            temp_handle.write(chunk)
                os.replace(temp_path, output_path)
                checkpoint["completed"][uuid] = make_checkpoint_entry(
                    candidate, output_path=output_path, status="completed"
                )
                checkpoint.get("failed", {}).pop(uuid, None)
                checkpoint.get("skipped", {}).pop(uuid, None)
                save_checkpoint(checkpoint, checkpoint_path)
                return {"status": "completed", "output_path": output_path}

            last_error = f"HTTP {response.status_code}"
        except Exception as exc:  # pragma: no cover - covered through mocks broadly
            last_error = str(exc)

        if attempt < APPROVED_DOWNLOAD_RETRY_ATTEMPTS:
            time.sleep(APPROVED_DOWNLOAD_RETRY_DELAY_SECONDS)

    checkpoint["failed"][uuid] = make_checkpoint_entry(
        candidate,
        output_path=output_path,
        status="failed",
        error=last_error,
    )
    save_checkpoint(checkpoint, checkpoint_path)
    return {"status": "failed", "output_path": output_path, "error": last_error}


def run_approved_download_pilot(
    review_csv_path: str = DISCOVERY_OUTPUT_CSV,
    approved_csv_path: str = APPROVED_DOWNLOAD_INPUT_CSV,
    output_dir: str = APPROVED_DOWNLOAD_OUTPUT_DIR,
    checkpoint_path: str = APPROVED_DOWNLOAD_CHECKPOINT_FILE,
    pilot_size: int = APPROVED_DOWNLOAD_PILOT_SIZE,
    http_client=requests,
) -> dict:
    log_debug("=== Starting approved PDF pilot downloader ===")

    if not check_api_key(PURE_API_KEY):
        raise RuntimeError("API key validation failed")
    if not test_api_connection(http_client=http_client):
        raise RuntimeError("API connection failed before pilot download")

    if not os.path.exists(approved_csv_path):
        if not os.path.exists(review_csv_path):
            raise FileNotFoundError(
                f"Neither approved CSV '{approved_csv_path}' nor review CSV '{review_csv_path}' exists"
            )
        create_proceed_candidates_from_review_csv(review_csv_path, approved_csv_path)

    approved_candidates = load_approved_candidates(approved_csv_path)
    pilot_candidates = approved_candidates[:pilot_size]
    checkpoint = load_checkpoint(checkpoint_path)

    summary = {
        "requested_candidates": len(approved_candidates),
        "pilot_size": pilot_size,
        "processed_candidates": len(pilot_candidates),
        "completed": 0,
        "failed": 0,
        "skipped": 0,
        "output_dir": output_dir,
        "checkpoint_path": checkpoint_path,
        "approved_csv_path": approved_csv_path,
        "results": [],
    }

    for candidate in pilot_candidates:
        result = download_candidate(
            candidate,
            checkpoint=checkpoint,
            output_dir=output_dir,
            checkpoint_path=checkpoint_path,
            http_client=http_client,
        )
        summary["results"].append({
            "uuid": candidate.get("uuid", ""),
            "title": candidate.get("title", ""),
            **result,
        })
        if result["status"] == "completed":
            summary["completed"] += 1
        elif result["status"] == "failed":
            summary["failed"] += 1
        else:
            summary["skipped"] += 1

    log_debug(f"Approved pilot download summary: {json.dumps(summary, indent=2)}")
    return summary


if __name__ == "__main__":
    result = run_approved_download_pilot()
    print(json.dumps(result, indent=2))
