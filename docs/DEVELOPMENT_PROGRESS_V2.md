# ART Q Master - Development Progress (v2 Branch)

## Overview
Started development on v2 branch with cloned files to preserve original functionality while implementing Phase 5 and Phase 3 updates.

---

## Files Created/Modified

### Phase 5.1: Company Process Isolation - COMPLETED ✅

#### New Files
- [Dispatcher_v2.py](src/ART%20Q%20Control/Dispatcher_v2.py)
  - Added new "Company Process" button to dispatcher menu (Mode 5)
  - Moved company process control from auto-triggered to explicit user selection
  - Company Process button styled with distinct color (#C2185B - Pink)
  - Support mode checkbox now works with Company Process

#### Cloned Files (Ready for Enhancement)
- [AutoSender_v2.py](src/ART%20Q%20Control/AutoSender_v2.py)
  - Company process removed from end of AutoSender flow
  - Updated header to reflect isolation
  - Now exits cleanly after processing NEW cases
  
- [CaseReviewer_v2.py](src/ART%20Q%20Control/CaseReviewer_v2.py)
  - No auto-trigger of Company Process
  - Updated header to reflect isolation
  - Independent execution path

- [CompaniesProcess_v2.py](src/ART%20Q%20Control/CompaniesProcess_v2.py)
  - **NEW:** Added `run_companies_process_standalone()` function for isolated execution
  - Can now be called directly from Dispatcher without AutoSender/CaseReviewer dependency
  - Proper initialization: Dialer login → CRM window switch → cache loading
  - Error handling for missing Companies sheet
  - Updated header to reflect isolation

### Implementation Details

**Dispatcher Flow Changes:**
```
Before (v1):
AutoSender → (auto) Companies Process → Dispatcher

After (v2):
AutoSender → Dispatcher (user selects next action)
  ├─ Case Reviewer
  ├─ Company Process (NEW)
  ├─ Update Configuration
  └─ Main Menu

Company Process → Standalone flow → Dispatcher
```

**Key Changes in CompaniesProcess_v2.py:**
- New function: `run_companies_process_standalone(support_agent=None)`
- Initializes its own driver and Dialer login
- Loads cache from get_todays_cache_path(mode="companies")
- Checks for Companies sheet before processing
- Provides user feedback if no data available
- Proper cleanup with driver.quit() and Windows inhibit disable

---

## Next Steps: Phase 5.2 & 5.3

### Phase 5.2: Company Metadata Implementation
**Files to modify:**
- [utils/timezone_map.py](utils/timezone_map.py) - NEW FILE
  - Create timezone mapping for all US states and Canadian provinces
  - Map: Region → UTC offset
  - Used for local time calculation

- [CompaniesProcess_v2.py](src/ART%20Q%20Control/CompaniesProcess_v2.py)
  - Extract metadata from Excel: Name, Company Name, Email, State/Province
  - Display in UI during company processing
  - Calculate local time based on timezone offset

### Phase 5.3: Previous Case Navigation Fix
**Files to modify:**
- [CaseReviewer_v2.py](src/ART%20Q%20Control/CaseReviewer_v2.py)
  - Fix "Previous Case" button functionality (currently broken)
  - Implement breadcrumb navigation display
  - Show current position in case list

---

## Testing Checklist for Phase 5.1

- [ ] Dispatcher_v2.py loads without errors
- [ ] New "Company Process" button appears in Mode Selector
- [ ] Support mode checkbox works with Company Process
- [ ] AutoSender_v2 exits cleanly without triggering Companies
- [ ] CaseReviewer_v2 exits cleanly without triggering Companies
- [ ] Dispatcher → Company Process → standalone execution works
- [ ] Company Process finds and processes Companies sheet from cache
- [ ] Proper error message if no Companies sheet exists
- [ ] Driver and resources clean up properly

---

## Architecture Notes

### v2 Branch Strategy
- Original files remain untouched for reference and rollback
- All enhancements in _v2 versions
- Once tested and stable, v2 versions can replace originals
- All imports remain compatible

### Phase Separation Benefits
- **Phase 5.1 (Complete):** User control over Company Process execution
- **Phase 5.2 (Next):** Enhanced data display with metadata
- **Phase 5.3 (Next):** Better UX with navigation fixes

### Integration Points
- SharedFunctions - no changes needed
- config_manager - compatible
- Excel handling - backward compatible
- PyQt5 dialogs - enhanced versions in later phases

---

## Known Issues & Considerations

1. **Timezone Map**: Will need to be created with proper UTC offset calculations
2. **Navigation Breadcrumb**: Requires state tracking across case navigation
3. **Previous Case Logic**: Current implementation doesn't properly handle backward navigation

---

## Progress Summary

| Phase | Component | Status | Completion |
|-------|-----------|--------|------------|
| 5.1   | Company Process Isolation | ✅ Complete | 100% |
| 5.2   | Company Metadata | ⚪ In Progress | 0% |
| 5.3   | Navigation Fixes | ⚪ Not Started | 0% |
| 3     | UI/UX Enhancements | ⚪ Not Started | 0% |

---

## Build & Deployment

To use v2 branch:
1. Use Dispatcher_v2.py instead of Dispatcher.py
2. Imports will automatically use AutoSender_v2.py, etc.
3. Original files remain as backup
4. Once stable, rename v2 files to originals and rebuild .spec

---

Generated: 2026-01-27
Version: v2 (Phase 5 - Enhanced)
