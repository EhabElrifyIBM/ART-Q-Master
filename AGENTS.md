# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Critical QApplication Pattern (PyQt5)
- **NEVER** import `QApplication` at module level except in `src/main.py`
- Use lazy imports: `from PyQt5.QtWidgets import QApplication` inside functions only
- Always check `QApplication.instance()` before creating dialogs/windows
- Pattern: `app = QApplication.instance() or QApplication(sys.argv)`
- Violating this causes "QWidget: Must construct a QApplication before a QWidget" errors
- See `docs/LAZY_IMPORT_FIX_QAPPLICATION.md` for details

## PyQt Version Conflict
- **Main codebase uses PyQt5** (ui/, ART Q Control/)
- **Functions.py uses PyQt6** (lines 30-36) - DO NOT mix imports
- When editing Functions.py, use PyQt6 imports only
- When editing other files, use PyQt5 imports only
- Mixing PyQt5/PyQt6 in same module causes import conflicts

## Config System (Non-Standard)
- `config.json` is validated on EVERY startup - missing fields abort execution
- Config loader in `src/ART Q Control/config_loader.py` (PyQt5)
- Legacy `config_manager.py` (tkinter) still exists but superseded
- First-time setup shows `ConfigSetupDialog` if config missing/invalid
- NO fallback values - all fields required

## Directory with Spaces
- Main automation module: `src/ART Q Control/` (note space in name)
- Import path handling in `src/main.py` lines 96-98
- Always use `os.path.join()` for paths to this directory

## Entry Points & Module Loading
- Main: `python src/main.py` (launches main menu)
- Direct tools: `python src/main.py merger|archiver|qcontrol|reachrate`
- ART Q Control uses `Dispatcher_v2.py` (preferred) → fallback to `Dispatcher.py` → `Main.py`
- Uses `runpy.run_path()` for robust module execution (lines 71-120)

## Cache & Resume System
- Cache files: `working_cases_{agent}_{mode}_{MMDD}.xlsx` in cache_directory
- AutoSender/CaseReviewer detect unfinished sessions and prompt RESUME/NEW
- Cache tracks: completed cases, skipped cases, current position
- Cache directory must exist (validated in config)

## Excel Column Mapping (FileProcessor)
- Uses fuzzy column name matching via `canonical_fields` dict (processor.py lines 47-74)
- Handles CRM export variations: `'Contact Name (Contact) (Contact)'` → `'Customer Name'`
- 40+ column mappings defined - DO NOT hardcode column names
- Always use `canonical_fields` for column lookups

## Selenium & CRM Automation
- Hardcoded dialer URL: `https://104.232.254.43/ui/ad/v1/index.html`
- Uses WebDriverManager for Chrome driver auto-download
- Screenshots on element-find failure (saved to working directory)
- Windows sleep inhibit during automation (ctypes, lines 76-80 in SharedFunctions.py)
- Chrome keep-alive via refresh interval (config: `refresh_interval`)

## Template System
- SMS/Email templates in `SharedFunctions.py` lines 85-120
- Dynamic placeholders: `{CX_Name}`, `{case_number}`, `{serial_val}`, `{AGENT_NAME}`
- Two email templates: OnSite/Depot vs CRU (Customer Replaceable Unit)
- Case notes use `get_case_note()` function with date formatting

## Theme System
- IBM Carbon Design color palette (`#0f62fe` primary blue)
- Three modes: Light, Dark, Auto (detects Windows dark mode)
- Theme persisted to `theme_config.json`
- Font size: 15-30px range, persisted to `config.json` → `ui_settings.font_size`
- Settings observer pattern broadcasts changes to all open dialogs

## PyInstaller Bundling
- `_pyinstaller_meta_imports()` in main.py (lines 9-54) - exhaustive imports for static analysis
- Frozen executable detection: `getattr(sys, 'frozen', False)`
- Uses `sys._MEIPASS` for bundled resource paths
- `multiprocessing.freeze_support()` required (line 153)

## Timezone Handling
- US/Canada state → timezone mapping in `src/utils/timezone_map.py`
- Uses `zoneinfo` (Python 3.9+) with `pytz` fallback
- Local time calculation for customer contact windows (8 AM - 6 PM local)

## Testing
- No formal test suite present
- No pytest configuration found
- Manual testing via direct module execution