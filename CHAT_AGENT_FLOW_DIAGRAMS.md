# Chat Agent Implementation - Process Flow Diagrams

## 1. Chat Agent Initialization Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      MainWindow (UI)                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ├─── Chat Agent Checkbox
                            │    (toggle visibility)
                            │
                            ├─── Supporter Name Input
                            │    (enter name when enabled)
                            │
                            └─── Process Button Clicked
                                        │
                                        ▼
                    ┌───────────────────────────────┐
                    │  get_chat_agent_info()        │
                    │                               │
                    │  If Checkbox Checked:         │
                    │  - Get supporter name         │
                    │  - Return enabled=True        │
                    │  Else:                        │
                    │  - Return None                │
                    └───────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────────────┐
                    │  FileProcessingWorker         │
                    │  chat_agent_info=<dict>       │
                    └───────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────────────┐
                    │  process_files()              │
                    │  chat_agent_info passed       │
                    └───────────────────────────────┘
```

---

## 2. Fair Share Calculation Flow

```
┌─────────────────────────────────────────────────────────────┐
│         calculate_fair_share(df, handlers, chat_agent_info)  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
    Count          Identify Status      Count Handlers
    In-Progress      Columns              in List
    Cases Only
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌─────────────────────┐
                    │ Calculate:          │
                    │ fair_share =        │
                    │ total_in_progress / │
                    │ total_handlers      │
                    └─────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
            Chat Agent Enabled?    No
                  │
                  │ Yes
                  ▼
            ┌────────────────────────┐
            │ Calculate Chat Agent:  │
            │ capacity =             │
            │ ceil(fair_share × 1.15)│
            │                        │
            │ Increment handlers: +1 │
            └────────────────────────┘
                    │
                    ▼
            ┌──────────────────────────┐
            │  Return fair_share_info  │
            │  {                       │
            │    total_cases: XXX,     │
            │    fair_share: XX.XX,    │
            │    chat_agent_capacity:  │
            │      XX,                 │
            │    handler_list: [...]   │
            │  }                       │
            └──────────────────────────┘
```

---

## 3. Case Redistribution Flow

```
┌──────────────────────────────────────────────────────────────────┐
│  redistribute_cases_to_chat_agent(df, chat_agent_info, name)     │
└──────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │ Step 1: Count Current   │
                │                         │
                │ Chat Agent status =     │
                │ "Assigned To" == name   │
                │ Filter by in_progress   │
                │ current_queue = count   │
                └─────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │ Step 2: Calculate Needs │
                │                         │
                │ cases_needed =          │
                │ target_capacity -       │
                │ current_queue           │
                │                         │
                │ If <= 0: Return (done)  │
                └─────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │ Step 3: Find Eligible Handlers        │
        │                                       │
        │ For each handler:                     │
        │ - Count in_progress cases            │
        │ - Is queue > fair_share?             │
        │ - If yes → Eligible                  │
        │ - Calculate excess workload          │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │ Step 4: Sort Eligible Handlers        │
        │                                       │
        │ By: excess workload (descending)     │
        │ (highest excess first)               │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │ Step 5: Pull Cases (Loop)             │
        │                                       │
        │ For each eligible handler:            │
        │ ├─ Get in_progress indices           │
        │ ├─ Pull from BOTTOM (oldest first)   │
        │ ├─ cases_to_pull = min(                
        │ │    cases_needed,                    │
        │ │    excess_available                 │
        │ │  )                                  │
        │ ├─ Update "Assigned To" to Chat Agent│
        │ ├─ cases_needed -= cases_to_pull     │
        │ └─ If cases_needed <= 0: Break       │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │ Step 6: Verify Results                │
        │                                       │
        │ Count final Chat Agent in_progress   │
        │ Confirm >= target_capacity            │
        │ Log verification message              │
        └───────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────────┐
                    │  Return Updated  │
                    │  DataFrame       │
                    │ (Assigned To col │
                    │  modified only)  │
                    └──────────────────┘
```

---

## 4. Complete process_files() Flow with Chat Agent

```
START: process_files(files, handlers, chat_agent_info)
    │
    ├─ Load Files
    │  ├─ Raw file (main data)
    │  ├─ Previous file (if exists)
    │  └─ SMS/Email files (if exist)
    │
    ├─ Apply Filters
    │  ├─ Work Order Status filter
    │  ├─ Case Reason filter
    │  ├─ Closing Code filter
    │  ├─ CID/DMR filter
    │  └─ Duplicate removal (sort by date, keep newest)
    │
    ├─ Assign Handlers (NEW CASES ONLY)
    │  ├─ Identify new cases (not in previous file)
    │  ├─ Group by company
    │  ├─ Assign multi-case companies to handlers
    │  └─ Assign single cases to handlers (fair distribution)
    │
    ├─ Calculate Fair Share ─────────────────┬──────────────┐
    │  ├─ Count IN_PROGRESS cases only       │              │
    │  ├─ fair_share = total / handlers      │              │
    │  └─ If Chat Agent enabled:             │              │
    │      └─ capacity = ceil(fair_share×1.15)             NEW
    │
    ├─ Redistribute to Chat Agent (IF ENABLED) ───────────┴──┐
    │  ├─ Count current Chat Agent in_progress              NEW
    │  ├─ Identify eligible handlers (queue > fair_share)    │
    │  ├─ Sort by excess workload                            │
    │  ├─ Pull oldest in_progress cases                      │
    │  └─ Reassign to Chat Agent until capacity reached      │
    │                                                          │
    ├─ Process Email/SMS Replies (if files exist)
    │  ├─ Load SMS/Email file
    │  ├─ Match cases to handler sheets
    │  └─ Update Final Action & Status
    │
    ├─ Create Output Sheets
    │  ├─ PA Cases sheet (main)
    │  ├─ Handler sheets (one per selected handler)
    │  ├─ Chat Agent's Cases sheet (IF ENABLED) ───────── NEW
    │  │  ├─ Get current Chat Agent cases
    │  │  ├─ Load previous Chat Agent cases
    │  │  ├─ Merge (current + preserved)
    │  │  └─ Write to "Chat Agent's Cases"
    │  ├─ Issue Not Fixed sheet
    │  ├─ DND Emails sheet
    │  └─ Companies sheet
    │
    ├─ Verify Persistence (IF ENABLED) ─── NEW
    │  ├─ Count current Chat Agent in_progress
    │  ├─ Load previous Chat Agent in_progress
    │  └─ Confirm persistence: current >= previous
    │
    └─ END: Output Excel file with all sheets
```

---

## 5. Chat Agent Cases - Selection Criteria

```
┌──────────────────────────────────────────────────────────────┐
│          Which Cases Get Reassigned to Chat Agent?           │
└──────────────────────────────────────────────────────────────┘

Selection Criteria (ALL must be true):
    │
    ├─ Status is "in_progress" 
    │  (Regex: r'in[_\s.]?progress')
    │
    ├─ Currently assigned to handler
    │
    ├─ Handler is eligible:
    │  (queue_size > fair_share)
    │
    ├─ Chat Agent has capacity:
    │  (cases_needed > 0)
    │
    └─ Case Order:
       (Pull from BOTTOM of handler queue = oldest first - FIFO)

┌──────────────────────────────────────────────────────────────┐
│              Eligibility by Handler Status                    │
└──────────────────────────────────────────────────────────────┘

Handler Queue Size    Fair Share    Eligible?    Can Contribute?
─────────────────────────────────────────────────────────────
    20                  20            No           0 cases
    22                  20            Yes          2 cases
    25                  20            Yes          5 cases
    30                  20            Yes          10 cases (but pull only as needed)

Example: If Chat Agent needs 8 cases:
- Pull 5 from handler with 25 (excess=5)
- Pull 3 from handler with 22 (excess=2, partially)
- Chat Agent now has: capacity met
```

---

## 6. Sheet Preservation Flow

```
┌────────────────────────────────────────────────────────────┐
│     Loading Previous "Chat Agent's Cases" Sheet             │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │ Check prev_file exists  │
                └─────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
                    No              Yes
                    │               │
                    │               ▼
                    │       ┌──────────────────────┐
                    │       │ Read Excel file      │
                    │       │ (list all sheets)    │
                    │       └──────────────────────┘
                    │               │
                    │               ▼
                    │       ┌──────────────────────────┐
                    │       │ Find "Chat Agent's Cases"│
                    │       │ sheet in sheet_names     │
                    │       └──────────────────────────┘
                    │               │
                    │        ┌──────┴──────┐
                    │        │             │
                    │      Found        Not Found
                    │        │             │
                    │        ▼             ▼
                    │     Load        prev_chat_cases
                    │     Cases       = DataFrame()
                    │        │
                    │        ▼
                    │     prev_chat_cases
                    │     = read_excel(
                    │         sheet_name)
                    │        │
                    └────────┼─────────────┐
                            │             │
                            ▼             ▼
        ┌─────────────────────────────────────────┐
        │ Normalize case numbers in both:         │
        │ - current_chat_cases                    │
        │ - prev_chat_cases                       │
        │ (Convert to Int64 for comparison)       │
        └─────────────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────┐
        │ Find cases in previous but not current: │
        │                                         │
        │ current_case_nums = set(               │
        │   current['Case Number'].dropna()       │
        │ )                                       │
        │                                         │
        │ previously_preserved = prev[           │
        │   ~prev['Case Number'].isin(            │
        │     current_case_nums                   │
        │   )                                     │
        │ ]                                       │
        └─────────────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────┐
        │ Merge:                                  │
        │ chat_agent_cases = pd.concat([          │
        │   current_chat_cases,    (first)        │
        │   previously_preserved   (second)       │
        │ ])                                      │
        │                                         │
        │ Order: Current cases first, then        │
        │        preserved cases (no duplicates)  │
        └─────────────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────┐
        │ Sort by Status                          │
        │ (using sort_cases_by_status method)     │
        └─────────────────────────────────────────┘
                            │
                            ▼
        ┌─────────────────────────────────────────┐
        │ Write to Excel                          │
        │ - Sheet name: "Chat Agent's Cases"      │
        │ - All output columns preserved          │
        │ - Auto-adjusted columns                 │
        │ - Password protected: 'artadmin'        │
        └─────────────────────────────────────────┘
```

---

## 7. Data Flow Summary

```
Input Sources:
    │
    ├─ MainWindow: chat_agent_info
    │  └─ {'enabled': bool, 'supporter_name': str}
    │
    ├─ Raw Excel File: Case data
    │  └─ 100+ cases with all details
    │
    ├─ Previous Excel File (optional): Handler sheets
    │  └─ "Chat Agent's Cases" sheet (if exists)
    │
    └─ Config: selected_handlers list
       └─ ["Adam", "Ehab", ..., Chat Agent]

Data Transformations:
    │
    ├─ Filter Cases: 100 → 80 (remove invalid)
    │  └─ Apply work order status, reason, code filters
    │
    ├─ Assign Handlers: 80 → distributed
    │  └─ Preserve old, assign new fairly
    │
    ├─ Calculate Fair Share: 80 → fair_share metric
    │  └─ In-progress only: 60 → fair_share = 12/handler
    │
    ├─ Redistribute to Chat Agent: Qualified cases → Chat Agent
    │  └─ Pull from eligible handlers to reach 115% capacity
    │
    └─ Create Chat Agent Sheet: Merge current + preserved
       └─ Write to "Chat Agent's Cases" sheet

Output:
    │
    ├─ Excel Workbook
    │  ├─ PA Cases (main)
    │  ├─ Adam's Cases
    │  ├─ Ehab's Cases
    │  ├─ Chat Agent's Cases ◄─── (IF ENABLED)
    │  ├─ Issue Not Fixed
    │  ├─ DND Emails
    │  └─ Companies
    │
    └─ Processing Stats & Logs
       ├─ Fair share info
       ├─ Redistribution results
       ├─ Persistence verification
       └─ Completion messages
```

---

## 8. Status Pattern Matching

```
┌────────────────────────────────────────────────────────────┐
│    In-Progress Status Pattern Detection                     │
└────────────────────────────────────────────────────────────┘

Regex Pattern Used: r'in[_\s.]?progress'

Matches These Variations:
✓ "in_progress"      (underscore)
✓ "in progress"      (space)
✓ "in.progress"      (dot)
✓ "inprogress"       (no separator)
✓ "IN_PROGRESS"      (case insensitive)
✓ "In Progress"      (case insensitive)
✓ "IN PROGRESS"      (case insensitive)

Does NOT Match:
✗ "in-progress"      (hyphen - not matching)
✗ "progress"         (partial only)
✗ "in_progress_today" (only matches "in_progress" part)
✗ "closed"
✗ "completed"
✗ "pending"

Application:
    DataFrame[status_col].astype(str)
        .str.lower()
        .str.contains(r'in[_\s.]?progress', regex=True, na=False)
```

---

## 9. Error Handling Flow

```
┌────────────────────────────────────────────────────────────┐
│          Exception Handling in Chat Agent Methods           │
└────────────────────────────────────────────────────────────┘

Method Call
    │
    ▼
try:
    ├─ Execute method logic
    │  └─ Validate inputs
    │  └─ Perform calculations
    │  └─ Update data
    │  └─ Log results
    │
    └─ If all succeeds:
       └─ Return result dict/dataframe
    
except Exception as e:
    │
    ├─ Log errors
    │  ├─ self.logger.error(f"Error in {method}: {str(e)}")
    │  └─ traceback.format_exc()
    │
    └─ Return safe default
       ├─ Alternative: Empty dict with 'error' key
       ├─ Alternative: Original DataFrame unchanged
       └─ Alternative: Zero/False values

Example Safe Returns:
    {
        'can_receive': False,
        'current_queue': 0,
        'capacity': 0,
        'error': str(e)
    }
```

---

## 10. Configuration Summary

```
Chat Agent Feature Configuration:
    │
    ├─ UI Control
    │  ├─ Checkbox: Enable/disable Chat Agent
    │  └─ Text Input: Supporter name (when enabled)
    │
    ├─ Constants
    │  ├─ Capacity Bonus: 115% of fair share (15% extra)
    │  ├─ Sheet Name: "Chat Agent's Cases" (fixed)
    │  ├─ Password: "artadmin" (sheet protection)
    │  └─ Status Pattern: r'in[_\s.]?progress'
    │
    ├─ Data Structures
    │  ├─ chat_agent_info: {enabled, supporter_name}
    │  ├─ fair_share_info: {capacity, fair_share, ...}
    │  └─ Output columns: Same as other handler sheets
    │
    ├─ Processing Stage
    │  ├─ After: Handler assignment
    │  ├─ Before: Email/SMS processing
    │  └─ Timing: Between filters and final output
    │
    └─ Preservation Rules
       ├─ Load: Previous Chat Agent sheet if exists
       ├─ Merge: Current + Previous (no duplicates)
       ├─ Sort: By status
       └─ Write: To output workbook
```

This comprehensive flow ensures proper Chat Agent case selection, redistribution, and preservation across processing runs.
