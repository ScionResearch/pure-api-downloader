# Pure API Cheatsheet# Pure API Python Script Cheatsheet



A generic reference guide for working with the Elsevier Pure API, with focus on research outputs and file downloads.## 📚 Official Documentation

- [Pure API Home](https://adk.elsevierpure.com/ws/api/)

## 📚 Official Documentation- [API User Guide: Files](https://adk.elsevierpure.com/ws/api/documentation/user-guide/files.html)

- [Pure API Home](https://adk.elsevierpure.com/ws/api/)- [API User Guide: Authorization](https://adk.elsevierpure.com/ws/api/documentation/user-guide/authorization.html)

- [API User Guide: Files](https://adk.elsevierpure.com/ws/api/documentation/user-guide/files.html)- [Python API Requests Examples](https://helpcenter.pure.elsevier.com/en_US/pure-api/python-api-requests-fundamental-coding-examples)

- [API User Guide: Authorization](https://adk.elsevierpure.com/ws/api/documentation/user-guide/authorization.html)

- [Python API Requests Examples](https://helpcenter.pure.elsevier.com/en_US/pure-api/python-api-requests-fundamental-coding-examples)## 🛠️ API Endpoints Used

- [Pure API: Getting Started](https://helpcenter.pure.elsevier.com/en_US/data-sources-and-integrations/how-to-get-started-using-the-pure-api-documentation)

- [Pure API: Working with Files](https://helpcenter.pure.elsevier.com/en_US/pure-api/pure-api-working-with-files)### Research Outputs

- **Get research output by numeric ID (auto-converts to UUID):**

## 🔑 Authentication  - `GET /ws/api/research-outputs/{numeric_id}`

  - Example: `/ws/api/research-outputs/27139086`

Pure API uses API key authentication via query parameter:  - Returns full object including UUID and `electronicVersions` with file info



```python- **Get research output by UUID:**

import requests  - `GET /ws/api/research-outputs/{uuid}`

  - Example: `/ws/api/research-outputs/12345678-1234-5678-1234-567812345678`

API_KEY = "your-api-key-here"

BASE_URL = "https://yourinstitution.elsevierpure.com/ws/api"- **Download a file:**

  - `GET /ws/api/research-outputs/{uuid}/files/{file_id}/{filename}`

response = requests.get(  - Example: `/ws/api/research-outputs/{uuid}/files/98765432/document.pdf`

    f"{BASE_URL}/research-outputs",  - Note: Use `fileId` from `electronicVersions[].file` field, NOT a separate file UUID

    params={"apiKey": API_KEY}

)### ⚠️ IMPORTANT: Files Are NOT at `/files` Endpoint

```The Pure API does **NOT** provide a `/research-outputs/{id}/files` endpoint to list files.

Instead, files are embedded in the research output object itself:

**Get your API key from your Pure system administrator.**- Files are in the `electronicVersions` array

- Each version contains a `file` object with `fileId`, `fileName`, `mimeType`, `size`

## 🛠️ Key API Endpoints- Download URL pattern: `/research-outputs/{uuid}/files/{fileId}/{filename}`



### Research Outputs## ⚡ Script Usage



#### Get by Numeric ID### Quick Start (Batch Download from CSV)

```1. **Configure your settings:**

GET /ws/api/research-outputs/{id}   ```bash

```   python setup_config.py

- Accepts numeric Pure ID (e.g., `27139086`)   ```

- Returns full research output object including UUID   - Enter your API key

- **Important:** Response includes `electronicVersions` array with file information   - Enter your institution's Pure API URL

   - Set CSV file path

Example:   - Configure download limit (3 for testing, None for all)

```python

response = requests.get(2. **Run the batch downloader:**

    f"{BASE_URL}/research-outputs/27139086",   ```bash

    params={"apiKey": API_KEY}   python download_pure_file.py

)   ```

data = response.json()   - The script will process your CSV file

uuid = data.get("uuid")   - Downloads all attached files for each Pure ID

files = data.get("electronicVersions", [])   - Saves files to `downloads/` directory

```

### Manual Configuration (Alternative)

#### Get by UUID1. **Copy and edit config file:**

```   ```bash

GET /ws/api/research-outputs/{uuid}   copy config.template.py config.py

```   ```

- Accepts UUID format: `12345678-1234-5678-1234-567812345678`   Then edit `config.py`:

- Returns same structure as numeric ID query   ```python

   PURE_API_KEY = "12345678-d656-42c9-8d3f-a23ea309df03"

#### Search Research Outputs   BASE_API_URL = "https://scion.elsevierpure.com/ws/api"

```   CSV_FILE_PATH = "Pure research outputs - FGR check.csv"

GET /ws/api/research-outputs   ID_COLUMN = "Pure ID"

```   MAX_DOWNLOADS = 3  # Or None for all entries

Query parameters:   ```

- `q`: Search query string

- `size`: Number of results (default: 10, max varies by instance)### Search Single ID (Testing)

- `offset`: Pagination offset```bash

- `apiKey`: Your API keypython search_by_id.py 27139086

```

Example:This will show you the full API response including UUID and available files.

```python

response = requests.get(## 📁 CSV File Format

    f"{BASE_URL}/research-outputs",Your CSV must have a column named `"Pure ID"`:

    params={```csv

        "apiKey": API_KEY,Pure ID,Title,Publication Year

        "q": "forest genetics",27139086,"Forest Protection Research",2023

        "size": 2046773789,"Cypress Stakes Study",2022

    }```

)

```**Supported ID formats:**

- Numeric Pure IDs (e.g., `27139086`) - automatically converted to UUID

## 📁 Working with Files- UUIDs (e.g., `12345678-1234-5678-1234-567812345678`)



### ⚠️ Critical Finding: No `/files` List Endpoint## 🧩 Python Libraries Used

- [`requests`](https://docs.python-requests.org/en/latest/): For making HTTP requests

**Despite some documentation suggesting otherwise, there is NO `/research-outputs/{id}/files` endpoint to list files.**- [`csv`](https://docs.python.org/3/library/csv.html): For reading CSV files with Pure IDs

- [`os`](https://docs.python.org/3/library/os.html): For file path and directory handling

Files must be extracted from the research output object itself.- [`json`](https://docs.python.org/3/library/json.html): For parsing API responses

- [`datetime`](https://docs.python.org/3/library/datetime.html): For logging timestamps

### File Information Location

## 📝 Key Functions

Files are in the `electronicVersions` array:

### Batch Processing

```json- **`batch_download_from_csv(csv_path, output_dir, id_column, max_downloads)`**

{  - Processes entire CSV file

  "uuid": "12345678-1234-5678-1234-567812345678",  - Handles both numeric IDs and UUIDs

  "title": "Research Title",  - Downloads all files for each entry

  "electronicVersions": [  - Returns statistics (success/fail counts)

    {

      "file": {### ID Handling

        "fileId": 98765432,- **`identify_pure_id_type(pure_id)`**

        "fileName": "document.pdf",  - Accepts numeric ID or UUID

        "mimeType": "application/pdf",  - Converts numeric ID to UUID via API

        "size": 1234567  - Returns research output object with file information

      },

      "accessType": {### File Extraction

        "value": "open"- **`get_electronic_versions(research_output_data, uuid)`**

      }  - Extracts files from `electronicVersions` field

    }  - Returns list of file objects with `fileId`, `fileName`, `mimeType`, `size`, `url`

  ]  - Handles missing or empty electronicVersions gracefully

}

```### Downloading

- **`download_file_from_url(file_url, output_path)`**

### Downloading Files  - Streams large files in chunks (8KB default)

  - Shows progress with file size

```  - Handles network errors gracefully

GET /ws/api/research-outputs/{uuid}/files/{fileId}/{filename}

```## 💡 How the Script Works (Important Details)



**Parameters:**### 1. ID Resolution

- `{uuid}`: Research output UUID- The script accepts **both** numeric Pure IDs and UUIDs

- `{fileId}`: Numeric file ID from `electronicVersions[].file.fileId`- Numeric IDs (e.g., `27139086`) are sent to: `GET /research-outputs/{id}`

- `{filename}`: File name from `electronicVersions[].file.fileName`- The API returns the full object including the UUID

- UUIDs can also be used directly

**Important:** Use `fileId` (numeric), not a separate "file UUID"

### 2. File Discovery (Critical!)

Example:Files are **NOT** at a separate `/files` endpoint. Instead:

```python```json

# Step 1: Get research outputGET /research-outputs/27139086

research_output = requests.get({

    f"{BASE_URL}/research-outputs/27139086",  "uuid": "12345678-...",

    params={"apiKey": API_KEY}  "title": "Research Title",

).json()  "electronicVersions": [

    {

# Step 2: Extract file info from electronicVersions      "file": {

uuid = research_output["uuid"]        "fileId": 98765432,

for version in research_output.get("electronicVersions", []):        "fileName": "document.pdf",

    file_info = version.get("file", {})        "mimeType": "application/pdf",

    file_id = file_info.get("fileId")        "size": 1234567

    file_name = file_info.get("fileName")      }

        }

    # Step 3: Download the file  ]

    file_url = f"{BASE_URL}/research-outputs/{uuid}/files/{file_id}/{file_name}"}

    file_response = requests.get(```

        file_url, 

        params={"apiKey": API_KEY}, ### 3. File Download

        stream=TrueUsing the `fileId` from above:

    )```

    GET /research-outputs/{uuid}/files/{fileId}/{filename}

    # Step 4: Save to diskExample: /research-outputs/12345678-.../files/98765432/document.pdf

    with open(file_name, "wb") as f:```

        for chunk in file_response.iter_content(chunk_size=8192):

            f.write(chunk)### 4. Encoding Handling

```The script tries multiple encodings for CSV files:

1. UTF-8-sig (handles BOM)

## 🔍 Common Response Fields2. Windows cp1252 (common Windows encoding)

3. Latin-1

### Research Output Object4. ISO-8859-1



Key fields in research output response:This ensures compatibility with CSV files exported from Pure on different systems.

- `uuid`: Unique identifier (UUID format)

- `pureId`: Numeric Pure ID## ⚠️ Troubleshooting

- `title`: Title object with `value` field

- `type`: Research output type### Configuration Issues

- `publicationStatuses`: Publication status information- **"Configuration Warning" on startup:**

- `electronicVersions`: **Array of file versions (this is where files are!)**  - Run `python setup_config.py` to configure settings

- `managingOrganizationalUnit`: Managing organization  - Or edit `config.py` directly with your API key and URL

- `persons`: Contributors/authors

### API Connection Failed

### Electronic Version Object- Verify `PURE_API_KEY` in `config.py` is correct

- Check `BASE_API_URL` format: `https://[institution].elsevierpure.com/ws/api`

Fields in `electronicVersions[]`:- Test with single ID: `python search_by_id.py 27139086`

- `file`: **File information object**- Contact Pure administrator if API access is denied

  - `fileId`: Numeric ID for download URL

  - `fileName`: Original filename### CSV Encoding Errors

  - `mimeType`: MIME type (e.g., `application/pdf`)- The script auto-detects encoding (UTF-8, cp1252, Latin-1)

  - `size`: File size in bytes- If issues persist, re-export CSV from Pure with UTF-8 encoding

- `accessType`: Access type object with `value` field (e.g., "open", "embargoed")- Check for special characters in column names

- `licenseType`: License information

- `versionType`: Version type (e.g., "publishedVersion")### No Files Found (404 Errors)

- **Common cause:** Research output has no attached files in Pure

## 💡 Best Practices- Verify the entry has files in Pure web interface

- Use `search_by_id.py` to inspect the API response

### 1. ID Handling- Check `electronicVersions` field in the response

- Pure supports **both** numeric IDs and UUIDs- Ensure you have permission to access the research output

- Numeric IDs are automatically converted to UUIDs by the API

- Store UUIDs for consistency if needed### Files Missing from Download

- Check `DOWNLOAD_FILE_TYPES` in `config.py` (empty = all types)

### 2. File Downloads- Some files may be embargoed or restricted

- Always use streaming for large files: `stream=True`- Check Pure web interface to see if files are publicly accessible

- Process in chunks to avoid memory issues

- Check `accessType` before attempting download### CSV Column Not Found

- Default column name is `"Pure ID"`

### 3. Error Handling

```python- Update `ID_COLUMN` in `config.py` if your CSV uses different name

response = requests.get(url, params={"apiKey": API_KEY})- Run script - it will show available column names if not found

if response.status_code == 200:

    data = response.json()## 🔗 More Resources

elif response.status_code == 404:- [Pure API: Getting Started](https://helpcenter.pure.elsevier.com/en_US/data-sources-and-integrations/how-to-get-started-using-the-pure-api-documentation)

    print("Resource not found")- [Pure API: Working with Files](https://helpcenter.pure.elsevier.com/en_US/pure-api/pure-api-working-with-files)

elif response.status_code == 401:- [Pure API: Uploading Files](https://helpcenter.pure.elsevier.com/en_US/api-examples/pure-api-uploading-files)

    print("Authentication failed - check API key")

else:## 🎯 Key Takeaways from Testing

    print(f"Error: {response.status_code}")

```1. **No `/files` Endpoint:** Despite documentation suggesting otherwise, the Pure API doesn't provide a `/research-outputs/{id}/files` endpoint. Files must be extracted from the `electronicVersions` field.



### 4. Rate Limiting2. **Numeric ID Support:** You can use numeric Pure IDs directly. The API accepts them and returns the full object including UUID.

- Be respectful of API rate limits

- Implement delays between requests if processing many items3. **FileId vs File UUID:** The download URL uses `fileId` (a numeric ID from the file object), not a separate file UUID.

- Handle 429 (Too Many Requests) responses

4. **Column Name:** The script expects a CSV column named `"Pure ID"` containing Pure IDs or UUIDs.

## 🐛 Common Issues

5. **Streaming Downloads:** The script streams large files in chunks to avoid memory issues, making it suitable for large datasets.

### Files Not Found (404)

**Cause:** Research output has no attached files6. **Configuration Security:** API keys are now stored in `config.py` which is gitignored to prevent accidental commits of sensitive data.

- Check `electronicVersions` array is not empty

- Verify files exist in Pure web interface---

- Check file access permissions

**Script Version:** 2.0  

### Authentication Errors (401)**Last Updated:** October 2024  

**Cause:** Invalid or missing API key**Status:** ✅ Production Ready - Tested with 76-entry CSV

- Verify API key is correct

- Ensure `apiKey` parameter is included in request---

- Check API key hasn't expired

*This cheatsheet reflects real-world testing and quirks discovered while implementing the Pure API downloader. For official documentation, see links above.*

### Incorrect File URLs
**Cause:** Using wrong file identifier
- Use `fileId` from `file` object (numeric)
- NOT a separate "file UUID"
- Include correct `fileName` in URL path

## 📝 Python Code Template

```python
import requests

class PureAPI:
    def __init__(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
    
    def get_research_output(self, id_or_uuid):
        """Get research output by ID or UUID"""
        url = f"{self.base_url}/research-outputs/{id_or_uuid}"
        response = requests.get(url, params={"apiKey": self.api_key})
        response.raise_for_status()
        return response.json()
    
    def get_files(self, id_or_uuid):
        """Extract file information from research output"""
        data = self.get_research_output(id_or_uuid)
        files = []
        
        uuid = data.get("uuid")
        for version in data.get("electronicVersions", []):
            file_info = version.get("file", {})
            if file_info:
                files.append({
                    "uuid": uuid,
                    "fileId": file_info.get("fileId"),
                    "fileName": file_info.get("fileName"),
                    "mimeType": file_info.get("mimeType"),
                    "size": file_info.get("size"),
                    "url": self._build_file_url(uuid, file_info)
                })
        return files
    
    def _build_file_url(self, uuid, file_info):
        """Build download URL for file"""
        file_id = file_info.get("fileId")
        file_name = file_info.get("fileName")
        return f"{self.base_url}/research-outputs/{uuid}/files/{file_id}/{file_name}"
    
    def download_file(self, file_url, output_path):
        """Download file to local path"""
        response = requests.get(
            file_url, 
            params={"apiKey": self.api_key},
            stream=True
        )
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

# Usage Example
api = PureAPI(
    base_url="https://yourinstitution.elsevierpure.com/ws/api",
    api_key="your-api-key"
)

# Get files for a research output
files = api.get_files(27139086)
for file in files:
    print(f"Downloading: {file['fileName']} ({file['size']} bytes)")
    api.download_file(file['url'], file['fileName'])
```

## 🎯 Key Takeaways

1. **No `/files` Endpoint:** The Pure API does NOT provide a `/research-outputs/{id}/files` endpoint to list files. Files are embedded in the `electronicVersions` array of the research output object.

2. **Numeric ID Support:** You can use numeric Pure IDs directly. The API accepts them and returns the full object including the UUID.

3. **FileId vs File UUID:** The download URL uses `fileId` (a numeric ID from the file object), not a separate "file UUID".

4. **Streaming Required:** Always stream large files using `stream=True` to avoid memory issues.

5. **Error Handling:** Always check HTTP status codes and handle 404 (not found) and 401 (auth failed) responses appropriately.

---

**Last Updated:** October 2024  
**API Version:** Pure API v1

*This cheatsheet is based on real-world API testing. Always refer to official Pure documentation for the most authoritative information.*
