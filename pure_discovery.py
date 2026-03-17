"""
Pure API Forestry Discovery Tool
================================

Searches the Pure API for forestry-themed research outputs, enriches them with
file metadata, and generates review artifacts before any download step.
"""

from __future__ import annotations

import csv
import json
import os
import time
from collections import Counter
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

import requests

try:
    import config
except ImportError as exc:  # pragma: no cover - matches existing repo style
    raise SystemExit("config.py not found. Please create or configure it first.") from exc

from download_pure_file import check_api_key, log_debug, test_api_connection

BASE_API_URL = config.BASE_API_URL
PURE_API_KEY = config.PURE_API_KEY
DEFAULT_OBJECT_TYPE = getattr(config, "DEFAULT_OBJECT_TYPE", "research-outputs")
REQUEST_TIMEOUT = getattr(config, "REQUEST_TIMEOUT", 30)
DISCOVERY_OUTPUT_CSV = getattr(config, "DISCOVERY_OUTPUT_CSV", "discovery_candidates.csv")
DISCOVERY_SUMMARY_REPORT = getattr(config, "DISCOVERY_SUMMARY_REPORT", "discovery_summary.md")
DISCOVERY_APPROVED_OUTPUT_CSV = getattr(
    config, "DISCOVERY_APPROVED_OUTPUT_CSV", "approved_candidates.csv"
)
DISCOVERY_PAGE_SIZE = getattr(config, "DISCOVERY_PAGE_SIZE", 25)
DISCOVERY_MAX_RESULTS_PER_KEYWORD = getattr(
    config, "DISCOVERY_MAX_RESULTS_PER_KEYWORD", 100
)
DISCOVERY_ALLOWED_ACCESS_TYPES = {
    item.lower()
    for item in getattr(
        config,
        "DISCOVERY_ALLOWED_ACCESS_TYPES",
        ["open", "public", "free", "openaccess", "oa"],
    )
}

DEFAULT_KEYWORD_THEMES = {
    "general_forestry": [
        "forestry",
        "forest",
        "plantation",
        "silviculture",
        "timber",
        "wood",
    ],
    "species": [
        "cypress",
        "cupressus",
        "eucalyptus",
        "eucalypt",
        "douglas-fir",
        "redwood",
        "sequoia",
        "radiata",
        "nitens",
        "fastigata",
        "regnans",
    ],
    "breeding_and_genetics": [
        "breeding",
        "genetics",
        "genomic",
        "provenance",
        "seed orchard",
        "clonal",
    ],
    "protection_and_biosecurity": [
        "biosecurity",
        "pest",
        "pathogen",
        "disease",
        "canker",
        "paropsis",
    ],
    "productivity_and_management": [
        "productivity",
        "growth model",
        "durability",
        "wood quality",
        "site mapping",
    ],
}
DISCOVERY_KEYWORD_THEMES = getattr(
    config, "DISCOVERY_KEYWORD_THEMES", DEFAULT_KEYWORD_THEMES
)

REVIEW_DECISION_COLUMN = "reviewer_decision"
REVIEW_NOTES_COLUMN = "reviewer_notes"
APPROVED_DECISIONS = {"approve", "approved", "pilot", "yes", "y"}


def get_request_headers() -> Dict[str, str]:
    return {
        "api-key": PURE_API_KEY,
        "Accept": "application/json",
        "User-Agent": "Pure-API-Discovery/1.0",
    }


def normalize_localized_text(value) -> str:
    """Extract text from Pure's mixed localized-string shapes."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("value", "text", "term", "uri"):
            nested = value.get(key)
            if isinstance(nested, dict):
                nested_text = normalize_localized_text(nested)
                if nested_text:
                    return nested_text
            elif nested:
                return str(nested).strip()
    if isinstance(value, list):
        joined = "; ".join(filter(None, (normalize_localized_text(item) for item in value)))
        return joined.strip()
    return str(value).strip()


def normalize_access_type(access_type) -> str:
    if isinstance(access_type, dict):
        for key in ("value", "term", "text", "uri"):
            nested = access_type.get(key)
            normalized = normalize_localized_text(nested)
            if normalized:
                return normalized
    return normalize_localized_text(access_type)


def flatten_keyword_themes(keyword_themes: Mapping[str, Sequence[str]]) -> List[str]:
    seen: Set[str] = set()
    flattened: List[str] = []
    for terms in keyword_themes.values():
        for term in terms:
            cleaned = term.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                flattened.append(cleaned)
    return flattened


def keyword_matches_content(keyword: str, title: str, abstract: str) -> Tuple[bool, Set[str]]:
    title_lower = title.lower()
    abstract_lower = abstract.lower()
    fields = set()
    if keyword in title_lower:
        fields.add("title")
    if keyword in abstract_lower:
        fields.add("abstract")
    return bool(fields), fields


def is_allowed_access(access_value: str) -> bool:
    normalized = access_value.lower().replace(" ", "")
    return any(token in normalized for token in DISCOVERY_ALLOWED_ACCESS_TYPES)


def format_elapsed_seconds(start_time: float) -> str:
    return f"{time.time() - start_time:.1f}s"


def search_research_outputs_page(
    query: str,
    size: int,
    offset: int = 0,
    validate_api_key: bool = True,
    http_client=requests,
) -> Optional[dict]:
    if validate_api_key and not check_api_key(PURE_API_KEY, verbose=False):
        return None

    url = f"{BASE_API_URL}/{DEFAULT_OBJECT_TYPE}"
    params = {"q": query, "size": size, "offset": offset}
    response = http_client.get(
        url,
        headers=get_request_headers(),
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        log_debug(
            f"Discovery search failed for '{query}' at offset {offset}: HTTP {response.status_code}",
            "ERROR",
        )
        return None
    return response.json()


def fetch_research_output_detail(uuid: str, http_client=requests) -> Optional[dict]:
    url = f"{BASE_API_URL}/{DEFAULT_OBJECT_TYPE}/{uuid}"
    response = http_client.get(
        url,
        headers=get_request_headers(),
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        log_debug(f"Failed to enrich research output {uuid}: HTTP {response.status_code}", "WARNING")
        return None
    return response.json()


def extract_file_records(research_output: dict) -> List[dict]:
    files = []
    for version in research_output.get("electronicVersions", []) or []:
        file_info = version.get("file") or {}
        if not file_info:
            continue
        access_value = normalize_access_type(version.get("accessType"))
        file_name = normalize_localized_text(file_info.get("fileName"))
        extension = os.path.splitext(file_name)[1].lower()
        files.append(
            {
                "file_id": file_info.get("fileId") or file_info.get("uuid") or "",
                "file_name": file_name,
                "extension": extension,
                "mime_type": normalize_localized_text(file_info.get("mimeType")),
                "size": file_info.get("size") or "",
                "access_type": access_value,
                "allowed_access": is_allowed_access(access_value) if access_value else False,
                "download_url": file_info.get("url")
                or (
                    f"{BASE_API_URL}/{DEFAULT_OBJECT_TYPE}/{research_output.get('uuid')}/files/"
                    f"{file_info.get('fileId')}/{file_name}"
                    if file_info.get("fileId") and file_name
                    else ""
                ),
            }
        )
    return files


def classify_files(file_records: Sequence[dict]) -> str:
    if not file_records:
        return "no_files"

    pdf_files = [record for record in file_records if record["extension"] == ".pdf"]
    non_pdf_files = [record for record in file_records if record["extension"] != ".pdf"]

    if pdf_files:
        if any(record["allowed_access"] for record in pdf_files):
            return "downloadable_pdf"
        return "restricted_or_unknown_access"

    if non_pdf_files:
        return "has_non_pdf_only"

    return "needs_review"


def calculate_match_score(matched_terms: Iterable[str], matched_fields: Iterable[str], status: str) -> int:
    score = len(set(matched_terms)) * 10
    fields = set(matched_fields)
    if "title" in fields:
        score += 20
    if "abstract" in fields:
        score += 10
    if status == "downloadable_pdf":
        score += 30
    elif status == "restricted_or_unknown_access":
        score += 10
    return score


def build_candidate_record(
    research_output: dict,
    matched_terms: Iterable[str],
    matched_fields: Iterable[str],
    source_queries: Iterable[str],
) -> dict:
    file_records = extract_file_records(research_output)
    status = classify_files(file_records)
    access_types = sorted({record["access_type"] for record in file_records if record["access_type"]})
    extensions = sorted({record["extension"] for record in file_records if record["extension"]})
    pdf_files = [record for record in file_records if record["extension"] == ".pdf"]
    open_pdf_files = [record for record in pdf_files if record["allowed_access"]]

    title = normalize_localized_text(research_output.get("title"))
    abstract = normalize_localized_text(research_output.get("abstract"))
    output_type = normalize_localized_text(research_output.get("type"))
    year = normalize_localized_text(research_output.get("publicationYear"))
    if not year:
        year = normalize_localized_text(research_output.get("year"))

    return {
        "uuid": research_output.get("uuid", ""),
        "pure_id": research_output.get("pureId", ""),
        "title": title,
        "year": year,
        "output_type": output_type,
        "abstract": abstract,
        "match_score": calculate_match_score(matched_terms, matched_fields, status),
        "matched_terms": "; ".join(sorted(set(matched_terms))),
        "matched_fields": "; ".join(sorted(set(matched_fields))),
        "source_queries": "; ".join(sorted(set(source_queries))),
        "file_count": len(file_records),
        "pdf_count": len(pdf_files),
        "open_pdf_count": len(open_pdf_files),
        "non_pdf_count": len(file_records) - len(pdf_files),
        "file_extensions": "; ".join(extensions),
        "access_types": "; ".join(access_types),
        "download_status": status,
        "recommended_action": "review_then_download" if status == "downloadable_pdf" else "manual_review",
        "first_open_pdf_name": open_pdf_files[0]["file_name"] if open_pdf_files else "",
        "first_open_pdf_url": open_pdf_files[0]["download_url"] if open_pdf_files else "",
        REVIEW_DECISION_COLUMN: "",
        REVIEW_NOTES_COLUMN: "",
    }


def discover_candidates(
    keyword_themes: Optional[Mapping[str, Sequence[str]]] = None,
    page_size: Optional[int] = None,
    max_results_per_keyword: Optional[int] = None,
    http_client=requests,
) -> List[dict]:
    resolved_keyword_themes: Mapping[str, Sequence[str]] = keyword_themes or DISCOVERY_KEYWORD_THEMES
    resolved_page_size = page_size or DISCOVERY_PAGE_SIZE
    resolved_max_results_per_keyword = (
        max_results_per_keyword or DISCOVERY_MAX_RESULTS_PER_KEYWORD
    )

    if not check_api_key(PURE_API_KEY, verbose=False):
        raise RuntimeError("API key validation failed before discovery search")

    keywords = flatten_keyword_themes(resolved_keyword_themes)
    discovered: Dict[str, dict] = {}
    workflow_start = time.time()

    log_debug(
        "Discovery search plan: "
        f"{len(keywords)} keywords, page size {resolved_page_size}, "
        f"up to {resolved_max_results_per_keyword} results per keyword"
    )

    for keyword_index, keyword in enumerate(keywords, start=1):
        keyword_start = time.time()
        unique_before = len(discovered)
        log_debug(
            f"[{keyword_index}/{len(keywords)}] Searching discovery candidates for keyword '{keyword}'"
        )
        offset = 0
        fetched = 0
        page_number = 0

        while fetched < resolved_max_results_per_keyword:
            page_number += 1
            page = search_research_outputs_page(
                keyword,
                resolved_page_size,
                offset=offset,
                validate_api_key=False,
                http_client=http_client,
            )
            if not page:
                log_debug(
                    f"  Keyword '{keyword}': stopping early because the API returned no usable page",
                    "WARNING",
                )
                break

            items = page.get("items", []) or []
            if not items:
                log_debug(f"  Keyword '{keyword}': no more results after page {page_number}")
                break

            matched_on_page = 0
            new_candidates_on_page = 0

            for item in items:
                title = normalize_localized_text(item.get("title"))
                abstract = normalize_localized_text(item.get("abstract"))
                matched, fields = keyword_matches_content(keyword, title, abstract)
                if not matched:
                    continue

                matched_on_page += 1

                uuid = item.get("uuid")
                if not uuid:
                    continue

                was_new_candidate = uuid not in discovered
                if was_new_candidate:
                    new_candidates_on_page += 1

                entry = discovered.setdefault(
                    uuid,
                    {
                        "matched_terms": set(),
                        "matched_fields": set(),
                        "source_queries": set(),
                        "search_item": item,
                    },
                )
                entry["matched_terms"].add(keyword)
                entry["matched_fields"].update(fields)
                entry["source_queries"].add(keyword)
                if len(title) > len(normalize_localized_text(entry["search_item"].get("title"))):
                    entry["search_item"] = item

            fetched += len(items)
            offset += len(items)
            total_count = page.get("count")
            max_for_keyword = min(
                resolved_max_results_per_keyword,
                total_count if isinstance(total_count, int) else resolved_max_results_per_keyword,
            )
            log_debug(
                "  "
                f"Page {page_number}: fetched {len(items)} items "
                f"({min(fetched, max_for_keyword)}/{max_for_keyword} checked for this keyword), "
                f"matched {matched_on_page}, new candidates {new_candidates_on_page}, "
                f"unique total {len(discovered)}"
            )
            if len(items) < resolved_page_size:
                break
            if isinstance(total_count, int) and offset >= total_count:
                break

        added_for_keyword = len(discovered) - unique_before
        log_debug(
            f"[{keyword_index}/{len(keywords)}] Finished keyword '{keyword}': "
            f"+{added_for_keyword} unique candidates in {format_elapsed_seconds(keyword_start)}"
        )

    candidates = []
    total_candidates_to_enrich = len(discovered)
    if total_candidates_to_enrich:
        log_debug(
            f"Enriching {total_candidates_to_enrich} unique candidates with file metadata..."
        )

    for index, (uuid, entry) in enumerate(discovered.items(), start=1):
        if index == 1 or index % 25 == 0 or index == total_candidates_to_enrich:
            log_debug(
                f"  Enrichment progress: {index}/{total_candidates_to_enrich} candidates processed"
            )
        detail = fetch_research_output_detail(uuid, http_client=http_client) or entry["search_item"]
        candidates.append(
            build_candidate_record(
                detail,
                entry["matched_terms"],
                entry["matched_fields"],
                entry["source_queries"],
            )
        )

    candidates.sort(key=lambda item: (-item["match_score"], item["title"].lower(), item["uuid"]))
    log_debug(
        f"Discovery search complete: {len(candidates)} unique candidates assembled in {format_elapsed_seconds(workflow_start)}"
    )
    return candidates


def write_candidates_csv(candidates: Sequence[dict], output_path: str = DISCOVERY_OUTPUT_CSV) -> str:
    fieldnames = [
        "uuid",
        "pure_id",
        "title",
        "year",
        "output_type",
        "match_score",
        "matched_terms",
        "matched_fields",
        "source_queries",
        "file_count",
        "pdf_count",
        "open_pdf_count",
        "non_pdf_count",
        "file_extensions",
        "access_types",
        "download_status",
        "recommended_action",
        "first_open_pdf_name",
        "first_open_pdf_url",
        REVIEW_DECISION_COLUMN,
        REVIEW_NOTES_COLUMN,
        "abstract",
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for candidate in candidates:
            row = {key: candidate.get(key, "") for key in fieldnames}
            writer.writerow(row)

    log_debug(f"Wrote discovery candidates CSV to {output_path}")
    return output_path


def build_summary_counts(candidates: Sequence[dict]) -> dict:
    status_counter = Counter(candidate["download_status"] for candidate in candidates)
    type_counter = Counter(candidate["output_type"] or "Unknown" for candidate in candidates)
    access_counter = Counter()
    keyword_counter = Counter()

    for candidate in candidates:
        for access_value in filter(None, candidate.get("access_types", "").split("; ")):
            access_counter[access_value] += 1
        for matched_term in filter(None, candidate.get("matched_terms", "").split("; ")):
            keyword_counter[matched_term] += 1

    return {
        "total_candidates": len(candidates),
        "status_counter": status_counter,
        "type_counter": type_counter,
        "access_counter": access_counter,
        "keyword_counter": keyword_counter,
    }


def generate_summary_report(candidates: Sequence[dict], output_path: str = DISCOVERY_SUMMARY_REPORT) -> str:
    counts = build_summary_counts(candidates)

    lines = [
        "# Forestry Discovery Summary",
        "",
        f"Total candidates: **{counts['total_candidates']}**",
        "",
        "## By download status",
        "",
    ]

    for status, count in counts["status_counter"].most_common():
        lines.append(f"- `{status}`: {count}")

    lines.extend(["", "## By output type", ""])
    for output_type, count in counts["type_counter"].most_common(15):
        lines.append(f"- `{output_type}`: {count}")

    lines.extend(["", "## By access type", ""])
    if counts["access_counter"]:
        for access_type, count in counts["access_counter"].most_common(15):
            lines.append(f"- `{access_type}`: {count}")
    else:
        lines.append("- No access types were present in the discovery results")

    lines.extend(["", "## Top matched keywords", ""])
    for keyword, count in counts["keyword_counter"].most_common(20):
        lines.append(f"- `{keyword}`: {count}")

    lines.extend(
        [
            "",
            "## Review instructions",
            "",
            f"1. Open `{os.path.basename(DISCOVERY_OUTPUT_CSV)}`.",
            f"2. Set `{REVIEW_DECISION_COLUMN}` to `approve` for candidates you want in the pilot batch.",
            f"3. Add optional notes in `{REVIEW_NOTES_COLUMN}`.",
            "4. Export approved rows before running any download workflow.",
        ]
    )

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    log_debug(f"Wrote discovery summary report to {output_path}")
    return output_path


def export_approved_candidates(
    review_csv_path: str = DISCOVERY_OUTPUT_CSV,
    output_path: str = DISCOVERY_APPROVED_OUTPUT_CSV,
) -> str:
    with open(review_csv_path, "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        approved_rows = []
        for row in reader:
            decision = (row.get(REVIEW_DECISION_COLUMN, "") or "").strip().lower()
            if decision in APPROVED_DECISIONS and row.get("download_status") == "downloadable_pdf":
                approved_rows.append(row)

    if not approved_rows:
        raise ValueError("No approved downloadable PDF candidates found in review CSV")

    with open(output_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(approved_rows[0].keys()))
        writer.writeheader()
        writer.writerows(approved_rows)

    log_debug(f"Wrote approved candidate CSV to {output_path}")
    return output_path


def run_discovery_workflow(
    output_csv_path: str = DISCOVERY_OUTPUT_CSV,
    summary_report_path: str = DISCOVERY_SUMMARY_REPORT,
    keyword_themes: Optional[Dict[str, Sequence[str]]] = None,
    http_client=requests,
) -> dict:
    log_debug("=== Starting forestry discovery workflow ===")

    if not test_api_connection(http_client=http_client):
        raise RuntimeError("API connection failed. Check config.py before discovery.")

    candidates = discover_candidates(keyword_themes=keyword_themes, http_client=http_client)
    write_candidates_csv(candidates, output_path=output_csv_path)
    generate_summary_report(candidates, output_path=summary_report_path)

    counts = build_summary_counts(candidates)
    result = {
        "candidate_count": len(candidates),
        "downloadable_pdf_count": counts["status_counter"].get("downloadable_pdf", 0),
        "output_csv_path": output_csv_path,
        "summary_report_path": summary_report_path,
    }
    log_debug(f"Discovery workflow complete: {json.dumps(result, indent=2)}")
    return result


if __name__ == "__main__":
    summary = run_discovery_workflow()
    print("Discovery complete")
    print(json.dumps(summary, indent=2))
