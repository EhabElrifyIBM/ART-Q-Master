# ============================================================================
# AutoSender_v2.py - Process NEW Cases (No Dialer) - ENHANCED VERSION
# ============================================================================
# Phase 5 Enhanced Version:
# - Company Process is NOW ISOLATED (separate button in Dispatcher)
# - Companies Process will NOT auto-run after AutoSender
# - User must explicitly select Company Process mode
# 
# Core functionality:
# - Send SMS
# - Send Email  
# - Add Case Notes
# - Update status to 'In Progress Today'
# NO DIALER/GENESYS INTEGRATION
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
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QObject

# Ensure both src and this directory are in path for proper imports
import sys
import os as os_module
src_dir = os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

art_q_dir = os_module.path.dirname(os_module.path.abspath(__file__))
if art_q_dir not in sys.path:
    sys.path.insert(0, art_q_dir)

# Import shared functions
from SharedFunctions import (
    CONFIG_MANAGER,
    AGENT_NAME,
    EXCEL_BASE_PATH,
    CACHE_DIRECTORY,
    EXCEL_SHEET_NAME,
    Chrome_ART_Profile,
    todays_excel_path,
    find_column_case_insensitive,
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
    safe_find,
    click_safe,
    send_keys_safe,
    show_file_search_popup,
    load_companies_for_handler,
    get_todays_cache_path,
    check_existing_cache_and_ask,
)

# CRM URL - Dynamics 365
CRM_URL = "https://lenovo-plrs-prod.crm5.dynamics.com/main.aspx?appid=00fd771a-9081-e911-a83a-000d3a07fba2&forceUCI=1&pagetype=dashboard&id=4e76815a-1f63-df11-ae90-00155d2e3002&type=system&_canOverride=true"

# ============================================================================
# WORKER THREAD CLASS - Keeps UI responsive during long operations
# ============================================================================
class AutoSenderWorker(QThread):
    """
    Worker thread that processes cases in the background.
    Emits signals to update UI without blocking the main thread.
    """
    
    # Signals for UI updates
    progress_updated = pyqtSignal(int, str, int, int, int, int)  # current, case_num, completed, skipped, failed, total
    log_message = pyqtSignal(str, str)  # message, level
    status_changed = pyqtSignal(str, bool)  # status_text, is_error
    finished = pyqtSignal(str, int, int)  # reason, processed_count, total_count
    
    def __init__(self, driver, cache_file, df, excel_path, config, cases_already_completed=0, total_new_cases=0, refresh_interval=10):
        super().__init__()
        self.driver = driver
        self.cache_file = cache_file
        self.df = df.copy()
        self.excel_path = excel_path
        self.config = config
        
        # Control flags
        self._pause_flag = False
        self._stop_flag = False
        self._abort_flag = False
        
        # Progress tracking
        self.processed_count = 0
        self.cases_failed = 0
        self.cases_skipped = 0
        self.cases_already_completed = cases_already_completed  # Cases completed in previous sessions
        self.total_new_cases = total_new_cases  # Total NEW cases in the sheet (for final counter)
        self.refresh_interval = refresh_interval  # How many cases between driver refreshes
    
    def set_pause(self, paused):
        """Set pause flag"""

        self._pause_flag = paused
    
    def set_stop(self, stop):
        """Set stop flag"""

        self._stop_flag = stop
    
    def set_abort(self, abort):
        """Set abort flag"""

        self._abort_flag = abort
    
    def run(self):
        """Main worker thread execution"""
        try:
            # Get parameters from config
            sheet_name = self.config.get('sheet_name', 'AutoSender')
            status_col = find_column_case_insensitive(self.df, 'Status')
            case_col = find_column_case_insensitive(self.df, 'Case Number')
            new_case_count = len(self.df[self.df[status_col].str.lower() == 'new']) if status_col else 0
            
            self.log_message.emit(f"Starting worker thread: {new_case_count} cases", "INFO")
            
            case_counter = 0
            today_str = datetime.now().strftime("%b %d, %Y")
            CaseNote = get_case_note("Sent SMS  // Sent Email")
            
            # Process each new case
            for idx, row in self.df.iterrows():
                # Check abort flag
                if self._abort_flag:

                    self.log_message.emit("AutoSender aborted by user!", "ERROR")
                    break
                
                # Check pause flag
                if self._pause_flag:
                    pass  # handled by while loop below

                while self._pause_flag:
                    time.sleep(0.1)
                    if self._abort_flag:
                        pass
                
                if self._abort_flag:
                    break
                
                try:
                    status = str(row.get(status_col, '')).strip().lower()
                    case_number = row.get(case_col)
                    
                    if pd.isna(case_number) or not str(case_number).strip():
                        continue
                    
                    case_number = str(case_number).strip()
                    
                    # Only process 'new' cases
                    if status != 'new':
                        continue
                    
                    # Emit progress update - show (already_done + current_in_session) / total
                    current_overall_progress = self.cases_already_completed + case_counter + 1
                    self.progress_updated.emit(
                        current_overall_progress,
                        case_number,
                        self.processed_count,
                        self.cases_skipped,
                        self.cases_failed,
                        self.total_new_cases if self.total_new_cases > 0 else new_case_count
                    )
                    
                    self.log_message.emit(f"Processing case {case_number}...", "INFO")
                    
                    # Check pause/abort before searching case
                    if self._abort_flag:

                        break
                    if self._pause_flag:

                        while self._pause_flag and not self._abort_flag:
                            time.sleep(0.1)
                        if self._abort_flag:
                            break
                    
                    # Search and open case (WITHOUT clicking Edit)
                    case_search_and_open_no_edit(self.driver, case_number)
                    
                    # Check pause/abort before checking solution
                    if self._abort_flag:

                        break
                    if self._pause_flag:

                        while self._pause_flag and not self._abort_flag:
                            time.sleep(0.1)
                        if self._abort_flag:
                            break
                    
                    # Check if Solution Provided - skip if not (before editing)
                    if not solution_provided_check_and_skip(self.driver, case_number, self.df, self.excel_path):
                        self.log_message.emit(f"Solution not provided, skipping case {case_number}", "WARNING")
                        self.df.at[idx, "Status"] = 'Skipped'
                        self.cases_skipped += 1
                        update_cache_file(self.cache_file, self.df, sheet_name)
                        case_counter += 1
                        continue
                    
                    # Solution provided - now click Edit button
                    self.log_message.emit("Clicking Edit button...", "INFO")
                    
                    # Check pause/abort before clicking edit
                    if self._abort_flag:

                        break
                    if self._pause_flag:

                        while self._pause_flag and not self._abort_flag:
                            time.sleep(0.1)
                        if self._abort_flag:
                            break
                    
                    click_edit_button(self.driver)
                    
                    # Check for e-ticketing case
                    eticket_check = eticket_check_and_skip(self.driver, case_number, self.df, self.excel_path)
                    if eticket_check:
                        self.log_message.emit(f"eTicket check was TRUE for case {case_number}, process done.", "ETICKET")
                    else:
                        self.log_message.emit(f"eTicket check was FALSE for case {case_number}, proceeding with actions.", "ETICKET")
                    
                    # Extract Serial Number
                    serial_val = serial_extraction(self.driver, case_number, self.df)
                    
                    # Extract Customer Name
                    CX_Name = customer_name_extraction(self.driver, case_number)
                    
                    # Format SMS Text
                    sms_text = formatting_texts_sms(CX_Name, serial_val, case_number, self.df)
                    
                    # Format Email Text
                    email_text = formatting_texts_email(CX_Name, serial_val, case_number, self.df)
                    
                    # Check pause/abort before SMS
                    if self._abort_flag:

                        break
                    if self._pause_flag:

                        while self._pause_flag and not self._abort_flag:
                            time.sleep(0.1)
                        if self._abort_flag:
                            break
                    
                    # Send SMS (if Action 1 empty)
                    sms_sent = False
                    if pd.isna(row.get("Action 1", "")) or str(row.get("Action 1", "")).strip() == "":
                        self.log_message.emit("Sending SMS...", "INFO")
                        sms_sent = send_SMS(self.driver, sms_text)
                        if sms_sent:
                            self.log_message.emit("SMS sent successfully", "SUCCESS")
                        else:
                            self.log_message.emit("SMS sending failed", "WARNING")
                            self.cases_failed += 1
                    else:
                        sms_sent = True  # Already sent
                    
                    # Check pause/abort before Email
                    if self._abort_flag:

                        break
                    if self._pause_flag:

                        while self._pause_flag and not self._abort_flag:
                            time.sleep(0.1)
                        if self._abort_flag:
                            break
                    
                    # Send Email (if Action 2 empty)
                    email_sent = False
                    if pd.isna(row.get("Action 2", "")) or str(row.get("Action 2", "")).strip() == "":
                        self.log_message.emit("Sending Email...", "INFO")
                        email_sent = send_Email(self.driver, email_text)
                        if email_sent:
                            self.log_message.emit("Email sent successfully", "SUCCESS")
                        else:
                            self.log_message.emit("Email sending failed", "WARNING")
                            self.cases_failed += 1
                    else:
                        email_sent = True  # Already sent
                    
                    # Check pause/abort before Case Note
                    if self._abort_flag:

                        break
                    if self._pause_flag:

                        while self._pause_flag and not self._abort_flag:
                            time.sleep(0.1)
                        if self._abort_flag:
                            break
                    
                    # Add Case Note
                    self.log_message.emit("Adding case note...", "INFO")
                    note_saved = add_Case_Note(self.driver, CaseNote)
                    if note_saved:
                        self.log_message.emit("Case note added", "SUCCESS")
                    
                    # Update DataFrame
                    if sms_sent:
                        self.df.at[idx, "Action 1"] = 'Sent SMS'
                    if email_sent:
                        self.df.at[idx, "Action 2"] = 'Sent Email'
                    self.df.at[idx, "Action 3"] = ''
                    self.df.at[idx, "Final Action"] = 'Sent Email'
                    
                    if sms_sent and email_sent and note_saved:
                        self.df.at[idx, "Status"] = 'In Progress Today'
                        self.processed_count += 1
                        self.log_message.emit(f"Case {case_number} completed successfully", "SUCCESS")
                    
                    # Update cache file
                    update_cache_file(self.cache_file, self.df, sheet_name)
                    
                    case_counter += 1
                    
                    # Refresh driver periodically to prevent memory buildup
                    if case_counter > 0 and case_counter % self.refresh_interval == 0:
                        self.log_message.emit(f"Refreshing browser after {case_counter} cases...", "INFO")
                        try:
                            keep_driver_alive(self.driver)
                            time.sleep(2)  # Brief pause after refresh
                            self.log_message.emit(f"Browser refreshed successfully", "SUCCESS")
                        except Exception as refresh_error:
                            self.log_message.emit(f"Browser refresh failed: {str(refresh_error)}", "WARNING")
                    
                    # Check if user requested stop
                    if self._stop_flag:
                        self.log_message.emit("Stop requested - gracefully exiting...", "WARNING")
                        break
                    
                except Exception as e:
                    self.log_message.emit(f"Error processing case: {str(e)}", "ERROR")
                    continue
            
            # Emit finished signal
            reason = "Aborted" if self._abort_flag else ("Stopped" if self._stop_flag else "Completed")
            self.finished.emit(reason, self.processed_count, new_case_count)
            self.log_message.emit(f"Worker thread finished: {reason}", "INFO")
            
        except Exception as e:
            self.log_message.emit(f"Critical error in worker thread: {str(e)}", "ERROR")
            self.finished.emit("Error", self.processed_count, 0)

def case_search_and_open_no_edit(driver, case_number):
    """
    Search for and open a case in Dynamics CRM WITHOUT clicking Edit button.
    Used in AutoSender to check Solution Provided before editing.
    """
    #Clicking Save Button for the previous case (will fail on first case, that's OK)
    click_safe(
        driver,
        By.XPATH,
        "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckIn.Command') and contains(@id,'-button')]",
        timeout=1,
        retries=2,
    )
    
    #sleep timer
    time.sleep(5)

    #clicking OK Button if avail
    click_safe(
        driver,
        By.XPATH,
        "//button[contains(@id,'okButton_')]/div",
        timeout=2,
        retries=2,
    )

    #sleep timer
    time.sleep(3)

    #Search Box - wait for it to be present
    safe_find(driver, By.ID, "GlobalSearchBox", timeout=3, retries=3)

    #Search for the case
    send_keys_safe(driver, By.ID, "GlobalSearchBox", case_number, timeout=3, retries=3)
    
    #click the first result's button to open the case
    click_safe(
        driver,
        By.XPATH,
        "//div[@id='id-globalSearchFlyout-1']/div/div/div/div/div/div[2]/div/button/span",
        timeout=7,
        retries=2,
    )

    # USFC discard dialog (if appears) - best-effort
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]",
        timeout=1,
        retries=2,
    )

    #clicking OK Button if avail
    click_safe(
        driver,
        By.XPATH,
        "//button[contains(@id,'okButton_')]/div",
        timeout=2,
        retries=2,
    )

    #sleep timer
    time.sleep(3)
    # NOTE: Edit button is NOT clicked here - done after solution check

def click_edit_button(driver):
    """Click the Edit button to start editing a case"""
    click_safe(
        driver,
        By.XPATH,
        "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckOut.Command') and contains(@id,'-button')]",
        timeout=1,
        retries=3,
    )
    #sleep timer
    time.sleep(3)

def count_remaining_cases(cache_file, sheet_name=EXCEL_SHEET_NAME):
    """
    Count how many NEW cases remain in the cache file (not yet completed).
    
    Phase 4.2 Enhancement: Provides accurate remaining case count for resume dialog.
    Counts only cases with Status='new' to exclude already processed cases.
    
    Args:
        cache_file: Path to the cache Excel file
        sheet_name: Sheet name to read from
    
    Returns:
        Tuple of (remaining_new_count, display_message)
        - remaining_new_count: Number of NEW cases remaining (not completed)
        - display_message: Formatted message for UI display
    """
    try:
        if not os.path.exists(cache_file):
            return 0, "Cache file not found"
        
        # Read cache file and count remaining NEW cases
        df_cache = pd.read_excel(cache_file, sheet_name=sheet_name)
        
        # Filter for Status='new' only
        status_col = find_column_case_insensitive(df_cache, 'Status')
        if status_col:
            df_remaining = df_cache[
                df_cache[status_col].astype(str).str.strip().str.lower() == 'new'
            ]
            remaining_new_count = len(df_remaining)
        else:
            # If no status column found, count all rows
            remaining_new_count = len(df_cache)
        
        if remaining_new_count == 0:
            return 0, "No NEW cases remain in cache"
        elif remaining_new_count == 1:
            return 1, "1 NEW case remains"
        else:
            return remaining_new_count, f"{remaining_new_count} NEW cases remain"
    
    except Exception as e:
        print(f"[WARN] Error counting remaining cases: {e}")
        return 0, "Unable to determine remaining cases"

def check_existing_cache_and_ask_enhanced(cache_path, mode_name="Auto Sender"):
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
    
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from ibm_theme import get_qss, IBM, _read_font_size

    _fs = _read_font_size()
    _c = IBM.LIGHT  # Resume dialog always light (modal over a light background)

    class EnhancedResumeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"Resume {mode_name}?")
            self.setFixedSize(500, 230)
            self.result = "NEW"
            self.setStyleSheet(get_qss('light', _fs))
            font = QFont('IBM Plex Sans', _fs)
            self.setFont(font)

            layout = QVBoxLayout(self)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 20, 24, 20)

            # Header
            header = QLabel("Existing session found")
            header.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
            header.setStyleSheet(f"font-weight: 700; color: {_c['text_primary']}; background: transparent; border: none;")
            layout.addWidget(header)

            # Info box — IBM info card style
            info_frame = QFrame()
            info_frame.setStyleSheet(
                f"background-color: {_c['info_bg']};"
                f"border-left: 4px solid {_c['interactive']};"
                f"border-top: 1px solid {_c['border_subtle']};"
                f"border-right: 1px solid {_c['border_subtle']};"
                f"border-bottom: 1px solid {_c['border_subtle']};"
                f"border-radius: 0px; padding: 4px;"
            )
            info_layout = QVBoxLayout(info_frame)
            info_layout.setContentsMargins(12, 8, 12, 8)
            remaining_text = QLabel(f"{count_message.capitalize()}\n\nWould you like to resume where you left off?")
            remaining_text.setFont(QFont('IBM Plex Sans', _fs))
            remaining_text.setStyleSheet(f"color: {_c['text_primary']}; background: transparent; border: none;")
            remaining_text.setWordWrap(True)
            info_layout.addWidget(remaining_text)
            layout.addWidget(info_frame)

            # Buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)

            resume_btn = QPushButton("Resume")
            resume_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
            resume_btn.setStyleSheet(
                f"QPushButton {{ background-color: {_c['interactive']}; color: #ffffff;"
                f" font-weight: 600; padding: 12px 28px; border: none; border-radius: 4px;"
                f" font-family: 'IBM Plex Sans','Segoe UI',Arial; font-size: {_fs}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c['interactive_hover']}; }}"
                f"QPushButton:pressed {{ background-color: {_c['interactive_active']}; }}"
            )
            resume_btn.clicked.connect(self.on_resume)
            btn_layout.addWidget(resume_btn)

            new_btn = QPushButton("Start Fresh")
            new_btn.setFont(QFont('IBM Plex Sans', _fs))
            new_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {_c['interactive']};"
                f" font-weight: 600; padding: 12px 28px;"
                f" border: 2px solid {_c['interactive']}; border-radius: 4px;"
                f" font-family: 'IBM Plex Sans','Segoe UI',Arial; font-size: {_fs}pt; min-height: 44px; }}"
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
        app = QApplication(sys.argv)
    
    dialog = EnhancedResumeDialog()
    dialog.exec_()
    return dialog.result

def run_auto_sender(excel_path=None, support_agent=None):
    """
    Main entry point for Auto Sender mode.
    Processes NEW cases only - sends SMS, Email, adds Notes.
    After NEW cases, runs Companies Process, then exits to Dispatcher.
    
    Args:
        excel_path: Optional path to the Excel file. If not provided, uses todays_excel_path()
        support_agent: Optional name of agent being supported (for dynamic sheet naming)
    """
    # Ensure QApplication exists FIRST before any QWidget creation
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    print("=" * 60)
    print("       AUTO SENDER - Process New Cases")
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
    
    print(f"[INFO] Mode: Auto Sender (No Dialer)")
    print("[INFO] Starting Auto Sender process...")
    
    driver = None
    progress_monitor = None
    cases_failed = 0
    
    try:
        # Lazy import UI components (after QApplication created)
        from ui.components.progress_monitor import ProgressMonitor
        from ui.components.loading_spinner import LoadingSpinner
        # Enable Windows sleep inhibit
        enable_windows_inhibit()
        
        # Use provided excel_path or default to todays_excel_path()
        if excel_path is None:
            excel_path = todays_excel_path()
        print(f"[INFO] Using Excel file: {excel_path}")
        
        # Use file search popup if file doesn't exist
        if not os.path.exists(excel_path):
            print(f"[INFO] Excel file does not exist yet. Showing search popup...")
            action, path = show_file_search_popup(excel_path, retry_interval_seconds=10)
            
            if action == "ABORT":
                print("[INFO] User aborted file search. Exiting Auto Sender.")
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
        driver.maximize_window()
        print("[INFO] Chrome driver initialized successfully")
        
        # Navigate to CRM URL
        print(f"[INFO] Navigating to CRM: {CRM_URL}")
        driver.get(CRM_URL)
        print("[INFO] Waiting for CRM page to load...")
        
        # Wait for CRM to fully load (wait for GlobalSearchBox)
        for attempt in range(30):  # Try for up to 30 seconds
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
        
        # Additional wait to ensure page is fully ready
        time.sleep(5)
        
        # =====================================================================
        # CHECK FOR EXISTING CACHE - Resume Logic (Phase 4.2 Enhanced)
        # =====================================================================
        cache_file = get_todays_cache_path(working_agent, mode="autosender")
        os.makedirs(CACHE_DIRECTORY, exist_ok=True)
        
        # Phase 4.2: Use enhanced cache resume dialog with remaining case count
        resume_choice = check_existing_cache_and_ask_enhanced(cache_file, mode_name="Auto Sender")
        
        if resume_choice == "RESUME":
            # Resume from existing cache
            print(f"[INFO] Resuming from existing cache: {cache_file}")
            
            # Phase 3.3: Show loading spinner while reading cache
            spinner = LoadingSpinner(message="Loading cached cases...", title="Auto Sender")
            spinner.show()
            try:
                df = pd.read_excel(cache_file, sheet_name=sheet_name)
                print(f"[INFO] Loaded {len(df)} total cases from cache")
            finally:
                spinner.close()
            
            # Initialize columns for processing
            status_col = find_column_case_insensitive(df, 'Status') or 'Status'
            case_col = find_column_case_insensitive(df, 'Case Number') or 'Case Number'
            assigned_col = find_column_case_insensitive(df, 'Assigned To') or 'Assigned To'
            
            # Count cases by status - keep ALL cases in dataframe
            try:
                df_new = df[
                    (df[status_col].astype(str).str.strip().str.lower() == 'new')
                ].copy()
                new_case_count = len(df_new)
                total_in_cache = len(df)
                cases_already_completed = total_in_cache - new_case_count
                original_new_count = total_in_cache  # Total cases we started with
                
                print(f"[INFO] Resume: Total in cache: {total_in_cache}, Remaining NEW: {new_case_count}, Already completed: {cases_already_completed}")
            except Exception as e:
                print(f"[WARN] Could not calculate completed cases: {e}")
                new_case_count = len(df)
                cases_already_completed = 0
                original_new_count = new_case_count
            
            # Keep ALL cases in dataframe (don't filter) - only loop through NEW ones
        else:
            # Create new cache from main Excel file
            # Phase 3.3: Show loading spinner while reading main Excel
            spinner = LoadingSpinner(message="Loading Excel file...", title="Auto Sender")
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
            
            # Filter for Status = "New" only (Ignore Assigned To)
            print(f"[INFO] Filtering for 'New' cases in sheet '{sheet_name}'")
            
            df_filtered = df_main[
                (df_main[status_col].astype(str).str.strip().str.lower() == 'new')
            ].copy()
            
            new_case_count = len(df_filtered)
            print(f"[INFO] Found {new_case_count} NEW cases to process")
            
            if new_case_count == 0:
                print("[INFO] No new 'Active Cases' to process. Proceeding to check Companies...")
            
            # Save all NEW cases to cache (will keep non-NEW cases if resuming)
            print(f"[INFO] Creating working cache file: {cache_file}")
            with pd.ExcelWriter(cache_file, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"[INFO] ✓ Cache file created with {len(df_filtered)} NEW cases")
            print(f"[INFO] Companies sheet will be created by CompaniesProcess when run separately")
            
            # Verify the cache file was written correctly
            try:
                with pd.ExcelFile(cache_file) as verify_xls:
                    pass  # verify file is readable
            except Exception as ve:
                print(f"[WARN] Could not verify cache file: {ve}")
            print(f"[INFO] Working cache created with {len(df_filtered)} cases")
            
            # Use only NEW cases for processing (worker sheet contains only new cases)
            df = df_filtered.copy()
            cases_already_completed = 0  # New session, no completed cases yet
            original_new_count = new_case_count  # Total NEW cases when starting fresh
        
        # Process counters
        # For NEW session: case_counter starts at 0
        # For RESUME: case_counter starts at number of already-completed NEW cases
        case_counter = cases_already_completed if resume_choice == "RESUME" else 0
        processed_count = 0
        today_str = datetime.now().strftime("%b %d, %Y")
        CaseNote = get_case_note("Sent SMS  // Sent Email")
        total_new_case_count = new_case_count + case_counter  # Total = remaining + already completed
        
        # Get refresh interval dynamically from config
        try:
            refresh_interval_val = CONFIG_MANAGER.get_value('execution_settings', 'refresh_interval')
            refresh_interval = int(refresh_interval_val)
        except Exception:
            refresh_interval = 10  # Default fallback
        print(f"[INFO] Driver refresh interval set to: {refresh_interval} cases")
        
        # Phase 4.1: Create progress monitor for real-time feedback
        total_case_count = original_new_count  # Total NEW cases (including already completed)
        progress_monitor = ProgressMonitor(
            title="AutoSender - Processing NEW Cases",
            total_cases=total_case_count,
            parent=None
        )
        progress_monitor.log_message(f"Starting AutoSender: {new_case_count} remaining cases to process out of {total_case_count} total NEW cases")
        progress_monitor.show()
        
        # ===== CREATE WORKER THREAD FOR PROCESSING (KEEP UI RESPONSIVE) =====
        worker = AutoSenderWorker(
            driver=driver,
            cache_file=cache_file,
            df=df,
            excel_path=excel_path,
            config={
                'sheet_name': sheet_name,
            },
            cases_already_completed=cases_already_completed,
            total_new_cases=original_new_count if 'original_new_count' in locals() else new_case_count,
            refresh_interval=refresh_interval
        )
        
        # Connect worker signals to progress monitor
        worker.progress_updated.connect(progress_monitor.update_progress)
        worker.log_message.connect(lambda msg, level: progress_monitor.log_message(msg, level))
        worker.status_changed.connect(lambda status, error: progress_monitor.set_status(status, error))
        worker.finished.connect(lambda reason, processed, total: on_worker_finished(progress_monitor, reason, processed, total))
        
        # Connect progress monitor pause/resume to worker
        def on_pause():
            worker.set_pause(True)
            progress_monitor.log_warning("Process paused by user")
        
        def on_resume():
            worker.set_pause(False)
            progress_monitor.log_message("Process resumed", "INFO")
        
        def on_stop():
            worker.set_stop(True)
        
        def on_abort():
            worker.set_abort(True)
        
        progress_monitor.pause_requested.connect(on_pause)
        progress_monitor.resume_requested.connect(on_resume)
        progress_monitor.stop_requested.connect(on_stop)
        progress_monitor.abort_requested.connect(on_abort)
        
        # Start worker thread
        progress_monitor.log_message("Starting background processing thread...", "INFO")
        worker.start()
        
        # Show progress monitor (non-blocking - thread runs in background)
        progress_monitor.exec_()
        
        # Get final statistics from worker
        worker_stats = worker.processed_count if hasattr(worker, 'processed_count') else 0
        print("\n" + "=" * 60)
        print(f"[INFO] Auto Sender Complete!")
        print(f"[INFO] Processed: {worker_stats} cases")
        print(f"[INFO] Cache file: {cache_file}")
        print("=" * 60)
        
        print("\n[INFO] Returning to Dispatcher.")
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Auto Sender failed: {e}")
        traceback.print_exc()
        
    finally:
        # Phase 4.1: Finish progress monitoring
        if progress_monitor:
            if progress_monitor.is_abort_requested():
                reason = "Aborted"
            elif progress_monitor.is_stop_requested():
                reason = "Stopped"
            else:
                reason = "Completed"
            progress_monitor.finish_process(reason)
            stats = progress_monitor.get_statistics()
            progress_monitor.exec_()  # Show dialog until closed
            print(f"[SUCCESS] AutoSender {reason}! Stats: Cases Completed={stats['cases_completed']}, Failed={stats['cases_failed']}, Duration={stats['duration']}")
        
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

def on_worker_finished(progress_monitor, reason, processed, total):
    """
    Callback when worker thread finishes.
    Called from worker thread via signal.
    """
    progress_monitor.finish_process(reason)
    print(f"[INFO] Worker thread finished: {reason} - {processed}/{total} cases processed")

def show_completion_dialog(processed, total):
    """Show completion dialog with results"""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        QMessageBox.information(
            None,
            "Auto Sender Complete",
            f"Auto Sender has finished processing.\n\n"
            f"Processed: {processed}/{total} cases\n\n"
            f"Click OK to exit."
        )
    except Exception as e:
        print(f"[WARN] Could not show completion dialog: {e}")

if __name__ == "__main__":
    run_auto_sender()
