# ============================================================================
# case_review_dialog.py - Enhanced Case Review Dialog Component
# ============================================================================
# Phase 3.1: Enhanced Dialog System
# 
# Provides enhanced case review dialog with company metadata and navigation.
# ============================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.components.base_dialog import BaseDialog
from ui.components.dialog_components import (
    FormLayout, DialogTitle, SectionTitle, DialogSeparator,
    StyledLineEdit, StyledTextEdit, StyledComboBox, InfoBox, WarningBox
)


class CaseReviewDialog(BaseDialog):
    """
    Enhanced Case Review Dialog for Case Reviewer.
    
    Features:
    - Display case information and company metadata
    - Show navigation status (current/total cases)
    - Provide action selection (Call, Email, SMS, DND, etc.)
    - Display previous case information if available
    - Add case notes and closing code
    
    Signals:
    - case_action_selected(action, notes, code)
    - navigation_requested(direction)  # 'prev' or 'next'
    """
    
    case_action_selected = pyqtSignal(str, str, str)  # action, notes, closing_code
    navigation_requested = pyqtSignal(str)  # 'prev' or 'next'
    
    def __init__(self, case_data=None, parent=None):
        """
        Initialize case review dialog.
        
        Args:
            case_data (dict): Dictionary with case information:
                - case_id (str)
                - customer_name (str)
                - company_name (str)
                - email (str)
                - phone (str)
                - case_notes (str)
                - current_position (int)
                - total_cases (int)
                - has_previous_case (bool)
                - has_next_case (bool)
            parent (QWidget): Parent widget
        """
        super().__init__(
            title="Case Review - Enhanced",
            parent=parent,
            width=600,
            height=700
        )
        
        self.case_data = case_data or {}
        self.action_selected = None
        self.closing_code = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup case review dialog UI."""
        # Case info section
        self.content_layout.addWidget(self._create_case_info_section())
        
        # Actions section
        self.content_layout.addWidget(self._create_actions_section())
        
        # Notes section
        self.content_layout.addWidget(self._create_notes_section())
        
        # Navigation buttons (replaces standard OK/Cancel)
        self._setup_navigation_buttons()
    
    def _create_case_info_section(self):
        """Create case information display."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with navigation status
        header_layout = QHBoxLayout()
        
        title = SectionTitle("Case Information")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Position indicator
        current = self.case_data.get('current_position', 1)
        total = self.case_data.get('total_cases', 1)
        position_label = QLabel(f"[{current}/{total}]")
        position_font = QFont()
        position_font.setPointSize(9)
        position_label.setFont(position_font)
        position_label.setStyleSheet("color: #a8a8a8;")
        header_layout.addWidget(position_label)
        
        layout.addLayout(header_layout)
        
        # Case info form
        form = FormLayout()
        
        # Case ID
        case_id = self.case_data.get('case_id', '')
        form.add_text_field("case_id", "Case ID", default_text=case_id)
        form.fields["case_id"].input_widget.setReadOnly(True)
        
        # Customer name
        customer = self.case_data.get('customer_name', '')
        form.add_text_field("customer", "Customer Name", default_text=customer)
        form.fields["customer"].input_widget.setReadOnly(True)
        
        # Company name
        company = self.case_data.get('company_name', '')
        form.add_text_field("company", "Company Name", default_text=company)
        form.fields["company"].input_widget.setReadOnly(True)
        
        # Email
        email = self.case_data.get('email', '')
        form.add_text_field("email", "Email", default_text=email)
        form.fields["email"].input_widget.setReadOnly(True)
        
        # Phone
        phone = self.case_data.get('phone', '')
        form.add_text_field("phone", "Phone", default_text=phone)
        form.fields["phone"].input_widget.setReadOnly(True)
        
        layout.addLayout(form)
        container.setLayout(layout)
        return container
    
    def _create_actions_section(self):
        """Create action selection section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Action"))
        layout.addWidget(DialogSeparator())
        
        # Action selection
        form = FormLayout()
        actions = ["Call Customer", "Send Email", "Send SMS", "Do Not Call", "Escalate"]
        form.add_combobox("action", "Select Action", actions, required=True)
        
        layout.addLayout(form)
        self.action_field = form.fields["action"].input_widget
        
        container.setLayout(layout)
        return container
    
    def _create_notes_section(self):
        """Create notes and closing code section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Details"))
        layout.addWidget(DialogSeparator())
        
        # Case notes
        case_notes = self.case_data.get('case_notes', '')
        notes_area = StyledTextEdit()
        notes_area.setText(case_notes)
        notes_area.setReadOnly(True)
        notes_area.setMinimumHeight(60)
        
        layout.addWidget(QLabel("Case Notes"))
        layout.addWidget(notes_area)
        
        # Closing code
        form = FormLayout()
        codes = ["Resolved", "Unresolved", "Duplicate", "Invalid", "Escalated"]
        form.add_combobox("closing_code", "Closing Code", codes, required=True)
        
        layout.addLayout(form)
        self.closing_code_field = form.fields["closing_code"].input_widget
        
        container.setLayout(layout)
        return container
    
    def _setup_navigation_buttons(self):
        """Setup navigation buttons instead of OK/Cancel."""
        # Clear default buttons
        self.ok_button.setText("Submit & Next")
        self.cancel_button.setText("Previous")
        
        # Disable previous button if no previous case
        if not self.case_data.get('has_previous_case', False):
            self.cancel_button.setEnabled(False)
            self.cancel_button.setText("Previous (Unavailable)")
        
        # Disable next button if no next case
        if not self.case_data.get('has_next_case', False):
            self.ok_button.setText("Submit & Close")
    
    def validate_input(self):
        """Validate action and closing code are selected."""
        if not self.action_field.currentText():
            self.show_error("Error", "Please select an action.")
            return False
        
        if not self.closing_code_field.currentText():
            self.show_error("Error", "Please select a closing code.")
            return False
        
        return True
    
    def accept_dialog(self):
        """Handle submit (OK button)."""
        if self.validate_input():
            self.action_selected = self.action_field.currentText()
            self.closing_code = self.closing_code_field.currentText()
            self.case_action_selected.emit(self.action_selected, "", self.closing_code)
            self.accept()
    
    def reject_dialog(self):
        """Handle previous button (Cancel button)."""
        self.navigation_requested.emit('prev')
        self.accept()
    
    def get_action_data(self):
        """Get selected action and closing code."""
        return {
            'action': self.action_selected,
            'closing_code': self.closing_code
        }


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    case_data = {
        'case_id': 'CASE-001',
        'customer_name': 'John Doe',
        'company_name': 'Acme Corp',
        'email': 'john@acme.com',
        'phone': '+1-555-0123',
        'case_notes': 'Customer reported issue with product. Needs callback.',
        'current_position': 1,
        'total_cases': 10,
        'has_previous_case': False,
        'has_next_case': True,
    }
    
    dialog = CaseReviewDialog(case_data)
    if dialog.exec_():
        print(f"Action: {dialog.action_selected}")
        print(f"Code: {dialog.closing_code}")
    else:
        print("Dialog rejected")
