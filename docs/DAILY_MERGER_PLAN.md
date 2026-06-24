# Daily Sheet Merger — Implementation Plan

## Top-Level Overview

Build a new standalone tool called **"Daily Case Merger"** that processes up to 30 daily
Excel workbooks (`Active Cases PA MM-DD.xlsx`), extracts specific sheets from each day,
deduplicates rows by case number (latest day wins globally), and exports a single output
workbook containing three merged sheets:

- **All Cases** — all handler `XXXX's Cases` sheets combined
- **Chat Agent's Cases** — all Chat Agent rows combined
- **Companies** — all Companies rows combined

The tool is a new card in the main menu, parallel to Archiver and Merger.

### Key Data Conventions
- **Filename format**: `Active Cases PA MM-DD.xlsx` — date is embedded as `MM-DD`
- **Header row**: Row 1 in every sheet
- **Data starts**: Row 2 onwards
- **Case number column**: Column A (index 0) for all handler + Companies sheets; Column L (index 11) for Chat Agent's Cases
- **Headers are identical** across all files for the same sheet type — column matching by header name is reliable
- **Month grouping**: The tool validates and groups files by month; the confirmation step reports how many daily files were found within the loaded month

---

## Architecture Decision

Follow the existing **3-tier pattern** used by Archiver and Merger:

| Layer | New File | Responsibility |
|---|---|---|
| Service | `DailyMerger/daily_merger_service.py` | All Excel I/O, deduplication logic, progress reporting |
| Window | `DailyMerger/daily_merger_window.py` | PyQt5 UI, QThread worker |
| Components | `DailyMerger/components/` | File list, summary view |
| Registry | `utils/tool_registry.py` | Tool card registration |
| Launcher | `utils/tool_launcher.py` | Window instantiation |

---

## Sub-Tasks

---

### Sub-Task 1 — Service Layer: `DailyMergerService`

**Intent**  
Implement all business logic for loading, validating, sorting, extracting, and
deduplicating daily Excel workbooks, completely decoupled from any UI.

**Expected Outcomes**
- A service class that can be driven entirely from tests or the UI
- Returns structured validation info (sheet counts per type per day)
- Runs deduplication correctly: case number column A for handler+companies sheets,
  column L for Chat Agent's Cases; latest day (by file date) wins globally
- Produces a single output workbook with three sheets

**Todo List**
1. Create `src_v2/DailyMerger/` directory with `__init__.py`
2. Create `src_v2/DailyMerger/daily_merger_service.py`
3. Define dataclasses:
   - `DailyFile` — path, date extracted from filename (`MM-DD`), list of sheet names found
   - `ValidationResult` — total files, dates found, handler names, missing sheet warnings
   - `MergeConfig` — list of file paths, output path
   - `MergeResult` — success bool, message, stats dict
4. Implement `DailyMergerService` class:
   - `validate_files(paths: List[Path]) -> ValidationResult`
     - Parse date from filename (`Active Cases PA MM-DD.xlsx` → `MM-DD`)
     - Sort files chronologically by `MM-DD`
     - Scan each workbook's sheet names (without fully loading data)
     - Identify: handler sheets (`*'s Cases` not "Chat Agent's Cases"), Chat Agent sheet, Companies sheet
     - Report detected handler names (union across all files)
     - Group files by month — report count per month for the confirmation step
     - Warn about missing sheets in specific days
   - `merge(config: MergeConfig, progress_callback) -> MergeResult`
     - Process files in chronological order (ascending date = oldest first)
     - For each file, in order: handler sheets → Chat Agent's Cases → Companies
     - Maintain three in-memory dicts keyed by case number:
       - `all_cases_map: Dict[str, row_data]` — key = column A value (row 2+)
       - `chat_map: Dict[str, row_data]` — key = column L value (row 2+)
       - `companies_map: Dict[str, row_data]` — key = column A value (row 2+)
     - **Row 1 = header row** — capture once per sheet type from the first file encountered;
       skip row 1 when reading data (data starts row 2)
     - For each data row: upsert into map (later day overwrites earlier)
     - Use header names (row 1) for column matching when writing output — ensures correct
       column alignment even if column order differs across files (it won't, but defensive)
     - After all files processed: write output workbook with openpyxl
       - Sheet 1: "All Cases" — row 1 headers + all_cases_map values
       - Sheet 2: "Chat Agent's Cases" — row 1 headers + chat_map values
       - Sheet 3: "Companies" — row 1 headers + companies_map values
     - Copy cell styles from source cells to output
     - Report progress via callback: file load %, sheet extraction %, writing %

**Relevant Context**
- `src_v2/Archiver/archiver_service.py` — reference for openpyxl patterns, backup creation, date parsing, cell style copying
- `src_v2/Merger/merger_service.py` — reference for pandas read patterns and merge stats
- Progress callback signature: `(percent: int, message: str) -> None`
- Header is always row 1; data starts row 2
- Case number key values begin at row 2

**Status** — `[x] done`

---

### Sub-Task 2 — UI Components: File List + Summary View

**Intent**  
Build the two custom PyQt5 widgets needed by the window:
`DailyFileListWidget` (load and reorder files) and `DailySummaryWidget`
(post-validation summary and merge trigger).

**Expected Outcomes**
- `DailyFileListWidget`: drag-drop multi-file selector, shows file count,
  detected date range, and a "Confirm (N files)" label matching the UX requirement
  of confirming total sheets before merging
- `DailySummaryWidget`: displays validation result table (per-day sheet counts,
  warnings for missing sheets), output path picker, "Merge" button

**Todo List**
1. Create `src_v2/DailyMerger/components/__init__.py`
2. Create `src_v2/DailyMerger/components/daily_file_list.py`
   - Subclass `QWidget`
   - Signal: `files_changed(list)` emitted when file list changes
   - Drag-drop area that accepts `.xlsx` files (multiple at once)
   - Browse button (multi-select file dialog)
   - File list display: filename, extracted date, detected sheet count
   - Remove individual files button per row
   - Clear all button
   - Shows "N files loaded | Date range: MM-DD → MM-DD" summary label
   - Theme-aware styling via design tokens
3. Create `src_v2/DailyMerger/components/daily_summary.py`
   - Signal: `merge_requested(config: dict)` emitted on "Merge" click
   - Displays `ValidationResult` in a table:
     - Columns: Date | Handler Sheets Found | Chat Agent | Companies | Warnings
   - Output file path picker (defaults to same folder as first input file)
   - "Merge N Files" primary button (disabled until validation passes)
   - Warning banner if any day is missing expected sheets

**Relevant Context**
- `src_v2/Archiver/components/file_selector.py` — reference for drag-drop pattern
- `src_v2/Archiver/components/analysis_view.py` — reference for stat display
- `src_v2/ui/components_v2/` — buttons, tables, inputs to reuse
- `src_v2/ui/design_system.py` — Spacing, Colors, BorderRadius tokens

**Status** — `[x] done`

---

### Sub-Task 3 — Window: `DailyMergerWindow`

**Intent**  
Build the main PyQt5 window that wires the service, components, and
a background QThread worker together into a complete user workflow:
load files → validate → review summary → merge → done.

**Expected Outcomes**
- Full window following the same patterns as `ArchiverWindow` and `MergerWindow`
- Worker thread prevents UI freeze during merge (up to 30 files × multiple sheets)
- Progress dialog with live percent + status message
- Success/error messaging via status bar and modal
- Keyboard shortcuts registered via `ShortcutManager`
- Theme-aware (light/dark)
- Typography mixin applied

**Todo List**
1. Create `src_v2/DailyMerger/daily_merger_window.py`
2. Define `DailyMergeWorker(QThread)`:
   - Signals: `progress(int, str)`, `finished(bool, str, dict)`
   - Runs `service.merge(config, callback)` in background thread
3. Define `DailyMergerWindow(QMainWindow, V2TypographyMixin)`:
   - Two-panel layout:
     - Left/top: `DailyFileListWidget`
     - Right/bottom: `DailySummaryWidget` (shown after validation)
   - Flow: files loaded → auto-validate → show summary → user picks output → merge
   - Validation runs on main thread (fast — only reads sheet names, not data)
   - Merge runs on worker thread
   - Menu bar: File (Open Files, Clear, Close), Help (About)
   - Status bar: last action message
   - Keyboard shortcuts:
     - `Ctrl+O` — Open files
     - `Ctrl+Return` — Validate / confirm
     - `Ctrl+M` — Start merge
     - `Ctrl+W` — Close window
4. Wire signals: `file_list.files_changed` → call validate → update summary widget
5. Wire signals: `summary.merge_requested` → start worker thread → show progress dialog
6. Handle worker `finished` signal: close progress dialog, show result message, open output folder option

**Relevant Context**
- `src_v2/Archiver/archiver_window.py` — reference for window structure, worker pattern, shortcuts
- `src_v2/ui/components_v2/dialogs.py` — `ProgressDialog` to reuse
- `src_v2/ui/typography_mixin.py` — `V2TypographyMixin`
- `src_v2/ui/services.py` — `V2SettingsBus` for theme/font subscription

**Status** — `[x] done`

---

### Sub-Task 4 — Registration: Tool Registry + Launcher

**Intent**  
Register the new tool in the main menu and wire the launcher so clicking
the card opens `DailyMergerWindow`.

**Expected Outcomes**
- A new "Daily Case Merger" card appears in the main menu alongside Archiver and Merger
- Clicking it opens `DailyMergerWindow`
- No regressions to existing tools

**Todo List**
1. Add `ToolDefinition` entry in `src_v2/utils/tool_registry.py`:
   ```
   tool_id="daily_merger"
   display_name="Daily Case Merger"
   description="Merge 30 daily Active Cases workbooks into one deduplicated output"
   area="Operations"
   icon="📅"
   status="active"
   ```
2. Add launch case in `src_v2/utils/tool_launcher.py`:
   - Import `DailyMergerWindow` from `DailyMerger.daily_merger_window`
   - Instantiate and show window when `tool_id == "daily_merger"`
3. Add `DailyMerger/__init__.py` export if needed for the import to resolve

**Relevant Context**
- `src_v2/utils/tool_registry.py` — existing `ToolDefinition` entries for "archiver", "merger"
- `src_v2/utils/tool_launcher.py` — existing launch switch/cases pattern

**Status** — `[x] done`

---

### Sub-Task 5 — Recent Files Tracking

**Intent**  
Persist recently used output folders and input file sets so the user
does not need to re-select 30 files every time.

**Expected Outcomes**
- Recent output folders shown in output path picker as a dropdown
- Last-used file folder remembered for the file browse dialog

**Todo List**
1. Create `src_v2/utils/recent_daily_merger_files.py`
   - Mirror pattern of `recent_archiver_files.py`
   - Stores last 5 used output folder paths
   - Singleton + thread-safe Lock
   - Persists to `~/.art_q_master/recent_daily_merger.json`
2. Integrate into `DailyFileListWidget`: remember last browse directory
3. Integrate into `DailySummaryWidget`: populate output folder dropdown from recent list

**Relevant Context**
- `src_v2/utils/recent_archiver_files.py` — exact pattern to mirror
- `src_v2/utils/recent_merger_files.py` — alternate reference

**Status** — `[x] done`

---

## Processing Flow Diagram (described in text)

Files are sorted chronologically by date extracted from filename.
Processing order per file: ALL handler sheets first, then Chat Agent's Cases, then Companies.
For each row in each sheet, the case number key is looked up in the global map.
If the key is absent → insert. If present → overwrite (later day wins).
After all 30 files are processed, write the three maps to the output workbook.

```
Day 1 → Day 2 → ... → Day 30
  ↓ each day:
  handler sheets (alphabetical) → Chat Agent's Cases → Companies
  ↓ each row:
  upsert into map[case_number] = row_data   ← later day always wins
```

---

## Key Design Decisions

| Decision | Choice | Reason |
|---|---|---|
| Case number column for handler sheets | Column A (index 0) | Per requirements |
| Case number column for Chat Agent | Column L (index 11) | Per requirements |
| Case number column for Companies | Column A (index 0) | Per requirements |
| Header row | Row 1 in all sheets | Per requirements |
| Data start row | Row 2 | Follows from header at row 1 |
| Header matching | By column name (row 1 values) | Headers identical across files — safe and defensive |
| Deduplication scope | Global across all handlers and days | Per requirements |
| Output sheet names | "All Cases", "Chat Agent's Cases", "Companies" | Clean and descriptive |
| Header source | Row 1 from first file encountered with that sheet type | Consistent headers |
| Processing order | Chronological ascending (oldest first, newest last) | Newest day wins via upsert |
| Month grouping | Files grouped by month in validation step | Confirms N daily sheets found in same month |
| Excel library | openpyxl (consistent with Archiver) | Already in project dependencies |
| Background processing | QThread worker (consistent with Archiver/Merger) | Prevents UI freeze |

---

## Files to Create

```
src_v2/DailyMerger/
├── __init__.py
├── daily_merger_service.py
├── daily_merger_window.py
└── components/
    ├── __init__.py
    ├── daily_file_list.py
    └── daily_summary.py

src_v2/utils/
└── recent_daily_merger_files.py    (new)

Modified:
src_v2/utils/tool_registry.py       (add ToolDefinition)
src_v2/utils/tool_launcher.py       (add launch case)
```
