# Input Components API Documentation

## Overview

Modern input components following IBM Carbon Design principles with Phase 5.1 enhancements. All inputs support validation, helper text, theming, and meet WCAG 2.1 AA accessibility standards.

## Input Types

### ModernLineEdit
Single-line text input for short text entries.

**Use Case:** Name, email, phone, search, single-line data entry

### ModernTextEdit
Multi-line text area for longer text content.

**Use Case:** Comments, descriptions, notes, multi-line data entry

### ModernComboBox
Dropdown selector for choosing from a list of options.

**Use Case:** Status selection, category selection, predefined choices

### ModernCheckBox
Boolean checkbox for yes/no or on/off selections.

**Use Case:** Agree to terms, enable feature, select multiple items

### ModernRadioButton
Single selection from a group of mutually exclusive options.

**Use Case:** Gender selection, payment method, single choice from group

---

## API Reference

### ModernLineEdit

#### Constructor

```python
input = ModernLineEdit(
    parent: Optional[QWidget] = None,
    show_clear_button: bool = True
)
```

**Parameters:**
- `parent` (QWidget, optional): Parent widget
- `show_clear_button` (bool): Whether to show clear button (default: True)

#### Properties

- **Minimum Height:** 44px (WCAG 2.1 AA touch target)
- **Focus Indicator:** 3px outline
- **Clear Button:** Built-in clear button (optional)

#### Methods

##### set_error(has_error: bool, message: str = "")
Set validation error state with optional error message.

```python
name_input = ModernLineEdit()
if not name_input.text():
    name_input.set_error(True, "Name is required")
else:
    name_input.set_error(False)
```

##### set_helper_text(text: str)
Set helper text for guidance.

```python
email_input = ModernLineEdit()
email_input.set_helper_text("Enter your email address")
```

##### get_helper_text() -> str
Get current helper text.

##### set_required(required: bool)
Mark field as required.

```python
name_input = ModernLineEdit()
name_input.set_required(True)
```

##### is_required() -> bool
Check if field is required.

##### validate() -> bool
Validate input value. Returns True if valid, False otherwise.

```python
if name_input.validate():
    print("Valid input")
else:
    print(f"Error: {name_input.get_error_message()}")
```

##### get_error_message() -> str
Get current error message.

#### Signals

##### textChanged(str)
Emitted when text changes (inherited from QLineEdit).

##### returnPressed()
Emitted when Enter is pressed (inherited from QLineEdit).

##### validationChanged(bool, str)
Emitted when validation state changes.
- Parameter 1: is_valid (bool)
- Parameter 2: message (str)

```python
def on_validation_changed(is_valid, message):
    if not is_valid:
        print(f"Validation error: {message}")

input.validationChanged.connect(on_validation_changed)
```

---

### ModernTextEdit

#### Constructor

```python
textarea = ModernTextEdit(parent: Optional[QWidget] = None)
```

#### Properties

- **Minimum Height:** 100px
- **Focus Indicator:** 3px outline
- **Multi-line:** Supports multiple lines of text

#### Methods

Same as ModernLineEdit, plus:

##### toPlainText() -> str
Get plain text content (inherited from QTextEdit).

##### setPlainText(text: str)
Set plain text content (inherited from QTextEdit).

#### Signals

##### textChanged()
Emitted when text changes (inherited from QTextEdit).

##### validationChanged(bool, str)
Emitted when validation state changes.

---

### ModernComboBox

#### Constructor

```python
combo = ModernComboBox(parent: Optional[QWidget] = None)
```

#### Properties

- **Minimum Height:** 44px (WCAG 2.1 AA touch target)
- **Focus Indicator:** 3px outline
- **Dropdown:** Styled dropdown list

#### Methods

Same validation methods as ModernLineEdit, plus:

##### addItem(text: str)
Add item to dropdown (inherited from QComboBox).

##### addItems(texts: List[str])
Add multiple items to dropdown (inherited from QComboBox).

##### currentText() -> str
Get currently selected text (inherited from QComboBox).

##### currentIndex() -> int
Get currently selected index (inherited from QComboBox).

##### setCurrentIndex(index: int)
Set currently selected index (inherited from QComboBox).

#### Signals

##### currentIndexChanged(int)
Emitted when selection changes (inherited from QComboBox).

##### currentTextChanged(str)
Emitted when selected text changes (inherited from QComboBox).

##### validationChanged(bool, str)
Emitted when validation state changes.

---

### ModernCheckBox

#### Constructor

```python
checkbox = ModernCheckBox(
    text: str = "",
    parent: Optional[QWidget] = None
)
```

**Parameters:**
- `text` (str): Checkbox label text
- `parent` (QWidget, optional): Parent widget

#### Properties

- **Minimum Height:** 44px (WCAG 2.1 AA touch target)
- **Indicator Size:** 20x20px
- **Focus Indicator:** 3px outline on indicator

#### Methods

##### isChecked() -> bool
Check if checkbox is checked (inherited from QCheckBox).

##### setChecked(checked: bool)
Set checkbox checked state (inherited from QCheckBox).

#### Signals

##### stateChanged(int)
Emitted when check state changes (inherited from QCheckBox).

##### toggled(bool)
Emitted when checkbox is toggled (inherited from QCheckBox).

---

### ModernRadioButton

#### Constructor

```python
radio = ModernRadioButton(
    text: str = "",
    parent: Optional[QWidget] = None
)
```

**Parameters:**
- `text` (str): Radio button label text
- `parent` (QWidget, optional): Parent widget

#### Properties

- **Minimum Height:** 44px (WCAG 2.1 AA touch target)
- **Indicator Size:** 20x20px (circular)
- **Focus Indicator:** 3px outline on indicator

#### Methods

##### isChecked() -> bool
Check if radio button is checked (inherited from QRadioButton).

##### setChecked(checked: bool)
Set radio button checked state (inherited from QRadioButton).

#### Signals

##### toggled(bool)
Emitted when radio button is toggled (inherited from QRadioButton).

---

## Usage Examples

### Basic Text Input

```python
from ui.components_v2 import ModernLineEdit

# Create text input
name_input = ModernLineEdit()
name_input.setPlaceholderText("Enter your name")

# Get value
name = name_input.text()
```

### Text Input with Validation

```python
# Create required input
email_input = ModernLineEdit()
email_input.setPlaceholderText("Enter email")
email_input.set_required(True)
email_input.set_helper_text("We'll never share your email")

# Validate on text change
def on_text_changed():
    text = email_input.text()
    if not text:
        email_input.set_error(True, "Email is required")
    elif "@" not in text:
        email_input.set_error(True, "Invalid email format")
    else:
        email_input.set_error(False)

email_input.textChanged.connect(on_text_changed)
```

### Multi-line Text Area

```python
from ui.components_v2 import ModernTextEdit

# Create text area
description = ModernTextEdit()
description.setPlaceholderText("Enter description...")
description.set_required(True)
description.set_helper_text("Provide a detailed description")

# Get value
text = description.toPlainText()
```

### Dropdown Selection

```python
from ui.components_v2 import ModernComboBox

# Create dropdown
status_combo = ModernComboBox()
status_combo.addItems(["Active", "Inactive", "Pending"])
status_combo.set_required(True)
status_combo.set_helper_text("Select current status")

# Get selected value
selected = status_combo.currentText()

# Handle selection change
def on_selection_changed(index):
    print(f"Selected: {status_combo.currentText()}")

status_combo.currentIndexChanged.connect(on_selection_changed)
```

### Checkbox

```python
from ui.components_v2 import ModernCheckBox

# Create checkbox
agree_checkbox = ModernCheckBox("I agree to the terms and conditions")

# Check if checked
if agree_checkbox.isChecked():
    print("User agreed")

# Handle state change
def on_state_changed(state):
    if state == Qt.Checked:
        print("Checkbox checked")
    else:
        print("Checkbox unchecked")

agree_checkbox.stateChanged.connect(on_state_changed)
```

### Radio Button Group

```python
from ui.components_v2 import ModernRadioButton
from PyQt5.QtWidgets import QButtonGroup, QVBoxLayout

# Create radio button group
gender_group = QButtonGroup()

male_radio = ModernRadioButton("Male")
female_radio = ModernRadioButton("Female")
other_radio = ModernRadioButton("Other")

gender_group.addButton(male_radio, 1)
gender_group.addButton(female_radio, 2)
gender_group.addButton(other_radio, 3)

# Add to layout
layout = QVBoxLayout()
layout.addWidget(male_radio)
layout.addWidget(female_radio)
layout.addWidget(other_radio)

# Get selected value
def get_selected_gender():
    if male_radio.isChecked():
        return "Male"
    elif female_radio.isChecked():
        return "Female"
    elif other_radio.isChecked():
        return "Other"
    return None
```

### Form with Validation

```python
from ui.components_v2 import ModernLineEdit, ModernComboBox, ModernCheckBox
from ui.components_v2 import PrimaryButton, SecondaryButton

class UserForm(QWidget):
    def __init__(self):
        super().__init__()
        
        # Create form inputs
        self.name_input = ModernLineEdit()
        self.name_input.setPlaceholderText("Full name")
        self.name_input.set_required(True)
        
        self.email_input = ModernLineEdit()
        self.email_input.setPlaceholderText("Email address")
        self.email_input.set_required(True)
        
        self.role_combo = ModernComboBox()
        self.role_combo.addItems(["User", "Admin", "Manager"])
        self.role_combo.set_required(True)
        
        self.active_checkbox = ModernCheckBox("Active user")
        self.active_checkbox.setChecked(True)
        
        # Create buttons
        self.submit_btn = PrimaryButton("Submit")
        self.submit_btn.clicked.connect(self.on_submit)
        
        self.cancel_btn = SecondaryButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel)
        
        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        layout.addWidget(QLabel("Role:"))
        layout.addWidget(self.role_combo)
        layout.addWidget(self.active_checkbox)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.submit_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def validate_form(self) -> bool:
        """Validate all form inputs."""
        valid = True
        
        # Validate name
        if not self.name_input.validate():
            valid = False
        
        # Validate email
        if not self.email_input.validate():
            valid = False
        elif "@" not in self.email_input.text():
            self.email_input.set_error(True, "Invalid email format")
            valid = False
        
        # Validate role
        if not self.role_combo.validate():
            valid = False
        
        return valid
    
    def on_submit(self):
        """Handle form submission."""
        if not self.validate_form():
            return
        
        # Get form data
        data = {
            "name": self.name_input.text(),
            "email": self.email_input.text(),
            "role": self.role_combo.currentText(),
            "active": self.active_checkbox.isChecked()
        }
        
        # Submit data
        self.submit_btn.set_loading(True)
        result = submit_user_data(data)
        self.submit_btn.set_loading(False)
        
        if result.success:
            self.close()
    
    def on_cancel(self):
        """Handle form cancellation."""
        self.close()
```

### Real-time Validation

```python
# Validate as user types
def setup_realtime_validation(input_field, validator_func):
    def on_text_changed():
        text = input_field.text()
        is_valid, message = validator_func(text)
        input_field.set_error(not is_valid, message)
    
    input_field.textChanged.connect(on_text_changed)

# Email validator
def validate_email(text):
    if not text:
        return False, "Email is required"
    if "@" not in text or "." not in text:
        return False, "Invalid email format"
    return True, ""

# Phone validator
def validate_phone(text):
    if not text:
        return False, "Phone is required"
    if not text.replace("-", "").replace(" ", "").isdigit():
        return False, "Phone must contain only numbers"
    return True, ""

# Apply validators
email_input = ModernLineEdit()
setup_realtime_validation(email_input, validate_email)

phone_input = ModernLineEdit()
setup_realtime_validation(phone_input, validate_phone)
```

---

## Accessibility

### Keyboard Navigation
- **Tab:** Move focus between inputs
- **Shift+Tab:** Move focus backwards
- **Enter:** Submit form (in text inputs)
- **Space:** Toggle checkbox/radio button
- **Arrow Keys:** Navigate dropdown options

### Screen Readers
- Input labels are announced
- Placeholder text is announced
- Error messages are announced
- Helper text is announced
- Required fields are announced

### Touch Targets
All inputs meet WCAG 2.1 AA Level AA requirements:
- Minimum 44x44px touch target size
- Adequate spacing between inputs

### Focus Indicators
- 3px visible outline when focused
- High contrast with background
- Clearly distinguishable from non-focused state

### Error States
- Visual indicator (red border)
- Error message text
- Announced by screen readers
- Persists until corrected

---

## Validation Patterns

### Required Field Validation

```python
def validate_required(input_field):
    if input_field.is_required() and not input_field.text():
        input_field.set_error(True, "This field is required")
        return False
    return True
```

### Email Validation

```python
import re

def validate_email_format(email_input):
    email = email_input.text()
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        email_input.set_error(True, "Invalid email format")
        return False
    
    email_input.set_error(False)
    return True
```

### Length Validation

```python
def validate_length(input_field, min_length, max_length):
    text = input_field.text()
    
    if len(text) < min_length:
        input_field.set_error(True, f"Minimum {min_length} characters required")
        return False
    
    if len(text) > max_length:
        input_field.set_error(True, f"Maximum {max_length} characters allowed")
        return False
    
    input_field.set_error(False)
    return True
```

### Custom Validation

```python
def validate_username(username_input):
    username = username_input.text()
    
    # Check length
    if len(username) < 3:
        username_input.set_error(True, "Username must be at least 3 characters")
        return False
    
    # Check characters
    if not username.isalnum():
        username_input.set_error(True, "Username must be alphanumeric")
        return False
    
    # Check availability (async)
    if not check_username_available(username):
        username_input.set_error(True, "Username already taken")
        return False
    
    username_input.set_error(False)
    return True
```

---

## Best Practices

### Input Labels
- Always provide clear labels for inputs
- Use sentence case: "Email address" not "EMAIL ADDRESS"
- Place labels above inputs for better readability
- Associate labels with inputs using QLabel

### Placeholder Text
- Use placeholder text for examples: "john@example.com"
- Don't use placeholder text as labels
- Keep placeholder text short and clear
- Use lighter color to distinguish from actual input

### Helper Text
- Provide guidance for complex inputs
- Explain format requirements: "Format: MM/DD/YYYY"
- Show character limits: "Maximum 500 characters"
- Display below input field

### Error Messages
- Be specific: "Email is required" not "Invalid input"
- Provide guidance: "Password must be at least 8 characters"
- Show immediately after validation
- Clear error when input is corrected

### Required Fields
- Mark required fields clearly
- Use asterisk (*) or "Required" label
- Validate on blur or submit
- Don't disable submit button (show errors instead)

### Form Layout
- Group related inputs together
- Use consistent spacing between inputs
- Align labels and inputs vertically
- Place buttons at bottom right

---

## Theme Support

All inputs automatically respond to theme changes:

**Light Theme:**
- Background: White (#ffffff)
- Border: Gray (#8d8d8d)
- Text: Dark gray (#161616)
- Error: Red (#da1e28)
- Focus: Blue (#0f62fe)

**Dark Theme:**
- Background: Dark gray (#262626)
- Border: Gray (#8d8d8d)
- Text: Light gray (#f4f4f4)
- Error: Light red (#ff5050)
- Focus: Light blue (#4589ff)

---

## Troubleshooting

### Validation Not Working
- Verify `set_required(True)` is called
- Check validation logic in validator function
- Ensure `validate()` is called before form submission

### Error Message Not Showing
- Verify `set_error(True, message)` is called
- Check if error message is empty
- Ensure input is visible on screen

### Clear Button Not Showing
- Verify `show_clear_button=True` in constructor
- Check if input has text
- Ensure input is enabled

### Focus Indicator Not Visible
- Verify focus policy is set
- Check theme colors for focus indicator
- Ensure no custom stylesheet overriding focus styles

---

## Related Components

- **Buttons:** Action buttons for form submission
- **Dialogs:** Modal dialogs containing forms
- **Cards:** Card components that may contain forms
- **Feedback:** Toast notifications for form feedback

---

**Last Updated:** Phase 5.1 Implementation
**Version:** 2.0.0
**Status:** ✅ Complete