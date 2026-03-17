"""
Pure API File Downloader
========================

🚀 QUICK SETUP INSTRUCTIONS:
1. Run: python setup_config.py   (to configure API key and settings)
2. Place your CSV file in this directory
3. Run: python download_pure_file.py

📁 CSV file should have a column named "Pure ID" with your Pure IDs

� All settings are now in config.py - you can edit that file directly
   or use setup_config.py for interactive setup

For detailed help, scroll down to the usage guide when you run the script.
"""

import requests
import os
import json
import csv
from datetime import datetime
from urllib.parse import urljoin

# Import configuration from config.py
try:
    import config
    
    # Load configuration values
    PURE_API_KEY = config.PURE_API_KEY
    BASE_API_URL = config.BASE_API_URL
    CSV_FILE_PATH = config.CSV_FILE_PATH
    ID_COLUMN = config.ID_COLUMN
    OUTPUT_DIRECTORY = config.OUTPUT_DIRECTORY
    MAX_DOWNLOADS = config.MAX_DOWNLOADS
    DOWNLOAD_FILE_TYPES = config.DOWNLOAD_FILE_TYPES
    REQUEST_TIMEOUT = config.REQUEST_TIMEOUT
    DOWNLOAD_CHUNK_SIZE = config.DOWNLOAD_CHUNK_SIZE
    
    # Validate configuration on import
    is_valid, validation_message = config.validate_config()
    if not is_valid:
        print(f"⚠️  Configuration Warning: {validation_message}")
        print("   Please run: python setup_config.py")
        print()
        
except ImportError:
    print("❌ Error: config.py not found!")
    print("   Please ensure config.py exists in the same directory")
    print("   You can use setup_config.py to create it")
    import sys
    sys.exit(1)
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    print("   Please check config.py for errors")
    import sys
    sys.exit(1)


def load_pure_ids_from_csv(csv_file_path: str, id_column: str = "Pure ID") -> list:
    """
    Load Pure IDs from a CSV file.

    Args:
        csv_file_path (str): Path to the CSV file
        id_column (str): Name of the column containing Pure IDs

    Returns:
        list: List of dictionaries with Pure ID data
    """
    log_debug(f"=== Loading Pure IDs from CSV: {csv_file_path} ===")

    if not os.path.exists(csv_file_path):
        log_debug(f"Error: CSV file not found: {csv_file_path}", "ERROR")
        return []

    pure_entries = []

    try:
        # Try different encodings
        encodings_to_try = ['utf-8-sig', 'cp1252', 'latin-1', 'iso-8859-1']
        file_content = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                with open(csv_file_path, "r", encoding=encoding, newline="") as test_file:
                    file_content = test_file.read()
                    used_encoding = encoding
                    log_debug(f"Successfully read CSV with {encoding} encoding")
                    break
            except UnicodeDecodeError:
                continue
        
        if file_content is None:
            log_debug("Error: Could not read CSV file with any supported encoding", "ERROR")
            return []
        
        # Parse CSV from the string content
        import io
        csvfile_io = io.StringIO(file_content)
        
        # Use comma as delimiter (standard CSV format)
        delimiter = ','
        log_debug(f"Using CSV delimiter: '{delimiter}'")

        reader = csv.DictReader(csvfile_io, delimiter=delimiter)

        log_debug(f"CSV columns found: {list(reader.fieldnames)}")

        if id_column not in reader.fieldnames:
            log_debug(f"Error: Column '{id_column}' not found in CSV", "ERROR")
            log_debug(f"Available columns: {list(reader.fieldnames)}", "INFO")
            return []

        for row_num, row in enumerate(
            reader, start=2
        ):  # Start at 2 since row 1 is header
            pure_id = row.get(id_column, "").strip()
            if pure_id:
                entry = {
                    "pure_id": pure_id,
                    "title": row.get("Title", "").strip(),
                    "year": row.get("Year", "").strip(),
                    "row_number": row_num,
                    "full_row": row,
                }
                pure_entries.append(entry)
                log_debug(
                    f"Row {row_num}: Found Pure ID '{pure_id}' - '{entry['title'][:50]}...'"
                )
            else:
                log_debug(f"Row {row_num}: No Pure ID found", "WARNING")

        log_debug(f"Successfully loaded {len(pure_entries)} Pure IDs from CSV")
        return pure_entries

    except UnicodeDecodeError as e:
        log_debug(f"Error reading CSV file - encoding issue: {e}", "ERROR")
        log_debug("Try saving the CSV file as UTF-8 encoding", "INFO")
        return []
    except Exception as e:
        log_debug(f"Error reading CSV file: {e}", "ERROR")
        return []


def identify_pure_id_type(pure_id: str, http_client=requests) -> dict:
    """
    Attempt to identify whether a Pure ID is an object ID or file ID by testing API calls.
    Updated to use direct ID lookup which works for numeric Pure IDs.

    Args:
        pure_id (str): The Pure ID to test

    Returns:
        dict: Information about the ID type and test results
    """
    log_debug(f"=== Identifying Pure ID type for: {pure_id} ===")

    if not check_api_key(PURE_API_KEY):
        return {"error": "API key validation failed"}

    results = {
        "pure_id": pure_id,
        "is_object_id": False,
        "is_file_id": False,
        "object_type": None,
        "test_results": {},
        "uuid": None,  # Store the UUID if we find it
        "title": None,  # Store the title if we find it
    }

    # Test 1: Try as research-outputs object ID (works with numeric IDs!)
    log_debug("Testing as research-outputs object ID (direct lookup)...")
    try:
        url = f"{BASE_API_URL}/research-outputs/{pure_id}"
        headers = {
            "api-key": PURE_API_KEY,
            "Accept": "application/json",
            "User-Agent": "Pure-API-Client/1.0",
        }

        response = http_client.get(url, headers=headers, timeout=10)
        results["test_results"]["research_outputs"] = {
            "status_code": response.status_code,
            "success": response.status_code == 200,
        }

        if response.status_code == 200:
            log_debug("[OK] Successfully identified as research-outputs object ID")
            results["is_object_id"] = True
            results["object_type"] = "research-outputs"

            # Try to get basic info
            try:
                data = response.json()
                title = data.get("title", {})
                if isinstance(title, dict):
                    title_text = title.get("value", "No title")
                else:
                    title_text = str(title)
                results["title"] = title_text
                results["uuid"] = data.get("uuid")
                log_debug(f"Object title: {title_text[:100]}...")
            except:
                pass
        else:
            log_debug(
                f"[X] Not a research-outputs object ID (status: {response.status_code})"
            )

    except Exception as e:
        log_debug(f"Error testing as research-outputs ID: {e}", "ERROR")
        results["test_results"]["research_outputs"] = {"error": str(e)}

    # Test 2: Try as persons object ID
    if not results["is_object_id"]:
        log_debug("Testing as persons object ID...")
        try:
            url = f"{BASE_API_URL}/persons/{pure_id}"
            response = http_client.get(url, headers=headers, timeout=10)
            results["test_results"]["persons"] = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
            }

            if response.status_code == 200:
                log_debug("[OK] Successfully identified as persons object ID")
                results["is_object_id"] = True
                results["object_type"] = "persons"
            else:
                log_debug(f"[X] Not a persons object ID (status: {response.status_code})")

        except Exception as e:
            log_debug(f"Error testing as persons ID: {e}", "ERROR")
            results["test_results"]["persons"] = {"error": str(e)}

    # Test 3: If it has UUID format, might be a file ID within a research output
    if not results["is_object_id"] and len(pure_id) == 36 and pure_id.count("-") == 4:
        log_debug("Testing as potential file UUID...")
        results["test_results"]["file_uuid_format"] = True
        # Note: Can't directly test file IDs without knowing the parent object

    # Test 4: Check if it's a numeric ID that might need conversion
    if pure_id.isdigit():
        log_debug(f"Pure ID '{pure_id}' is numeric - this is likely an object ID")
        results["test_results"]["numeric_id"] = True

        # In some Pure systems, numeric IDs need to be converted to UUIDs
        # or used differently in API calls

    log_debug(f"ID type identification complete: {results}")
    return results


def get_electronic_versions(object_type: str, object_uuid: str, http_client=requests):
    """
    Get electronic versions (files) from a Pure research output.
    Files are stored in the electronicVersions field, not in a separate /files endpoint.
    
    Parameters:
        object_type (str): The type of Pure object (e.g., 'research-outputs')
        object_uuid (str): The UUID of the Pure object
        
    Returns:
        list: List of file information dictionaries, or empty list if error
    """
    log_debug(f"=== Getting electronic versions for {object_type}/{object_uuid} ===")
    
    if not check_api_key(PURE_API_KEY):
        return []
    
    url = f"{BASE_API_URL}/{object_type}/{object_uuid}"
    headers = {
        "api-key": PURE_API_KEY,
        "Accept": "application/json",
        "User-Agent": "Pure-API-Client/1.0",
    }
    
    try:
        response = http_client.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            electronic_versions = data.get("electronicVersions", [])
            log_debug(f"Found {len(electronic_versions)} electronic versions")
            
            files_list = []
            for ev in electronic_versions:
                if "file" in ev:
                    file_info = ev["file"]
                    # Add the electronic version metadata too
                    file_info["accessType"] = ev.get("accessType", {})
                    file_info["versionType"] = ev.get("versionType", "unknown")
                    file_info["electronicVersionId"] = ev.get("pureId")
                    files_list.append(file_info)
                    
                    log_debug(f"  File: {file_info.get('fileName', 'unknown')}")
                    log_debug(f"    FileId: {file_info.get('fileId', 'unknown')}")
                    log_debug(f"    Size: {file_info.get('size', 'unknown')} bytes")
            
            return files_list
        else:
            log_debug(f"Failed to get research output: {response.status_code}", "ERROR")
            return []
            
    except Exception as e:
        log_debug(f"Error getting electronic versions: {e}", "ERROR")
        return []


def download_from_csv_entry(
    csv_entry: dict, output_dir: str = "downloads", http_client=requests
) -> bool:
    """
    Download files for a single CSV entry after identifying the Pure ID type.

    Args:
        csv_entry (dict): Entry from CSV with pure_id and other metadata
        output_dir (str): Directory to save downloaded files

    Returns:
        bool: True if successful, False otherwise
    """
    pure_id = csv_entry["pure_id"]
    title = csv_entry.get("title", "Unknown")

    log_debug(f"=== Processing CSV entry: {pure_id} ===")
    log_debug(f"Title: {title}")

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_debug(f"Created output directory: {output_dir}")

    # Identify Pure ID type
    id_info = identify_pure_id_type(pure_id, http_client)

    if id_info.get("is_object_id") and id_info.get("object_type"):
        object_type = id_info["object_type"]
        uuid = id_info.get("uuid")  # Get the UUID from identification
        
        log_debug(f"Identified as {object_type} object ID")
        log_debug(f"UUID: {uuid}")

        # Generate safe filename
        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        safe_title = safe_title[:50]  # Limit length
        if not safe_title:
            safe_title = f"pure_{pure_id}"

        # Try to download using UUID (required for file operations)
        try:
            if not uuid:
                log_debug("No UUID available for file operations", "ERROR")
                return False
            
            # Get files from electronic versions
            files_list = get_electronic_versions(object_type, uuid, http_client)

            if files_list:
                log_debug(f"Found {len(files_list)} files for this object")

                # Download the first suitable file (PDF or DOCX)
                for file_info in files_list:
                    file_name = file_info.get("fileName", "")
                    file_id = file_info.get("fileId")
                    file_url = file_info.get("url")
                    
                    # Check if it's a PDF or DOCX
                    if file_name.lower().endswith(('.pdf', '.docx', '.doc')):
                        log_debug(f"Downloading file: {file_name}")
                        
                        # Use the provided URL or construct it
                        if file_url:
                            download_url = file_url
                        elif file_id:
                            download_url = f"{BASE_API_URL}/{object_type}/{uuid}/files/{file_id}/{file_name}"
                        else:
                            log_debug("No download URL or file ID available", "ERROR")
                            continue
                        
                        # Download the file
                        output_path = os.path.join(output_dir, f"{safe_title}_{pure_id}{os.path.splitext(file_name)[1]}")
                        
                        headers = {
                            "api-key": PURE_API_KEY,
                            "Accept": "application/octet-stream",
                            "User-Agent": "Pure-API-Client/1.0",
                        }
                        
                        response = http_client.get(download_url, headers=headers, stream=True, timeout=300)
                        
                        if response.status_code == 200:
                            with open(output_path, "wb") as f:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            
                            file_size = os.path.getsize(output_path)
                            log_debug(f"[OK] Downloaded {file_name} ({file_size} bytes) to {output_path}")
                            return True
                        else:
                            log_debug(f"Failed to download file: HTTP {response.status_code}", "ERROR")
                            continue
                
                log_debug("No suitable PDF/DOCX files found", "WARNING")
                return False
            else:
                log_debug("No files found for this object", "WARNING")
                return False

        except Exception as e:
            log_debug(f"Error downloading for {pure_id}: {e}", "ERROR")
            return False

    elif id_info.get("test_results", {}).get("numeric_id"):
        log_debug("Numeric ID detected - may need special handling", "WARNING")
        log_debug(
            "Some Pure systems use numeric IDs that need to be converted or used differently",
            "INFO",
        )
        return False

    else:
        log_debug("Could not identify Pure ID type", "ERROR")
        log_debug("This might be:", "INFO")
        log_debug("  1. A file UUID (needs parent object ID)", "INFO")
        log_debug("  2. An ID from a different Pure system", "INFO")
        log_debug("  3. An invalid ID", "INFO")
        return False


def batch_download_from_csv(
    csv_file_path: str,
    output_dir: str = "downloads",
    id_column: str = "Pure ID",
    max_downloads: int = None,
) -> dict:
    """
    Download files for all entries in a CSV file.

    Args:
        csv_file_path (str): Path to the CSV file
        output_dir (str): Directory to save downloaded files
        id_column (str): Name of the column containing Pure IDs
        max_downloads (int): Maximum number of downloads (None for all)

    Returns:
        dict: Summary of download results
    """
    log_debug(f"=== Starting batch download from CSV ===")
    log_debug(f"CSV file: {csv_file_path}")
    log_debug(f"Output directory: {output_dir}")
    log_debug(f"ID column: {id_column}")

    # Load entries from CSV
    entries = load_pure_ids_from_csv(csv_file_path, id_column)

    if not entries:
        log_debug("No entries loaded from CSV", "ERROR")
        return {"error": "No entries found"}

    if max_downloads:
        entries = entries[:max_downloads]
        log_debug(f"Limiting to first {max_downloads} entries")

    results = {
        "total_entries": len(entries),
        "successful_downloads": 0,
        "failed_downloads": 0,
        "errors": [],
    }

    for i, entry in enumerate(entries, 1):
        log_debug(f"\n--- Processing entry {i}/{len(entries)} ---")

        try:
            success = download_from_csv_entry(entry, output_dir)
            if success:
                results["successful_downloads"] += 1
                log_debug(f"[OK] Success for entry {i}")
            else:
                results["failed_downloads"] += 1
                results["errors"].append(
                    f"Failed to download for Pure ID: {entry['pure_id']}"
                )
                log_debug(f"[X] Failed for entry {i}")

        except Exception as e:
            results["failed_downloads"] += 1
            error_msg = f"Error processing Pure ID {entry['pure_id']}: {e}"
            results["errors"].append(error_msg)
            log_debug(error_msg, "ERROR")

    # Summary
    log_debug(f"\n=== Batch Download Summary ===")
    log_debug(f"Total entries processed: {results['total_entries']}")
    log_debug(f"Successful downloads: {results['successful_downloads']}")
    log_debug(f"Failed downloads: {results['failed_downloads']}")

    if results["errors"]:
        log_debug("Errors encountered:", "WARNING")
        for error in results["errors"]:
            log_debug(f"  - {error}", "WARNING")

    return results


def log_debug(message: str, level: str = "INFO") -> None:
    """
    Enhanced logging function with timestamps and levels.
    Args:
        message (str): The message to log
        level (str): Log level (DEBUG, INFO, WARNING, ERROR)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Use safe ASCII characters instead of Unicode symbols
    try:
        print(f"[{timestamp}] [{level}] {message}")
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        safe_message = message.encode('ascii', 'replace').decode('ascii')
        print(f"[{timestamp}] [{level}] {safe_message}")


def check_api_key(api_key: str, verbose: bool = True) -> bool:
    """
    Check if the provided API key is valid (not empty or placeholder).
    Returns True if valid, False otherwise.
    """
    if verbose:
        log_debug("Checking API key validity...")
    if not api_key:
        if verbose:
            log_debug("Error: PURE_API_KEY is empty or None", "ERROR")
        return False
    if api_key == "YOUR_API_KEY":
        if verbose:
            log_debug(
                "Error: PURE_API_KEY is still the placeholder value 'YOUR_API_KEY'", "ERROR"
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
    """
    Validate the base URL format for Pure API.
    Expected format: https://yourinstitution.elsevierpure.com/ws/api
    """
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
            "Warning: URL should end with '/ws/api' for Pure API endpoints", "WARNING"
        )
    log_debug("Base URL validation complete")
    return True


# ============================================================================
# 🔧 CONFIGURATION NOW LOADED FROM config.py
# ============================================================================
# All configuration settings are now in config.py
# Use setup_config.py for interactive configuration, or edit config.py directly
#
# Configuration loaded at import time:
#   - PURE_API_KEY
#   - BASE_API_URL
#   - CSV_FILE_PATH
#   - ID_COLUMN
#   - OUTPUT_DIRECTORY
#   - MAX_DOWNLOADS
#   - DOWNLOAD_FILE_TYPES
#   - REQUEST_TIMEOUT
#   - DOWNLOAD_CHUNK_SIZE
# ============================================================================

# Validate configuration on import
log_debug("=== Pure API Script Configuration Check ===")
validate_base_url(BASE_API_URL)


def list_pure_files(object_type: str, object_uuid: str, http_client=requests):
    """
    List available files for a Pure object.
    Parameters:
        object_type (str): The type of Pure object (e.g., 'research-outputs', 'persons').
        object_uuid (str): The UUID of the Pure object.
    Returns:
        dict or None: JSON response with file info, or None if error.
    """
    log_debug("=== Starting list_pure_files ===")
    log_debug(
        f"Input parameters - object_type: '{object_type}', object_uuid: '{object_uuid}'"
    )

    # Validate API key
    if not check_api_key(PURE_API_KEY):
        log_debug("API key validation failed", "ERROR")
        return None

    # Validate object_type
    if not object_type or not isinstance(object_type, str):
        log_debug(
            "Error: object_type must be a non-empty string. Example: 'research-outputs', 'persons', etc.",
            "ERROR",
        )
        log_debug(
            "Common object types: research-outputs, persons, organisational-units, activities, projects",
            "INFO",
        )
        return None

    # Validate object_uuid
    if not object_uuid or not isinstance(object_uuid, str):
        log_debug(
            "Error: object_uuid must be a non-empty string. Example: '123e4567-e89b-12d3-a456-426614174000'",
            "ERROR",
        )
        return None

    # Basic UUID format validation
    if len(object_uuid) != 36 or object_uuid.count("-") != 4:
        log_debug(
            f"Warning: UUID format looks unusual. Expected format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "WARNING",
        )

    # Construct URL
    url = f"{BASE_API_URL}/{object_type}/{object_uuid}/files"
    log_debug(f"Constructed URL: {url}")

    # Prepare headers
    headers = {
        "api-key": PURE_API_KEY,
        "Accept": "application/json",
        "User-Agent": "Pure-API-Client/1.0",
    }
    log_debug(
        f"Request headers: {json.dumps({k: v if k != 'api-key' else '[REDACTED]' for k, v in headers.items()}, indent=2)}"
    )

    try:
        log_debug("Sending GET request...")
        response = http_client.get(url, headers=headers, timeout=30)

        log_debug(f"Response status code: {response.status_code}")
        # Be defensive: response.headers may be missing or non-mapping in tests
        try:
            headers_dict = (
                response.headers
                if isinstance(response.headers, dict)
                else dict(response.headers)
            )
        except Exception:
            headers_dict = {"<unavailable>": "<mock or non-mapping headers>"}
        log_debug(f"Response headers: {json.dumps(headers_dict, indent=2)}")

        if response.status_code == 200:
            log_debug("[OK] Request successful!")
            try:
                response_data = response.json()
                log_debug(
                    f"Response contains {len(response_data.get('items', []))} files"
                )

                # Log file details for debugging
                if "items" in response_data:
                    for i, file_obj in enumerate(response_data["items"]):
                        log_debug(f"File {i+1}:")
                        log_debug(f"  - UUID: {file_obj.get('uuid', 'N/A')}")
                        log_debug(f"  - Filename: {file_obj.get('fileName', 'N/A')}")
                        log_debug(f"  - Size: {file_obj.get('size', 'N/A')} bytes")
                        log_debug(f"  - MIME type: {file_obj.get('mimeType', 'N/A')}")
                        log_debug(f"  - Created: {file_obj.get('created', 'N/A')}")

                print("\n=== Available files ===")
                print(json.dumps(response_data, indent=2))
                return response_data

            except json.JSONDecodeError as e:
                log_debug(f"Error decoding JSON response: {e}", "ERROR")
                log_debug(f"Raw response content: {response.text[:500]}...", "DEBUG")
                return None

        elif response.status_code == 401:
            log_debug("[X] Authentication failed - check your API key", "ERROR")
        elif response.status_code == 403:
            log_debug("[X] Access forbidden - check permissions for this object", "ERROR")
        elif response.status_code == 404:
            log_debug("[X] Object not found - check object_type and object_uuid", "ERROR")
        elif response.status_code == 429:
            log_debug("[X] Rate limit exceeded - wait before retrying", "ERROR")
        else:
            log_debug(f"[X] Unexpected status code: {response.status_code}", "ERROR")

        log_debug(f"Error response content: {response.text[:1000]}", "DEBUG")
        return None

    except requests.exceptions.Timeout:
        log_debug("[X] Request timed out after 30 seconds", "ERROR")
        return None
    except requests.exceptions.ConnectionError as e:
        log_debug(f"[X] Connection error: {e}", "ERROR")
        log_debug("Check your BASE_API_URL and network connection", "INFO")
        return None
    except requests.exceptions.RequestException as e:
        log_debug(f"[X] Request error: {e}", "ERROR")
        return None
    except Exception as e:
        # Catch-all to handle non-requests exceptions in tests/mocks
        log_debug(f"[X] Unexpected error: {e}", "ERROR")
        return None


def get_first_report_file_uuid(
    object_type: str, object_uuid: str, http_client=requests
) -> str:
    """
    Returns the file UUID of the first PDF or DOCX file for the given object, or None if not found.
    Includes enhanced filtering and logging for debugging.
    """
    log_debug("=== Starting get_first_report_file_uuid ===")

    files_info = list_pure_files(object_type, object_uuid, http_client)
    if not files_info or "items" not in files_info:
        log_debug("No files found for this object.", "WARNING")
        return None

    log_debug(f"Searching through {len(files_info['items'])} files for PDF or DOCX...")

    # Supported file extensions (case insensitive)
    supported_extensions = [".pdf", ".docx", ".doc"]

    for i, file_obj in enumerate(files_info["items"]):
        filename = file_obj.get("fileName", "").lower()
        file_uuid = file_obj.get("uuid")
        mime_type = file_obj.get("mimeType", "")

        log_debug(f"Checking file {i+1}: '{filename}' (UUID: {file_uuid})")
        log_debug(f"  MIME type: {mime_type}")

        # Check by file extension
        for ext in supported_extensions:
            if filename.endswith(ext):
                log_debug(f"[OK] Found suitable file: '{filename}' with extension '{ext}'")
                return file_uuid

        # Additional check by MIME type for files without proper extensions
        if any(mime in mime_type.lower() for mime in ["pdf", "word", "document"]):
            log_debug(f"[OK] Found suitable file by MIME type: '{filename}' ({mime_type})")
            return file_uuid

    log_debug("[X] No PDF, DOC, or DOCX files found for this object.", "WARNING")
    log_debug("Available file types:", "INFO")
    for file_obj in files_info["items"]:
        filename = file_obj.get("fileName", "Unknown")
        log_debug(f"  - {filename}")

    return None


def download_pure_file(
    object_type: str,
    object_uuid: str,
    file_uuid: str = None,
    output_path: str = None,
    http_client=requests,
) -> None:
    """
    Download a file from the Pure API for any object type. If file_uuid is None, will auto-select first PDF/DOCX file.
    Enhanced with comprehensive error handling and progress tracking.
    """
    log_debug("=== Starting download_pure_file ===")
    log_debug(
        f"Parameters - object_type: '{object_type}', object_uuid: '{object_uuid}', file_uuid: '{file_uuid}', output_path: '{output_path}'"
    )

    # Parameter validation
    if not check_api_key(PURE_API_KEY):
        log_debug("API key validation failed", "ERROR")
        return

    if not object_type or not isinstance(object_type, str):
        log_debug(
            "Error: object_type must be a non-empty string. Example: 'research-outputs', 'persons', etc.",
            "ERROR",
        )
        return

    if not object_uuid or not isinstance(object_uuid, str):
        log_debug(
            "Error: object_uuid must be a non-empty string. Example: '123e4567-e89b-12d3-a456-426614174000'",
            "ERROR",
        )
        return

    # Auto-select file if not specified
    if file_uuid is None:
        log_debug("No file_uuid provided, attempting to auto-select PDF/DOCX file...")
        file_uuid = get_first_report_file_uuid(object_type, object_uuid, http_client)
        if not file_uuid:
            log_debug("No suitable file found to download.", "ERROR")
            return

    if not isinstance(file_uuid, str):
        log_debug("Error: file_uuid must be a string.", "ERROR")
        return

    if output_path is not None and not isinstance(output_path, str):
        log_debug(
            "Error: output_path must be a string if provided. Example: 'output.pdf'",
            "ERROR",
        )
        return

    # Construct download URL
    url = f"{BASE_API_URL}/{object_type}/{object_uuid}/files/{file_uuid}"
    log_debug(f"Download URL: {url}")

    # Prepare headers for file download
    headers = {
        "api-key": PURE_API_KEY,
        "Accept": "application/octet-stream",
        "User-Agent": "Pure-API-Client/1.0",
    }
    log_debug(
        f"Request headers: {json.dumps({k: v if k != 'api-key' else '[REDACTED]' for k, v in headers.items()}, indent=2)}"
    )

    try:
        log_debug("Sending download request...")
        response = http_client.get(
            url, headers=headers, stream=True, timeout=300
        )  # 5 minute timeout for large files

        log_debug(f"Response status code: {response.status_code}")
        log_debug(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")

        if response.status_code == 200:
            log_debug("[OK] Download request successful!")

            # Extract filename and extension from Content-Disposition header
            content_disp = response.headers.get("Content-Disposition", "")
            content_length = response.headers.get("Content-Length")
            content_type = response.headers.get("Content-Type", "unknown")

            log_debug(f"Content-Disposition: {content_disp}")
            log_debug(f"Content-Length: {content_length} bytes")
            log_debug(f"Content-Type: {content_type}")

            # Determine file extension
            ext = ""
            filename_from_header = ""
            if "filename=" in content_disp:
                # Extract filename from Content-Disposition header
                filename_from_header = content_disp.split("filename=")[-1].strip("\"'")
                ext = os.path.splitext(filename_from_header)[1]
                log_debug(f"Filename from header: {filename_from_header}")
            elif "pdf" in content_type.lower():
                ext = ".pdf"
            elif "word" in content_type.lower() or "document" in content_type.lower():
                ext = ".docx"

            # Set output path if not provided
            if not output_path:
                if filename_from_header:
                    output_path = filename_from_header
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = f"downloaded_pure_file_{timestamp}{ext}"

            log_debug(f"Saving to: {output_path}")

            # Download with progress tracking
            try:
                total_size = int(content_length) if content_length else 0
                downloaded = 0

                with open(output_path, "wb") as out_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            out_file.write(chunk)
                            downloaded += len(chunk)

                            # Log progress for large files
                            if (
                                total_size > 0 and downloaded % (1024 * 1024) == 0
                            ):  # Every MB
                                progress = (downloaded / total_size) * 100
                                log_debug(
                                    f"Download progress: {progress:.1f}% ({downloaded}/{total_size} bytes)"
                                )

                file_size = os.path.getsize(output_path)
                log_debug(f"[OK] Download completed! File size: {file_size} bytes")
                log_debug(f"[OK] File saved to: {os.path.abspath(output_path)}")
                print(f"Success: File downloaded to {output_path}")

                # Verify file was downloaded correctly
                if total_size > 0 and file_size != total_size:
                    log_debug(
                        f"Warning: Downloaded file size ({file_size}) doesn't match expected size ({total_size})",
                        "WARNING",
                    )

            except IOError as e:
                log_debug(f"[X] File I/O error: {e}", "ERROR")
                return

        elif response.status_code == 401:
            log_debug("[X] Authentication failed - check your API key", "ERROR")
        elif response.status_code == 403:
            log_debug("[X] Access forbidden - check permissions for this file", "ERROR")
        elif response.status_code == 404:
            log_debug(
                "[X] File not found - check object_type, object_uuid, and file_uuid",
                "ERROR",
            )
        elif response.status_code == 429:
            log_debug("[X] Rate limit exceeded - wait before retrying", "ERROR")
        else:
            log_debug(f"[X] Unexpected status code: {response.status_code}", "ERROR")

        if response.status_code != 200:
            log_debug(f"Error response content: {response.text[:1000]}", "DEBUG")

    except requests.exceptions.Timeout:
        log_debug("[X] Download timed out after 5 minutes", "ERROR")
    except requests.exceptions.ConnectionError as e:
        log_debug(f"[X] Connection error: {e}", "ERROR")
        log_debug("Check your BASE_API_URL and network connection", "INFO")
    except requests.exceptions.RequestException as e:
        log_debug(f"[X] Request error: {e}", "ERROR")


def search_research_outputs(query: str = "", size: int = 10, http_client=requests):
    """
    Search for research outputs to find UUIDs for testing.
    This is helpful for finding objects to test with.
    """
    log_debug(f"=== Searching research outputs: '{query}' ===")

    if not check_api_key(PURE_API_KEY):
        return None

    url = f"{BASE_API_URL}/research-outputs"
    headers = {
        "api-key": PURE_API_KEY,
        "Accept": "application/json",
        "User-Agent": "Pure-API-Client/1.0",
    }

    params = {"size": size}
    if query:
        params["q"] = query

    try:
        log_debug(f"Searching URL: {url}")
        log_debug(f"Search parameters: {params}")

        response = http_client.get(url, headers=headers, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json()
            log_debug(f"Found {data.get('count', 0)} total results")

            print("\n=== SEARCH RESULTS ===")
            for i, item in enumerate(data.get("items", [])[:size]):
                uuid = item.get("uuid", "N/A")
                title = item.get("title", {})
                title_text = (
                    title.get("value", "No title")
                    if isinstance(title, dict)
                    else str(title)
                )

                print(f"\n{i+1}. UUID: {uuid}")
                print(
                    f"   Title: {title_text[:100]}{'...' if len(title_text) > 100 else ''}"
                )
                print(
                    f"   Type: {item.get('type', {}).get('term', {}).get('text', 'Unknown')}"
                )

            return data
        else:
            log_debug(f"Search failed with status {response.status_code}", "ERROR")
            return None

    except requests.exceptions.RequestException as e:
        log_debug(f"Search error: {e}", "ERROR")
        return None


def validate_uuid_format(uuid_string: str) -> bool:
    """
    Validate UUID format (basic check).
    """
    import re

    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(uuid_pattern, uuid_string, re.IGNORECASE))


# Quick test function for easy debugging
def quick_test():
    """
    Quick test function to verify API connectivity and configuration.
    Call this function to do a basic health check.
    """
    print("\n" + "=" * 50)
    print("QUICK API TEST")
    print("=" * 50)

    # Test 1: Configuration
    print("1. Configuration Check:")
    api_key_ok = check_api_key(PURE_API_KEY)
    url_ok = validate_base_url(BASE_API_URL)
    print(f"   API Key: {'[OK]' if api_key_ok else '[X]'}")
    print(f"   Base URL: {'[OK]' if url_ok else '[X]'}")

    if not (api_key_ok and url_ok):
        print("\n❌ Configuration issues found. Please fix before proceeding.")
        return False

    # Test 2: Connectivity
    print("\n2. API Connectivity:")
    connection_ok = test_api_connection()
    print(f"   Connection: {'[OK]' if connection_ok else '[X]'}")

    if not connection_ok:
        print("\n❌ Cannot connect to API. Check network and credentials.")
        return False

    # Test 3: Search capability
    print("\n3. Search Test:")
    try:
        results = search_research_outputs("", 3)  # Get 3 recent items
        search_ok = results is not None
        print(f"   Search: {'[OK]' if search_ok else '[X]'}")

        if search_ok and results.get("items"):
            print(f"   Found {len(results['items'])} sample items for testing")

    except Exception as e:
        print(f"   Search: [X] ({e})")
        search_ok = False

    print("\n" + "=" * 50)
    if api_key_ok and url_ok and connection_ok:
        print("✅ All tests passed! API is ready to use.")
        return True
    else:
        print("❌ Some tests failed. Check configuration and network.")
        return False


def test_api_connection(http_client=requests) -> bool:
    """
    Test basic connectivity to the Pure API endpoint.
    Returns True if connection is successful, False otherwise.
    """
    log_debug("=== Testing API Connection ===")

    if not check_api_key(PURE_API_KEY):
        return False

    # Test with a simple endpoint that should always be available
    test_url = f"{BASE_API_URL}/research-outputs"
    headers = {
        "api-key": PURE_API_KEY,
        "Accept": "application/json",
        "User-Agent": "Pure-API-Client/1.0",
    }

    try:
        log_debug(f"Testing connection to: {test_url}")
        response = http_client.get(
            test_url, headers=headers, timeout=10, params={"size": 1}
        )

        log_debug(f"Test response status: {response.status_code}")

        if response.status_code == 200:
            log_debug("[OK] API connection test successful!")
            return True
        elif response.status_code == 401:
            log_debug("[X] Authentication failed - check your API key", "ERROR")
        elif response.status_code == 403:
            log_debug("[X] Access forbidden - check API permissions", "ERROR")
        else:
            log_debug(f"[X] Unexpected response: {response.status_code}", "ERROR")

        return False

    except requests.exceptions.RequestException as e:
        log_debug(f"[X] Connection test failed: {e}", "ERROR")
        return False


def print_usage_examples():
    """
    Print detailed usage examples and troubleshooting information.
    """
    print("\n" + "=" * 80)
    print("PURE API FILE DOWNLOADER - USAGE GUIDE")
    print("=" * 80)

    print("\n1. CONFIGURATION REQUIRED:")
    print(
        f"   • Set PURE_API_KEY to your actual API key (currently: {'[SET]' if PURE_API_KEY != 'YOUR_API_KEY' else '[NOT SET]'})"
    )
    print(f"   • Set BASE_API_URL to your institution's Pure API URL")
    print(f"     Current: {BASE_API_URL}")
    print(f"     Example: https://youruni.elsevierpure.com/ws/api")

    print("\n2. CSV MODE (RECOMMENDED):")
    print("   • Place your CSV file in the same directory as this script")
    print("   • CSV should have a column with Pure IDs (default: 'Pure ID')")
    print("   • Script will automatically:")
    print("     - Identify whether IDs are object IDs or file IDs")
    print("     - Test first few entries to determine ID type")
    print("     - Download files from identified objects")
    print("   ")
    print("   Example CSV structure:")
    print("   Year,Title,Pure ID")
    print("   2020,Research Paper Title,27139086")
    print("   2021,Another Paper,46773789")

    print("\n3. SINGLE ID MODE:")
    print("   # List files for a research output:")
    print("   list_pure_files('research-outputs', 'your-uuid-here')")
    print("   ")
    print("   # Download first PDF/DOCX file automatically:")
    print("   download_pure_file('research-outputs', 'your-uuid-here')")
    print("   ")
    print("   # Download specific file:")
    print(
        "   download_pure_file('research-outputs', 'object-uuid', 'file-uuid', 'output.pdf')"
    )

    print("\n4. PURE ID TYPES:")
    print("   • Object IDs: Identify research outputs, persons, etc.")
    print("     - Often numeric (e.g., 27139086) or UUID format")
    print("     - These are what you typically find in CSV exports")
    print("   • File IDs: Identify specific files within objects")
    print("     - Usually UUID format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)")
    print("     - Script will auto-detect and handle appropriately")

    print("\n5. SUPPORTED OBJECT TYPES:")
    print("   • research-outputs (most common for documents)")
    print("   • persons")
    print("   • organisational-units")
    print("   • activities")
    print("   • projects")

    print("\n6. TROUBLESHOOTING:")
    print("   • HTTP 401: Check your API key")
    print("   • HTTP 403: Check permissions for the object")
    print("   • HTTP 404: Check object type and UUID")
    print("   • HTTP 429: Rate limit exceeded, wait before retrying")
    print("   • Connection errors: Check BASE_API_URL and network")
    print("   • 'Numeric ID detected': May need special handling for your Pure system")

    print("\n7. BATCH PROCESSING:")
    print("   • Set MAX_DOWNLOADS to a small number for testing (e.g., 3)")
    print("   • Set to None to process all entries in CSV")
    print("   • Files are saved to 'downloads' directory by default")
    print("   • Filenames include title and Pure ID for identification")

    print("=" * 80)


if __name__ == "__main__":
    print_usage_examples()

    # Test API connection first
    log_debug("\n=== STARTING PURE API SCRIPT ===")

    if not test_api_connection():
        log_debug("API connection test failed. Please check configuration.", "ERROR")
        print("\nCONFIGURATION CHECK FAILED!")
        print("Please verify:")
        print("1. PURE_API_KEY is set correctly in config.py")
        print("2. BASE_API_URL points to your institution's Pure API")
        print("3. You have network connectivity")
        print("\nRun: python setup_config.py to configure settings")
        exit(1)

    # Configuration is loaded from config.py at import time
    # Variables available: CSV_FILE_PATH, OUTPUT_DIRECTORY, ID_COLUMN, MAX_DOWNLOADS

    # Single ID testing configuration (for manual testing only)
    OBJECT_TYPE = "research-outputs"
    OBJECT_UUID = "pure-object-uuid-here"
    FILE_UUID = None
    OUTPUT_PATH = None

    log_debug(f"Configuration:")
    log_debug(f"  CSV_FILE_PATH: {CSV_FILE_PATH}")
    log_debug(f"  OUTPUT_DIRECTORY: {OUTPUT_DIRECTORY}")
    log_debug(f"  ID_COLUMN: {ID_COLUMN}")
    log_debug(f"  MAX_DOWNLOADS: {MAX_DOWNLOADS}")

    # Choose operation mode
    if os.path.exists(CSV_FILE_PATH):
        print(f"\n--- CSV MODE: Processing {CSV_FILE_PATH} ---")

        # Option 1: Test ID identification for first few entries
        print("\n=== TESTING PURE ID IDENTIFICATION ===")
        entries = load_pure_ids_from_csv(CSV_FILE_PATH, ID_COLUMN)

        if entries:
            # Test first 3 entries to identify ID types
            test_entries = entries[:3]
            for i, entry in enumerate(test_entries, 1):
                print(f"\n--- Testing entry {i}: {entry['pure_id']} ---")
                print(f"Title: {entry['title'][:80]}...")

                id_info = identify_pure_id_type(entry["pure_id"])

                print("Test Results:")
                if id_info.get("is_object_id"):
                    print(f"  [OK] Identified as {id_info['object_type']} object ID")
                    if id_info.get("title"):
                        print(f"  [OK] Object title: {id_info['title'][:60]}...")
                else:
                    print(f"  [X] Could not identify as standard object ID")
                    if id_info.get("test_results", {}).get("numeric_id"):
                        print(f"  ⚠ Numeric ID detected - may need special handling")

                print(f"  Status codes: {id_info.get('test_results', {})}")

            # Option 2: Batch download
            print(f"\n=== STARTING BATCH DOWNLOAD ===")
            print(f"Downloading files for max {MAX_DOWNLOADS} entries from CSV")

            # Start batch download:
            results = batch_download_from_csv(CSV_FILE_PATH, OUTPUT_DIRECTORY, ID_COLUMN, MAX_DOWNLOADS)
            print(f"\nBatch download results: {results}")

    else:
        print(f"\n--- SINGLE ID MODE ---")
        print(f"CSV file '{CSV_FILE_PATH}' not found.")
        print("Falling back to single ID testing...")

        if OBJECT_UUID == "pure-object-uuid-here":
            print("\nWARNING: Please update OBJECT_UUID with a real UUID.")
            print("Or place your CSV file in the same directory as this script.")
        else:
            # Single ID operations
            print(f"\n--- Listing files for {OBJECT_TYPE}/{OBJECT_UUID} ---")
            list_pure_files(OBJECT_TYPE, OBJECT_UUID)

            print(f"\n--- Downloading file from {OBJECT_TYPE}/{OBJECT_UUID} ---")
            download_pure_file(OBJECT_TYPE, OBJECT_UUID, FILE_UUID, OUTPUT_PATH)

    log_debug("=== SCRIPT COMPLETED ===")

# QUICK START INSTRUCTIONS:
# 1. Set your PURE_API_KEY and BASE_API_URL at the top of this file
# 2. Place your CSV file in the same directory as this script
# 3. Run: python download_pure_file.py
# 4. Script will automatically test Pure ID types and offer download options
#
# CSV FORMAT EXPECTED:
# - Column named 'Pure ID' (or modify ID_COLUMN variable)
# - Pure IDs can be numeric (object IDs) or UUID format (object/file IDs)
# - Additional columns like 'Title', 'Year' help with identification
#
# ID TYPE HANDLING:
# - Object IDs (like 27139086): Used to find research outputs/persons
# - File IDs (UUID format): Need parent object ID (script will detect)
# - Numeric IDs: Most likely object IDs, script will test automatically
#
# DEBUGGING TIPS:
# - All functions include detailed logging with timestamps
# - Script tests ID types before attempting downloads
# - Use MAX_DOWNLOADS=3 for initial testing
# - Check log messages to understand what's happening
# - HTTP status codes and response headers are logged
# - File download progress is tracked for large files
# - Use quick_test() function to verify API connectivity
