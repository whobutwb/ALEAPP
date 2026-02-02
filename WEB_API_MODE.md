# ALEAPP Web API Mode

ALEAPP supports a Web API mode that allows it to query and retrieve evidence files from a remote REST API server. This enables integration with cloud-based or web-enabled DFIR platforms without requiring direct filesystem access to the evidence.

## Overview

Instead of reading from a local directory, tar, or zip file, ALEAPP can connect to a REST API that provides:
1. File search/discovery based on glob patterns
2. File download for matched files

This is useful for:
- Cloud-hosted evidence storage
- Multi-user DFIR platforms
- Distributed processing environments
- Integration with existing case management systems

## Architecture

```
┌─────────────┐         HTTP/HTTPS          ┌──────────────────┐
│   ALEAPP    │ ◄─────────────────────────► │  Web API Server  │
│  (Client)   │   Search & Download Files   │  (Your Platform) │
└─────────────┘                             └────────┬─────────┘
                                                     │
                                                     ▼
                                            ┌──────────────────┐
                                            │ Evidence Storage │
                                            │  (Filesystem/S3) │
                                            └──────────────────┘
```

## API Specification

The Web API server must implement the following endpoints:

### GET /files/search

Search for files matching a glob pattern.

**Query Parameters:**
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| pattern   | string | Yes      | Glob pattern (e.g., `*/databases/*.db`) |

**Response:**
```json
{
  "files": [
    {
      "path": "data/com.android.providers.contacts/databases/contacts2.db",
      "size": 524288,
      "mtime": 1706745600.0,
      "ctime": 1706745600.0
    }
  ],
  "count": 1
}
```

**Response Fields:**
| Field | Type   | Required | Description |
|-------|--------|----------|-------------|
| files | array  | Yes      | List of matching file objects |
| files[].path | string | Yes | Relative path within evidence |
| files[].size | int | No | File size in bytes |
| files[].mtime | float | No | Modification timestamp (Unix epoch) |
| files[].ctime | float | No | Creation timestamp (Unix epoch) |

### GET /files/download

Download a specific file.

**Query Parameters:**
| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| path      | string | Yes      | Relative file path from search results |

**Response:**
- Binary file content
- Content-Type: application/octet-stream

**Response Headers:**
| Header | Description |
|--------|-------------|
| X-File-Mtime | Modification timestamp (Unix epoch) |
| X-File-Ctime | Creation timestamp (Unix epoch) |

### GET /health (Optional)

Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "evidence_root": "/path/to/evidence",
  "auth_enabled": true
}
```

## Authentication

The API supports Bearer token authentication via the `Authorization` header:

```
Authorization: Bearer <your-api-key>
```

Authentication is optional but recommended for production deployments.

## Usage

### Running ALEAPP with Web API

```python
from scripts.search_files import FileSeekerWeb

# Initialize the web seeker
seeker = FileSeekerWeb(
    base_url="https://your-dfir-platform.com/api/v1",
    data_folder="/tmp/aleapp_output/data",
    headers={"Authorization": "Bearer your-api-key"},
    timeout=60
)

# Search for files (same interface as other seekers)
contacts_dbs = seeker.search("*/databases/contacts*.db")
```

### Running the Example Server

A reference Flask implementation is provided in `examples/web_api_server.py`:

```bash
# Install Flask
pip install flask

# Run with default settings
python examples/web_api_server.py --evidence-root /path/to/extracted/evidence

# Run with authentication
python examples/web_api_server.py \
    --evidence-root /path/to/evidence \
    --api-key your-secret-key \
    --port 8080
```

### Server Options

| Option | Default | Description |
|--------|---------|-------------|
| --evidence-root, -e | ./evidence | Root directory containing extracted evidence |
| --api-key, -k | None | API key for authentication |
| --host | 0.0.0.0 | Host to bind to |
| --port, -p | 5000 | Port to listen on |
| --debug | False | Enable Flask debug mode |

## Implementation Notes

### FileSeekerWeb Behavior

- **Caching**: Search results and downloaded files are cached to avoid redundant API calls
- **Retry Logic**: Automatic retry with exponential backoff for transient failures (429, 5xx)
- **Timeout**: Configurable request timeout (default 30 seconds)
- **File Storage**: Downloaded files are stored in the `data_folder` with preserved directory structure

### Security Considerations

1. **Use HTTPS** in production to encrypt file transfers
2. **Enable authentication** to prevent unauthorized access
3. **Implement path traversal protection** in your server (see example)
4. **Consider rate limiting** for large evidence sets
5. **Audit logging** of file access for chain of custody

### Performance Tips

1. **Index caching**: Pre-build and cache the file index on the server
2. **Streaming downloads**: Use chunked transfer for large files
3. **Connection pooling**: FileSeekerWeb uses a session with connection reuse
4. **Selective patterns**: Use specific glob patterns to minimize search results

## Extending the API

The example server can be extended to support:

- **Multiple evidence sources**: Route to different storage backends
- **Access control**: Per-user or per-case permissions
- **Audit logging**: Track file access for forensic documentation
- **Cloud storage**: Integrate with S3, Azure Blob, or GCS
- **Compression**: Compress responses for bandwidth optimization

## Troubleshooting

### Connection Issues

```
Warning: Could not verify API connection
```
- Verify the base URL is correct
- Check network connectivity
- Ensure the server is running

### Authentication Errors

```
Warning: API returned 401 Unauthorized
```
- Verify the API key is correct
- Check the Authorization header format

### Missing Files

If expected files aren't found:
- Verify the evidence root path on the server
- Check glob pattern syntax
- Call `/files/refresh` if evidence was recently added
