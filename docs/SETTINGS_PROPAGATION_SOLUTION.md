# Settings Propagation Solution - ART Q Control Suite
**Phase: Settings Bus Integration Fix**  
**Scope: src_v2/ART Q Control ONLY**  
**Date: 2026-05-07**

---

## Executive Summary

This document provides a focused, practical solution for fixing settings propagation issues in the ART Q Control suite. The V2SettingsBus infrastructure exists and works correctly - we just need to wire all dialogs properly.

### Current State Analysis

**✅ Working Correctly:**
- [`Dispatcher_v2.py`](../src_v2/ART Q Control/Dispatcher_v2.py) - Best integrated, subscribes to both `theme_changed` and `font_size_changed`
- [`config_loader.py`](../src_v2/ART Q Control/config_loader.py) - Subscribes to `theme_changed` and `font_preset_changed`
- [`CompaniesProcess_v2.py`](../src_v2/ART Q Control/CompaniesProcess_v2.py) - Main dialogs subscribe to both signals

**⚠️ Partially Working:**
- [`AutoSender_v2.py`](../src_v2/ART Q Control/AutoSender_v2.py) - Theme subscriptions present, **font subscriptions MISSING**
- [`CaseReviewer_v2.py`](../src_v2/ART Q Control/CaseReviewer_v2.py) - Main dialog integrated, **utility dialogs use snapshots**

**❌ Not Integrated:**
- [`Main.py`](../src_v2/ART Q Control/Main.py) - Hardcoded styles, no bus integration
- Legacy dialogs in [`SharedFunctions.py`](../src_v2/ART Q Control/SharedFunctions.py)

### Key Issues Identified

1. **Signal Inconsistency**: Mixed use of `font_size_changed` vs `font_preset_changed`
2. **Missing Font Subscriptions**: Many dialogs subscribe to theme but not font changes
3. **Snapshot Values**: Dialogs read `font_size` at creation but don't re-subscribe
4. **Hardcoded Styles**: Welcome/config dialogs have no dynamic styling

---

## Standard Subscription Pattern

### Pattern A: Full V2 Integration (Recommended)

Use this for all modernized dialogs with V2TypographyMixin:

```python
class MyDialog(QDialog, V2TypographyMixin):
    """Modern dialog with full V2 integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)
        
        # Get V2 services
        self.theme_manager = get_theme_manager()
        self.settings_bus = get_v2_settings_bus()
        self.theme_service = V2ThemeService()
        
        # Setup UI first
        self._setup_ui()
        
        # Apply initial theme/typography
        self._apply_theme()
        self._apply_typography()
        
        # Subscribe to changes (BOTH signals required)
        self.settings_bus.theme_changed.connect(self._on_theme_changed)
        self.settings_bus.font_size_changed.connect(self._on_font_changed)
    
    def _setup_ui(self):
        """Create UI elements."""
        # Create widgets with object names for styling
        self.title_label = QLabel("Dialog Title")
        self.title_label.setObjectName("dialogTitle")
        # ... more UI setup
    
    def _apply_theme(self):
        """Apply theme-aware styling."""
        theme_mode = self.settings_bus.theme
        colors = self.theme_service.colors_for(theme_mode)
        
        # Generate stylesheet using current theme colors
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['window_bg']};
            }}
            QLabel#dialogTitle {{
                color: {colors['text_primary']};
            }}
            /* ... more styles */
        """)
    
    def _apply_typography(self):
        """Apply typography to all widgets."""
        # Use V2TypographyMixin methods
        self.apply_typography_to_widget(self.title_label, 'h2', QFont.Bold)
        # ... apply to other widgets
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change - reapply theme."""
        self._apply_theme()
    
    def _on_font_changed(self, size: int):
        """Handle font size change - reapply typography."""
        self._apply_typography()
```

### Pattern B: Legacy Dialog Upgrade (Minimal Changes)

Use this for legacy dialogs that can't be fully modernized:

```python
class LegacyDialog(QDialog):
    """Legacy dialog with minimal V2 integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Get settings bus only
        from ui.services import get_v2_settings_bus, V2ThemeService
        self.settings_bus = get_v2_settings_bus()
        self.theme_service = V2ThemeService()
        
        # Get current values
        self.font_size = self.settings_bus.font_size
        self.theme = self.settings_bus.theme
        
        self._setup_ui()
        self._apply_styling()
        
        # Subscribe to changes
        self.settings_bus.theme_changed.connect(self._on_settings_changed)
        self.settings_bus.font_size_changed.connect(self._on_settings_changed)
    
    def _setup_ui(self):
        """Create UI elements."""
        # ... existing UI code
    
    def _apply_styling(self):
        """Apply current theme and font size."""
        colors = self.theme_service.colors_for(self.theme)
        
        # Apply font size to all widgets
        font = QFont()
        font.setPointSize(self.font_size)
        self.setFont(font)
        
        # Apply theme colors
        self.setStyleSheet(f"""
            QDialog {{ background-color: {colors['window_bg']}; }}
            /* ... more styles */
        """)
    
    def _on_settings_changed(self, value):
        """Handle any settings change."""
        # Update cached values
        self.font_size = self.settings_bus.font_size
        self.theme = self.settings_bus.theme
        # Reapply styling
        self._apply_styling()
```

---

## File-by-File Modification Plan

### Priority 1: AutoSender_v2.py (Most Used Tool)

**Status**: Theme ✅ | Font ❌

**Dialogs to Fix:**
1. `ModernResumeDialog` (line 510)
2. `ModernFileSelectionDialog` (line 752)
3. `ModernCompletionDialog` (line 1053)

**Changes Required:**

```python
# In each dialog's __init__, ADD font subscription:
self.settings_bus.font_size_changed.connect(self._on_font_changed)

# ADD new handler method:
def _on_font_changed(self, size: int):
    """Handle font size change."""
    self._apply_typography()

# ENSURE _apply_typography exists and updates all widgets:
def _apply_typography(self):
    """Apply typography to all widgets."""
    self.apply_typography_to_widget(self.header, 'h2', QFont.Bold)
    self.apply_typography_to_widget(self.subtitle, 'body')
    # ... apply to ALL text widgets
```

**Estimated Impact**: High - AutoSender is heavily used, 3 dialogs affected

---

### Priority 2: CaseReviewer_v2.py (Critical Tool)

**Status**: Main dialog ✅ | Utility dialogs ❌

**Dialogs to Fix:**
1. `EnhancedResumeDialog` (line 188) - Uses snapshot values
2. `CallOutcomeDialog` (line 981) - Uses snapshot `font_size` variable

**Changes Required:**

**EnhancedResumeDialog:**
```python
class EnhancedResumeDialog(QDialog, V2TypographyMixin):
    def __init__(self, ...):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)
        
        # ADD V2 services
        self.settings_bus = get_v2_settings_bus()
        self.theme_service = V2ThemeService()
        
        self._setup_ui()
        self._apply_theme()
        self._apply_typography()
        
        # ADD subscriptions
        self.settings_bus.theme_changed.connect(self._on_theme_changed)
        self.settings_bus.font_size_changed.connect(self._on_font_changed)
    
    # ADD handlers
    def _apply_theme(self):
        """Apply theme-aware styling."""
        colors = self.theme_service.colors_for(self.settings_bus.theme)
        # ... generate stylesheet
    
    def _apply_typography(self):
        """Apply typography."""
        # Use V2TypographyMixin methods
    
    def _on_theme_changed(self, theme: str):
        self._apply_theme()
    
    def _on_font_changed(self, size: int):
        self._apply_typography()
```

**CallOutcomeDialog:**
```python
# REPLACE snapshot usage (line 995):
# OLD: self.setFont(QFont('IBM Plex Sans', font_size))
# NEW: self.setFont(QFont('IBM Plex Sans', self.settings_bus.font_size))

# ADD at start of __init__:
from ui.services import get_v2_settings_bus, V2ThemeService
self.settings_bus = get_v2_settings_bus()
self.theme_service = V2ThemeService()

# ADD subscriptions before dialog.exec_():
self.settings_bus.theme_changed.connect(self._on_settings_changed)
self.settings_bus.font_size_changed.connect(self._on_settings_changed)

# ADD handler:
def _on_settings_changed(self, value):
    """Handle settings change."""
    # Reapply font to all widgets
    font = QFont('IBM Plex Sans', self.settings_bus.font_size)
    self.setFont(font)
    # Reapply theme colors
    colors = self.theme_service.colors_for(self.settings_bus.theme)
    # ... update stylesheet
```

**Estimated Impact**: High - CaseReviewer is critical, 2 dialogs affected

---

### Priority 3: CompaniesProcess_v2.py (Verify & Fix)

**Status**: Mostly integrated ✅ | Needs verification

**Dialogs to Verify:**
1. `CompaniesResumeDialog` (line 157) - Check subscriptions
2. `PerCaseOutcomesDialog` (line 333) - Check subscriptions

**Verification Checklist:**
- [ ] Both dialogs inherit from `V2TypographyMixin`
- [ ] Both subscribe to `theme_changed` AND `font_size_changed`
- [ ] Both have `_apply_theme()` and `_apply_typography()` methods
- [ ] Both have `_on_theme_changed()` and `_on_font_changed()` handlers

**If Missing**: Apply Pattern A from above

**Estimated Impact**: Medium - Already mostly working, verification needed

---

### Priority 4: Dispatcher_v2.py (Already Working)

**Status**: ✅ Best integrated

**Action**: **NO CHANGES NEEDED** - Use as reference implementation

**Why It Works:**
- Subscribes to both `theme_changed` and `font_size_changed`
- Has proper `_apply_theme()` and `_apply_typography()` methods
- Uses V2TypographyMixin correctly

---

### Priority 5: config_loader.py (Needs Font Signal Fix)

**Status**: Theme ✅ | Font uses wrong signal ⚠️

**Issue**: Uses `font_preset_changed` instead of `font_size_changed`

**Changes Required:**

```python
# Line 203: REPLACE
# OLD: self.settings_bus.font_preset_changed.connect(self._on_font_changed)
# NEW: self.settings_bus.font_size_changed.connect(self._on_font_changed)

# UPDATE handler to accept int instead of str:
def _on_font_changed(self, size: int):  # Was: preset: str
    """Handle font size change."""
    self._apply_typography()
```

**Estimated Impact**: Low - Config dialog rarely shown, but should be consistent

---

### Priority 6: Main.py (Legacy - Low Priority)

**Status**: ❌ Not integrated, hardcoded styles

**Recommendation**: **DEFER** - This is legacy code, focus on v2 files first

**If Time Permits**: Apply Pattern B (Legacy Dialog Upgrade)

---

## Signal Standardization Decision

### ✅ DECISION: Use `font_size_changed` Everywhere

**Rationale:**
1. **Consistency**: Most dialogs already use `font_size_changed`
2. **Direct Control**: Pixel size is more predictable than preset conversion
3. **Simpler Logic**: No need to convert preset → pixels in each dialog
4. **Bus Design**: `V2SettingsBus.font_size` property returns int (pixels)

**Migration Path:**
- Replace all `font_preset_changed` subscriptions with `font_size_changed`
- Update handlers to accept `int` instead of `str`
- Remove preset-to-pixel conversion logic from dialogs

---

## Testing Checklist

### Per-Tool Testing

**For Each Tool (AutoSender, CaseReviewer, CompaniesProcess):**

1. **Launch Tool**
   - [ ] Tool opens without errors
   - [ ] Initial theme applied correctly
   - [ ] Initial font size applied correctly

2. **Change Theme (Light → Dark)**
   - [ ] Open Settings dialog
   - [ ] Change theme to Dark
   - [ ] Verify tool dialog updates immediately
   - [ ] Check all text colors readable
   - [ ] Check all backgrounds updated

3. **Change Theme (Dark → Light)**
   - [ ] Change theme back to Light
   - [ ] Verify tool dialog updates immediately
   - [ ] Check all colors reverted correctly

4. **Change Font Size (Normal → Large)**
   - [ ] Open Settings dialog
   - [ ] Change font size to Large
   - [ ] Verify all text in tool dialog scales up
   - [ ] Check layout doesn't break
   - [ ] Check buttons still readable

5. **Change Font Size (Large → Small)**
   - [ ] Change font size to Small
   - [ ] Verify all text scales down
   - [ ] Check nothing gets cut off

6. **Test All Dialogs**
   - [ ] Open each dialog in the tool
   - [ ] Verify theme/font applied to each
   - [ ] Change settings while dialog open
   - [ ] Verify dialog updates live

### Integration Testing

**Cross-Tool Testing:**

1. **Settings Persistence**
   - [ ] Set theme to Dark, font to Large
   - [ ] Close application
   - [ ] Reopen application
   - [ ] Launch each tool
   - [ ] Verify settings persisted

2. **Multiple Tools Open**
   - [ ] Open AutoSender
   - [ ] Open CaseReviewer (separate instance)
   - [ ] Change theme in Settings
   - [ ] Verify BOTH tools update

3. **Rapid Changes**
   - [ ] Open Settings dialog
   - [ ] Rapidly toggle theme multiple times
   - [ ] Verify no crashes or visual glitches
   - [ ] Rapidly change font size
   - [ ] Verify smooth updates

### Regression Testing

**Ensure No Breakage:**

1. **Core Functionality**
   - [ ] AutoSender can process cases
   - [ ] CaseReviewer can review cases
   - [ ] CompaniesProcess can handle companies
   - [ ] All buttons still work
   - [ ] All inputs still functional

2. **Performance**
   - [ ] No noticeable lag when changing settings
   - [ ] Dialogs open quickly
   - [ ] No memory leaks from subscriptions

---

## Risk Mitigation Strategies

### Risk 1: Breaking Existing Functionality

**Mitigation:**
- Make changes incrementally, one file at a time
- Test each file thoroughly before moving to next
- Keep backup of working code
- Use git branches for each file modification

**Rollback Plan:**
- If issues found, revert specific file
- Each file is independent, can rollback individually

### Risk 2: Signal Connection Leaks

**Mitigation:**
- Dialogs are short-lived, connections auto-cleanup on deletion
- Use `QDialog.finished` signal to explicitly disconnect if needed
- Test with multiple dialog open/close cycles

**Detection:**
- Monitor for duplicate signal emissions
- Check for memory growth with repeated dialog usage

### Risk 3: Theme/Font Mismatch

**Mitigation:**
- Always call `_apply_theme()` AND `_apply_typography()` in `__init__`
- Always subscribe to BOTH signals
- Use consistent method names across all dialogs

**Validation:**
- Visual inspection of each dialog
- Automated screenshot comparison (if time permits)

### Risk 4: Legacy Code Interference

**Mitigation:**
- Focus on v2 files only (AutoSender_v2, CaseReviewer_v2, etc.)
- Don't modify legacy files (Main.py, SharedFunctions.py) unless necessary
- Keep v2 and legacy code paths separate

**Boundary:**
- Only touch files in `src_v2/ART Q Control/` with `_v2` suffix
- Leave `src/ART Q Control/` untouched

---

## Implementation Order

### Phase 1: AutoSender_v2.py (Day 1)
**Why First**: Most used tool, clear issues, high impact

1. Add font subscriptions to all 3 dialogs
2. Add `_on_font_changed` handlers
3. Ensure `_apply_typography` exists and works
4. Test thoroughly with all dialogs

**Success Criteria**: All AutoSender dialogs respond to theme AND font changes

---

### Phase 2: CaseReviewer_v2.py (Day 2)
**Why Second**: Critical tool, needs utility dialog fixes

1. Upgrade `EnhancedResumeDialog` to full V2 integration
2. Fix `CallOutcomeDialog` snapshot usage
3. Verify main dialog still works
4. Test all dialog interactions

**Success Criteria**: All CaseReviewer dialogs respond to settings changes

---

### Phase 3: CompaniesProcess_v2.py (Day 3)
**Why Third**: Mostly working, needs verification

1. Verify both dialogs have proper subscriptions
2. Fix any missing handlers
3. Test company selection flow
4. Test per-case outcomes dialog

**Success Criteria**: All CompaniesProcess dialogs confirmed working

---

### Phase 4: config_loader.py (Day 4)
**Why Fourth**: Low priority, but should be consistent

1. Change `font_preset_changed` to `font_size_changed`
2. Update handler signature
3. Test config setup dialog
4. Verify settings persistence

**Success Criteria**: Config dialog uses consistent signal

---

### Phase 5: Integration Testing (Day 5)
**Why Last**: Verify everything works together

1. Run full testing checklist
2. Test cross-tool scenarios
3. Test settings persistence
4. Document any remaining issues

**Success Criteria**: All tools pass testing checklist

---

## Code Patterns Reference

### Getting V2 Services

```python
from ui.theme_manager import get_theme_manager
from ui.services import get_v2_settings_bus, V2ThemeService
from ui.typography_mixin import V2TypographyMixin

# In __init__:
self.theme_manager = get_theme_manager()
self.settings_bus = get_v2_settings_bus()
self.theme_service = V2ThemeService()
```

### Subscribing to Signals

```python
# ALWAYS subscribe to BOTH signals:
self.settings_bus.theme_changed.connect(self._on_theme_changed)
self.settings_bus.font_size_changed.connect(self._on_font_changed)
```

### Handler Methods

```python
def _on_theme_changed(self, theme: str):
    """Handle theme change."""
    self._apply_theme()

def _on_font_changed(self, size: int):
    """Handle font size change."""
    self._apply_typography()
```

### Applying Theme

```python
def _apply_theme(self):
    """Apply theme-aware styling."""
    theme_mode = self.settings_bus.theme
    colors = self.theme_service.colors_for(theme_mode)
    
    self.setStyleSheet(f"""
        QDialog {{
            background-color: {colors['window_bg']};
        }}
        /* ... more styles using colors dict */
    """)
```

### Applying Typography

```python
def _apply_typography(self):
    """Apply typography to all widgets."""
    # Using V2TypographyMixin:
    self.apply_typography_to_widget(self.title, 'h2', QFont.Bold)
    self.apply_typography_to_widget(self.body, 'body')
    self.apply_typography_to_widget(self.button, 'button')
    
    # Or manually:
    font = self.get_font('body')
    self.some_widget.setFont(font)
```

---

## Success Metrics

### Quantitative Metrics

- **100%** of v2 dialogs subscribe to both theme and font signals
- **0** hardcoded font sizes in v2 dialogs
- **0** snapshot-based theme/font usage in v2 dialogs
- **<100ms** response time for settings changes

### Qualitative Metrics

- All dialogs update immediately when settings change
- No visual glitches during theme transitions
- Consistent styling across all tools
- Improved user experience with live updates

---

## Maintenance Guidelines

### For Future Dialog Development

**When creating a new dialog:**

1. **Always** inherit from `V2TypographyMixin` if using modern styling
2. **Always** subscribe to both `theme_changed` and `font_size_changed`
3. **Always** implement `_apply_theme()` and `_apply_typography()`
4. **Never** use hardcoded colors or font sizes
5. **Never** read `font_size` once and cache it

**Template for new dialogs:**

```python
class NewDialog(QDialog, V2TypographyMixin):
    """New dialog with V2 integration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)
        
        # Get services
        self.settings_bus = get_v2_settings_bus()
        self.theme_service = V2ThemeService()
        
        # Setup
        self._setup_ui()
        self._apply_theme()
        self._apply_typography()
        
        # Subscribe
        self.settings_bus.theme_changed.connect(self._on_theme_changed)
        self.settings_bus.font_size_changed.connect(self._on_font_changed)
    
    def _setup_ui(self):
        """Create UI elements."""
        pass
    
    def _apply_theme(self):
        """Apply theme-aware styling."""
        colors = self.theme_service.colors_for(self.settings_bus.theme)
        # ... generate stylesheet
    
    def _apply_typography(self):
        """Apply typography."""
        # ... apply fonts to widgets
    
    def _on_theme_changed(self, theme: str):
        self._apply_theme()
    
    def _on_font_changed(self, size: int):
        self._apply_typography()
```

---

## Appendix: Current State Summary

### Files Analyzed

| File | Dialogs | Theme Sub | Font Sub | Status |
|------|---------|-----------|----------|--------|
| Dispatcher_v2.py | 1 | ✅ | ✅ | Perfect |
| config_loader.py | 1 | ✅ | ⚠️ | Wrong signal |
| AutoSender_v2.py | 3 | ✅ | ❌ | Missing font |
| CaseReviewer_v2.py | 3 | ⚠️ | ⚠️ | Mixed |
| CompaniesProcess_v2.py | 2 | ✅ | ✅ | Verify |
| Main.py | 3+ | ❌ | ❌ | Legacy |

### Signal Usage

| Signal | Files Using | Correct Usage |
|--------|-------------|---------------|
| `theme_changed` | 5/6 | ✅ Standard |
| `font_size_changed` | 3/6 | ✅ Recommended |
| `font_preset_changed` | 2/6 | ⚠️ Deprecated |

---

**Document Version**: 1.0  
**Last Updated**: 2026-05-07  
**Author**: Bob (Plan Mode)  
**Status**: Ready for Implementation