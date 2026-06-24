# ============================================================================
# feedback_dialog.py - Per-Case Feedback Dialog Component
# ============================================================================
# Phase 3.1: Enhanced Dialog System
# 
# Provides structured feedback form for case feedback submission.
# ============================================================================

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ui.components.base_dialog import BaseDialog
from ui.components.dialog_components import (
    FormLayout, SectionTitle, DialogSeparator,
    StyledLineEdit, StyledTextEdit, StyledComboBox, StyledCheckBox, InfoBox
)


class FeedbackDialog(BaseDialog):
    """
    Per-Case Feedback Dialog for collecting feedback.
    
    Features:
    - Case reference information
    - Satisfaction rating
    - Structured feedback form
    - Optional follow-up options
    - Attachment indication
    
    Signals:
    - feedback_submitted(feedback_data)
    """
    
    feedback_submitted = pyqtSignal(dict)  # feedback_data
    
    def __init__(self, case_info=None, parent=None):
        """
        Initialize feedback dialog.
        
        Args:
            case_info (dict): Case information:
                - case_id (str)
                - customer_name (str)
                - issue_summary (str)
                - resolution (str)
            parent (QWidget): Parent widget
        """
        super().__init__(
            title="Case Feedback",
            parent=parent,
            width=600,
            height=700
        )
        
        self.case_info = case_info or {}
        self.feedback_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup feedback dialog UI."""
        # Case reference
        self.content_layout.addWidget(self._create_case_reference_section())
        
        # Satisfaction section
        self.content_layout.addWidget(self._create_satisfaction_section())
        
        # Feedback section
        self.content_layout.addWidget(self._create_feedback_section())
        
        # Follow-up options
        self.content_layout.addWidget(self._create_followup_section())
    
    def _create_case_reference_section(self):
        """Create case reference display."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Case Reference"))
        layout.addWidget(DialogSeparator())
        
        # Case info
        case_id = self.case_info.get('case_id', 'N/A')
        customer = self.case_info.get('customer_name', 'N/A')
        summary = self.case_info.get('issue_summary', 'N/A')
        resolution = self.case_info.get('resolution', 'N/A')
        
        form = FormLayout()
        form.add_text_field("case_id", "Case ID", default_text=case_id)
        form.fields["case_id"].input_widget.setReadOnly(True)
        
        form.add_text_field("customer", "Customer", default_text=customer)
        form.fields["customer"].input_widget.setReadOnly(True)
        
        form.add_text_area("summary", "Issue Summary", default_text=summary)
        form.fields["summary"].input_widget.setReadOnly(True)
        form.fields["summary"].input_widget.setMinimumHeight(50)
        
        form.add_text_area("resolution", "Resolution", default_text=resolution)
        form.fields["resolution"].input_widget.setReadOnly(True)
        form.fields["resolution"].input_widget.setMinimumHeight(50)
        
        layout.addLayout(form)
        container.setLayout(layout)
        return container
    
    def _create_satisfaction_section(self):
        """Create satisfaction rating section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Customer Satisfaction"))
        layout.addWidget(DialogSeparator())
        
        # Rating options
        ratings = ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"]
        
        form = FormLayout()
        form.add_combobox("rating", "Overall Satisfaction", ratings, required=True)
        self.rating_field = form.fields["rating"].input_widget
        
        layout.addLayout(form)
        container.setLayout(layout)
        return container
    
    def _create_feedback_section(self):
        """Create detailed feedback section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Feedback Details"))
        layout.addWidget(DialogSeparator())
        
        form = FormLayout()
        
        # What went well
        form.add_text_area(
            "went_well",
            "What Went Well?",
            placeholder="Tell us what we did right...",
        )
        form.fields["went_well"].input_widget.setMinimumHeight(70)
        
        # What could improve
        form.add_text_area(
            "improve",
            "What Could Be Improved?",
            placeholder="Any suggestions for improvement...",
        )
        form.fields["improve"].input_widget.setMinimumHeight(70)
        
        # Additional comments
        form.add_text_area(
            "comments",
            "Additional Comments",
            placeholder="Any other feedback...",
        )
        form.fields["comments"].input_widget.setMinimumHeight(70)
        
        layout.addLayout(form)
        self.feedback_form = form
        container.setLayout(layout)
        return container
    
    def _create_followup_section(self):
        """Create follow-up options section."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        layout.addWidget(SectionTitle("Follow-up"))
        layout.addWidget(DialogSeparator())
        
        # Contact options
        layout.addWidget(QLabel("How should we contact you for follow-up?"))
        
        form = FormLayout()
        
        # Email checkbox
        form.add_checkbox("follow_email", "Email me a summary")
        
        # Phone checkbox
        form.add_checkbox("follow_phone", "Call me with results")
        
        # Newsletter checkbox
        form.add_checkbox("newsletter", "Subscribe to our newsletter")
        
        layout.addLayout(form)
        self.followup_form = form
        container.setLayout(layout)
        return container
    
    def validate_input(self):
        """Validate required fields."""
        if not self.rating_field.currentText():
            self.show_error("Error", "Please select a satisfaction rating.")
            return False
        
        return True
    
    def accept_dialog(self):
        """Handle submit button click."""
        if self.validate_input():
            # Collect feedback data
            self.feedback_data = {
                'case_id': self.case_info.get('case_id'),
                'rating': self.rating_field.currentText(),
                'went_well': self.feedback_form.fields.get("went_well", {}).get("value", ""),
                'improve': self.feedback_form.fields.get("improve", {}).get("value", ""),
                'comments': self.feedback_form.fields.get("comments", {}).get("value", ""),
                'follow_email': self.followup_form.fields.get("follow_email", {}).get("checked", False),
                'follow_phone': self.followup_form.fields.get("follow_phone", {}).get("checked", False),
                'newsletter': self.followup_form.fields.get("newsletter", {}).get("checked", False),
            }
            
            self.feedback_submitted.emit(self.feedback_data)
            self.is_valid = True
            self.accepted.emit()
            self.accept()
    
    def get_feedback_data(self):
        """Get submitted feedback data."""
        return self.feedback_data


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    case_info = {
        'case_id': 'CASE-001',
        'customer_name': 'John Doe',
        'issue_summary': 'Product not working as expected',
        'resolution': 'Sent replacement unit'
    }
    
    dialog = FeedbackDialog(case_info)
    if dialog.exec_():
        feedback = dialog.get_feedback_data()
        print(f"Feedback received: {feedback}")
    else:
        print("Dialog cancelled")
