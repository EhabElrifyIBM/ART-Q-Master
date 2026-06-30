# ============================================================================
# AutoSender_v2.py - Process NEW Cases (No Dialer) - MODERNIZED VERSION
# ============================================================================
# Phase 6.6: AutoSender Modernization
# - Integrated V2 foundation systems (ThemeManager, TypographyMixin, SettingsBus)
# - Modernized dialogs with V2 styling
# - Enhanced file selection with drag-drop and recent files
# - Keyboard shortcuts support
# - Improved cache statistics display
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
from PyQt5.QtWidgets import (
    QApplication, QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QFileDialog, QWidget
)
from PyQt5.QtCore import QThread, pyqtSignal, QObject, Qt, QEvent
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

# Ensure both src and this directory are in path for proper imports
import sys
import os as os_module
src_dir = os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

art_q_dir = os_module.path.dirname(os_module.path.abspath(__file__))
if art_q_dir not in sys.path:
    sys.path.insert(0, art_q_dir)

# Import V2 foundation systems (Phase 6.6)
from ui.theme_manager import get_theme_manager
from ui.typography_mixin import V2TypographyMixin
from ui.services import get_v2_settings_bus
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory
from ui.design_system import Colors, Spacing, BorderRadius
from utils.recent_tools import get_recent_tools_manager

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
                    
                    # Convert to int first to remove .0, then to string
                    try:
                        case_number = str(int(float(case_number))).strip()
                    except (ValueError, TypeError):
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
                    else:
                        self.log_message.emit("Case note failed", "WARNING")
                    
                    # Update DataFrame
                    if sms_sent:
                        self.df.at[idx, "Action 1"] = 'Sent SMS'
                    if email_sent:
                        self.df.at[idx, "Action 2"] = 'Sent Email'
                    self.df.at[idx, "Action 3"] = ''
                    self.df.at[idx, "Final Action"] = 'Sent Email'
                    
                    # Determine if case completed successfully or failed
                    if sms_sent and email_sent and note_saved:
                        # All activities succeeded - mark as completed
                        self.df.at[idx, "Status"] = 'In Progress Today'
                        self.processed_count += 1
                        self.log_message.emit(f"Case {case_number} completed successfully", "SUCCESS")
                    else:
                        # At least one activity failed - increment failed counter ONCE per case
                        self.cases_failed += 1
                        failed_activities = []
                        if not sms_sent:
                            failed_activities.append("SMS")
                        if not email_sent:
                            failed_activities.append("Email")
                        if not note_saved:
                            failed_activities.append("Note")
                        self.log_message.emit(f"Case {case_number} failed: {', '.join(failed_activities)} failed", "ERROR")
                    
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

# ============================================================================
# MODERNIZED RESUME DIALOG (Phase 6.6)
# ============================================================================
class ModernResumeDialog(QDialog, V2TypographyMixin):
    """
    Modernized resume dialog with V2 foundation systems.
    
    Features:
    - V2ThemeManager integration
    - Typography system
    - Settings bus subscription
    - Enhanced cache statistics
    - Modern card-based layout
    """
    
    def __init__(self, cache_path: str, mode_name: str = "Auto Sender", parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)
        
        self.cache_path = cache_path
        self.mode_name = mode_name
        self.user_choice = "NEW"
        
        # Get theme manager and settings bus
        self.theme_manager = get_theme_manager()
        self.settings_bus = get_v2_settings_bus()
        
        # Count remaining cases
        self.remaining_count, self.count_message = count_remaining_cases(cache_path)
        
        self._setup_ui()
        self._apply_theme()
        
        # Connect to theme and font size changes
        self.settings_bus.theme_changed.connect(self._on_theme_changed)
        self.settings_bus.font_size_changed.connect(self._on_font_changed)
    
    def _setup_ui(self):
        """Set up dialog UI."""
        self.setWindowTitle(f"Resume {self.mode_name}?")
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        main_layout.setSpacing(Spacing.LG)
        
        # Header
        header = QLabel("Existing Session Found")
        header.setObjectName("dialogTitle")
        self.apply_typography_to_widget(header, 'h2', QFont.Bold)
        main_layout.addWidget(header)
        
        # Info card with cache statistics
        info_card = self._create_info_card()
        main_layout.addWidget(info_card)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.MD)
        button_layout.addStretch(1)
        
        # Resume button (primary)
        resume_btn = QPushButton("Resume Session")
        resume_btn.setObjectName("primaryButton")
        resume_btn.setMinimumWidth(160)
        resume_btn.setMinimumHeight(48)
        self.apply_typography_to_widget(resume_btn, 'button', QFont.Bold)
        resume_btn.clicked.connect(self._on_resume)
        button_layout.addWidget(resume_btn)
        
        # Start fresh button (secondary)
        new_btn = QPushButton("Start Fresh")
        new_btn.setObjectName("secondaryButton")
        new_btn.setMinimumWidth(160)
        new_btn.setMinimumHeight(48)
        self.apply_typography_to_widget(new_btn, 'button')
        new_btn.clicked.connect(self._on_new)
        button_layout.addWidget(new_btn)
        
        main_layout.addLayout(button_layout)
        
        # Block keyboard navigation to prevent accidental activation
        self.installEventFilter(self)
    
    def _create_info_card(self) -> QFrame:
        """Create info card with cache statistics."""
        card = QFrame()
        card.setObjectName("infoCard")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
        card_layout.setSpacing(Spacing.SM)
        
        # Main message
        message = QLabel(f"{self.count_message.capitalize()}")
        message.setObjectName("infoMessage")
        message.setWordWrap(True)
        self.apply_typography_to_widget(message, 'body_lg')
        card_layout.addWidget(message)
        
        # Question
        question = QLabel("Would you like to resume where you left off?")
        question.setObjectName("infoQuestion")
        question.setWordWrap(True)
        self.apply_typography_to_widget(question, 'body')
        card_layout.addWidget(question)
        
        # Cache file info
        cache_info = QLabel(f"Cache file: {os.path.basename(self.cache_path)}")
        cache_info.setObjectName("cacheInfo")
        self.apply_typography_to_widget(cache_info, 'caption')
        card_layout.addWidget(cache_info)
        
        return card
    
    def _apply_theme(self):
        """Apply theme-aware styling."""
        theme_mode = self.settings_bus.theme
        colors = Colors.DARK if theme_mode == "dark" else Colors.LIGHT
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
            }}
            
            QLabel#dialogTitle {{
                color: {colors['text_primary']};
            }}
            
            QFrame#infoCard {{
                background-color: {colors['info_bg']};
                border-left: 4px solid {colors['primary']};
                border-top: 1px solid {colors['border']};
                border-right: 1px solid {colors['border']};
                border-bottom: 1px solid {colors['border']};
                border-radius: {BorderRadius.MD}px;
            }}
            
            QLabel#infoMessage {{
                color: {colors['text_primary']};
                font-weight: 600;
            }}
            
            QLabel#infoQuestion {{
                color: {colors['text_secondary']};
            }}
            
            QLabel#cacheInfo {{
                color: {colors['text_tertiary']};
            }}
            
            QPushButton#primaryButton {{
                background-color: {colors['primary']};
                color: {colors['text_inverse']};
                border: none;
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            
            QPushButton#primaryButton:pressed {{
                background-color: {colors['primary_active']};
            }}
            
            QPushButton#secondaryButton {{
                background-color: transparent;
                color: {colors['primary']};
                border: 2px solid {colors['primary']};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
            }}
            
            QPushButton#secondaryButton:hover {{
                background-color: {colors['surface_hover']};
            }}
        """)
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        self._apply_theme()
    
    def _on_font_changed(self, font_size: int):
        """Handle font size change."""
        # Reapply typography to all widgets with current font size
        header = self.findChild(QLabel, "dialogTitle")
        if header:
            self.apply_typography_to_widget(header, 'h2', QFont.Bold)
        
        # Update info card labels
        info_message = self.findChild(QLabel, "infoMessage")
        if info_message:
            self.apply_typography_to_widget(info_message, 'body_lg')
        
        info_question = self.findChild(QLabel, "infoQuestion")
        if info_question:
            self.apply_typography_to_widget(info_question, 'body')
        
        cache_info = self.findChild(QLabel, "cacheInfo")
        if cache_info:
            self.apply_typography_to_widget(cache_info, 'caption')
        
        # Update buttons
        for btn in self.findChildren(QPushButton):
            if btn.objectName() == "primaryButton":
                self.apply_typography_to_widget(btn, 'button', QFont.Bold)
            elif btn.objectName() == "secondaryButton":
                self.apply_typography_to_widget(btn, 'button')
        
        # Reapply theme to update any font-size dependent styles
        self._apply_theme()
    
    def _on_resume(self):
        """Handle resume button click."""
        self.user_choice = "RESUME"
        self.accept()
    
    def _on_new(self):
        """Handle start fresh button click."""
        self.user_choice = "NEW"
        self.accept()
    
    def eventFilter(self, obj, event):
        """Block keyboard entries to prevent accidental activation."""
        if event.type() == QEvent.KeyPress:
            key = event.key()
            # Block Enter, Space, Tab, and arrow keys
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space,
                      Qt.Key_Tab, Qt.Key_Backtab,
                      Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                return True
        return super().eventFilter(obj, event)
    
    def keyPressEvent(self, event):
        """Override to block keyboard activation."""
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space,
                  Qt.Key_Tab, Qt.Key_Backtab,
                  Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            event.ignore()
            return
        super().keyPressEvent(event)


def check_existing_cache_and_ask_enhanced(cache_path, mode_name="Auto Sender"):
    """
    Phase 6.6 Modernized Version: Check if cache exists and show modern resume dialog.
    
    Args:
        cache_path: Path to today's cache file
        mode_name: Display name for the mode
    
    Returns:
        - "RESUME" = Resume from existing cache
        - "NEW" = Create new cache from main Excel file
    """
    if not os.path.exists(cache_path):
        return "NEW"
    
    # Ensure QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Show modern resume dialog
    dialog = ModernResumeDialog(cache_path, mode_name)
    dialog.exec_()
    return dialog.user_choice

# ============================================================================
# MODERN FILE SELECTION DIALOG (Phase 6.6)
# ============================================================================
class ModernFileSelectionDialog(QDialog, V2TypographyMixin):
    """
    Modern file selection dialog with drag-drop support and recent files.
    
    Features:
    - Drag and drop Excel files
    - Recent files integration
    - File validation feedback
    - Modern styling
    """
    
    def __init__(self, default_path: str = None, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)
        
        self.default_path = default_path
        self.selected_file = None
        
        # Get services
        self.theme_manager = get_theme_manager()
        self.settings_bus = get_v2_settings_bus()
        self.recent_manager = get_recent_tools_manager()
        
        self._setup_ui()
        self._apply_theme()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Connect to theme and font size changes
        self.settings_bus.theme_changed.connect(self._on_theme_changed)
        self.settings_bus.font_size_changed.connect(self._on_font_changed)
    
    def _setup_ui(self):
        """Set up dialog UI."""
        self.setWindowTitle("Select Excel File - AutoSender")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        main_layout.setSpacing(Spacing.LG)
        
        # Header
        header = QLabel("Select Cases File")
        header.setObjectName("dialogTitle")
        self.apply_typography_to_widget(header, 'h2', QFont.Bold)
        main_layout.addWidget(header)
        
        subtitle = QLabel("Choose an Excel file containing cases to process, or drag and drop a file below")
        subtitle.setObjectName("dialogSubtitle")
        subtitle.setWordWrap(True)
        self.apply_typography_to_widget(subtitle, 'body')
        main_layout.addWidget(subtitle)
        
        # Drop zone
        drop_zone = self._create_drop_zone()
        main_layout.addWidget(drop_zone)
        
        # Or divider
        divider_layout = QHBoxLayout()
        divider_layout.addWidget(self._create_divider())
        or_label = QLabel("OR")
        or_label.setObjectName("dividerLabel")
        self.apply_typography_to_widget(or_label, 'caption')
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(self._create_divider())
        main_layout.addLayout(divider_layout)
        
        # Browse button
        browse_btn = QPushButton("Browse for File...")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setMinimumHeight(48)
        self.apply_typography_to_widget(browse_btn, 'button')
        browse_btn.clicked.connect(self._browse_file)
        main_layout.addWidget(browse_btn)
        
        # Selected file display
        self.file_label = QLabel("No file selected")
        self.file_label.setObjectName("fileLabel")
        self.apply_typography_to_widget(self.file_label, 'body')
        main_layout.addWidget(self.file_label)
        
        main_layout.addStretch(1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.MD)
        button_layout.addStretch(1)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.setMinimumHeight(48)
        self.apply_typography_to_widget(cancel_btn, 'button')
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.ok_btn = QPushButton("Continue")
        self.ok_btn.setObjectName("primaryButton")
        self.ok_btn.setMinimumWidth(120)
        self.ok_btn.setMinimumHeight(48)
        self.ok_btn.setEnabled(False)
        self.apply_typography_to_widget(self.ok_btn, 'button', QFont.Bold)
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_drop_zone(self) -> QFrame:
        """Create drag-drop zone."""
        zone = QFrame()
        zone.setObjectName("dropZone")
        zone.setMinimumHeight(150)
        
        layout = QVBoxLayout(zone)
        layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel("📁")
        icon_label.setObjectName("dropIcon")
        icon_label.setAlignment(Qt.AlignCenter)
        self.apply_typography_to_widget(icon_label, 'display_md')
        layout.addWidget(icon_label)
        
        text_label = QLabel("Drag and drop Excel file here")
        text_label.setObjectName("dropText")
        text_label.setAlignment(Qt.AlignCenter)
        self.apply_typography_to_widget(text_label, 'body_lg')
        layout.addWidget(text_label)
        
        hint_label = QLabel("Supported: .xlsx, .xls")
        hint_label.setObjectName("dropHint")
        hint_label.setAlignment(Qt.AlignCenter)
        self.apply_typography_to_widget(hint_label, 'caption')
        layout.addWidget(hint_label)
        
        return zone
    
    def _create_divider(self) -> QFrame:
        """Create horizontal divider."""
        line = QFrame()
        line.setObjectName("divider")
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        return line
    
    def _browse_file(self):
        """Open file browser."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            self.default_path or "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        
        if file_path:
            self._set_file(file_path)
    
    def _set_file(self, file_path: str):
        """Set selected file and validate."""
        if not os.path.exists(file_path):
            self.file_label.setText(f"❌ File not found: {file_path}")
            self.file_label.setObjectName("fileLabelError")
            self.ok_btn.setEnabled(False)
            return
        
        if not file_path.lower().endswith(('.xlsx', '.xls')):
            self.file_label.setText(f"❌ Invalid file type: {os.path.basename(file_path)}")
            self.file_label.setObjectName("fileLabelError")
            self.ok_btn.setEnabled(False)
            return
        
        self.selected_file = file_path
        self.file_label.setText(f"✓ Selected: {os.path.basename(file_path)}")
        self.file_label.setObjectName("fileLabelSuccess")
        self.ok_btn.setEnabled(True)
        self._apply_theme()  # Refresh styling
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle file drop."""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self._set_file(file_path)
    
    def _apply_theme(self):
        """Apply theme-aware styling."""
        theme_mode = self.settings_bus.theme
        colors = Colors.DARK if theme_mode == "dark" else Colors.LIGHT
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
            }}
            
            QLabel#dialogTitle {{
                color: {colors['text_primary']};
            }}
            
            QLabel#dialogSubtitle {{
                color: {colors['text_secondary']};
            }}
            
            QFrame#dropZone {{
                background-color: {colors['surface']};
                border: 2px dashed {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
            
            QFrame#dropZone:hover {{
                border-color: {colors['primary']};
                background-color: {colors['surface_hover']};
            }}
            
            QLabel#dropIcon {{
                color: {colors['text_secondary']};
            }}
            
            QLabel#dropText {{
                color: {colors['text_primary']};
                font-weight: 600;
            }}
            
            QLabel#dropHint {{
                color: {colors['text_tertiary']};
            }}
            
            QLabel#dividerLabel {{
                color: {colors['text_tertiary']};
                padding: 0 {Spacing.MD}px;
            }}
            
            QFrame#divider {{
                background-color: {colors['border']};
            }}
            
            QLabel#fileLabel {{
                color: {colors['text_secondary']};
                padding: {Spacing.SM}px;
                background-color: {colors['surface']};
                border-radius: {BorderRadius.SM}px;
            }}
            
            QLabel#fileLabelSuccess {{
                color: {colors['success']};
                background-color: {colors['success_bg']};
            }}
            
            QLabel#fileLabelError {{
                color: {colors['danger']};
                background-color: {colors['danger_bg']};
            }}
            
            QPushButton#primaryButton {{
                background-color: {colors['primary']};
                color: {colors['text_inverse']};
                border: none;
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            
            QPushButton#primaryButton:disabled {{
                background-color: {colors['surface_hover']};
                color: {colors['text_disabled']};
            }}
            
            QPushButton#secondaryButton {{
                background-color: transparent;
                color: {colors['primary']};
                border: 2px solid {colors['primary']};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
            }}
            
            QPushButton#secondaryButton:hover {{
                background-color: {colors['surface_hover']};
            }}
        """)
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        self._apply_theme()
    
    def _on_font_changed(self, font_size: int):
        """Handle font size change."""
        # Reapply typography to all widgets with current font size
        header = self.findChild(QLabel, "dialogTitle")
        if header:
            self.apply_typography_to_widget(header, 'h2', QFont.Bold)
        
        subtitle = self.findChild(QLabel, "dialogSubtitle")
        if subtitle:
            self.apply_typography_to_widget(subtitle, 'body')
        
        # Update drop zone labels
        drop_icon = self.findChild(QLabel, "dropIcon")
        if drop_icon:
            self.apply_typography_to_widget(drop_icon, 'display_md')
        
        drop_text = self.findChild(QLabel, "dropText")
        if drop_text:
            self.apply_typography_to_widget(drop_text, 'body_lg')
        
        drop_hint = self.findChild(QLabel, "dropHint")
        if drop_hint:
            self.apply_typography_to_widget(drop_hint, 'caption')
        
        divider_label = self.findChild(QLabel, "dividerLabel")
        if divider_label:
            self.apply_typography_to_widget(divider_label, 'caption')
        
        # Update file label
        if hasattr(self, 'file_label'):
            self.apply_typography_to_widget(self.file_label, 'body')
        
        # Update buttons
        for btn in self.findChildren(QPushButton):
            if btn.objectName() == "primaryButton":
                self.apply_typography_to_widget(btn, 'button', QFont.Bold)
            elif btn.objectName() == "secondaryButton":
                self.apply_typography_to_widget(btn, 'button')
        
        # Reapply theme to update any font-size dependent styles
        self._apply_theme()
    
    def get_selected_file(self) -> str:
        """Get the selected file path."""
        return self.selected_file


# ============================================================================
# MODERN COMPLETION DIALOG (Phase 6.6)
# ============================================================================
class ModernCompletionDialog(QDialog, V2TypographyMixin):
    """
    Modern completion dialog with statistics summary.
    
    Features:
    - Summary statistics card
    - Cases processed count
    - Time taken
    - Success/failure breakdown
    - Action buttons
    """
    
    def __init__(self, stats: dict, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)
        
        self.stats = stats
        
        # Get services
        self.theme_manager = get_theme_manager()
        self.settings_bus = get_v2_settings_bus()
        
        self._setup_ui()
        self._apply_theme()
        
        # Connect to theme and font size changes
        self.settings_bus.theme_changed.connect(self._on_theme_changed)
        self.settings_bus.font_size_changed.connect(self._on_font_changed)
    
    def _setup_ui(self):
        """Set up dialog UI."""
        self.setWindowTitle("AutoSender Complete")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        main_layout.setSpacing(Spacing.LG)
        
        # Header with icon
        header_layout = QHBoxLayout()
        icon = QLabel("✓")
        icon.setObjectName("successIcon")
        self.apply_typography_to_widget(icon, 'display_lg')
        header_layout.addWidget(icon)
        
        header = QLabel("Processing Complete")
        header.setObjectName("dialogTitle")
        self.apply_typography_to_widget(header, 'h1', QFont.Bold)
        header_layout.addWidget(header)
        header_layout.addStretch(1)
        main_layout.addLayout(header_layout)
        
        # Statistics card
        stats_card = self._create_stats_card()
        main_layout.addWidget(stats_card)
        
        main_layout.addStretch(1)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.MD)
        button_layout.addStretch(1)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.setMinimumWidth(160)
        close_btn.setMinimumHeight(48)
        self.apply_typography_to_widget(close_btn, 'button', QFont.Bold)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_stats_card(self) -> QFrame:
        """Create statistics summary card."""
        card = QFrame()
        card.setObjectName("statsCard")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        card_layout.setSpacing(Spacing.MD)
        
        # Title
        title = QLabel("Summary")
        title.setObjectName("cardTitle")
        self.apply_typography_to_widget(title, 'h3', QFont.Bold)
        card_layout.addWidget(title)
        
        # Stats grid
        stats_grid = QVBoxLayout()
        stats_grid.setSpacing(Spacing.SM)
        
        # Add stat rows
        self._add_stat_row(stats_grid, "Cases Completed",
                          str(self.stats.get('cases_completed', 0)), "success")
        self._add_stat_row(stats_grid, "Cases Skipped",
                          str(self.stats.get('cases_skipped', 0)), "warning")
        self._add_stat_row(stats_grid, "Cases Failed",
                          str(self.stats.get('cases_failed', 0)), "danger")
        self._add_stat_row(stats_grid, "Total Processed",
                          str(self.stats.get('total_cases', 0)), "info")
        self._add_stat_row(stats_grid, "Duration",
                          self.stats.get('duration', 'N/A'), "info")
        
        card_layout.addLayout(stats_grid)
        
        return card
    
    def _add_stat_row(self, layout: QVBoxLayout, label: str, value: str, style: str):
        """Add a statistics row."""
        row = QHBoxLayout()
        row.setSpacing(Spacing.MD)
        
        label_widget = QLabel(label)
        label_widget.setObjectName("statLabel")
        self.apply_typography_to_widget(label_widget, 'body')
        row.addWidget(label_widget)
        
        row.addStretch(1)
        
        value_widget = QLabel(value)
        value_widget.setObjectName(f"statValue_{style}")
        self.apply_typography_to_widget(value_widget, 'body_lg', QFont.Bold)
        row.addWidget(value_widget)
        
        layout.addLayout(row)
    
    def _apply_theme(self):
        """Apply theme-aware styling."""
        theme_mode = self.settings_bus.theme
        colors = Colors.DARK if theme_mode == "dark" else Colors.LIGHT
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
            }}
            
            QLabel#successIcon {{
                color: {colors['success']};
            }}
            
            QLabel#dialogTitle {{
                color: {colors['text_primary']};
            }}
            
            QFrame#statsCard {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
            
            QLabel#cardTitle {{
                color: {colors['text_primary']};
                padding-bottom: {Spacing.SM}px;
            }}
            
            QLabel#statLabel {{
                color: {colors['text_secondary']};
            }}
            
            QLabel#statValue_success {{
                color: {colors['success']};
            }}
            
            QLabel#statValue_warning {{
                color: {colors['warning']};
            }}
            
            QLabel#statValue_danger {{
                color: {colors['danger']};
            }}
            
            QLabel#statValue_info {{
                color: {colors['text_primary']};
            }}
            
            QPushButton#primaryButton {{
                background-color: {colors['primary']};
                color: {colors['text_inverse']};
                border: none;
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {colors['primary_hover']};
            }}
        """)
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        self._apply_theme()
    
    def _on_font_changed(self, font_size: int):
        """Handle font size change."""
        # Reapply typography to all widgets with current font size
        icon = self.findChild(QLabel, "successIcon")
        if icon:
            self.apply_typography_to_widget(icon, 'display_lg')
        
        header = self.findChild(QLabel, "dialogTitle")
        if header:
            self.apply_typography_to_widget(header, 'h1', QFont.Bold)
        
        card_title = self.findChild(QLabel, "cardTitle")
        if card_title:
            self.apply_typography_to_widget(card_title, 'h3', QFont.Bold)
        
        # Update stat labels
        for label in self.findChildren(QLabel):
            if label.objectName() == "statLabel":
                self.apply_typography_to_widget(label, 'body')
            elif label.objectName() and label.objectName().startswith("statValue_"):
                self.apply_typography_to_widget(label, 'body_lg', QFont.Bold)
        
        # Update buttons
        for btn in self.findChildren(QPushButton):
            if btn.objectName() == "primaryButton":
                self.apply_typography_to_widget(btn, 'button', QFont.Bold)
        
        # Reapply theme to update any font-size dependent styles
        self._apply_theme()


def run_auto_sender(excel_path=None, support_agents=None, support_agent=None):
    """
    Main entry point for Auto Sender mode.
    Processes NEW cases only - sends SMS, Email, adds Notes.
    After NEW cases, runs Companies Process, then exits to Dispatcher.

    Args:
        excel_path:     Optional path to the Excel file.
        support_agents: List of agent names being supported (DEV MODE: multiple).
                        When provided, cases are pulled from each agent's sheet in turn.
                        Signatures / case-notes always use the config AGENT_NAME.
        support_agent:  Legacy single-name parameter (kept for backward compat).
                        Ignored when support_agents is given.
    """
    # Normalise: support_agents wins; fall back to legacy support_agent
    if support_agents is None:
        support_agents = [support_agent] if support_agent else []

    # Ensure QApplication exists FIRST before any QWidget creation
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()

    print("=" * 60)
    print("       AUTO SENDER - Process New Cases")
    print("=" * 60)

    # Build the list of (working_agent_name, sheet_name) pairs to process.
    # working_agent_name → used only for cache-file naming (first name or own).
    # sheet_name         → the Excel sheet to pull cases from.
    # NOTE: Signatures / case-notes always read AGENT_NAME (config) — never changed here.
    if support_agents:
        sheet_names = [f"{name}'s Cases" for name in support_agents]
        working_agent = support_agents[0]   # cache folder key (first supported agent)
        print(f"[INFO] Support Mode: Working on sheets: {', '.join(sheet_names)}")
    else:
        sheet_names = [EXCEL_SHEET_NAME]
        working_agent = AGENT_NAME
        print(f"[INFO] Agent: {AGENT_NAME}")

    # For single-sheet runs (the common path) keep existing behaviour unchanged.
    sheet_name = sheet_names[0]
    print(f"[INFO] Using sheet: {sheet_name}")
    if len(sheet_names) > 1:
        print(f"[INFO] DEV MODE: additional sheets will follow — {sheet_names[1:]}")
    
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
            stats = progress_monitor.get_statistics()
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
