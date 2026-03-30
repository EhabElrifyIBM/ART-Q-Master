# Chat Agent Code Reference - Complete Methods

## Complete Method Code Snippets

### 1. MainWindow.get_chat_agent_info()
**File:** main_window_assigner.py (Lines 1086-1103)
**Purpose:** Extract Chat Agent configuration from UI inputs

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

### 2. MainWindow._on_chat_agent_toggled()
**File:** main_window_assigner.py (Lines 1066-1072)
**Purpose:** Toggle Chat Agent supporter name input visibility

```python
def _on_chat_agent_toggled(self, state):
    """Handle Chat Agent checkbox toggle
    Shows/hides the supporter name input field
    """
    if self.chat_agent_input:
        self.chat_agent_input.setVisible(state == Qt.Checked)
        if state != Qt.Checked:
            # Clear the input field when unchecked
            self.chat_agent_input.clear()
```

---

### 3. FileProcessor.calculate_fair_share()
**File:** assigner_processor.py (Lines 2683-2775)
**Purpose:** Calculate fair share and Chat Agent capacity based on in-progress cases

```python
def calculate_fair_share(self, df, selected_handlers, chat_agent_info=None):
    """Calculate fair share of cases for equitable distribution
    
    CRITICAL: Only counts IN_PROGRESS cases for fair share calculation
    Chat Agent gets: fair_share × 1.15 from in_progress cases only
    
    Args:
        df: DataFrame with all cases
        selected_handlers: List of selected handler names
        chat_agent_info: Dict with Chat Agent info or None
        
    Returns:
        dict: {
            'total_cases': int (in_progress only),
            'total_handlers': int,
            'fair_share': float,
            'chat_agent_capacity': float (if enabled),
            'handler_list': list of all handlers including Chat Agent
        }
    """
    try:
        # CRITICAL: Count ONLY in_progress cases
        # Find all status columns and identify in_progress cases
        status_cols = [col for col in df.columns if 'status' in col.lower()]
        
        # Build a mask for in_progress cases
        in_progress_mask = pd.Series([False] * len(df), index=df.index)
        
        if status_cols:
            for status_col in status_cols:
                in_progress_mask = in_progress_mask | (df[status_col].astype(str).str.lower().str.contains(r'in[_\s.]?progress', regex=True, na=False))
        
        # Count only in_progress cases
        total_cases = in_progress_mask.sum()
        
        self.logger.info(f"Fair Share Calculation (IN_PROGRESS CASES ONLY):")
        self.logger.info(f"  Total cases in dataframe: {len(df)}")
        self.logger.info(f"  Total IN_PROGRESS cases: {total_cases}")
        self.logger.info(f"  Status columns used: {status_cols}")
        
        # Calculate total handlers
        total_handlers = len(selected_handlers)
        if chat_agent_info and chat_agent_info.get('enabled'):
            total_handlers += 1  # Add Chat Agent as a handler
        
        # Calculate fair share based on in_progress cases only
        if total_handlers > 0:
            fair_share = total_cases / total_handlers
        else:
            fair_share = 0
        
        result = {
            'total_cases': total_cases,
            'total_handlers': total_handlers,
            'fair_share': fair_share,
            'handler_list': selected_handlers.copy()
        }
        
        # Add Chat Agent info if enabled
        if chat_agent_info and chat_agent_info.get('enabled'):
            import math
            # Calculate Chat Agent capacity: 15% more than fair share
            chat_agent_capacity_raw = fair_share * 1.15
            chat_agent_capacity = math.ceil(chat_agent_capacity_raw)  # Round UP to nearest integer
            
            result['chat_agent_capacity'] = chat_agent_capacity
            result['chat_agent_capacity_raw'] = chat_agent_capacity_raw
            result['chat_agent_name'] = chat_agent_info.get('supporter_name', 'Chat Agent')
            result['handler_list'].append('Chat Agent')
            
            self.logger.info(f"Chat Agent Capacity Rule (15% bonus):")
            self.logger.info(f"  Fair share (regular handlers): {fair_share:.2f}")
            self.logger.info(f"  Chat Agent capacity (raw): {chat_agent_capacity_raw:.2f}")
            self.logger.info(f"  Chat Agent capacity (rounded up): {chat_agent_capacity}")
        
        self.logger.info(f"Fair Share Calculation:")
        self.logger.info(f"  Total cases: {total_cases}")
        self.logger.info(f"  Total handlers: {total_handlers}")
        self.logger.info(f"  Fair share per handler: {fair_share:.2f}")
        
        return result
        
    except Exception as e:
        self.logger.error(f"Error in calculate_fair_share: {str(e)}")
        import traceback
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'total_cases': 0,
            'total_handlers': len(selected_handlers),
            'fair_share': 0,
            'handler_list': selected_handlers.copy()
        }
```

---

### 4. FileProcessor.calculate_chat_agent_cases_needed()
**File:** assigner_processor.py (Lines 2776-2844)
**Purpose:** Determine how many cases Chat Agent needs to reach capacity

```python
def calculate_chat_agent_cases_needed(self, df, chat_agent_supporter_name='Chat Agent'):
    """Calculate how many cases Chat Agent needs to reach capacity
    
    Only counts in_progress cases.
    
    Args:
        df: DataFrame with current case assignments
        chat_agent_supporter_name: Name of Chat Agent supporter
        
    Returns:
        dict: {
            'can_receive': bool,
            'current_queue': int,
            'capacity': int,
            'cases_needed': int
        }
    """
    try:
        if not self.fair_share_info or 'chat_agent_capacity' not in self.fair_share_info:
            return {
                'can_receive': False,
                'current_queue': 0,
                'capacity': 0,
                'cases_needed': 0,
                'reason': 'Chat Agent not enabled or capacity not calculated'
            }
        
        # Count current Chat Agent queue - ONLY in_progress cases
        current_queue = 0
        if 'Assigned To' in df.columns:
            chat_cases = df[df['Assigned To'] == chat_agent_supporter_name]
            # Filter for in_progress status (check Status or Case Status columns)
            if len(chat_cases) > 0:
                # Look for in_progress status - OR all status columns
                status_cols = [col for col in chat_cases.columns if 'status' in col.lower()]
                in_progress_mask = pd.Series([False] * len(chat_cases), index=chat_cases.index)
                for status_col in status_cols:
                    if status_col in chat_cases.columns:
                        in_progress_mask = in_progress_mask | (chat_cases[status_col].astype(str).str.lower().str.contains(r'in[_\s.]?progress', regex=True, na=False))
                in_progress_cases = chat_cases[in_progress_mask]
                current_queue = len(in_progress_cases)
        
        capacity = self.fair_share_info['chat_agent_capacity']
        cases_needed = capacity - current_queue
        can_receive = cases_needed > 0
        
        self.logger.info(f"Chat Agent Capacity Check:")
        self.logger.info(f"  Current in_progress queue: {current_queue}")
        self.logger.info(f"  Capacity (fair share × 1.15): {capacity}")
        self.logger.info(f"  Cases needed: {cases_needed}")
        self.logger.info(f"  Can receive more: {can_receive}")
        
        return {
            'can_receive': can_receive,
            'current_queue': current_queue,
            'capacity': capacity,
            'cases_needed': cases_needed if cases_needed > 0 else 0
        }
        
    except Exception as e:
        self.logger.error(f"Error in calculate_chat_agent_cases_needed: {str(e)}")
        import traceback
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            'can_receive': False,
            'current_queue': 0,
            'capacity': 0,
            'cases_needed': 0,
            'error': str(e)
        }
```

---

### 5. FileProcessor.redistribute_cases_to_chat_agent()
**File:** assigner_processor.py (Lines 2847-2979)
**Purpose:** Pull cases from eligible handlers and reassign to Chat Agent

**Key Algorithm Steps:**

```python
def redistribute_cases_to_chat_agent(self, df, chat_agent_info, chat_agent_supporter_name='Chat Agent'):
    """Redistribute IN_PROGRESS cases from eligible handlers to Chat Agent
    
    Redistribution rules:
    - Chat Agent capacity = Fair Share × 1.15 (already calculated)
    - Preserve previous Chat Agent cases
    - Pull ONLY in_progress cases from bottom of eligible handlers' queues (oldest first - FIFO)
    - Only from handlers whose queue is ABOVE fair share
    - Pull from BOTTOM of handler queue (oldest cases) - copy entire row with all data
    - Only update "Assigned To" to Chat Agent name
    
    Args:
        df: DataFrame with case assignments
        chat_agent_info: Chat Agent info dict
        chat_agent_supporter_name: Chat Agent supporter name (goes in Assigned To column)
        
    Returns:
        DataFrame with redistributed cases (ALL data preserved, only Assigned To changed)
    """
    try:
        if not chat_agent_info or not chat_agent_info.get('enabled'):
            self.logger.info("Chat Agent not enabled - skipping redistribution")
            return df
        
        if not self.fair_share_info:
            self.logger.warning("Fair share info not available - skipping redistribution")
            return df
        
        # Get target capacity for Chat Agent (115% of fair share)
        target_capacity = self.fair_share_info.get('chat_agent_capacity', 0)
        fair_share = self.fair_share_info.get('fair_share', 0)
        selected_handlers = [h for h in self.fair_share_info.get('handler_list', []) if h != 'Chat Agent']
        
        self.logger.info(f"\n=== CHAT AGENT REDISTRIBUTION (115% CAPACITY MODEL) ===")
        self.logger.info(f"Chat Agent: {chat_agent_supporter_name}")
        self.logger.info(f"Fair share per handler: {fair_share:.2f}")
        self.logger.info(f"Chat Agent target capacity (115% of fair share): {target_capacity}")
        
        # STEP 1: Identify all status columns and determine what 'in_progress' looks like
        status_cols = [col for col in df.columns if 'status' in col.lower()]
        self.logger.info(f"\nStatus columns identified: {status_cols}")
        
        if not status_cols or 'Assigned To' not in df.columns:
            self.logger.warning("Missing status columns or 'Assigned To' column - cannot redistribute")
            return df
        
        # Show sample status values for debugging
        all_status_values = set()
        for col in status_cols:
            unique_vals = df[col].dropna().unique()[:10]
            all_status_values.update([str(v).lower() for v in unique_vals])
        self.logger.info(f"Sample status values found: {all_status_values}")
        
        # STEP 2: Count current Chat Agent in_progress cases
        current_chat_in_progress = 0
        chat_agent_cases = df[df['Assigned To'] == chat_agent_supporter_name]
        
        if not chat_agent_cases.empty:
            # Build in_progress mask for Chat Agent's current cases
            in_progress_mask_chat = pd.Series([False] * len(chat_agent_cases), index=chat_agent_cases.index)
            for status_col in status_cols:
                if status_col in chat_agent_cases.columns:
                    in_progress_mask_chat = in_progress_mask_chat | (
                        chat_agent_cases[status_col].astype(str).str.lower().str.contains(r'in[_\s.]?progress', regex=True, na=False)
                    )
            current_chat_in_progress = in_progress_mask_chat.sum()
        
        cases_needed = target_capacity - current_chat_in_progress
        self.logger.info(f"\nCurrent Chat Agent in_progress cases: {current_chat_in_progress}")
        self.logger.info(f"Cases needed to reach target capacity: {max(0, cases_needed)}")
        
        if cases_needed <= 0:
            self.logger.info("Chat Agent at or above capacity - no redistribution needed")
            return df
        
        # STEP 3: Identify eligible handlers (in_progress queue > fair share)
        self.logger.info(f"\n=== IDENTIFYING ELIGIBLE HANDLERS (in_progress queue > {fair_share:.2f}) ===")
        eligible_handlers_info = {}  # handler -> {queue_size, indices}
        
        for handler in selected_handlers:
            handler_all = df[df['Assigned To'] == handler]
            if handler_all.empty:
                continue
            
            # Build in_progress mask for this handler
            in_progress_mask_handler = pd.Series([False] * len(handler_all), index=handler_all.index)
            for status_col in status_cols:
                if status_col in handler_all.columns:
                    in_progress_mask_handler = in_progress_mask_handler | (
                        handler_all[status_col].astype(str).str.lower().str.contains(r'in[_\s.]?progress', regex=True, na=False)
                    )
            
            handler_in_progress_indices = handler_all[in_progress_mask_handler].index.tolist()
            queue_size = len(handler_in_progress_indices)
            
            if queue_size > fair_share:
                eligible_status = f" → ELIGIBLE (excess: {queue_size - fair_share:.0f})"
                eligible_handlers_info[handler] = {
                    'queue_size': queue_size,
                    'in_progress_indices': handler_in_progress_indices,
                    'excess': queue_size - fair_share
                }
            else:
                eligible_status = " → not eligible"
            
            self.logger.info(f"  {handler}: {queue_size} in_progress cases (fair share: {fair_share:.2f}){eligible_status}")
        
        if not eligible_handlers_info:
            self.logger.info("No eligible handlers found - all have in_progress queue at or below fair share")
            return df
        
        # STEP 4: Sort eligible handlers by excess workload (descending)
        sorted_handlers = sorted(eligible_handlers_info.items(), 
                                key=lambda x: x[1]['excess'], reverse=True)
        
        self.logger.info(f"\n=== PULLING CASES TO REACH CHAT AGENT CAPACITY ({target_capacity} cases) ===")
        
        # STEP 5: Pull in_progress cases from eligible handlers (from bottom = oldest first)
        total_pulled = 0
        
        for handler, info in sorted_handlers:
            if cases_needed <= 0:
                break
            
            # Get in_progress indices for this handler (already identified above)
            in_progress_indices = info['in_progress_indices']
            queue_size = info['queue_size']
            
            # Pull from bottom (start of list = oldest entries)
            cases_to_pull = min(cases_needed, len(in_progress_indices))
            indices_to_reassign = in_progress_indices[:cases_to_pull]
            
            # Get case numbers for logging
            case_num_col = None
            for col in df.columns:
                if 'case number' in col.lower():
                    case_num_col = col
                    break
            
            case_numbers_pulled = []
            if case_num_col:
                case_numbers_pulled = df.loc[indices_to_reassign, case_num_col].tolist()
            
            # Reassign these cases to Chat Agent
            df.loc[indices_to_reassign, 'Assigned To'] = chat_agent_supporter_name
            
            cases_needed -= cases_to_pull
            total_pulled += cases_to_pull
            
            remaining_after = queue_size - cases_to_pull  
            self.logger.info(f"  {handler}: Pulled {cases_to_pull} cases (queue: {queue_size} → {remaining_after}, still need: {max(0, cases_needed)})")
            if case_numbers_pulled:
                self.logger.info(f"    Case #s: {case_numbers_pulled[:5]}{'...' if len(case_numbers_pulled) > 5 else ''}")
        
        self.logger.info(f"\n✓ REDISTRIBUTION COMPLETE")
        self.logger.info(f"  Total in_progress cases pulled to Chat Agent: {total_pulled}")
        self.logger.info(f"  Chat Agent will now have: {current_chat_in_progress + total_pulled} cases (target: {target_capacity})")
        
        # Verify results
        final_chat_cases = df[df['Assigned To'] == chat_agent_supporter_name]
        final_chat_in_progress = 0
        if not final_chat_cases.empty:
            in_progress_mask_final = pd.Series([False] * len(final_chat_cases), index=final_chat_cases.index)
            for status_col in status_cols:
                if status_col in final_chat_cases.columns:
                    in_progress_mask_final = in_progress_mask_final | (
                        final_chat_cases[status_col].astype(str).str.lower().str.contains('in.?progress|inprogress', regex=True, na=False)
                    )
            final_chat_in_progress = in_progress_mask_final.sum()
        
        self.logger.info(f"  Verification: Chat Agent now has {final_chat_in_progress} in_progress cases (capacity: {target_capacity})")
        
        return df
        
    except Exception as e:
        self.logger.error(f"Error in redistribute_cases_to_chat_agent: {str(e)}")
        import traceback
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        return df
```

---

### 6. FileProcessor.verify_chat_agent_persistence()
**File:** assigner_processor.py (Lines 3027-3094)
**Purpose:** Verify that Chat Agent cases are properly preserved

```python
def verify_chat_agent_persistence(self, df, chat_agent_info, prev_file=None):
    """Verify that Chat Agent cases are properly preserved from previous day
    
    Sheet name: Always "Chat Agent's Cases" (not using supporter name)
    Only counts in_progress cases
    
    Args:
        df: Current dataframe with assignments
        chat_agent_info: Chat Agent info dict
        prev_file: Path to previous file
        
    Returns:
        dict with persistence verification info
    """
    try:
        if not chat_agent_info or not chat_agent_info.get('enabled'):
            return {'enabled': False}
        
        chat_agent_supporter = chat_agent_info.get('supporter_name', 'Chat Agent')
        
        # Count in_progress Chat Agent cases in current dataframe
        current_chat_agent_cases = 0
        if 'Assigned To' in df.columns:
            chat_cases = df[df['Assigned To'] == chat_agent_supporter]
            # Filter for in_progress status only
            status_cols = [col for col in df.columns if 'status' in col.lower()]
            in_progress_cases = chat_cases
            for status_col in status_cols:
                in_progress_cases = in_progress_cases[in_progress_cases[status_col].astype(str).str.lower().str.contains('in_progress', na=False)]
            current_chat_agent_cases = len(in_progress_cases)
        
        # Check if Chat Agent sheet exists in previous file
        prev_chat_agent_cases = 0
        chat_agent_sheet_name = "Chat Agent's Cases"  # Fixed sheet name
        
        if prev_file and os.path.exists(prev_file):
            try:
                excel_file = pd.ExcelFile(prev_file)
                if chat_agent_sheet_name in excel_file.sheet_names:
                    prev_df = pd.read_excel(prev_file, sheet_name=chat_agent_sheet_name)
                    # Only count in_progress cases from previous file
                    status_cols = [col for col in prev_df.columns if 'status' in col.lower()]
                    in_progress_prev = prev_df
                    for status_col in status_cols:
                        in_progress_prev = in_progress_prev[in_progress_prev[status_col].astype(str).str.lower().str.contains('in_progress', na=False)]
                    prev_chat_agent_cases = len(in_progress_prev)
            except Exception:
                pass
        
        self.logger.info(f"\n=== Chat Agent Persistence Verification ===")
        self.logger.info(f"Chat Agent supporter name: {chat_agent_supporter}")
        self.logger.info(f"Sheet name: {chat_agent_sheet_name}")
        self.logger.info(f"Current in_progress cases assigned: {current_chat_agent_cases}")
        self.logger.info(f"Previous day in_progress cases: {prev_chat_agent_cases}")

        return {
            'enabled': True,
            'supporter_name': chat_agent_supporter,
            'current_cases': current_chat_agent_cases,
            'previous_cases': prev_chat_agent_cases,
            'sheet_name': chat_agent_sheet_name,
            'persistence_confirmed': current_chat_agent_cases >= prev_chat_agent_cases
        }
        
    except Exception as e:
        self.logger.error(f"Error verifying Chat Agent persistence: {str(e)}")
        import traceback
        self.logger.error(f"Traceback: {traceback.format_exc()}")
        return {'enabled': True, 'error': str(e)}
```

---

### 7. FileProcessor.create_chat_agent_sheet_output()
**File:** assigner_processor.py (Lines 3097-3254)
**Purpose:** Create and write Chat Agent's Cases sheet to output Excel

**Key Sections:**

**Step 1: Get Current Cases**
```python
current_chat_cases = pd.DataFrame()
if 'Assigned To' in output_df.columns:
    current_chat_cases = output_df[output_df['Assigned To'] == chat_agent_supporter_name].copy()
    self.logger.info(f"  Current cases assigned to {chat_agent_supporter_name}: {len(current_chat_cases)}")
```

**Step 2: Load Previous Cases**
```python
prev_chat_cases = pd.DataFrame()
chat_agent_sheet_name = "Chat Agent's Cases"  # Fixed sheet name

if prev_file and os.path.exists(prev_file):
    try:
        excel_file = pd.ExcelFile(prev_file)
        if chat_agent_sheet_name in excel_file.sheet_names:
            prev_chat_cases = pd.read_excel(prev_file, sheet_name=chat_agent_sheet_name)
            self.logger.info(f"  ✓ Previous Chat Agent cases loaded: {len(prev_chat_cases)}")
```

**Step 3: Normalize Case Numbers**
```python
if 'Case Number' in current_chat_cases.columns:
    current_chat_cases['Case Number'] = current_chat_cases['Case Number'].apply(
        lambda v: int(float(str(v).strip())) if pd.notna(v) and str(v).strip().replace('.','',1).isdigit() else pd.NA
    ).astype('Int64')

if 'Case Number' in prev_chat_cases.columns:
    prev_chat_cases['Case Number'] = prev_chat_cases['Case Number'].apply(
        lambda v: int(float(str(v).strip())) if pd.notna(v) and str(v).strip().replace('.','',1).isdigit() else pd.NA
    ).astype('Int64')
```

**Step 4: Merge (Current + Preserved)**
```python
current_case_nums = set(current_chat_cases['Case Number'].dropna().tolist()) if not current_chat_cases.empty else set()

if not prev_chat_cases.empty:
    previously_preserved = prev_chat_cases[~prev_chat_cases['Case Number'].isin(current_case_nums)].copy()
    self.logger.info(f"  Preserved from previous days: {len(previously_preserved)} cases")
else:
    previously_preserved = pd.DataFrame()

# Combine: current cases first, then preserved cases
if not current_chat_cases.empty or not previously_preserved.empty:
    chat_agent_cases = pd.concat([current_chat_cases, previously_preserved], ignore_index=True)
else:
    chat_agent_cases = pd.DataFrame()
```

**Step 5: Sort & Write**
```python
if not chat_agent_cases.empty:
    total_cases = len(chat_agent_cases)
    chat_agent_cases = self.sort_cases_by_status(chat_agent_cases)
    
    # Write to Excel
    chat_agent_cases.to_excel(writer, sheet_name=chat_agent_sheet_name, index=False)
    self.auto_adjust_columns(writer, chat_agent_cases, chat_agent_sheet_name)
    self.protect_worksheet(writer, chat_agent_sheet_name, password='artadmin')
    self.logger.info(f"✓ Created '{chat_agent_sheet_name}' sheet with {total_cases} total cases")
else:
    # Create empty sheet with headers if no cases
    empty_sheet_df = pd.DataFrame(columns=self.output_columns)
    empty_sheet_df.to_excel(writer, sheet_name=chat_agent_sheet_name, index=False)
    self.auto_adjust_columns(writer, empty_sheet_df, chat_agent_sheet_name)
    self.protect_worksheet(writer, chat_agent_sheet_name, password='artadmin')
    self.logger.info(f"✓ Created empty '{chat_agent_sheet_name}' sheet with headers")
```

---

## Integration Points in process_files()

### Location 1: Fair Share Calculation (Line 1297)
```python
self.fair_share_info = self.calculate_fair_share(output_df, selected_handlers, chat_agent_info)
```

### Location 2: Case Redistribution (Lines 1300-1303)
```python
if chat_agent_info and chat_agent_info.get('enabled'):
    self.logger.info("\n=== Redistributing Cases for Chat Agent Support ===")
    chat_agent_supporter_name = chat_agent_info.get('supporter_name', 'Chat Agent')
    output_df = self.redistribute_cases_to_chat_agent(output_df, chat_agent_info, chat_agent_supporter_name)
```

### Location 3: Persistence Verification (Lines 1511-1512)
```python
if chat_agent_info and chat_agent_info.get('enabled'):
    persistence_info = self.verify_chat_agent_persistence(output_df, chat_agent_info, prev_file)
```

### Location 4: Sheet Creation (in FinalProcessor)
```python
success, message = final_processor.process_final_output(
    output_df, 
    output_file, 
    processing_stats, 
    sms_file, 
    email_file, 
    prev_file, 
    duplicate_company_cases=self.duplicate_company_cases,
    selected_handlers=selected_handlers,
    chat_agent_info=chat_agent_info  # Passed to FinalProcessor
)
```

---

## Status Pattern Matching

### In-Progress Detection
Uses regex pattern: `r'in[_\s.]?progress'`

**Matches:**
- `in_progress`
- `in progress`
- `in.progress`
- `inprogress`

**Case Insensitive:**
Applied with `.str.lower().str.contains(pattern, regex=True, na=False)`

---

## Error Handling

All methods include comprehensive try-except blocks:

```python
try:
    # Method logic here
except Exception as e:
    self.logger.error(f"Error in {method_name}: {str(e)}")
    import traceback
    self.logger.error(f"Traceback: {traceback.format_exc()}")
    # Return safe default
    return {...}
```

---

## Logging Best Practices

**Key logging calls:**

1. **Initialization:**
   ```python
   self.logger.info(f"Chat Agent enabled: {chat_agent_info['supporter_name']} (15% capacity)")
   ```

2. **Calculations:**
   ```python
   self.logger.info(f"Chat Agent capacity (raw): {chat_agent_capacity_raw:.2f}")
   self.logger.info(f"Chat Agent capacity (rounded up): {chat_agent_capacity}")
   ```

3. **Operations:**
   ```python
   self.logger.info(f"  {handler}: Pulled {cases_to_pull} cases (queue: {queue_size} → {remaining_after})")
   ```

4. **Verification:**
   ```python
   self.logger.info(f"  Verification: Chat Agent now has {final_chat_in_progress} in_progress cases")
   ```

---

## Summary Table

| Method | Purpose | Input | Output |
|--------|---------|-------|--------|
| `get_chat_agent_info()` | Extract Chat Agent config from UI | UI state | `{'enabled': bool, 'supporter_name': str}` |
| `calculate_fair_share()` | Calculate case distribution | DataFrame, handlers | Fair share info dict |
| `calculate_chat_agent_cases_needed()` | Determine Chat Agent capacity | DataFrame | Capacity needs dict |
| `redistribute_cases_to_chat_agent()` | Pull cases from eligible handlers | DataFrame, info | Updated DataFrame |
| `verify_chat_agent_persistence()` | Verify data preservation | DataFrame, prev_file | Verification dict |
| `create_chat_agent_sheet_output()` | Create Chat Agent sheet | Writer, DataFrame | Excel sheet written |
