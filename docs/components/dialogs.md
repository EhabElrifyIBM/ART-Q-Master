# Dialog Components Documentation

## Overview

Dialog components provide modal and non-modal windows for user interactions. They follow IBM Carbon Design principles and integrate seamlessly with the design system.

**Phase 5.2 Enhancements:**
- ✅ 8 dialog types available (Confirm, Message, Input, Progress, Error, Success, Warning, Custom)
- ✅ Focus trapping (Tab cycles within dialog)
- ✅ Escape key closes dialogs
- ✅ Backdrop click to close (optional)
- ✅ Dialog animations (fade in/out)
- ✅ Proper z-index stacking
- ✅ Max-width constraints (600px default)
- ✅ Scrollable content area

## Dialog Types

### 1. ConfirmDialog
Confirmation dialog with Yes/No buttons.

**Use Cases:**
- Confirming destructive actions
- User decision points
- Permission requests

### 2. InputDialog
Dialog for text input with OK/Cancel buttons.

**Use Cases:**
- Collecting user input
- Renaming items
- Quick data entry

### 3. ProgressDialog
Dialog showing progress of long operations.

**Use Cases:**
- File uploads/downloads
- Batch processing
- Long-running tasks

### 4. MessageDialog
General message dialog with customizable type.

**Use Cases:**
- Information messages
- Warnings
- Errors
- Success notifications

### 5. ErrorDialog
Specialized error message dialog (red text).

**Use Cases:**
- Error notifications
- Failure messages
- Exception handling

### 6. SuccessDialog
Specialized success message dialog (green text).

**Use Cases:**
- Success confirmations
- Completion messages
- Positive feedback

### 7. WarningDialog
Specialized warning message dialog (yellow text).

**Use Cases:**
- Warning messages
- Caution notices
- Non-critical alerts

### 8. CustomDialog
Fully customizable dialog for complex scenarios.

**Use Cases:**
- Complex forms
- Multi-step wizards
- Custom layouts

## API Reference

### ModernDialog (Base Class)

Base class for all dialog variants. Provides common functionality.

#### Constructor

```python
ModernDialog(
    parent: Optional[QWidget] = None,
    title: str = "",
    max_width: int = 600,
    close_on_backdrop: bool = False,
    animate: bool = True
)
```

**Parameters:**
- `parent`: Parent widget
- `title`: Dialog window title
- `max_width`: Maximum dialog width in pixels (default: 600)
- `close_on_backdrop`: Whether clicking backdrop closes dialog (default: False)
- `animate`: Whether to animate dialog appearance (default: True)

#### Methods

##### add_content(widget: QWidget)
Add content widget to dialog.

```python
content = QLabel("Dialog content")
dialog.add_content(content)
```

##### add_buttons(*buttons: QPushButton)
Add buttons to dialog button layout.

```python
dialog.add_buttons(cancel_btn, ok_btn)
```

##### set_theme(theme_mode: str)
Update dialog theme ('light' or 'dark').

```python
dialog.set_theme("dark")
```

#### Signals

##### closing
Emitted when dialog is about to close.

```python
dialog.closing.connect(on_dialog_closing)
```

#### Keyboard Shortcuts

- **Escape**: Close dialog (reject)
- **Tab**: Cycle focus forward through dialog widgets
- **Shift+Tab**: Cycle focus backward through dialog widgets

### ConfirmDialog

#### Constructor

```python
ConfirmDialog(
    parent: Optional[QWidget] = None,
    message: str = "",
    title: str = "Confirm",
    yes_text: str = "Yes",
    no_text: str = "No"
)
```

**Parameters:**
- `parent`: Parent widget
- `message`: Confirmation message
- `title`: Dialog title
- `yes_text`: Text for yes button (default: "Yes")
- `no_text`: Text for no button (default: "No")

**Returns:**
- `QDialog.Accepted` if Yes clicked
- `QDialog.Rejected` if No clicked or dialog closed

### InputDialog

#### Constructor

```python
InputDialog(
    parent: Optional[QWidget] = None,
    label: str = "",
    title: str = "Input",
    default_text: str = "",
    placeholder: str = ""
)
```

**Parameters:**
- `parent`: Parent widget
- `label`: Input label text
- `title`: Dialog title
- `default_text`: Default input text
- `placeholder`: Placeholder text

#### Methods

##### get_text() -> str
Get entered text.

```python
if dialog.exec_() == QDialog.Accepted:
    text = dialog.get_text()
```

##### set_text(text: str)
Set initial text.

```python
dialog.set_text("Initial value")
```

### ProgressDialog

#### Constructor

```python
ProgressDialog(
    parent: Optional[QWidget] = None,
    message: str = "Processing...",
    title: str = "Progress",
    cancelable: bool = False
)
```

**Parameters:**
- `parent`: Parent widget
- `message`: Progress message
- `title`: Dialog title
- `cancelable`: Whether dialog can be cancelled

#### Methods

##### set_progress(value: int)
Set progress value (0-100).

```python
dialog.set_progress(50)  # 50%
```

##### set_message(message: str)
Update progress message.

```python
dialog.set_message("Processing file 5 of 10...")
```

### MessageDialog

#### Constructor

```python
MessageDialog(
    parent: Optional[QWidget] = None,
    title: str = "",
    message: str = "",
    message_type: str = "info"
)
```

**Parameters:**
- `parent`: Parent widget
- `title`: Dialog title
- `message`: Message text
- `message_type`: Type of message ('info', 'warning', 'error', 'success')

#### Static Methods

##### information(parent, title, message) -> int
Show information dialog.

```python
MessageDialog.information(parent, "Info", "Operation completed")
```

##### warning(parent, title, message) -> int
Show warning dialog.

```python
MessageDialog.warning(parent, "Warning", "File already exists")
```

##### error(parent, title, message) -> int
Show error dialog.

```python
MessageDialog.error(parent, "Error", "Failed to save file")
```

##### success(parent, title, message) -> int
Show success dialog.

```python
MessageDialog.success(parent, "Success", "File saved successfully")
```

### ErrorDialog

#### Static Methods

##### show_error(parent, title, message) -> int
Show error dialog.

```python
ErrorDialog.show_error(parent, "Error", "Connection failed")
```

### SuccessDialog

#### Static Methods

##### show_success(parent, title, message) -> int
Show success dialog.

```python
SuccessDialog.show_success(parent, "Success", "Data saved")
```

### WarningDialog

#### Static Methods

##### show_warning(parent, title, message) -> int
Show warning dialog.

```python
WarningDialog.show_warning(parent, "Warning", "Unsaved changes")
```

### CustomDialog

#### Constructor

```python
CustomDialog(
    parent: Optional[QWidget] = None,
    title: str = "Dialog",
    max_width: int = 600,
    close_on_backdrop: bool = False
)
```

#### Methods

##### set_content(widget: QWidget)
Set dialog content.

```python
dialog.set_content(my_custom_widget)
```

##### add_custom_button(text: str, callback, primary: bool = False) -> QPushButton
Add custom button to dialog.

```python
dialog.add_custom_button("Apply", on_apply, primary=True)
dialog.add_custom_button("Close", dialog.reject)
```

## Usage Examples

### Example 1: Confirmation Dialog

```python
from ui.components_v2 import ConfirmDialog
from PyQt5.QtWidgets import QDialog

def delete_item():
    dialog = ConfirmDialog(
        parent=self,
        message="Are you sure you want to delete this item?",
        title="Confirm Delete"
    )
    
    if dialog.exec_() == QDialog.Accepted:
        # User clicked Yes
        perform_delete()
    else:
        # User clicked No or closed dialog
        print("Delete cancelled")
```

### Example 2: Input Dialog

```python
from ui.components_v2 import InputDialog
from PyQt5.QtWidgets import QDialog

def rename_file():
    dialog = InputDialog(
        parent=self,
        label="Enter new filename:",
        title="Rename File",
        default_text="document.txt",
        placeholder="filename.ext"
    )
    
    if dialog.exec_() == QDialog.Accepted:
        new_name = dialog.get_text()
        if new_name:
            perform_rename(new_name)
```

### Example 3: Progress Dialog

```python
from ui.components_v2 import ProgressDialog
from PyQt5.QtWidgets import QApplication

def process_files(files):
    dialog = ProgressDialog(
        parent=self,
        message="Processing files...",
        title="File Processing",
        cancelable=True
    )
    
    dialog.show()
    
    for i, file in enumerate(files):
        # Check if user cancelled
        if dialog.result() == QDialog.Rejected:
            break
        
        # Update progress
        progress = int((i + 1) / len(files) * 100)
        dialog.set_progress(progress)
        dialog.set_message(f"Processing {file.name}...")
        
        # Process file
        process_file(file)
        QApplication.processEvents()
    
    dialog.close()
```

### Example 4: Message Dialogs

```python
from ui.components_v2 import MessageDialog

# Information
MessageDialog.information(
    self,
    "Information",
    "The operation completed successfully."
)

# Warning
MessageDialog.warning(
    self,
    "Warning",
    "The file already exists. It will be overwritten."
)

# Error
MessageDialog.error(
    self,
    "Error",
    "Failed to connect to the server."
)

# Success
MessageDialog.success(
    self,
    "Success",
    "Your changes have been saved."
)
```

### Example 5: Specialized Dialogs

```python
from ui.components_v2 import ErrorDialog, SuccessDialog, WarningDialog

# Error dialog
ErrorDialog.show_error(
    self,
    "Connection Error",
    "Unable to connect to the database."
)

# Success dialog
SuccessDialog.show_success(
    self,
    "Upload Complete",
    "All files have been uploaded successfully."
)

# Warning dialog
WarningDialog.show_warning(
    self,
    "Unsaved Changes",
    "You have unsaved changes. Do you want to continue?"
)
```

### Example 6: Custom Dialog

```python
from ui.components_v2 import CustomDialog
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QWidget

def show_custom_dialog():
    dialog = CustomDialog(
        parent=self,
        title="User Registration",
        max_width=500,
        close_on_backdrop=True
    )
    
    # Create custom content
    content_layout = QVBoxLayout()
    
    content_layout.addWidget(QLabel("Name:"))
    name_input = QLineEdit()
    content_layout.addWidget(name_input)
    
    content_layout.addWidget(QLabel("Email:"))
    email_input = QLineEdit()
    content_layout.addWidget(email_input)
    
    content_widget = QWidget()
    content_widget.setLayout(content_layout)
    dialog.set_content(content_widget)
    
    # Add custom buttons
    def on_register():
        name = name_input.text()
        email = email_input.text()
        if name and email:
            register_user(name, email)
            dialog.accept()
    
    dialog.add_custom_button("Register", on_register, primary=True)
    dialog.add_custom_button("Cancel", dialog.reject)
    
    dialog.exec_()
```

### Example 7: Dialog with Backdrop Click

```python
from ui.components_v2 import CustomDialog

# Dialog closes when clicking outside
dialog = CustomDialog(
    parent=self,
    title="Quick Settings",
    close_on_backdrop=True  # Enable backdrop click to close
)

dialog.set_content(settings_widget)
dialog.exec_()
```

### Example 8: Non-Modal Dialog

```python
from ui.components_v2 import ProgressDialog

# Show non-modal dialog (doesn't block)
dialog = ProgressDialog(
    parent=self,
    message="Downloading...",
    title="Download Progress"
)

dialog.show()  # Use show() instead of exec_() for non-modal

# Continue with other operations
# Update progress from background thread
```

### Example 9: Dialog with Custom Width

```python
from ui.components_v2 import CustomDialog

# Wide dialog for complex content
dialog = CustomDialog(
    parent=self,
    title="Data Table",
    max_width=1000  # Wider than default 600px
)

dialog.set_content(table_widget)
dialog.exec_()
```

### Example 10: Dialog without Animation

```python
from ui.components_v2 import ModernDialog

# Dialog without fade animation (instant)
dialog = ModernDialog(
    parent=self,
    title="Quick Action",
    animate=False  # Disable animation
)

dialog.add_content(content_widget)
dialog.exec_()
```

## Best Practices

### 1. Choose the Right Dialog Type

- **ConfirmDialog**: For yes/no decisions
- **InputDialog**: For single text input
- **ProgressDialog**: For long operations
- **MessageDialog**: For simple messages
- **CustomDialog**: For complex scenarios

### 2. Dialog Titles

- Keep titles short and descriptive
- Use title case (e.g., "Confirm Delete")
- Avoid redundant words like "Dialog"

### 3. Message Text

- Be clear and concise
- Explain what will happen
- Use active voice
- Avoid technical jargon

### 4. Button Labels

- Use action verbs (e.g., "Delete", "Save", "Cancel")
- Be specific (e.g., "Delete File" instead of "OK")
- Primary action on the right

### 5. Progress Dialogs

- Always show progress percentage
- Update message to show current step
- Allow cancellation for long operations
- Close automatically when complete

### 6. Modal vs Non-Modal

- **Modal** (exec_()): Blocks parent window, use for critical decisions
- **Non-Modal** (show()): Doesn't block, use for progress/status

### 7. Backdrop Click

- Enable for non-critical dialogs
- Disable for important confirmations
- Consider user expectations

### 8. Accessibility

- All dialogs support keyboard navigation
- Tab cycles through focusable elements
- Escape closes dialog
- Enter activates default button

## Focus Trapping

Dialogs implement focus trapping for accessibility:

```python
# Focus automatically cycles within dialog
# Tab: Move to next focusable element
# Shift+Tab: Move to previous focusable element
# Focus wraps around (last -> first, first -> last)
```

This ensures keyboard users can't accidentally tab out of the dialog.

## Animation System

Dialogs use fade in/out animations:

```python
# Fade in when shown (250ms)
dialog.show()  # or dialog.exec_()

# Fade out when closed (250ms)
dialog.close()  # or dialog.reject()
```

Disable animations for instant display:

```python
dialog = ModernDialog(animate=False)
```

## Scrollable Content

Dialogs automatically handle long content:

```python
# Content area is scrollable
# Vertical scrollbar appears when needed
# Horizontal scrollbar is disabled
# Buttons always visible at bottom
```

## Theme Integration

Dialogs automatically integrate with the theme system:

```python
# Dialogs respond to theme changes automatically
from ui.services import get_v2_settings_bus

settings_bus = get_v2_settings_bus()
settings_bus.theme_changed.connect(lambda mode: dialog.set_theme(mode))
```

## Typography Integration

Dialogs automatically respond to font preset changes:

```python
# Font sizes update automatically when preset changes
from ui.services import get_v2_settings_bus

settings_bus = get_v2_settings_bus()
# Dialog text will automatically resize when preset changes
```

## Design Tokens Used

Dialogs use the following design system tokens:

- **Spacing**: `LG` (24px), `MD` (16px), `SM` (8px)
- **BorderRadius**: `LG` (12px), `SM` (4px)
- **Colors**: `background`, `surface`, `border`, `text_primary`, `primary`, `danger`, `warning`, `success`
- **Animation**: `DURATION_NORMAL` (250ms)
- **ZIndex**: `MODAL` (1300)

## Migration from Old Dialogs

If migrating from older dialog implementations:

```python
# Old way (QMessageBox)
from PyQt5.QtWidgets import QMessageBox
reply = QMessageBox.question(self, "Confirm", "Delete?")

# New way
from ui.components_v2 import ConfirmDialog
dialog = ConfirmDialog(self, "Delete this item?", "Confirm")
if dialog.exec_() == QDialog.Accepted:
    delete_item()
```

Benefits of new dialogs:
- Consistent styling with design system
- Automatic theme support
- Focus trapping for accessibility
- Smooth animations
- Scrollable content
- Customizable buttons

## Related Components

- **Buttons**: Used for dialog actions
- **Inputs**: Used in InputDialog and CustomDialog
- **Cards**: Can contain dialog triggers
- **Typography**: Dialog text uses typography system

## Troubleshooting

### Dialog not showing
```python
# Make sure to call exec_() or show()
dialog.exec_()  # Modal
# or
dialog.show()  # Non-modal
```

### Focus trap not working
```python
# Focus trap is automatic
# Make sure widgets have proper focus policy
widget.setFocusPolicy(Qt.FocusPolicy.TabFocus)
```

### Animation not playing
```python
# Make sure animate=True (default)
dialog = ModernDialog(animate=True)
```

### Backdrop click not working
```python
# Make sure close_on_backdrop=True
dialog = CustomDialog(close_on_backdrop=True)
```

### Content not scrolling
```python
# Content area is automatically scrollable
# Make sure content height exceeds dialog height
```

## Performance Considerations

- Dialogs are lightweight and efficient
- Fade animations run at 60 FPS (smooth)
- Focus trapping has no performance impact
- Scrollable content uses native Qt scrolling

## Accessibility

- **Keyboard Navigation**: Full keyboard support (Tab, Shift+Tab, Enter, Escape)
- **Focus Trapping**: Focus cycles within dialog
- **Screen Readers**: Proper ARIA labels (future enhancement)
- **Theme Support**: Automatic theme changes
- **Font Scaling**: Automatic font size changes

## Security Considerations

- Input validation should be done after dialog closes
- Don't trust user input without validation
- Sanitize input before using in operations

```python
dialog = InputDialog(self, "Enter filename:")
if dialog.exec_() == QDialog.Accepted:
    filename = dialog.get_text()
    # Validate and sanitize
    if is_valid_filename(filename):
        save_file(sanitize_filename(filename))
```

---

**Last Updated**: Phase 5.2 Implementation
**Component Version**: 2.0
**Design System**: IBM Carbon Design