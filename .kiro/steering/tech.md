# Technology Stack

## Language
- Python 3.9+ (primary)

## Key Dependencies
- `sqlite3` - Database parsing (most artifacts are SQLite DBs)
- `protobuf` / `blackboxprotobuf` - Protocol buffer parsing
- `beautifulsoup4` - HTML parsing
- `pillow` - Image processing
- `simplekml` - KML file generation for geolocation data
- `folium` / `geopy` - Mapping and geocoding
- `pytz` - Timezone handling
- `xlsxwriter` - Excel export
- `PyCryptodome` - Cryptographic operations
- `tkinter` - GUI (aleappGUI.py)

## Build & Distribution
- PyInstaller for creating standalone executables
- Spec files: `aleapp.spec`, `aleappGUI.spec` (Windows), `*_macOS.spec` (macOS)

## Common Commands

### Install dependencies
```bash
pip install -r requirements.txt
# Linux also needs: sudo apt-get install python3-tk
```

### Run CLI
```bash
python aleapp.py -t <zip|tar|fs|gz> -i <input_path> -o <output_path>
python aleapp.py -tz "America/New_York" -t fs -i ./extraction -o ./reports
```

### Run GUI
```bash
python aleappGUI.py
```

### Build executables
```bash
pyinstaller --onefile aleapp.spec
pyinstaller --onefile --noconsole aleappGUI.spec
```

### Generate artifact path list
```bash
python aleapp.py -p
```

### Create profile/case data
```bash
python aleapp.py -c <output_folder>
```
