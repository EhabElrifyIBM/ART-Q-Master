# ============================================================================
# company_email_dialog.py - Company Email Template Dialog Component
# ============================================================================
# Phase 3.1: Enhanced Dialog System
# 
# Provides email template selection and preview dialog.
# ============================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.components.base_dialog import BaseDialog
from ui.components.dialog_components import (
    FormLayout, SectionTitle, DialogSeparator,
    StyledComboBox, StyledTextEdit, InfoBox
)


class CompanyEmailDialog(BaseDialog):
    """
    Company Email Template Selection and Preview Dialog.
    
    Features:
    - Select email template
    - Preview email content
    - Display recipient information
    - Confirm sending
    
    Signals:
    - template_selected(template_name, recipients)
    """
    
    template_selected = pyqtSignal(str, list)  # template_name, recipients
    
    def __init__(self, company_info=None, templates=None, parent=None):
        """
        Initialize company email dialog.
        
        Args:
            company_info (dict): Company information:
                - company_name (str)
                - recipients (list): Email addresses
                - recipient_names (list): Recipient names
            templates (dict): Email templates:
                - template_name: {
                    'subject': str,
                    'body': str
                  }
            parent (QWidget): Parent widget
        """
        super().__init__(
            title="Send Company Email",
            parent=parent,
            width=700,
            height=600
        )
        
        self.company_info = company_info or {}
        self.templates = templates or {}
        self.selected_template = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup email dialog UI."""
        # Company info section
        self.content_layout.addWidget(self._create_company_info_section())
        
        # Template selection section
        self.content_layout.addWidget(self._create_template_section())
        
        # Email preview section
        self.content_layout.addWidget(self._create_preview_section())
    
    def _create_company_info_section(self):
        """Create company information display."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Company Information"))
        layout.addWidget(DialogSeparator())
        
        # Company info
        company_name = self.company_info.get('company_name', 'N/A')
        
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel(f"Company: {company_name}"))
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Recipients
        recipients = self.company_info.get('recipients', [])
        recipient_names = self.company_info.get('recipient_names', [])
        
        recipients_text = ", ".join(recipient_names) if recipient_names else ", ".join(recipients)
        
        recipients_label = QLabel("Recipients:")
        recipients_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(recipients_label)
        
        recipients_display = QLabel(recipients_text)
        recipients_display.setWordWrap(True)
        recipients_display.setStyleSheet("color: #525252; margin-left: 10px;")
        layout.addWidget(recipients_display)
        
        container.setLayout(layout)
        return container
    
    def _create_template_section(self):
        """Create template selection section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Email Template"))
        layout.addWidget(DialogSeparator())
        
        # Template selection
        form = FormLayout()
        template_names = list(self.templates.keys()) if self.templates else ["Default"]
        form.add_combobox("template", "Select Template", template_names, required=True)
        
        self.template_combo = form.fields["template"].input_widget
        self.template_combo.currentTextChanged.connect(self._update_preview)
        
        layout.addLayout(form)
        container.setLayout(layout)
        return container
    
    def _create_preview_section(self):
        """Create email preview section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Email Preview"))
        layout.addWidget(DialogSeparator())
        
        # Subject
        subject_label = QLabel("Subject:")
        subject_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(subject_label)
        
        self.subject_display = QLabel()
        self.subject_display.setWordWrap(True)
        self.subject_display.setStyleSheet("""
            background-color: #f4f4f4;
            border: 1px solid #d8d8d8;
            border-radius: 4px;
            padding: 8px;
            color: #161616;
        """)
        self.subject_display.setMinimumHeight(30)
        layout.addWidget(self.subject_display)
        
        # Body
        body_label = QLabel("Body:")
        body_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(body_label)
        
        self.body_preview = StyledTextEdit()
        self.body_preview.setReadOnly(True)
        self.body_preview.setMinimumHeight(150)
        layout.addWidget(self.body_preview)
        
        container.setLayout(layout)
        
        # Update preview on initialization
        self._update_preview()
        
        return container
    
    def _update_preview(self):
        """Update email preview based on selected template."""
        template_name = self.template_combo.currentText()
        
        if template_name in self.templates:
            template = self.templates[template_name]
            subject = template.get('subject', '')
            body = template.get('body', '')
        else:
            subject = 'Default Subject'
            body = 'Default email body'
        
        self.subject_display.setText(subject)
        self.body_preview.setText(body)
        self.selected_template = template_name
    
    def validate_input(self):
        """Validate template selection."""
        if not self.template_combo.currentText():
            self.show_error("Error", "Please select an email template.")
            return False
        
        return True
    
    def accept_dialog(self):
        """Handle send button click."""
        if self.validate_input():
            recipients = self.company_info.get('recipients', [])
            self.template_selected.emit(self.selected_template, recipients)
            self.is_valid = True
            self.accepted.emit()
            self.accept()
    
    def get_selected_template(self):
        """Get selected template name."""
        return self.selected_template


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    templates = {
        'Follow-up': {
            'subject': 'Follow-up on Your Support Case',
            'body': 'Dear Customer,\n\nThank you for contacting us. We wanted to follow up on your case...'
        },
        'Resolution': {
            'subject': 'Your Issue Has Been Resolved',
            'body': 'Dear Customer,\n\nWe are pleased to inform you that your issue has been resolved...'
        }
    }
    
    company_info = {
        'company_name': 'Acme Corp',
        'recipients': ['john@acme.com', 'jane@acme.com'],
        'recipient_names': ['John Doe', 'Jane Smith']
    }
    
    dialog = CompanyEmailDialog(company_info, templates)
    if dialog.exec_():
        print(f"Template selected: {dialog.get_selected_template()}")
    else:
        print("Dialog cancelled")
