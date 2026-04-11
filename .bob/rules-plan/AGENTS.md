# Plan Mode Architecture Rules (Non-Obvious Only)

## Critical Architectural Constraints

### QApplication Initialization Order
- QApplication MUST be created before ANY QWidget instantiation
- UI component imports at module level cause "QWidget: Must construct a QApplication before a QWidget" errors
- Solution: Lazy imports inside functions after QApplication.instance() check
- Affects: ProgressMonitor, LoadingSpinner, all dialog components
- See `docs/LAZY_IMPORT_FIX_QAPPLICATION.md` for pattern details

### PyQt Version Isolation
- Functions.py uses PyQt6 (intentional isolation from main codebase)
- All other modules use PyQt5
- Mixing versions in same module causes import conflicts
- No migration path planned - intentional dual-version architecture

### Config System Architecture
- Strict validation on EVERY startup - no fallback values
- Missing/invalid fields abort execution immediately
- Two config systems exist: config_loader.py (PyQt5, active) and config_manager.py (tkinter, legacy)
- First-time setup shows ConfigSetupDialog if config missing/invalid
- Config changes require restart - no hot reload

### Module Loading with Spaces
- `src/ART Q Control/` directory name contains space (not a typo)
- Requires special path handling: `os.path.join()` for all paths
- Uses `runpy.run_path()` for robust module execution
- Import path manipulation in main.py lines 96-98

## Data Flow Architecture

### Cache & Resume System
- Cache files: `working_cases_{agent}_{mode}_{MMDD}.xlsx` in cache_directory
- AutoSender/CaseReviewer detect unfinished sessions on startup
- Cache tracks: completed cases, skipped cases, current row position
- No automatic cleanup - manual cache management required

### Excel Column Mapping Strategy
- Fuzzy column name matching via `canonical_fields` dict (processor.py lines 47-74)
- Handles 40+ CRM export column name variations
- Example: `'Contact Name (Contact) (Contact)'` → `'Customer Name'`
- Hardcoded column names will break - always use canonical_fields

### Entry Point Hierarchy
- Main: `python src/main.py` → launches main menu
- Direct tools: `python src/main.py merger|archiver|qcontrol|reachrate`
- ART Q Control: Dispatcher_v2.py (preferred) → Dispatcher.py (fallback) → Main.py (legacy)
- Fallback chain ensures backward compatibility

## UI Architecture

### Theme System
- Observer pattern broadcasts theme/font changes to all open dialogs
- Three modes: Light, Dark, Auto (detects Windows dark mode via registry)
- IBM Carbon Design color palette (`#0f62fe` primary blue)
- Theme persisted to `theme_config.json`, font size to `config.json`
- Settings changes apply immediately to all dialogs without restart

### Settings Observer Pattern
- SettingsObserver broadcasts changes to registered dialogs
- Dialogs inherit from SettingsAwareDialog to auto-respond
- Font size range: 15-30px, applies live to all open windows
- Accessibility features integrated into observer system

## Automation Architecture

### Selenium & CRM Integration
- Hardcoded dialer URL: `https://104.232.254.43/ui/ad/v1/index.html`
- Element locators centralized in `LOCATORS` dict (SharedFunctions.py lines 130+)
- Screenshots saved on element-find failure for debugging
- Chrome driver auto-managed by WebDriverManager
- Windows sleep inhibit via ctypes during automation (prevents screen lock)

### Template System
- SMS/Email templates in SharedFunctions.py with dynamic placeholders
- Two email templates: OnSite/Depot vs CRU (Customer Replaceable Unit)
- Placeholders: `{CX_Name}`, `{case_number}`, `{serial_val}`, `{AGENT_NAME}`
- Case notes use `get_case_note(action)` with automatic date formatting

### Workflow Orchestration
- AutoSender can auto-trigger CompaniesProcess after completion
- CaseReviewer uses SIP dialer for call flow
- CompaniesProcess groups cases by company email for batch processing
- Each mode maintains independent cache file

## Deployment Architecture

### PyInstaller Bundling
- `_pyinstaller_meta_imports()` in main.py (lines 9-54) - never called, exists for static analysis
- Frozen executable detection: `getattr(sys, 'frozen', False)`
- Bundled resources accessed via `sys._MEIPASS`
- `multiprocessing.freeze_support()` required at entry point (line 153)

### Timezone Handling
- US/Canada state → timezone mapping in `src/utils/timezone_map.py`
- Uses `zoneinfo` (Python 3.9+) with `pytz` fallback
- Local time calculation for customer contact windows (8 AM - 6 PM local)
- Critical for compliance with contact time restrictions

## Testing Architecture
- No formal test suite present
- No pytest configuration
- Manual testing via direct module execution
- Integration testing through full workflow execution