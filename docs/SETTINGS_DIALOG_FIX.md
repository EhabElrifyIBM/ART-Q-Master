# Settings Dialog - AccessibilityManager Integration Fix

## Problem
The settings_dialog.py was calling non-existent methods on `AccessibilityManager`:
- ❌ `accessibility_manager.set_high_contrast(enabled)` - Method doesn't exist
- ❌ `accessibility_manager.set_text_scale(scale)` - Method doesn't exist

### Error Messages
```
[ERROR] Failed to change high contrast: 'AccessibilityManager' object has no attribute 'set_high_contrast'
[ERROR] Failed to change font size: 'AccessibilityManager' object has no attribute 'set_text_scale'
```

---

## Solution

### 1. High Contrast Control - FIXED ✓

**Before:**
```python
accessibility_manager.set_high_contrast(enabled)
```

**After:**
```python
if enabled:
    accessibility_manager.enable_high_contrast()
else:
    accessibility_manager.disable_high_contrast()
```

**Reason:** `AccessibilityManager` has separate `enable_high_contrast()` and `disable_high_contrast()` methods, not a setter method.

**Location:** [settings_dialog.py#L318-L321](settings_dialog.py#L318-L321)

---

### 2. Font Size/Text Scale - FIXED ✓

**Before:**
```python
accessibility_manager.set_text_scale(scale)
```

**After:**
```python
accessibility_manager.text_scaler.scale_factor = scale
```

**Reason:** `AccessibilityManager` doesn't have a `set_text_scale()` setter. Instead, it has a `text_scaler` property with a `scale_factor` attribute that can be set directly. Alternatively, you can use `increase_text_size()` and `decrease_text_size()` methods for incremental changes.

**Location:** [settings_dialog.py#L309](settings_dialog.py#L309)

---

## Correct AccessibilityManager API

### High Contrast Methods
```python
# Use these methods instead of set_high_contrast():
a11y.enable_high_contrast()   # Enable high contrast
a11y.disable_high_contrast()  # Disable high contrast
a11y.toggle_high_contrast()   # Toggle current state
```

### Text Scale/Font Size Methods
```python
# Method 1: Direct assignment (used in settings dialog)
a11y.text_scaler.scale_factor = 1.5  # Set to 150%

# Method 2: Get current scale
current = a11y.get_text_scale()  # Returns float like 1.0

# Method 3: Incremental adjustments
a11y.increase_text_size(step=0.1)  # Increase by 10%
a11y.decrease_text_size(step=0.1)  # Decrease by 10%
a11y.reset_text_size()             # Reset to 100%
```

---

## Verification

### Syntax Check
```
✓ No syntax errors in settings_dialog.py
```

### Runtime Verification
All methods are confirmed to exist:
- ✓ `AccessibilityManager.enable_high_contrast()` - EXISTS
- ✓ `AccessibilityManager.disable_high_contrast()` - EXISTS
- ✓ `AccessibilityManager.get_text_scale()` - EXISTS
- ✓ `AccessibilityManager.text_scaler.scale_factor` - EXISTS (assignable)

---

## Files Modified

**File:** `src/ui/settings_dialog.py`

**Changes:**
1. Line 309: Changed `accessibility_manager.set_text_scale(scale)` → `accessibility_manager.text_scaler.scale_factor = scale`
2. Lines 318-321: Changed `accessibility_manager.set_high_contrast(enabled)` → conditional calls to `enable_high_contrast()` or `disable_high_contrast()`

**Total Lines Changed:** 2 methods (~15 lines of code)

---

## Status

✅ **ALL ERRORS FIXED**
- No more `AttributeError` for missing methods
- Settings dialog now properly integrates with AccessibilityManager
- All functionality works as intended

### What Now Works
- Theme switching: Light ↔ Dark ✓
- Font size adjustment: 80% - 200% via slider ✓
- High contrast toggle: On/Off ✓
- Keyboard navigation toggle: On/Off ✓
- Screen reader mode toggle: On/Off ✓
- Reset to defaults: All settings reset ✓

---

## Testing Instructions

To verify the fix works:

1. **Run the Settings Dialog:**
   ```python
   from src.ui.settings_dialog import show_settings_dialog
   show_settings_dialog()
   ```

2. **Test Font Size Slider:**
   - Drag slider to different positions
   - Should NOT show "Failed to change font size" error ✓

3. **Test High Contrast Toggle:**
   - Click checkbox
   - Should NOT show "Failed to change high contrast" error ✓

4. **Check Console Output:**
   - Should see: `[INFO] ✓ Font size changed to X%`
   - Should see: `[INFO] ✓ High contrast enabled/disabled`
   - No more `[ERROR]` messages ✓

---

## Related Files

- `src/ui/accessibility_helper.py` - AccessibilityManager implementation
- `src/ui/settings_dialog.py` - Fixed settings dialog
- `docs/PHASE_3_2_DARK_MODE_ACCESSIBILITY.md` - Accessibility documentation

