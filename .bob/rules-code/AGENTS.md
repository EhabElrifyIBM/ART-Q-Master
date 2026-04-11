# Code Mode Rules (Non-Obvious Only)

## QApplication Lazy Import Pattern
- Import `QApplication` inside functions, never at module level (except main.py)
- UI components (ProgressMonitor, LoadingSpinner, dialogs) must use lazy imports
- Pattern: Import inside function after `QApplication.instance()` check
- See `docs/LAZY_IMPORT_FIX_QAPPLICATION.md` for implementation details

## PyQt Version Isolation
- Functions.py uses PyQt6 (lines 30-36) - isolated from rest of codebase
- All other modules use PyQt5 - never mix in same file
- When editing Functions.py: use PyQt6 imports only
- When editing any other file: use PyQt5 imports only

## Config Validation (Strict)
- Config loader in `config_loader.py` validates ALL fields on startup
- Missing/empty fields cause immediate abort - no fallbacks allowed
- Use `CONFIG_MANAGER.get_value(section, key)` from SharedFunctions.py
- Never hardcode config values - always read from CONFIG_MANAGER

## Excel Column Mapping
- Use `canonical_fields` dict in `processor.py` (lines 47-74) for ALL column lookups
- Never hardcode CRM column names - they vary between exports
- Example: `'Contact Name (Contact) (Contact)'` maps to `'Customer Name'`
- 40+ variations handled - always use the mapping

## Module Loading with Spaces
- `src/ART Q Control/` has space in directory name
- Use `os.path.join()` for all paths to this directory
- See `main.py` lines 96-98 for path handling pattern
- Use `runpy.run_path()` for robust module execution

## Cache File Naming Convention
- Format: `working_cases_{agent}_{mode}_{MMDD}.xlsx`
- Must be in cache_directory from config
- AutoSender/CaseReviewer check for existing cache on startup
- Cache tracks: completed cases, skipped cases, current row position

## Selenium Element Locators
- Centralized in `LOCATORS` dict in SharedFunctions.py (lines 130+)
- Always use LOCATORS dict, never inline XPath strings
- Screenshots saved on element-find failure for debugging
- Chrome driver auto-managed by WebDriverManager

## Template Placeholders
- SMS/Email templates in SharedFunctions.py use specific placeholders
- Required: `{CX_Name}`, `{case_number}`, `{serial_val}`, `{AGENT_NAME}`
- Two email templates: CaseEmailOnSite_Depot vs CaseEmailCRU
- Use `get_case_note(action)` for dynamic case notes with date

## Windows Sleep Inhibit
- Use ctypes constants in SharedFunctions.py (lines 76-80)
- Required during automation to prevent screen lock
- Pattern: Set ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
- Must restore original state when done

## PyInstaller Meta Imports
- `_pyinstaller_meta_imports()` in main.py (lines 9-54) ensures bundling
- Function never called - exists only for static analysis
- Add new dependencies here for frozen executable support
- Use `sys._MEIPASS` for bundled resource paths