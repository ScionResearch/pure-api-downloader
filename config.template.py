"""
Pure API Configuration Template
================================

INSTRUCTIONS:
1. Copy this file to config.py
2. Edit the values below with your actual settings
3. Run: python setup_config.py for interactive setup
   OR edit this file directly

IMPORTANT: config.py contains your API key and should NOT be committed to version control
           (it's already in .gitignore)
"""

# ============================================================================
# API Authentication
# ============================================================================

# Your Pure API key (get this from your Pure system administrator)
# Example: "12345678-d656-42c9-8d3f-a23ea309df03"
PURE_API_KEY = "YOUR_API_KEY"

# Your institution's Pure API base URL
# Format: https://[yourinstitution].elsevierpure.com/ws/api
# Example: "https://scion.elsevierpure.com/ws/api"
BASE_API_URL = "https://yourinstitution.elsevierpure.com/ws/api"


# ============================================================================
# CSV File Settings
# ============================================================================

# Path to your CSV file containing Pure IDs
# Can be absolute path or relative to this directory
CSV_FILE_PATH = "your_file.csv"

# Name of the column containing Pure IDs
# Default is "Pure ID"
ID_COLUMN = "Pure ID"


# ============================================================================
# Download Settings
# ============================================================================

# Directory where downloaded files will be saved
# Will be created if it doesn't exist
OUTPUT_DIRECTORY = "downloads"

# Maximum number of entries to process from CSV
# Set to None to process all entries
# Set to a number (e.g., 3, 5, 10) for testing
MAX_DOWNLOADS = 3


# ============================================================================
# Advanced Settings (usually don't need to change these)
# ============================================================================

# File types to download (empty list = all types)
# Example: [".pdf", ".docx"] to only download PDFs and Word documents
DOWNLOAD_FILE_TYPES = []

# Request timeout in seconds
REQUEST_TIMEOUT = 30

# Download chunk size in bytes (for streaming large files)
DOWNLOAD_CHUNK_SIZE = 8192


# ============================================================================
# Configuration Validation
# ============================================================================

def validate_config():
    """
    Validates the configuration settings.
    Returns: (is_valid, error_message)
    """
    issues = []
    
    # Check API key
    if not PURE_API_KEY or PURE_API_KEY == "YOUR_API_KEY":
        issues.append("API key not set")
    elif len(PURE_API_KEY) < 10:
        issues.append("API key seems too short")
    
    # Check base URL
    if "yourinstitution" in BASE_API_URL:
        issues.append("Base URL still contains 'yourinstitution' placeholder")
    elif not BASE_API_URL.startswith("https://"):
        issues.append("Base URL should use HTTPS")
    elif not BASE_API_URL.endswith("/ws/api"):
        issues.append("Base URL should end with '/ws/api'")
    
    # Check CSV file
    if CSV_FILE_PATH == "your_file.csv":
        issues.append("CSV file path not set")
    
    if issues:
        return False, "; ".join(issues)
    
    return True, "Configuration valid"


# ============================================================================
# Auto-validate on import (shows warning but doesn't stop execution)
# ============================================================================

if __name__ != "__main__":
    is_valid, message = validate_config()
    if not is_valid:
        import sys
        print(f"⚠️  Configuration issues detected: {message}", file=sys.stderr)
        print("   Run: python setup_config.py to fix configuration", file=sys.stderr)
