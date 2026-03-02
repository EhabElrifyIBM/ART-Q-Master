# ============================================================================
# company_metadata_display.py - Company Information Display
# ============================================================================
# Phase 5.2: Company Metadata Integration
#
# Displays company information including:
# - Company name
# - Contact email/phone
# - State/Province
# - Local time calculation
# ============================================================================

import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Lazy imports
timezone_map = None


def _init_timezone_map():
    """Initialize timezone map."""
    global timezone_map
    try:
        from utils.timezone_map import get_timezone_offset, calculate_local_time
        timezone_map = {
            'get_offset': get_timezone_offset,
            'calc_local': calculate_local_time
        }
        return True
    except Exception as e:
        print(f"[WARNING] Could not load timezone_map: {e}")
        return False


class CompanyMetadataDialog(QDialog):
    """
    Dialog displaying company information and metadata.
    
    Shows:
    - Company name
    - Contact information (email, phone)
    - State/Province
    - Local time for the company location
    - Number of cases to process
    """
    
    def __init__(self, company_data, parent=None):
        """
        Initialize metadata dialog.
        
        Args:
            company_data (dict): Company information
                - company_name (str)
                - email (str)
                - phone (str, optional)
                - state_province (str, optional)
                - case_count (int)
                - cases (list of case dicts)
                - font_settings (dict, optional): Font settings from theme manager
        """
        super().__init__(parent)
        self.company_data = company_data
        self.font_settings = company_data.get('font_settings', None)
        self.setWindowTitle("Company Information")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)

        # --- Apply UI_DIALOG_THEME_REFERENCE.md styles ---
        self.setStyleSheet("""
            QDialog {
                background-color: #f7f9fa;
                border-radius: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 21px;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 21px;
                font-weight: 600;
                color: #222;
            }
            QPushButton {
                background-color: #1976D2;
                color: #fff;
                font-weight: 600;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 21px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1565C0;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QProgressBar {
                border: 1px solid #b0bec5;
                border-radius: 6px;
                text-align: center;
                height: 14px;
                font-size: 18px;
                background: #eceff1;
            }
            QProgressBar::chunk {
                background-color: #43A047;
                border-radius: 6px;
            }
            QFrame {
                background: #fff;
                border-radius: 10px;
            }
            QCheckBox {
                font-size: 21px;
            }
        """)
        
        # Initialize timezone map
        _init_timezone_map()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        
        # ===== Helper function to get font =====
        def get_font(size=12, bold=False):
            """Get font with optional theme settings"""
            if self.font_settings:
                font = QFont(self.font_settings.get('font_family', 'Segoe UI'))
                font.setPointSize(size)
                if bold:
                    font.setBold(True)
                return font
            else:
                font = QFont()
                font.setPointSize(size)
                if bold:
                    font.setBold(True)
                return font
        
        # ===== HEADER =====
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #E3F2FD;
                border: 1px solid #BBDEFB;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_frame)
        
        company_name = self.company_data.get('company_name', 'Unknown Company')
        title = QLabel(f"🏢 {company_name}")
        title.setFont(get_font(17, bold=True))
        header_layout.addWidget(title)
        
        header_layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(header_frame)
        
        # ===== CONTACT INFORMATION =====
        contact_group = QFrame()
        contact_group.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        contact_layout = QGridLayout(contact_group)
        contact_layout.setSpacing(12)
        
        # Email
        email_label = QLabel("📧 Email:")
        email_label.setFont(get_font(13, bold=True))
        contact_layout.addWidget(email_label, 0, 0)
        
        email_value = QLabel(self.company_data.get('email', 'N/A'))
        email_value.setFont(get_font(13))
        email_value.setStyleSheet("color: #0f62fe; font-weight: normal;")
        contact_layout.addWidget(email_value, 0, 1)
        
        # Phone (if available)
        phone = self.company_data.get('phone', None)
        if phone:
            phone_label = QLabel("📞 Phone:")
            phone_label.setFont(get_font(13, bold=True))
            contact_layout.addWidget(phone_label, 1, 0)
            
            phone_value = QLabel(str(phone))
            phone_value.setFont(get_font(13))
            phone_value.setStyleSheet("color: #0f62fe; font-weight: normal;")
            contact_layout.addWidget(phone_value, 1, 1)
            current_row = 2
        else:
            current_row = 1
        
        contact_group.setLayout(contact_layout)
        layout.addWidget(contact_group)
        
        # ===== LOCATION & TIME =====
        location_group = QFrame()
        location_group.setStyleSheet("""
            QFrame {
                background-color: #F3E5F5;
                border: 1px solid #E1BEE7;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        location_layout = QGridLayout(location_group)
        location_layout.setSpacing(12)
        
        # State/Province
        state = self.company_data.get('state_province', None)
        if state:
            location_label = QLabel("📍 Location:")
            location_label.setFont(get_font(13, bold=True))
            location_layout.addWidget(location_label, 0, 0)
            
            location_value = QLabel(str(state))
            location_value.setFont(get_font(13))
            location_value.setStyleSheet("color: #6A1B9A; font-weight: normal;")
            location_layout.addWidget(location_value, 0, 1)
            
            # Local time (Phase 5.2: Timezone integration)
            if timezone_map:
                try:
                    local_time = timezone_map['calc_local'](state)
                    if local_time:
                        time_label = QLabel("🕐 Local Time:")
                        time_label.setFont(get_font(13, bold=True))
                        location_layout.addWidget(time_label, 1, 0)
                        
                        time_value = QLabel(local_time.strftime("%H:%M:%S %Z"))
                        time_value.setFont(get_font(13, bold=True))
                        time_value.setStyleSheet("color: #6A1B9A; font-weight: bold;")
                        location_layout.addWidget(time_value, 1, 1)
                except Exception as e:
                    print(f"[WARNING] Could not calculate local time: {e}")
        
        location_group.setLayout(location_layout)
        layout.addWidget(location_group)
        
        # ===== CASE INFORMATION =====
        case_group = QFrame()
        case_group.setStyleSheet("""
            QFrame {
                background-color: #E8F5E9;
                border: 1px solid #C8E6C9;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        case_layout = QGridLayout(case_group)
        case_layout.setSpacing(12)
        
        # Case count
        case_count = self.company_data.get('case_count', 0)
        case_count_label = QLabel("📋 Cases to Process:")
        case_count_label.setFont(get_font(13, bold=True))
        case_layout.addWidget(case_count_label, 0, 0)
        
        case_count_value = QLabel(f"{case_count} case{'s' if case_count != 1 else ''}")
        case_count_value.setFont(get_font(13, bold=True))
        case_count_value.setStyleSheet("color: #2E7D32; font-weight: bold;")
        case_layout.addWidget(case_count_value, 0, 1)
        
        case_group.setLayout(case_layout)
        layout.addWidget(case_group)
        
        # ===== BUTTON =====
        layout.addStretch()
        
        close_btn = QPushButton("✓ Understood - Continue")
        close_btn.setMinimumHeight(40)
        close_btn.setFont(get_font(13))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f62fe;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0353e9;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
    
    @staticmethod
    def show_company_info(company_data, parent=None):
        """
        Show company metadata dialog.
        
        Args:
            company_data (dict): Company information
            parent: Parent widget
        
        Returns:
            bool: True if user accepted, False if cancelled
        """
        dialog = CompanyMetadataDialog(company_data, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted


def extract_company_metadata(row, excel_df=None):
    """
    Extract company metadata from a row.
    
    Args:
        row: DataFrame row with company data
        excel_df: Full DataFrame (optional, for lookup)
    
    Returns:
        dict: Company metadata
    """
    try:
        metadata = {
            'company_name': row.get('Company Name', 'Unknown'),
            'email': row.get('Email', '') or row.get('Primary Email (Contact) (Contact)', ''),
            'phone': row.get('Phone Number', '') or row.get('Contact Mobile Phone', ''),
            'state_province': row.get('State/Province', '') or row.get('State/Province (Case) (Case)', ''),
            'contact_name': row.get('Customer Name', '') or row.get('Contact Name', ''),
        }
        return metadata
    except Exception as e:
        print(f"[WARNING] Error extracting company metadata: {e}")
        return {}


def format_company_metadata_display(row, excel_df=None):
    """
    Format company metadata for display.
    
    Args:
        row: DataFrame row
        excel_df: Full DataFrame (optional)
    
    Returns:
        str: Formatted display string
    """
    metadata = extract_company_metadata(row, excel_df)
    
    display_parts = [
        f"🏢 {metadata.get('company_name', 'Company')}",
        f"📧 {metadata.get('email', 'No email')}",
    ]
    
    if metadata.get('phone'):
        display_parts.append(f"📞 {metadata['phone']}")
    
    if metadata.get('state_province'):
        display_parts.append(f"📍 {metadata['state_province']}")
    
    return " | ".join(display_parts)
