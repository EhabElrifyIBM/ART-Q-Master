# ============================================================================
# CaseReviewer.py - Review IN-PROGRESS Cases (With Dialer)
# ============================================================================
# This module handles processing of IN-PROGRESS cases:
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
    QLineEdit, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt5.QtCore import Qt

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
# CASE REVIEWER DIALOG
# ============================================================================
def get_case_closing_code(case_number, cases_completed_count, total_in_progress_count=None, case_status="in_progress"):
    """
    Opens a case reviewer dialog for the current case.
    Creates a fresh dialog for each case to avoid garbage collection issues.
    Returns the selected closing code and whether to add a note.
    """
    # Dialog creation for case review
    
    class CaseReviewerDialog(QDialog):
        def __init__(self, case_num, cases_completed, total_count, status):
            super().__init__()
            super().__init__()
            self.setWindowTitle("Case Reviewer")
            self.resize(600, 750)  # Taller window to fit all sections + error log
            self.selected_code = None
            self.add_note = False
            self.case_status = status  # Store status for display
            self.setModal(True)
            
            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)  # Reduced from 15
            main_layout.setSpacing(8)  # Reduced from 10
            
            # ========== TOP PANEL: Case Info & Progress ==========
            info_layout = QVBoxLayout()
            info_layout.setSpacing(5)
            
            self.case_info_label = QLabel()
            self.case_info_label.setStyleSheet("font-weight: bold; font-size: 15px; color: #1976D2;")
            info_layout.addWidget(self.case_info_label)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setTextVisible(True)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #CCCCCC;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                }
            """)
            info_layout.addWidget(self.progress_bar)
            
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
            
            skip_btn = self._create_button("Skip the Case", "Skipped", "#FFEBEE")
            sec_c.addWidget(skip_btn, 0, 0)
            
            prev_case_btn = self._create_button("⬅ Previous Case", "PREVIOUS_CASE", "#FFF9C4")
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
            
            self.add_note_checkbox = QCheckBox("✓ Add Case Note")
            self.add_note_checkbox.setStyleSheet("font-size: 15px; padding: 8px;")
            bottom_layout.addWidget(self.add_note_checkbox)
            
            # Add a close/exit button
            close_btn = QPushButton("⛔ Close & Exit Application")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F;
                    color: white;
                    border: 1px solid #B71C1C;
                    border-radius: 4px;
                    font-weight: bold;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #B71C1C;
                }
                QPushButton:pressed {
                    background-color: #7B1FA2;
                }
            """)
            close_btn.clicked.connect(lambda: self.on_button_clicked("CLOSE_APPLICATION"))
            bottom_layout.addWidget(close_btn)
            
            # Add bottom layout to main layout
            main_layout.addLayout(bottom_layout)
            
            self.setLayout(main_layout)
            self.update_case_info(case_num, cases_completed, total_count)
        
        def _create_section_header(self, title):
            """Create a section header label with visible styling"""
            header = QLabel(f"▼ {title}")
            header.setStyleSheet("""
                font-weight: bold;
                font-size: 15px;
                color: white;
                background-color: #1976D2;
                padding: 10px 12px;
                border-radius: 4px;
                margin-top: 5px;
            """)
            return header
        
        def _create_button(self, label_text, code, bg_color):
            """Create a styled button"""
            btn = QPushButton(label_text)
            btn.setMinimumHeight(40)
            btn.setMaximumWidth(220)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg_color};
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    font-weight: bold;
                    color: #333;
                    padding: 8px 12px;
                    font-size: 15px;
                }}
                QPushButton:hover {{
                    border: 2px solid #1976D2;
                    background-color: {bg_color};
                }}
                QPushButton:pressed {{
                    background-color: #90CAF9;
                }}
            """)
            btn.clicked.connect(lambda: self.on_button_clicked(code))
            return btn
        
        def update_case_info(self, case_num, cases_completed, total_count):
            """Update the case info and progress bar"""
            try:
                print(f"[DEBUG] update_case_info: cases_completed={cases_completed}, total_count={total_count}, type(total)={type(total_count)}")
                status_display = self.case_status.title() if self.case_status else "Unknown"
                if total_count and total_count > 0:
                    display_num = cases_completed + 1
                    percentage = int(((cases_completed + 1) / total_count) * 100)
                    self.case_info_label.setText(f"Case: {case_num}  |  Status: {status_display}  |  Progress: {display_num} of {total_count} ({percentage}%)")
                    self.progress_bar.setValue(percentage)
                    self.progress_bar.setFormat(f"{display_num}/{total_count} ({percentage}%)")
                else:
                    self.case_info_label.setText(f"Case: {case_num}  |  Status: {status_display}")
                    self.progress_bar.setValue(0)
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
    
    # Get or create QApplication
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    
    # Create fresh dialog for this case
    dialog = CaseReviewerDialog(case_number, cases_completed_count, total_in_progress_count, case_status)
    
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
    
    # If we created the app, quit it
    if created_app:
        app.quit()
    
    return result_code, result_note


def get_call_closing_code():
    """
    Opens a call outcome dialog for the current call.
    Returns the selected closing code and whether to add a note.
    """
    closing_code = {"value": None, "add_note": False}

    class CallOutcomeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Call Closing Code")
            self.resize(400, 450)
            
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(10)
            
            label = QLabel("Select Call Closing Code:")
            label.setStyleSheet("font-weight: bold; font-size: 15px;")
            main_layout.addWidget(label)
            
            btn_frame = QWidget()
            grid = QGridLayout(btn_frame)
            grid.setSpacing(8)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)
            
            buttons = [
                ("Issue Resolved", "Called - Answered: Issue Resolved"),
                ("Issue Not Fixed", "Called - Answered: Issue Not Resolved"),
                ("Not Reached", "Customer Not Reached"),
                ("Not Yet Tested", "Customer Claims that the Machine Not Yet Tested"),
                ("Left Voicemail", "Called: Not Reached // left Voicemail"),
                ("Ext Not Found", "Called - Company NO. Extension Found: Not Reached"),
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
            
            for idx, (label_text, code) in enumerate(buttons):
                r = idx // 2
                c = idx % 2
                btn = QPushButton(label_text)
                btn.setMinimumHeight(45)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #E3F2FD;
                        border: 1px solid #CCCCCC;
                        border-radius: 4px;
                        font-weight: bold;
                        color: #333;
                        padding: 8px 12px;
                        font-size: 15px;
                    }
                    QPushButton:hover {
                        border: 2px solid #1976D2;
                    }
                    QPushButton:pressed {
                        background-color: #90CAF9;
                    }
                """)
                btn.clicked.connect(lambda checked=False, c=code: set_code_and_close(c))
                grid.addWidget(btn, r, c)
            
            main_layout.addWidget(btn_frame)
            
            other_btn = QPushButton("Custom Code")
            other_btn.setMinimumHeight(40)
            other_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFF3E0;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    font-weight: bold;
                    color: #333;
                    padding: 6px;
                }
                QPushButton:hover {
                    border: 2px solid #FF9800;
                }
            """)
            other_btn.clicked.connect(ask_other_code)
            main_layout.addWidget(other_btn)
            
            self.add_note_checkbox = QCheckBox("✓ Add Case Note")
            self.add_note_checkbox.setStyleSheet("font-size: 15px; padding: 8px;")
            main_layout.addWidget(self.add_note_checkbox)
            
            main_layout.addStretch()
            self.setLayout(main_layout)
    
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    
    dialog = CallOutcomeDialog()
    print(f"[INFO] Waiting for call outcome selection...")
    dialog.exec_()
    
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
    print("=" * 60)
    print("       CASE REVIEWER - Review In-Progress Cases")
    print("=" * 60)
    
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
        # CHECK FOR EXISTING CACHE - Resume Logic
        # =====================================================================
        cache_file = get_todays_cache_path(working_agent, mode="casereviewer")
        os.makedirs(CACHE_DIRECTORY, exist_ok=True)
        
        resume_choice = check_existing_cache_and_ask(cache_file, mode_name="Case Reviewer")
        
        if resume_choice == "RESUME":
            # Resume from existing cache
            print(f"[INFO] Resuming from existing cache: {cache_file}")
            df = pd.read_excel(cache_file, sheet_name=sheet_name)
            case_count = len(df)
            print(f"[INFO] Loaded {case_count} cases from cache")
            
            # Find columns for processing
            status_col = find_column_case_insensitive(df, 'Status') or 'Status'
            case_col = find_column_case_insensitive(df, 'Case Number') or 'Case Number'
        else:
            # Create new cache from main Excel file
            # Load Excel data
            print(f"[INFO] Loading Excel file: {excel_path}")
            df_main = pd.read_excel(excel_path, sheet_name=sheet_name)
            print(f"[INFO] Loaded {len(df_main)} rows from Excel")
            
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
        
        # Process counters
        case_counter = 0
        processed_count = 0
        today_str = datetime.now().strftime("%b %d, %Y")
        total_case_count = case_count
        
        # Process each in-progress case
        # Process each in-progress case
        current_idx = 0
        while current_idx < len(df):
            row = df.iloc[current_idx]
            idx = df.index[current_idx]
            
            try:
                status = str(row.get(status_col, '')).strip().lower()
                case_number = row.get(case_col)
                
                if pd.isna(case_number) or not str(case_number).strip():
                    current_idx += 1
                    continue
                
                # Convert to int first to remove .0, then to string
                try:
                    case_number = str(int(float(case_number))).strip()
                except (ValueError, TypeError):
                    case_number = str(case_number).strip()
                
                # Only process 'in_progress' or 'skipped' cases
                if status not in ('in_progress', 'skipped'):
                    current_idx += 1
                    continue
                
                print(f"\n[INFO] Processing case {case_counter + 1}/{case_count}: {case_number} (status: {status})")
                
                # Search and open case
                case_search_and_open(driver, case_number)
                
                # Show closing code dialog with case status
                CaseClosingCode, add_note = get_case_closing_code(case_number, case_counter, total_case_count, case_status=status)
                
                # Check if user clicked Close & Exit
                if CaseClosingCode == "CLOSE_APPLICATION":
                    print(f"[INFO] User clicked Close & Exit - shutting down...")
                    break
                
                # Check if user clicked Previous Case - go back to previous case
                if CaseClosingCode == "PREVIOUS_CASE":
                    print(f"[INFO] User clicked Previous Case - going back...")
                    if current_idx > 0:
                        # Need to go back 2 positions: current case is at current_idx,
                        # but we haven't incremented yet, so go back 1 to get previous case
                        current_idx = max(0, current_idx - 1)
                        case_counter = max(0, case_counter - 1)
                        continue  # Restart loop with previous case
                    else:
                        print(f"[WARN] Already at first case, cannot go back")
                        continue  # Stay on current case
                
                # Create case note
                print(f"[DEBUG] Creating case note for code: {CaseClosingCode}")
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
                    current_idx += 1
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
                        current_idx += 1
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
                        current_idx += 1
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
                    current_idx += 1
                    processed_count += 1
                    continue  # Move to next case
                
                # Still in Review (Need Third Action) - leave all columns untouched, just move to next case
                if CaseClosingCode == "Need Third Action":
                    print(f"[DEBUG] Still in Review - leaving case untouched, moving to next...")
                    case_counter += 1
                    current_idx += 1
                    continue
                
                # Skipped - mark as Skipped and move on
                if CaseClosingCode == "Skipped":
                    print(f"[DEBUG] Skipping case...")
                    df.at[idx, "Status"] = 'Skipped'
                    update_cache_file(cache_file, df, EXCEL_SHEET_NAME)
                    case_counter += 1
                    current_idx += 1
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
                current_idx += 1  # Move to next case on error
                continue
            
            # Increment index to move to next case
            current_idx += 1
        
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
