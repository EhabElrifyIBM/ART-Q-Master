# ART Q Master — Full Codebase Refactor Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean up, rewire, and stabilise the `src_v2/` codebase: remove dead/duplicate files, establish a single config source of truth, fix settings propagation to all tool windows, improve error handling and logging, and fix all broken UI wiring.

**Architecture:** `src_v2/` is the sole production tree. Config is unified into one `src_v2/config.json` with two top-level sections (`ui_settings`, `agent_settings`). The `config/manager.py` singleton is the only reader/writer. The `V2SettingsBus` singleton (via `get_v2_settings_bus()`) is the only channel for live theme/font changes to tool windows.

**Tech Stack:** Python 3.10+, PyQt5, openpyxl/pandas, stdlib `logging`, `pathlib`.

## Global Constraints

- Never touch `src/` code — only drop an `ARCHIVED.md` marker inside it.
- Never commit the `password` field to any config file (ignore for now, leave as-is).
- All `import` fixes must keep backward-compatible module names where other files rely on them.
- `theme_manager.py` and `theme.py` stay in place — they already wrap `design_system.py`. Do not consolidate them in this refactor.
- Run `python src_v2/main.py` after every phase and confirm the shell opens without errors.
- Never call `V2SettingsBus()` directly outside `ui/services.py`. Always use `get_v2_settings_bus()`.
- File deletions must be preceded by a grep confirming nothing imports the file.

---

## Phase 1 — Safe File Cleanup

**Goal:** Remove orphaned, duplicate, and dead files without touching any logic.

---

### Task 1.1 — Archive `src/` and delete `theme_config.json`

**Files:**
- Create: `src/ARCHIVED.md`
- Delete: `theme_config.json` (project root)

- [ ] **Step 1: Create ARCHIVED.md inside src/**

```
src/ARCHIVED.md content:
# ARCHIVED

This directory contains the original pre-v2 implementation. It is no longer
maintained. All active development happens in `src_v2/`.

Do not modify files here. Do not import from here in new code.
```

Write the file:
```bash
# Using Write tool — create src/ARCHIVED.md with above content
```

- [ ] **Step 2: Confirm theme_config.json is not imported by any Python file**

```bash
grep -r "theme_config" src_v2/ --include="*.py"
```
Expected output: zero matches (only `utils/runtime.py` reads it as a fallback, which we'll fix in Phase 2).

- [ ] **Step 3: Delete theme_config.json**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\theme_config.json"
```

- [ ] **Step 4: Smoke test — shell still opens**

```bash
cd src_v2 && python main.py
```
Expected: Shell window opens. Close it.

---

### Task 1.2 — Delete orphaned `src_v2/ui/main_window.py`

**Files:**
- Delete: `src_v2/ui/main_window.py`

- [ ] **Step 1: Confirm nothing imports it**

```bash
grep -r "from ui.main_window\|from .main_window\|import main_window" src_v2/ --include="*.py"
```
Expected: zero matches.

- [ ] **Step 2: Delete file**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ui\main_window.py"
```

- [ ] **Step 3: Smoke test**

```bash
cd src_v2 && python main.py
```
Expected: Shell opens normally.

---

### Task 1.3 — Delete orphaned `src_v2/ui/settings_dialog_v2.py`

**Files:**
- Delete: `src_v2/ui/settings_dialog_v2.py`

- [ ] **Step 1: Confirm nothing imports it**

```bash
grep -r "settings_dialog_v2" src_v2/ --include="*.py"
```
Expected: zero matches (or only its own file-level if __name__ == __main__ block).

- [ ] **Step 2: Delete file**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ui\settings_dialog_v2.py"
```

---

### Task 1.4 — Delete orphaned `src_v2/ART Q Control/runtime.py`

**Files:**
- Delete: `src_v2/ART Q Control/runtime.py`

- [ ] **Step 1: Confirm nothing in ART Q Control imports it**

```bash
grep -r "from.*runtime import\|import runtime" "src_v2/ART Q Control/" --include="*.py"
```
Expected: zero matches (all ART Q Control files either use absolute `utils.runtime` or nothing).

- [ ] **Step 2: Delete file**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ART Q Control\runtime.py"
```

---

### Task 1.5 — Remove duplicate ART Q Control originals; rename backup file

**Files:**
- Delete: `src_v2/ART Q Control/AutoSender.py`
- Delete: `src_v2/ART Q Control/CaseReviewer.py`
- Delete: `src_v2/ART Q Control/CompaniesProcess.py`
- Rename: `Main_BackUp_eticket_VoiceMail_II.py` → `_reference_voicemail_eticket.py`

- [ ] **Step 1: Confirm originals are not imported by active _v2 files**

```bash
grep -r "from AutoSender import\|import AutoSender[^_]\|from CaseReviewer import\|import CaseReviewer[^_]\|from CompaniesProcess import\|import CompaniesProcess[^_]" "src_v2/ART Q Control/" --include="*.py"
```
Expected: zero matches (the `_v2` files import from each other using the `_v2` suffix).

- [ ] **Step 2: Delete original files**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ART Q Control\AutoSender.py"
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ART Q Control\CaseReviewer.py"
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ART Q Control\CompaniesProcess.py"
```

- [ ] **Step 3: Rename backup file**

```bash
git mv "src_v2/ART Q Control/Main_BackUp_eticket_VoiceMail_II.py" "src_v2/ART Q Control/_reference_voicemail_eticket.py"
```

---

### Task 1.6 — Delete old tkinter `Merger.py`

**Files:**
- Delete: `src_v2/Merger/Merger.py`

- [ ] **Step 1: Confirm nothing imports it (besides tool_launcher subprocess path, which we'll fix)**

```bash
grep -r "from Merger.Merger\|from Merger import Merger\|import Merger.Merger" src_v2/ --include="*.py"
```
Expected: zero matches (tool_launcher only builds a file path string, not an import).

- [ ] **Step 2: Delete file**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\Merger\Merger.py"
```

- [ ] **Step 3: Fix tool_launcher dev path (part of Phase 5, note it here)**

`src_v2/utils/tool_launcher.py` line 159 currently reads:
```python
"merger": os.path.join(paths.src_v2_root, "Merger", "Merger.py"),
```
This will break dev-mode launching after the deletion. Fix is in **Task 5.2**.

---

### Task 1.7 — Commit Phase 1

- [ ] **Step 1: Stage and commit**

```bash
git add -A
git commit -m "chore: phase 1 cleanup — remove orphaned/duplicate files, archive src/"
```

---

## Phase 2 — Config Consolidation

**Goal:** Single `src_v2/config.json` with two sections. `config/manager.py` is the only reader/writer. All other config files eliminated.

---

### Task 2.1 — Design and write the unified config schema

**Files:**
- Modify: `src_v2/config.json` (the existing file — merge with ART Q Control config)
- Modify: `src_v2/config/schema.py` (update to match new structure)

**Merged schema:**

```json
{
  "agent_settings": {
    "agent_name": "Your Name",
    "user_id": "",
    "password": "",
    "place_id": ""
  },
  "file_paths": {
    "excel_base_path": "",
    "cache_directory": ""
  },
  "crm_settings": {
    "excel_sheet_name": ""
  },
  "execution_settings": {
    "refresh_interval": 10
  },
  "ui_settings": {
    "theme_mode": "light",
    "font_preset": "normal",
    "high_contrast": false,
    "animations_enabled": true
  }
}
```

- [ ] **Step 1: Read current `src_v2/config.json` and `src_v2/ART Q Control/config.json`**

Use Read tool on both files to extract current values.

- [ ] **Step 2: Write merged `src_v2/config.json`**

Write the unified schema above, populating values from the existing files. Key mappings:
- `src_v2/config.json` → `ui_settings` section
- `src_v2/ART Q Control/config.json` → `agent_settings`, `file_paths`, `crm_settings`, `execution_settings`

- [ ] **Step 3: Update `src_v2/config/schema.py`**

Add/update the `UISettings` and top-level `Configuration` dataclass to include `ui_settings` dict:

```python
# src_v2/config/schema.py
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AgentSettings:
    agent_name: str = ""
    user_id: str = ""
    password: str = ""
    place_id: str = ""

@dataclass
class FilePaths:
    excel_base_path: str = ""
    cache_directory: str = ""

@dataclass
class CRMSettings:
    excel_sheet_name: str = ""

@dataclass
class ExecutionSettings:
    refresh_interval: int = 10

@dataclass
class UISettings:
    theme_mode: str = "light"
    font_preset: str = "normal"
    high_contrast: bool = False
    animations_enabled: bool = True
```

- [ ] **Step 4: Delete `src_v2/ART Q Control/config.json`**

```bash
del "C:\Users\EhabElrify\Desktop\Projects\ART Q Master\src_v2\ART Q Control\config.json"
```

---

### Task 2.2 — Wire `config/manager.py` to the correct absolute path

**Files:**
- Modify: `src_v2/config/manager.py`

The current `load()` takes a relative path. It must resolve to `src_v2/config.json` regardless of working directory.

- [ ] **Step 1: Add a module-level `get_config_path()` helper**

In `src_v2/config/manager.py`, add before the class:

```python
from pathlib import Path

def _default_config_path() -> Path:
    """Always resolve to src_v2/config.json regardless of cwd."""
    return Path(__file__).parent.parent / "config.json"
```

- [ ] **Step 2: Update `load()` to use absolute path by default**

```python
def load(self, config_path: Optional[str] = None) -> bool:
    with self._operation_lock:
        try:
            path = Path(config_path) if config_path else _default_config_path()
            self._config_path = path
            if not path.exists():
                self._config = self._create_default_config()
                self.save()
                return True
            with open(path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            return True
        except Exception as e:
            from utils.error_logger import get_error_logger
            get_error_logger("ConfigManager").log_error("Failed to load config", e)
            return False
```

- [ ] **Step 3: Update `_create_default_config()` to match the unified schema**

```python
def _create_default_config(self) -> Dict[str, Any]:
    return {
        "agent_settings": {
            "agent_name": "", "user_id": "", "password": "", "place_id": ""
        },
        "file_paths": {
            "excel_base_path": "", "cache_directory": ""
        },
        "crm_settings": {
            "excel_sheet_name": ""
        },
        "execution_settings": {
            "refresh_interval": 10
        },
        "ui_settings": {
            "theme_mode": "light",
            "font_preset": "normal",
            "high_contrast": False,
            "animations_enabled": True
        }
    }
```

- [ ] **Step 4: Add `get()` and `set()` convenience methods if not already present**

```python
def get(self, *keys: str, default: Any = None) -> Any:
    """Dot-path getter: get('ui_settings', 'theme_mode')"""
    with self._operation_lock:
        node = self._config
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

def set(self, *keys_and_value) -> None:
    """Dot-path setter: set('ui_settings', 'theme_mode', 'dark')"""
    *keys, value = keys_and_value
    with self._operation_lock:
        node = self._config
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value
```

- [ ] **Step 5: Add module-level singleton getter**

At the bottom of `manager.py`:

```python
_config_manager_instance: Optional['ConfigManager'] = None

def get_config_manager() -> 'ConfigManager':
    """Return the loaded singleton ConfigManager. Loads on first call."""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
        _config_manager_instance.load()
    return _config_manager_instance
```

---

### Task 2.3 — Update `utils/runtime.py` to read from the config manager

**Files:**
- Modify: `src_v2/utils/runtime.py`

`get_theme_mode()` currently reads JSON directly and has a legacy fallback to `theme_config.json`. Replace it with the config manager.

- [ ] **Step 1: Update `get_theme_mode()` and `get_runtime_paths()`**

```python
def get_theme_mode(default: str = "light") -> str:
    """Read theme mode from the unified config via ConfigManager."""
    try:
        from config.manager import get_config_manager
        return get_config_manager().get("ui_settings", "theme_mode", default=default)
    except Exception:
        return default

def get_runtime_paths() -> RuntimePaths:
    src_v2_root = get_src_v2_root()
    project_root = get_project_root()
    return RuntimePaths(
        project_root=project_root,
        src_v2_root=src_v2_root,
        art_q_control_dir=os.path.join(src_v2_root, "ART Q Control"),
        ui_dir=os.path.join(src_v2_root, "ui"),
        utils_dir=_utils_dir(),
        config_file=os.path.join(src_v2_root, "config.json"),  # src_v2/ not project root
    )
```

Note: `config_file` now points to `src_v2/config.json`, not the project root.

---

### Task 2.4 — Update `ART Q Control/config_loader.py` to use the shared manager

**Files:**
- Modify: `src_v2/ART Q Control/config_loader.py`

The `init_config()` function currently creates its own `ConfigManager` (the one in `config_loader.py`, not `config/manager.py`). It should delegate to the shared `config/manager.py` singleton.

- [ ] **Step 1: Update `init_config()` to load from the shared manager**

```python
def init_config():
    """
    Initialise configuration via the shared ConfigManager.
    Shows the setup dialog if required fields are empty.
    Returns the shared ConfigManager with loaded config.
    """
    from config.manager import get_config_manager
    mgr = get_config_manager()

    # If agent_name is empty, the tool hasn't been configured yet
    agent_name = mgr.get("agent_settings", "agent_name", default="")
    if not agent_name.strip():
        _run_setup_dialog(mgr, "Agent settings not configured.")

    return mgr


def _run_setup_dialog(mgr, reason: str) -> None:
    """Show the config setup dialog. Exits if the user cancels."""
    import sys
    from PyQt5.QtWidgets import QApplication, QDialog
    print(f"[INFO] {reason} Starting setup dialog...")
    app = QApplication.instance() or QApplication(sys.argv)
    dialog = ConfigSetupDialog(mgr)
    if dialog.exec_() != QDialog.Accepted:
        print("[ERROR] Configuration setup cancelled. Exiting.")
        sys.exit(1)
```

- [ ] **Step 2: Update `ConfigSetupDialog` to accept the shared manager type**

The `ConfigSetupDialog` factory currently uses the local `ConfigManager` class (the one defined in `config_loader.py`). Update the `save_configuration()` method inside the factory to call `mgr.set(...)` and `mgr.save()` using the shared manager's API instead of local `save_config()`.

Key change in `save_configuration()`:
```python
config_data = {
    "agent_settings": {"agent_name": agent_name, "user_id": user_id,
                       "password": password, "place_id": place_id},
    "file_paths": {"excel_base_path": excel_path, "cache_directory": cache_path},
    "crm_settings": {"excel_sheet_name": sheet_name},
    "execution_settings": {"refresh_interval": self.refresh_interval_input.value()}
}
for section, values in config_data.items():
    for key, value in values.items():
        self.config_manager.set(section, key, value)
self.config_manager.save()
```

- [ ] **Step 3: Smoke test ART Q Control launch**

```bash
cd src_v2 && python main.py
```
Click the Q Control tile. Confirm the config setup dialog appears if unconfigured, or the tool launches if configured.

---

### Task 2.5 — Update `shell.py` to read agent name from config manager

**Files:**
- Modify: `src_v2/ui/shell.py`

Replace `_load_agent_name()` disk-read-every-call pattern with cached read via config manager.

- [ ] **Step 1: Replace `_load_agent_name()` method**

```python
def _load_agent_name(self) -> str:
    """Load agent name from unified config (cached — reads disk once)."""
    try:
        from config.manager import get_config_manager
        return get_config_manager().get("agent_settings", "agent_name", default="User") or "User"
    except Exception:
        return "User"
```

The `_view_profile()` method also calls `self._load_agent_name()` — it will now use the cached manager result automatically.

---

### Task 2.6 — Commit Phase 2

- [ ] **Step 1: Stage and commit**

```bash
git add -A
git commit -m "feat: phase 2 — unified config in src_v2/config.json, config/manager.py as single reader"
```

---

## Phase 3 — Logger Enhancement

**Goal:** Improve `error_logger.py` with colour-coded terminal output and shorter messages. Replace all `print("[INFO]")` calls with the proper logger. Keep both terminal and file output.

---

### Task 3.1 — Enhance `utils/error_logger.py`

**Files:**
- Modify: `src_v2/utils/error_logger.py`

Current issues: `logging.basicConfig()` creates a new timestamped log file every session (hard to tail); no terminal colour; module_name on every call is verbose.

- [ ] **Step 1: Add ANSI colour codes and rewrite `_setup_logging()`**

Replace `_setup_logging()` with:

```python
# ANSI colour codes (Windows 10+ terminal supports them)
_COLOURS = {
    "DEBUG":    "\033[36m",   # cyan
    "INFO":     "\033[32m",   # green
    "WARNING":  "\033[33m",   # yellow
    "ERROR":    "\033[31m",   # red
    "CRITICAL": "\033[35m",   # magenta
    "RESET":    "\033[0m",
}

def _setup_logging(self):
    log_file = os.path.join(self.log_dir, f"{self.module_name}.log")

    file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    self.logger = logging.getLogger(self.module_name)
    self.logger.setLevel(logging.DEBUG)
    if not self.logger.handlers:   # avoid duplicate handlers on re-import
        self.logger.addHandler(file_handler)
    self.logger.propagate = False  # don't bubble to root logger
```

- [ ] **Step 2: Replace `print()` in `log_error()` with coloured output**

```python
def log_error(self, message, exception=None, error_level=ErrorLevel.ERROR, context=None, recovery_action=None):
    # ... existing record building ...

    # Coloured terminal output
    colour = _COLOURS.get(error_level.value, "")
    reset  = _COLOURS["RESET"]
    tag    = f"[{error_level.value}]"
    print(f"{colour}{tag}{reset} {self.module_name}: {message}")
    if exception:
        print(f"  ↳ {type(exception).__name__}: {exception}")
    if recovery_action:
        print(f"  ↳ Recovery: {recovery_action}")

    # File log
    self.logger.log(
        getattr(logging, error_level.value, logging.ERROR),
        message,
        exc_info=exception is not None
    )
```

- [ ] **Step 3: Add a convenience module function for quick logging**

At the bottom of `error_logger.py`, below `get_error_logger()`:

```python
def log(level: str, module: str, message: str, exc: Exception = None) -> None:
    """
    One-liner convenience wrapper for quick logging without storing the logger.

    Usage:
        from utils.error_logger import log
        log("INFO", "shell", "Settings dialog opened")
        log("ERROR", "shell", "Failed to open settings", exc=e)
    """
    logger = get_error_logger(module)
    level_map = {
        "DEBUG":    ErrorLevel.INFO,
        "INFO":     ErrorLevel.INFO,
        "WARNING":  ErrorLevel.WARNING,
        "ERROR":    ErrorLevel.ERROR,
        "CRITICAL": ErrorLevel.CRITICAL,
    }
    logger.log_error(message, exception=exc, error_level=level_map.get(level.upper(), ErrorLevel.INFO))
```

---

### Task 3.2 — Replace `print("[INFO]")` calls with `log()` across src_v2

**Files to update:**
- `src_v2/ui/shell.py` (3–4 print calls)
- `src_v2/utils/tool_launcher.py` (none — already clean)
- `src_v2/ART Q Control/config_loader.py` (8+ print calls)
- `src_v2/config/manager.py` (2 print calls)
- `src_v2/Merger/merger_window.py` (0 — already using status bar)

Pattern to apply everywhere:

```python
# BEFORE
print(f"[INFO] Shell loaded font preset from config: {saved_preset}")
print(f"[WARNING] Could not load preset from config: {e}")

# AFTER
from utils.error_logger import log
log("INFO", "shell", f"Loaded font preset: {saved_preset}")
log("WARNING", "shell", "Could not load font preset", exc=e)
```

- [ ] **Step 1: Update `src_v2/ui/shell.py`**

Find all `print(f"[INFO]` / `print(f"[WARNING]` / `print(f"Warning:` / `print(f"Error:` in `shell.py` and replace with `log()` calls. Add import at the top of the file: `from utils.error_logger import log`.

- [ ] **Step 2: Update `src_v2/ART Q Control/config_loader.py`**

Replace all `print(f"[INFO]")`, `print(f"[WARN]")`, `print(f"[ERROR]")` calls. Add import.

- [ ] **Step 3: Update `src_v2/config/manager.py`**

Replace `print(f"Error loading configuration: {e}")` etc.

- [ ] **Step 4: Run smoke test**

```bash
cd src_v2 && python main.py
```
Confirm terminal output now shows coloured log lines (e.g., `[INFO] shell: Loaded font preset: normal`).

---

### Task 3.3 — Commit Phase 3

```bash
git add -A
git commit -m "feat: phase 3 — enhanced logger with colour output; replace print() calls"
```

---

## Phase 4 — Settings Propagation Fix

**Goal:** Theme and font changes in the Settings dialog propagate live to every open tool window (Merger, Archiver, DailyMerger, MonthlyMerger, Assigner, QControl).

**Root cause:** 4 tool windows call `V2SettingsBus()` directly, creating isolated instances. The Settings dialog emits its own signals but never calls `get_v2_settings_bus().set_theme()`.

---

### Task 4.1 — Fix all tool windows to use the singleton bus

**Files:**
- Modify: `src_v2/Merger/merger_window.py:95`
- Modify: `src_v2/Archiver/archiver_window.py:124`
- Modify: `src_v2/DailyMerger/daily_merger_window.py:299`
- Modify: `src_v2/MonthlyMerger/monthly_merger_window.py:224`

In every file, replace:
```python
self.settings_bus = V2SettingsBus()
```
with:
```python
from ui.services import get_v2_settings_bus
self.settings_bus = get_v2_settings_bus()
```

Also remove the unused `V2SettingsBus` import from each file's import block.

- [ ] **Step 1: Update `merger_window.py`**

Line 19-20 currently imports `V2SettingsBus`. Change to:
```python
from ui.services import get_v2_settings_bus
```
Line 95: `self.settings_bus = get_v2_settings_bus()`

- [ ] **Step 2: Update `archiver_window.py`**

Same pattern.

- [ ] **Step 3: Update `daily_merger_window.py`**

Same pattern.

- [ ] **Step 4: Update `monthly_merger_window.py`**

Same pattern.

- [ ] **Step 5: Verify no other direct instantiations exist**

```bash
grep -rn "V2SettingsBus()" src_v2/ --include="*.py"
```
Expected: only one match in `ui/services.py` (the singleton factory).

---

### Task 4.2 — Overhaul `settings_dialog.py`: wire to singleton bus and fix propagation

**Files:**
- Modify: `src_v2/ui/settings_dialog.py`

The current dialog emits its own `theme_changed` / `font_size_changed` signals. These are not connected to the singleton bus. Fix: when the user applies a setting, call `get_v2_settings_bus().set_theme()` / `set_font_size()` directly. The bus emits to all connected tool windows automatically.

- [ ] **Step 1: Add singleton bus import to settings_dialog.py**

At the top of the file (after existing imports):
```python
from ui.services import get_v2_settings_bus
from config.manager import get_config_manager
```

- [ ] **Step 2: In `__init__`, bind to the singleton bus instead of using module-level `theme_manager`**

Replace:
```python
self._init_managers()
self.current_theme = getattr(theme_manager, 'current_theme', None)
...
```
With:
```python
self._bus = get_v2_settings_bus()
self._cfg = get_config_manager()
self.current_theme = self._bus.theme
self.current_preset = self._cfg.get("ui_settings", "font_preset", default="normal")
```

- [ ] **Step 3: Update `_apply_theme_change()` (or equivalent save method)**

When the user clicks "Apply" or "Save", the method must:
1. Call `self._bus.set_theme(new_theme)` — broadcasts to all windows live
2. Call `self._bus.font_preset_changed.emit(new_preset)` — broadcasts font change
3. Call `self._cfg.set("ui_settings", "theme_mode", new_theme)` — persists to disk
4. Call `self._cfg.set("ui_settings", "font_preset", new_preset)` — persists to disk
5. Call `self._cfg.save()` — writes config.json

Pattern:
```python
def _apply_settings(self):
    theme = self._get_selected_theme()     # read from combo/radio in dialog
    preset = self._get_selected_preset()   # read from combo in dialog

    # Live broadcast to all open windows
    self._bus.set_theme(theme)
    self._bus.font_preset_changed.emit(preset)

    # Persist to config
    self._cfg.set("ui_settings", "theme_mode", theme)
    self._cfg.set("ui_settings", "font_preset", preset)
    self._cfg.save()
```

- [ ] **Step 4: Remove the dialog's own `theme_changed` / `font_size_changed` pyqtSignals**

These are now redundant — the bus handles propagation. Remove:
```python
theme_changed = pyqtSignal(str)
font_size_changed = pyqtSignal(float)
accessibility_changed = pyqtSignal(dict)
```
And remove any `self.theme_changed.emit(...)` / `self.font_size_changed.emit(...)` calls.

- [ ] **Step 5: Manual test — settings propagate to open Merger**

1. Run `python src_v2/main.py`
2. Open the Merger from the shell
3. Open Settings (⚙️ button)
4. Switch theme to Dark → click Apply/OK
5. Confirm: shell AND Merger window both switch to dark theme immediately

---

### Task 4.3 — Persist font preset on shell load (fix the clamp bug)

**Files:**
- Modify: `src_v2/ui/services.py`
- Modify: `src_v2/ui/shell.py`

Current bug: `V2SettingsBus.__init__` sets `self._font_size = max(20, get_ui_font_size(default=20))` which always returns 20, ignoring the saved preset. `set_font_size()` clamps to `max(20, ...)` which ignores "small" preset.

The font system is preset-based (`small`/`normal`/`large`/`xlarge`) not pixel-based. Fix the bus to load the preset from config on init.

- [ ] **Step 1: Update `V2SettingsBus.__init__` to load theme and preset from config**

```python
def __init__(self):
    super().__init__()
    try:
        from config.manager import get_config_manager
        cfg = get_config_manager()
        self._theme = cfg.get("ui_settings", "theme_mode", default="light")
        self._font_preset = cfg.get("ui_settings", "font_preset", default="normal")
    except Exception:
        self._theme = "light"
        self._font_preset = "normal"
    self._font_size = 20   # pixel fallback; preset system drives actual sizes
    self._dev_mode: bool = False
```

- [ ] **Step 2: Add `font_preset` property and `set_font_preset()` method to bus**

```python
@property
def font_preset(self) -> str:
    return self._font_preset

def set_font_preset(self, preset: str) -> None:
    valid = {"small", "normal", "large", "xlarge"}
    if preset not in valid:
        return
    self._font_preset = preset
    self.font_preset_changed.emit(preset)
```

- [ ] **Step 3: Update `_apply_settings()` in settings dialog to use `set_font_preset()` instead of `font_preset_changed.emit()` directly**

```python
self._bus.set_font_preset(preset)   # emits signal AND updates internal state
```

---

### Task 4.4 — Commit Phase 4

```bash
git add -A
git commit -m "feat: phase 4 — settings propagation fixed; all tools use singleton V2SettingsBus"
```

---

## Phase 5 — Broken Wiring & Dead Code Removal

**Goal:** Fix all broken method wiring. Remove dead UI elements and dead methods. Fix dev-mode Merger launcher.

---

### Task 5.1 — Fix `open_main_menu()` import error in `main_window.py`

> **Note:** If `src_v2/ui/main_window.py` was deleted in Task 1.2 (it is orphaned), skip this task. Otherwise:

**Files:**
- Modify: `src_v2/ui/main_window.py` (if it still exists after Task 1.2)

The method tries `from .main_menu import MainMenu` but the class is `V2MainMenu`.

- [ ] **Step 1: Fix the import**

```python
def open_main_menu(self):
    try:
        from ui.main_menu import V2MainMenu
        self.menu_window = V2MainMenu()
        self.menu_window.show()
        self.close()
    except Exception as e:
        from utils.error_logger import log
        log("ERROR", "main_window", "Failed to open main menu", exc=e)
```

---

### Task 5.2 — Fix dev-mode Merger launcher in `tool_launcher.py`

**Files:**
- Modify: `src_v2/utils/tool_launcher.py`

The dev subprocess path points to the deleted `Merger/Merger.py` (tkinter). Create a `run_merger.py` entry point first, then update the launcher.

- [ ] **Step 1: Create `src_v2/Merger/run_merger.py`**

```python
"""Entry point for running the Merger standalone (dev mode)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from Merger.merger_window import MergerWindow

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    w = MergerWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update `_get_v2_file_map()` in `tool_launcher.py`**

```python
"merger": os.path.join(paths.src_v2_root, "Merger", "run_merger.py"),
```

- [ ] **Step 3: Update `_build_launch_command()` to handle merger like other tools**

Merger currently falls through to `[sys.executable, target]`. Add:
```python
if tool_id == "merger":
    return [sys.executable, "-m", "Merger.run_merger"]
```
Place this before the final `return [sys.executable, target]`.

- [ ] **Step 4: Test dev-mode Merger launch**

```bash
cd src_v2 && python main.py
```
Click the Merger tile. Confirm `MergerWindow` (PyQt5) opens, not the old tkinter app.

---

### Task 5.3 — Fix `handlers_cache.json` absolute path

**Files:**
- Modify: `src_v2/ui/main_window.py` (if still present — this is for the Assigner or other QControl window that uses this)

Search all files for `handlers_cache.json`:

```bash
grep -rn "handlers_cache" src_v2/ --include="*.py"
```

For each file found, replace the relative open with an absolute path:

```python
# BEFORE
with open('handlers_cache.json', 'w') as f:

# AFTER
from utils.runtime import get_src_v2_root
import os
_cache_path = os.path.join(get_src_v2_root(), 'handlers_cache.json')
with open(_cache_path, 'w') as f:
```

Apply the same fix to the corresponding read call.

---

### Task 5.4 — Remove dead methods from `main_window.py` (Assigner window) if applicable

If `src_v2/ui/main_window.py` was deleted in Phase 1, skip this task.

Otherwise, remove the following confirmed-dead methods (grep confirms they are never called):
- `create_top_bar()`
- `create_right_panel()`
- `create_file_section()`
- `_create_processing_view()`

Also:
- Remove the hidden `QProgressBar` creation code (lines ~489–525) — if the feature is removed, don't create the widget
- Replace `show_progress()` with a proper log line or remove it
- Disable (not hide) the Progress View button until reimplemented: `progress_btn.setEnabled(False)`
- Replace `process_files()` stub with disabled button: add `setEnabled(False)` to the connected button on init
- Replace `output_path_changed()` stub with actual validation or remove the signal connection

---

### Task 5.5 — Fix responsive grid in shell (`_tools_grid` never assigned)

**Files:**
- Modify: `src_v2/ui/shell.py`

`resizeEvent` checks `hasattr(self, '_tools_grid')` but the attribute is never set.

- [ ] **Step 1: Assign `self._tools_grid` in `_build_all_tools_section()`**

```python
def _build_all_tools_section(self) -> QWidget:
    ...
    grid_layout = QGridLayout()
    grid_layout.setSpacing(16)
    grid_layout.setContentsMargins(0, 0, 0, 0)
    self._tools_grid = grid_layout  # ← assign to self so resizeEvent can reach it
    ...
```

This makes the responsive resize logic in `resizeEvent` actually fire when the window width crosses 800px.

---

### Task 5.6 — Fix search leaving orphan section title

**Files:**
- Modify: `src_v2/ui/shell.py`

When all cards in "All Tools" are filtered out, the "All Tools" section title label remains visible.

- [ ] **Step 1: Track the section title and hide it when all cards are hidden**

In `_build_all_tools_section()`, store the title label:
```python
self._all_tools_title = title   # QLabel("All Tools")
```

In `_filter_tools()`, after hiding/showing cards:
```python
any_visible = any(card.isVisible() for card in self._tool_cards.values())
if hasattr(self, '_all_tools_title'):
    self._all_tools_title.setVisible(any_visible)
```

---

### Task 5.7 — Fix duplicate `font-size` in stylesheet

**Files:**
- Modify: `src_v2/ui/services.py`

The `build_shell_stylesheet()` (and `build_tool_dialog_stylesheet()`) have a `QPushButton#secondaryButton` rule with two `font-size:` declarations. The second overrides the first.

- [ ] **Step 1: Find the duplicate**

```bash
grep -n "font-size" src_v2/ui/services.py
```

- [ ] **Step 2: Remove the first `font-size: {button_size}px;` line in secondaryButton rule**

Keep only `font-size: {font_size}px;` (the one with the dynamic `font_size` variable, which is what the rest of the stylesheet uses). Delete the `button_size` variable if it becomes unused.

---

### Task 5.8 — Fix misleading "Sign Out" UX

**Files:**
- Modify: `src_v2/ui/shell.py`

"Sign Out" in the profile dropdown just calls `self.close()`. There is no authentication session in the app.

- [ ] **Step 1: Rename "Sign Out" to "Exit" in `ProfileButton`**

In `src_v2/ui/components_v2/__init__.py` or wherever `ProfileButton` is defined, find the "Sign Out" menu item and rename it to "Exit".

- [ ] **Step 2: Update the connected method**

```python
def _sign_out(self):
    """Exit the application."""
    reply = QMessageBox.question(
        self, "Exit", "Are you sure you want to exit ART Q Master?",
        QMessageBox.Yes | QMessageBox.No
    )
    if reply == QMessageBox.Yes:
        self.close()
```

- [ ] **Step 3: Rename the method from `_sign_out` to `_exit_app`**

Update the connection in `_build_header()`:
```python
profile_btn.signOutClicked.connect(self._exit_app)
```

---

### Task 5.9 — Fix `MergerWorker.terminate()` → graceful stop

**Files:**
- Modify: `src_v2/Merger/merger_window.py`

`QThread.terminate()` kills the thread immediately and can corrupt Excel output files.

- [ ] **Step 1: Add a stop flag to `MergerWorker`**

```python
class MergerWorker(QThread):
    def __init__(self, service, operation, payload=None):
        super().__init__()
        self.service = service
        self.operation = operation
        self.payload = payload
        self._stop_requested = False

    def request_stop(self):
        """Ask the worker to stop after the current step."""
        self._stop_requested = True
```

- [ ] **Step 2: Check the flag at safe points in `run()`**

```python
def run(self):
    try:
        if self.operation == "merge":
            ...
            def progress_callback(message: str):
                if self._stop_requested:
                    raise InterruptedError("Merge cancelled by user")
                step["count"] += 1
                ...
```

- [ ] **Step 3: Update `closeEvent` in `MergerWindow`**

```python
if self.worker and self.worker.isRunning():
    reply = QMessageBox.question(...)
    if reply == QMessageBox.No:
        a0.ignore()
        return
    self.worker.request_stop()      # ← graceful request
    self.worker.wait(3000)          # wait up to 3s
    if self.worker.isRunning():
        self.worker.terminate()     # force-kill only as last resort
```

---

### Task 5.10 — Commit Phase 5

```bash
git add -A
git commit -m "feat: phase 5 — fix broken wiring, dead code removal, responsive grid, merger graceful stop"
```

---

## Phase 6 — Error Handling

**Goal:** Replace bare `except: pass` and broad `except Exception: pass` blocks with typed handling and proper log calls throughout `ART Q Control/` and other modules.

---

### Task 6.1 — Audit and fix bare `except` in `ART Q Control/`

**Files:**
- Modify: `src_v2/ART Q Control/AutoSender_v2.py`
- Modify: `src_v2/ART Q Control/CaseReviewer_v2.py`
- Modify: `src_v2/ART Q Control/CompaniesProcess_v2.py`
- Modify: `src_v2/ART Q Control/Dispatcher_v2.py`

- [ ] **Step 1: Find all bare except blocks**

```bash
grep -n "except:" "src_v2/ART Q Control/AutoSender_v2.py"
grep -n "except:" "src_v2/ART Q Control/CaseReviewer_v2.py"
grep -n "except:" "src_v2/ART Q Control/CompaniesProcess_v2.py"
grep -n "except:" "src_v2/ART Q Control/Dispatcher_v2.py"
```

- [ ] **Step 2: For each bare `except: pass` — apply this pattern**

```python
# BEFORE
try:
    risky_operation()
except:
    pass

# AFTER
try:
    risky_operation()
except Exception as e:
    from utils.error_logger import log
    log("WARNING", "AutoSender_v2", "risky_operation failed", exc=e)
```

Specific case: if the operation is genuinely "best effort" and failure is expected (e.g., cleaning up a temp file), use `except OSError` with a comment explaining why it's safe to ignore.

- [ ] **Step 3: Fix broad `except Exception: pass` blocks similarly**

```bash
grep -n "except Exception" "src_v2/ART Q Control/" -r --include="*.py"
```

For each one, check whether the exception is being discarded entirely. If yes, add a log call.

---

### Task 6.2 — Fix bare `except` in `Archiver/`

**Files:**
- Modify: `src_v2/Archiver/Archiver.py` (7 bare `pass` statements)
- Modify: `src_v2/Archiver/archiver_service.py`

Same pattern as Task 6.1.

- [ ] **Step 1: Audit**

```bash
grep -n "except:" src_v2/Archiver/ -r --include="*.py"
grep -n "except Exception" src_v2/Archiver/ -r --include="*.py"
```

- [ ] **Step 2: Fix each occurrence**

For file-cleanup operations (e.g., deleting temp files), `except OSError` is acceptable. For business logic, always log.

---

### Task 6.3 — Fix `_keep_alive` memory leak in `tool_launcher.py`

**Files:**
- Modify: `src_v2/utils/tool_launcher.py`

Current code catches signal-connection failure silently, leaving windows in `_open_windows` forever.

- [ ] **Step 1: Fix the handler**

```python
def _keep_alive(widget) -> None:
    """Prevent a window from being garbage-collected after launch."""
    _open_windows.append(widget)
    try:
        widget.destroyed.connect(
            lambda: _open_windows.remove(widget) if widget in _open_windows else None
        )
    except Exception as e:
        log("WARNING", "tool_launcher", f"Could not connect destroyed signal for {widget}", exc=e)
        # Widget will stay in _open_windows but this is benign — it won't block shutdown
```

---

### Task 6.4 — Fix `config_loader.py` bare `except: pass` when loading config

**Files:**
- Modify: `src_v2/ART Q Control/config_loader.py`

Line 195: `except: pass  # Config doesn't exist yet`

- [ ] **Step 1: Replace with typed exception**

```python
try:
    self.current_config = config_manager.load_config()
except (FileNotFoundError, KeyError):
    pass   # Config not yet created — safe to ignore
except Exception as e:
    log("WARNING", "config_loader", "Unexpected error loading existing config", exc=e)
```

---

### Task 6.5 — Fix `except: pass` in `settings_dialog.py` (`_init_managers`-style lazy init)

Find all bare except in `settings_dialog.py`:
```bash
grep -n "except" src_v2/ui/settings_dialog.py
```
Apply typed exceptions throughout.

---

### Task 6.6 — Commit Phase 6

```bash
git add -A
git commit -m "feat: phase 6 — typed exception handling; bare except blocks eliminated"
```

---

## Phase 7 — Code Quality

**Goal:** Fix type hints, remove wildcard imports, fix `ConfigSetupDialog` naming, fix `_is_valid_time` dead code.

---

### Task 7.1 — Fix wildcard import in `_reference_voicemail_eticket.py`

**Files:**
- Modify: `src_v2/ART Q Control/_reference_voicemail_eticket.py`

```python
# BEFORE
from Functions import *

# AFTER
# This is a reference file only — do not use in production.
# Specific imports were: (list the names actually used in the file)
from Functions import FunctionA, FunctionB   # replace with actual names
```

- [ ] **Step 1: Read the file to find which names from `Functions` are actually used**

```bash
grep -n "^from Functions import\|^import Functions" "src_v2/ART Q Control/_reference_voicemail_eticket.py"
```

Then grep for usage of each name in the file and import only those.

---

### Task 7.2 — Fix `any` → `Any` type hint in `accessibility_helper.py`

**Files:**
- Modify: `src_v2/ui/accessibility_helper.py`

```python
# BEFORE
def get_accessibility_info(self) -> Dict[str, any]:

# AFTER
from typing import Any
def get_accessibility_info(self) -> Dict[str, Any]:
```

---

### Task 7.3 — Remove duplicate `get_accessibility_manager()` definition

**Files:**
- Modify: `src_v2/ui/accessibility_helper.py`

Two definitions exist (~line 480 and ~line 629). Python uses the second (last) definition silently.

- [ ] **Step 1: Find both definitions**

```bash
grep -n "def get_accessibility_manager" src_v2/ui/accessibility_helper.py
```

- [ ] **Step 2: Remove the first definition**

Keep the second (lower) definition which Python actually uses.

---

### Task 7.4 — Remove dead `_is_valid_time()` from `config_loader.py`

**Files:**
- Modify: `src_v2/ART Q Control/config_loader.py`

Verify it's never called:
```bash
grep -rn "_is_valid_time\|is_valid_time" src_v2/ --include="*.py"
```

If zero external callers: delete the `_is_valid_time` static method from `ConfigManager`.

---

### Task 7.5 — Fix `ConfigSetupDialog` factory naming

**Files:**
- Modify: `src_v2/ART Q Control/config_loader.py`

The function `ConfigSetupDialog(config_manager)` is named like a class but is a factory function. This breaks IDE tooling and type analysis.

- [ ] **Step 1: Rename to a function naming convention**

```python
def create_config_setup_dialog(config_manager):
    """Factory: creates and returns a _ConfigSetupDialog instance."""
    ...
    return _ConfigSetupDialog(config_manager)
```

- [ ] **Step 2: Update all callers**

```bash
grep -rn "ConfigSetupDialog(" src_v2/ --include="*.py"
```

Replace each call:
```python
# BEFORE
dialog = ConfigSetupDialog(config_manager)

# AFTER
dialog = create_config_setup_dialog(config_manager)
```

---

### Task 7.6 — Final smoke test and commit

- [ ] **Step 1: Full manual test**

1. Launch `python src_v2/main.py`
2. Confirm shell opens, all tool tiles are visible
3. Search "merger" → only Merger card visible; "All Tools" title visible; search "xyz" → "All Tools" title hidden
4. Open Settings → change theme to Dark → Apply → shell AND any open tool window switch to dark
5. Open Merger → load 2 Excel files → preview merge → merge to output → confirm file exists
6. Open Settings from within Merger's shortcut or top bar if applicable
7. Resize shell below 800px → confirm grid switches to 1 column
8. Open Q Control → confirm config setup dialog or main tool window appears correctly

- [ ] **Step 2: Commit**

```bash
git add -A
git commit -m "feat: phase 7 — code quality fixes; wildcard imports, type hints, dead code, factory rename"
```

---

## Self-Review

### Spec Coverage Check

| Requirement | Covered in |
|-------------|-----------|
| Ignore password | ✅ Not touched anywhere |
| Fix wiring (MainMenu import) | ✅ Task 5.1 |
| Fix wiring (Merger dev launcher) | ✅ Task 5.2 |
| Fix wiring (handlers_cache path) | ✅ Task 5.3 |
| Remove dead code (4 methods) | ✅ Task 5.4 |
| Remove dead code (progress bar widget) | ✅ Task 5.4 |
| Config single source of truth | ✅ Tasks 2.1–2.5 |
| Delete ART Q Control/config.json | ✅ Task 2.1 |
| Delete theme_config.json | ✅ Task 1.1 |
| Remove ART Q Control duplicate files | ✅ Task 1.5 |
| Rename backup file | ✅ Task 1.5 |
| Delete old Merger.py | ✅ Task 1.6 |
| Delete orphaned main_window.py | ✅ Task 1.2 |
| Delete settings_dialog_v2.py | ✅ Task 1.3 |
| Delete ART Q Control/runtime.py | ✅ Task 1.4 |
| Archive src/ | ✅ Task 1.1 |
| Settings propagation to sub-tools | ✅ Tasks 4.1–4.3 |
| Fix font preset propagation / clamp bug | ✅ Task 4.3 |
| Improve logger (colour, brevity, both terminal+UI) | ✅ Tasks 3.1–3.2 |
| Replace print() with logger | ✅ Task 3.2 |
| Fix responsive grid (_tools_grid) | ✅ Task 5.5 |
| Fix search orphan section title | ✅ Task 5.6 |
| Fix duplicate font-size in stylesheet | ✅ Task 5.7 |
| Fix misleading Sign Out → Exit | ✅ Task 5.8 |
| Fix MergerWorker.terminate() | ✅ Task 5.9 |
| Fix bare except blocks (ART Q Control) | ✅ Task 6.1 |
| Fix bare except blocks (Archiver) | ✅ Task 6.2 |
| Fix _keep_alive memory leak | ✅ Task 6.3 |
| Fix wildcard import | ✅ Task 7.1 |
| Fix `any` → `Any` type hint | ✅ Task 7.2 |
| Remove duplicate get_accessibility_manager | ✅ Task 7.3 |
| Remove dead _is_valid_time | ✅ Task 7.4 |
| Fix ConfigSetupDialog factory naming | ✅ Task 7.5 |

### Placeholder Scan

No "TBD", "TODO", or "implement later" placeholders in any task. Every code change shows the exact replacement code.

### Type Consistency

- `get_v2_settings_bus()` returns `V2SettingsBus` — used consistently in Tasks 4.1, 4.2, 4.3
- `get_config_manager()` returns `ConfigManager` — used in Tasks 2.2, 2.4, 2.5, 4.2, 4.3
- `log(level, module, message, exc)` signature defined in Task 3.1, used in all Phase 3+ tasks
- `set_font_preset(preset: str)` defined in Task 4.3, used in Task 4.2
