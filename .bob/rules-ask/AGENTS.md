# Ask Mode Documentation Rules (Non-Obvious Only)

## Project Structure Quirks
- `src/ART Q Control/` has space in directory name - not a typo
- Multiple entry points exist: Dispatcher_v2.py (preferred) → Dispatcher.py → Main.py
- Legacy files (Main.py, config_manager.py) still present but superseded by v2 versions
- Functions.py uses PyQt6 while rest uses PyQt5 - intentional isolation

## Documentation Location
- Session-based development notes in `docs/` directory
- May contain stale information from previous development sessions
- `docs/LAZY_IMPORT_FIX_QAPPLICATION.md` documents critical QApplication pattern
- README.md is authoritative for current project state

## Module Organization
- `SharedFunctions.py` contains shared CRM automation utilities, not just functions
- Config system split: config_loader.py (PyQt5, active) vs config_manager.py (tkinter, legacy)
- FileProcessor in `processor.py` is 4184 lines - handles entire Excel pipeline
- Theme system uses observer pattern for live updates across dialogs

## Non-Standard Patterns
- Config has NO fallback values - all fields required or abort
- Cache files use specific naming: `working_cases_{agent}_{mode}_{MMDD}.xlsx`
- Excel columns use fuzzy matching via `canonical_fields` dict - handles 40+ CRM export variations
- Dialer URL hardcoded: `https://104.232.254.43/ui/ad/v1/index.html`

## Architecture Flow
- Main menu → Tool selection → Module execution via `runpy.run_path()`
- ART Q Control: Dispatcher shows mode selector → AutoSender/CaseReviewer/CompaniesProcess
- AutoSender can auto-trigger CompaniesProcess after completion
- Cache resume system detects unfinished sessions on startup

## UI System
- IBM Carbon Design color palette (`#0f62fe` primary blue)
- Three theme modes: Light, Dark, Auto (detects Windows dark mode)
- Font size range: 15-30px, persisted to config
- Settings observer broadcasts changes to all open dialogs in real-time

## Selenium Automation
- Element locators centralized in `LOCATORS` dict in SharedFunctions.py
- Screenshots saved automatically on element-find failure
- Windows sleep inhibit via ctypes during automation
- Chrome driver auto-managed by WebDriverManager

## Template System
- SMS/Email templates with dynamic placeholders in SharedFunctions.py
- Two email templates: OnSite/Depot vs CRU (Customer Replaceable Unit)
- Case notes use `get_case_note(action)` with automatic date formatting
- Placeholders: `{CX_Name}`, `{case_number}`, `{serial_val}`, `{AGENT_NAME}`

## PyInstaller Bundling
- `_pyinstaller_meta_imports()` in main.py never called - exists for static analysis only
- Frozen executable detection: `getattr(sys, 'frozen', False)`
- Bundled resources accessed via `sys._MEIPASS`
- `multiprocessing.freeze_support()` required at entry point