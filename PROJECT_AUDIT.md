# ART Q Master — Full Project Audit

> Generated: 2026-06-30  
> Scope: `src_v2/` only (docs folder excluded per instructions)  
> Intent: Identify all flaws, dead code, broken wiring, config inconsistencies, UI problems, and improvement opportunities. No code was changed.

## User Decisions (2026-06-30)

| # | Finding | Decision |
|---|---------|----------|
| 1 | Hardcoded password in config.json | **Ignore for now** |
| 2 | Broken wiring & useless code | **Fix wiring; remove unused/useless** |
| 3 | Dead code | **Remove — carefully, no regressions** |
| 4 | Config chaos | **One file, two sections (`src_v2/config.json`). `config/manager.py` becomes the single reader.** |
| 5 | Duplicates in src_v2/ | See detailed decisions below |
| 6 | Error handling gaps | **Improve throughout** |
| 7 | UI problems | **Fix without breaking any flow** |
| 8 | Data flow & logic bugs | **Fix** |
| 9 | Code quality | **Improve** |
| 10 | src/ vs src_v2/ | **Drop ARCHIVED.md inside src/; src_v2/ is production** |

### Detailed Duplicate Decisions

| File / Pair | Decision |
|-------------|----------|
| `settings_dialog.py` vs `settings_dialog_v2.py` | Keep `settings_dialog.py`, delete `_v2.py`. Fully overhaul the surviving one: fix theme/font propagation to all sub-tools, clean up the UI. |
| `utils/runtime.py` vs `ART Q Control/runtime.py` | Keep `utils/runtime.py`, delete the ART Q Control copy. ART Q Control imports the shared one. |
| `ui/theme.py` + `ui/theme_manager.py` + `ui/design_system.py` | Consolidate into `design_system.py` as sole colour/token source. Remove `theme.py` and `theme_manager.py` after migrating any unique content. |
| `AutoSender.py` / `CaseReviewer.py` / `CompaniesProcess.py` (originals) | Delete — `_v2` versions are active. |
| `Main_BackUp_eticket_VoiceMail_II.py` | Rename to `_reference_voicemail_eticket.py` (prefix marks it as reference-only, not executable). |
| `Merger/Merger.py` (tkinter) | Delete — `merger_window.py` (PyQt5) is the active version and dev-mode launcher will be updated to match. |
| `ui/main_window.py` | Delete — nothing imports it. It is fully orphaned. |
| `src/` old version | Add `ARCHIVED.md` inside `src/`. No files moved or deleted. |

### Settings & Theme Propagation Fix (Key Architecture Change)

The root cause of settings not reaching sub-tools: several windows call `V2SettingsBus()` directly (creates a new instance) instead of using the `get_v2_settings_bus()` singleton. Theme and font signals emitted from the shell never reach tools opened in separate windows.

**Fix:** All modules must use `get_v2_settings_bus()`. `V2SettingsBus()` direct construction outside of `services.py` is forbidden. Settings dialog emits through the singleton so every connected tool updates live.

### Logger Strategy

Both terminal (print-style) and UI logging improved together:
- Replace all `print("[INFO]…")` / `print("[WARNING]…")` calls with `utils/error_logger.py`
- Improve `error_logger.py`: structured output, shorter messages, colour-coded terminal output, severity levels
- Add a `LogPanel` widget (or improve the existing log text area in tools that have one) so errors are visible inside the UI without needing a terminal
- `ART Q Control/logger.py` kept for ART-specific log context but wired to the same underlying logger

---

## Table of Contents

1. [Critical Security Issues](#1-critical-security-issues)
2. [Broken Wiring — Features That Crash or Do Nothing](#2-broken-wiring--features-that-crash-or-do-nothing)
3. [Dead Code — Methods Never Called](#3-dead-code--methods-never-called)
4. [Config System — No Single Source of Truth](#4-config-system--no-single-source-of-truth)
5. [Duplicate Implementations](#5-duplicate-implementations)
6. [Error Handling Gaps](#6-error-handling-gaps)
7. [UI Problems](#7-ui-problems)
8. [Data Flow & Logic Bugs](#8-data-flow--logic-bugs)
9. [Code Quality Issues](#9-code-quality-issues)
10. [Architecture Problems](#10-architecture-problems)
11. [Priority Fix List](#11-priority-fix-list)

---

## 1. Critical Security Issues

### 1.1 Password stored in plain-text in config.json

**File:** `src_v2/ART Q Control/config.json` and `src_v2/config.json`

The dialer password is written to a plain-text JSON file that sits in the project directory and is tracked by git:

```json
"agent_settings": {
    "agent_name": "Ehab Elrify",
    "user_id": "Agent_Cairo_US_925",
    "password": "123456",
    "place_id": "Place_57080_SIPSwitch_US"
}
```

Anyone with read access to the file or the git repo sees the password. The `config_loader.py` `_validate_config()` method treats `password` as a required field and blocks startup if it is empty — forcing the password to always be present in the file.

**Fix:** Read the password from an environment variable (`ARTQ_PASSWORD`) or use OS-level credential storage (keyring). Remove the password field from config.json and never commit it.

---

## 2. Broken Wiring — Features That Crash or Do Nothing

### 2.1 `open_main_menu()` tries to import a class that does not exist

**File:** `src_v2/ui/main_window.py`

```python
def open_main_menu(self):
    from .main_menu import MainMenu   # ← ImportError at runtime
    self.menu_window = MainMenu()
    self.menu_window.show()
    self.close()
```

`src_v2/ui/main_menu.py` exports `V2MainMenu`, not `MainMenu`. Every click of the "Main Menu" button silently catches this `ImportError` and logs it, so the user never actually gets back to the main menu. The window just stays open.

**Fix:** Change the import to `from .main_menu import V2MainMenu` and instantiate `V2MainMenu`.

---

### 2.2 `process_files()` is wired to the UI but does nothing

**File:** `src_v2/ui/main_window.py`

```python
def process_files(self):
    # TODO: Implement file processing logic
    pass
```

This is connected to a button. Clicking it produces zero feedback — no log line, no dialog, nothing. The user has no way to know whether the button failed or the feature is missing.

**Fix:** Either implement it or disable/hide the button until it is implemented.

---

### 2.3 `output_path_changed()` is wired to a signal but does nothing

**File:** `src_v2/ui/main_window.py`

```python
def output_path_changed(self):
    # This method gets called when the output file path changes
    pass
```

Connected to the output path field's `textChanged` signal. No logic runs when the path changes, meaning any downstream validation or UI update that should happen on path change never fires.

---

### 2.4 Dev-mode subprocess launcher points to the old tkinter Merger

**File:** `src_v2/utils/tool_launcher.py` line 159

```python
"merger": os.path.join(paths.src_v2_root, "Merger", "Merger.py"),
```

`Merger.py` is the old tkinter implementation. `merger_window.py` is the current PyQt5 version. When you click "Merger" in dev mode (running `.py` files, not the `.exe`), you get the obsolete tkinter UI. The frozen/exe path correctly uses `MergerWindow` from `merger_window.py`.

**Fix:** Change the dev subprocess path to point to a `run_merger.py` entry point (parallel to how `run_archiver.py`, `run_daily_merger.py` etc. work).

---

### 2.5 `handlers_cache.json` saved to current working directory

**File:** `src_v2/ui/main_window.py`

```python
with open('handlers_cache.json', 'w') as f:
    json.dump(handlers_data, f)
```

Uses a bare relative path. The file will be written wherever Python was launched from. When the app is run from different directories (terminal, IDE, shortcut), the file lands in different places and cannot be found on the next load. The actual `handlers_cache.json` exists in `src_v2/` but code doesn't guarantee writing to that location.

**Fix:** Use an absolute path derived from `__file__` or from `get_runtime_paths()`.

---

### 2.6 "View Profile" is a stub that shows a toast

**File:** `src_v2/ui/shell.py` lines 526–533

```python
def _view_profile(self):
    from ui.components_v2 import Toast
    Toast.show_info(self, f"Profile: {self._load_agent_name()}", "Profile management coming soon")
```

The profile button in the header shows a "Profile management coming soon" toast. This is in the main navigation and gives the impression the app is unfinished.

**Fix:** Either implement a real profile view or remove the button entirely.

---

### 2.7 "Sign Out" just closes the window

**File:** `src_v2/ui/shell.py` lines 535–544

```python
def _sign_out(self):
    reply = QMessageBox.question(self, "Sign Out", "Are you sure you want to sign out?", ...)
    if reply == QMessageBox.Yes:
        self.close()
```

There is no actual authentication in the app. "Sign Out" closing the window is misleading UX — it implies a session concept that does not exist. Users may expect their credentials to be cleared.

**Fix:** Rename to "Exit" or remove the "Sign Out" option from the profile menu.

---

### 2.8 `_is_valid_time()` defined but never called

**File:** `src_v2/ART Q Control/config_loader.py` lines 100–112

```python
@staticmethod
def _is_valid_time(time_str):
    """Check if time string is in HH:MM format"""
    ...
```

This utility is defined inside `ConfigManager` but is never called anywhere in the codebase. The config schema does not include time fields, so it cannot be used by `_validate_config()` either.

**Fix:** Remove it, or add time-format fields to the schema and wire this validator in.

---

## 3. Dead Code — Methods Never Called

### 3.1 `create_top_bar()` — defined, never called

**File:** `src_v2/ui/main_window.py` (~lines 590–605)

Creates a top bar widget with a "Progress View" button. This method is never called by `create_main_window()` or any other method. The top bar does not appear in the running UI. The button inside it calls `show_progress()` which also does nothing (see §3.3).

---

### 3.2 `create_right_panel()` — defined, never called

**File:** `src_v2/ui/main_window.py` (~lines 606–705)

~100 lines of widget creation for a right panel. The actual right panel is built inline inside `create_main_window()` (lines 401–464). This duplicate method is never called and produces no UI.

---

### 3.3 `create_file_section()` — defined, never called

**File:** `src_v2/ui/main_window.py` (~lines 707–778)

~70 lines of widget creation. Never called anywhere.

---

### 3.4 `_create_processing_view()` — defined, never called

**File:** `src_v2/ui/main_window.py` (~lines 780–882)

~100 lines of complex UI creation for a "processing view". Never called.

---

### 3.5 `show_progress()` — feature removed, method is a log stub

**File:** `src_v2/ui/main_window.py`

```python
def show_progress(self):
    # Progress view has been removed from this build.
    self.add_log("Progress View feature has been removed in this build.")
```

This method is wired to a button that is then hidden (`setEnabled(False)`, `setVisible(False)`). Both the button and the method are dead weight.

---

### 3.6 Progress bar created and immediately hidden

**File:** `src_v2/ui/main_window.py` lines 489–525

A `QProgressBar` is constructed, laid out, and then hidden via:

```python
if hasattr(self, 'progress_bar'):
    self.progress_bar.setVisible(False)
```

It takes up memory and the layout still reserves space for it depending on timing. If the feature is removed, the widget should not be created at all.

---

### 3.7 `_tools_grid` referenced in `resizeEvent` but never created

**File:** `src_v2/ui/shell.py` lines 596–610

```python
def resizeEvent(self, a0):
    self._update_responsive_typography()
    self._apply_current_style()
    
    if hasattr(self, '_tools_grid'):       # ← This attribute is never assigned
        if self.width() < 800:
            self._set_grid_columns(1)
        else:
            self._set_grid_columns(2)
```

`_tools_grid` is checked in `resizeEvent` and `_set_grid_columns()` but is never created anywhere in `UnifiedToolShell`. The responsive column switch never fires. The grid layout built in `_build_all_tools_section()` uses a local variable `grid_layout`, not `self._tools_grid`.

**Fix:** Either assign `self._tools_grid = grid_layout` in `_build_all_tools_section()`, or remove the dead resize logic entirely.

---

### 3.8 `get_accessibility_manager()` defined twice

**File:** `src_v2/ui/accessibility_helper.py`

The function `get_accessibility_manager()` is defined at line ~480 and again at line ~629. Python silently uses the second definition. The first definition is dead code. Since they differ slightly, the one being used may not be the intended one.

---

## 4. Config System — No Single Source of Truth

The project has **four** separate config files with incompatible schemas:

| File | Purpose | Issues |
|------|---------|--------|
| `config.json` (project root) | Old/legacy | Has no `theme_mode`, no `font_preset` |
| `src_v2/config.json` | v2 UI settings | Uses `font_preset: "normal"` (string), `theme_mode: "light"` |
| `src_v2/ART Q Control/config.json` | ART tool settings | Uses `font_size: 10` (integer), no `theme_mode` |
| `theme_config.json` (root) | Theme only | `theme_mode: "dark"` — conflicts with `src_v2/config.json` |

### 4.1 Inconsistent key names for the same concept

- `src_v2/config.json` uses `"font_preset": "normal"` (string preset name)
- `src_v2/ART Q Control/config.json` uses `"font_size": 10` (integer pixels)
- `src_v2/config/manager.py` defaults use `"font_size": 20`
- `src_v2/ui/services.py` line 34 hardcodes `max(20, get_ui_font_size(default=20))`

Four different representations of the same setting. Changing font size in Settings may update one file while the app reads from another on the next launch.

### 4.2 Theme mode conflict

- `src_v2/config.json`: `"theme_mode": "light"`
- `theme_config.json`: `"theme_mode": "dark"`

Both files are read by `utils/runtime.py`. Which one wins depends on load order — unpredictable behavior.

### 4.3 `config/manager.py` uses `"theme": "auto"`, code expects `"theme_mode"`

**File:** `src_v2/config/manager.py` `_create_default_config()`

```python
"ui_settings": {
    "theme": "auto",       # ← key is "theme"
    ...
}
```

But `utils/runtime.py` `get_theme_mode()` reads `config.get('ui_settings', {}).get('theme_mode', 'light')`. The key mismatch means `config/manager.py` defaults are never read for theme; the fallback `'light'` is always used instead.

### 4.4 `ConfigSetupDialog` is a factory function pretending to be a class

**File:** `src_v2/ART Q Control/config_loader.py` line 159

```python
def ConfigSetupDialog(config_manager):   # ← function, not a class
    ...
    return _ConfigSetupDialog(config_manager)   # returns an instance
```

It is named like a class but is a regular function. It is called with `dialog = ConfigSetupDialog(config_manager)` and then `dialog.exec_()`. This works, but it is deeply confusing and breaks IDE type analysis, auto-complete, and subclassing.

---

## 5. Duplicate Implementations

### 5.1 Two `runtime.py` files doing the same job

| File | Functions |
|------|-----------|
| `src_v2/utils/runtime.py` | `get_src_v2_root`, `get_project_root`, `get_runtime_paths`, `ensure_runtime_paths`, `read_json_file`, `get_ui_font_size`, `get_theme_mode`, `build_daily_cache_name`, `build_cache_path` |
| `src_v2/ART Q Control/runtime.py` | Same functions with minor path differences |

Any bug fix or new field must be applied to both files. One already diverges: `utils/runtime.py` computes `art_q_control_dir` from the project root; the ART Q Control version uses `_module_dir()`. If paths change, both need updating.

### 5.2 Two settings dialogs

| File | Lines |
|------|-------|
| `src_v2/ui/settings_dialog.py` | 621 |
| `src_v2/ui/settings_dialog_v2.py` | 622 |

Both are nearly identical. `shell.py` imports `SettingsDialog` from `settings_dialog.py`. It is unclear if `settings_dialog_v2.py` is an in-progress replacement or abandoned. Bug fixes applied to one are not reflected in the other.

### 5.3 Old tkinter Merger alongside new PyQt5 Merger

| File | Framework | Status |
|------|-----------|--------|
| `src_v2/Merger/Merger.py` | tkinter | Old, launched in dev mode (bug — see §2.4) |
| `src_v2/Merger/merger_window.py` | PyQt5 | Current, launched in production (.exe) |

Both coexist. The old one should be archived or deleted once the new one is confirmed stable.

### 5.4 Three overlapping theme/color systems

| File | Role |
|------|------|
| `src_v2/ui/design_system.py` | Centralised color tokens |
| `src_v2/ui/theme.py` | Another theme definition system |
| `src_v2/ui/theme_manager.py` | Legacy, imports from `design_system` |
| `src_v2/ui/services.py` | Builds its own inline stylesheets using color dicts |

To change a color you must potentially update four files. `services.py` builds full Qt stylesheets inline with f-strings, duplicating color references from `design_system.py`.

### 5.5 Whole `src/` directory alongside `src_v2/`

The project root contains both `src/` (old version) and `src_v2/` (new version). The old version is still present, causing confusion about which code is active. There is no clear migration complete date or archive marker.

---

## 6. Error Handling Gaps

### 6.1 Bare `except: pass` blocks swallow all errors silently

Pattern found throughout `ART Q Control/`:

```python
try:
    # critical business logic
except:
    pass
```

A bare `except` without a type catches `SystemExit`, `KeyboardInterrupt`, and every other exception. Silent `pass` means the user and developer get no feedback when something breaks. This is the single biggest debugging obstacle in the codebase.

Notable locations:
- `ART Q Control/Functions.py` — multiple bare `except: pass`
- `ART Q Control/AutoSender.py` — broad exception handlers
- `Archiver/Archiver.py` — 7 separate bare `pass` in except blocks
- `config_loader.py` line 195: `except: pass` when loading existing config

### 6.2 Settings open error silently falls through

**File:** `src_v2/ui/shell.py` lines 668–679

```python
def _open_settings(self):
    try:
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec_()
    except Exception as e:
        print(f"Error opening settings: {e}")
        QMessageBox.warning(self, "Settings Error", f"Could not open settings dialog:\n{str(e)}")
```

`print()` goes to the terminal/console. If the user launched the app via a desktop shortcut or .exe, there is no console — the error is invisible. Use proper logging.

### 6.3 `_keep_alive` swallows destroyed signal errors

**File:** `src_v2/utils/tool_launcher.py` lines 58–64

```python
try:
    widget.destroyed.connect(
        lambda: _open_windows.remove(widget) if widget in _open_windows else None
    )
except Exception:
    pass
```

If the signal connection fails, the window is never removed from `_open_windows`. It stays in the list forever, preventing garbage collection of every tool window opened during the session.

---

## 7. UI Problems

### 7.1 Hardcoded window sizes that ignore screen resolution

| File | Line | Size |
|------|------|------|
| `src_v2/ui/shell.py` | 286 | `self.resize(1380, 900)` |
| `src_v2/ui/main_window.py` | 137 | `self.setGeometry(100, 100, 1280, 800)` |
| `src_v2/Merger/merger_window.py` | 112 | `self.setMinimumSize(1200, 800)` |
| `src_v2/ART Q Control/config_loader.py` (dialog) | ~209 | `self.setMinimumSize(750, 800)` |

On a 1366×768 laptop screen the windows are too large. On a 4K display they feel tiny. No `QSettings` or screen-aware sizing is used.

### 7.2 Responsive grid (`_tools_grid`) never activates

**File:** `src_v2/ui/shell.py` (see §3.7)

The shell advertises responsive behavior — switching from 2 columns to 1 column on narrow screens — but the attribute that controls it (`self._tools_grid`) is never set. Resizing the window has no effect on the tool card grid layout.

### 7.3 Duplicate `font-size` in generated stylesheet

**File:** `src_v2/ui/services.py` (inside `build_shell_stylesheet`)

```css
QPushButton#secondaryButton {
    ...
    font-size: {button_size}px;    /* first declaration */
    font-size: {font_size}px;      /* second declaration — overrides the first */
    ...
}
```

The second `font-size` line silently overrides the first. The `button_size` variable is wasted. This makes font-size tuning unpredictable.

### 7.4 Inconsistent base font size across the codebase

| Location | Value |
|----------|-------|
| `src_v2/ui/services.py` line 34 | `max(20, ...)` — minimum 20px |
| `src_v2/ui/settings_dialog.py` | `int(16 * preset_enum.get_multiplier())` — base 16px |
| `src_v2/ART Q Control/config.json` | `"font_size": 10` |
| `src_v2/config/manager.py` defaults | `"font_size": 20` |

The settings dialog saves a value derived from base 16, but the shell enforces a minimum of 20. A user who sets "Small" text in settings gets 20px anyway because of the `max(20, ...)` clamp — their setting is ignored.

### 7.5 Email Replies widget comment contradicts its state

**File:** `src_v2/ui/main_window.py` lines 440–453

```python
# Email Replies Input
# TODO: Email Replies widget is currently hidden - under development
email_file_box = QGroupBox("Email Replies")
...
# Show the Email Replies widget (re-activated)
email_file_box.setVisible(True)
```

The comment says "hidden - under development" but the next line makes it visible. The code and comment are contradictory. It is unclear whether the feature is complete or still a work in progress.

### 7.6 Settings button and Profile button both open Settings

**File:** `src_v2/ui/shell.py` lines 328–342

Both the ⚙️ settings button and the profile button's "Settings" action call `self._open_settings()`. This is redundant but not broken. However, the profile button also has a "Sign Out" action (see §2.7) which only closes the window, making the profile menu misleading.

### 7.7 Search bar filters tool cards but leaves empty section titles visible

**File:** `src_v2/ui/shell.py` `_filter_tools()`

When filtering by search text, individual `EnhancedToolCard` widgets are hidden but the "All Tools" section title label remains visible even if all cards are hidden. The UI shows an orphan section header with no content below it.

### 7.8 `ToolPlaceholderDialog` shown for tools that are supposed to be launchable

**File:** `src_v2/ui/shell.py` `open_tool()`

If `can_launch_tool()` returns `False` (e.g., a `.py` file is missing in dev), the placeholder dialog appears. The placeholder dialog's body says "This tool remains pending until its exact production startup path is confirmed" — which is incorrect for fully implemented tools that just have a missing file. The user sees a confusing "pending migration" message for a working tool.

---

## 8. Data Flow & Logic Bugs

### 8.1 `_on_files_changed` removes files before new ones are loaded

**File:** `src_v2/Merger/merger_window.py` lines 250–268

```python
def _on_files_changed(self, file_paths: List[str]):
    current_loaded = set(self.service.loaded_files.keys())
    current_selected = {str(Path(path).resolve()) for path in file_paths}

    for removed_path in current_loaded - current_selected:
        self.service.remove_file(removed_path)

    self._refresh_sheet_selector()
    ...
```

Files are removed from the service when they leave `file_paths`, but new files are not added here — they are added only when `file_loaded` fires (line 229). If signals fire in the wrong order, the sheet selector is refreshed before the newly added file's data is loaded, showing stale data.

### 8.2 `MergerWorker.terminate()` on close is abrupt

**File:** `src_v2/Merger/merger_window.py` lines 453–463

```python
if self.worker and self.worker.isRunning():
    reply = QMessageBox.question(...)
    if reply == QMessageBox.No:
        a0.ignore()
        return
    self.worker.terminate()   # ← abrupt thread kill
```

`QThread.terminate()` kills the thread immediately without cleanup. If the worker is mid-write to an Excel file, the output file will be corrupted. Should request a graceful stop instead.

### 8.3 `_load_agent_name()` called twice on every shell build

**File:** `src_v2/ui/shell.py`

`_load_agent_name()` reads and parses `config.json` from disk. It is called in `_build_header()` (line 320) and again in `_view_profile()` (line 531). Each call opens and parses the file. The value should be loaded once in `__init__` and cached as `self._agent_name`.

### 8.4 Config moved to cache directory silently changes `config_manager.config_path`

**File:** `src_v2/ART Q Control/config_loader.py` lines 658–672

```python
config_manager.config_path = cache_config_path
config_manager.config_dir = cache_dir
```

After `init_config()` runs, the `config_manager` object's path is mutated to point to the cache copy. Any code that saves config after this will write to the cache directory, not the original location. On next launch the original file may still have old values. The config can drift between the two locations silently.

---

## 9. Code Quality Issues

### 9.1 Wildcard import pollutes namespace

**File:** `src_v2/ART Q Control/Main_BackUp_eticket_VoiceMail_II.py` line 24

```python
from Functions import *
```

Wildcard imports make it impossible to know what names are available, create silent shadowing of builtins, and prevent static analysis tools from working.

### 9.2 Type hint uses lowercase `any` instead of `Any`

**File:** `src_v2/ui/accessibility_helper.py`

```python
def get_accessibility_info(self) -> Dict[str, any]:
```

`any` is the built-in function. The correct type hint is `Any` from `typing`. This passes at runtime but breaks type checkers and misleads readers.

### 9.3 `ConfigSetupDialog` factory catches `except:` when loading existing config

**File:** `src_v2/ART Q Control/config_loader.py` line 195

```python
try:
    self.current_config = config_manager.load_config()
except:
    pass  # Config doesn't exist yet
```

This swallows all errors, including valid JSON parse errors, permission errors, and programming mistakes. The comment says "Config doesn't exist yet" but a `FileNotFoundError` is the only case that justifies passing silently.

### 9.4 `print()` used for logging throughout

Every module uses `print(f"[INFO] ...")` and `print(f"[WARNING] ...")`. There is a `src_v2/utils/error_logger.py` and `src_v2/ART Q Control/logger.py` — proper logging infrastructure exists but is not used consistently. `print()` output is lost when the app runs without a console (shortcut launch, `.exe`).

### 9.5 Inconsistent `__init__` calling pattern in Merger

**File:** `src_v2/Merger/merger_window.py` lines 91–93

```python
class MergerWindow(QMainWindow, V2TypographyMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)   # explicit second __init__ call
```

In Python MRO, `super().__init__()` is the correct pattern for cooperative multiple inheritance. Calling `V2TypographyMixin.__init__(self)` explicitly bypasses the MRO and can cause double-initialization if `V2TypographyMixin` ever calls `super()`.

---

## 10. Architecture Problems

### 10.1 No migration boundary — `src/` and `src_v2/` coexist with no deprecation plan

The `src/` directory contains the original implementation. `src_v2/` is the current active version. Both are present, meaning any developer who opens the project must figure out which version is active. No README section, no deprecation marker, no "do not modify src/" comment exists.

### 10.2 Config module in `src_v2/config/` is unused by most of the app

`src_v2/config/` contains `manager.py`, `validator.py`, `schema.py`, `migrator.py`, `backup.py`, `security.py`. This is a comprehensive config management system. However, most of the app reads config via `utils/runtime.py`'s `read_json_file()` which bypasses all of this. The `config/` module is largely a dead investment.

### 10.3 `V2SettingsBus` instantiated multiple times per window

**File:** `src_v2/ui/services.py` / `src_v2/ui/shell.py` / `src_v2/Merger/merger_window.py`

```python
self.settings_bus = V2SettingsBus()    # in MergerWindow
self._settings_bus = get_v2_settings_bus()  # in UnifiedToolShell
```

`get_v2_settings_bus()` returns a singleton. `V2SettingsBus()` creates a new instance. If a component creates its own `V2SettingsBus()` instead of using the singleton, it does not receive signals emitted from the shared bus. Theme/font changes may not propagate to all windows.

### 10.4 `set_tools()` rebuilds the entire UI

**File:** `src_v2/ui/shell.py` lines 585–594

```python
def set_tools(self, tools):
    self._tools = list(tools)
    self._tool_buttons.clear()
    old_central = self.centralWidget()
    if old_central is not None:
        old_central.deleteLater()
    self._build_ui()
```

Calling `set_tools()` tears down and rebuilds the entire central widget. All widget state (search text, scroll position) is lost. This is unnecessarily expensive and disruptive to the user.

### 10.5 No tests cover any UI behavior

The `tests/` directory exists but contains no tests for UI components, signal wiring, config loading, or tool launching. All tested paths (if any) are in utilities only. Given the number of broken wiring issues found above, even basic smoke tests would have caught several of them.

---

## 11. Priority Fix List

Ordered by impact vs. effort:

| # | Fix | Severity | Effort |
|---|-----|----------|--------|
| 1 | Remove password from config.json; use env var | CRITICAL | Low |
| 2 | Fix `open_main_menu()` import (`MainMenu` → `V2MainMenu`) | HIGH | Low |
| 3 | Fix dev-mode Merger launcher (points to old tkinter file) | HIGH | Low |
| 4 | Fix `_tools_grid` never assigned — responsive resize is dead | HIGH | Low |
| 5 | Fix duplicate `font-size` in `services.py` stylesheet | MEDIUM | Low |
| 6 | Fix `handlers_cache.json` relative path | MEDIUM | Low |
| 7 | Remove or properly implement `process_files()` | MEDIUM | Low |
| 8 | Replace bare `except: pass` blocks with typed exception handling + logging | HIGH | High |
| 9 | Unify config schema — one file, one key set, one reader | HIGH | High |
| 10 | Delete or archive duplicate `runtime.py` | MEDIUM | Medium |
| 11 | Delete or archive `settings_dialog_v2.py` (or make it the only one) | MEDIUM | Medium |
| 12 | Delete dead methods: `create_top_bar`, `create_right_panel`, `create_file_section`, `_create_processing_view` | MEDIUM | Low |
| 13 | Remove or archive old tkinter `Merger.py` | MEDIUM | Low |
| 14 | Replace all `print("[INFO]"` / `print("[WARNING]")` with the existing logger | MEDIUM | High |
| 15 | Remove `src/` or mark it as archived with a clear notice | LOW | Low |
| 16 | Add `self._agent_name` cache to avoid repeated disk reads | LOW | Low |
| 17 | Fix search bar to hide section title when all cards are filtered out | LOW | Low |
| 18 | Fix `MergerWorker.terminate()` — use a graceful stop flag instead | MEDIUM | Medium |
| 19 | Fix V2SettingsBus instantiation — use singleton everywhere | MEDIUM | Low |
| 20 | Add smoke tests for shell launch, settings open, tool card click | HIGH | High |
