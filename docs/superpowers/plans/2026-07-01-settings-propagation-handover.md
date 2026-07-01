# Handover — Settings Dialog Error + Settings Not Propagating to Sub-Tools

Date: 2026-07-01
Context: Continuation of the ART Q Master v2 refactor. Phases 1–7 of the main
refactor are done (see `.superpowers/sdd/progress.md` and git log). This
handover covers a NEW issue reported after those phases, not yet fixed.

## What the user reported

1. Opening Settings (or just running the app) prints these lines to console:
   ```
   [INFO ] Shell        | Shell loaded font preset from config: normal
   Warning: Could not load agent name: No module named 'config.manager'; 'config' is not a package
   [ACCESSIBILITY] Keyboard navigation setup with 12 focusable widgets
   [INFO] Theme loaded from config.json: light
   [WARN ] Shell        | Could not load font preset: No module named 'config.manager'; 'config' is not a package
   [INFO] Set current font preset: normal
   ```
2. Changing font/theme in the Settings dialog: Assigner picks up the theme
   change; user is unsure whether Assigner's font size updates; **every other
   sub-tool (Merger, Archiver, DailyMerger, MonthlyMerger, Reach Rate
   Calculator) does not receive the settings change.**

User's exact invocation:
```
& C:/Users/EhabElrify/AppData/Local/Programs/Python/Python314/python.exe "c:/Users/EhabElrify/Desktop/Projects/ART Q Master/src_v2/main.py"
```
Note: Python **3.14.0**, launched with an absolute interpreter path from the
project root as cwd.

## Investigation done so far (this session)

### Finding A — "config is not a package" could NOT be reproduced here

I ran `python src_v2/main.py` and `python "c:/.../src_v2/main.py"` from this
sandbox multiple times (after clearing `__pycache__`) and got **no output at
all** — the import succeeded silently every time. I also tested the import
directly:
```python
sys.path.insert(0, ".../src_v2")
sys.path.insert(0, ".../src_v2/ART Q Control")
from config.manager import get_config_manager   # works fine here
```
No conflicting `pip`-installed package named `config` exists in this
environment (`pip show config` → not found). `src_v2/config/__init__.py`
exists and is a normal package.

**This means the failure is environment-specific to the user's machine/Python
3.14 install, not a code defect visible from source alone.** Next session
should reproduce it live in the user's actual environment (not assume from
reading code) before attempting a fix. Things worth checking there:
- `python -c "import sys; print(sys.path)"` run the same way the user
  launches it, to see if `src_v2` is really on `sys.path`, and in what order.
- Whether `_ensure_import_paths()` (`src_v2/main.py` lines ~24–30) actually
  ran before the failing import. It inserts `"ART Q Control"` at
  `sys.path[0]` **after** inserting `src_v2` root at `sys.path[0]`, so the
  final order is `[ART Q Control, src_v2, ...]`. If `ART Q Control` ever
  gains its own `config.py`/`config/` (it currently doesn't — only
  `config_loader.py` and `config_manager.py`, no bare `config.py`), it would
  shadow the real package. Worth double-checking case-sensitivity and stray
  files there on the user's disk.
- Whether the user has a global `PYTHONPATH` env var or another project on
  their system that puts some unrelated `config` namespace package earlier
  in resolution.
- Whether this is a **Python 3.14-specific** import-system change (3.14 is
  very new; namespace-package resolution details have shifted across 3.x
  versions before). Confirm what Python version this project has actually
  been tested against elsewhere in the repo (check for a `pyproject.toml` /
  `requirements.txt` version pin, or ask the user).

### Where this import actually gets used (3 call sites, all wrapped in try/except so they degrade to defaults rather than crash)

- `src_v2/ui/shell.py:402` — `_load_agent_name()`, falls back to `"User"`
- `src_v2/ui/settings_dialog.py:419` — `_save_preset_to_config()`, silently fails to persist
- `src_v2/ui/settings_dialog.py:428` — `_load_current_preset()`, falls back to `"normal"` (this is the one whose warning fires **specifically when the Settings dialog is constructed**, matching the user's "when I open settings" report)
- `src_v2/utils/runtime.py:97` — `get_theme_mode()`, falls back to `"light"`

None of these raise — they all log a warning and continue with a default.
So the console warnings are not fatal, but they mean **font-preset
persistence to `config.json` silently fails** in the user's environment:
changes made in Settings won't survive to the next launch even if this
session's live behavior were otherwise fine.

### Finding B — architectural reason settings can't propagate to already-open sub-tools in dev mode (HIGH CONFIDENCE, this one IS a real code-level issue)

`src_v2/utils/tool_launcher.py`:
- `_is_frozen()` (line 36) returns `False` for a normal `python main.py` run.
- `launch_tool()` (line 228) calls `_launch_in_subprocess()` (line 258) whenever
  not frozen — i.e. **every tool launch during normal dev-mode use spawns a
  separate OS process** via `subprocess.Popen`.

`V2SettingsBus` (`src_v2/ui/services.py`) is an in-memory `QObject` singleton
(`get_v2_settings_bus()`), reachable only within one process's memory space.
**A `Popen`-spawned subprocess gets its own separate Python interpreter, its
own separate `V2SettingsBus` instance, and never receives Qt signals emitted
in the main shell's process.** This is not a wiring bug in the individual
tool windows — it's a structural limitation of using an in-memory singleton
across process boundaries. It only works correctly when:
- the app is a **frozen build** (`_is_frozen()` → True), where `tool_launcher`
  uses `_launch_in_process()` instead (line ~233) and all tool windows really
  do share one process/one bus, or
- multiple tools are opened **within the same running dev-mode process**
  (not currently possible via the UI's normal "launch tool" button, since
  that path always subprocesses in dev mode).

This fully explains "other sub tools does not get the settings passed
through": in the user's dev-mode session, each sub-tool they opened is a
separate process that already has its own default settings loaded at its own
startup and can never hear about later changes made in the shell.

It also explains why a **freshly launched** tool might still pick up a
change (it re-reads `config.json` — or the `V2SettingsBus.__init__` default
via `get_theme_mode()`/`get_ui_font_size()` — at its own startup), *provided*
Finding A hasn't already broken that persistence path. In the user's actual
run, Finding A likely means even fresh launches don't pick up the new value
either, since the write to `config.json` never happened.

### Finding C — MonthlyMerger is missing a signal connection (confirmed, independent bug)

Grep of every tool window's constructor for settings-bus connections:

| Window | theme_changed | font_preset_changed / font_size_changed |
|---|---|---|
| Assigner (`main_window_assigner.py:246,249`) | ✅ | ✅ `font_size_changed` |
| Merger (`merger_window.py:235,236`) | ✅ | ✅ `font_preset_changed` |
| Archiver (`archiver_window.py:312,313`) | ✅ | ✅ `font_preset_changed` |
| DailyMerger (`daily_merger_window.py:539,540`) | ✅ | ✅ `font_preset_changed` |
| **MonthlyMerger (`monthly_merger_window.py:904`)** | ✅ | ❌ **missing** |
| ReachRateCalculator (`ReachRateCalculatorUI_v2.py:275,278`) | ✅ | ✅ `font_preset_changed` |
| Dispatcher_v2 (`Dispatcher_v2.py:141,142`) | ✅ | ✅ `font_size_changed` |

**Fix needed regardless of Findings A/B**: `monthly_merger_window.py` needs a
`self.settings_bus.font_preset_changed.connect(<handler>)` line near line 904,
plus a handler method that calls whatever the equivalent of `apply_typography()`
is for that window (check how Archiver/DailyMerger's `apply_typography`
methods are implemented and mirror the pattern — MonthlyMerger already has
the card/label structure built during Phase-refactor work in this repo, it
just never wires the font signal).

## Suggested next-session plan

1. **Reproduce Finding A live** in the user's actual environment (ask them to
   run a small diagnostic: print `sys.path` and Python version at the top of
   `src_v2/main.py`, or have them run `python -c "import sys; sys.path.insert(0, r'...\src_v2'); from config.manager import get_config_manager; print('ok')"` directly) before changing any code. Don't guess-fix this one.
2. Once reproduced, most likely fixes depending on cause:
   - If it's an `ART Q Control`-before-`src_v2` sys.path ordering issue: flip
     the insertion order in `_ensure_import_paths()` (`src_v2/main.py`) so
     `src_v2` root ends up first, not `ART Q Control`.
   - If it's a namespace-package quirk specific to Python 3.14: may need
     `sys.path` to use `os.path.realpath()` normalization, or ensure no
     duplicate/mixed-case path entries exist.
3. **Fix MonthlyMerger's missing `font_preset_changed` connection** — this is
   real and doesn't depend on reproducing Finding A. Straightforward, mirror
   Archiver/DailyMerger's pattern.
4. **Decide what to do about Finding B** (dev-mode subprocess isolation).
   Options, in rough order of effort:
   - Cheapest: document it as expected dev-mode behavior (settings changes
     require closing and reopening a sub-tool to take effect in dev mode;
     frozen builds behave correctly) — if that's an acceptable UX, no code
     change needed beyond making sure config.json persistence (Finding A)
     actually works so reopened tools pick up the new value.
   - Bigger: make dev-mode also launch in-process (call `_launch_in_process`
     unconditionally, or add a dev flag), so all tools share one
     `V2SettingsBus` and live propagation actually works during development.
     Check why subprocess launching was chosen for dev mode in the first
     place (likely so each tool gets its own Qt event loop / crash isolation
     during development) before changing this — it may be an intentional
     tradeoff, in which case option (a) is more appropriate.
5. Re-verify with a real settings-change test: open two sub-tools + main
   shell in one session, change theme/font in Settings, confirm which
   windows update live vs. need reopening, and confirm the change persists
   in `src_v2/config.json` (`ui_settings.theme_mode` / `ui_settings.font_preset`)
   after closing the whole app.

## Relevant file map

- `src_v2/main.py` — `_ensure_import_paths()`, sys.path setup
- `src_v2/config/manager.py`, `src_v2/config/__init__.py` — the package that fails to import in the user's env
- `src_v2/ui/services.py` — `V2SettingsBus`, `get_v2_settings_bus()` singleton
- `src_v2/ui/settings_dialog.py` — `_save_preset_to_config`, `_load_current_preset`, `_on_theme_changed`, `_on_preset_changed`
- `src_v2/ui/shell.py` — `_load_agent_name`, `_load_saved_preset`, `_on_preset_changed`
- `src_v2/utils/tool_launcher.py` — `_is_frozen`, `_launch_in_subprocess`, `_launch_in_process`, `launch_tool`
- `src_v2/MonthlyMerger/monthly_merger_window.py` — missing `font_preset_changed` connection (~line 904)
- `src_v2/utils/runtime.py` — `get_theme_mode()`, another `config.manager` import call site
