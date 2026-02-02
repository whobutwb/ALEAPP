"""
Example REST API server for ALEAPP FileSeekerWeb integration.

This Flask server provides the endpoints required by FileSeekerWeb to enable
ALEAPP to query and retrieve files from a remote DFIR platform.

Requirements:
    pip install flask

Usage:
    python web_api_server.py --evidence-root /path/to/extracted/evidence
    
    # With authentication
    python web_api_server.py --evidence-root /path/to/evidence --api-key your-secret-key
"""

import os
import argparse
import fnmatch
from pathlib import Path
from functools import wraps

from flask import Flask, request, jsonify, send_file, abort

app = Flask(__name__)

# Configuration (set via command line or environment)
EVIDENCE_ROOT = os.environ.get('EVIDENCE_ROOT', './evidence')
API_KEY = os.environ.get('API_KEY', None)


def require_api_key(f):
    """Decorator to enforce API key authentication when configured."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if API_KEY:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                abort(401, description='Missing or invalid Authorization header')
            token = auth_header[7:]  # Strip 'Bearer '
            if token != API_KEY:
                abort(401, description='Invalid API key')
        return f(*args, **kwargs)
    return decorated


def build_file_index(root_path):
    """Build an index of all files under the evidence root."""
    files = []
    root = Path(root_path)
    if not root.exists():
        return files
    
    for path in root.rglob('*'):
        if path.is_file():
            try:
                stat = path.stat()
                rel_path = str(path.relative_to(root))
                files.append({
                    'path': rel_path,
                    'size': stat.st_size,
                    'mtime': stat.st_mtime,
                    'ctime': stat.st_ctime,
                })
            except (OSError, ValueError):
                continue
    return files


# Cache the file index (rebuild on demand in production)
_file_index = None


def get_file_index():
    """Get or build the file index."""
    global _file_index
    if _file_index is None:
        _file_index = build_file_index(EVIDENCE_ROOT)
    return _file_index


def refresh_index():
    """Force rebuild of file index."""
    global _file_index
    _file_index = build_file_index(EVIDENCE_ROOT)
    return _file_index


@app.route('/files/search', methods=['GET'])
@require_api_key
def search_files():
    """
    Search for files matching a glob pattern.
    
    Query Parameters:
        pattern (str): Glob pattern to match (e.g., '*/databases/*.db')
    
    Returns:
        JSON: {"files": [{"path": "...", "size": 123, "mtime": 1234567890, "ctime": 1234567890}, ...]}
    """
    pattern = request.args.get('pattern', '')
    
    if not pattern:
        return jsonify({'files': [], 'error': 'No pattern provided'})
    
    # Normalize pattern - strip leading */ or root/ that ALEAPP adds
    search_pattern = pattern.lstrip('*').lstrip('/')
    if search_pattern.startswith('root/'):
        search_pattern = search_pattern[5:]
    
    file_index = get_file_index()
    matches = []
    
    for file_info in file_index:
        file_path = file_info['path']
        # Match against the pattern
        if fnmatch.fnmatch(file_path, search_pattern) or fnmatch.fnmatch(file_path, pattern):
            matches.append(file_info)
    
    return jsonify({'files': matches, 'pattern': pattern, 'count': len(matches)})


@app.route('/files/download', methods=['GET'])
@require_api_key
def download_file():
    """
    Download a specific file.
    
    Query Parameters:
        path (str): Relative path to the file within evidence root
    
    Returns:
        Binary file content with headers:
            X-File-Mtime: Modification timestamp
            X-File-Ctime: Creation timestamp
    """
    file_path = request.args.get('path', '')
    
    if not file_path:
        abort(400, description='No file path provided')
    
    # Security: prevent path traversal
    safe_path = Path(EVIDENCE_ROOT) / file_path
    try:
        safe_path = safe_path.resolve()
        evidence_root = Path(EVIDENCE_ROOT).resolve()
        if not str(safe_path).startswith(str(evidence_root)):
            abort(403, description='Access denied')
    except (ValueError, RuntimeError):
        abort(400, description='Invalid path')
    
    if not safe_path.exists():
        abort(404, description='File not found')
    
    if not safe_path.is_file():
        abort(400, description='Path is not a file')
    
    # Get file timestamps
    stat = safe_path.stat()
    
    response = send_file(safe_path, as_attachment=True)
    response.headers['X-File-Mtime'] = str(stat.st_mtime)
    response.headers['X-File-Ctime'] = str(stat.st_ctime)
    
    return response


@app.route('/files/refresh', methods=['POST'])
@require_api_key
def refresh_files():
    """
    Refresh the file index (call after evidence changes).
    
    Returns:
        JSON: {"status": "ok", "file_count": 123}
    """
    index = refresh_index()
    return jsonify({'status': 'ok', 'file_count': len(index)})


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (no auth required)."""
    return jsonify({
        'status': 'healthy',
        'evidence_root': EVIDENCE_ROOT,
        'auth_enabled': API_KEY is not None
    })


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ALEAPP Web API Server')
    parser.add_argument('--evidence-root', '-e', default='./evidence',
                        help='Root directory containing extracted evidence')
    parser.add_argument('--api-key', '-k', default=None,
                        help='API key for authentication (optional)')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host to bind to')
    parser.add_argument('--port', '-p', type=int, default=5000,
                        help='Port to listen on')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    
    args = parser.parse_args()
    
    EVIDENCE_ROOT = args.evidence_root
    API_KEY = args.api_key
    
    print(f"Starting ALEAPP Web API Server")
    print(f"  Evidence root: {EVIDENCE_ROOT}")
    print(f"  Authentication: {'enabled' if API_KEY else 'disabled'}")
    print(f"  Listening on: http://{args.host}:{args.port}")
    
    # Build initial index
    refresh_index()
    print(f"  Indexed {len(_file_index)} files")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
