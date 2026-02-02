# Project Structure

```
aleapp/
├── aleapp.py              # CLI entry point
├── aleappGUI.py           # GUI entry point (tkinter)
├── plugin_loader.py       # Dynamic artifact plugin loader
├── requirements.txt       # Python dependencies
├── *.spec                 # PyInstaller build specs
│
├── scripts/
│   ├── artifacts/         # Artifact parser plugins (200+ modules)
│   │   ├── chrome.py      # Example: Chrome browser artifacts
│   │   ├── contacts.py    # Example: Contacts database
│   │   └── ...
│   │
│   ├── ilapfuncs.py       # Core utility functions (logging, TSV, timeline, KML)
│   ├── artifact_report.py # HTML report generation class
│   ├── report.py          # Main report orchestration
│   ├── search_files.py    # File seekers (FileSeekerDir, FileSeekerZip, etc.)
│   ├── html_parts.py      # HTML template fragments
│   ├── version_info.py    # Version constants
│   │
│   ├── MDB-Free_4.13.0/   # Bootstrap/MDB CSS/JS for reports
│   ├── timeline/          # Timeline visualization assets
│   └── *.js, *.css        # Report frontend assets
│
└── assets/                # Application icons and logos
```

## Artifact Plugin Structure

Each plugin in `scripts/artifacts/` must define:

```python
__artifacts_v2__ = {
    "artifact_id": {
        "name": "Display Name",
        "description": "What it parses",
        "author": "@username",
        "version": "0.1",
        "date": "2024-01-01",
        "requirements": "none",
        "category": "Category Name",
        "notes": "",
        "paths": ('*/path/pattern/*.db',),  # Glob patterns
        "function": "function_name"
    }
}

def function_name(files_found, report_folder, seeker, wrap_text, time_offset):
    # Parse files, generate reports
    pass
```

## Output Structure

Reports are generated to: `<output>/ALEAPP_Reports_<timestamp>/`
- `<Category>/` - HTML reports per artifact category
- `_TSV Exports/` - Tab-separated data files
- `_Timeline/` - Timeline database (tl.db)
- `_KML Exports/` - Geolocation data
- `Script Logs/` - Processing logs
