"""
Configuration Helper for Pure API Downloader
===========================================

This script provides an interactive way to create or update the local `.env`
file used by `config.py`.

Why this matters:
- semi-technical users can edit a simple text file instead of Python code
- API keys stay out of source files
- setup remains easy to rerun whenever paths or limits change
"""

from __future__ import annotations

import importlib
import os
from pathlib import Path


DEFAULT_ENV_SETTINGS = {
    "PURE_API_KEY": "YOUR_API_KEY",
    "BASE_API_URL": "https://yourinstitution.elsevierpure.com/ws/api",
    "DISCOVERY_SEARCH_TERMS": "example topic one, example topic two",
    "APPROVED_DOWNLOAD_PILOT_SIZE": "25",
}


def get_env_file_path() -> str:
    """Return the `.env` path, allowing tests to override it."""
    override_path = os.environ.get("PURE_DOWNLOADER_ENV_PATH")
    if override_path:
        return override_path

    script_dir = Path(__file__).resolve().parent
    return str(script_dir / ".env")


def get_config_file_path() -> str:
    """Backward-compatible wrapper kept for older tests and tooling."""
    return get_env_file_path()


def _parse_env_file(env_file: str) -> dict[str, str]:
    if not os.path.exists(env_file):
        return {}

    settings: dict[str, str] = {}
    with open(env_file, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            settings[key.strip()] = value.strip().strip('"').strip("'")
    return settings


def _render_env_file(settings: dict[str, str]) -> str:
    """Render a friendly, commented `.env` file for local users."""
    return (
        "# Pure API Downloader local settings\n"
        "# --------------------------------\n"
        "# Keep this file on your machine only. Do not commit real credentials.\n\n"
        "# Required Pure API credentials\n"
        f"PURE_API_KEY={settings['PURE_API_KEY']}\n"
        f"BASE_API_URL={settings['BASE_API_URL']}\n\n"
        "# Discovery workflow settings\n"
        "# Provide a comma-separated list of search terms or phrases.\n"
        f"DISCOVERY_SEARCH_TERMS={settings['DISCOVERY_SEARCH_TERMS']}\n\n"
        "# Approved download workflow settings\n"
        f"APPROVED_DOWNLOAD_PILOT_SIZE={settings['APPROVED_DOWNLOAD_PILOT_SIZE']}\n"
    )


def setup_configuration():
    """Interactively create or update the local `.env` configuration file."""

    print("🔧 Pure API Downloader Configuration Setup")
    print("=" * 50)
    print()

    try:
        env_file = get_env_file_path()
    except Exception as e:
        print(f"❌ Error locating .env file: {e}")
        return False

    if os.path.exists(env_file):
        print(f"📍 Found existing .env file at: {env_file}")
    else:
        print(f"📍 No .env file found yet. A new one will be created at: {env_file}")
    print()

    # Read current configuration
    try:
        current_settings = {**DEFAULT_ENV_SETTINGS, **_parse_env_file(env_file)}
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False

    current_api_key = current_settings["PURE_API_KEY"]
    current_base_url = current_settings["BASE_API_URL"]
    current_search_terms = current_settings["DISCOVERY_SEARCH_TERMS"]
    current_pilot_size = current_settings["APPROVED_DOWNLOAD_PILOT_SIZE"]

    print("📋 Current Configuration:")
    print(
        f"   API Key: {'[SET - ' + current_api_key[:10] + '...]' if current_api_key != 'YOUR_API_KEY' and len(current_api_key) > 10 else '[NOT SET]'}"
    )
    print(f"   Base URL: {current_base_url}")
    print(f"   Search Terms: {current_search_terms}")
    print(f"   Approved Pilot Size: {current_pilot_size}")
    print()

    # Get new API key
    print("🔑 API Key Setup:")
    print("   Contact your Pure system administrator to get your API key.")
    print("   This value is stored in `.env`, which stays local to your machine.")
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

    # Get search terms
    print("🔎 Discovery Search Terms:")
    print("   Enter a comma-separated list of search terms or phrases.")
    print("   Example: carbon sequestration,biosecurity,remote sensing")
    print(f"   Current: {current_search_terms}")
    print()

    new_search_terms = input(
        "Enter discovery search terms (or press Enter to keep current): "
    ).strip()
    if not new_search_terms:
        new_search_terms = current_search_terms
        print(f"   Keeping current: {new_search_terms}")
    else:
        print(f"   ✓ Search terms set: {new_search_terms}")

    print()

    # Get approved pilot size
    print("⚙️  Approved Download Pilot Size:")
    print("   This controls how many approved records are downloaded in one run by default.")
    print(f"   Current: {current_pilot_size}")
    print()

    new_pilot_size = input(
        "Enter approved pilot size (or press Enter to keep current): "
    ).strip()
    if not new_pilot_size:
        new_pilot_size = current_pilot_size
        print(f"   Keeping current: {new_pilot_size}")
    else:
        if new_pilot_size.isdigit() and int(new_pilot_size) > 0:
            print(f"   ✓ Approved pilot size set to {new_pilot_size}")
        else:
            print(f"   ⚠️  Invalid input, keeping current: {current_pilot_size}")
            new_pilot_size = current_pilot_size

    print()

    # Confirm changes
    print("📝 Summary of Changes:")
    api_key_display = f"{new_api_key[:10]}..." if len(new_api_key) > 10 else new_api_key
    print(f"   API Key: {api_key_display}")
    print(f"   Base URL: {new_base_url}")
    print(f"   Search Terms: {new_search_terms}")
    print(f"   Approved Pilot Size: {new_pilot_size}")
    print()

    confirm = input("Apply these changes? (y/n): ").strip().lower()
    if confirm != "y":
        print("❌ Configuration cancelled")
        return False

    # Apply changes
    try:
        settings_to_write = {
            **current_settings,
            "PURE_API_KEY": new_api_key,
            "BASE_API_URL": new_base_url,
            "DISCOVERY_SEARCH_TERMS": new_search_terms,
            "APPROVED_DOWNLOAD_PILOT_SIZE": new_pilot_size,
        }

        Path(env_file).parent.mkdir(parents=True, exist_ok=True)
        with open(env_file, "w", encoding="utf-8") as handle:
            handle.write(_render_env_file(settings_to_write))

        print("✅ Configuration updated successfully in .env!")
        print()
        print("🚀 Next Steps:")
        print("1. Review .env to confirm the values look right")
        print("2. Run: python pure_discovery.py")
        print("3. Review the generated CSV before downloading approved files")
        print()
        print("💡 Tip: You can also edit .env directly with any text editor")

        return True

    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        return False


def validate_current_config():
    """Check if current configuration is valid."""
    try:
        env_file = get_env_file_path()

        if not os.path.exists(env_file):
            return False, ".env not found"

        import config

        config = importlib.reload(config)
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
