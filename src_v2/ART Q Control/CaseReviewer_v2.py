# ============================================================================
# CaseReviewer_v2.py - Review IN-PROGRESS Cases (With Dialer) - MODERNIZED
# ============================================================================
# Phase 6.7: CaseReviewer Modernization
# - Integrated V2 foundation systems (ThemeManager, TypographyMixin, SettingsBus)
# - Modernized dialogs with V2 styling
# - Keyboard shortcuts support
# - Enhanced navigation UI
# - Improved company metadata display
#
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
    QLineEdit, QRadioButton, QButtonGroup, QGroupBox, QFrame, QShortcut
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QResizeEvent, QKeySequence

# Ensure both src and this directory are in path for proper imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

art_q_dir = os.path.dirname(os.path.abspath(__file__))
if art_q_dir not in sys.path:
    sys.path.insert(0, art_q_dir)

# Import V2 foundation systems (Phase 6.7)
from ui.theme_manager import get_theme_manager
from ui.typography_mixin import V2TypographyMixin
from ui.services import get_v2_settings_bus, V2ThemeService
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory
from ui.design_system import Colors, Spacing, BorderRadius

# Phase 3.2: Theme and Accessibility Managers (imported lazily after QApplication)
theme_manager = None
accessibility_manager = None
error_logger = None
v2_settings_bus = None
v2_theme_service = None

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
    Phase 6.7 Modernized Version: Check if cache exists and show remaining case count.
    
    Uses V2 theme system and modern styling.
    
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
    
    # Get V2 theme service
    global v2_theme_service
    if v2_theme_service is None:
        v2_theme_service = V2ThemeService()
    
    # Get current theme from settings bus
    global v2_settings_bus
    if v2_settings_bus is None:
        v2_settings_bus = get_v2_settings_bus()
    
    theme_mode = v2_settings_bus.theme
    colors = v2_theme_service.colors_for(theme_mode)
    font_size = v2_settings_bus.font_size

    class EnhancedResumeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f"Resume {mode_name}?")
            self.setFixedSize(500, 230)
            self._result = "NEW"  # Use _result to avoid conflict with QDialog.result()
            
            # Store current theme and font settings
            self._theme = theme_mode
            self._colors = colors
            self._font_size = font_size
            
            # Subscribe to settings bus
            self.settings_bus = get_v2_settings_bus()
            self.settings_bus.theme_changed.connect(self._on_theme_changed)
            self.settings_bus.font_size_changed.connect(self._on_font_changed)
            
            # Apply V2 styling
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {self._colors['window_bg']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
            """)
            self.setFont(QFont('IBM Plex Sans', self._font_size))

            layout = QVBoxLayout(self)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 20, 24, 20)

            header = QLabel("Existing session found")
            header.setFont(QFont('IBM Plex Sans', font_size, QFont.Bold))
            header.setStyleSheet(f"font-weight: 700; color: {colors['text_primary']}; background: transparent; border: none;")
            layout.addWidget(header)

            # Store widgets for dynamic updates
            self.header = header
            self.info_frame = QFrame()
            self.info_frame.setStyleSheet(
                f"background-color: {self._colors['accent_soft']};"
                f"border-left: 4px solid {self._colors['accent']};"
                f"border-top: 1px solid {self._colors['surface_border']};"
                f"border-right: 1px solid {self._colors['surface_border']};"
                f"border-bottom: 1px solid {self._colors['surface_border']};"
                f"border-radius: 4px; padding: 4px;"
            )
            info_layout_inner = QVBoxLayout(self.info_frame)
            info_layout_inner.setContentsMargins(12, 8, 12, 8)
            self.remaining_text = QLabel(f"{count_message.capitalize()}\n\nWould you like to resume where you left off?")
            self.remaining_text.setFont(QFont('IBM Plex Sans', self._font_size))
            self.remaining_text.setStyleSheet(f"color: {self._colors['text_primary']}; background: transparent; border: none;")
            self.remaining_text.setWordWrap(True)
            info_layout_inner.addWidget(self.remaining_text)
            layout.addWidget(self.info_frame)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)

            self.resume_btn = QPushButton("Resume")
            self.resume_btn.setFont(QFont('IBM Plex Sans', self._font_size, QFont.Bold))
            self.resume_btn.setStyleSheet(
                f"QPushButton {{ background-color: {self._colors['accent']}; color: #ffffff;"
                f" font-weight: 600; padding: 12px 28px; border: none; border-radius: 4px;"
                f" font-size: {self._font_size}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {self._colors['accent_hover']}; }}"
            )
            self.resume_btn.clicked.connect(self.on_resume)
            btn_layout.addWidget(self.resume_btn)

            self.new_btn = QPushButton("Start Fresh")
            self.new_btn.setFont(QFont('IBM Plex Sans', self._font_size))
            self.new_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {self._colors['accent']};"
                f" font-weight: 600; padding: 12px 28px;"
                f" border: 2px solid {self._colors['accent']}; border-radius: 4px;"
                f" font-size: {self._font_size}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {self._colors['surface_alt']}; }}"
            )
            self.new_btn.clicked.connect(self.on_new)
            btn_layout.addWidget(self.new_btn)

            layout.addLayout(btn_layout)
            self.setLayout(layout)
            
            # Install event filter to block keyboard entries
            self.installEventFilter(self)
        
        def _on_theme_changed(self, theme: str):
            """Handle theme changes"""
            self._theme = theme
            self._colors = v2_theme_service.colors_for(theme)
            self._apply_theme()
        
        def _on_font_changed(self, font_size: int):
            """Handle font size changes"""
            self._font_size = font_size
            self._apply_theme()
        
        def _apply_theme(self):
            """Apply current theme and font settings to all widgets"""
            # Update main dialog
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {self._colors['window_bg']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
            """)
            self.setFont(QFont('IBM Plex Sans', self._font_size))
            
            # Update header
            self.header.setFont(QFont('IBM Plex Sans', self._font_size, QFont.Bold))
            self.header.setStyleSheet(f"font-weight: 700; color: {self._colors['text_primary']}; background: transparent; border: none;")
            
            # Update info frame
            self.info_frame.setStyleSheet(
                f"background-color: {self._colors['accent_soft']};"
                f"border-left: 4px solid {self._colors['accent']};"
                f"border-top: 1px solid {self._colors['surface_border']};"
                f"border-right: 1px solid {self._colors['surface_border']};"
                f"border-bottom: 1px solid {self._colors['surface_border']};"
                f"border-radius: 4px; padding: 4px;"
            )
            
            # Update remaining text
            self.remaining_text.setFont(QFont('IBM Plex Sans', self._font_size))
            self.remaining_text.setStyleSheet(f"color: {self._colors['text_primary']}; background: transparent; border: none;")
            
            # Update buttons
            self.resume_btn.setFont(QFont('IBM Plex Sans', self._font_size, QFont.Bold))
            self.resume_btn.setStyleSheet(
                f"QPushButton {{ background-color: {self._colors['accent']}; color: #ffffff;"
                f" font-weight: 600; padding: 12px 28px; border: none; border-radius: 4px;"
                f" font-size: {self._font_size}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {self._colors['accent_hover']}; }}"
            )
            
            self.new_btn.setFont(QFont('IBM Plex Sans', self._font_size))
            self.new_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {self._colors['accent']};"
                f" font-weight: 600; padding: 12px 28px;"
                f" border: 2px solid {self._colors['accent']}; border-radius: 4px;"
                f" font-size: {self._font_size}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {self._colors['surface_alt']}; }}"
            )
        
        def eventFilter(self, obj, event):
            """Block keyboard entries at dialog level"""
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Tab, Qt.Key_Backtab):
                    print("[EVENT FILTER] Blocked key in EnhancedResumeDialog: {}".format(key))
                    return True
            return super().eventFilter(obj, event)
        
        def on_resume(self):
            self._result = "RESUME"
            self.accept()
        
        def on_new(self):
            self._result = "NEW"
            self.accept()
        
        def keyPressEvent(self, event):
            """
            Override keyPressEvent to prevent accidental button activation.
            Blocks: Enter, Space, Tab, Shift+Tab, Arrow keys
            Allows: Mouse clicks only
            """
            key = event.key()
            print("[EnhancedResumeDialog] keyPressEvent called with key: {}".format(key))
            
            # Block keyboard-based selections that might trigger buttons
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space,
                      Qt.Key_Tab, Qt.Key_Backtab,
                      Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                print("[KEYBOARD BLOCKED] Blocked key in EnhancedResumeDialog: {}".format(key))
                event.ignore()
                return
            
            # Allow other keys (unlikely but be safe)
            super().keyPressEvent(event)
    
    app = QApplication.instance()
    if app is None:
        # Fallback for standalone dialog testing
        app = QApplication(sys.argv)
    
    dialog = EnhancedResumeDialog()
    dialog.exec_()
    return dialog._result

# ============================================================================
# CASE REVIEWER DIALOG
# ============================================================================
def get_case_closing_code(case_number, cases_completed_count, total_in_progress_count=None, case_status="in_progress", current_position=None):
    """
    Phase 6.7 Modernized: Opens a case reviewer dialog for the current case.
    
    Uses V2 theme system, typography, and keyboard shortcuts.
    Creates a fresh dialog for each case to avoid garbage collection issues.
    Returns the selected closing code and whether to add a note.
    
    Args:
        case_number: The case number
        cases_completed_count: Number of cases completed (used for progress if current_position not provided)
        total_in_progress_count: Total number of cases
        case_status: Status of the case (in_progress, skipped, etc.)
        current_position: Current position in the list (1-based) - if provided, overrides cases_completed_count for display
    """
    # Get V2 theme service and settings bus
    global v2_theme_service, v2_settings_bus
    if v2_theme_service is None:
        v2_theme_service = V2ThemeService()
    if v2_settings_bus is None:
        v2_settings_bus = get_v2_settings_bus()
    
    theme_mode = v2_settings_bus.theme
    colors = v2_theme_service.colors_for(theme_mode)
    font_size = v2_settings_bus.font_size

    class CaseReviewerDialog(QDialog, V2TypographyMixin):
        def __init__(self, case_num, cases_completed, total_count, status, current_position=None):
            QDialog.__init__(self)
            V2TypographyMixin.__init__(self)
            
            self.case_num = case_num
            self.cases_completed = cases_completed
            self.total_count = total_count
            self.case_status = status
            self.current_position = current_position

            self._theme = theme_mode
            self._colors = colors
            self._base_font_size = font_size
            self._buttons = []
            self._section_headers = []
            self._copy_btn = None
            self._scroll = None
            self._custom_button = None
            self._close_btn = None
            self._shortcut_manager = None

            font = self.get_font('body')
            self.setFont(font)
            self.setWindowTitle("Case Reviewer")
            self.resize(620, 850)
            self.selected_code = None
            self.add_note = False
            self.setModal(True)
            
            # Apply V2 styling
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['window_bg']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
            """)
            
            # Main layout
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.setSpacing(8)
            
            # ========== TOP PANEL: Case Info & Progress ==========
            info_layout = QVBoxLayout()
            info_layout.setSpacing(12)
            
            # Case info with copy button
            case_info_h_layout = QHBoxLayout()
            case_info_h_layout.setSpacing(12)
            case_info_h_layout.setContentsMargins(0, 0, 0, 0)
            
            self.case_info_label = QLabel()
            self.case_info_label.setFont(self.get_font('h2', QFont.Bold))
            self.case_info_label.setStyleSheet(
                f"font-weight: 700; color: {colors['accent']}; background: transparent; border: none;"
            )
            case_info_h_layout.addWidget(self.case_info_label)
            
            # Copy button
            copy_btn = QPushButton("📋")
            self._copy_btn = copy_btn
            copy_btn.setMaximumWidth(40)
            copy_btn.setMaximumHeight(40)
            copy_btn.setToolTip("Copy case number to clipboard")
            copy_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; border: 1px solid {colors['surface_border']};"
                f" border-radius: 4px; padding: 4px; font-size: 16pt; }}"
                f"QPushButton:hover {{ background-color: {colors['surface_alt']}; border: 1px solid {colors['accent']}; }}"
                f"QPushButton:pressed {{ background-color: {colors['accent']}; color: #ffffff; }}"
            )
            copy_btn.clicked.connect(self.copy_case_number)
            case_info_h_layout.addWidget(copy_btn)
            case_info_h_layout.addStretch()
            
            info_layout.addLayout(case_info_h_layout)

            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(10)
            self.progress_bar.setStyleSheet(
                f"QProgressBar {{ border: none; border-radius: 4px;"
                f" background-color: {colors['surface_border']}; }}"
                f"QProgressBar::chunk {{ background-color: {colors['accent']}; border-radius: 4px; }}"
            )
            info_layout.addWidget(self.progress_bar)

            # Case position label (below bar)
            self.case_position_label = QLabel()
            self.case_position_label.setFont(self.get_font('caption'))
            self.case_position_label.setStyleSheet(
                f"color: {colors['text_secondary']}; background: transparent; border: none;"
            )
            info_layout.addWidget(self.case_position_label)
            
            main_layout.addLayout(info_layout)
            main_layout.addSpacing(10)
            
            # ========== SCROLLABLE BUTTON SECTIONS ==========
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setStyleSheet(f"""
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """)
            scroll_widget = QWidget()
            scroll_widget.setStyleSheet("background-color: transparent;")
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)  # Reduced from 15
            scroll_layout.setContentsMargins(5, 5, 5, 5)  # Add margins
            
            # ===== SECTION A: Issue Resolution =====
            scroll_layout.addWidget(self._create_section_header("Issue Resolution"))
            self._scroll = scroll
            sec_a = QGridLayout()
            sec_a.setSpacing(6)  # Reduced from 8
            sec_a.setColumnStretch(0, 1)
            sec_a.setColumnStretch(1, 1)
            
            sec_a_buttons = [
                ("Resolved", "Issue Resolved"),
                ("Issue Not Fixed", "Issue Not Fixed"),
                ("Not Reached", "Customer Not Reached"),
                ("Not Yet Tested", "Not Yet Tested"),
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

            self.add_note_checkbox = QCheckBox("Add Case Note")
            self.add_note_checkbox.setFont(self.get_font('body'))
            self.add_note_checkbox.setStyleSheet(f"padding: 6px; color: {colors['text_primary']};")
            bottom_layout.addWidget(self.add_note_checkbox)

            close_btn = QPushButton("Close & Exit Application")
            self._close_btn = close_btn
            close_btn.setFont(self.get_font('button'))
            close_btn.setStyleSheet(
                f"QPushButton {{ background-color: #da1e28; color: #ffffff;"
                f" border: none; border-radius: 4px; font-weight: 600;"
                f" padding: 10px; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: #ba1b23; }}"
            )
            close_btn.clicked.connect(lambda: self.on_button_clicked("CLOSE_APPLICATION"))
            bottom_layout.addWidget(close_btn)

            # Add bottom layout to main layout
            main_layout.addLayout(bottom_layout)

            self.setLayout(main_layout)
            self.update_case_info(self.case_num, self.cases_completed, self.total_count, self.current_position)
            
            # Setup keyboard shortcuts
            self._setup_shortcuts()
            
            # Install event filter to block keyboard entries at the dialog level
            self.installEventFilter(self)
            self._blocked_keys_count = 0
            
            # Subscribe to settings bus for theme/font changes
            self.settings_bus = get_v2_settings_bus()
            self.settings_bus.theme_changed.connect(self._on_theme_changed)
            self.settings_bus.font_size_changed.connect(self._on_font_changed)
            
            # Apply initial typography
            self.apply_typography()
        
        def _setup_shortcuts(self):
            """Setup keyboard shortcuts for the dialog"""
            self._shortcut_manager = ShortcutManager(self)
            
            # Register shortcuts
            self._shortcut_manager.register_shortcut(
                "skip_case",
                ShortcutDefinition(
                    key_sequence="Ctrl+S",
                    description="Skip current case",
                    category=ShortcutCategory.TOOL_SPECIFIC,
                    action=lambda: self.on_button_clicked("Skipped")
                )
            )
            
            self._shortcut_manager.register_shortcut(
                "previous_case",
                ShortcutDefinition(
                    key_sequence="Ctrl+P",
                    description="Go to previous case",
                    category=ShortcutCategory.NAVIGATION,
                    action=lambda: self.close_with_nav("NAV_PREV")
                )
            )
            
            self._shortcut_manager.register_shortcut(
                "close_case",
                ShortcutDefinition(
                    key_sequence="Ctrl+C",
                    description="Close current case",
                    category=ShortcutCategory.TOOL_SPECIFIC,
                    action=lambda: self.on_button_clicked("Issue Resolved")
                )
            )
            
            self._shortcut_manager.register_shortcut(
                "toggle_note",
                ShortcutDefinition(
                    key_sequence="Ctrl+N",
                    description="Toggle add case note",
                    category=ShortcutCategory.TOOL_SPECIFIC,
                    action=self._toggle_note_checkbox
                )
            )
        
        def _toggle_note_checkbox(self):
            """Toggle the add note checkbox"""
            self.add_note_checkbox.setChecked(not self.add_note_checkbox.isChecked())
        
        def apply_typography(self):
            """Apply typography to all widgets"""
            # Update fonts using typography system
            self.case_info_label.setFont(self.get_font('h2', QFont.Bold))
            self.case_position_label.setFont(self.get_font('caption'))
            self.add_note_checkbox.setFont(self.get_font('body'))
            if self._close_btn:
                self._close_btn.setFont(self.get_font('button'))
            
            # Update section headers
            for header in self._section_headers:
                header.setFont(self.get_font('h3', QFont.Bold))
            
            # Update buttons
            for btn in self._buttons:
                btn.setFont(self.get_font('button', QFont.Bold))
        
        def _on_theme_changed(self, theme: str):
            """Handle theme changes"""
            self._theme = theme
            self._colors = v2_theme_service.colors_for(theme)
            self._update_styling()
        
        def _on_font_changed(self, font_size: int):
            """Handle font size changes"""
            self._base_font_size = font_size
            self.apply_typography()
            self._update_styling()  # Reapply to refresh font-dependent styles
        
        def _update_styling(self):
            """Update all styling with current theme colors"""
            colors = self._colors
            
            # Update main dialog and scroll area
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['window_bg']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
                QScrollArea {{
                    background-color: transparent;
                    border: none;
                }}
                QScrollArea > QWidget > QWidget {{
                    background-color: transparent;
                }}
            """)
            
            # Update scroll area styling
            if self._scroll:
                self._scroll.setStyleSheet(f"""
                    QScrollArea {{
                        background-color: transparent;
                        border: none;
                    }}
                    QScrollArea > QWidget > QWidget {{
                        background-color: transparent;
                    }}
                """)
            
            # Update case info label
            self.case_info_label.setStyleSheet(
                f"font-weight: 700; color: {colors['accent']}; background: transparent; border: none;"
            )
            
            # Update copy button
            if self._copy_btn:
                self._copy_btn.setStyleSheet(
                    f"QPushButton {{ background-color: transparent; border: 1px solid {colors['surface_border']};"
                    f" border-radius: 4px; padding: 4px; font-size: 16pt; }}"
                    f"QPushButton:hover {{ background-color: {colors['surface_alt']}; border: 1px solid {colors['accent']}; }}"
                    f"QPushButton:pressed {{ background-color: {colors['accent']}; color: #ffffff; }}"
                )
            
            # Update progress bar
            self.progress_bar.setStyleSheet(
                f"QProgressBar {{ border: none; border-radius: 4px;"
                f" background-color: {colors['surface_border']}; }}"
                f"QProgressBar::chunk {{ background-color: {colors['accent']}; border-radius: 4px; }}"
            )
            
            # Update case position label
            self.case_position_label.setStyleSheet(
                f"color: {colors['text_secondary']}; background: transparent; border: none;"
            )
            
            # Update checkbox
            self.add_note_checkbox.setStyleSheet(f"padding: 6px; color: {colors['text_primary']};")
            
            # Update section headers
            for header in self._section_headers:
                header.setStyleSheet(
                    f"font-weight: 700; color: {colors['text_primary']};"
                    f" background: transparent; border: none;"
                    f" border-bottom: 2px solid {colors['accent']};"
                    f" padding-bottom: 4px; margin-top: 6px; letter-spacing: 0.5px;"
                )
            
            # Update buttons
            for btn in self._buttons:
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {colors['surface']};"
                    f" border: 1px solid {colors['surface_border']}; border-radius: 4px;"
                    f" font-weight: 600; color: {colors['text_primary']};"
                    f" padding: 6px 10px; text-align: center; }}"
                    f"QPushButton:hover {{ background-color: {colors['accent']};"
                    f" color: #ffffff; border: 1px solid {colors['accent']}; }}"
                    f"QPushButton:pressed {{ background-color: {colors['accent_hover']};"
                    f" color: #ffffff; }}"
                )

        def close_with_nav(self, nav_code):
            self.selected_code = nav_code
            self.add_note = bool(self.add_note_checkbox.isChecked())
            self.accept()

        def _create_section_header(self, title):
            """V2 section header: bold label with accent bottom border"""
            header = QLabel(title.upper())
            self._section_headers.append(header)
            header.setFont(self.get_font('h3', QFont.Bold))
            header.setStyleSheet(
                f"font-weight: 700; color: {colors['text_primary']};"
                f" background: transparent; border: none;"
                f" border-bottom: 2px solid {colors['accent']};"
                f" padding-bottom: 4px; margin-top: 6px;"
                f" letter-spacing: 0.5px;"
            )
            return header

        def _create_button(self, label_text, code, bg_color):
            """V2 action button with modern styling"""
            btn = QPushButton(label_text)
            self._buttons.append(btn)
            btn.setFont(self.get_font('button', QFont.Bold))
            btn.setMinimumHeight(42)
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {colors['surface']};"
                f" border: 1px solid {colors['surface_border']}; border-radius: 4px;"
                f" font-weight: 600; color: {colors['text_primary']};"
                f" padding: 6px 10px; text-align: center; }}"
                f"QPushButton:hover {{ background-color: {colors['accent']};"
                f" color: #ffffff; border: 1px solid {colors['accent']}; }}"
                f"QPushButton:pressed {{ background-color: {colors['accent_hover']};"
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
        
        def copy_case_number(self):
            """Copy case number to clipboard"""
            try:
                from PyQt5.QtWidgets import QApplication
                from PyQt5.QtGui import QClipboard
                
                # Extract case number from label text (format: "Case XXXXX — Status")
                label_text = self.case_info_label.text()
                if label_text and "Case" in label_text:
                    case_num = label_text.split("Case ")[1].split("  —")[0].strip()
                    
                    # Copy to clipboard
                    clipboard = QApplication.clipboard()
                    if clipboard is not None:
                        clipboard.setText(case_num)
                    print(f"[INFO] Case number copied to clipboard: {case_num}")
            except Exception as e:
                print(f"[WARN] Failed to copy case number: {e}")
        
        def eventFilter(self, a0, a1):
            return super().eventFilter(a0, a1)
        
        def on_button_clicked(self, code):
            """Handle button click - close dialog with result"""
            self.selected_code = code
            self.add_note = bool(self.add_note_checkbox.isChecked())
            self.accept()  # Close dialog and return success
        
        def ask_other_code(self):
            """Ask for custom closing code with Final Action, Status and themed styling."""
            c = self._colors

            custom_dialog = QDialog(self)
            custom_dialog.setWindowTitle("Custom Closing Code")
            custom_dialog.resize(420, 300)
            custom_dialog.setStyleSheet(f"""
                QDialog {{
                    background-color: {c['window_bg']};
                    color: {c['text_primary']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
                QLabel {{
                    color: {c['text_primary']};
                    background: transparent;
                    border: none;
                }}
                QLineEdit {{
                    background-color: {c['surface']};
                    color: {c['text_primary']};
                    border: 1px solid {c['surface_border']};
                    border-radius: 4px;
                    padding: 6px 10px;
                    selection-background-color: {c['accent']};
                    selection-color: #ffffff;
                }}
                QLineEdit:focus {{
                    border-color: {c['accent']};
                }}
                QGroupBox {{
                    color: {c['text_primary']};
                    border: 1px solid {c['surface_border']};
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 6px;
                    font-weight: 600;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 8px;
                    color: {c['text_primary']};
                }}
                QRadioButton {{
                    color: {c['text_primary']};
                    background: transparent;
                    spacing: 6px;
                    padding: 2px 0px;
                }}
                QRadioButton::indicator {{
                    width: 14px;
                    height: 14px;
                }}
                QPushButton {{
                    background-color: {c['surface']};
                    color: {c['text_primary']};
                    border: 1px solid {c['surface_border']};
                    border-radius: 4px;
                    font-weight: 500;
                    padding: 7px 20px;
                    min-height: 32px;
                }}
                QPushButton:hover {{
                    background-color: {c['surface_alt']};
                    border-color: {c['accent']};
                }}
            """)

            layout = QVBoxLayout(custom_dialog)
            layout.setSpacing(12)
            layout.setContentsMargins(16, 14, 16, 14)

            # Custom code text input
            text_label = QLabel("Enter custom closing code (for notes):")
            text_label.setFont(self.get_font('body'))
            layout.addWidget(text_label)

            text_input = QLineEdit()
            text_input.setPlaceholderText("Custom code text...")
            text_input.setMinimumHeight(34)
            text_input.setFont(self.get_font('body'))
            layout.addWidget(text_input)

            # Radio buttons section
            radio_layout = QHBoxLayout()
            radio_layout.setSpacing(10)

            # Final Action column
            final_action_group = QGroupBox("Final Action")
            final_action_layout = QVBoxLayout(final_action_group)
            final_action_layout.setSpacing(4)
            self.final_action_btn_group = QButtonGroup(custom_dialog)

            reviewed_radio = QRadioButton("Reviewed")
            reviewed_radio.setChecked(True)
            reviewed_radio.setFont(self.get_font('body'))
            not_reached_radio = QRadioButton("Not Reached")
            not_reached_radio.setFont(self.get_font('body'))

            self.final_action_btn_group.addButton(reviewed_radio, 0)
            self.final_action_btn_group.addButton(not_reached_radio, 1)

            final_action_layout.addWidget(reviewed_radio)
            final_action_layout.addWidget(not_reached_radio)
            radio_layout.addWidget(final_action_group)

            # Status column
            status_group = QGroupBox("Status")
            status_layout = QVBoxLayout(status_group)
            status_layout.setSpacing(4)
            self.status_btn_group = QButtonGroup(custom_dialog)

            in_progress_radio = QRadioButton("In Progress")
            in_progress_radio.setChecked(True)
            in_progress_radio.setFont(self.get_font('body'))
            skipped_radio = QRadioButton("Skipped")
            skipped_radio.setFont(self.get_font('body'))
            closed_radio = QRadioButton("Closed")
            closed_radio.setFont(self.get_font('body'))

            self.status_btn_group.addButton(in_progress_radio, 0)
            self.status_btn_group.addButton(skipped_radio, 1)
            self.status_btn_group.addButton(closed_radio, 2)

            status_layout.addWidget(in_progress_radio)
            status_layout.addWidget(skipped_radio)
            status_layout.addWidget(closed_radio)
            radio_layout.addWidget(status_group)

            layout.addLayout(radio_layout)

            # OK/Cancel buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(8)

            ok_btn = QPushButton("OK")
            ok_btn.setStyleSheet(
                f"QPushButton {{ background-color: {c['accent']}; color: #ffffff;"
                f" border: none; border-radius: 4px; font-weight: 600; padding: 7px 20px; }}"
                f"QPushButton:hover {{ background-color: {c['accent_hover']}; }}"
            )
            ok_btn.setFont(self.get_font('button'))

            cancel_btn = QPushButton("Cancel")
            cancel_btn.setFont(self.get_font('button'))

            ok_btn.clicked.connect(custom_dialog.accept)
            cancel_btn.clicked.connect(custom_dialog.reject)

            btn_layout.addWidget(cancel_btn)
            btn_layout.addWidget(ok_btn)
            layout.addLayout(btn_layout)

            if custom_dialog.exec_() == QDialog.Accepted:
                custom_text = text_input.text().strip()

                # Get selected Final Action
                final_action_id = self.final_action_btn_group.checkedId()
                final_action = "Reviewed" if final_action_id == 0 else "Not Reached"

                # Get selected Status
                status_id = self.status_btn_group.checkedId()
                if status_id == 0:
                    status = "In Progress"
                elif status_id == 1:
                    status = "Skipped"
                else:
                    status = "Closed"

                # Store the selections for later use
                self.custom_final_action = final_action
                self.custom_status = status

                # Use the custom text as the code (for notes), but also pass final action and status
                if custom_text:
                    result_code = f"CUSTOM|{custom_text}|{final_action}|{status}"
                    self.on_button_clicked(result_code)
                else:
                    result_code = f"CUSTOM||{final_action}|{status}"
                    self.on_button_clicked(result_code)
        
        def resizeEvent(self, event):
            """Handle window resize - update typography if needed"""
            super().resizeEvent(event)
            # Typography system handles responsive sizing automatically
    
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
    Phase 6.7 Modernized: Opens a call outcome dialog for the current call.
    
    Uses V2 theme system and modern styling.
    Returns the selected closing code and whether to add a note.
    """
    closing_code = {"value": None, "add_note": False}

    # Get V2 theme service and settings bus
    global v2_theme_service, v2_settings_bus
    if v2_theme_service is None:
        v2_theme_service = V2ThemeService()
    if v2_settings_bus is None:
        v2_settings_bus = get_v2_settings_bus()

    class CallOutcomeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Call Closing Code")
            self.setMinimumWidth(360)
            self.setMinimumHeight(360)
            
            # Subscribe to settings bus (reactive pattern)
            self.settings_bus = get_v2_settings_bus()
            self.settings_bus.theme_changed.connect(self._on_theme_changed)
            self.settings_bus.font_size_changed.connect(self._on_font_changed)
            
            # Get current settings from bus (no snapshots)
            self._theme = self.settings_bus.theme
            self._colors = v2_theme_service.colors_for(self._theme)
            self._font_size = self.settings_bus.font_size
            self._buttons = []
            
            # Apply V2 styling
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {self._colors['window_bg']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
            """)
            self.setFont(QFont('IBM Plex Sans', self._font_size))

            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(16, 12, 16, 12)
            main_layout.setSpacing(8)

            self.header = QLabel("Call Closing Code")
            self.header.setFont(QFont('IBM Plex Sans', self._font_size - 6, QFont.Normal))
            self.header.setStyleSheet(
                f"font-weight: 500; color: {self._colors['text_primary']};"
                f" background: transparent; border: none; padding-bottom: 4px;"
            )
            main_layout.addWidget(self.header)

            btn_frame = QWidget()
            grid = QGridLayout(btn_frame)
            grid.setSpacing(6)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)

            buttons = [
                ("Issue Resolved",    "Called - Answered: Issue Resolved"),
                ("Issue Not Fixed",   "Called - Answered: Issue Not Resolved"),
                ("Not Reached",       "Customer Not Reached"),
                ("Not Yet Tested",    "Customer Claims that the Machine Not Yet Tested"),
            ]

            # Modern color scheme for button types
            self._btn_colors = [
                (self._colors['accent'],        self._colors['accent_hover']),      # Resolved  — Blue
                (self._colors.get('danger', '#da1e28'), self._colors.get('danger_hover', '#ba1b23')),  # Not Fixed — Red
                (self._colors['text_secondary'], self._colors['accent']),           # Not Reached — Grey
                (self._colors.get('info', self._colors['accent']), self._colors.get('info_hover', self._colors['accent_hover'])),  # Not Tested — Info
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
                    c = self._colors
                    custom_dialog = QDialog(self)
                    custom_dialog.setWindowTitle("Custom Closing Code")
                    custom_dialog.resize(420, 300)
                    custom_dialog.setStyleSheet(f"""
                        QDialog {{
                            background-color: {c['window_bg']};
                            color: {c['text_primary']};
                            font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                        }}
                        QLabel {{
                            color: {c['text_primary']};
                            background: transparent;
                            border: none;
                        }}
                        QLineEdit {{
                            background-color: {c['surface']};
                            color: {c['text_primary']};
                            border: 1px solid {c['surface_border']};
                            border-radius: 4px;
                            padding: 6px 10px;
                            selection-background-color: {c['accent']};
                            selection-color: #ffffff;
                        }}
                        QLineEdit:focus {{
                            border-color: {c['accent']};
                        }}
                        QGroupBox {{
                            color: {c['text_primary']};
                            border: 1px solid {c['surface_border']};
                            border-radius: 4px;
                            margin-top: 8px;
                            padding-top: 6px;
                            font-weight: 600;
                        }}
                        QGroupBox::title {{
                            subcontrol-origin: margin;
                            subcontrol-position: top left;
                            left: 8px;
                            color: {c['text_primary']};
                        }}
                        QRadioButton {{
                            color: {c['text_primary']};
                            background: transparent;
                            spacing: 6px;
                            padding: 2px 0px;
                        }}
                        QRadioButton::indicator {{
                            width: 14px;
                            height: 14px;
                        }}
                        QPushButton {{
                            background-color: {c['surface']};
                            color: {c['text_primary']};
                            border: 1px solid {c['surface_border']};
                            border-radius: 4px;
                            font-weight: 500;
                            padding: 7px 20px;
                            min-height: 32px;
                        }}
                        QPushButton:hover {{
                            background-color: {c['surface_alt']};
                            border-color: {c['accent']};
                        }}
                    """)

                    layout = QVBoxLayout(custom_dialog)
                    layout.setSpacing(12)
                    layout.setContentsMargins(16, 14, 16, 14)

                    text_label = QLabel("Enter custom closing code (for notes):")
                    text_label.setFont(QFont('IBM Plex Sans', self._font_size - 7))
                    layout.addWidget(text_label)

                    text_input = QLineEdit()
                    text_input.setPlaceholderText("Custom code text...")
                    text_input.setMinimumHeight(34)
                    text_input.setFont(QFont('IBM Plex Sans', self._font_size - 7))
                    layout.addWidget(text_input)

                    radio_layout = QHBoxLayout()
                    radio_layout.setSpacing(10)

                    # Final Action group
                    final_action_group = QGroupBox("Final Action")
                    fa_layout = QVBoxLayout(final_action_group)
                    fa_layout.setSpacing(4)
                    fa_btn_group = QButtonGroup(custom_dialog)

                    reviewed_radio = QRadioButton("Reviewed")
                    reviewed_radio.setChecked(True)
                    reviewed_radio.setFont(QFont('IBM Plex Sans', self._font_size - 7))
                    not_reached_radio = QRadioButton("Not Reached")
                    not_reached_radio.setFont(QFont('IBM Plex Sans', self._font_size - 7))

                    fa_btn_group.addButton(reviewed_radio, 0)
                    fa_btn_group.addButton(not_reached_radio, 1)
                    fa_layout.addWidget(reviewed_radio)
                    fa_layout.addWidget(not_reached_radio)
                    radio_layout.addWidget(final_action_group)

                    # Status group
                    status_group = QGroupBox("Status")
                    st_layout = QVBoxLayout(status_group)
                    st_layout.setSpacing(4)
                    st_btn_group = QButtonGroup(custom_dialog)

                    in_progress_radio = QRadioButton("In Progress")
                    in_progress_radio.setChecked(True)
                    in_progress_radio.setFont(QFont('IBM Plex Sans', self._font_size - 7))
                    skipped_radio = QRadioButton("Skipped")
                    skipped_radio.setFont(QFont('IBM Plex Sans', self._font_size - 7))
                    closed_radio = QRadioButton("Closed")
                    closed_radio.setFont(QFont('IBM Plex Sans', self._font_size - 7))

                    st_btn_group.addButton(in_progress_radio, 0)
                    st_btn_group.addButton(skipped_radio, 1)
                    st_btn_group.addButton(closed_radio, 2)
                    st_layout.addWidget(in_progress_radio)
                    st_layout.addWidget(skipped_radio)
                    st_layout.addWidget(closed_radio)
                    radio_layout.addWidget(status_group)

                    layout.addLayout(radio_layout)

                    btn_layout = QHBoxLayout()
                    btn_layout.setSpacing(8)

                    ok_btn = QPushButton("OK")
                    ok_btn.setFont(QFont('IBM Plex Sans', self._font_size - 7, QFont.Medium))
                    ok_btn.setStyleSheet(
                        f"QPushButton {{ background-color: {c['accent']}; color: #ffffff;"
                        f" border: none; border-radius: 4px; font-weight: 600; padding: 7px 20px; }}"
                        f"QPushButton:hover {{ background-color: {c['accent_hover']}; }}"
                    )
                    cancel_btn = QPushButton("Cancel")
                    cancel_btn.setFont(QFont('IBM Plex Sans', self._font_size - 7))

                    ok_btn.clicked.connect(custom_dialog.accept)
                    cancel_btn.clicked.connect(custom_dialog.reject)
                    btn_layout.addWidget(cancel_btn)
                    btn_layout.addWidget(ok_btn)
                    layout.addLayout(btn_layout)

                    if custom_dialog.exec_() == QDialog.Accepted:
                        custom_text = text_input.text().strip()
                        if custom_text:
                            set_code_and_close(custom_text)
                        else:
                            # Fall back to the selected final action label as the code
                            fa_label = "Reviewed" if fa_btn_group.checkedId() == 0 else "Not Reached"
                            set_code_and_close(fa_label)

                except Exception as e:
                    print(f"[WARN] Custom code input failed: {e}")

            for idx, ((label_text, code), (bg, hover)) in enumerate(zip(buttons, self._btn_colors)):
                r = idx // 2
                c = idx % 2
                btn = QPushButton(label_text)
                btn.setFont(QFont('IBM Plex Sans', self._font_size - 7, QFont.Normal))
                btn.setMinimumHeight(30)
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {bg}; color: #ffffff;"
                    f" border: none; border-radius: 4px;"
                    f" font-weight: 500; padding: 5px 4px;"
                    f" font-size: {self._font_size - 7}pt; text-align: center; }}"
                    f"QPushButton:hover {{ background-color: {hover}; }}"
                    f"QPushButton:pressed {{ background-color: {hover}; opacity: 0.9; }}"
                )
                btn.clicked.connect(lambda checked=False, c=code: set_code_and_close(c))
                self._buttons.append(btn)
                grid.addWidget(btn, r, c)

            main_layout.addWidget(btn_frame)

            self.other_btn = QPushButton("Custom Code")
            self.other_btn.setFont(QFont('IBM Plex Sans', self._font_size - 7))
            self.other_btn.setMinimumHeight(28)
            self.other_btn.setStyleSheet(
                f"QPushButton {{ background-color: {self._colors['surface']};"
                f" color: {self._colors['text_primary']};"
                f" border: 1px solid {self._colors['surface_border']}; border-radius: 4px;"
                f" font-weight: 500; padding: 4px;"
                f" font-size: {self._font_size - 7}pt; }}"
                f"QPushButton:hover {{ background-color: {self._colors['surface_alt']}; border-color: {self._colors['accent']}; }}"
            )
            self.other_btn.clicked.connect(ask_other_code)
            main_layout.addWidget(self.other_btn)

            self.add_note_checkbox = QCheckBox("Add Case Note")
            self.add_note_checkbox.setFont(QFont('IBM Plex Sans', self._font_size - 7))
            self.add_note_checkbox.setStyleSheet(f"padding: 2px; color: {self._colors['text_primary']};")
            main_layout.addWidget(self.add_note_checkbox)

            self.setLayout(main_layout)
            
            # Install event filter to block keyboard entries
            self.installEventFilter(self)
        
        def _on_theme_changed(self, theme: str):
            """Handle theme changes"""
            self._theme = theme
            self._colors = v2_theme_service.colors_for(theme)
            self._apply_theme()
        
        def _on_font_changed(self, font_size: int):
            """Handle font size changes"""
            self._font_size = font_size
            self._apply_theme()
        
        def _apply_theme(self):
            """Apply current theme and font settings to all widgets"""
            # Update main dialog
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {self._colors['window_bg']};
                    font-family: 'IBM Plex Sans', 'Segoe UI', Arial, sans-serif;
                }}
            """)
            self.setFont(QFont('IBM Plex Sans', self._font_size))
            
            # Update header
            self.header.setFont(QFont('IBM Plex Sans', self._font_size - 6, QFont.Normal))
            self.header.setStyleSheet(
                f"font-weight: 500; color: {self._colors['text_primary']};"
                f" background: transparent; border: none; padding-bottom: 4px;"
            )
            
            # Update button colors
            self._btn_colors = [
                (self._colors['accent'],        self._colors['accent_hover']),
                (self._colors.get('danger', '#da1e28'), self._colors.get('danger_hover', '#ba1b23')),
                (self._colors['text_secondary'], self._colors['accent']),
                (self._colors.get('info', self._colors['accent']), self._colors.get('info_hover', self._colors['accent_hover'])),
            ]
            
            # Update action buttons
            for idx, btn in enumerate(self._buttons):
                bg, hover = self._btn_colors[idx]
                btn.setFont(QFont('IBM Plex Sans', self._font_size - 7, QFont.Normal))
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {bg}; color: #ffffff;"
                    f" border: none; border-radius: 4px;"
                    f" font-weight: 500; padding: 5px 4px;"
                    f" font-size: {self._font_size - 7}pt; text-align: center; }}"
                    f"QPushButton:hover {{ background-color: {hover}; }}"
                    f"QPushButton:pressed {{ background-color: {hover}; opacity: 0.9; }}"
                )
            
            # Update custom code button
            self.other_btn.setFont(QFont('IBM Plex Sans', self._font_size - 7))
            self.other_btn.setStyleSheet(
                f"QPushButton {{ background-color: {self._colors['surface']};"
                f" color: {self._colors['text_primary']};"
                f" border: 1px solid {self._colors['surface_border']}; border-radius: 4px;"
                f" font-weight: 500; padding: 4px;"
                f" font-size: {self._font_size - 7}pt; }}"
                f"QPushButton:hover {{ background-color: {self._colors['surface_alt']}; border-color: {self._colors['accent']}; }}"
            )
            
            # Update checkbox
            self.add_note_checkbox.setFont(QFont('IBM Plex Sans', self._font_size - 7))
            self.add_note_checkbox.setStyleSheet(f"padding: 2px; color: {self._colors['text_primary']};")
        
        def eventFilter(self, a0, a1):
            return super().eventFilter(a0, a1)
    
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
def run_case_reviewer(support_agents=None, support_agent=None):
    """
    Main entry point for Case Reviewer mode.
    Processes IN-PROGRESS cases with dialer integration.
    Opens closing code dialog for each case.

    Args:
        support_agents: List of agent names being supported (DEV MODE: multiple).
                        Cases are pulled from each agent's sheet in turn.
                        Signatures / case-notes always use the config AGENT_NAME.
        support_agent:  Legacy single-name parameter (backward compat).
    """
    # Normalise
    if support_agents is None:
        support_agents = [support_agent] if support_agent else []

    global theme_manager, accessibility_manager, error_logger

    print("=" * 60)
    print("       CASE REVIEWER - Review In-Progress Cases")
    print("=" * 60)

    # Initialize QApplication FIRST (required before any QWidget is created)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()

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

    # Build sheet list.
    # NOTE: Signatures / case-notes always read AGENT_NAME from config — never overridden.
    if support_agents:
        sheet_names = [f"{name}'s Cases" for name in support_agents]
        working_agent = support_agents[0]
        print(f"[INFO] Support Mode: Working on sheets: {', '.join(sheet_names)}")
    else:
        sheet_names = [EXCEL_SHEET_NAME]
        working_agent = AGENT_NAME
        print(f"[INFO] Agent: {AGENT_NAME}")

    sheet_name = sheet_names[0]
    print(f"[INFO] Using sheet: {sheet_name}")
    if len(sheet_names) > 1:
        print(f"[INFO] DEV MODE: additional sheets will follow — {sheet_names[1:]}")
    
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
            except Exception:
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
            _advance_pointer = True  # Default: move forward after each case
            
            try:
                status = str(row.get(status_col, '')).strip().lower()
                case_number = row.get(case_col)
                
                if pd.isna(case_number) or not str(case_number).strip():
                    pointer += 1
                    continue
                
                # Convert to int first to remove .0, then to string
                try:
                    case_number = str(int(float(case_number))).strip()
                except (ValueError, TypeError):
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
                if CaseClosingCode in ("PREVIOUS_CASE", "NAV_PREV"):
                    if pointer > 0:
                        pointer -= 1  # Go back one position in the pointer
                        # Restore the previous case's status to 'in_progress' so the
                        # status-filter at the top of the loop doesn't skip over it
                        # (it may have been set to 'Closed' / 'In Progress Today' etc.)
                        prev_idx = to_process_indices[pointer]
                        prev_status = str(df.at[prev_idx, status_col]).strip().lower()
                        if prev_status not in ('in_progress', 'skipped'):
                            df.at[prev_idx, status_col] = 'in_progress'
                            print(f"[INFO] ⬅ Restored previous case status to 'in_progress' for re-review")
                        print(f"[INFO] ⬅ Navigating to previous case - Pointer: {pointer}")
                    else:
                        print(f"[INFO] ⚠ Already at first case - cannot navigate backwards")
                    _advance_pointer = False  # Don't auto-advance — pointer already set
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
                
                sms_text = ""
                email_text = ""

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
                
                # Handle CUSTOM format status (CUSTOM|text|final_action|status)
                if isinstance(CaseClosingCode, str) and CaseClosingCode.startswith("CUSTOM|"):
                    try:
                        parts = CaseClosingCode.split("|")
                        if len(parts) >= 4:
                            # Extract status from CUSTOM format
                            custom_status = parts[3].strip()
                            df.at[idx, "Status"] = custom_status
                        else:
                            # Fallback if format is incomplete
                            df.at[idx, "Status"] = 'Closed'
                    except Exception as e:
                        print(f"[WARN] Failed to parse CUSTOM status: {e}")
                        df.at[idx, "Status"] = 'Closed'
                else:
                    # Default status for non-CUSTOM codes
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
                failing_case_number = locals().get('case_number', 'UNKNOWN')
                print(f"[ERROR] Exception processing case {failing_case_number}: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                pointer += 1  # Move to next case on error
                continue
            
            # Increment index to move to next case (skipped when navigating backwards)
            if _advance_pointer:
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

        theme_mode = get_v2_settings_bus().theme
        colors = Colors.DARK if theme_mode == "dark" else Colors.LIGHT

        msg = QMessageBox()
        msg.setWindowTitle("Case Reviewer Complete")
        msg.setText(
            f"Case Reviewer has finished processing.\n\n"
            f"Processed: {processed}/{total} cases\n\n"
            f"Click OK to exit."
        )
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet(f"""
            QMessageBox {{ background-color: {colors['background']}; }}
            QMessageBox QLabel {{ color: {colors['text_primary']}; }}
            QPushButton {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: 4px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{ background-color: {colors['surface_hover']}; }}
        """)
        msg.exec_()
    except Exception as e:
        print(f"[WARN] Could not show completion dialog: {e}")

if __name__ == "__main__":
    run_case_reviewer()
