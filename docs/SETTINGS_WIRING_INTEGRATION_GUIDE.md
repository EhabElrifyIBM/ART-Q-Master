# Settings Wiring - How to Integrate with Dispatcher/CaseReviewer/AutoSender/CompaniesProcess

## Current Status: ⚠️ PARTIALLY WIRED

**What Works:**
- ✅ Settings dialog opens from Dispatcher
- ✅ Theme changes apply globally via `app.setStyleSheet()`
- ✅ Font size changes apply globally via `app.setFont()`

**What's Missing:**
- ❌ Individual windows DON'T respond to settings changes
- ❌ Each window has hardcoded local stylesheets that override global theme
- ❌ Font size changes don't affect local widget stylesheets
- ❌ Need explicit integration in each window

---

## Solution Provided

### Two New Infrastructure Files Created:

#### 1. **settings_observer.py** (Signal Broadcaster)
```python
class SettingsObserver(QObject):
    theme_changed = pyqtSignal(str)      # Broadcasts theme changes
    font_size_changed = pyqtSignal(float) # Broadcasts font size changes
    
    def notify_theme_changed(theme):     # Called by settings dialog
    def notify_font_size_changed(scale): # Called by settings dialog
```

**Purpose:** Central hub for settings change broadcasts
- Settings dialog calls `observer.notify_theme_changed()`
- All connected windows receive signal and can respond

#### 2. **settings_aware_dialog.py** (Mixin Class)
```python
class SettingsAwareMixin:
    def setup_settings_awareness():       # Call in __init__
    def on_theme_changed(theme):         # Override in subclass
    def on_font_size_changed(scale):     # Override in subclass
    def apply_dynamic_font_size(scale):  # Helper method
```

**Purpose:** Easy integration for any dialog/window
- Add to class inheritance: `class MyDialog(QDialog, SettingsAwareMixin):`
- Override `on_theme_changed()` and `on_font_size_changed()`
- Automatically receives settings broadcasts

---

## Integration Steps (For Each Window)

### For CaseReviewer_v2:

**Step 1:** Add mixin to class definition
```python
# BEFORE:
class CaseReviewerDialog(QDialog):

# AFTER:
from ui.settings_aware_dialog import SettingsAwareMixin

class CaseReviewerDialog(QDialog, SettingsAwareMixin):
```

**Step 2:** Add setup call in `__init__`
```python
def __init__(self, parent=None):
    super().__init__(parent)
    # ... existing code ...
    self.setup_settings_awareness()  # ← Add this line
```

**Step 3:** Override to handle theme changes
```python
def on_theme_changed(self, theme):
    """Respond to theme changes."""
    if theme == 'dark':
        # Update header, labels, etc. for dark mode
        self.case_info_label.setStyleSheet("color: #FFFFFF;")
    else:
        # Update for light mode
        self.case_info_label.setStyleSheet("color: #161616;")
```

**Step 4:** Override to handle font size changes
```python
def on_font_size_changed(self, scale):
    """Respond to font size changes."""
    self.apply_dynamic_font_size(scale)  # Updates this dialog's font
```

---

### For AutoSender_v2:

Same as CaseReviewer_v2:
1. Import mixin
2. Add to class inheritance
3. Call `setup_settings_awareness()`
4. Override `on_theme_changed()` and `on_font_size_changed()`

---

### For CompaniesProcess_v2:

Same integration process as above.

---

### For Dispatcher_v2:

Dispatcher already opens settings dialog. Just ensure it broadcasts:
```python
# In _show_settings_dialog(), the settings dialog now:
# 1. Calls app.setStyleSheet() for global theme
# 2. Broadcasts via observer.notify_theme_changed()
# 3. Broadcasts via observer.notify_font_size_changed()

# So Dispatcher receives broadcasts if it's registered as observer
```

---

## Current Data Flow

```
Settings Dialog (user changes theme/font)
    ↓
settings_dialog.py:
  - Calls app.setStyleSheet()  (global theme)
  - Calls app.setFont()        (global font)
  - Calls observer.notify_theme_changed()
  - Calls observer.notify_font_size_changed()
    ↓
settings_observer.py:
  - Broadcasts theme_changed signal
  - Broadcasts font_size_changed signal
    ↓
All registered listeners (windows):
  - Receive signal in on_theme_changed()
  - Receive signal in on_font_size_changed()
  - Update their local styles
  - Update their local widgets
```

---

## Why This Is Needed

**Problem:** Local stylesheets override global stylesheet
```python
# Global (works)
app.setStyleSheet("QLabel { color: white; }")

# Local (overrides global)
label.setStyleSheet("color: black;")  # ← This wins
```

**Solution:** Windows listen for changes and update their local stylesheets
```python
def on_theme_changed(self, theme):
    if theme == 'dark':
        label.setStyleSheet("color: white;")  # ← Update local style
```

---

## Testing the Integration

### Before Integration:
```
1. Open Dispatcher
2. Open Settings → Change theme to Dark
3. Settings dialog turns dark ✓
4. Dispatcher window stays light ✗
5. Open CaseReviewer → Still light ✗
```

### After Integration:
```
1. Open Dispatcher
2. Open Settings → Change theme to Dark
3. Settings dialog turns dark ✓
4. Dispatcher window turns dark ✓
5. Open CaseReviewer → Also dark ✓
6. All new windows open in dark theme ✓
```

---

## Quick Implementation Guide

### For Each Window (CaseReviewer, AutoSender, CompaniesProcess):

```python
# 1. Import at top of file
from ui.settings_aware_dialog import SettingsAwareMixin

# 2. Modify class definition
class MyDialog(QDialog, SettingsAwareMixin):  # ← Add mixin
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # ... existing code ...
        self.setup_settings_awareness()  # ← Add this
    
    # 3. Add these two methods (override for your specific widgets)
    def on_theme_changed(self, theme):
        """Called when theme changes."""
        # Update any widgets that have hardcoded colors
        if theme == 'dark':
            self.label.setStyleSheet("color: #FFF;")
        else:
            self.label.setStyleSheet("color: #000;")
    
    def on_font_size_changed(self, scale):
        """Called when font size changes."""
        self.apply_dynamic_font_size(scale)
```

---

## Files Involved

### Created (3):
1. `src/ui/settings_observer.py` - Signal broadcaster ✅
2. `src/ui/settings_aware_dialog.py` - Mixin class ✅
3. Updated `src/ui/settings_dialog.py` - Now broadcasts signals ✅

### To Modify (4):
1. `src/ART Q Control/Dispatcher_v2.py` - Add mixin + handlers
2. `src/ART Q Control/CaseReviewer_v2.py` - Add mixin + handlers
3. `src/ART Q Control/AutoSender_v2.py` - Add mixin + handlers
4. `src/ART Q Control/CompaniesProcess_v2.py` - Add mixin + handlers

---

## Key Concepts

### SettingsObserver (Centralized Broadcaster)
- Single instance that all windows listen to
- When settings change, it broadcasts signals
- Windows connect to these signals and respond

### SettingsAwareMixin (Reusable Mixin)
- Provides `setup_settings_awareness()` to connect to observer
- Provides `on_theme_changed()` and `on_font_size_changed()` for overriding
- Provides `apply_dynamic_font_size()` helper method

### Signal Flow
```
Settings → Observer → All Connected Windows → UI Updates
```

---

## Status Summary

| Component | Status | Action |
|-----------|--------|--------|
| Settings Dialog | ✅ Complete | Broadcasts signals |
| Observer | ✅ Complete | Receives from settings, broadcasts to windows |
| Mixin | ✅ Complete | Ready for any window to use |
| Dispatcher | ⚠️ Partial | Needs mixin integration |
| CaseReviewer | ⚠️ Partial | Needs mixin integration |
| AutoSender | ⚠️ Partial | Needs mixin integration |
| CompaniesProcess | ⚠️ Partial | Needs mixin integration |

---

## Next Steps

Ready to integrate? Follow this order:
1. **Start with CaseReviewer_v2** (simplest window)
   - Add mixin
   - Test theme/font changes
   
2. **Then AutoSender_v2** (similar structure)
   
3. **Then CompaniesProcess_v2** (more complex)
   
4. **Finally Dispatcher_v2** (if needed)

Each integration takes ~5-10 minutes and follows the same pattern.

