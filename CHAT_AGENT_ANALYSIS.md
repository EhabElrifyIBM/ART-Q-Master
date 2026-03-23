# Chat Agent Implementation Analysis - Assigner Module

## Overview
The Chat Agent feature is a specialized case assignment system that allocates cases at 115% capacity of regular handlers. This document provides a complete analysis of the chat agent related code, flow, and implementation details.

---

## 1. Chat Agent Initialization & Configuration

### MainWindow (main_window_assigner.py)

#### UI Components
Location: [main_window_assigner.py](main_window_assigner.py#L1038-L1075)

**Checkbox Control:**
```python
self.chat_agent_checkbox = QCheckBox()
self.chat_agent_checkbox.stateChanged.connect(self._on_chat_agent_toggled)
self.handler_vars["Chat Agent"] = self.chat_agent_checkbox
```

**Supporter Name Input:**
```python
self.chat_agent_input = QLineEdit()
self.chat_agent_input.setPlaceholderText("Enter supporter name...")
self.chat_agent_input.setMaximumWidth(150)
self.chat_agent_input.setVisible(False)  # Hidden by default
```

#### Toggle Handler (Lines 1066-1072)
```python
def _on_chat_agent_toggled(self, state):
    """Handle Chat Agent checkbox toggle
    Shows/hides the supporter name input field
    """
    if self.chat_agent_input:
        self.chat_agent_input.setVisible(state == Qt.Checked)
        if state != Qt.Checked:
            self.chat_agent_input.clear()
```

#### Get Chat Agent Info (Lines 1086-1103)
```python
def get_chat_agent_info(self):
    """Get Chat Agent info if selected
    Returns:
        dict: {'enabled': bool, 'supporter_name': str} or None if not selected
    """
    if not self.chat_agent_checkbox or not self.chat_agent_checkbox.isChecked():
        return None
    
    supporter_name = self.chat_agent_input.text().strip() if self.chat_agent_input else ""
    if not supporter_name:
        return None  # Chat Agent checkbox checked but no supporter name entered
    
    return {
        'enabled': True,
        'supporter_name': supporter_name
    }
```

---

## 2. Process Flow with Chat Agent

### FileProcessingWorker (main_window_assigner.py)

#### Worker Constructor (Lines 78-86)
```python
def __init__(self, raw_file, prev_file, sms_file, email_file, output_file, selected_handlers, chat_agent_info=None):
    super().__init__()
    self.raw_file = raw_file
    self.prev_file = prev_file
    self.sms_file = sms_file
    self.email_file = email_file
    self.output_file = output_file
    self.selected_handlers = selected_handlers
    self.chat_agent_info = chat_agent_info  # Passed from MainWindow
```

#### Worker Run Method (Lines 88-130)
The worker logs Chat Agent info if enabled:
```python
if self.chat_agent_info:
    self.emit_log(f"Chat Agent: {self.chat_agent_info['supporter_name']} (with 15% capacity bonus)")
```

Then passes chat_agent_info to the main processor:
```python
success, message = processor.process_files(
    self.raw_file,
    self.prev_file if self.prev_file else None,
    self.sms_file if self.sms_file else None,
    self.email_file if self.email_file else None,
    self.output_file,
    self.selected_handlers,
    chat_agent_info=self.chat_agent_info  # Passed to processor
)
```

#### Process Button Handler (Lines 1214-1247)
```python
def process(self):
    """Process the files with the selected handlers (now threaded)"""
    # ... validation code ...
    
    # Get Chat Agent info if selected
    chat_agent_info = self.get_chat_agent_info()
    
    self.worker = FileProcessingWorker(
        self.raw_file_path.text(),
        self.prev_file_path.text() if self.prev_file_path.text() else None,
        self.sms_file_path.text() if self.sms_file_path.text() else None,
        self.email_file_path.text() if self.email_file_path.text() else None,
        self.output_file_edit.text(),
        selected_handlers,
        chat_agent_info  # Passed to worker
    )
```

---

## 3. FileProcessor Main Processing Flow (assigner_processor.py)

### process_files() Method (Lines 994-1535)

#### Chat Agent Logging at Start (Lines 999-1000)
```python
if chat_agent_info:
    self.logger.info(f"Chat Agent enabled: {chat_agent_info['supporter_name']} (15% capacity)")
```

#### Fair Share Calculation with Chat Agent (Line 1297)
```python
self.fair_share_info = self.calculate_fair_share(output_df, selected_handlers, chat_agent_info)
```

#### Case Redistribution to Chat Agent (Lines 1300-1303)
```python
if chat_agent_info and chat_agent_info.get('enabled'):
    self.logger.info("\n=== Redistributing Cases for Chat Agent Support ===")
    chat_agent_supporter_name = chat_agent_info.get('supporter_name', 'Chat Agent')
    output_df = self.redistribute_cases_to_chat_agent(output_df, chat_agent_info, chat_agent_supporter_name)
```

#### Chat Agent Persistence Verification (Lines 1511-1512)
```python
if chat_agent_info and chat_agent_info.get('enabled'):
    persistence_info = self.verify_chat_agent_persistence(output_df, chat_agent_info, prev_file)
```

---

## 4. Fair Share Calculation

### calculate_fair_share() Method (Lines 2683-2775)

**Purpose:** Calculate fair share of cases and Chat Agent capacity based on in-progress cases only

**Key Parameters:**
```python
def calculate_fair_share(self, df, selected_handlers, chat_agent_info=None):
    """Calculate fair share of cases for equitable distribution
    
    CRITICAL: Only counts IN_PROGRESS cases for fair share calculation
    Chat Agent gets: fair_share × 1.15 from in_progress cases only
    """
```

**Logic:**
1. Count ONLY in-progress cases (ignores closed, pending, etc.)
2. Calculate fair_share = total_in_progress_cases / total_handlers
3. If Chat Agent enabled: chat_agent_capacity = fair_share × 1.15 (rounded UP)

**Return Value:**
```python
result = {
    'total_cases': total_cases,              # in_progress only
    'total_handlers': total_handlers,        # includes Chat Agent if enabled
    'fair_share': fair_share,                # float, per handler
    'chat_agent_capacity': chat_agent_capacity,  # if enabled
    'chat_agent_capacity_raw': chat_agent_capacity_raw,  # raw value
    'chat_agent_name': supporter_name,       # if enabled
    'handler_list': list_with_chat_agent     # includes Chat Agent
}
```

**Example:**
- 100 in-progress cases
- 4 regular handlers + 1 Chat Agent = 5 total handlers
- Fair share = 100 / 5 = 20 cases per handler
- Chat Agent capacity = 20 × 1.15 = 23 cases (rounded up to 23)

---

## 5. Chat Agent Case Selection & Redistribution

### calculate_chat_agent_cases_needed() (Lines 2776-2844)

**Purpose:** Determine how many cases Chat Agent needs to reach capacity

**Parameters:**
```python
def calculate_chat_agent_cases_needed(self, df, chat_agent_supporter_name='Chat Agent'):
    """Calculate how many cases Chat Agent needs to reach capacity
    
    Only counts in_progress cases.
    """
```

**Returns:**
```python
{
    'can_receive': bool,           # Whether Chat Agent can accept more cases
    'current_queue': int,          # Current in_progress cases assigned
    'capacity': int,               # Total capacity
    'cases_needed': int            # Cases needed to reach capacity
}
```

**Logic Flow:**
1. Count current in-progress cases assigned to Chat Agent
2. Get target capacity from fair_share_info
3. Calculate: cases_needed = capacity - current_queue
4. Return can_receive = (cases_needed > 0)

---

### redistribute_cases_to_chat_agent() (Lines 2847-2979)

**Purpose:** Pull cases from eligible handlers and reassign to Chat Agent to reach capacity

**Key Features:**
- Only redistributes in-progress cases
- Pulls from handlers whose queue > fair share
- Pulls from BOTTOM of queue (oldest cases first - FIFO)
- Preserves all other case data (only changes "Assigned To")
- Logs detailed reassignment steps

**Redistribution Algorithm:**

**Step 1: Current Capacity Check**
```python
current_chat_in_progress = 0  # Count Chat Agent's current in_progress cases
cases_needed = target_capacity - current_chat_in_progress
```

**Step 2: Identify Eligible Handlers**
```python
# A handler is eligible if: queue_size > fair_share
for handler in selected_handlers:
    queue_size = count_in_progress_cases(handler)
    if queue_size > fair_share:
        eligible_handlers_info[handler] = {
            'queue_size': queue_size,
            'in_progress_indices': indices,
            'excess': queue_size - fair_share
        }
```

**Step 3: Sort by Excess Workload**
```python
sorted_handlers = sorted(eligible_handlers_info.items(), 
                        key=lambda x: x[1]['excess'], reverse=True)
```

**Step 4: Pull Cases (Oldest First)**
```python
for handler, info in sorted_handlers:
    if cases_needed <= 0:
        break
    
    in_progress_indices = info['in_progress_indices']  # Already filtered
    cases_to_pull = min(cases_needed, len(in_progress_indices))
    
    # Pull from BOTTOM (oldest cases = start of list)
    indices_to_reassign = in_progress_indices[:cases_to_pull]
    
    # Reassign to Chat Agent
    df.loc[indices_to_reassign, 'Assigned To'] = chat_agent_supporter_name
    cases_needed -= cases_to_pull
```

**Example:**
```
Handlers with in-progress cases:
- Adam: 25 cases (excess: +5)
- Ehab: 22 cases (excess: +2)
- Other: 18 cases (eligible: no)

Chat Agent needs: 8 more cases
Fair share: 20 each

Redistribution:
1. From Adam: pull 5 oldest cases (excess all)
2. From Ehab: pull 3 more oldest cases (from excess 2)
3. Chat Agent now has target capacity
```

---

## 6. Chat Agent Persistence Verification

### verify_chat_agent_persistence() (Lines 3027-3094)

**Purpose:** Verify that Chat Agent cases are properly preserved from previous day

**Key Parameters:**
```python
def verify_chat_agent_persistence(self, df, chat_agent_info, prev_file=None):
    """Verify that Chat Agent cases are properly preserved from previous day
    
    Sheet name: Always "Chat Agent's Cases" (not using supporter name)
    Only counts in_progress cases
    """
```

**Logic:**
1. Count current in-progress Chat Agent cases from output_df
2. Load previous "Chat Agent's Cases" sheet from prev_file
3. Count previous in-progress Chat Agent cases
4. Verify: current_cases >= previous_cases (persistence confirmed)

**Return Value:**
```python
{
    'enabled': True/False,           # Chat Agent status
    'supporter_name': str,           # Chat Agent supporter
    'current_cases': int,            # Current in_progress cases
    'previous_cases': int,           # Previous in_progress cases
    'sheet_name': str,               # "Chat Agent's Cases"
    'persistence_confirmed': bool    # Verification result
}
```

---

## 7. Chat Agent Sheet Creation & Preservation

### create_chat_agent_sheet_output() (Lines 3097-3254)

**Purpose:** Create and write the "Chat Agent's Cases" sheet to output Excel file

**Key Features:**
- Preserves ALL previous Chat Agent cases (all statuses)
- Adds all current cases assigned to Chat Agent
- Merges data without duplicates
- Sorts by status
- Creates empty sheet with headers if no cases

**Preservation Rules:**
```python
# STEP 1: Get current Chat Agent cases from output_df
current_chat_cases = output_df[output_df['Assigned To'] == chat_agent_supporter_name].copy()

# STEP 2: Load previous Chat Agent cases from "Chat Agent's Cases" sheet
if chat_agent_sheet_name in excel_file.sheet_names:
    prev_chat_cases = pd.read_excel(prev_file, sheet_name=chat_agent_sheet_name)

# STEP 3: Normalize case numbers for merging
# (Convert to integers for accurate comparison)

# STEP 4: Merge - keep current, add previous not in current
current_case_nums = set(current_chat_cases['Case Number'].dropna())
previously_preserved = prev_chat_cases[~prev_chat_cases['Case Number'].isin(current_case_nums)]

# STEP 5: Combine (current first, then preserved)
chat_agent_cases = pd.concat([current_chat_cases, previously_preserved], ignore_index=True)

# STEP 6: Write to Excel
chat_agent_cases.to_excel(writer, sheet_name="Chat Agent's Cases", index=False)
```

**Sheet Structure:**
- Fixed sheet name: `"Chat Agent's Cases"` (not using supporter name)
- Contains ALL output columns (same as handler sheets)
- Preserves entire row with all data
- Sorted by status
- Auto-adjusted columns for readability
- Sheet protected with password 'artadmin'

---

## 8. Process Flow Summary

### Complete Chat Agent Flow:

```
1. MainWindow.get_chat_agent_info()
   ↓ Returns: {'enabled': True, 'supporter_name': 'John Doe'}

2. FileProcessingWorker.__init__(chat_agent_info)
   ↓ Stores chat_agent_info

3. process_files(chat_agent_info)
   ↓
   3a. Assign handlers to all cases (new and previous)
   ↓
   3b. calculate_fair_share(chat_agent_info)
       - Count only IN_PROGRESS cases
       - Calculate: fair_share = total_in_progress / total_handlers
       - Calculate: chat_agent_capacity = fair_share × 1.15
   ↓
   3c. redistribute_cases_to_chat_agent()
       - Count current Chat Agent in_progress queue
       - Identify eligible handlers (queue > fair_share)
       - Pull oldest in_progress cases from eligible handlers
       - Reassign to Chat Agent until capacity reached
   ↓
   3d. verify_chat_agent_persistence()
       - Count current in_progress Chat Agent cases
       - Load previous "Chat Agent's Cases" sheet
       - Verify cases preserved: current >= previous
   ↓
   3e. format_output_data()
       - Standard case formatting and cleanup
   ↓
   3f. create_chat_agent_sheet_output()
       - Get current Chat Agent cases
       - Load previous Chat Agent cases from prev file
       - Merge without duplicates (current first)
       - Write "Chat Agent's Cases" sheet to output Excel

4. Final workbook created with:
   - PA Cases (main sheet)
   - Handler sheets (one per selected handler)
   - Chat Agent's Cases (if enabled)
   - Issue Not Fixed, DND Emails, Companies sheets
```

---

## 9. Key Data Structures

### chat_agent_info Dictionary
```python
{
    'enabled': bool,              # True if Chat Agent is selected
    'supporter_name': str         # Name of supporter (e.g., 'John Doe')
}
```

### fair_share_info Dictionary (after calculate_fair_share())
```python
{
    'total_cases': int,                    # in_progress cases only
    'total_handlers': int,                 # includes Chat Agent if enabled
    'fair_share': float,                   # per regular handler
    'chat_agent_capacity': int,            # rounded up (fair_share × 1.15)
    'chat_agent_capacity_raw': float,      # raw value before rounding
    'chat_agent_name': str,                # supporter name (if enabled)
    'handler_list': [str, ...]             # all handlers including Chat Agent
}
```

### Chat Agent Cases Status Breakdown
```python
current_chat_cases.groupby('Status').size()
# Example:
# Status
# closed              15
# in_progress         10
# in_progress_today    5
# Name: count, dtype: int64
```

---

## 10. Chat Agent Selection Rules

### Who Gets Selected?
- Only cases with 'in_progress' status (regex: r'in[_\s.]?progress')
- Excludes closed, pending, completed cases
- Only from handlers whose queue is ABOVE fair share

### Redistribution Order
1. Sort eligible handlers by excess workload (highest first)
2. Pull from each handler until Chat Agent reaches capacity
3. Pull oldest cases first (FIFO)
4. Stop when capacity reached

### Capacity Calculation
- Base: fair_share = total_in_progress_cases / total_handlers
- Chat Agent: capacity = ceil(fair_share × 1.15)
- Example: 100 cases, 5 handlers = 20/handler, Chat Agent = ceil(23) = 23

---

## 11. Sheet Preservation Across Runs

### Previous File Loading
When previous file exists:
1. Load main PA Cases sheet → preserve assignments for existing cases
2. Load all handler sheets (ending with "'s Cases") → preserve individual handler work
3. Load "Chat Agent's Cases" sheet → preserve Chat Agent's previous cases

### Merging Logic
- **Current cases first** (always include today's assignments)
- **Then previous cases** (add only cases not in current)
- Prevents duplicates while preserving all historical data

### Sheet Name Fixed
- Always: `"Chat Agent's Cases"` (not dynamic like handler sheets)
- Ensures consistent reference across runs
- Can be reliably loaded in future runs

---

## 12. Logging & Monitoring

### Key Log Messages

**Initialization:**
```
Chat Agent enabled: {supporter_name} (15% capacity)
```

**Fair Share Calculation:**
```
Fair Share Calculation (IN_PROGRESS CASES ONLY):
  Total cases in dataframe: XXX
  Total IN_PROGRESS cases: YYY
  Fair share per handler: ZZ.ZZ
  Chat Agent (raw): XX.XX
  Chat Agent (rounded up): XX
```

**Redistribution:**
```
=== CHAT AGENT REDISTRIBUTION (115% CAPACITY MODEL) ===
Chat Agent: {supporter_name}
Fair share per handler: XX.XX
Chat Agent target capacity (115% of fair share): XX

Current Chat Agent in_progress cases: XX
Cases needed to reach target capacity: XX

{Handler}: Pulled XX cases (queue: XX → XX, still need: XX)
    Case #s: [XXXXXX, XXXXXX, ...]

✓ REDISTRIBUTION COMPLETE
  Total in_progress cases pulled: XX
  Chat Agent will now have: XX cases (target: XX)
  Verification: Chat Agent now has XX in_progress cases
```

**Persistence:**
```
=== Chat Agent Persistence Verification ===
Chat Agent supporter name: {supporter_name}
Sheet name: Chat Agent's Cases
Current in_progress cases assigned: XX
Previous day in_progress cases: XX
```

**Sheet Creation:**
```
=== CREATING CHAT AGENT'S CASES SHEET ===
Chat Agent supporter: {supporter_name}
  Current cases assigned to {supporter_name}: XX
  Previous Chat Agent cases loaded: XX
  Preserved from previous days: XX cases
  ✓ Total cases for Chat Agent sheet:
    - Current: XX
    - Preserved from previous: XX
    - TOTAL: XX
✓ Created 'Chat Agent's Cases' sheet with XX total cases
```

---

## Summary

The Chat Agent feature is a sophisticated case distribution system that:

1. **Calculates** fair share based on in-progress cases only
2. **Allocates** 115% capacity to Chat Agent (bonus workload)
3. **Selects** cases from eligible handlers (those above fair share)
4. **Redistributes** oldest in-progress cases first (FIFO)
5. **Preserves** all case data while changing assignment
6. **Maintains** separate Chat Agent sheet across runs
7. **Verifies** persistence and logging at each step
8. **Protects** Chat Agent workload through dedicated sheet

The system is designed to balance workload while giving Chat Agent a capacity bonus to handle the volume of chat-based support requests.
