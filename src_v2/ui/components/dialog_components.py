# ============================================================================
# dialog_components.py - Reusable Dialog Component Library
# ============================================================================
# Phase 2.1: Base Dialog Architecture
# 
# Provides common UI components for use in dialogs.
# Ensures consistent styling and functionality across all dialogs.
# ============================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QCheckBox, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QFrame
)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QFont, QIcon


class DialogTitle(QLabel):
    """Styled title label for dialogs."""
    
    def __init__(self, text):
        """Initialize title label."""
        super().__init__(text)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet("color: #161616; margin-bottom: 5px;")


class DialogLabel(QLabel):
    """Styled label for dialog fields."""
    
    def __init__(self, text, required=False):
        """
        Initialize label.
        
        Args:
            text (str): Label text
            required (bool): Whether field is required (adds *)
        """
        if required:
            text = f"{text} *"
        super().__init__(text)
        self.setStyleSheet("color: #525252; font-weight: 500;")


class StyledLineEdit(QLineEdit):
    """Styled text input field."""
    
    def __init__(self, placeholder=""):
        """Initialize text input."""
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(36)
        self.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d8d8d8;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #161616;
                selection-background-color: #0f62fe;
            }
            QLineEdit:focus {
                border: 2px solid #0f62fe;
                padding: 7px;
            }
            QLineEdit:disabled {
                background-color: #f4f4f4;
                color: #a8a8a8;
            }
        """)


class StyledTextEdit(QTextEdit):
    """Styled multi-line text input."""
    
    def __init__(self, placeholder=""):
        """Initialize text area."""
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(80)
        self.setStyleSheet("""
            QTextEdit {
                border: 1px solid #d8d8d8;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #161616;
                selection-background-color: #0f62fe;
            }
            QTextEdit:focus {
                border: 2px solid #0f62fe;
            }
            QTextEdit:disabled {
                background-color: #f4f4f4;
                color: #a8a8a8;
            }
        """)


class StyledComboBox(QComboBox):
    """Styled dropdown/combobox."""
    
    def __init__(self, items=None):
        """
        Initialize combobox.
        
        Args:
            items (list): List of items to add
        """
        super().__init__()
        self.setMinimumHeight(36)
        if items:
            self.addItems(items)
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #d8d8d8;
                border-radius: 4px;
                padding: 8px;
                background-color: #ffffff;
                color: #161616;
                selection-background-color: #0f62fe;
            }
            QComboBox:focus {
                border: 2px solid #0f62fe;
            }
            QComboBox:disabled {
                background-color: #f4f4f4;
                color: #a8a8a8;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)


class StyledCheckBox(QCheckBox):
    """Styled checkbox."""
    
    def __init__(self, text=""):
        """Initialize checkbox."""
        super().__init__(text)
        self.setStyleSheet("""
            QCheckBox {
                color: #161616;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ffffff;
                border: 1px solid #d8d8d8;
            }
            QCheckBox::indicator:checked {
                background-color: #0f62fe;
                border: 1px solid #0f62fe;
            }
            QCheckBox::indicator:disabled {
                background-color: #f4f4f4;
                border: 1px solid #d8d8d8;
            }
        """)


class InputField(QWidget):
    """
    Container for a labeled input field.
    
    Combines label + input for consistent layout and spacing.
    """
    
    def __init__(self, label_text, input_widget, required=False, help_text=""):
        """
        Initialize input field.
        
        Args:
            label_text (str): Label text
            input_widget (QWidget): Input widget (QLineEdit, QComboBox, etc.)
            required (bool): Whether field is required
            help_text (str): Help text below field
        """
        super().__init__()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Label
        label = DialogLabel(label_text, required=required)
        layout.addWidget(label)
        
        # Input widget
        layout.addWidget(input_widget)
        
        # Help text
        if help_text:
            help_label = QLabel(help_text)
            help_label.setStyleSheet("color: #a8a8a8; font-size: 9pt; margin-top: 2px;")
            layout.addWidget(help_label)
        
        self.setLayout(layout)
        self.input_widget = input_widget
    
    def get_value(self):
        """Get value from input widget."""
        if isinstance(self.input_widget, (QLineEdit, QTextEdit)):
            return self.input_widget.text()
        elif isinstance(self.input_widget, QComboBox):
            return self.input_widget.currentText()
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            return self.input_widget.value()
        elif isinstance(self.input_widget, QCheckBox):
            return self.input_widget.isChecked()
        else:
            return None
    
    def set_value(self, value):
        """Set value in input widget."""
        if isinstance(self.input_widget, (QLineEdit, QTextEdit)):
            self.input_widget.setText(str(value))
        elif isinstance(self.input_widget, QComboBox):
            index = self.input_widget.findText(str(value))
            if index >= 0:
                self.input_widget.setCurrentIndex(index)
        elif isinstance(self.input_widget, (QSpinBox, QDoubleSpinBox)):
            self.input_widget.setValue(value)
        elif isinstance(self.input_widget, QCheckBox):
            self.input_widget.setChecked(bool(value))
    
    def set_enabled(self, enabled):
        """Enable/disable the input widget."""
        self.input_widget.setEnabled(enabled)


class FormLayout(QVBoxLayout):
    """
    Simplified form layout for dialogs.
    
    Automatically manages spacing and alignment of form fields.
    """
    
    def __init__(self):
        """Initialize form layout."""
        super().__init__()
        self.setSpacing(12)
        self.setContentsMargins(0, 0, 0, 0)
        self.fields = {}
    
    def add_field(self, name, label_text, input_widget, required=False, help_text=""):
        """
        Add labeled input field to form.
        
        Args:
            name (str): Field name (for retrieving value later)
            label_text (str): Label text
            input_widget (QWidget): Input widget
            required (bool): Whether field is required
            help_text (str): Help text
        
        Returns:
            InputField: Created input field
        """
        field = InputField(label_text, input_widget, required=required, help_text=help_text)
        self.addWidget(field)
        self.fields[name] = field
        return field
    
    def add_text_field(self, name, label_text, placeholder="", required=False):
        """
        Add text input field.
        
        Args:
            name (str): Field name
            label_text (str): Label text
            placeholder (str): Placeholder text
            required (bool): Whether field is required
        
        Returns:
            InputField: Created field
        """
        widget = StyledLineEdit(placeholder)
        return self.add_field(name, label_text, widget, required=required)
    
    def add_text_area(self, name, label_text, placeholder="", required=False):
        """
        Add multi-line text field.
        
        Args:
            name (str): Field name
            label_text (str): Label text
            placeholder (str): Placeholder text
            required (bool): Whether field is required
        
        Returns:
            InputField: Created field
        """
        widget = StyledTextEdit(placeholder)
        return self.add_field(name, label_text, widget, required=required)
    
    def add_combobox(self, name, label_text, items, required=False):
        """
        Add dropdown field.
        
        Args:
            name (str): Field name
            label_text (str): Label text
            items (list): List of items
            required (bool): Whether field is required
        
        Returns:
            InputField: Created field
        """
        widget = StyledComboBox(items)
        return self.add_field(name, label_text, widget, required=required)
    
    def add_checkbox(self, name, label_text):
        """
        Add checkbox field.
        
        Args:
            name (str): Field name
            label_text (str): Label text
        
        Returns:
            InputField: Created field
        """
        widget = StyledCheckBox(label_text)
        field = InputField("", widget)
        self.addWidget(field)
        self.fields[name] = field
        return field
    
    def get_values(self):
        """
        Get all field values.
        
        Returns:
            dict: Dictionary of field names and values
        """
        return {name: field.get_value() for name, field in self.fields.items()}
    
    def set_values(self, values):
        """
        Set all field values.
        
        Args:
            values (dict): Dictionary of field names and values
        """
        for name, value in values.items():
            if name in self.fields:
                self.fields[name].set_value(value)


class DialogSeparator(QFrame):
    """Visual separator for dialog sections."""
    
    def __init__(self):
        """Initialize separator."""
        super().__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("color: #e0e0e0; margin: 8px 0px;")


class SectionTitle(QLabel):
    """Section title within dialog."""
    
    def __init__(self, text):
        """Initialize section title."""
        super().__init__(text)
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        self.setFont(font)
        self.setStyleSheet("color: #161616; margin-top: 8px; margin-bottom: 4px;")


class InfoBox(QFrame):
    """Information box for displaying messages."""
    
    def __init__(self, title="Info", message=""):
        """
        Initialize info box.
        
        Args:
            title (str): Box title
            message (str): Box message
        """
        super().__init__()
        self.setStyleSheet("""
            InfoBox {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #1565c0;")
            layout.addWidget(title_label)
        
        if message:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            message_label.setStyleSheet("color: #0d47a1;")
            layout.addWidget(message_label)
        
        self.setLayout(layout)


class WarningBox(QFrame):
    """Warning box for displaying warnings."""
    
    def __init__(self, title="Warning", message=""):
        """
        Initialize warning box.
        
        Args:
            title (str): Box title
            message (str): Box message
        """
        super().__init__()
        self.setStyleSheet("""
            WarningBox {
                background-color: #fff3e0;
                border: 1px solid #ffe0b2;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #e65100;")
            layout.addWidget(title_label)
        
        if message:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            message_label.setStyleSheet("color: #bf360c;")
            layout.addWidget(message_label)
        
        self.setLayout(layout)


class ErrorBox(QFrame):
    """Error box for displaying errors."""
    
    def __init__(self, title="Error", message=""):
        """
        Initialize error box.
        
        Args:
            title (str): Box title
            message (str): Box message
        """
        super().__init__()
        self.setStyleSheet("""
            ErrorBox {
                background-color: #ffebee;
                border: 1px solid #ef9a9a;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #c62828;")
            layout.addWidget(title_label)
        
        if message:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            message_label.setStyleSheet("color: #b71c1c;")
            layout.addWidget(message_label)
        
        self.setLayout(layout)


class SuccessBox(QFrame):
    """Success box for displaying success messages."""
    
    def __init__(self, title="Success", message=""):
        """
        Initialize success box.
        
        Args:
            title (str): Box title
            message (str): Box message
        """
        super().__init__()
        self.setStyleSheet("""
            SuccessBox {
                background-color: #e8f5e9;
                border: 1px solid #a5d6a7;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        if title:
            title_label = QLabel(title)
            title_font = QFont()
            title_font.setBold(True)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: #2e7d32;")
            layout.addWidget(title_label)
        
        if message:
            message_label = QLabel(message)
            message_label.setWordWrap(True)
            message_label.setStyleSheet("color: #1b5e20;")
            layout.addWidget(message_label)
        
        self.setLayout(layout)
