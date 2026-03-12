# ART Q Assigner Tool - Complete Analysis

## Overview
The "Assigner Tool" is the main Excel case-assignment pipeline UI located at `src/ui/main_window.py`. It orchestrates file processing using two main processors:
1. **FileProcessor** (`src/file_processing/processor.py`) - Primary processing engine
2. **FinalProcessor** (`src/file_processing/final_processor.py`) - Secondary processor for final output formatting and additional sheets

---

## Architecture Flow

```
User Interface (MainWindow in src/ui/main_window.py)
    ↓
FileProcessingWorker (QThread) - handles async processing
    ↓
FileProcessor.process_files()
    ├── Read & validate raw file
    ├── Load previous file (optional)
    ├── Apply filters (Work Order Status, Case Reason, Closing Code, CID/DMR)
    ├── Remove duplicates
    ├── Format output data
    ├── Assign handlers (CRITICAL STEP)
    ├── Identify email duplicates for Companies sheet
    ├── Process DND database
    ├── Process SMS replies (if provided)
    ├── Process Email replies (if provided)
    │
    └── FinalProcessor.process_final_output()
        ├── Create Companies sheet (from email duplicates)
        ├── Create Handler individual sheets (preserve all handlers)
        ├── Create Counter sheet (progress tracking)
        ├── Create Summary sheet (statistics & validation)
        ├── Create Issue Not Fixed sheet
        └── Validate output data
```

---

## Step-by-Step Detailed Processing

### STEP 1: File Input & Validation (lines 939-970)
**In: `process_files()` - FileProcessor**

- Reads raw Excel file with `pd.read_excel(raw_file)`
- Cleans all string columns (strip, standardize)
- Normalizes ID columns
- Counts initial records

**Output:** 
- `df` - normalized DataFrame with `initial_count` records

---

### STEP 2: Load Previous File (lines 969-978)
**In: `process_files()` - FileProcessor**

- If `prev_file` exists, loads with `load_previous_file(prev_file)`
- Used later for:
  - Preserving previous handler assignments
  - Merging with current data
  - Tracking case updates

**Output:**
- `prev_df` - previous file DataFrame or None

---

### STEP 3: Apply Nested Filters (lines 982-1168)

#### Filter 3A: Work Order Status (lines 1002-1023)
- **Excluded statuses:** 
  - 'Cancelled'
  - 'Cancelled by lenovo'
- **Action:** Removes rows matching excluded statuses
- **Tracking:** Detailed logging of removed cases

#### Filter 3B: Case Reason (lines 1025-1047)
- **Excluded reasons:**
  - 'Escalation/Complaint'
- **Action:** Removes rows matching excluded case reasons

#### Filter 3C: Closing Code (lines 1049-1081)
- **Excluded codes:**
  - 'Customer Induced Damage'
  - 'Cancelled by Customer'
  - 'Cancelled by Lenovo'
  - 'Customer Not available'
  - 'Machine Not Found'
  - 'Returned but Un-repaired'

#### Filter 3D: CID/DMR Filter (lines 1083-1108)
- Calls `filter_case(df)` to identify and remove CID/DMR cases
- **Action:** Removes cases containing 'CID' or 'DMR' keywords

#### Filter 3E: Duplicate Removal (lines 1110-1168)
- **Process:**
  1. Normalizes Case Numbers to integer format
  2. Sorts by 'Created On' date (newest first)
  3. Removes duplicate Case Numbers (keeps first/newest)
  4. Drops temporary sorting column
- **Critical:** Prevents cases from being assigned to multiple handlers

**Output after all filters:** 
- `df` - filtered to `filtered_count` records
- `dropped_cases_details` - comprehensive tracking dictionary

---

### STEP 4: Calculate Previous File Statistics (lines 1170-1196)
**In: `process_files()` - FileProcessor**

If previous file exists, calculates:
- Initial Count - total cases in prev_df
- Matching Cases - cases appearing in both prev_df and current df
- New Cases - cases only in current df
- Updated Cases - cases in both but with field differences

**Output:**
- `prev_stats` - dictionary with matching/new/updated counts

---

### STEP 5: Format Output Data (line 1200)
**In: `process_files()` - FileProcessor**
**Method:** `format_output_data(df, prev_df)`

- Maps raw columns to output columns
- Merges with previous file data
- Maintains output column order

**Output:**
- `output_df` - properly formatted DataFrame ready for handler assignment

---

### STEP 6: ASSIGN HANDLERS (line 1203) ⭐ CRITICAL STEP
**In: `process_files()` - FileProcessor**
**Method:** `assign_handlers(output_df, selected_handlers, prev_df, prev_file)`

**Location:** Lines 2331-2596 in processor.py

#### Sub-Step 6.1: Validation Setup
- Cleans handler names (strips whitespace, title case)
- Validates selected_handlers list
- Creates empty 'Assigned To' column if missing

#### Sub-Step 6.2: Preserve Previous Assignments
- **Purpose:** Keep cases that already have handler assignments from prev_file
- **Process:**
  1. Loads prev_df and normalizes Case Numbers
  2. Creates mapping: `case_num → handler`
  3. Applies preserved assignments to current df
  4. **Critical:** These handlers are NOT counted in the "selected_handlers" distribution
  5. Logs preserved assignments separately

**Code Logic (lines 2363-2410):**
```python
# Build mapping from previous file
prev_case_to_handler = {}
prev_assignments = set()
for _, row in prev_df_local.dropna(subset=['Case Number']).iterrows():
    case_num = int(row['Case Number'])
    handler = self.clean_handler_name(row.get('Assigned To', ''))
    if handler:
        prev_case_to_handler[case_num] = handler
        prev_assignments.add(case_num)

# Apply preserved assignments
for case_num, handler in prev_case_to_handler.items():
    mask = df['Case Number'] == case_num
    if mask.any():
        idx = mask.idxmax()
        df.at[idx, 'Assigned To'] = handler
```

#### Sub-Step 6.3: Identify NEW Cases Needing Assignment
- **Definition:** Cases without an Assigned To value from previous file
- **Logic:**
  ```python
  new_cases_mask = (~df['Case Number'].isin(prev_assignments)) & \
                   ((df['Assigned To'].isna()) | (df['Assigned To'] == ''))
  new_case_numbers = df[new_cases_mask]['Case Number'].astype('Int64').tolist()
  ```

#### Sub-Step 6.4: Group New Cases by COMPANY (Company-group Assignment)
- **Purpose:** Keep all cases from same company assigned to same handler
- **Process (lines 2424-2520):**
  1. Gets Company Name column from dataframe
  2. For each NEW case, identifies company group
  3. Separates into three categories:
     - **Multi-case companies:** 2+ cases from same company
     - **Single-case companies:** 1 case from company
     - **No-company cases:** Empty/missing company field
  4. Prioritizes multi-case companies for fair distribution
  5. Sorts multi-case companies by size (largest first)
  
**Company Group Logic:**
```python
# Build company groups from new cases
company_groups = {}  # company → [case_numbers]
for _, row in new_cases.iterrows():
    company = row.get('Company Name', '').strip()
    if company and company != 'nan':
        if company not in company_groups:
            company_groups[company] = []
        company_groups[company].append(row['Case Number'])

# Separate into multi/single/no-company
multi_case_companies = {c: cases for c, cases in company_groups.items() if len(cases) > 1}
single_case_companies = {c: cases for c, cases in company_groups.items() if len(cases) == 1}
no_company_cases = [...]  # Cases without company
```

#### Sub-Step 6.5: Round-Robin Distribution (Company Groups + Single Cases)
- **Purpose:** Fairly distribute company groups across selected handlers
- **Process (lines 2481-2540):**
  1. **Phase 1:** Distribute multi-case company groups
     - Assigns entire company group to one handler
     - Cycles through selected_handlers
     - Moves to next handler for next company
  
  2. **Phase 2:** Distribute single-case & no-company cases
     - Assigns individual cases
     - Continues cycling from where Phase 1 left off
     - Fair distribution maintains momentum

**Round-Robin Logic:**
```python
handler_idx = 0

# Phase 1: Multi-case companies (get priority)
for company, case_nums in sorted(multi_case_companies.items()):  # Largest first
    handler = selected_handlers[handler_idx % len(selected_handlers)]
    # Assign ALL cases from this company to same handler
    for case_num in case_nums:
        df.loc[df['Case Number'] == case_num, 'Assigned To'] = handler
    handler_idx += 1

# Phase 2: Single cases continue cycling
for case_num in (single_case_companies.values() + no_company_cases):
    handler = selected_handlers[handler_idx % len(selected_handlers)]
    df.loc[df['Case Number'] == case_num, 'Assigned To'] = handler
    handler_idx += 1
```

#### Sub-Step 6.6: Final Deduplication Check
- Ensures no case appears multiple times
- Removes duplicates keeping last occurrence
- Logs any duplicates removed

#### Sub-Step 6.7: Validation & Distribution Summary (lines 2511-2596)
- Validates unselected handlers not assigned new cases
- Calculates final distribution:
  - Selected handlers workload (new cases only)
  - Preserved handlers workload (from previous file)
  - Total per handler workload
- Calculates fairness ratio: `min_cases / max_cases`
  - 1.0 = perfectly fair distribution
  - < 0.8 = warns about uneven distribution
- Logs comprehensive distribution report

**Output after assign_handlers:**
- `output_df` - all cases now have 'Assigned To' value

---

### STEP 7: Identify Email Duplicates for Companies Sheet (lines 1251-1253)
**In: `process_files()` - FileProcessor**
**Method:** `identify_email_duplicates_new_cases(output_df, prev_df, prev_file)`

- **Purpose:** Find cases with duplicate emails (same customer from multiple companies)
- **Result:** Creates `duplicate_company_cases` - list of case numbers that are email duplicates
- **Used for:** Creating separate "Companies" sheet with these cases

---

### STEP 8: Process DND Emails Database (lines 1257-1258)
**In: `process_files()` - FileProcessor**
**Method:** `process_dnd_emails_database(output_df, prev_file)`

- Loads DND (Do Not Disturb) database from previous file
- Updates cases in output_df if they match DND emails
- Preserves DND status from previous runs

---

### STEP 9: Process SMS Replies (lines 1262-1339)
**In: `process_files()` - FileProcessor**
**Method:** `process_sms_replies(output_df, sms_file, prev_file)`

- If SMS file provided:
  1. Reads SMS reply data
  2. Updates case statuses based on replies
  3. Updates individual handler sheets
  4. Creates temp prev_file with updated handler sheets
  
**Output:**
- Updated `output_df` with SMS status changes
- `updated_handler_sheets` - dictionary of handler sheets with updated data
- `prev_file_for_final` - path to temp file with handlers if created, else original prev_file

---

### STEP 10: Process Email Replies (similar to SMS)
- If email file provided, processes similarly to SMS

---

### STEP 11: Prepare Processing Statistics (lines 1375-1383)
**In: `process_files()` - FileProcessor**

Collects comprehensive statistics dictionary:
```python
processing_stats = {
    'Initial Count': initial_count,
    'After Work Order Status': wo_status_count,
    'After Case Reason': case_reason_count,
    'After Closing Code': closing_code_count,
    'After CID/DMR Filter': post_cid_count,
    'After Duplicate Removal': filtered_count,
    'Final Count': final_count,
    'Total Removed': initial_count - filtered_count,
    'Previous File Stats': prev_stats,
    'SMS Processing Stats': sms_processing_stats,
    'Email Processing Stats': email_processing_stats,
    'Raw File DND Emails': raw_dnd_emails,
    'DND Database': getattr(self, 'dnd_database', []),
    'Dropped Cases Details': dropped_cases_details,
    'Bank/Sutherland Updated Cases': getattr(self, 'bank_sutherland_updated_cases', []),
    'DND Updated Cases': getattr(self, 'dnd_updated_cases', [])
}
```

---

### STEP 12: FINAL PROCESSOR - Create Additional Sheets (lines 1385-1433) ⭐ CRITICAL
**In: `process_files()` - FileProcessor**
**Method:** `FinalProcessor.process_final_output(...)`

**Location:** Lines 257-336 in final_processor.py

#### FinalProcessor 12.1: Validate Output Data
- Checks for missing case numbers
- Validates handler assignments
- Identifies duplicate/invalid data
- Logs critical issues

#### FinalProcessor 12.2: Create Companies Sheet (lines 257-294)
**Purpose:** Separate sheet for cases with duplicate emails (multi-company cases)

**Process:**
1. Identifies NEW duplicate email cases (from `duplicate_company_cases` list)
2. Loads previous Companies sheet (if exists)
3. **Merges with preservation:** Previous Companies data takes priority
   - Overlapping cases: KEEP previous data (actions, status, handler preserved)
   - Non-overlapping previous cases: PRESERVE all previous work
   - Truly new cases: ADD for assignment
4. Groups by EMAIL (not company!)
   - Same email → same handler
   - One handler assigned per unique email group
5. Uses `_assign_companies_cases()` for round-robin email-based assignment
   - Preserves existing handlers for emails already in previous file
   - Uses round-robin for new emails
6. Creates "Companies" sheet with these cases

**Key Difference:** 
- PA Cases main sheet: Groups by COMPANY for assignment
- Companies sheet: Groups by EMAIL for assignment
- This is intentional - companies duplicates need email-based grouping

#### FinalProcessor 12.3: Create Handler Individual Sheets (lines 1328-1503)
**Purpose:** Each handler gets their own sheet with assigned cases

**Process `create_handler_sheets_from_processed_data()`:**
1. Loads all handler sheets from previous file (if exists)
2. For each handler:
   - Gets current cases (from output_df where Assigned To = handler)
   - Gets previous cases (from prev_file handler sheet)
   - **Merges using logic:**
     ```
     For each previous case:
       If case still assigned to handler → Update with latest data
       If case no LONGER assigned to handler → Remove it
     For each new case:
       Add new cases from current output
     ```
3. **Result:** Preserves handler's work history, adds new cases, removes unrelated cases
4. Locks sheet with password 'artadmin'

**Key Logic (lines 1439-1520):**
- New cases: Use latest current data
- Existing cases: Merge current data with previous custom fields (Notes, etc.)
- Removed cases: Don't appear in handler sheet anymore

#### FinalProcessor 12.4: Create Counter Sheet (lines 2597-2770)
**Purpose:** Progress tracking dashboard for each handler

**Contents:**
1. **Progress Counter Table** - for each handler:
   - Total cases
   - Requires a Call
   - In Progress  
   - New (status='new')
   - Closed
   - Skipped

2. **Final Action Counter Table** - for each handler:
   - Fixed
   - Refused Callback
   - Issue Not Fixed
   - Escalation
   - Left VM
   - etc.

3. **Formulas:** Uses COUNTIFS to read from individual handler sheets
   - Dynamically updates when handler sheets change
   - References: `'Handler Name's Cases'!R:R` for Status column

#### FinalProcessor 12.5: Create Summary Sheet (lines 2911-3030)
**Purpose:** Statistical report of processing

**Includes:**
- Record count statistics
- Processing stage breakdowns
- Handler workload distribution
- Data quality checks (missing data, duplicates, invalid emails)
- Bank/Sutherland rule applied cases
- Dropped cases by reason

---

## Data Flow Summary: Key Variables

| Variable | Type | Content |
|----------|------|---------|
| `df` | DataFrame | Main working dataframe through processing |
| `output_df` | DataFrame | After formatting, ready for final output |
| `prev_df` | DataFrame | Data from previous file (for merging/preservation) |
| `selected_handlers` | list[str] | User-selected handlers for new case assignment |
| `duplicate_company_cases` | list | Case numbers with duplicate emails (for Companies sheet) |
| `updated_handler_sheets` | dict | Handler → DataFrame for sheets updated via SMS/Email |
| `processing_stats` | dict | Comprehensive statistics for Summary sheet |

---

## Critical Handler Assignment Rules

### Rule 1: Preserve Previous Assignments
- Cases with existing handler from prev_file keep that handler (from BOTH main sheet AND individual handler sheets)
- These are NOT part of the round-robin distribution
- Preserved cases are "locked in" and exempt from new assignment

### Rule 2 (PA Cases Main): Group by COMPANY
- NEW cases grouped by Company Name column
- Multi-case companies (2+ cases): ALL cases from same company → SAME handler (single assignment)
- Single-case companies & no-company cases: assigned individually via round-robin
- One handler assigned per company group, not per case

### Rule 3 (Companies Sheet): Group by EMAIL
- Companies cases (email duplicates) grouped by Email column
- Same email across cases → SAME handler (single assignment)
- One handler assigned per email group, not per case

### Rule 4: Round-Robin Distribution
- New company/email groups assigned to handlers in order
- Cycles through selected_handlers list
- Fair distribution across selected handlers ONLY
- No unselected handlers get new cases

### Rule 5: Only NEW Cases Get Assigned
- Cases already having assignments from prev_file are skipped
- Only unassigned cases participate in round-robin grouping

### Rule 6: Handler Sheet Preservation
- ALL handler sheets preserved from previous file
- Even if handler not in selected_handlers
- Preserves complete handler work history
- Companies cases EXCLUDED from handler sheets
- Handler sheets focus on PA Cases only

---

## Exception Handling

1. **File Validation Failures:**
   - Returns error immediately with message
   - Doesn't proceed to processing

2. **Import Errors (FinalProcessor):**
   - Catches ImportError, logs warning
   - Saves basic output without additional sheets

3. **Processing Errors:**
   - Catches general Exception during final processing
   - Saves basic output as fallback
   - Logs full traceback

---

## Performance Considerations

1. **Email Grouping:** Groups by Email (expensive for large files)
2. **Handler Sheet Loading:** Reads entire previous file structure
3. **Duplicate Checking:** Sorts by Created On date (requires parsing)
4. **Companies Sheet Processing:** Additional filtering and assignment logic

---

## Validation & Quality Checks

### Before Processing:
- File column validation
- Handler list validation

### During Processing:
- Duplicate case detection
- Case number normalization
- Completion date preservation

### Final Processing (FinalProcessor):
- Output data validation
- Missing value checks
- Invalid email detection
- Distribution fairness checks

---

## User-Facing UI (MainWindow)

The assigner tool UI at `src/ui/main_window.py`:

1. **File Selection:** Raw file, previous file, SMS file, email file
2. **Handler Management:** Checkbox for each handler
3. **Processing Trigger:** Start button (runs FileProcessingWorker thread)
4. **Log Display:** Real-time progress logging
5. **Output Specification:** Output file path

The UI communicates with backend via:
- `FileProcessingWorker` QThread for async processing
- `FileProcessor` class for business logic
- Signal/slot communication for logging and completion

