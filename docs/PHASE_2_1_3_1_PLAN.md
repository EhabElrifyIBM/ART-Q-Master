# 📋 PHASE 2.1 & 3.1 IMPLEMENTATION PLAN

**Date:** January 27, 2026  
**Session:** 14  
**Objective:** Implement Base Dialog Architecture and Enhanced Dialog System

---

## Phase 2.1: Base Dialog Architecture

### Goal
Create a reusable base dialog component to eliminate duplication across dialog implementations.

### Components to Create
1. **BaseDialog.py** - Base class for all PyQt5 dialogs
   - Common styling and layout
   - Standard button handling
   - Dialog lifecycle management
   - Common methods for open/close/validation

2. **DialogComponents.py** - Common UI elements
   - Styled buttons
   - Styled labels
   - Styled input fields
   - Common layouts

### Implementation Steps
1. Create `src/ui/components/base_dialog.py`
2. Create `src/ui/components/dialog_components.py`
3. Document base class usage
4. Prepare for Phase 3.1 integration

### Time Estimate
- 1-2 hours

### Files Modified
- New: `src/ui/components/base_dialog.py`
- New: `src/ui/components/dialog_components.py`
- Documentation: `docs/PHASE_2_1_BASE_DIALOG_ARCHITECTURE.md`

---

## Phase 3.1: Enhanced Dialog System

### Goal
Implement enhanced dialogs for Case Reviewer and Company Process using the base dialog architecture.

### Dialogs to Enhance
1. **Case Review Dialog** (CaseReviewer.py)
   - Enhanced layout with company metadata
   - Previous/Next case navigation
   - Better visual feedback

2. **Company Email Template Dialog**
   - Email preview before sending
   - Template selection UI
   - Attachment handling

3. **Per-Case Feedback Dialog**
   - Structured feedback form
   - Case information display
   - Validation before submission

### Implementation Steps
1. Create enhanced case review dialog component
2. Create company email template preview dialog
3. Create per-case feedback dialog
4. Integrate into AutoSender_v2.py and CaseReviewer_v2.py
5. Test all dialog interactions
6. Update documentation

### Time Estimate
- 2-3 hours

### Files Modified
- New: `src/ui/components/case_review_dialog.py`
- New: `src/ui/components/company_email_dialog.py`
- New: `src/ui/components/feedback_dialog.py`
- Modified: `src/ART Q Control/CaseReviewer_v2.py` (dialog integration)
- Modified: `src/ART Q Control/AutoSender_v2.py` (dialog integration)

---

## Total Effort
- **Phase 2.1 (Base Dialogs):** 1-2 hours
- **Phase 3.1 (Enhanced Dialogs):** 2-3 hours
- **Total:** 3-5 hours (1-2 sessions)

---

## Success Criteria
✅ Base dialog class implemented with common functionality  
✅ Dialog components created and reusable  
✅ All three enhanced dialogs created  
✅ Dialogs integrated into v2 files  
✅ No syntax errors in any new files  
✅ Documentation complete

---

## Next Steps After This
1. Phase 4.3 - Better Error Logging & Recovery
2. Phase 3.2 - Dark Mode & Accessibility
3. Phase 1.2 - SmartWait Optimization
4. Phase 1.1 - Application Closure & Crash Handling
5. Deployment & Production Release

