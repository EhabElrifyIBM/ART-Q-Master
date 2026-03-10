# ============================================================================
# CaseReviewer_v2.py - Review IN-PROGRESS Cases (With Dialer) - ENHANCED
# ============================================================================
# Phase 5 Enhanced Version:
# - Company Process is NOW ISOLATED (separate button in Dispatcher)
# - Companies Process will NOT auto-run after CaseReviewer
# 
# Core functionality:
# - Opens Dialer and logs in (skips "not ready chat" toggle)
# - Opens Dynamics CRM
# - Shows closing code dialog for each case
# - Processes based on selected action (call, send SMS/Email, DND, etc.)
# - Updates status to 'Closed'
# ============================================================================

import os
import sys
import time
import traceback
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QInputDialog, QWidget, QCheckBox, QScrollArea, QProgressBar, QMessageBox,
    QLineEdit, QRadioButton, QButtonGroup, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.settings_aware_dialog import SettingsAwareMixin

# Ensure both src and this directory are in path for proper imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

art_q_dir = os.path.dirname(os.path.abspath(__file__))
if art_q_dir not in sys.path:
    sys.path.insert(0, art_q_dir)

# Phase 3.2: Theme and Accessibility Managers (imported lazily after QApplication)
theme_manager = None
accessibility_manager = None
error_logger = None

# Import shared functions
from SharedFunctions import (
    CONFIG_MANAGER,
    AGENT_NAME,
    EXCEL_BASE_PATH,
    CACHE_DIRECTORY,
    EXCEL_SHEET_NAME,
    REFRESH_INTERVAL,
    Chrome_ART_Profile,
    todays_excel_path,
    find_column_case_insensitive,
    case_search_and_open,
    solution_provided_check_and_skip,
    eticket_check_and_skip,
    serial_extraction,
    customer_name_extraction,
    formatting_texts_sms,
    formatting_texts_email,
    send_SMS,
    send_Email,
    add_Case_Note,
    get_case_note,
    update_cache_file,
    enable_windows_inhibit,
    disable_windows_inhibit,
    keep_driver_alive,
    wait_for_excel_file,
    perform_dialer_login,
    perform_call_flow,
    DND_CX,
    excelCaseClosingCode,
    SMSText,
    safe_find,
    switch_to_crm_window,
    show_file_search_popup,
    get_todays_cache_path,
    check_existing_cache_and_ask,
)

# CRM URL - Dynamics 365
CRM_URL = "https://lenovo-plrs-prod.crm5.dynamics.com/main.aspx?appid=00fd771a-9081-e911-a83a-000d3a07fba2&forceUCI=1&pagetype=dashboard&id=4e76815a-1f63-df11-ae90-00155d2e3002&type=system&_canOverride=true"

# ============================================================================
# PHASE 4.2: CACHE RESUME ENHANCEMENTS
# ============================================================================
def count_remaining_cases(cache_file, sheet_name=EXCEL_SHEET_NAME):
    """
    Count how many cases remain to be processed in the cache file.
    
    Updated: Counts cases that ARE 'in_progress' or 'skipped' (cases still pending).
    This gives users accurate count of work still remaining in resume dialog.
    
    Args:
        cache_file: Path to the cache Excel file
        sheet_name: Sheet name to read from
    
    Returns:
        Tuple of (remaining_in_progress_or_skipped, display_message)
        - remaining_in_progress_or_skipped: Number of cases still in 'in_progress' or 'skipped'
        - display_message: Formatted message for UI display
    """
    try:
        if not os.path.exists(cache_file):
            return 0, "Cache file not found"
        
        # Read cache file
        df_cache = pd.read_excel(cache_file, sheet_name=sheet_name)
        
        # Find Status column
        status_col = find_column_case_insensitive(df_cache, 'Status')
        if not status_col:
            # Fallback: count all cases if Status not found
            total_remaining = len(df_cache)
        else:
            # Count cases that ARE 'in_progress' or 'skipped' (still pending review)
            statuses = df_cache[status_col].astype(str).str.lower().str.strip()
            remaining_in_progress = len(df_cache[statuses.isin(['in_progress', 'skipped'])])
            total_remaining = remaining_in_progress
        
        if total_remaining == 0:
            return 0, "No cases remain to review"
        elif total_remaining == 1:
            return 1, "1 case remains"
        else:
            return total_remaining, f"{total_remaining} cases remain"
    
    except Exception as e:
        print(f"[WARN] Error counting remaining cases: {e}")
        return 0, "Unable to determine remaining cases"

def check_existing_cache_and_ask_enhanced(cache_path, mode_name="Case Reviewer"):
    """
    Phase 4.2 Enhanced Version: Check if cache exists and show remaining case count.
    
    Modified version of check_existing_cache_and_ask that:
    - Counts remaining cases in the cache file
    - Displays count in resume confirmation dialog
    - Provides better decision-making information
    
    Args:
        cache_path: Path to today's cache file
        mode_name: Display name for the mode
    
    Returns:
        - "RESUME" = Resume from existing cache
        - "NEW" = Create new cache from main Excel file
    """
    if not os.path.exists(cache_path):
        return "NEW"
    
    # Count remaining cases
    remaining_count, count_message = count_remaining_cases(cache_path)
    
    from PyQt5.QtGui import QFont
    from ibm_theme import get_qss, IBM, _read_font_size as _rfs
    _fs = _rfs()
    _c = IBM.LIGHT

    class EnhancedResumeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"Resume {mode_name}?")
            self.setFixedSize(500, 230)
            self.result = "NEW"
            self.setStyleSheet(get_qss('light', _fs))
            self.setFont(QFont('IBM Plex Sans', _fs))

            layout = QVBoxLayout(self)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 20, 24, 20)

            header = QLabel("Existing session found")
            header.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
            header.setStyleSheet(f"font-weight: 700; color: {_c['text_primary']}; background: transparent; border: none;")
            layout.addWidget(header)

            info_frame = QFrame()
            info_frame.setStyleSheet(
                f"background-color: {_c['info_bg']};"
                f"border-left: 4px solid {_c['interactive']};"
                f"border-top: 1px solid {_c['border_subtle']};"
                f"border-right: 1px solid {_c['border_subtle']};"
                f"border-bottom: 1px solid {_c['border_subtle']};"
                f"border-radius: 0px; padding: 4px;"
            )
            info_layout_inner = QVBoxLayout(info_frame)
            info_layout_inner.setContentsMargins(12, 8, 12, 8)
            remaining_text = QLabel(f"{count_message.capitalize()}\n\nWould you like to resume where you left off?")
            remaining_text.setFont(QFont('IBM Plex Sans', _fs))
            remaining_text.setStyleSheet(f"color: {_c['text_primary']}; background: transparent; border: none;")
            remaining_text.setWordWrap(True)
            info_layout_inner.addWidget(remaining_text)
            layout.addWidget(info_frame)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)

            resume_btn = QPushButton("Resume")
            resume_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
            resume_btn.setStyleSheet(
                f"QPushButton {{ background-color: {_c['interactive']}; color: #ffffff;"
                f" font-weight: 600; padding: 12px 28px; border: none; border-radius: 4px;"
                f" font-size: {_fs}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c['interactive_hover']}; }}"
            )
            resume_btn.clicked.connect(self.on_resume)
            btn_layout.addWidget(resume_btn)

            new_btn = QPushButton("Start Fresh")
            new_btn.setFont(QFont('IBM Plex Sans', _fs))
            new_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {_c['interactive']};"
                f" font-weight: 600; padding: 12px 28px;"
                f" border: 2px solid {_c['interactive']}; border-radius: 4px;"
                f" font-size: {_fs}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c['layer_02']}; }}"
            )
            new_btn.clicked.connect(self.on_new)
            btn_layout.addWidget(new_btn)

            layout.addLayout(btn_layout)
            self.setLayout(layout)
        
        def on_resume(self):
            self.result = "RESUME"
            self.accept()
        
        def on_new(self):
            self.result = "NEW"
            self.accept()
    
    app = QApplication.instance()
    if app is None:
        # Fallback for standalone dialog testing
        app = QApplication(sys.argv)
    
    dialog = EnhancedResumeDialog()
    dialog.exec_()
    return dialog.result

# ============================================================================
# CASE REVIEWER DIALOG
# ============================================================================
def get_case_closing_code(case_number, cases_completed_count, total_in_progress_count=None, case_status="in_progress", current_position=None):
    """
    Opens a case reviewer dialog for the current case.
    Creates a fresh dialog for each case to avoid garbage collection issues.
    Returns the selected closing code and whether to add a note.
    
    Args:
        case_number: The case number
        cases_completed_count: Number of cases completed (used for progress if current_position not provided)
        total_in_progress_count: Total number of cases
        case_status: Status of the case (in_progress, skipped, etc.)
        current_position: Current position in the list (1-based) - if provided, overrides cases_completed_count for display
    """
    # Dialog creation for case review
    
    from ibm_theme import get_qss, IBM, _read_font_size as _rfs2
    _fs2 = _rfs2()
    _c2 = IBM.LIGHT

    class CaseReviewerDialog(QDialog, SettingsAwareMixin):
        def __init__(self, case_num, cases_completed, total_count, status, current_position=None):
            super().__init__()
            self.case_num = case_num
            self.cases_completed = cases_completed
            self.total_count = total_count
            self.case_status = status
            self.current_position = current_position

            from PyQt5.QtGui import QFont
            font = QFont('IBM Plex Sans', _fs2)
            self.setFont(font)
            self.setWindowTitle("Case Reviewer")
            self.resize(620, 850)
            self.selected_code = None
            self.add_note = False
            self.setModal(True)
            self.setStyleSheet(get_qss('light', _fs2))
            
            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 15
            main_layout.setSpacing(8)  # Reduced from 10
            
            # ========== TOP PANEL: Case Info & Progress ==========
            info_layout = QVBoxLayout()
            info_layout.setSpacing(5)
            
            self.case_info_label = QLabel()
            self.case_info_label.setFont(QFont('IBM Plex Sans', _fs2, QFont.Bold))
            self.case_info_label.setStyleSheet(
                f"font-weight: 700; color: {_c2['interactive']}; background: transparent; border: none;"
            )
            info_layout.addWidget(self.case_info_label)

            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(8)
            self.progress_bar.setStyleSheet(
                f"QProgressBar {{ border: none; border-radius: 4px;"
                f" background-color: {_c2['progress_track']}; }}"
                f"QProgressBar::chunk {{ background-color: {_c2['progress_fill']}; border-radius: 4px; }}"
            )
            info_layout.addWidget(self.progress_bar)

            # Case position label (below bar)
            self.case_position_label = QLabel()
            self.case_position_label.setFont(QFont('IBM Plex Sans', _fs2 - 2))
            self.case_position_label.setStyleSheet(
                f"color: {_c2['text_secondary']}; background: transparent; border: none;"
            )
            info_layout.addWidget(self.case_position_label)
            
            main_layout.addLayout(info_layout)
            main_layout.addSpacing(10)
            
            # ========== SCROLLABLE BUTTON SECTIONS ==========
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)  # Reduced from 15
            scroll_layout.setContentsMargins(5, 5, 5, 5)  # Add margins
            
            # ===== SECTION A: Issue Resolution =====
            scroll_layout.addWidget(self._create_section_header("Issue Resolution"))
            sec_a = QGridLayout()
            sec_a.setSpacing(6)  # Reduced from 8
            sec_a.setColumnStretch(0, 1)
            sec_a.setColumnStretch(1, 1)
            
            sec_a_buttons = [
                ("Resolved", "Issue Resolved"),
                ("Issue Not Fixed", "Issue Not Fixed"),
                ("Not Reached", "Customer Not Reached"),
                ("Not Yet Tested", "Machine Not Yet Tested"),
                ("DND", "DND"),
                ("Escalated", "Escalated"),
                ("Still in Review", "Need Third Action"),
            ]
            
            for idx, (label_text, code) in enumerate(sec_a_buttons):
                btn = self._create_button(label_text, code, "#E3F2FD")
                sec_a.addWidget(btn, idx // 2, idx % 2)
            
            scroll_layout.addLayout(sec_a)
            scroll_layout.addSpacing(3)  # Reduced from 5
            
            # ===== SECTION B: Communication Follow-up =====
            scroll_layout.addWidget(self._create_section_header("Communication Follow-up"))
            sec_b = QGridLayout()
            sec_b.setSpacing(6)  # Reduced from 8
            sec_b.setColumnStretch(0, 1)
            sec_b.setColumnStretch(1, 1)
            
            sec_b_buttons = [
                ("Send SMS", "Send SMS"),
                ("Send Email", "Send Email"),
                ("Send SMS + Email", "Send SMS and Email"),
                ("Call Customer", "Call the Customer"),
            ]
            
            for idx, (label_text, code) in enumerate(sec_b_buttons):
                btn = self._create_button(label_text, code, "#F3E5F5")
                sec_b.addWidget(btn, idx // 2, idx % 2)
            
            scroll_layout.addLayout(sec_b)
            scroll_layout.addSpacing(5)
            
            # ===== SECTION C: Case Management =====
            scroll_layout.addWidget(self._create_section_header("Case Management"))
            sec_c = QGridLayout()
            sec_c.setSpacing(8)
            sec_c.setColumnStretch(0, 1)
            sec_c.setColumnStretch(1, 1)
            
            skip_btn = self._create_button("⊘ Skip the Case", "Skipped", "#FFEBEE")
            skip_btn.setToolTip("Skip this case and move to the next one")
            sec_c.addWidget(skip_btn, 0, 0)

            prev_case_btn = self._create_button("↶ Previous Case", "NAV_PREV", "#FFF9C4")
            prev_case_btn.setToolTip("Go back to review the previous case again")
            prev_case_btn.clicked.disconnect()
            prev_case_btn.clicked.connect(lambda: self.close_with_nav("NAV_PREV"))
            sec_c.addWidget(prev_case_btn, 0, 1)

            other_btn = self._create_button("Custom Code", "custom", "#E0E0E0")
            other_btn.clicked.disconnect()
            other_btn.clicked.connect(self.ask_other_code)
            sec_c.addWidget(other_btn, 1, 0)

            scroll_layout.addLayout(sec_c)
            scroll_layout.addStretch()

            scroll.setWidget(scroll_widget)
            main_layout.addWidget(scroll)

            # ========== BOTTOM PANEL: Options ========== 
            bottom_layout = QVBoxLayout()
            bottom_layout.setSpacing(10)

            from PyQt5.QtGui import QFont
            self.add_note_checkbox = QCheckBox("Add Case Note")
            self.add_note_checkbox.setFont(QFont('IBM Plex Sans', _fs2))
            self.add_note_checkbox.setStyleSheet(f"padding: 6px; color: {_c2['text_primary']};")
            bottom_layout.addWidget(self.add_note_checkbox)

            close_btn = QPushButton("Close & Exit Application")
            close_btn.setFont(QFont('IBM Plex Sans', _fs2))
            close_btn.setStyleSheet(
                f"QPushButton {{ background-color: {_c2['danger']}; color: #ffffff;"
                f" border: none; border-radius: 4px; font-weight: 600;"
                f" padding: 10px; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c2['danger_hover']}; }}"
            )
            close_btn.clicked.connect(lambda: self.on_button_clicked("CLOSE_APPLICATION"))
            bottom_layout.addWidget(close_btn)

            # Add bottom layout to main layout
            main_layout.addLayout(bottom_layout)

            self.setLayout(main_layout)
            self.update_case_info(self.case_num, self.cases_completed, self.total_count, self.current_position)

        def close_with_nav(self, nav_code):
            self.selected_code = nav_code
            self.add_note = bool(self.add_note_checkbox.isChecked())
            self.accept()
        
        def on_theme_changed(self, theme: str):
            """Handle theme changes — applies full IBM QSS."""
            from ibm_theme import get_qss, IBM
            self.setStyleSheet(get_qss(theme, _fs2))
            _tc = IBM.DARK if theme == 'dark' else IBM.LIGHT
            self.case_info_label.setStyleSheet(
                f"font-weight: 700; color: {_tc['interactive']}; background: transparent; border: none;"
            )
        
        def on_font_size_changed(self, scale: float):
            """Handle font size changes."""
            # Import and use the static helper
            from ui.settings_aware_dialog import apply_font_to_widget_and_children
            apply_font_to_widget_and_children(self, scale)
        
        def _apply_current_font_size(self):
            """Apply current font size from config to all widgets."""
            try:
                import json
                import os
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
                font_size = 15  # default
                
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    if 'ui_settings' in config and 'font_size' in config['ui_settings']:
                        font_size = max(10, min(20, int(config['ui_settings']['font_size'])))
                
                from ui.settings_aware_dialog import apply_font_to_widget_and_children
                apply_font_to_widget_and_children(self, font_size)
            except Exception:
                pass

        def _create_section_header(self, title):
            """IBM Carbon section header: bold label with blue bottom border"""
            from PyQt5.QtGui import QFont
            header = QLabel(title.upper())
            header.setFont(QFont('IBM Plex Sans', _fs2 - 2, QFont.Bold))
            header.setStyleSheet(
                f"font-weight: 700; color: {_c2['text_secondary']};"
                f" background: transparent; border: none;"
                f" border-bottom: 2px solid {_c2['interactive']};"
                f" padding-bottom: 4px; margin-top: 6px;"
                f" letter-spacing: 0.5px;"
            )
            return header

        def _create_button(self, label_text, code, bg_color):
            """IBM Carbon action button — solid accent color, centered text, easy to click"""
            from PyQt5.QtGui import QFont
            btn = QPushButton(label_text)
            btn.setFont(QFont('IBM Plex Sans', _fs2, QFont.Bold))
            btn.setMinimumHeight(45)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {_c2['layer_01']};"
                f" border: 1px solid {_c2['border_subtle']}; border-radius: 4px;"
                f" font-weight: 600; color: {_c2['text_primary']};"
                f" padding: 12px 16px; text-align: center; }}"
                f"QPushButton:hover {{ background-color: {_c2['interactive']};"
                f" color: #ffffff; border: 1px solid {_c2['interactive']}; }}"
                f"QPushButton:pressed {{ background-color: {_c2['interactive_hover']};"
                f" color: #ffffff; }}"
            )
            btn.clicked.connect(lambda: self.on_button_clicked(code))
            return btn
        
        def update_case_info(self, case_num, cases_completed, total_count, current_position=None):
            """Update the case info and progress bar."""
            try:
                status_display = self.case_status.title() if self.case_status else "Unknown"
                self.case_info_label.setText(f"Case {case_num}  —  {status_display}")
                if total_count and total_count > 0:
                    percentage = int(((cases_completed + 1) / total_count) * 100)
                    self.progress_bar.setValue(percentage)
                    pos = current_position if current_position else cases_completed + 1
                    self.case_position_label.setText(f"{pos} of {total_count} cases ({percentage}%)")
                else:
                    self.progress_bar.setValue(0)
                    self.case_position_label.setText("")
            except Exception as e:
                print(f"[WARN] Error updating case info: {e}")
        
        def on_button_clicked(self, code):
            """Handle button click - close dialog with result"""
            self.selected_code = code
            self.add_note = bool(self.add_note_checkbox.isChecked())
            self.accept()  # Close dialog and return success
        
        def ask_other_code(self):
            """Ask for custom closing code with Final Action and Status options"""
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QButtonGroup, QPushButton, QGroupBox
            
            custom_dialog = QDialog(self)
            custom_dialog.setWindowTitle("Custom Closing Code")
            custom_dialog.resize(400, 280)
            
            layout = QVBoxLayout(custom_dialog)
            layout.setSpacing(15)
            
            # Custom code text input
            text_label = QLabel("Enter custom closing code (for notes):")
            text_label.setStyleSheet("font-weight: bold;")
            layout.addWidget(text_label)
            
            text_input = QLineEdit()
            text_input.setPlaceholderText("Custom code text...")
            text_input.setMinimumHeight(30)
            layout.addWidget(text_input)
            
            # Radio buttons section
            radio_layout = QHBoxLayout()
            
            # Final Action column
            final_action_group = QGroupBox("Final Action")
            final_action_layout = QVBoxLayout(final_action_group)
            self.final_action_btn_group = QButtonGroup(custom_dialog)
            
            reviewed_radio = QRadioButton("Reviewed")
            reviewed_radio.setChecked(True)
            not_reached_radio = QRadioButton("Not Reached")
            
            self.final_action_btn_group.addButton(reviewed_radio, 0)
            self.final_action_btn_group.addButton(not_reached_radio, 1)
            
            final_action_layout.addWidget(reviewed_radio)
            final_action_layout.addWidget(not_reached_radio)
            radio_layout.addWidget(final_action_group)
            
            # Status column
            status_group = QGroupBox("Status")
            status_layout = QVBoxLayout(status_group)
            self.status_btn_group = QButtonGroup(custom_dialog)
            
            skipped_radio = QRadioButton("Skipped")
            skipped_radio.setChecked(True)
            closed_radio = QRadioButton("Closed")
            
            self.status_btn_group.addButton(skipped_radio, 0)
            self.status_btn_group.addButton(closed_radio, 1)
            
            status_layout.addWidget(skipped_radio)
            status_layout.addWidget(closed_radio)
            radio_layout.addWidget(status_group)
            
            layout.addLayout(radio_layout)
            
            # OK/Cancel buttons
            btn_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            ok_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 20px;")
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet("background-color: #9E9E9E; color: white; padding: 8px 20px;")
            
            ok_btn.clicked.connect(custom_dialog.accept)
            cancel_btn.clicked.connect(custom_dialog.reject)
            
            btn_layout.addWidget(ok_btn)
            btn_layout.addWidget(cancel_btn)
            layout.addLayout(btn_layout)
            
            if custom_dialog.exec_() == QDialog.Accepted:
                custom_text = text_input.text().strip()
                
                # Get selected Final Action
                final_action_id = self.final_action_btn_group.checkedId()
                final_action = "Reviewed" if final_action_id == 0 else "Not Reached"
                
                # Get selected Status
                status_id = self.status_btn_group.checkedId()
                status = "Skipped" if status_id == 0 else "Closed"
                
                # Store the selections for later use
                self.custom_final_action = final_action
                self.custom_status = status
                
                # Use the custom text as the code (for notes), but also pass final action and status
                if custom_text:
                    # Format: "custom_text|final_action|status" to be parsed later
                    result_code = f"CUSTOM|{custom_text}|{final_action}|{status}"
                    self.on_button_clicked(result_code)
                else:
                    # No custom text, just use the selected final action
                    result_code = f"CUSTOM||{final_action}|{status}"
                    self.on_button_clicked(result_code)
    
    # Get or create QApplication (should already exist from run_case_reviewer)
    app = QApplication.instance()
    if app is None:
        # Fallback for standalone dialog testing
        app = QApplication(sys.argv)
        created_app = True
    else:
        created_app = False
    
    # Create fresh dialog for this case
    dialog = CaseReviewerDialog(case_number, cases_completed_count, total_in_progress_count, case_status, current_position)
    
    # Show dialog modally and wait for result
    print(f"[INFO] Waiting for case reviewer input for case: {case_number}")
    dialog.exec_()
    
    # Get result from dialog
    if dialog.selected_code:
        result_code = dialog.selected_code
        result_note = dialog.add_note
        print(f"[INFO] Case {case_number} closing code selected: {result_code}")
    else:
        # User closed dialog without selecting - default to "New"
        result_code = "New"
        result_note = False
        print(f"[WARN] Case {case_number} dialog closed without selection, defaulting to: {result_code}")
    
    # Only quit if we created the app (for standalone testing)
    if created_app:
        app.quit()
    
    return result_code, result_note

def get_call_closing_code():
    """
    Opens a call outcome dialog for the current call.
    Returns the selected closing code and whether to add a note.
    """
    closing_code = {"value": None, "add_note": False}

    from ibm_theme import get_qss, IBM, _read_font_size as _rfs_cc
    _cc_fs = _rfs_cc()
    _c_cc = IBM.LIGHT

    class CallOutcomeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Call Closing Code")
            self.setMinimumWidth(460)
            self.setMinimumHeight(500)
            self.setStyleSheet(get_qss('light', _cc_fs))
            self.setFont(QFont('IBM Plex Sans', _cc_fs))

            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(24, 20, 24, 20)
            main_layout.setSpacing(14)

            header = QLabel("Select Call Closing Code")
            header.setFont(QFont('IBM Plex Sans', _cc_fs, QFont.Bold))
            header.setStyleSheet(
                f"font-weight: 700; color: {_c_cc['interactive']};"
                f" background: transparent; border: none;"
            )
            main_layout.addWidget(header)

            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet(f"color: {_c_cc['border_subtle']};")
            main_layout.addWidget(sep)

            btn_frame = QWidget()
            grid = QGridLayout(btn_frame)
            grid.setSpacing(10)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)

            buttons = [
                ("Issue Resolved",    "Called - Answered: Issue Resolved"),
                ("Issue Not Fixed",   "Called - Answered: Issue Not Resolved"),
                ("Not Reached",       "Customer Not Reached"),
                ("Not Yet Tested",    "Customer Claims that the Machine Not Yet Tested"),
                ("Left Voicemail",    "Called: Not Reached // left Voicemail"),
                ("Ext Not Found",     "Called - Company NO. Extension Found: Not Reached"),
            ]

            # Accent colors per button type
            _btn_colors = [
                (_c_cc['interactive'],    _c_cc['interactive_hover']),   # Resolved  — Blue
                (_c_cc['danger'],         _c_cc['danger_hover']),         # Not Fixed — Red
                (_c_cc['text_secondary'], _c_cc['interactive']),          # Not Reached — Grey
                (_c_cc['teal'],           _c_cc['teal_hover']),           # Not Tested — Teal
                (_c_cc['purple'],         _c_cc['purple_hover']),         # Voicemail — Purple
                (_c_cc['text_secondary'], _c_cc['interactive']),          # Ext Not Found — Grey
            ]

            def set_code_and_close(code):
                closing_code["value"] = code
                try:
                    closing_code["add_note"] = bool(self.add_note_checkbox.isChecked())
                except Exception:
                    closing_code["add_note"] = False
                self.accept()

            def ask_other_code():
                try:
                    text, ok = QInputDialog.getText(self, "Custom Closing Code", "Enter custom closing code:")
                    if ok and text.strip():
                        set_code_and_close(text.strip())
                except Exception as e:
                    print(f"[WARN] Custom code input failed: {e}")

            for idx, ((label_text, code), (bg, hover)) in enumerate(zip(buttons, _btn_colors)):
                r = idx // 2
                c = idx % 2
                btn = QPushButton(label_text)
                btn.setFont(QFont('IBM Plex Sans', _cc_fs, QFont.Bold))
                btn.setMinimumHeight(52)
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {bg}; color: #ffffff;"
                    f" border: none; border-radius: 4px;"
                    f" font-weight: 700; padding: 14px 12px;"
                    f" font-size: {_cc_fs}pt; text-align: center; }}"
                    f"QPushButton:hover {{ background-color: {hover}; }}"
                    f"QPushButton:pressed {{ border: 2px inset rgba(0,0,0,0.2); }}"
                )
                btn.clicked.connect(lambda checked=False, c=code: set_code_and_close(c))
                grid.addWidget(btn, r, c)

            main_layout.addWidget(btn_frame)

            other_btn = QPushButton("Custom Code")
            other_btn.setFont(QFont('IBM Plex Sans', _cc_fs))
            other_btn.setMinimumHeight(40)
            other_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {_c_cc['text_secondary']};"
                f" border: 1px solid {_c_cc['border_subtle']}; border-radius: 4px;"
                f" font-weight: 600; padding: 10px;"
                f" font-size: {_cc_fs}pt; }}"
                f"QPushButton:hover {{ background-color: {_c_cc['layer_02']}; color: {_c_cc['text_primary']}; }}"
            )
            other_btn.clicked.connect(ask_other_code)
            main_layout.addWidget(other_btn)

            self.add_note_checkbox = QCheckBox("Add Case Note")
            self.add_note_checkbox.setFont(QFont('IBM Plex Sans', _cc_fs))
            self.add_note_checkbox.setStyleSheet(f"padding: 6px; color: {_c_cc['text_primary']};")
            main_layout.addWidget(self.add_note_checkbox)

            self.setLayout(main_layout)
    
    app = QApplication.instance()
    if app is None:
        # Fallback for standalone dialog testing
        app = QApplication(sys.argv)
        created_app = True
    else:
        created_app = False
    
    dialog = CallOutcomeDialog()
    print(f"[INFO] Waiting for call outcome selection...")
    dialog.exec_()
    
    # Only quit if we created the app (for standalone testing)
    if created_app:
        app.quit()
    
    result_code = closing_code.get("value")
    result_note = bool(closing_code.get("add_note", False))
    print(f"[INFO] Call closing code selected: {result_code}, add_note={result_note}")
    
    return result_code, result_note

# ============================================================================
# MAIN CASE REVIEWER FUNCTION
# ============================================================================
def run_case_reviewer(support_agent=None):
    """
    Main entry point for Case Reviewer mode.
    Processes IN-PROGRESS cases with dialer integration.
    Opens closing code dialog for each case.
    
    Args:
        support_agent: Optional name of agent being supported (for dynamic sheet naming)
    """
    global theme_manager, accessibility_manager, error_logger
    
    print("=" * 60)
    print("       CASE REVIEWER - Review In-Progress Cases")
    print("=" * 60)
    
    # Initialize QApplication FIRST (required before any QWidget is created)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # ===== PHASE 3.2: Initialize Theme & Accessibility =====
    try:
        from ui.theme_manager import get_theme_manager
        from ui.accessibility_helper import get_accessibility_manager
        from utils.error_logger import get_error_logger
        
        theme_manager = get_theme_manager()
        accessibility_manager = get_accessibility_manager()
        error_logger = get_error_logger("CaseReviewer")
        
        print("[INFO] ✓ Theme Manager initialized (Phase 3.2)")
        print("[INFO] ✓ Accessibility Manager initialized (Phase 3.2)")
        print("[INFO] ✓ Error Logger initialized (Phase 4.3)")
    except Exception as e:
        print(f"[WARNING] Could not initialize theme/accessibility managers: {e}")
        theme_manager = None
        accessibility_manager = None
        error_logger = None
    
    # Use support agent name if provided, otherwise agent's own name
    working_agent = support_agent if support_agent else AGENT_NAME
    sheet_name = EXCEL_SHEET_NAME
    if support_agent:
        # Format: "AgentName's Cases"
        sheet_name = f"{support_agent}'s Cases"
        print(f"[INFO] Support Mode: Working on {support_agent}'s cases")
    else:
        print(f"[INFO] Agent: {AGENT_NAME}")
        
    print(f"[INFO] Using sheet: {sheet_name}")
    
    print(f"[INFO] Mode: Case Reviewer (With Dialer)")
    print("[INFO] Starting Case Reviewer process...")
    
    driver = None
    
    try:
        # Lazy import UI components (after QApplication created)
        from ui.components.loading_spinner import LoadingSpinner
        
        # Enable Windows sleep inhibit
        enable_windows_inhibit()
        
        # Get today's Excel path
        excel_path = todays_excel_path()
        print(f"[INFO] Looking for Excel file: {excel_path}")
        
        # Use file search popup if file doesn't exist
        if not os.path.exists(excel_path):
            print(f"[INFO] Excel file does not exist yet. Showing search popup...")
            action, path = show_file_search_popup(excel_path, retry_interval_seconds=10)
            
            if action == "ABORT":
                print("[INFO] User aborted file search. Exiting Case Reviewer.")
                return
            elif action == "MANUAL":
                excel_path = path
                print(f"[INFO] Using manually selected file: {excel_path}")
            elif action == "FOUND":
                excel_path = path
        
        print(f"[INFO] Excel file found: {excel_path}")
        
        # Set Chrome to use ART Profile
        chrome_options = Chrome_ART_Profile()
        
        # Initialize Chrome driver
        print("[INFO] Initializing Chrome driver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        print("[INFO] Chrome driver initialized successfully")
        
        # Login to dialer FIRST (CRM will open automatically)
        print("[INFO] Logging into dialer...")
        if not perform_dialer_login(driver):
            print("[ERROR] Failed to login to dialer")
            return
        print("[INFO] Dialer login successful")
        
        # CRM opens automatically after dialer login - switch to CRM window
        print("[INFO] Switching to CRM window...")
        time.sleep(3)  # Wait for CRM to open automatically
        
        if not switch_to_crm_window(driver):
            print("[ERROR] Failed to switch to CRM window")
            return
        
        # Wait for CRM to fully load
        print("[INFO] Waiting for CRM page to load...")
        for attempt in range(30):
            try:
                search_box = safe_find(driver, By.ID, "GlobalSearchBox", timeout=2, retries=1)
                if search_box:
                    print("[INFO] CRM page loaded successfully - GlobalSearchBox found")
                    break
            except:
                pass
            time.sleep(1)
            if attempt % 5 == 0:
                print(f"[INFO] Still waiting for CRM to load... ({attempt}s)")
        
        print("[INFO] Ready to process cases")
        time.sleep(2)
        
        # =====================================================================
        # CHECK FOR EXISTING CACHE - Resume Logic (Phase 4.2 Enhanced)
        # =====================================================================
        cache_file = get_todays_cache_path(working_agent, mode="casereviewer")
        os.makedirs(CACHE_DIRECTORY, exist_ok=True)
        
        # Phase 4.2: Use enhanced cache resume dialog with remaining case count
        resume_choice = check_existing_cache_and_ask_enhanced(cache_file, mode_name="Case Reviewer")
        
        if resume_choice == "RESUME":
            # Resume from existing cache
            print(f"[INFO] Resuming from existing cache: {cache_file}")
            
            # Phase 3.3: Show loading spinner while reading cache
            spinner = LoadingSpinner(message="Loading cached cases...", title="Case Reviewer")
            spinner.show()
            try:
                df = pd.read_excel(cache_file, sheet_name=sheet_name)
                case_count = len(df)
            finally:
                spinner.close()
            
            print(f"[INFO] Loaded {case_count} cases from cache")
            
            # Find columns for processing
            status_col = find_column_case_insensitive(df, 'Status') or 'Status'
            case_col = find_column_case_insensitive(df, 'Case Number') or 'Case Number'
            
            # Calculate how many cases in this cache are already completed (not in_progress/skipped)
            try:
                statuses = df[status_col].astype(str).str.lower().str.strip()
                cases_still_pending = len(df[statuses.isin(['in_progress', 'skipped'])])
                cases_already_completed = case_count - cases_still_pending
                # Store original total count for progress calculation
                original_total_count = case_count
                print(f"[INFO] Cache status: Total={case_count}, Still pending={cases_still_pending}, Already completed={cases_already_completed}")
            except Exception as e:
                print(f"[WARN] Could not calculate completed cases: {e}")
                cases_already_completed = 0
                original_total_count = case_count
        else:
            # Create new cache from main Excel file
            # Phase 3.3: Show loading spinner while reading main Excel
            spinner = LoadingSpinner(message="Loading Excel file...", title="Case Reviewer")
            spinner.show()
            try:
                print(f"[INFO] Loading Excel file: {excel_path}")
                df_main = pd.read_excel(excel_path, sheet_name=sheet_name)
                print(f"[INFO] Loaded {len(df_main)} rows from Excel")
            finally:
                spinner.close()
            
            # Find columns (case-insensitive) - matching original Main.py
            status_col = find_column_case_insensitive(df_main, 'Status') or 'Status'
            case_col = find_column_case_insensitive(df_main, 'Case Number') or 'Case Number'
            assigned_col = find_column_case_insensitive(df_main, 'Assigned To') or 'Assigned To'
            
            # Filter for IN_PROGRESS and SKIPPED cases assigned to this agent
            # agent_first = working_agent.split()[0]
            # print(f"[INFO] Filtering for IN_PROGRESS and SKIPPED cases assigned to: {agent_first}")
            
            # UPDATED: Filter only by Status (ignore Assigned To)
            print(f"[INFO] Filtering for IN_PROGRESS and SKIPPED cases in sheet '{sheet_name}'")
            df_filtered = df_main[
                (df_main[status_col].astype(str).str.strip().str.lower().isin(['in_progress', 'skipped']))
            ].copy()
            
            case_count = len(df_filtered)
            print(f"[INFO] Found {case_count} cases to process (in_progress + skipped)")
            
            if case_count == 0:
                print("[INFO] No in-progress or skipped cases to process. Exiting Case Reviewer.")
                show_completion_dialog(0, 0)
                return
            
            # Save filtered cases to cache
            print(f"[INFO] Creating working cache file: {cache_file}")
            df_filtered.to_excel(cache_file, sheet_name=sheet_name, index=False)
            print(f"[INFO] Working cache created with {len(df_filtered)} cases")
            
            # Use filtered dataframe for processing
            df = df_filtered.copy()
            cases_already_completed = 0  # New session, no completed cases
            original_total_count = case_count  # Total count for fresh start
        
        # Process counters - track progress as (completed + 1) / total_original_count
        processed_count = 0
        case_counter = 0  # Tracks cases processed in this session
        today_str = datetime.now().strftime("%b %d, %Y")
        
        # Create list of indices from filtered dataframe for pointer-based navigation
        to_process_indices = list(df.index)
        
        # Process each in-progress case using pointer logic
        pointer = cases_already_completed if resume_choice == "RESUME" else 0
        while pointer < len(to_process_indices):
            idx = to_process_indices[pointer]
            row = df.loc[idx]
            
            try:
                status = str(row.get(status_col, '')).strip().lower()
                case_number = row.get(case_col)
                
                if pd.isna(case_number) or not str(case_number).strip():
                    pointer += 1
                    continue
                    
                case_number = str(case_number).strip()
                
                # Only process 'in_progress' or 'skipped' cases
                if status not in ('in_progress', 'skipped'):
                    pointer += 1
                    continue
                
                print(f"\n[INFO] Processing case {pointer + 1}/{original_total_count}: {case_number} (status: {status})")
                
                # Search and open case
                case_search_and_open(driver, case_number)
                
                # Pass pointer+1 as current position for accurate progress that advances with navigation
                CaseClosingCode, add_note = get_case_closing_code(case_number, pointer, original_total_count, case_status=status, current_position=pointer + 1)
                
                # Check if user clicked Close & Exit
                if CaseClosingCode == "CLOSE_APPLICATION":
                    print(f"[INFO] User clicked Close & Exit - shutting down...")
                    break
                
                # Check if user clicked Previous Case - go back to previous case
                if CaseClosingCode == "PREVIOUS_CASE":
                    if pointer > 0:
                        pointer -= 1  # Go back one position in the pointer
                        print(f"[INFO] ⬅ Navigating to previous case - Pointer: {pointer}")
                        # Continue to reopen the previous case
                        continue
                    else:
                        print(f"[INFO] ⚠ Already at first case - cannot navigate backwards")
                        # Reopen same case
                        continue
                
                # Create case note

                CaseNote = get_case_note(f"Case is Reviewed with closing code {CaseClosingCode}")
                
                # If user requested adding a Case Note
                if add_note:
                    try:
                        add_Case_Note(driver, CaseNote=CaseNote)
                    except Exception as e:
                        print(f"[WARN] add_Case_Note failed for {case_number}: ")
                
                # If DND selected, update contact preferences
                if CaseClosingCode == "DND":
                    DND_CX(driver, case_number)
                
                # If Call the Customer selected
                if CaseClosingCode == "Call the Customer":
                    # Force Qt event processing to prevent UI freeze
                    QApplication.processEvents()
                    
                    # Perform call flow
                    call_success = perform_call_flow(driver)
                    
                    if not call_success:
                        print(f"[WARN] Call flow failed - attempting to recover...")
                        # Try switching back to CRM
                        switch_to_crm_window(driver, max_retries=3)
                    
                    # Force Qt event processing before showing dialog
                    QApplication.processEvents()
                    time.sleep(0.5)
                    
                    # Get call outcome
                    CallOutcome, add_note = get_call_closing_code()
                    
                    # Build case note
                    case_note_text = f"Date: {today_str}\nQueue: ART Project - Follow up\nAgent: {AGENT_NAME}\nAction: Called the Customer // {CallOutcome}"
                    
                    try:
                        add_Case_Note(driver, CaseNote=case_note_text)
                    except Exception as e:
                        print(f"[WARN] add_Case_Note failed for {case_number} after call: {e}")
                    
                    # ALWAYS update Excel: Action 3 = Called the Customer, Final Action = outcome
                    df.at[idx, "Action 3"] = 'Called the Customer'
                    df.at[idx, "Final Action"] = excelCaseClosingCode(CallOutcome)
                    df.at[idx, "Status"] = 'Closed'
                    update_cache_file(cache_file, df, sheet_name)
                    
                    # Move to next case after call flow
                    case_counter += 1
                    pointer += 1
                    processed_count += 1
                    print(f"[INFO] Call completed for {case_number} - outcome: {CallOutcome}")
                    continue  # Skip to next case
                
                # Handle SMS/Email actions
                if CaseClosingCode in ("Send SMS", "Send Email", "Send SMS and Email"):
                    try:
                        serial_val = serial_extraction(driver, case_number, df)
                    except Exception:
                        serial_val = ''
                    try:
                        CX_Name = customer_name_extraction(driver, case_number)
                    except Exception:
                        CX_Name = 'Our Valued Customer'
                    
                    try:
                        sms_text = formatting_texts_sms(CX_Name, serial_val, case_number, df)
                    except Exception:
                        sms_text = SMSText.format(CX_Name=CX_Name, case_number=case_number)
                    
                    try:
                        email_text = formatting_texts_email(CX_Name, serial_val, case_number, df)
                    except Exception:
                        email_text = ""
                
                if CaseClosingCode == "Send SMS":
                    try:
                        send_SMS(driver, sms_text)
                        add_Case_Note(driver, CaseNote=CaseNote)
                        # Update Excel: Action 1 = Sent SMS, Status = In Progress Today
                        df.at[idx, "Action 1"] = 'Sent SMS'
                        df.at[idx, "Status"] = 'In Progress Today'
                        update_cache_file(cache_file, df, sheet_name)
                        case_counter += 1
                        pointer += 1
                        processed_count += 1
                        continue  # Move to next case
                    except Exception as e:
                        print(f"[WARN] send_SMS failed for {case_number}: ")
                
                if CaseClosingCode == "Send Email":
                    try:
                        send_Email(driver, email_text)
                        add_Case_Note(driver, CaseNote=CaseNote)
                        # Update Excel: Action 2 = Sent Email, Status = In Progress Today
                        df.at[idx, "Action 2"] = 'Sent Email'
                        df.at[idx, "Status"] = 'In Progress Today'
                        update_cache_file(cache_file, df, sheet_name)
                        case_counter += 1
                        pointer += 1
                        processed_count += 1
                        continue  # Move to next case
                    except Exception as e:
                        print(f"[WARN] send_Email failed for {case_number}: ")
                
                if CaseClosingCode == "Send SMS and Email":
                    try:
                        send_SMS(driver, sms_text)
                    except Exception as e:
                        print(f"[WARN] send_SMS (part of combined) failed for {case_number}: ")
                    try:
                        send_Email(driver, email_text)
                    except Exception as e:
                        print(f"[WARN] send_Email (part of combined) failed for {case_number}: ")
                    try:
                        add_Case_Note(driver, CaseNote=CaseNote)
                    except Exception as e:
                        print(f"[WARN] add_Case_Note failed after combined send for {case_number}: ")
                    # Update Excel: Action 1 = Sent SMS, Action 2 = Sent Email, Final Action = Sent Email, Status = In Progress Today
                    df.at[idx, "Action 1"] = 'Sent SMS'
                    df.at[idx, "Action 2"] = 'Sent Email'
                    df.at[idx, "Final Action"] = 'Sent Email'
                    df.at[idx, "Status"] = 'In Progress Today'
                    update_cache_file(cache_file, df, sheet_name)
                    case_counter += 1
                    pointer += 1
                    processed_count += 1
                    continue  # Move to next case
                
                # Still in Review (Need Third Action) - leave all columns untouched, just move to next case
                if CaseClosingCode == "Need Third Action":

                    case_counter += 1
                    pointer += 1
                    continue
                
                # Skipped - mark as Skipped and move on
                if CaseClosingCode == "Skipped":

                    df.at[idx, "Status"] = 'Skipped'
                    update_cache_file(cache_file, df, EXCEL_SHEET_NAME)
                    case_counter += 1
                    pointer += 1
                    continue
                
                # Update DataFrame for other closing codes
                if 'called' in CaseClosingCode.lower():
                    df.at[idx, "Action 3"] = 'Called the Customer'
                
                df.at[idx, "Final Action"] = excelCaseClosingCode(CaseClosingCode)
                df.at[idx, "Status"] = 'Closed'
                
                # Update cache file
                update_cache_file(cache_file, df, sheet_name)
                
                processed_count += 1
                case_counter += 1
                print(f"[INFO] Completed case {case_number} - {case_counter}/{case_count} done")
                
                # Keep driver alive periodically
                if case_counter % REFRESH_INTERVAL == 0:
                    keep_driver_alive(driver)
                    time.sleep(5)
                    
            except Exception as e:
                print(f"[ERROR] Exception processing case {case_number if 'case_number' in locals() else 'UNKNOWN'}: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                pointer += 1  # Move to next case on error
                continue
            
            # Increment index to move to next case
            pointer += 1
        
        print("\n" + "=" * 60)
        print(f"[INFO] Case Reviewer Complete!")
        print(f"[INFO] Processed: {processed_count}/{case_count} cases")
        print(f"[INFO] Cache file: {cache_file}")
        print("=" * 60)
        
        # Show completion dialog
        show_completion_dialog(processed_count, case_count)
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Case Reviewer failed: {e}")
        traceback.print_exc()
        
    finally:
        # Cleanup
        try:
            if driver is not None:
                print("[INFO] Closing Chrome driver...")
                driver.quit()
                print("[INFO] Chrome driver closed successfully.")
        except Exception as e:
            print(f"[WARN] Error closing Chrome driver: {e}")
        
        # Disable Windows sleep inhibit
        try:
            disable_windows_inhibit()
        except Exception as e:
            print(f"[WARN] Error disabling Windows inhibit: {e}")

def show_completion_dialog(processed, total):
    """Show completion dialog with results"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        QMessageBox.information(
            None,
            "Case Reviewer Complete",
            f"Case Reviewer has finished processing.\n\n"
            f"Processed: {processed}/{total} cases\n\n"
            f"Click OK to exit."
        )
    except Exception as e:
        print(f"[WARN] Could not show completion dialog: {e}")

if __name__ == "__main__":
    run_case_reviewer()
