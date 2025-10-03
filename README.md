# Pure API File Downloader

A Python tool to batch download research output files from the Elsevier Pure API using a CSV list of Pure IDs.

## 📋 Features

- ✅ Batch download files from Pure API using CSV input
- ✅ Supports both numeric Pure IDs and UUIDs
- ✅ Automatic file type detection (PDF, DOCX, etc.)
- ✅ Configurable download limits for testing
- ✅ Comprehensive error handling and logging
- ✅ CSV encoding auto-detection (UTF-8, Windows cp1252, Latin-1)
- ✅ Secure configuration management

## 🚀 Quick Start

### 1. Initial Setup

```bash
# First time setup - configure your API credentials
python setup_config.py
```

This will prompt you for:
- Your Pure API key
- Your institution's Pure API URL
- CSV file path
- Download settings

### 2. Run the Downloader

```bash
python download_pure_file.py
```

The script will:
1. Test API connection
2. Load Pure IDs from your CSV
3. Download all attached files to the `downloads/` directory

## 📁 File Structure

```
pure_downloader/
├── config.py              # Your configuration (gitignored - contains API key)
├── config.template.py     # Template for creating config.py
├── download_pure_file.py  # Main downloader script
├── setup_config.py        # Interactive configuration utility
├── .gitignore            # Protects sensitive config files
├── README.md             # This file
└── downloads/            # Downloaded files go here (created automatically)
```

## ⚙️ Configuration

### Option 1: Interactive Setup (Recommended)

```bash
python setup_config.py
```

### Option 2: Manual Configuration

1. Copy the template:
   ```bash
   copy config.template.py config.py
   ```

2. Edit `config.py` with your settings:
   ```python
   PURE_API_KEY = "your-api-key-here"
   BASE_API_URL = "https://yourinstitution.elsevierpure.com/ws/api"
   CSV_FILE_PATH = "example.csv"
   MAX_DOWNLOADS = None  # Or set to a number for testing
   ```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `PURE_API_KEY` | Your Pure API key | *Required* |
| `BASE_API_URL` | Your Pure API endpoint | *Required* |
| `CSV_FILE_PATH` | Path to CSV with Pure IDs | `"your_file.csv"` |
| `ID_COLUMN` | CSV column with IDs | `"Pure ID"` |
| `OUTPUT_DIRECTORY` | Where to save files | `"downloads"` |
| `MAX_DOWNLOADS` | Limit for testing | `None` (all entries, or set to number for testing) |
| `DOWNLOAD_FILE_TYPES` | Filter file types | `['.pdf', '.docx', '.doc']` |
| `REQUEST_TIMEOUT` | API timeout seconds | `300` |
| `DOWNLOAD_CHUNK_SIZE` | Streaming chunk size | `8192` |

## 📊 CSV Format

Your CSV file should have a column named `"Pure ID"` containing Pure IDs:

```csv
Pure ID,Title,Year
27139086,"Forest Protection Research",2023
46773789,"Cypress Stakes Study",2022
14344978,"Genetic Resources",2021
```

**Supported ID formats:**
- Numeric Pure IDs: `27139086`, `46773789`
- UUIDs: `12345678-1234-5678-1234-567812345678`

## 🔧 Advanced Usage

### Test with Limited Downloads

For testing, set `MAX_DOWNLOADS` to a small number:

```python
# In config.py
MAX_DOWNLOADS = 3  # Download only first 3 entries
```

### Download All Entries

```python
# In config.py
MAX_DOWNLOADS = None  # Download everything
```

### Filter File Types

To only download specific file types:

```python
# In config.py
DOWNLOAD_FILE_TYPES = [".pdf", ".docx"]  # Only PDFs and Word docs
```

### Search Single ID

Use the standalone search utility:

```bash
python search_by_id.py 27139086
```

## 🔍 How It Works

1. **ID Resolution**: The script accepts numeric Pure IDs or UUIDs
   - Numeric IDs are automatically converted to UUIDs via API
   
2. **File Discovery**: Files are extracted from the `electronicVersions` field
   - Not from `/files` endpoint (Pure API quirk)
   
3. **Download**: Files are streamed in chunks to handle large files efficiently

4. **Naming**: Files are saved with sanitized titles and original extensions

## 🛡️ Security

- **API Key Protection**: `config.py` is automatically gitignored
- **Template Provided**: `config.template.py` shows structure without sensitive data
- **Never commit** your actual `config.py` to version control

## 🐛 Troubleshooting

### Configuration Issues

```bash
# Validate current configuration
python -c "import config; print(config.validate_config())"

# Reconfigure interactively
python setup_config.py
```

### API Connection Failed

1. Check `PURE_API_KEY` is correct in `config.py`
2. Verify `BASE_API_URL` format: `https://[institution].elsevierpure.com/ws/api`
3. Test network connectivity
4. Contact Pure administrator for API access

### CSV Encoding Errors

The script auto-detects encoding (UTF-8, cp1252, Latin-1, ISO-8859-1). If issues persist:
- Try re-exporting CSV from Pure with UTF-8 encoding
- Check for special characters in titles

### No Files Found (404 Errors)

- Verify the Pure ID exists and has attached files
- Check you have permission to access the research output
- Use `search_by_id.py` to inspect the full API response

## 📝 API Reference

### Pure API Endpoints Used

- `GET /research-outputs/{id}` - Get research output by numeric ID
- `GET /research-outputs/{uuid}` - Get research output by UUID
- `GET /research-outputs/{uuid}/files/{fileId}/{filename}` - Download file

### Authentication

The API uses API key authentication via the `api_key` query parameter.

## 🧪 Testing

Test files are located in `tests/`:

```bash
cd tests
python run_tests.py
```

## 📄 License

[Add your license here]

## 👥 Credits

Developed for Scion's Forest Genetic Resources AI Tool project.

## 🔗 Resources

- [Pure API Documentation](https://support.elsevier.com/app/answers/detail/a_id/28518/supporthub/pure/)
- [Pure API Cheat Sheet](pure_api_cheatsheet.md)

---

**Version**: 2.0  
**Last Updated**: 2024  
**Status**: ✅ Production Ready
