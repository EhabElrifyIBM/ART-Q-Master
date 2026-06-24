# Button Components API Documentation

## Overview

Modern button components following IBM Carbon Design principles with Phase 5.1 enhancements. All buttons support theming, loading states, icons, and meet WCAG 2.1 AA accessibility standards.

## Button Variants

### PrimaryButton
Main action buttons with high visual emphasis. Use for the primary action in a view or dialog.

**Visual Style:** Filled background with primary color
**Use Case:** Save, Submit, Confirm, Create

### SecondaryButton
Secondary action buttons with medium emphasis. Use for actions that complement the primary action.

**Visual Style:** Outlined with transparent background
**Use Case:** Cancel, Back, Skip, Learn More

### GhostButton
Tertiary action buttons with low emphasis. Use for less important actions or when minimal visual weight is needed.

**Visual Style:** Text only, no border or background
**Use Case:** View Details, Dismiss, Close

### DangerButton
Destructive action buttons. Use for actions that delete, remove, or have irreversible consequences.

**Visual Style:** Filled background with danger color (red)
**Use Case:** Delete, Remove, Discard, Uninstall

---

## API Reference

### Constructor

```python
button = PrimaryButton(
    text: str = "",
    parent: Optional[QWidget] = None,
    icon_name: Optional[str] = None,
    icon_position: str = "left"
)
```

**Parameters:**
- `text` (str): Button label text
- `parent` (QWidget, optional): Parent widget
- `icon_name` (str, optional): Icon identifier for button icon
- `icon_position` (str): Icon position - "left" or "right" (default: "left")

### Properties

#### Minimum Size
All buttons meet WCAG 2.1 AA touch target requirements:
- **Minimum Height:** 44px
- **Minimum Width:** 44px

#### Focus Indicator
- **Outline Width:** 3px
- **Outline Offset:** 2px
- **Color:** Primary color (theme-aware)

### Methods

#### set_loading(loading: bool)
Set button loading state. When loading, button is disabled and shows animated spinner.

```python
save_btn = PrimaryButton("Save")
save_btn.set_loading(True)  # Show loading state
# ... perform async operation ...
save_btn.set_loading(False)  # Hide loading state
```

#### is_loading() -> bool
Check if button is in loading state.

```python
if not save_btn.is_loading():
    save_btn.click()
```

#### set_icon(icon_name: Optional[str], position: str = "left")
Set or update button icon.

```python
btn = PrimaryButton("Save")
btn.set_icon("save", "left")  # Add icon on left
btn.set_icon(None)  # Remove icon
```

#### set_theme(theme_mode: str)
Update button theme. Automatically called when theme changes.

```python
btn.set_theme("dark")  # Switch to dark theme
btn.set_theme("light")  # Switch to light theme
```

#### set_font_preset(preset: FontSizePreset)
Update font size preset. Automatically called when font preset changes.

```python
from ui.typography import FontSizePreset
btn.set_font_preset(FontSizePreset.LARGE)
```

### Signals

#### clicked
Emitted when button is clicked (inherited from QPushButton).

```python
def on_save():
    print("Save clicked")

save_btn = PrimaryButton("Save")
save_btn.clicked.connect(on_save)
```

### States

#### Default State
Normal appearance when button is enabled and not interacted with.

#### Hover State
Slightly darker/lighter background when mouse hovers over button.

#### Active/Pressed State
Even darker/lighter background when button is being clicked.

#### Focus State
3px outline when button has keyboard focus (Tab navigation).

#### Disabled State
Reduced opacity and muted colors when button is disabled.
- Cursor changes to "not-allowed"
- Click events are blocked

#### Loading State
Animated spinner displayed, button is disabled.
- Text remains visible
- Spinner animates at 20 FPS

---

## Usage Examples

### Basic Usage

```python
from ui.components_v2 import PrimaryButton, SecondaryButton, GhostButton, DangerButton

# Create primary button
save_btn = PrimaryButton("Save Changes")
save_btn.clicked.connect(on_save)

# Create secondary button
cancel_btn = SecondaryButton("Cancel")
cancel_btn.clicked.connect(on_cancel)

# Create ghost button
details_btn = GhostButton("View Details")
details_btn.clicked.connect(on_view_details)

# Create danger button
delete_btn = DangerButton("Delete")
delete_btn.clicked.connect(on_delete)
```

### With Loading State

```python
def on_save():
    save_btn.set_loading(True)
    
    # Perform async operation
    result = perform_save_operation()
    
    save_btn.set_loading(False)
    
    if result.success:
        show_success_message("Saved successfully")
    else:
        show_error_message("Save failed")

save_btn = PrimaryButton("Save")
save_btn.clicked.connect(on_save)
```

### With Icons

```python
# Button with left icon
save_btn = PrimaryButton("Save", icon_name="save", icon_position="left")

# Button with right icon
next_btn = PrimaryButton("Next", icon_name="arrow_right", icon_position="right")

# Add icon later
btn = SecondaryButton("Export")
btn.set_icon("download", "left")
```

### Disabled State

```python
submit_btn = PrimaryButton("Submit")

# Disable button
submit_btn.setEnabled(False)

# Enable button
submit_btn.setEnabled(True)
```

### Dialog Button Layout

```python
from PyQt5.QtWidgets import QHBoxLayout, QDialog

class ConfirmDialog(QDialog):
    def __init__(self):
        super().__init__()
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Cancel button (secondary)
        cancel_btn = SecondaryButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # Confirm button (primary)
        confirm_btn = PrimaryButton("Confirm")
        confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(confirm_btn)
        
        # Add to dialog layout
        self.layout().addLayout(button_layout)
```

### Destructive Action with Confirmation

```python
def on_delete():
    # Show confirmation dialog
    reply = QMessageBox.question(
        self,
        "Confirm Delete",
        "Are you sure you want to delete this item?",
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        delete_btn.set_loading(True)
        perform_delete()
        delete_btn.set_loading(False)

delete_btn = DangerButton("Delete Item")
delete_btn.clicked.connect(on_delete)
```

---

## Accessibility

### Keyboard Navigation
- **Tab:** Move focus between buttons
- **Shift+Tab:** Move focus backwards
- **Enter/Space:** Activate focused button

### Screen Readers
- Button text is announced by screen readers
- Loading state is announced when changed
- Disabled state is announced

### Touch Targets
All buttons meet WCAG 2.1 AA Level AA requirements:
- Minimum 44x44px touch target size
- Adequate spacing between adjacent buttons

### Focus Indicators
- 3px visible outline when focused
- High contrast with background
- Offset by 2px for clarity

### Color Contrast
All button text meets WCAG AA contrast requirements:
- Primary: 4.5:1 minimum contrast ratio
- Secondary: 4.5:1 minimum contrast ratio
- Ghost: 4.5:1 minimum contrast ratio
- Danger: 4.5:1 minimum contrast ratio

---

## Best Practices

### Button Hierarchy
1. **One Primary per Screen:** Use only one primary button per view/dialog
2. **Secondary for Alternatives:** Use secondary buttons for alternative actions
3. **Ghost for Low Priority:** Use ghost buttons for tertiary actions
4. **Danger for Destructive:** Always use danger button for destructive actions

### Button Text
- Use action verbs: "Save", "Delete", "Create"
- Be specific: "Save Changes" instead of "OK"
- Keep it short: 1-3 words maximum
- Use sentence case: "Save changes" not "SAVE CHANGES"

### Loading States
- Always show loading state for async operations
- Disable button during loading to prevent double-clicks
- Keep button text visible during loading
- Show success/error feedback after loading completes

### Disabled States
- Only disable buttons when action is truly unavailable
- Provide tooltip explaining why button is disabled
- Consider using validation messages instead of disabling

### Icon Usage
- Use icons to reinforce button meaning
- Don't rely solely on icons (include text)
- Position icons consistently (left for actions, right for navigation)
- Ensure icons are recognizable at button size

---

## Theme Support

All buttons automatically respond to theme changes:

```python
# Buttons automatically update when theme changes
from ui.services import get_v2_settings_bus

settings_bus = get_v2_settings_bus()
settings_bus.theme_changed.connect(lambda theme: print(f"Theme changed to {theme}"))
```

**Light Theme:**
- Primary: Blue (#0f62fe) on white text
- Secondary: Blue border with blue text
- Ghost: Blue text only
- Danger: Red (#da1e28) on white text

**Dark Theme:**
- Primary: Light blue (#4589ff) on dark text
- Secondary: Light blue border with light blue text
- Ghost: Light blue text only
- Danger: Light red (#ff5050) on dark text

---

## Migration Guide

### From Old Buttons

```python
# Old way (QPushButton)
old_btn = QPushButton("Save")
old_btn.setStyleSheet("background-color: blue; color: white;")

# New way (PrimaryButton)
new_btn = PrimaryButton("Save")
# Styling is automatic, theme-aware, and accessible
```

### From Legacy Components

```python
# Old way (custom button class)
from ui.components import CustomButton
old_btn = CustomButton("Save", style="primary")

# New way (PrimaryButton)
from ui.components_v2 import PrimaryButton
new_btn = PrimaryButton("Save")
```

---

## Troubleshooting

### Button Not Responding to Clicks
- Check if button is enabled: `btn.isEnabled()`
- Check if button is in loading state: `btn.is_loading()`
- Verify signal connection: `btn.clicked.connect(handler)`

### Focus Indicator Not Visible
- Ensure button has focus policy: `btn.setFocusPolicy(Qt.StrongFocus)`
- Check theme colors for focus indicator
- Verify no custom stylesheet overriding focus styles

### Loading Spinner Not Showing
- Verify `set_loading(True)` is called
- Check if button is visible on screen
- Ensure button has minimum size (44x44px)

---

## Related Components

- **Inputs:** Form input components (text, dropdown, checkbox, etc.)
- **Dialogs:** Modal dialog components using buttons
- **Cards:** Card components that may contain buttons
- **Navigation:** Navigation components with button-like elements

---

**Last Updated:** Phase 5.1 Implementation
**Version:** 2.0.0
**Status:** ✅ Complete