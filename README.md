# ART Q Master

**Lenovo ART Team Automation Suite** — A Windows desktop application for the NA PC Assurance Resolution Team that automates case management workflows via Microsoft Dynamics 365 CRM and Excel-based data processing.

> **Current Release:** `v2.0.1` — built with PyInstaller, one-folder bundle at `dist/ART Q Master v2/`

---

## 📦 What Is This Project?

ART Q Master is a **Windows desktop automation suite** built to help Lenovo ART team agents process large queues of support cases efficiently. It combines:

- **CRM automation** via Selenium (auto-sending SMS, emails, notes in Dynamics 365)
- **Excel-based case assignment and pipeline processing** via pandas / openpyxl
- **Excel file management utilities** (Merger, Daily Merger, Monthly Merger, Archiver)
- **Reach Rate analytics** — per-channel metrics across SMS, Email, and Phone Calls
- **A PyQt5 GUI** built on the IBM Carbon Design System that ties everything together

The tool runs on the agent's local machine, opens Chrome, navigates Dynamics 365 CRM and a SIP dialer, and performs actions that would otherwise require many manual steps per case.

---

## 🏗️ Project Structure

```
ART-Q-Master/
├── src_v2/                         # Active v2 source tree
│   ├── main.py                     # Entry point — launches unified v2 main menu
│   ├── version.py                  # Single source of truth for app version
│   ├── ART Q Control/              # Core CRM automation engine
│   │   ├── Dispatcher_v2.py        # Mode selector dialog (entry point)
│   │   ├── AutoSender_v2.py        # Mode 1: Process NEW cases (SMS + Email + Note)
│   │   ├── CaseReviewer_v2.py      # Mode 2: Review IN-PROGRESS cases via dialer
│   │   ├── CompaniesProcess_v2.py  # Mode 3: Batch-process grouped company cases
│   │   ├── SharedFunctions.py      # Shared CRM helpers, templates, config loader
│   │   ├── config_loader.py        # ConfigManager + first-time setup dialog
│   │   ├── ibm_theme.py            # IBM Carbon theme constants for ART Q Control
│   │   ├── logger.py               # Structured logger for automation runs
│   │   └── runtime.py              # Runtime state and session management
│   ├── Assigner/
│   │   ├── main_window_assigner.py # ART Q Assigner PyQt5 dashboard
│   │   └── assigner_processor.py  # Full Excel case assignment pipeline (FileProcessor)
│   ├── ui/
│   │   ├── main_menu.py            # Unified v2 main menu (UnifiedToolShell)
│   │   ├── shell.py                # Base shell / window frame
│   │   ├── services.py             # Background service orchestration
│   │   ├── design_system.py        # IBM Carbon Design System constants
│   │   ├── theme.py                # Theme tokens
│   │   ├── theme_manager.py        # Light / Dark / Auto theme switching
│   │   ├── typography.py           # IBM Plex font management
│   │   ├── typography_mixin.py     # Mixin for consistent typography in widgets
│   │   ├── responsive.py           # Responsive layout helpers
│   │   ├── keyboard_shortcuts.py   # Global keyboard shortcut registry
│   │   ├── keyboard_locker.py      # Locks keyboard during CRM automation
│   │   ├── accessibility_helper.py # Screen reader + keyboard navigation support
│   │   ├── settings.py             # Persisted settings model
│   │   ├── settings_dialog_v2.py   # Settings UI (theme, font size, accessibility)
│   │   ├── views.py                # Reusable view base classes
│   │   ├── feedback_guide.py       # In-app feedback guide widget
│   │   ├── company_metadata_display.py  # Company info widget
│   │   ├── components/             # Reusable v1-era dialog components
│   │   └── components_v2/          # IBM Carbon component library
│   │       ├── buttons.py
│   │       ├── cards.py
│   │       ├── dialogs.py
│   │       ├── inputs.py
│   │       ├── tables.py
│   │       ├── navigation.py
│   │       └── feedback.py
│   ├── Merger/
│   │   ├── Merger.py               # (legacy) tkinter merger
│   │   ├── merger_window.py        # PyQt5 merger window
│   │   ├── merger_service.py       # Merge logic service layer
│   │   └── components/             # File list, sheet selector, column mapper, preview
│   ├── DailyMerger/
│   │   ├── daily_merger_window.py  # PyQt5 daily merger UI
│   │   ├── daily_merger_service.py # Daily merge logic
│   │   └── components/             # Calendar, file list, summary widgets
│   ├── MonthlyMerger/
│   │   ├── monthly_merger_window.py
│   │   └── run_monthly_merger.py
│   ├── Archiver/
│   │   ├── Archiver.py             # (legacy) tkinter archiver
│   │   ├── archiver_window.py      # PyQt5 archiver window
│   │   ├── archiver_service.py     # Archive logic service layer
│   │   └── components/             # File selector, analysis view, export dialog
│   ├── Reach Rate Calculator/
│   │   ├── ReachRateCalculator.py          # Core calculation engine
│   │   ├── ReachRateCalculatorUI_v2.py     # Active PyQt5 UI
│   │   └── chart_generator.py              # matplotlib chart builder
│   ├── file_processing/
│   │   ├── processor.py            # FileProcessor — full Excel pipeline
│   │   └── final_processor.py      # FinalProcessor — output sheet builder
│   ├── config/
│   │   ├── manager.py              # Config read/write manager
│   │   ├── schema.py               # JSON schema definitions
│   │   ├── validator.py            # Runtime config validation
│   │   ├── migrator.py             # Config schema migrations
│   │   ├── backup.py               # Config backup/restore
│   │   └── security.py             # Credential encryption helpers
│   └── utils/
│       ├── crash_handler.py        # Global crash reporter
│       ├── error_handler.py        # Centralised error handling
│       ├── error_logger.py         # File-based error logging
│       ├── tool_launcher.py        # Tool launch orchestration
│       ├── tool_registry.py        # Registry of available tools
│       ├── recent_tools.py         # Recently-used tools tracker
│       ├── recent_merger_files.py
│       ├── recent_daily_merger_files.py
│       ├── recent_archiver_files.py
│       ├── merge_templates.py      # Saved merge configuration templates
│       ├── runtime.py              # App-wide runtime state
│       ├── helpers.py              # General utilities
│       └── timezone_map.py         # US/Canada state → timezone mappings
├── assets/
│   └── ibm_logo.png                # App icon used in the .exe
├── config.json                     # User configuration (agent name, paths, credentials)
├── art_q_master_v2.spec            # PyInstaller build spec
└── docs/                           # Internal session-based development notes
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **GUI Framework** | PyQt5 (primary), tkinter (legacy merger/archiver) |
| **Design System** | IBM Carbon Design System — `#0f62fe` primary blue |
| **CRM Automation** | Selenium WebDriver + Chrome + WebDriverManager |
| **CRM System** | Microsoft Dynamics 365 (Lenovo-hosted instance) |
| **Dialer System** | SIP-based web dialer at `104.232.254.43` |
| **Data Processing** | pandas, openpyxl, xlsxwriter |
| **Charts** | matplotlib (Reach Rate Calculator) |
| **Config Storage** | `config.json` (JSON, schema-validated on startup) |
| **Packaging** | PyInstaller 6.x — one-folder Windows bundle |
| **OS Integration** | ctypes — Windows sleep/display inhibit during automation |
| **Logging** | Python `logging` — file + console + GUI handlers |
| **Timezone** | `zoneinfo` / `pytz` — US & Canada state → timezone mapping |
| **Screenshots** | Selenium `save_screenshot` on element-find failure |
| **Error reporting** | Structured crash handler, timestamped error logs in `errors/` |

---

## 🚀 Tools & Features

### 1. ART Q Assigner (`Assigner/`)
A **multi-panel PyQt5 dashboard** for processing raw CRM export files into per-handler day-sheets:

- **Inputs:** Raw CRM export Excel, previous day's output, SMS replies file, email replies file
- **Processing pipeline (`FileProcessor`):**
  - Validates and normalises 40+ CRM columns with fuzzy column-name matching
  - Filters out cancelled, CID, DMR, and escalation cases
  - Parses SMS/Email reply codes (`1` = Fixed, `2` = Issue Not Fixed, `3` = DND/Stop)
  - Detects DND contacts, updates status, maintains a persistent DND database
  - Computes customer local time using state → timezone mapping
  - Assigns cases to handlers with fair distribution and company-grouping rules
  - **Chat Agent auto-distribution** (enabled via checkbox): redistributes in-progress cases from overloaded handlers at the final step, using a fixed `"Chat Agent's Cases"` sheet for cross-day preservation
  - Writes per-handler sheets + Companies sheet + Summary + Skipped Cases + Issue Not Fixed
- **Output:** Multi-sheet Excel workbook, password-protected sheets (`artadmin`)

---

### 2. ART Q Control — Mode: Auto Sender (`ART Q Control/AutoSender_v2.py`)
**Processes NEW cases** that have never been contacted:

- For each new case: opens CRM → checks status → detects e-ticket → extracts serial/name → sends **SMS** → sends **Email** (OnSite/Depot or CRU template) → adds **Case Note**
- Date-stamped working cache with resume support (`RESUME` / `NEW` dialog)
- Live progress monitor with **Pause / Resume / Abort** controls
- Windows sleep inhibit keeps the machine awake during long runs

---

### 3. ART Q Control — Mode: Case Reviewer (`ART Q Control/CaseReviewer_v2.py`)
**Reviews IN-PROGRESS cases** that were previously contacted:

- Uses the **SIP dialer** to place calls through Dynamics 365
- Per-case dialog: closing code selector, DND flag, Issue Not Fixed flag, case note, Previous / Next / Skip navigation
- **Support Agent mode** — process on behalf of a different agent
- Seamless window switching between CRM and Dialer

---

### 4. ART Q Control — Mode: Companies Process (`ART Q Control/CompaniesProcess_v2.py`)
**Batch-processes cases grouped by company email:**

- Groups cases by company email → shows per-case outcome dialog per group → applies closing codes and saves in CRM
- Runs standalone (from Dispatcher) or auto-chains after Auto Sender

---

### 5. Excel Merger (`Merger/`)
A **PyQt5 multi-step wizard** for merging multiple Excel files:

1. Select `.xlsx` / `.xls` files with recent-files memory
2. Choose sheets to merge (searchable list)
3. Configure column mapping (add / remove / combine)
4. Preview output before saving
5. Save as new Excel file — supports saved merge templates

---

### 6. Daily Merger (`DailyMerger/`)
Consolidates **daily handler sheets** from multiple workbooks into a single file:

- Calendar-based date selection
- Daily file list with auto-detection
- Summary view before export

---

### 7. Monthly Merger (`MonthlyMerger/`)
End-of-month aggregation tool that consolidates all daily outputs into a **monthly master workbook**.

---

### 8. Excel Archiver (`Archiver/`)
A **PyQt5 tool** for managing large Excel workbooks over time:

- Analyses all handler sheets and extracts date metadata
- **Export by month** — extract all cases for a selected month (with optional cleanup from source)
- **Export old cases** — extract cases older than a configurable threshold (N days)
- Background threading keeps the UI responsive during long exports

---

### 9. Reach Rate Calculator (`Reach Rate Calculator/`)
**Analytics tool** for measuring channel effectiveness across SMS, Email, and Phone Calls:

- Compares case numbers across PA Cases, SMS View, Email View, and Phone Call View sheets
- Computes **reached vs. not-reached** per case per channel
- Optional **date range filter** (start / end date) using `Completion Date`, `Date Created`, `Entered Queue`
- **Output Excel** contains:
  - Total Cases sheet with channel matching
  - **Metrics sheet** with tables and matplotlib charts:
    - Breakdown 1: Total numbers per channel per month
    - Breakdown 2: Reached vs. Not Reached per channel per month
    - Breakdown 3: Reach rate per channel per month
    - Breakdown 4: Work Order Type (OnSite / Depot / CRU) per channel per month

---

## ⚙️ Configuration (`config.json`)

```json
{
  "agent_settings": {
    "agent_name": "Agent Full Name",
    "user_id": "Dialer username / agent ID",
    "password": "Dialer password",
    "place_id": "SIP Place ID for dialer"
  },
  "file_paths": {
    "excel_base_path": "Path to folder containing daily PA sheets",
    "cache_directory": "Path to folder for working cache files"
  },
  "crm_settings": {
    "excel_sheet_name": "Agent's Cases (sheet name inside the daily Excel)"
  },
  "execution_settings": {
    "start_time": "HH:MM (24h) — automation start window",
    "end_time": "HH:MM (24h) — automation end window",
    "refresh_interval": 10
  },
  "ui_settings": {
    "font_size": 10
  }
}
```

Config is validated on every startup via the `config/` schema subsystem. Missing or invalid fields surface a `ConfigSetupDialog` (PyQt5 form with file pickers) before any tool launches.

---

## 🎨 UI System

Built on the **IBM Carbon Design System**:

- **Theme Manager:** Light, Dark, and Auto (detects Windows dark mode) — `#0f62fe` primary blue
- **Typography:** IBM Plex Sans at configurable sizes; `typography_mixin.py` propagates font changes to all open widgets
- **Keyboard Shortcuts:** Global registry (`keyboard_shortcuts.py`) for power-user navigation
- **Keyboard Locker:** Blocks stray keypresses from interfering with CRM automation
- **Accessibility:** Keyboard navigation, screen reader hints (`accessibility_helper.py`)
- **Components V2:** `buttons`, `cards`, `dialogs`, `inputs`, `tables`, `navigation`, `feedback` — IBM Carbon tokens throughout
- **Responsive Layout:** `responsive.py` adapts panels to different window sizes
- **Recent Files:** Separate recency trackers for Merger, Daily Merger, and Archiver

---

## ✅ Feature Status

| Feature | Status |
|---|---|
| ART Q Assigner — full Excel pipeline | ✅ Working |
| Auto Sender — SMS sending | ✅ Working |
| Auto Sender — Email sending (OnSite/Depot & CRU) | ✅ Working |
| Auto Sender — Case note insertion | ✅ Working |
| Auto Sender — E-ticket detection + field auto-fill | ✅ Working |
| Auto Sender — Cache resume | ✅ Working |
| Auto Sender — Progress monitor with pause/abort | ✅ Working |
| Case Reviewer — Full call flow via dialer | ✅ Working |
| Case Reviewer — Closing code dialog | ✅ Working |
| Case Reviewer — DND marking + Case notes | ✅ Working |
| Case Reviewer — Support Agent mode | ✅ Working (lightly tested) |
| Companies Process — Grouped batch processing | ✅ Working |
| Chat Agent auto-distribution (final step) | ✅ Working |
| Chat Agent — fixed sheet name across days | ✅ Working |
| Excel Merger — multi-file, multi-sheet wizard | ✅ Working |
| Daily Merger | ✅ Working |
| Monthly Merger | ✅ Working |
| Archiver — Export by month / by age | ✅ Working |
| Reach Rate Calculator — per-channel metrics | ✅ Working |
| Reach Rate Calculator — monthly breakdowns (4 tables) | ✅ Working |
| IBM Carbon Design System UI | ✅ Working |
| Theme Manager — Light / Dark / Auto | ✅ Working |
| Config schema validation + migration | ✅ Working |
| Windows sleep inhibit during automation | ✅ Working |
| Crash handler + structured error logs | ✅ Working |
| PyInstaller one-folder `.exe` bundle | ✅ Working (`v2.0.1`) |
| PowerBI Dashboard button | ❌ Placeholder — not implemented |
| Voicemail injection via CABLE Input | ❌ Known issue — audio routing blocked |

---

## ⚠️ Known Issues

| Area | Issue |
|---|---|
| Column mapping | 4-level fuzzy fallback — may silently pick wrong column if raw file has unusual headers |
| Email duplicate sheet | Duplicate-email cases found but final output destination needs verification |
| SMS/Email → PA Cases sync | Reply status updates written to handler sheets only, not back to PA Cases sheet |
| DND database | Case-sensitive email matching; no deduplication or size cap |
| `merge_with_previous()` | 200+ line method — functional but fragile to modification |
| `Functions.py` (legacy) | Uses PyQt6 while the rest of the project uses PyQt5 — do not import directly |
| `Main.py` (legacy V1) | Not actively used — replaced by `Dispatcher_v2.py` |

---

## 🔮 Planned / Future Work

| Feature | Notes |
|---|---|
| **Column mapping refactor** | Unified `_detect_column()` + custom config-file mappings |
| **Email duplicate sheet fix** | Clarify and implement Companies sheet output for duplicates |
| **DND database improvements** | Fuzzy/case-insensitive matching, deduplication |
| **Unit test suite** | `pytest` coverage for pipeline, handler assignment, Chat Agent logic |
| **PowerBI Dashboard** | Placeholder button exists — live case metrics view |
| **Voicemail playback** | Audio injection to CABLE Input for Genesys (routing issue) |
| **Scheduled auto-launch** | Start automation at configured `start_time` without manual trigger |
| **Automated daily summary report** | Export what was sent/reviewed per session |
| **Full PyQt5 migration** | Remove remaining tkinter (`config_manager.py`) and PyQt6 (`Functions.py`) code |

---

## 🏃 How to Run

### From source

```bash
# From project root
python src_v2/main.py
```

### From the built executable

```
dist/
└── ART Q Master v2/
    ├── ART Q Master v2.exe   ← launch this
    └── _internal/            ← must stay alongside the .exe
```

On first run, if `config.json` is missing or incomplete, a setup dialog appears to collect agent credentials and file paths before any tool is launched.

### Build the executable yourself

```bash
pyinstaller art_q_master_v2.spec --clean
```

Requires PyInstaller 6.x and all project dependencies installed in the active Python environment.

---

## 📋 Key Files Reference

| File | Purpose |
|---|---|
| [`src_v2/main.py`](src_v2/main.py) | Application entry point |
| [`src_v2/version.py`](src_v2/version.py) | Single source of truth for version string |
| [`src_v2/ART Q Control/Dispatcher_v2.py`](src_v2/ART%20Q%20Control/Dispatcher_v2.py) | ART Q Control launcher (mode selector) |
| [`src_v2/ART Q Control/SharedFunctions.py`](src_v2/ART%20Q%20Control/SharedFunctions.py) | All shared CRM automation functions |
| [`src_v2/ART Q Control/AutoSender_v2.py`](src_v2/ART%20Q%20Control/AutoSender_v2.py) | Auto Sender mode (new cases) |
| [`src_v2/ART Q Control/CaseReviewer_v2.py`](src_v2/ART%20Q%20Control/CaseReviewer_v2.py) | Case Reviewer mode (in-progress cases) |
| [`src_v2/ART Q Control/CompaniesProcess_v2.py`](src_v2/ART%20Q%20Control/CompaniesProcess_v2.py) | Company batch processing mode |
| [`src_v2/Assigner/assigner_processor.py`](src_v2/Assigner/assigner_processor.py) | Core Excel pipeline (FileProcessor + FinalProcessor) |
| [`src_v2/Assigner/main_window_assigner.py`](src_v2/Assigner/main_window_assigner.py) | ART Q Assigner PyQt5 UI |
| [`src_v2/ui/main_menu.py`](src_v2/ui/main_menu.py) | Unified v2 main menu |
| [`src_v2/ui/design_system.py`](src_v2/ui/design_system.py) | IBM Carbon Design System constants |
| [`src_v2/Reach Rate Calculator/ReachRateCalculatorUI_v2.py`](src_v2/Reach%20Rate%20Calculator/ReachRateCalculatorUI_v2.py) | Reach Rate Calculator UI |
| [`art_q_master_v2.spec`](art_q_master_v2.spec) | PyInstaller build spec |
| [`config.json`](config.json) | User / agent configuration |
