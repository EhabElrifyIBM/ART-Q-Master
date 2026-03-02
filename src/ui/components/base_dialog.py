# ============================================================================
# base_dialog.py - Base Dialog Component
# ============================================================================
# Phase 2.1: Base Dialog Architecture
# 
# Provides a reusable base class for all PyQt5 dialogs in the application.
# Eliminates code duplication across dialog implementations.
# 
# Features:
# - Standard dialog styling and layout
# - Common button handling (OK, Cancel, Custom buttons)
# - Dialog lifecycle management
# - Consistent user experience across all dialogs
# - Built-in validation support
# - Easy customization for specific use cases
# ============================================================================

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QWidget, QFrame, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QIcon


class BaseDialog(QDialog):
    """
    Base class for all dialogs in the application.
    
    Provides common functionality for dialog management, styling, and button handling.
    
    Features:
    - Consistent styling across all dialogs
    - Standard button handling
    - Built-in dialog lifecycle management
    - Easy customization through inheritance
    - Validation support
    - Signal emission for dialog actions
    
    Usage:
        class MyCustomDialog(BaseDialog):
            def __init__(self, parent=None):
                super().__init__(
                    title="My Custom Dialog",
                    parent=parent
                )
                self.setup_ui()
            
            def setup_ui(self):
                # Add custom UI elements to self.content_layout
                label = QLabel("Custom Content")
                self.content_layout.addWidget(label)
            
            def validate_input(self):
                # Override to add validation
                return True
    """
    
    # Signals
    accepted = pyqtSignal()
    rejected = pyqtSignal()
    
    def __init__(self, title="Dialog", parent=None, width=500, height=300):
        """
        Initialize base dialog.
        
        Args:
            title (str): Dialog window title
            parent (QWidget): Parent widget
            width (int): Dialog width in pixels
            height (int): Dialog height in pixels
        """
        super().__init__(parent)
        
        self.title = title
        self.width = width
        self.height = height
        
        # Dialog state
        self.is_valid = False
        self.result_data = None
        
        # Setup UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components."""
        # Window properties
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, self.width, self.height)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setModal(True)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # Title label (optional, can be hidden)
        self.title_label = QLabel(self.title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        main_layout.addWidget(self.title_label)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #CCCCCC;")
        main_layout.addWidget(separator)
        
        # Content area (for subclasses to add their widgets)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        main_layout.addLayout(self.content_layout, 1)
        
        # Separator line before buttons
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("color: #CCCCCC;")
        main_layout.addWidget(separator2)
        
        # Button layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()
        
        # Standard buttons
        self.ok_button = self.create_button("OK", self.accept_dialog, primary=True)
        self.cancel_button = self.create_button("Cancel", self.reject_dialog, primary=False)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        main_layout.addLayout(button_layout)
        
        # Apply styling
        self.apply_styling()
        
        self.setLayout(main_layout)
        
    def create_button(self, text, callback, primary=False):
        """
        Create a styled button.
        
        Args:
            text (str): Button text
            callback (callable): Function to call when clicked
            primary (bool): Whether this is a primary button (OK) or secondary (Cancel)
        
        Returns:
            QPushButton: Configured button
        """
        button = QPushButton(text)
        button.clicked.connect(callback)
        button.setCursor(Qt.PointingHandCursor)
        button.setMinimumWidth(80)
        button.setMinimumHeight(36)
        
        # Apply primary or secondary styling
        if primary:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #0f62fe;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    padding: 6px 20px;
                }
                QPushButton:hover {
                    background-color: #0353e9;
                }
                QPushButton:pressed {
                    background-color: #0242d3;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f4f4f4;
                    color: #161616;
                    border: 1px solid #d8d8d8;
                    border-radius: 4px;
                    padding: 6px 20px;
                }
                QPushButton:hover {
                    background-color: #e8e8e8;
                }
                QPushButton:pressed {
                    background-color: #d8d8d8;
                }
            """)
        
        return button
    
    def apply_styling(self):
        """Apply consistent styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                color: #161616;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #d8d8d8;
                border-radius: 4px;
                padding: 6px;
                background-color: #ffffff;
                color: #161616;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #0f62fe;
                padding: 5px;
            }
        """)
    
    def validate_input(self):
        """
        Validate dialog input.
        
        Override in subclasses to add validation logic.
        
        Returns:
            bool: True if input is valid, False otherwise
        """
        return True
    
    def get_data(self):
        """
        Get data from the dialog.
        
        Override in subclasses to return custom data.
        
        Returns:
            dict or any: Dialog data/result
        """
        return self.result_data
    
    def accept_dialog(self):
        """Handle OK button click."""
        if self.validate_input():
            self.is_valid = True
            self.accepted.emit()
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Please check your input and try again.",
                QMessageBox.Ok
            )
    
    def reject_dialog(self):
        """Handle Cancel button click."""
        self.is_valid = False
        self.rejected.emit()
        self.reject()
    
    def show_error(self, title, message):
        """
        Show error message.
        
        Args:
            title (str): Error title
            message (str): Error message
        """
        QMessageBox.critical(self, title, message, QMessageBox.Ok)
    
    def show_info(self, title, message):
        """
        Show info message.
        
        Args:
            title (str): Info title
            message (str): Info message
        """
        QMessageBox.information(self, title, message, QMessageBox.Ok)
    
    def show_warning(self, title, message):
        """
        Show warning message.
        
        Args:
            title (str): Warning title
            message (str): Warning message
        """
        QMessageBox.warning(self, title, message, QMessageBox.Ok)
    
    def add_button(self, text, callback, primary=False):
        """
        Add a custom button to the dialog.
        
        Args:
            text (str): Button text
            callback (callable): Function to call when clicked
            primary (bool): Whether this is a primary button
        
        Returns:
            QPushButton: The created button
        """
        button = self.create_button(text, callback, primary=primary)
        # Insert before OK/Cancel buttons
        layout = self.layout()
        button_layout = layout.itemAt(layout.count() - 1).layout()
        button_layout.insertWidget(button_layout.count() - 2, button)
        return button
    
    def set_title(self, title):
        """Set dialog title."""
        self.title = title
        self.title_label.setText(title)
        self.setWindowTitle(title)
    
    def closeEvent(self, event):
        """Handle window close button."""
        self.reject_dialog()
        event.accept()


class ConfirmDialog(BaseDialog):
    """
    Simple confirmation dialog for yes/no decisions.
    
    Usage:
        dialog = ConfirmDialog(
            "Delete Item?",
            "Are you sure you want to delete this item?",
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            # User clicked Yes
            pass
    """
    
    def __init__(self, title, message, parent=None, yes_text="Yes", no_text="No"):
        """
        Initialize confirmation dialog.
        
        Args:
            title (str): Dialog title
            message (str): Confirmation message
            parent (QWidget): Parent widget
            yes_text (str): Yes button text
            no_text (str): No button text
        """
        super().__init__(title, parent, width=400, height=150)
        self.yes_text = yes_text
        self.no_text = no_text
        self.message_text = message
        self.setup_ui_content()
    
    def setup_ui_content(self):
        """Setup confirmation dialog content."""
        message_label = QLabel(self.message_text)
        message_label.setWordWrap(True)
        message_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        message_label.setFont(font)
        self.content_layout.addWidget(message_label, 1)
        
        # Update button text
        self.ok_button.setText(self.yes_text)
        self.cancel_button.setText(self.no_text)


class InputDialog(BaseDialog):
    """
    Simple input dialog for getting text input from user.
    
    Usage:
        dialog = InputDialog(
            "Enter Name",
            "Please enter your name:",
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_data()
    """
    
    def __init__(self, title, label_text, parent=None, default_text=""):
        """
        Initialize input dialog.
        
        Args:
            title (str): Dialog title
            label_text (str): Label text above input field
            parent (QWidget): Parent widget
            default_text (str): Default input text
        """
        super().__init__(title, parent, width=400, height=150)
        self.label_text = label_text
        self.default_text = default_text
        self.input_field = None
        self.setup_ui_content()
    
    def setup_ui_content(self):
        """Setup input dialog content."""
        from PyQt5.QtWidgets import QLineEdit
        
        label = QLabel(self.label_text)
        self.content_layout.addWidget(label)
        
        self.input_field = QLineEdit()
        self.input_field.setText(self.default_text)
        self.input_field.setMinimumHeight(36)
        self.content_layout.addWidget(self.input_field)
    
    def validate_input(self):
        """Validate input is not empty."""
        if not self.input_field.text().strip():
            self.show_error("Error", "Please enter a value.")
            return False
        return True
    
    def get_data(self):
        """Get entered text."""
        return self.input_field.text().strip()


# ============================================================================
# ENHANCEMENTS (Phase 3.4 & 5.4): Theme Support & Keyboard Locking
# ============================================================================

def apply_theme_to_dialog(dialog, theme='light'):
    """
    Apply theme to dialog (light or dark mode).
    
    Args:
        dialog (QDialog): Dialog to theme
        theme (str): 'light' or 'dark'
    """
    if theme == 'dark':
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                border: 1px solid #333333;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 6px;
                background-color: #2E2E2E;
                color: #FFFFFF;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #0f62fe;
                padding: 5px;
            }
            QPushButton {
                background-color: #0f62fe;
                color: white;
                border-radius: 4px;
                padding: 6px 20px;
            }
            QPushButton:hover {
                background-color: #0353e9;
            }
        """)
    else:  # light theme (default)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
            }
            QLabel {
                color: #161616;
            }
            QLineEdit, QTextEdit, QComboBox {
                border: 1px solid #D8D8D8;
                border-radius: 4px;
                padding: 6px;
                background-color: #FFFFFF;
                color: #161616;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #0f62fe;
                padding: 5px;
            }
        """)


def enable_keyboard_lock_on_dialog(dialog, allow_navigation_keys=True):
    """
    Enable keyboard locking on dialog to prevent accidental input.
    
    Args:
        dialog (QDialog): Dialog to lock keyboard on
        allow_navigation_keys (bool): Allow Tab, Enter, Escape
    
    Phase 3.4: Prevents keyboard input on dialogs
    """
    original_keyPressEvent = dialog.keyPressEvent
    
    def locked_keyPressEvent(event):
        key = event.key()
        
        if allow_navigation_keys:
            # Allow navigation keys
            if key in (Qt.Key_Tab, Qt.Key_Backtab, Qt.Key_Return, Qt.Key_Enter,
                      Qt.Key_Escape, Qt.Key_Up, Qt.Key_Down):
                original_keyPressEvent(event)
                return
        
        # Block other keys
        event.ignore()
    
    dialog.keyPressEvent = locked_keyPressEvent


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Example: Confirmation dialog
    confirm_dialog = ConfirmDialog(
        "Delete File?",
        "Are you sure you want to delete file.txt?",
        yes_text="Delete",
        no_text="Cancel"
    )
    
    if confirm_dialog.exec_():
        print("User clicked Yes")
    else:
        print("User clicked No")
    
    # Example: Input dialog
    input_dialog = InputDialog(
        "Enter Name",
        "Please enter your name:",
        default_text="John Doe"
    )
    
    if input_dialog.exec_():
        print(f"User entered: {input_dialog.get_data()}")
    else:
        print("User cancelled")
