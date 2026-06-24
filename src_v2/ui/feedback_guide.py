"""
Feedback Mechanisms Usage Guide
================================

This module provides guidance on when and how to use different feedback mechanisms
in the ART Q Master application. All feedback components follow IBM Carbon Design
principles and integrate with the design system.

Feedback Types
--------------

1. **Toast Notifications** (Auto-dismiss)
   - Quick, non-intrusive messages
   - Appear at top of screen
   - Auto-dismiss after set duration
   - Use for: Success confirmations, info messages, warnings

2. **Loading Indicators**
   - Show progress of operations
   - Three types based on duration
   - Use for: Any operation that takes time

3. **Dialogs** (Require acknowledgment)
   - Modal windows that block interaction
   - User must acknowledge before continuing
   - Use for: Errors, confirmations, important messages

Duration Standards
------------------

Toast notifications follow these duration standards:
- **Success**: 3 seconds (green) - Quick confirmation
- **Info**: 4 seconds (blue) - Informational message
- **Warning**: 5 seconds (yellow) - Needs attention
- **Error**: Dialog (red) - Requires acknowledgment

Loading Indicator Selection
----------------------------

Choose loading indicator based on operation duration:

1. **ModernSpinner** (< 2 seconds)
   - Quick operations
   - Simple animation
   - No progress percentage
   - Examples: Saving settings, quick validation

2. **ModernProgressBar** (2-30 seconds)
   - File operations
   - Shows percentage complete
   - Embedded in UI
   - Examples: File upload, data processing

3. **ProgressDialog** (> 30 seconds)
   - Long-running operations
   - Modal dialog with progress
   - Can show detailed status
   - Examples: Batch processing, large file operations

Usage Examples
--------------

### Toast Notifications

```python
from ui.components_v2 import Toast

# Success toast (3s, green)
Toast.success(parent, "File saved successfully!")

# Info toast (4s, blue)
Toast.info(parent, "Processing 10 items...")

# Warning toast (5s, yellow)
Toast.warning(parent, "Some items were skipped")

# Error dialog (requires acknowledgment, red)
Toast.error(parent, "Failed to save file", "Save Error")
```

### Loading Indicators

```python
from ui.components_v2 import ModernSpinner, ModernProgressBar
from ui.components_v2.dialogs import ProgressDialog

# Quick operation (< 2s) - Spinner
spinner = ModernSpinner(parent)
spinner.start()
# ... do quick operation ...
spinner.stop()

# File operation (2-30s) - Progress Bar
progress_bar = ModernProgressBar(parent)
layout.addWidget(progress_bar)
for i in range(100):
    progress_bar.setValue(i)
    # ... process file ...

# Long operation (> 30s) - Progress Dialog
dialog = ProgressDialog(parent, "Processing files...", "Batch Process")
dialog.show()
for i, file in enumerate(files):
    dialog.set_progress(int((i / len(files)) * 100))
    dialog.set_message(f"Processing {file}...")
    # ... process file ...
dialog.close()
```

### Message Dialogs

```python
from ui.components_v2.dialogs import MessageDialog, ConfirmDialog

# Information dialog
MessageDialog.information(parent, "Info", "Operation completed")

# Warning dialog
MessageDialog.warning(parent, "Warning", "This action cannot be undone")

# Error dialog
MessageDialog.error(parent, "Error", "Failed to connect to server")

# Success dialog
MessageDialog.success(parent, "Success", "All items processed")

# Confirmation dialog
dialog = ConfirmDialog(parent, "Delete this item?", "Confirm Delete")
if dialog.exec_() == ConfirmDialog.Accepted:
    delete_item()
```

Best Practices
--------------

1. **Choose the Right Feedback Type**
   - Use toasts for non-critical messages
   - Use dialogs for errors and confirmations
   - Use appropriate loading indicator for operation duration

2. **Message Content**
   - Be concise and clear
   - Use action-oriented language
   - Provide context when needed
   - Example: "File saved" vs "config.json saved successfully"

3. **Timing**
   - Don't show too many toasts at once
   - Respect duration standards
   - Don't interrupt user with unnecessary dialogs

4. **Accessibility**
   - All feedback components support keyboard navigation
   - Dialogs can be closed with Esc key
   - Primary actions can be triggered with Enter key

5. **Theme Integration**
   - All feedback components automatically adapt to theme changes
   - Colors follow design system standards
   - Typography scales with font size settings

Component Reference
-------------------

### Toast
- **Location**: `ui.components_v2.feedback.Toast`
- **Methods**: `success()`, `info()`, `warning()`, `error()`
- **Auto-dismiss**: Yes (except error which shows dialog)
- **Theme support**: Yes
- **Keyboard**: N/A (auto-dismiss)

### ModernSpinner
- **Location**: `ui.components_v2.feedback.ModernSpinner`
- **Methods**: `start()`, `stop()`
- **Duration**: < 2 seconds
- **Theme support**: Yes
- **Progress**: No

### ModernProgressBar
- **Location**: `ui.components_v2.feedback.ModernProgressBar`
- **Methods**: `setValue()`, `setMaximum()`, `setMinimum()`
- **Duration**: 2-30 seconds
- **Theme support**: Yes
- **Progress**: Yes (percentage)

### ProgressDialog
- **Location**: `ui.components_v2.dialogs.ProgressDialog`
- **Methods**: `set_progress()`, `set_message()`
- **Duration**: > 30 seconds
- **Theme support**: Yes
- **Progress**: Yes (percentage + message)

### MessageDialog
- **Location**: `ui.components_v2.dialogs.MessageDialog`
- **Methods**: `information()`, `warning()`, `error()`, `success()`
- **Modal**: Yes
- **Theme support**: Yes
- **Keyboard**: Esc to close, Enter to accept

### ConfirmDialog
- **Location**: `ui.components_v2.dialogs.ConfirmDialog`
- **Methods**: `exec_()`
- **Modal**: Yes
- **Theme support**: Yes
- **Keyboard**: Esc to cancel, Enter to accept

Migration from Old Components
------------------------------

If migrating from old feedback components:

**Old LoadingSpinner** → **ModernSpinner**
```python
# Old
from ui.components import LoadingSpinner
spinner = LoadingSpinner(parent)

# New
from ui.components_v2 import ModernSpinner
spinner = ModernSpinner(parent)
```

**Old ProgressMonitor** → **ProgressDialog**
```python
# Old
from ui.components import ProgressMonitor
monitor = ProgressMonitor(parent, "Processing...")

# New
from ui.components_v2.dialogs import ProgressDialog
dialog = ProgressDialog(parent, "Processing...", "Progress")
```

**Old MessageBox** → **MessageDialog**
```python
# Old
from PyQt5.QtWidgets import QMessageBox
QMessageBox.information(parent, "Title", "Message")

# New
from ui.components_v2.dialogs import MessageDialog
MessageDialog.information(parent, "Title", "Message")
```

See Also
--------
- `ui/design_system.py` - Color and spacing constants
- `ui/typography.py` - Font sizing system
- `ui/components_v2/feedback.py` - Feedback component implementations
- `ui/components_v2/dialogs.py` - Dialog component implementations
- `docs/PHASE_4_FEEDBACK_MECHANISMS.md` - Implementation details

Made with Bob
"""

__all__ = []  # This is a documentation module, no exports

# Made with Bob
