# ART Q Master

**Lenovo ART Team Automation Suite** — A desktop application for the NA PC Assurance Resolution Team that automates case management workflows via Microsoft Dynamics 365 CRM and Excel-based data processing.

---

## 📦 What Is This Project?

ART Q Master is a **Windows desktop automation suite** built to help Lenovo ART team agents process large queues of support cases efficiently. It combines:

- **CRM automation** via Selenium (auto-sending SMS, emails, notes in Dynamics 365)
- **Excel-based case assignment and pipeline processing** via pandas / openpyxl
- **Excel file management utilities** (Merger and Archiver)
- **A PyQt5 GUI** that ties all of the above together in one launcher

The tool runs on the agent's local machine, opens Chrome, navigates Dynamics 365 CRM and a SIP dialer, and performs actions that would otherwise require many manual steps per case.

---

## 🏗️ Project Structure

```
ART-Q-Master/
├── src/
│   ├── main.py                   # Entry point — launches main menu or a specific module
│   ├── ART Q Control/            # Core CRM automation engine
│   │   ├── Dispatcher.py         # (Legacy) V1 dispatcher
│   │   ├── Dispatcher_v2.py      # Active entry point — mode selector dialog
│   │   ├── SharedFunctions.py    # Shared CRM helpers, templates, config loader
│   │   ├── AutoSender_v2.py      # Mode 1: Process NEW cases (SMS + Email + Note)
│   │   ├── CaseReviewer_v2.py    # Mode 2: Review IN-PROGRESS cases via dialer
│   │   ├── CompaniesProcess_v2.py# Mode 3: Batch-process cases grouped by company email
│   │   ├── config_loader.py      # ConfigManager + first-time setup dialog (PyQt5)
│   │   ├── config_manager.py     # Legacy credential manager (tkinter, JSON hidden file)
│   │   ├── Functions.py          # Legacy standalone helpers (PyQt6-based dialogs)
│   │   ├── Main.py               # Legacy monolithic main script (V1 — not active)
│   │   └── Main_BackUp_eticket_VoiceMail_II.py  # Prototype/backup script
│   ├── ui/
│   │   ├── main_menu.py          # PyQt5 main menu window with tool launcher buttons
│   │   ├── main_window.py        # ART Q Assigner — Excel case-assignment pipeline UI
│   │   ├── theme_manager.py      # Light/Dark/Auto theme system with IBM color palette
│   │   ├── settings_dialog.py    # Settings UI (theme, font size, accessibility)
│   │   ├── settings_observer.py  # Observer pattern for theme/font-size changes
│   │   ├── settings_aware_dialog.py # Mixin for dialogs to auto-respond to settings
│   │   ├── accessibility_helper.py  # Keyboard navigation and screen reader support
│   │   ├── company_metadata_display.py # Company info display widget
│   │   ├── keyboard_locker.py    # Locks keyboard during automation to prevent interference
│   │   └── components/
│   │       ├── base_dialog.py         # Base dialog with common styling
│   │       ├── case_review_dialog.py  # Case review UI component
│   │       ├── company_email_dialog.py # Company email interaction dialog
│   │       ├── dialog_components.py   # Reusable dialog widgets
│   │       ├── feedback_dialog.py     # User feedback dialog
│   │       ├── loading_spinner.py     # Animated loading spinner widget
│   │       └── progress_monitor.py    # Real-time progress tracking widget
│   ├── file_processing/
│   │   ├── processor.py          # FileProcessor — full Excel pipeline (4184 lines)
│   │   └── final_processor.py    # Extended/alternative processor variant
│   ├── Merger/
│   │   └── Merger.py             # Excel file merger utility (tkinter UI)
│   ├── Archiver/
│   │   └── Archiver.py           # Excel workbook archiver — export by month/age
│   └── utils/
│       ├── config.py             # Global utility config
│       ├── error_handler.py      # Centralized error handling
│       ├── error_logger.py       # File-based error logging
│       ├── helpers.py            # General utilities
│       └── timezone_map.py       # US/Canada state → timezone mappings
├── config.json                   # User configuration (agent name, paths, credentials)
├── theme_config.json             # Persisted theme preference
└── docs/                         # Internal session-based development notes (may be stale)
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **GUI Framework** | PyQt5 (primary), tkinter (Merger, Archiver, legacy) |
| **CRM Automation** | Selenium WebDriver + Chrome + WebDriverManager |
| **CRM System** | Microsoft Dynamics 365 (Lenovo-hosted instance) |
| **Dialer System** | SIP-based web dialer at `104.232.254.43` |
| **Data Processing** | pandas, openpyxl, xlsxwriter |
| **Config Storage** | `config.json` (JSON, validated on startup) |
| **Packaging** | PyInstaller (frozen executable support in `main.py`) |
| **OS Integration** | ctypes — Windows sleep/display inhibit during automation |
| **Logging** | Python `logging` module — file + console + GUI handlers |
| **Timezone** | `zoneinfo` / `pytz` — US & Canada state → timezone mapping |
| **Screenshots** | Selenium `save_screenshot` on element-find failure |

---

## 🚀 Tools & Features

### 1. ART Q Assigner (`src/ui/main_window.py`)
A **multi-panel PyQt5 dashboard** for processing raw CRM export files into day-sheets:

- **Inputs:** Raw CRM export Excel, previous day's output, SMS replies file, email replies file
- **Processing pipeline (`FileProcessor`):**
  - Validates and normalizes 40+ CRM columns with fuzzy column-name matching
  - Filters out cancelled, CID, DMR, and escalation cases
  - Processes and parses SMS reply codes (`1` = Issue Resolved, `2` = Need Assistance, `3` = Stop)
  - Detects DND (Do Not Disturb) contacts and updates status
  - Computes customer local time using state → timezone mapping
  - Assigns cases to handlers (agents) and writes per-handler sheets
  - Generates an "Issue Not Fixed" sheet for cases needing follow-up
  - Preserves case history from previous files
- **Output:** Multi-sheet Excel workbook with one sheet per handler (`handler's Cases`)

---

### 2. ART Q Control — Mode: Auto Sender (`AutoSender_v2.py`)
**Processes NEW cases** that have never been contacted:

- Reads today's daily sheet Excel (e.g., `Active Cases PA MM-DD.xlsx`)
- Creates a date-stamped cache file (`working_cases_{agent}_autosender_{MMDD}.xlsx`)
- For each new case in the queue:
  1. Opens the case in Dynamics 365 CRM
  2. Checks if status is `Solution Provided` (skips if not)
  3. Detects e-ticketing cases and auto-fills Case Reason / Contact Reason fields
  4. Extracts serial number and customer name from CRM
  5. Sends **SMS** via CRM (personalized with customer name and case number)
  6. Sends **Email** via CRM (template selected based on Work Order Type: OnSite/Depot or CRU)
  7. Adds a **Case Note** to CRM (date, agent name, action taken)
  8. Marks case as `completed` in cache
- **Cache resume:** Detects unfinished sessions and asks to resume or start fresh
- **Progress monitor:** Live UI showing completed/remaining/skipped counts
- **Pause/Resume/Abort** controls during processing

---

### 3. ART Q Control — Mode: Case Reviewer (`CaseReviewer_v2.py`)
**Reviews IN-PROGRESS cases** that were previously contacted:

- Uses the **SIP dialer** (`perform_call_flow`) to place calls through Dynamics
- Case-by-case review dialog (`CaseReviewerDialog`) with:
  - **Closing code selection** organized by outcome category
  - **Navigation** (Previous / Next / Skip)
  - **DND** (Do Not Disturb) marking
  - **"Issue Not Fixed"** flag option
  - Add case note checkbox
- Supports **"Support Agent" mode** — process on behalf of another agent (dynamic sheet name)
- Seamlessly switches between CRM and Dialer browser windows

---

### 4. ART Q Control — Mode: Companies Process (`CompaniesProcess_v2.py`)
**Batch-processes cases grouped by company email:**

- Groups cases by company email from the cache Excel sheet
- For each company group:
  1. Opens each case in CRM to check status (`Solution Provided` or `Closed`)
  2. Shows a `PerCaseOutcomesDialog` for agent to set per-case results
  3. Navigates back to each case and applies the selected closing code and notes
  4. Saves each case
- Can run **standalone** (from Dispatcher menu) or **automatically** after Auto Sender completes

---

### 5. Excel Merger (`src/Merger/Merger.py`)
A **tkinter-based multi-step wizard** for merging multiple Excel files:

1. Select multiple `.xlsx` / `.xls` files
2. Choose which sheets to merge (filterable search)
3. Configure column mapping (add/remove/combine columns)
4. Preview output data before saving
5. Export merged result to a new Excel file

---

### 6. Excel Archiver (`src/Archiver/Archiver.py`)
A **tkinter-based tool** for managing large Excel workbooks over time:

- Analyzes all handler sheets and extracts date information
- **Export by month:** Extract all cases from a selected month into a new file (with optional cleanup from source)
- **Export old cases:** Extract cases older than N days (configurable threshold)
- Both modes support merging all handlers into a single sheet in the output
- Background threading — UI stays responsive during export

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

Config is validated on every startup. Missing or invalid fields abort execution. First-time setup shows a `ConfigSetupDialog` (PyQt5 form with file pickers).

---

## 🎨 UI System

- **Theme Manager:** Light, Dark, and Auto (detects Windows dark mode setting) with IBM Carbon Design color palette (`#0f62fe` primary blue)
- **Font Size:** Configurable slider (15–30px range), persisted to `config.json`, applies live to all open dialogs
- **Accessibility:** Keyboard navigation support, screen reader hints, keyboard locker (blocks stray keypresses during CRM automation)
- **Settings dialog:** Accessible from Dispatcher mode selector (gear icon)
- **Loading spinner:** Animated spinner component used during async operations
- **Progress monitor:** Real-time widget showing case counts with pause/resume

---

## ✅ What Is Working

| Feature | Status |
|---|---|
| ART Q Assigner (Excel pipeline) | ✅ Working |
| Auto Sender — SMS sending | ✅ Working |
| Auto Sender — Email sending (OnSite/Depot & CRU templates) | ✅ Working |
| Auto Sender — Case note insertion | ✅ Working |
| Auto Sender — E-ticket detection + field auto-fill | ✅ Working |
| Auto Sender — Solution Provided check before processing | ✅ Working |
| Auto Sender — Cache resume (`RESUME` / `NEW` dialog) | ✅ Working |
| Auto Sender — Progress monitor with pause/abort | ✅ Working |
| Case Reviewer — Full call flow via dialer | ✅ Working |
| Case Reviewer — Closing code dialog (all categories) | ✅ Working |
| Case Reviewer — DND marking | ✅ Working |
| Case Reviewer — Case notes | ✅ Working |
| Case Reviewer — Cache resume | ✅ Working |
| Companies Process — Grouped batch processing | ✅ Working |
| Companies Process — Per-case outcomes dialog | ✅ Working |
| Companies Process — Standalone mode | ✅ Working |
| Excel Merger — Multi-file, multi-sheet merging | ✅ Working |
| Archiver — Export by month | ✅ Working |
| Archiver — Export old cases (age threshold) | ✅ Working |
| Theme Manager — Light / Dark / Auto | ✅ Working |
| Settings dialog — Theme + font size + accessibility | ✅ Working |
| Config setup dialog (first-time + update) | ✅ Working |
| Windows sleep inhibit during automation | ✅ Working |
| Chrome driver keep-alive (auto refresh) | ✅ Working |
| Error screenshots on element-find failure | ✅ Working |

---

## ⚠️ What Is Not Working / Known Issues

| Feature | Status |
|---|---|
| `Main.py` (legacy V1) | ⚠️ Not actively used — replaced by `Dispatcher_v2.py` |
| `Functions.py` (legacy) | ⚠️ Uses **PyQt6** while the rest of the project uses **PyQt5** — import conflicts possible if mixed |
| `Main_BackUp_eticket_VoiceMail_II.py` | ⚠️ Prototype/backup script — not integrated into the launcher |
| PowerBI Dashboard button (Main Menu) | ❌ Placeholder only — not implemented |
| Email Archiver button (Main Menu legacy) | ❌ Placeholder — now replaced by Archiver tool |
| Voicemail injection / VB-Audio playback | ❌ Known issue — audio routing to CABLE Input device for Genesys fails in some configurations |
| `config_manager.py` (legacy tkinter config UI) | ⚠️ Superseded by `config_loader.py` (PyQt5) — both exist |
| Support agent mode in Case Reviewer is functional but not fully tested | ⚠️ Partial |

---

## 🔮 Planned / Future Additions

| Feature | Notes |
|---|---|
| **PowerBI Dashboard integration** | Placeholder button exists in `MainMenu` — to show live case metrics |
| **Voicemail playback via dialer** | Audio injection into CABLE Input device — partially explored, blocked by routing issue |
| **Automated report generation** | Export daily summary of what was sent/reviewed |
| **Multi-agent support** | Run automation on behalf of multiple agents in one session |
| **Unified cache viewer** | UI to inspect and edit cache files directly |
| **Scheduled startup** | Auto-launch at configured `start_time` without manual trigger |
| **Notifications** | Desktop toast notifications on completion or errors |
| **"Issue Not Fixed" auto-callback** | Auto-trigger Case Reviewer for cases flagged from SMS/email replies |
| **Full PyQt5 migration** | Migrate `Functions.py` (PyQt6) and `config_manager.py` (tkinter) to PyQt5 for consistency |
| **Archiver integration into main menu** | Currently launched via command-line argument only; needs a proper main menu button |
| **Merger integration into main menu** | Same as above |

---

## 🏃 How to Run

```bash
# From project root, launch main menu
python src/main.py

# Launch a specific tool directly
python src/main.py merger
python src/main.py archiver
python src/main.py qcontrol
```

On first run, if `config.json` is missing or incomplete, a setup dialog appears to collect agent credentials and file paths.

---

## 📋 Key Files Reference

| File | Purpose |
|---|---|
| `src/main.py` | Application entry point |
| `src/ART Q Control/Dispatcher_v2.py` | ART Q Control launcher (mode selector) |
| `src/ART Q Control/SharedFunctions.py` | All shared CRM automation functions |
| `src/ART Q Control/AutoSender_v2.py` | Auto Sender mode (new cases) |
| `src/ART Q Control/CaseReviewer_v2.py` | Case Reviewer mode (in-progress cases) |
| `src/ART Q Control/CompaniesProcess_v2.py` | Company batch processing mode |
| `src/ART Q Control/config_loader.py` | Config file manager + validation + UI |
| `src/ui/main_window.py` | ART Q Assigner Excel processing UI |
| `src/ui/theme_manager.py` | Dark/Light/Auto theme system |
| `src/file_processing/processor.py` | Core Excel pipeline (FileProcessor) |
| `src/Merger/Merger.py` | Excel file merger wizard |
| `src/Archiver/Archiver.py` | Excel workbook archiver |
| `config.json` | User / agent configuration |
