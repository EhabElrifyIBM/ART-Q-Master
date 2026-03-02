# V2 Development Branch - Quick Start Guide

## What Has Been Done

### ✅ Phase 5.1: Company Process Isolation - COMPLETE

Four new _v2 files have been created:

1. **[Dispatcher_v2.py](src/ART%20Q%20Control/Dispatcher_v2.py)** - Main dispatcher with Company Process as separate button
2. **[AutoSender_v2.py](src/ART%20Q%20Control/AutoSender_v2.py)** - No auto-trigger of Companies
3. **[CaseReviewer_v2.py](src/ART%20Q%20Control/CaseReviewer_v2.py)** - No auto-trigger of Companies
4. **[CompaniesProcess_v2.py](src/ART%20Q%20Control/CompaniesProcess_v2.py)** - Standalone mode with new `run_companies_process_standalone()` function

---

## How to Test Phase 5.1

### Test Case 1: Dispatcher Menu
```bash
# Run Dispatcher_v2
python src/ART\ Q\ Control/Dispatcher_v2.py
```
**Expected Results:**
- New "Company Process" button visible alongside Auto Sender & Case Reviewer
- Button color: Pink (#C2185B)
- Support mode checkbox works with Company Process selection

### Test Case 2: AutoSender Isolation
```bash
# Run AutoSender_v2 directly
python src/ART\ Q\ Control/AutoSender_v2.py
```
**Expected Results:**
- Processes NEW cases only
- Does NOT trigger Company Process
- Exits cleanly after case processing
- Shows completion dialog
- Returns control to Dispatcher

### Test Case 3: Company Process Standalone
```bash
# Start Dispatcher_v2 → Select Company Process → Standalone execution
```
**Expected Results:**
- Company Process initializes its own driver
- Performs Dialer login
- Switches to CRM
- Loads cache file
- Checks for Companies sheet
- Shows appropriate error if no data
- Processes companies if sheet exists
- Cleans up driver properly

---

## Files Overview

### Original Files (Unchanged)
- `Dispatcher.py` - Original version (still functional)
- `AutoSender.py` - Original version (still functional)
- `CaseReviewer.py` - Original version (still functional)
- `CompaniesProcess.py` - Original version (still functional)

### V2 Files (Enhanced)
- `Dispatcher_v2.py` - NEW: Company Process button
- `AutoSender_v2.py` - CHANGED: Removed auto-companies trigger
- `CaseReviewer_v2.py` - CHANGED: Removed auto-companies trigger
- `CompaniesProcess_v2.py` - ENHANCED: Added standalone function

---

## Next: Phase 5.2 - Company Metadata

### What Needs to be Done

1. **Create [utils/timezone_map.py](utils/timezone_map.py)**
   ```python
   # Map all US states and Canadian provinces to UTC offset
   TIMEZONE_MAP = {
       "Alabama": {"offset": -5, "display": "Central Time"},
       "Alaska": {"offset": -9, "display": "Alaska Time"},
       # ... etc for all 50 US states + Canadian provinces
   }
   ```

2. **Update [CompaniesProcess_v2.py](src/ART%20Q%20Control/CompaniesProcess_v2.py)**
   - Import timezone_map
   - Extract State/Province from Excel
   - Calculate local time: `datetime.now() + timezone_offset`
   - Display in company processing dialog

3. **Data Source:** Excel sheet columns
   - Name
   - Company Name
   - Email
   - State/Province (for timezone lookup)

---

## Next: Phase 5.3 - Navigation Fixes

### What Needs to be Done

1. **Fix Previous Case Button in [CaseReviewer_v2.py](src/ART%20Q%20Control/CaseReviewer_v2.py)**
   - Current code tries to go back but has index logic issues
   - Need to properly track case history
   - Implement stack-based navigation

2. **Add Navigation Breadcrumb**
   - Show: "Case 5 of 12"
   - Display case history path
   - Show progress visually

3. **Test Cases:**
   - Forward navigation (1→2→3)
   - Backward navigation (3→2→1)
   - Cannot go before first case
   - Index tracking stays accurate

---

## Merging Back to Original Files

When Phase 5 is complete and tested:

```bash
# Backup originals
mv Dispatcher.py Dispatcher.bak
mv AutoSender.py AutoSender.bak
mv CaseReviewer.py CaseReviewer.bak
mv CompaniesProcess.py CompaniesProcess.bak

# Promote v2 to production
mv Dispatcher_v2.py Dispatcher.py
mv AutoSender_v2.py AutoSender.py
mv CaseReviewer_v2.py CaseReviewer.py
mv CompaniesProcess_v2.py CompaniesProcess.py

# Rebuild .spec
pyinstaller ART_Q_Master_Stock.spec
```

---

## Development Notes

### Design Pattern
- **Isolation First:** Each mode can run independently
- **Explicit Control:** Users choose actions, not auto-triggered
- **Graceful Fallback:** Error messages guide users to missing data
- **Clean Separation:** Companies Process is self-contained

### Code Quality
- All original code preserved in original files
- Minimal changes needed for isolation
- Comments mark where changes were made
- Function signatures remain compatible

### Testing Strategy
1. Test each mode individually
2. Test mode transitions
3. Test error cases (missing files, etc.)
4. Test cleanup (driver closure, resource management)
5. Full integration test with all modes

---

## Files Tracking

### Phase 5 Status
| File | Phase 5.1 | Phase 5.2 | Phase 5.3 | Status |
|------|-----------|-----------|-----------|--------|
| Dispatcher_v2.py | ✅ | - | - | Done |
| AutoSender_v2.py | ✅ | - | - | Done |
| CaseReviewer_v2.py | ✅ | - | ✅ (Ready) | Ready |
| CompaniesProcess_v2.py | ✅ | ⚪ | - | Ready |
| utils/timezone_map.py | - | ⚪ | - | TODO |

---

## Quick Command Reference

```bash
# Test Dispatcher
python -m src.ART\ Q\ Control.Dispatcher_v2

# Test AutoSender
python -m src.ART\ Q\ Control.AutoSender_v2

# Test CaseReviewer
python -m src.ART\ Q\ Control.CaseReviewer_v2

# Test CompaniesProcess
python -m src.ART\ Q\ Control.CompaniesProcess_v2

# View changes
git diff Dispatcher.py Dispatcher_v2.py
```

---

## Documentation Files

- [PHASE_ROADMAP.md](PHASE_ROADMAP.md) - Overall project phases and plan
- [DEVELOPMENT_PROGRESS_V2.md](DEVELOPMENT_PROGRESS_V2.md) - Detailed progress tracking
- [V2_QUICK_START.md](V2_QUICK_START.md) - This file

---

**Ready to proceed with Phase 5.2 and Phase 5.3!**

Generated: 2026-01-27
