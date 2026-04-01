# ============================================================================
# CompaniesProcess_v2.py - Process Company Cases - ISOLATED VERSION
# ============================================================================
# Phase 5 Enhanced Version:
# - Company Process is NOW ISOLATED from AutoSender
# - Can be run as standalone from Dispatcher menu
# - Users explicitly choose to run Company Process
# - Not auto-triggered after AutoSender completion
# 
# Core functionality:
# - Process company cases grouped by email
# - Send bulk email to company contact
# - Perform call flow
# - Track outcomes per case
# ============================================================================

import os
import sys
import time
import traceback
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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

# Import PyQt5 for dialog
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QWidget, QFrame, QGridLayout,
    QProgressBar
)
from PyQt5.QtCore import Qt
from ui.settings_aware_dialog import SettingsAwareMixin

# Import shared functions
from SharedFunctions import (
    AGENT_NAME,
    CACHE_DIRECTORY,
    EXCEL_SHEET_NAME,
    find_column_case_insensitive,
    case_search_and_open,
    case_search_and_open_no_edit,
    solution_provided_check_and_skip,
    solution_provided_check_and_skip_companies,
    eticket_check_and_skip,
    send_Email,
    add_Case_Note,
    get_case_note,
    update_cache_file,
    perform_call_flow,
    CompaniesProcessDialog,
    load_companies_for_handler,
    build_companies_email_body,
    show_companies_email_confirmation,
    safe_find,
    click_safe,
    Chrome_ART_Profile,
    perform_dialer_login,
    switch_to_crm_window,
    excelCaseClosingCode,
    todays_excel_path,
    get_todays_cache_path,
)

# Import call closing code dialog from CaseReviewer_v2 (Phase 5 version)
from CaseReviewer_v2 import get_call_closing_code

# CRM URL for navigation
CRM_URL = "https://lenovo-plrs-prod.crm5.dynamics.com/main.aspx?appid=00fd771a-9081-e911-a83a-000d3a07fba2&forceUCI=1&pagetype=dashboard&id=4e76815a-1f63-df11-ae90-00155d2e3002&type=system&_canOverride=true"

# ============================================================================
# RESUME HELPERS - Companies Process
# ============================================================================

def count_remaining_companies(cache_file, sheet_name="Companies"):
    """
    Count how many NEW company cases remain in the cache file.
    Returns (remaining_count, display_message).
    """
    try:
        if not os.path.exists(cache_file):
            return 0, "Cache file not found"

        import pandas as _pd
        df_c = _pd.read_excel(cache_file, sheet_name=sheet_name)

        from SharedFunctions import find_column_case_insensitive as _fci
        status_col = _fci(df_c, 'Status')
        if status_col:
            remaining = len(df_c[
                df_c[status_col].astype(str).str.strip().str.lower() == 'new'
            ])
        else:
            remaining = len(df_c)

        if remaining == 0:
            return 0, "No NEW company cases remain in cache"
        elif remaining == 1:
            return 1, "1 NEW company case remains"
        else:
            return remaining, f"{remaining} NEW company cases remain"
    except Exception as e:
        print(f"[WARN] count_remaining_companies: {e}")
        return 0, "Unable to determine remaining cases"


def check_companies_cache_and_ask(cache_path):
    """
    If a previous companies cache exists, ask the user whether to resume or
    start fresh.  Returns "RESUME" or "NEW".
    """
    if not os.path.exists(cache_path):
        return "NEW"

    remaining, msg = count_remaining_companies(cache_path)

    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    try:
        from ibm_theme import get_qss, IBM, _read_font_size
        _fs = _read_font_size()
        _c  = IBM.LIGHT
        _qss = get_qss('light', _fs)
    except Exception:
        _fs = 13
        _c  = {
            'bg': '#f4f4f4', 'layer_01': '#ffffff', 'layer_02': '#f4f4f4',
            'text_primary': '#161616', 'text_secondary': '#525252',
            'interactive': '#0f62fe', 'interactive_hover': '#0353e9',
            'interactive_active': '#002d9c', 'border_subtle': '#e0e0e0',
            'info_bg': '#edf5ff', 'teal': '#005d5d', 'layer_03': '#e0e0e0',
        }
        _qss = ''

    class CompaniesResumeDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Resume Companies Process?")
            self.setFixedSize(500, 230)
            self.result = "NEW"
            if _qss:
                self.setStyleSheet(_qss)
            self.setFont(QFont('IBM Plex Sans', _fs))

            layout = QVBoxLayout(self)
            layout.setSpacing(16)
            layout.setContentsMargins(24, 20, 24, 20)

            header = QLabel("Existing session found")
            header.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
            header.setStyleSheet(
                f"font-weight: 700; color: {_c['text_primary']};"
                f" background: transparent; border: none;"
            )
            layout.addWidget(header)

            info_frame = QFrame()
            info_frame.setStyleSheet(
                f"background-color: {_c.get('info_bg', '#edf5ff')};"
                f"border-left: 4px solid {_c['interactive']};"
                f"border-top: 1px solid {_c['border_subtle']};"
                f"border-right: 1px solid {_c['border_subtle']};"
                f"border-bottom: 1px solid {_c['border_subtle']};"
                f"border-radius: 0px; padding: 4px;"
            )
            info_lyt = QVBoxLayout(info_frame)
            info_lyt.setContentsMargins(12, 8, 12, 8)
            info_lbl = QLabel(
                f"{msg.capitalize()}\n\nWould you like to resume where you left off?"
            )
            info_lbl.setFont(QFont('IBM Plex Sans', _fs))
            info_lbl.setStyleSheet(
                f"color: {_c['text_primary']}; background: transparent; border: none;"
            )
            info_lbl.setWordWrap(True)
            info_lyt.addWidget(info_lbl)
            layout.addWidget(info_frame)

            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)

            resume_btn = QPushButton("Resume")
            resume_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
            resume_btn.setStyleSheet(
                f"QPushButton {{ background-color: {_c['interactive']}; color: #ffffff;"
                f" font-weight: 600; padding: 12px 28px; border: none; border-radius: 4px;"
                f" font-family: 'IBM Plex Sans','Segoe UI',Arial; font-size: {_fs}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c['interactive_hover']}; }}"
                f"QPushButton:pressed {{ background-color: {_c.get('interactive_active', '#002d9c')}; }}"
            )
            resume_btn.setFocusPolicy(Qt.ClickFocus)
            resume_btn.clicked.connect(self.on_resume)
            btn_layout.addWidget(resume_btn)

            new_btn = QPushButton("Start Fresh")
            new_btn.setFont(QFont('IBM Plex Sans', _fs))
            new_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {_c['interactive']};"
                f" font-weight: 600; padding: 12px 28px;"
                f" border: 2px solid {_c['interactive']}; border-radius: 4px;"
                f" font-family: 'IBM Plex Sans','Segoe UI',Arial; font-size: {_fs}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c.get('layer_02', '#f4f4f4')}; }}"
            )
            new_btn.setFocusPolicy(Qt.ClickFocus)
            new_btn.clicked.connect(self.on_new)
            btn_layout.addWidget(new_btn)

            layout.addLayout(btn_layout)
            self.setLayout(layout)
            
            # Install event filter to block keyboard entries
            self.installEventFilter(self)

        def eventFilter(self, obj, event):
            """Block keyboard entries at dialog level"""
            from PyQt5.QtCore import Qt, QEvent
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Tab, Qt.Key_Backtab):
                    print("[EVENT FILTER] Blocked key in CompaniesResumeDialog: {}".format(key))
                    return True
            return super().eventFilter(obj, event)

        def on_resume(self):
            self.result = "RESUME"
            self.accept()

        def on_new(self):
            self.result = "NEW"
            self.accept()
        
        def keyPressEvent(self, event):
            """
            Override keyPressEvent to prevent accidental button activation.
            Blocks: Enter, Space, Tab, Shift+Tab, Arrow keys
            Allows: Mouse clicks only
            """
            from PyQt5.QtCore import Qt
            key = event.key()
            print("[CompaniesResumeDialog] keyPressEvent called with key: {}".format(key))
            
            # Block keyboard-based selections that might trigger buttons
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, 
                      Qt.Key_Tab, Qt.Key_Backtab,
                      Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                print("[KEYBOARD BLOCKED] Blocked key in CompaniesResumeDialog: {}".format(key))
                event.ignore()
                return
            
            # Allow other keys (unlikely but be safe)
            super().keyPressEvent(event)

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dlg = CompaniesResumeDialog()
    dlg.exec_()
    return dlg.result

def show_per_case_outcomes_dialog(email, cases, batch_index=1, total_batches=1):
    """
    Shows a dialog allowing the user to set individual outcomes for each case in a company batch.

    Args:
        email: Company email address
        cases: List of case dicts with 'case_number', 'serial', 'mtm', 'row_idx'
        batch_index: 1-based index of this batch in the overall company queue
        total_batches: Total number of distinct email groups (batches) to process

    Returns:
        dict: {case_number: outcome} mapping, or None if cancelled
    """
    outcomes = {}
    
    from PyQt5.QtGui import QFont
    from ibm_theme import get_qss, IBM, _read_font_size as _rfs3
    _fs3 = _rfs3()
    _c3 = IBM.LIGHT

    class PerCaseOutcomesDialog(QDialog, SettingsAwareMixin):
        def __init__(self):
            super().__init__()
            self.setup_settings_awareness()
            self.setWindowTitle("Company Call Results")
            self.setMinimumWidth(560)
            self.setMinimumHeight(420)
            self.combos = {}
            self.setWindowModality(Qt.ApplicationModal)
            self.setStyleSheet(get_qss('light', _fs3))
            self.setFont(QFont('IBM Plex Sans', _fs3))

            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(24, 20, 24, 20)
            main_layout.setSpacing(12)


            # Header
            header = QLabel(f"Call Results  —  {email}")
            header.setFont(QFont('IBM Plex Sans', _fs3, QFont.Bold))
            header.setStyleSheet(
                f"font-weight: 700; color: {_c3['teal']}; background: transparent; border: none;"
            )
            main_layout.addWidget(header)
            self.header = header

            subtitle = QLabel(f"Select outcome for each case  ({len(cases)} machines)")
            subtitle.setFont(QFont('IBM Plex Sans', _fs3 - 1))
            subtitle.setStyleSheet(f"color: {_c3['text_secondary']}; background: transparent; border: none;")
            main_layout.addWidget(subtitle)
            
            # Separator
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            main_layout.addWidget(line)
            
            # Scrollable area for cases
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(10)
            
            # Outcome options
            outcome_options = [
                "Issue Resolved",
                "Issue Not Fixed", 
                "Not Yet Tested",
                "Need Follow-up",
                "Customer Not Reached",
                "DND",
                "Left Voicemail"
            ]
            
            # Create row for each case
            for case in cases:
                case_num = case['case_number']
                serial = case.get('serial', '') or case.get('mtm', '') or 'N/A'

                row_widget = QFrame()
                row_widget.setStyleSheet(
                    f"QFrame {{ background-color: {_c3['layer_01']};"
                    f" border: none;"
                    f" border-bottom: 1px solid {_c3['border_subtle']};"
                    f" border-radius: 0px; }}"
                )
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(8, 10, 8, 10)

                info_label = QLabel(f"Case {case_num}  |  {serial}")
                info_label.setFont(QFont('IBM Plex Mono', _fs3 - 1, QFont.Bold))
                info_label.setStyleSheet(
                    f"font-weight: 700; color: {_c3['text_primary']};"
                    f" background: transparent; border: none;"
                )
                info_label.setMinimumWidth(240)
                row_layout.addWidget(info_label)

                combo = QComboBox()
                combo.addItems(outcome_options)
                combo.setCurrentIndex(0)
                combo.setMinimumWidth(200)
                combo.setFont(QFont('IBM Plex Sans', _fs3 - 1))
                # IBM dropdown styled by the global QSS
                row_layout.addWidget(combo)
                
                self.combos[case_num] = combo
                scroll_layout.addWidget(row_widget)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            main_layout.addWidget(scroll)
            
            # Quick-set buttons — clearly styled solid pills
            quick_label = QLabel("Quick-set all outcomes:")
            quick_label.setFont(QFont('IBM Plex Sans', _fs3 - 1))
            quick_label.setStyleSheet(
                f"color: {_c3['text_secondary']}; background: transparent; border: none;"
            )
            main_layout.addWidget(quick_label)

            quick_layout = QHBoxLayout()
            quick_layout.setSpacing(10)

            def _pill(label, color, hover, text_color="#ffffff"):
                from PyQt5.QtCore import Qt
                btn = QPushButton(label)
                btn.setFont(QFont('IBM Plex Sans', _fs3 - 1, QFont.Bold))
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {color}; color: {text_color};"
                    f" border: none; border-radius: 20px;"
                    f" font-family: 'IBM Plex Sans','Segoe UI',Arial; font-size: {_fs3 - 1}pt;"
                    f" font-weight: 600; padding: 8px 18px; min-height: 38px; }}"
                    f"QPushButton:hover {{ background-color: {hover}; }}"
                    f"QPushButton:pressed {{ opacity: 0.85; }}"
                )
                btn.setFocusPolicy(Qt.ClickFocus)
                return btn

            set_all_resolved = _pill(
                "✔  All Resolved",
                _c3.get('success', '#198038'),
                _c3.get('success_hover', '#0e6027')
            )
            set_all_resolved.clicked.connect(lambda: self.set_all("Issue Resolved"))
            quick_layout.addWidget(set_all_resolved)

            set_all_not_reached = _pill(
                "📞  All Not Reached",
                _c3.get('teal', '#005d5d'),
                _c3.get('teal_hover', '#004144')
            )
            set_all_not_reached.clicked.connect(lambda: self.set_all("Customer Not Reached"))
            quick_layout.addWidget(set_all_not_reached)

            set_all_not_fixed = _pill(
                "✖  All Not Fixed",
                _c3.get('danger', '#da1e28'),
                _c3.get('danger_hover', '#a2191f')
            )
            set_all_not_fixed.clicked.connect(lambda: self.set_all("Issue Not Fixed"))
            quick_layout.addWidget(set_all_not_fixed)

            main_layout.addLayout(quick_layout)
            
            # Action buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(12)

            cancel_btn = QPushButton("Cancel")
            cancel_btn.setFont(QFont('IBM Plex Sans', _fs3))
            cancel_btn.setStyleSheet(
                f"QPushButton {{ background-color: transparent; color: {_c3['interactive']};"
                f" font-weight: 600; padding: 10px 24px;"
                f" border: 2px solid {_c3['interactive']}; border-radius: 4px;"
                f" font-size: {_fs3}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c3['layer_02']}; }}"
            )
            cancel_btn.setFocusPolicy(Qt.ClickFocus)
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)

            btn_layout.addStretch()

            apply_btn = QPushButton("Apply Results")
            apply_btn.setFont(QFont('IBM Plex Sans', _fs3, QFont.Bold))
            apply_btn.setStyleSheet(
                f"QPushButton {{ background-color: {_c3['teal']}; color: #ffffff;"
                f" font-weight: 600; padding: 10px 30px;"
                f" border: none; border-radius: 4px;"
                f" font-size: {_fs3}pt; min-height: 44px; }}"
                f"QPushButton:hover {{ background-color: {_c3['teal_hover']}; }}"
            )
            apply_btn.setFocusPolicy(Qt.ClickFocus)
            apply_btn.clicked.connect(self.accept)
            btn_layout.addWidget(apply_btn)

            main_layout.addLayout(btn_layout)
            self.setLayout(main_layout)
            
            # Install event filter to block keyboard entries
            self.installEventFilter(self)
        
        def eventFilter(self, obj, event):
            """Block keyboard entries at dialog level"""
            from PyQt5.QtCore import Qt, QEvent
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Tab, Qt.Key_Backtab):
                    print("[EVENT FILTER] Blocked key in PerCaseOutcomesDialog: {}".format(key))
                    return True
            return super().eventFilter(obj, event)
        
        def set_all(self, outcome):
            """Set all dropdowns to the same outcome"""
            for combo in self.combos.values():
                index = combo.findText(outcome)
                if index >= 0:
                    combo.setCurrentIndex(index)
        
        def get_outcomes(self):
            """Get outcome for each case"""
            return {case_num: combo.currentText() for case_num, combo in self.combos.items()}
        
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

        def on_theme_changed(self, theme: str):
            """Handle theme changes — applies full IBM QSS."""
            from ibm_theme import get_qss, IBM
            self.setStyleSheet(get_qss(theme, _fs3))
            _tc3 = IBM.DARK if theme == 'dark' else IBM.LIGHT
            self.header.setStyleSheet(
                f"font-weight: 700; color: {_tc3['teal']}; background: transparent; border: none;"
            )
        
        def on_font_size_changed(self, scale: float):
            """Handle font size changes."""
            # Import and use the static helper
            from ui.settings_aware_dialog import apply_font_to_widget_and_children
            apply_font_to_widget_and_children(self, scale)
        
        def keyPressEvent(self, event):
            """
            Override keyPressEvent to prevent accidental button/dropdown activation.
            Blocks: Enter, Space, Tab, Shift+Tab, Arrow keys
            Allows: Mouse clicks and dropdown interactions only
            """
            from PyQt5.QtCore import Qt
            key = event.key()
            print("[PerCaseOutcomesDialog] keyPressEvent called with key: {}".format(key))
            
            # Block keyboard-based selections that might trigger buttons or accidentally change combos
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, 
                      Qt.Key_Tab, Qt.Key_Backtab,
                      Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                print("[KEYBOARD BLOCKED] Blocked key in PerCaseOutcomesDialog: {}".format(key))
                event.ignore()
                return
            
            # Allow Escape to close dialog
            if key == Qt.Key_Escape:
                print("[KEYBOARD ALLOWED] Escape key allowed in PerCaseOutcomesDialog")
                super().keyPressEvent(event)
                return
            
            # Block everything else (Ctrl+C, Alt+Tab, etc)
            print("[KEYBOARD BLOCKED] Other key blocked in PerCaseOutcomesDialog: {}".format(key))
            event.ignore()
    
    # Show dialog
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = PerCaseOutcomesDialog()
    result = dialog.exec_()
    
    if result == 1:  # Accepted
        outcomes = dialog.get_outcomes()
        print(f"[INFO] Per-case outcomes selected: {outcomes}")
        return outcomes
    else:
        print(f"[INFO] Per-case outcomes dialog cancelled")
        return None

def run_companies_process(driver, cache_file, agent_name, sheet_name="Companies", font_settings=None):
    """
    Main function to process all company cases grouped by email.
    
    FLOW:
    1. Gather case numbers from cache file
    2. For each case: case_search_and_open_no_edit (without Edit)
    3. Use solution_provided_check_and_skip to check status
    4. Go to first solution provided case
    5. Use original case_search_and_open (with Edit)
    6. Build company email (confirm)
    7. Send email
    8. Perform call
    9. Leave note with closing code on first case
    10. Register on excel sheet
    11. Go to all other cases for same email - leave note (call performed on first case)
    12. Press save on each
    13. Go to next email group
    """
    print("[INFO] === Starting Companies Process ===")
    
    # =========================================================================
    # NOTE: Driver already initialized and logged into Dialer by caller
    # This function uses the existing driver without restart
    # =========================================================================
    if not driver:
        print("[WARN] No driver provided - cannot proceed")
        return
    
    print("[INFO] ✓ Using existing Chrome driver (no restart)")
    
    # =========================================================================
    
    grouped, df_companies = load_companies_for_handler(cache_file, agent_name, sheet_name)
    
    if not grouped:
        print("[INFO] No company cases to process for this handler")
        return
    
    print(f"[INFO] Found {len(grouped)} distinct companies (emails) to process")
    
    today_str = datetime.now().strftime("%b %d, %Y")
    total_groups = len(grouped)
    all_emails = list(grouped.keys())

    for batch_index, (email, data) in enumerate(grouped.items(), start=1):
        cases = data['cases']
        
        print(f"\n[INFO] ========== Processing Company Email: {email} ({len(cases)} cases) ==========")
        
        # ===== Phase 5.2: Show Company Metadata =====
        try:
            from ui.company_metadata_display import CompanyMetadataDialog
            
            # Extract company metadata from first case (now has company_name and state_province)
            first_case_row = cases[0]
            
            # Compute progress figures
            cases_processed_so_far = sum(
                len(grouped[e]['cases']) for e in all_emails[:batch_index - 1]
            )
            total_cases_all = sum(len(grouped[e]['cases']) for e in all_emails)
            cases_left = total_cases_all - cases_processed_so_far
            groups_left = total_groups - batch_index  # groups AFTER this one

            company_metadata = {
                'company_name': first_case_row.get('company_name', 'Unknown Company'),
                'email': email,
                'phone': first_case_row.get('phone', ''),
                'state_province': first_case_row.get('state_province', ''),
                'case_count': len(cases),
                'cases': cases,
                'font_settings': font_settings,
                'batch_index': batch_index,
                'total_groups': total_groups,
                'cases_left': cases_left,
                'groups_left': groups_left,
            }

            # Show metadata dialog
            CompanyMetadataDialog.show_company_info(company_metadata)
            print("[INFO] ✓ Company metadata displayed to user")
        except Exception as e:
            print(f"[WARNING] Could not display company metadata: {e}")
        
        # =====================================================================
        # STEP 1-3: Go through each case and check Solution Provided status
        # =====================================================================
        solution_provided_cases = []
        
        for case in cases:
            case_num = case['case_number']
            idx = case.get('row_idx')
            print(f"\n[INFO] Step 2: Opening case {case_num} (no edit)...")
            
            try:
                # Step 2: Open case WITHOUT pressing Edit
                case_search_and_open_no_edit(driver, case_num)
                time.sleep(2)
                
                # Step 3: Check if solution provided OR closed using new function
                print(f"[INFO] Step 3: Checking Solution Provided / Closed status...")
                is_solution_or_closed = solution_provided_check_and_skip_companies(driver, case_num, df_companies, cache_file)
                
                if is_solution_or_closed:
                    solution_provided_cases.append({
                        'case_number': case_num,
                        'serial': case.get('serial', ''),
                        'mtm': case.get('mtm', ''),
                        'row_idx': case.get('row_idx')
                    })
                else:
                    print(f"[INFO] ✗ Case {case_num}: Neither Solution Provided nor Closed - marking as Skipped")
                    # Mark cases without solution provided as Skipped in Excel
                    if idx is not None:
                        df_companies.at[idx, 'Status'] = 'Skipped'
                        print(f"[INFO] Case {case_num} marked as Skipped in Excel sheet")
                    
            except Exception as e:
                print(f"[WARN] Failed to check case {case_num}: {e}")
                continue
        
        # Save skipped cases to cache immediately
        if not solution_provided_cases:
            with pd.ExcelWriter(cache_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_companies.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # =====================================================================
        # Check if we have any solution provided cases
        # =====================================================================
        if not solution_provided_cases:
            print(f"\n[INFO] No Solution Provided cases found for {email} - skipping company")
            continue
        
        print(f"\n[INFO] Found {len(solution_provided_cases)} Solution Provided cases for email batch")
        
        # =====================================================================
        # STEP 4-5: Go to first solution provided case with Edit
        # =====================================================================
        first_case = solution_provided_cases[0]['case_number']
        
        try:
            print(f"\n[INFO] Step 4-5: Opening first case {first_case} WITH Edit...")
            case_search_and_open(driver, first_case)
            time.sleep(1)
            
            # Check for e-ticketing and skip if needed (after opening with edit)
            print(f"[INFO] Checking for e-ticketing...")
            eticket_check_and_skip(driver, first_case, df_companies, cache_file)
            time.sleep(2)
            
            # =====================================================================
            # STEP 6: Build email and confirm
            # =====================================================================
            print(f"[INFO] Step 6: Building email for confirmation...")
            email_body = build_companies_email_body(solution_provided_cases, agent_name)
            confirmed = show_companies_email_confirmation(email, solution_provided_cases, email_body)
            
            if not confirmed:
                print("[INFO] Email not confirmed - skipping this company")
                continue
            
            # =====================================================================
            # STEP 7: Send email
            # =====================================================================
            print("[INFO] Step 7: Sending companies batch email...")
            send_Email(driver, email_body)
            time.sleep(2)
            
            # =====================================================================
            # STEP 8: Perform call
            # =====================================================================
            print("[INFO] Step 8: Performing call flow...")
            
            # Force Qt event processing before call
            QApplication.processEvents()
            
            call_success = perform_call_flow(driver)
            
            if not call_success:
                print("[WARN] Call flow may have failed - continuing...")
                switch_to_crm_window(driver, max_retries=3)
            
            # Force Qt event processing before showing dialog
            QApplication.processEvents()
            time.sleep(0.5)
            
            # =====================================================================
            # STEP 9: Get PER-CASE outcomes (instead of single outcome)
            # =====================================================================
            print("[INFO] Step 9: Getting outcomes for each case...")
            case_outcomes = show_per_case_outcomes_dialog(email, solution_provided_cases)
            
            if case_outcomes is None:
                print("[INFO] Per-case outcomes cancelled - skipping this company")
                continue
            
            print(f"[INFO] Case outcomes: {case_outcomes}")
            
            # Build note for first case with all outcomes
            serials_str = "\n".join([f"{c['case_number']} | {c['serial'] or c['mtm']}: {case_outcomes.get(c['case_number'], 'N/A')}" for c in solution_provided_cases])
            first_case_note = (
                f"Date: {today_str}\n"
                "Queue: ART Project - Follow up\n"
                f"Agent: {agent_name}\n"
                f"Action: Sent Company Email with devices:\n{serials_str}\n"
                " \n ------------------------"
            )
            
            print(f"[INFO] Leaving note on first case {first_case}...")
            add_Case_Note(driver, first_case_note)
            
            # =====================================================================
            # STEP 10: Update Excel with INDIVIDUAL outcomes per case
            # =====================================================================
            print("[INFO] Step 10: Updating Companies sheet with individual outcomes...")
            
            for case in solution_provided_cases:
                case_num = case['case_number']
                idx = case.get('row_idx')
                outcome = case_outcomes.get(case_num, "Issue Resolved")  # Default if not found
                
                if idx is not None:
                    df_companies.at[idx, 'Action 2'] = 'Sent Email'
                    df_companies.at[idx, 'Action 3'] = 'Called the Customer'
                    df_companies.at[idx, 'Final Action'] = excelCaseClosingCode(outcome)
                    df_companies.at[idx, 'Status'] = 'closed'
                    print(f"[INFO] Case {case_num}: {outcome}")
            
            # Save to cache immediately
            with pd.ExcelWriter(cache_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_companies.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"[INFO] Updated {len(solution_provided_cases)} cases in Companies sheet with individual outcomes")
            
            # =====================================================================
            # STEP 12-13: Go to other cases and leave note that call was on first case
            # =====================================================================
            if len(solution_provided_cases) > 1:
                print(f"\n[INFO] Step 11-12: Leaving notes on other {len(solution_provided_cases)-1} cases...")
                
                for case in solution_provided_cases[1:]:  # Skip first case already processed
                    case_num = case['case_number']
                    print(f"[INFO] Processing case {case_num}...")
                    
                    try:
                        # Open case with Edit
                        case_search_and_open(driver, case_num)
                        time.sleep(2)
                        
                        # Check for e-ticketing and skip if needed (after opening with edit)
                        print(f"[INFO] Checking for e-ticketing...")
                        eticket_check_and_skip(driver, case_num, df_companies, cache_file)
                        time.sleep(2)   
                        
                        # Get this case's individual outcome
                        case_outcome = case_outcomes.get(case_num, "Issue Resolved")
                        
                        # Leave note referencing first case with this case's outcome
                        other_case_note = (
                            f"Date: {today_str}\n"
                            "Queue: ART Project - Follow up\n"
                            f"Agent: {agent_name}\n"
                            f"Action: Company Bulk Email sent and Call performed on Case Number: {first_case}\n"
                            f"Case Outcome: {case_outcome}\n"
                            " \n ------------------------"
                        )
                        
                        add_Case_Note(driver, other_case_note)
                        
                        # Step 13: Press Save
                        print(f"[INFO] Step 13: Saving case {case_num}...")
                        click_safe(
                            driver,
                            By.XPATH,
                            "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckIn.Command') and contains(@id,'-button')]",
                            timeout=2,
                            retries=2
                        )
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"[WARN] Failed to process other case {case_num}: {e}")
                        continue
            
            print(f"\n[INFO] ✓ Completed processing company: {email}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process company {email}: {e}")
            continue
    
    print("\n[INFO] === Companies Process Complete ===")

# ============================================================================
# NEW: Standalone Companies Process Runner (Phase 5.1)
# ============================================================================
def run_companies_process_standalone(support_agent=None):
    """
    Standalone entry point for Company Process mode (isolated execution).
    Can be called directly from Dispatcher without auto-trigger.
    
    Args:
        support_agent: Optional name of agent being supported
    """
    global theme_manager, accessibility_manager, error_logger
    
    print("=" * 60)
    print("       COMPANY PROCESS - Isolated Mode")
    print("=" * 60)
    
    # ===== FIX: Initialize QApplication FIRST to prevent QWidget errors =====
    app = QApplication.instance()
    if app is None:
        print("[INFO] Initializing QApplication...")
        app = QApplication(sys.argv)
    print("[INFO] ✓ QApplication ready")
    
    # ===== PHASE 3.2: Initialize Theme & Accessibility =====
    theme_manager = None
    accessibility_manager = None
    error_logger = None
    font_settings = None  # Cache font settings to prevent garbage collection issues
    
    try:
        from ui.theme_manager import get_theme_manager
        from ui.accessibility_helper import get_accessibility_manager
        from utils.error_logger import get_error_logger
        
        theme_manager = get_theme_manager()
        accessibility_manager = get_accessibility_manager()
        error_logger = get_error_logger("CompaniesProcess")
        
        # Extract font settings immediately to prevent garbage collection issues
        try:
            if theme_manager:
                font_settings = theme_manager.get_font_settings()
                print("[INFO] ✓ Font settings cached")
        except Exception as e:

            font_settings = None
        
        print("[INFO] ✓ Theme Manager initialized (Phase 3.2)")
        print("[INFO] ✓ Accessibility Manager initialized (Phase 3.2)")
        print("[INFO] ✓ Error Logger initialized (Phase 4.3)")
    except Exception as e:
        print(f"[WARNING] Could not initialize theme/accessibility managers: {e}")
        theme_manager = None
        accessibility_manager = None
        error_logger = None
        font_settings = None
    
    # Use support agent name if provided, otherwise agent's own name
    working_agent = support_agent if support_agent else AGENT_NAME
    
    if support_agent:
        print(f"[INFO] Support Mode: Working on {support_agent}'s cases")
    else:
        print(f"[INFO] Agent: {AGENT_NAME}")
    
    print("[INFO] Starting Company Process (isolated)...")
    
    driver = None
    
    try:
        from SharedFunctions import (
            enable_windows_inhibit,
            disable_windows_inhibit,
            perform_dialer_login,
            switch_to_crm_window,
            safe_find,
            get_todays_cache_path,
        )
        import time
        
        # Enable Windows sleep inhibit
        enable_windows_inhibit()
        
        # ===== FIX: Create cache file BEFORE starting Chrome session =====
        # Get AutoSender cache file to load agent's cases (reference)
        autosender_cache_file = get_todays_cache_path(working_agent, mode="autosender")
        
        # Get Companies cache file path (where we'll create Companies data)
        cache_file = get_todays_cache_path(working_agent, mode="companies")
        os.makedirs(CACHE_DIRECTORY, exist_ok=True)
        
        print("[INFO] Creating Companies cache file...")
        # Create Companies cache if it doesn't exist
        if not os.path.exists(cache_file):
            print(f"[INFO] Creating Companies cache file: {cache_file}")
            
            # Load Excel data to get Companies sheet
            from SharedFunctions import (
                todays_excel_path,
                find_column_case_insensitive as find_col,
            )
            
            excel_path = todays_excel_path()
            
            try:
                with pd.ExcelFile(excel_path) as xls:
                    # Find Companies sheet
                    companies_sheet_name = None
                    for sheet in xls.sheet_names:
                        if 'companies' in str(sheet).lower():
                            companies_sheet_name = sheet
                            break
                    
                    if companies_sheet_name:
                        print(f"[INFO] Loading Companies data from '{companies_sheet_name}'")
                        df_companies = pd.read_excel(excel_path, sheet_name=companies_sheet_name)
                        
                        # Filter for handler's cases
                        comp_assigned_col = find_col(df_companies, 'Assigned To')
                        if comp_assigned_col:
                            # Get handler name from agent's first name
                            handler_name = working_agent.split()[0]
                            print(f"[INFO] Filtering Companies for handler: {handler_name}")
                            
                            df_companies_handler = df_companies[
                                df_companies[comp_assigned_col].astype(str).str.strip() == handler_name
                            ].copy()
                            
                            # Filter by Status 'New'
                            status_col = find_col(df_companies_handler, 'Status')
                            if status_col:
                                df_companies_handler = df_companies_handler[
                                    df_companies_handler[status_col].astype(str).str.strip().str.lower() == 'new'
                                ].copy()
                            
                            if len(df_companies_handler) > 0:
                                # Create cache with Companies sheet
                                print(f"[INFO] ✓ Found {len(df_companies_handler)} NEW Companies cases for {handler_name}")
                                with pd.ExcelWriter(cache_file, engine='openpyxl') as writer:
                                    df_companies_handler.to_excel(writer, sheet_name='Companies', index=False)
                                print(f"[INFO] ✓ Companies cache created: {cache_file}")
                            else:
                                print("[INFO] No NEW Companies cases found for this handler")
                                return
                        else:
                            print("[WARN] No 'Assigned To' column found in Companies sheet")
                            return
                    else:
                        print("[INFO] No Companies sheet found in Excel file")
                        print("[INFO] Please ensure Excel file has a 'Companies' sheet")
                        return
            except Exception as e:
                print(f"[ERROR] Failed to create Companies cache: {e}")
                traceback.print_exc()
                return
        else:
            print(f"[INFO] ✓ Companies cache already exists: {cache_file}")
            # ── Resume dialog
            resume_choice = check_companies_cache_and_ask(cache_file)
            if resume_choice == "NEW":
                print("[INFO] User chose to start fresh — deleting old cache")
                try:
                    os.remove(cache_file)
                except Exception as _re:
                    print(f"[WARN] Could not remove old cache: {_re}")
                # Rebuild cache from Excel (re-run the creation branch)
                from SharedFunctions import (
                    todays_excel_path as _tep,
                    find_column_case_insensitive as _fcib,
                )
                _excel = _tep()
                try:
                    with pd.ExcelFile(_excel) as _xls:
                        _comp_sheet = None
                        for _s in _xls.sheet_names:
                            if 'companies' in str(_s).lower():
                                _comp_sheet = _s
                                break
                        if _comp_sheet:
                            _df = pd.read_excel(_excel, sheet_name=_comp_sheet)
                            _ac = _fcib(_df, 'Assigned To')
                            if _ac:
                                _hn = working_agent.split()[0]
                                _df = _df[_df[_ac].astype(str).str.strip() == _hn].copy()
                            _sc = _fcib(_df, 'Status')
                            if _sc:
                                _df = _df[_df[_sc].astype(str).str.strip().str.lower() == 'new'].copy()
                            if len(_df) > 0:
                                with pd.ExcelWriter(cache_file, engine='openpyxl') as _w:
                                    _df.to_excel(_w, sheet_name='Companies', index=False)
                                print(f"[INFO] ✓ Fresh cache created with {len(_df)} cases")
                            else:
                                print("[INFO] No NEW Companies cases found — nothing to do")
                                return
                        else:
                            print("[INFO] No Companies sheet found — cannot rebuild cache")
                            return
                except Exception as _ce:
                    print(f"[ERROR] Could not rebuild Companies cache: {_ce}")
                    traceback.print_exc()
                    return
            else:
                print("[INFO] Resuming previous Companies session")
        
        # ===== Now that cache is ready, initialize Chrome driver =====
        print("[INFO] Initializing Chrome driver...")
        # Initialize Chrome driver
        chrome_options = Chrome_ART_Profile()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Perform Dialer Login
        try:
            perform_dialer_login(driver)
        except Exception as e:
            print(f"[WARN] Dialer login failed or incomplete: {e}")
        
        # Wait for Dialer to open CRM automatically
        print("[INFO] Waiting 3 seconds for Dialer to open CRM...")
        time.sleep(3)
        
        # Switch to CRM window
        if not switch_to_crm_window(driver):
            print("[WARN] Failed to switch to CRM window - please check if it opened")
        
        # Now run companies process with created/existing cache
        print(f"[INFO] Loading Companies cache: {cache_file}")
        try:
            run_companies_process(driver, cache_file, working_agent, "Companies", font_settings=font_settings)
        except Exception as e:
            print(f"[ERROR] Failed to run Companies Process: {e}")
            traceback.print_exc()
        
        print("[INFO] Company Process complete - returning to Dispatcher")
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Company Process failed: {e}")
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

if __name__ == "__main__":
    print("[INFO] CompaniesProcess_v2 module - run via Dispatcher or standalone")
    print("[INFO] Use run_companies_process_standalone() for isolated Company Process mode")

