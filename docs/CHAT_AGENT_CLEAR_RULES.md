# Chat Agent Logic - Clear Step-by-Step Rules

## 🎯 Core Principle
Chat Agent is a **special role** that gets cases pulled from regular handlers. It has different rules at each step to prevent confusion.

---

## 📋 Step 1: Define Handlers at Start of Processing

**WHO & WHAT**:
- User selects handlers via UI (checkboxes): Example: **Sherif, Mark**
- User optionally enables Chat Agent and enters a supporter name: Example: **"Sherif"**

**RULE #1 - "Active Handlers" Definition**:
```
Active Handlers = Selected handlers MINUS Chat Agent (if enabled)

Example:
  Selected by user: [Sherif, Mark]  
  Chat Agent enabled: YES, supporter_name="Sherif"
  Active Handlers = [Mark]  ← Sherif is removed because he's Chat Agent
```

**RULE #2 - No Double Assignment**:
```
If a handler name is selected AND is the Chat Agent supporter:
  → That person becomes Chat Agent, NOT a regular handler
  → They do NOT get a personal handler sheet
  → They appear ONLY in Chat Agent's Cases sheet
```

---

## 📊 Step 2: Calculate Fair Share

**FORMULA**:
```
1. Count ALL in_progress cases from ACTIVE handlers only
   Example: [Mark has 100 in_progress]
   
2. Fair Share = total_in_progress / num_active_handlers
   Fair Share = 100 / 1 = 100
   
3. Chat Agent Capacity = Fair Share × 1.15 (if enabled)
   Chat Agent Capacity = 100 × 1.15 = 115 (rounded)
```

**RULE #3 - Chat Agent Capacity**:
```
Chat Agent joins the fair share calculation:
  total_handlers = len(active_handlers) + (1 if chat_agent_enabled else 0)
  
But Chat Agent's cases come LATER from active handlers, not from original distribution.
```

---

## 🔄 Step 3: Handler Assignment (NORMAL)

**BEFORE Chat Agent redistribution**:
- All cases assigned to ACTIVE handlers only (not Chat Agent yet)
- Companies get assigned to ACTIVE handlers only

**RULE #4 - No Chat Agent Yet**:
```
Handler Assignment ONLY looks at:
  selected_handlers = [Sherif, Mark] (with Chat Agent Sherif)
  active_handlers = [Mark] (Chat Agent removed)
  
Result: Cases assigned to Mark, NOT to Sherif (he's Chat Agent now)
```

---

## 📌 Step 4: Chat Agent Final Step (THE KEY STEP)

**THIS IS WHERE CHAT AGENT GETS CASES**

### STEP 4.1: Count in_progress Cases

**RULE #5 - Count only from Active Handlers**:
```
For EACH active handler:
  in_progress_count[handler] = count of cases with Status='in_progress'

Example:
  Mark: 100 in_progress cases
  
Total in_progress = 100
```

### STEP 4.2: Divide Equally

**RULE #6 - Equal Distribution**:
```
cases_per_handler = total_in_progress / num_active_handlers
cases_per_handler = 100 / 1 = 100

Pull 100 cases from Mark for Chat Agent
```

### STEP 4.3: Pull Cases from BOTTOM (Newest)

**RULE #7 - Pull Newest, Not Oldest**:
```
Pull from the BOTTOM of in_progress queue:
  - BOTTOM = end of list = newest cases
  - NOT FIFO (oldest first)
  - Copy entire row, only change "Assigned To"

For Mark's 100 in_progress cases:
  Pull the 100 NEWEST cases
  Change "Assigned To" = "Sherif" (current Chat Agent)
```

### STEP 4.4: Load & Preserve Previous Chat Agent Sheet

**RULE #8 - Fixed Sheet Name**:
```
ALWAYS look for sheet named: "Chat Agent's Cases"
NOT "Sherif's Cases" or "Mark's Cases"

This is FIXED and doesn't change with supporter name.
```

**RULE #9 - Preserve Previous Assignments**:
```
If previous file exists with "Chat Agent's Cases":
  Load ALL cases (all statuses)
  Keep their ORIGINAL "Assigned To" values
  
Example:
  Previous:  100 cases, "Assigned To" = "Sherif"
  Today:    Chat Agent is "Sherif"
  Result:    Keep "Assigned To" = "Sherif" (DO NOT CHANGE)
```

### STEP 4.5: Merge New & Previous Cases

**RULE #10 - NEW Cases Get Current Supporter**:
```
New pulled cases:
  "Assigned To" = Current Chat Agent supporter name
  
Example:
  Pulled 50 new cases from Mark
  Set "Assigned To" = "Sherif" (today's Chat Agent)
```

**RULE #11 - PREVIOUS Cases Keep Original Names**:
```
Previous cases from "Chat Agent's Cases":
  "Assigned To" = Original value from previous file
  DO NOT CHANGE THEM
  
Example:
  Previous had 100 cases with "Assigned To" = "Sherif"
  Keep them as "Assigned To" = "Sherif" (exact value)
```

**RULE #12 - Merge Order**:
```
Final sheet = [NEW cases] + [PREVIOUS cases not in new]

"Chat Agent's Cases" sheet gets:
  Top: 50 new cases with "Assigned To" = "Sherif"
  Bottom: 100 previous cases with "Assigned To" = "Sherif"
  Total: 150 cases
```

### STEP 4.6: Write Chat Agent Sheet

**RULE #13 - Fixed Sheet Name When Writing**:
```
ALWAYS write to sheet: "Chat Agent's Cases"
NOT to "Sherif's Cases" or current supporter's name

Sheet name = "Chat Agent's Cases" (fixed)
Supporter name = goes in "Assigned To" column only
```

---

## 📊 Step 5: Create Regular Handler Sheets

**IMPORTANT**: Handler sheets show ONLY that handler's current cases (after Chat Agent pull)

**RULE #14 - Handler Sheets Exclude Redistribution**:
```
Mark's Cases sheet shows:
  - Cases currently assigned to Mark
  - This is AFTER Chat Agent pulled 100 cases
  - So Mark now has fewer cases than before
  
DO NOT create a sheet for Chat Agent (Sherif)
  - Sherif is Chat Agent, not a regular handler
  - His cases appear ONLY in "Chat Agent's Cases"
```

---

## 📈 Step 6: Create Counter Sheet

**RULE #15 - Counter Shows ONLY Active Handlers**:
```
Active Handlers = selected_handlers MINUS Chat Agent

Counter tables include:
  - Progress Counter: Shows Mark only
  - Final Action Counter: Shows Mark only
  - Company Cases Counter: Shows Mark only

NOT included:
  - Sherif (he's Chat Agent, not in counter as regular handler)
  - Chat Agent (as a separate row) - NOT SHOWN
```

**RULE #16 - In-Progress Count Excludes Chat Agent**:
```
When counting "in_progress" status:
  - Count ONLY active handlers
  - DO NOT count Chat Agent rows
  
Example counter:
  Row 1: Handler | Closed | In Progress | New | Total
  Row 2: Mark   | 50     | 0           | 20  | 70
```

---

## 🏢 Step 7: Create Companies Sheet

**RULE #17 - Companies Excluded from Chat Agent**:
```
Companies are assigned to ACTIVE handlers only:
  active_handlers = [Mark]

Do NOT assign companies to Chat Agent
```

**RULE #18 - Companies Counter Excludes Chat Agent**:
```
Company Cases Counter shows:
  Handler | New | Closed | Total
  Mark    | 10  | 5      | 15
  
NOT included:
  - Sherif / Chat Agent
```

---

## 🔍 Summary Table: At Each Step, Who Shows Where

| Step | Sherif (Chat Agent) | Mark (Active Handler) |
|------|---------------------|----------------------|
| **Handler Assignment** | NOT assigned (Chat Agent role) | All cases initially |
| **After Chat Agent Pull** | Gets 100 pulled cases | Has remaining cases only |
| **Handler Sheet** | NO sheet (use Chat Agent's Cases) | "Mark's Cases" sheet |
| **PA Cases Main** | Some cases appear with "Assigned To"=Sherif | Has remaining cases |
| **Chat Agent Sheet** | "Chat Agent's Cases" sheet (merged prev+new) | - |
| **Counter Progress** | NOT shown (excluded) | Shown only |
| **Counter Final Action** | NOT shown (excluded) | Shown only |
| **Companies Sheet** | NOT assigned cases | Assigned round-robin |
| **Companies Counter** | NOT shown (excluded) | Shown only |

---

## 🚨 Common Mistakes to Avoid

❌ **WRONG**:
```
Create sheet "Sherif's Cases" for Chat Agent
  → Sheet names should ALWAYS be "Chat Agent's Cases"
```

✅ **CORRECT**:
```
Create sheet "Chat Agent's Cases"
  → Supporter name "Sherif" appears in "Assigned To" column
```

---

❌ **WRONG**:
```
Show Sherif in Counter as regular handler
  → He's Chat Agent, should NOT appear in counters
```

✅ **CORRECT**:
```
Show ONLY Mark in counters
  → Exclude Chat Agent completely from counter calculations
```

---

❌ **WRONG**:
```
Previous Chat Agent cases with "Assigned To"="Sherif"
  → Change them to new supporter name
```

✅ **CORRECT**:
```
Previous Chat Agent cases with "Assigned To"="Sherif"
  → Keep them as "Assigned To"="Sherif" (preserve original)
```

---

## 📍 Code Locations

| Rule | Location | Method |
|------|----------|---------|
| Rules #1-2 | Line ~1300 | `process_files()` - active handlers calculation |
| Rules #3 | Line ~2700 | `calculate_fair_share()` |
| Rules #4 | Line ~2500 | `assign_handlers()` |
| Rules #5-12 | Line ~2800 | `process_chat_agent_final_step()` |
| Rules #13 | Line ~5250 | FinalProcessor - Writing Chat Agent sheet |
| Rules #14 | Line ~5200 | FinalProcessor - Handler sheet creation |
| Rules #15-16 | Line ~7750 | `create_counters_sheet()` |
| Rules #17-18 | Line ~5600 | `create_companies_sheet_with_preservation()` |

---

## ✅ Verification Checklist

After processing with Chat Agent enabled:

- [ ] File "Chat Agent's Cases" exists (NOT "Sherif's Cases" or other supporter name)
- [ ] "Chat Agent's Cases" contains new cases with "Assigned To" = "Sherif"
- [ ] "Chat Agent's Cases" preserves previous cases with original "Assigned To"
- [ ] Regular handler sheets exist (e.g., "Mark's Cases")
- [ ] Counter sheet shows ONLY active handlers (Mark, NOT Sherif/Chat Agent)
- [ ] Chat Agent NOT listed as separate row in any counter table
- [ ] Companies sheet cases assigned to ONLY active handlers
- [ ] Companies counter shows ONLY active handlers
- [ ] PA Cases main sheet shows some cases with "Assigned To" = "Sherif" (Chat Agent)
- [ ] PA Cases main sheet shows remaining cases with "Assigned To" = "Mark"

