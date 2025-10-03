"""
Configuration Helper for Pure API Downloader
===========================================

This script helps you set up the configuration for the Pure API downloader.
Run this first to configure your API key, base URL, and other settings.

The configuration is stored in config.py, which is easier to edit and manage.
"""

import os
import re


def setup_configuration():
    """Interactive setup for Pure API configuration."""

    print("🔧 Pure API Downloader Configuration Setup")
    print("=" * 50)
    print()

    # Get current script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.py")

    # Check if config.py exists
    if not os.path.exists(config_file):
        print("❌ Error: config.py not found in current directory")
        print("   Please ensure config.py exists before running setup")
        return False

    print("📍 Found config.py")
    print()

    # Read current configuration
    with open(config_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract current values using more flexible regex
    api_key_match = re.search(r'PURE_API_KEY\s*=\s*"([^"]*)"', content)
    base_url_match = re.search(r'BASE_API_URL\s*=\s*"([^"]*)"', content)
    csv_file_match = re.search(r'CSV_FILE_PATH\s*=\s*"([^"]*)"', content)
    id_column_match = re.search(r'ID_COLUMN\s*=\s*"([^"]*)"', content)
    output_dir_match = re.search(r'OUTPUT_DIRECTORY\s*=\s*"([^"]*)"', content)
    max_downloads_match = re.search(r'MAX_DOWNLOADS\s*=\s*(\w+)', content)

    current_api_key = api_key_match.group(1) if api_key_match else "YOUR_API_KEY"
    current_base_url = (
        base_url_match.group(1)
        if base_url_match
        else "https://yourinstitution.elsevierpure.com/ws/api"
    )
    current_csv_file = csv_file_match.group(1) if csv_file_match else "your_file.csv"
    current_id_column = id_column_match.group(1) if id_column_match else "Pure ID"
    current_output_dir = output_dir_match.group(1) if output_dir_match else "downloads"
    current_max_downloads = max_downloads_match.group(1) if max_downloads_match else "None"

    print("📋 Current Configuration:")
    print(
        f"   API Key: {'[SET - ' + current_api_key[:10] + '...]' if current_api_key != 'YOUR_API_KEY' and len(current_api_key) > 10 else '[NOT SET]'}"
    )
    print(f"   Base URL: {current_base_url}")
    print(f"   CSV File: {current_csv_file}")
    print(f"   ID Column: '{current_id_column}'")
    print(f"   Output Directory: {current_output_dir}")
    print(f"   Max Downloads: {current_max_downloads}")
    print()

    # Get new API key
    print("🔑 API Key Setup:")
    print("   Contact your Pure system administrator to get your API key.")
    print("   It should be a long string of letters, numbers, and dashes.")
    print()

    new_api_key = input(
        "Enter your Pure API key (or press Enter to keep current): "
    ).strip()
    if not new_api_key:
        new_api_key = current_api_key
        print(
            f"   Keeping current API key: {'[SET]' if new_api_key != 'YOUR_API_KEY' else '[NOT SET]'}"
        )
    else:
        print(f"   ✓ API key set (length: {len(new_api_key)})")

    print()

    # Get new base URL
    print("🌐 Base URL Setup:")
    print("   This is your institution's Pure API endpoint.")
    print("   Format: https://[yourinstitution].elsevierpure.com/ws/api")
    print("   Examples:")
    print("     https://scion.elsevierpure.com/ws/api")
    print("     https://university.elsevierpure.com/ws/api")
    print()

    new_base_url = input(
        "Enter your Pure API base URL (or press Enter to keep current): "
    ).strip()
    if not new_base_url:
        new_base_url = current_base_url
        print(f"   Keeping current URL: {new_base_url}")
    else:
        # Validate URL format
        if not new_base_url.startswith("https://"):
            print("   ⚠️  Warning: URL should start with https://")
        if not new_base_url.endswith("/ws/api"):
            print("   ⚠️  Warning: URL should end with /ws/api")
        print(f"   ✓ Base URL set: {new_base_url}")

    print()

    # Get CSV file path
    print("📁 CSV File Setup:")
    print("   Path to your CSV file with Pure IDs")
    print(f"   Current: {current_csv_file}")
    print()

    new_csv_file = input(
        "Enter CSV file path (or press Enter to keep current): "
    ).strip()
    if not new_csv_file:
        new_csv_file = current_csv_file
        print(f"   Keeping current: {new_csv_file}")
    else:
        print(f"   ✓ CSV file set: {new_csv_file}")

    print()

    # Get max downloads
    print("⚙️  Download Limit Setup:")
    print("   How many entries to download from CSV?")
    print("   Enter a number for testing (e.g., 3, 5, 10)")
    print("   Or enter 'all' to download everything")
    print(f"   Current: {current_max_downloads}")
    print()

    new_max_downloads = input(
        "Enter max downloads (or press Enter to keep current): "
    ).strip().lower()
    if not new_max_downloads:
        new_max_downloads = current_max_downloads
        print(f"   Keeping current: {new_max_downloads}")
    else:
        if new_max_downloads in ['all', 'none']:
            new_max_downloads = "None"
            print(f"   ✓ Will download all entries")
        elif new_max_downloads.isdigit():
            print(f"   ✓ Will download max {new_max_downloads} entries")
        else:
            print(f"   ⚠️  Invalid input, keeping current: {current_max_downloads}")
            new_max_downloads = current_max_downloads

    print()

    # Confirm changes
    print("📝 Summary of Changes:")
    api_key_display = f"{new_api_key[:10]}..." if len(new_api_key) > 10 else new_api_key
    print(f"   API Key: {api_key_display}")
    print(f"   Base URL: {new_base_url}")
    print(f"   CSV File: {new_csv_file}")
    print(f"   ID Column: {current_id_column}")
    print(f"   Output Directory: {current_output_dir}")
    print(f"   Max Downloads: {new_max_downloads}")
    print()

    confirm = input("Apply these changes? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Configuration cancelled")
        return False

    # Apply changes
    try:
        # Update the configuration in the file
        content = re.sub(
            r'(PURE_API_KEY\s*=\s*)"[^"]*"', 
            f'\\1"{new_api_key}"', 
            content
        )

        content = re.sub(
            r'(BASE_API_URL\s*=\s*)"[^"]*"', 
            f'\\1"{new_base_url}"', 
            content
        )

        content = re.sub(
            r'(CSV_FILE_PATH\s*=\s*)"[^"]*"', 
            f'\\1"{new_csv_file}"', 
            content
        )

        content = re.sub(
            r'(MAX_DOWNLOADS\s*=\s*)\w+', 
            f'\\1{new_max_downloads}', 
            content
        )

        # Write back to file
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(content)

        print("✅ Configuration updated successfully in config.py!")
        print()
        print("🚀 Next Steps:")
        print("1. Verify your CSV file is in place")
        print("2. Run: python download_pure_file.py")
        print("3. The script will read settings from config.py")
        print()
        print("💡 Tip: You can also edit config.py directly with any text editor")

        return True

    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False


def validate_current_config():
    """Check if current configuration is valid."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.py")

    if not os.path.exists(config_file):
        return False, "config.py not found"

    try:
        # Import and validate
        import sys
        sys.path.insert(0, script_dir)
        import config
        
        is_valid, message = config.validate_config()
        return is_valid, message
        
    except Exception as e:
        return False, f"Error loading config: {e}"


if __name__ == "__main__":
    print("🔍 Checking current configuration...")

    is_valid, message = validate_current_config()

    if is_valid:
        print(f"✅ {message}")
        print()
        response = (
            input("Configuration is already set. Do you want to change it? (y/n): ")
            .strip()
            .lower()
        )
        if response != "y":
            print("👍 Configuration check complete!")
            exit(0)
    else:
        print(f"⚠️  {message}")
        print()

    success = setup_configuration()
    exit(0 if success else 1)
