# ============================================================================
# CompaniesProcess_v2.py - Process Company Cases - MODERNIZED VERSION
# ============================================================================
# Phase 6.8: CompaniesProcess Modernization (FINAL ART Q Control Phase)
# - Integrated V2 foundation systems (ThemeManager, TypographyMixin, SettingsBus)
# - Modernized dialogs with V2 styling
# - Enhanced company selection with modern table widget
# - Improved email template system with preview
# - Keyboard shortcuts support
# - Unified progress tracking
#
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

# Import PyQt5 for dialog
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QScrollArea, QWidget, QFrame, QGridLayout,
    QProgressBar, QShortcut
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QKeySequence

# Import V2 foundation systems (Phase 6.8)
from ui.theme_manager import get_theme_manager, ColorScheme
from ui.typography_mixin import V2TypographyMixin
from ui.services import get_v2_settings_bus, V2ThemeService
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory
from ui.design_system import Colors, Spacing, BorderRadius
from ui.components_v2.dialogs import ProgressDialog, ModernDialog, ConfirmDialog
from ui.components_v2.buttons import PrimaryButton, SecondaryButton

# Phase 6.8: V2 managers (imported lazily after QApplication)
theme_manager = None
accessibility_manager = None
error_logger = None
v2_settings_bus = None
v2_theme_service = None

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
    Count how many companies remain to be processed in the cache file.
    Returns (count, message_string).
    """
    try:
        if not os.path.exists(cache_file):
            return (0, "no cache file found")
        
        df_c = pd.read_excel(cache_file, sheet_name=sheet_name)
        
        # Find Status column
        status_col = find_column_case_insensitive(df_c, 'Status')
        if not status_col:
            remaining = len(df_c)
        else:
            # Count rows where Status is NOT 'Closed' or 'Skipped'
            remaining = len(df_c[
                ~df_c[status_col].astype(str).str.strip().str.lower().isin(['closed', 'skipped'])
            ])
        
        if remaining == 0:
            msg = "all companies have been processed"
        elif remaining == 1:
            msg = "1 company remaining"
        else:
            msg = f"{remaining} companies remaining"
        
        return (remaining, msg)
    
    except Exception as e:
        print(f"[WARN] Could not count remaining companies: {e}")
        return (0, "error reading cache")


def check_companies_cache_and_ask(cache_path):
    """
    If a previous companies cache exists, ask the user whether to resume or
    start fresh.  Returns "RESUME" or "NEW".
    
    Phase 6.8: Modernized with V2 components and theme manager.
    """
    if not os.path.exists(cache_path):
        return "NEW"

    remaining, msg = count_remaining_companies(cache_path)

    class CompaniesResumeDialog(QDialog, V2TypographyMixin):
        """Modernized resume dialog with V2 styling."""
        
        def __init__(self):
            QDialog.__init__(self)
            V2TypographyMixin.__init__(self)
            
            self.setWindowTitle("Resume Companies Process?")
            self.setMinimumSize(500, 250)
            self.user_choice = "NEW"
            
            # Initialize V2 systems
            self._theme_manager = get_theme_manager()
            self._settings_bus = get_v2_settings_bus()
            self._theme_service = V2ThemeService()
            
            # Subscribe to theme changes
            self._settings_bus.theme_changed.connect(self._on_theme_changed)
            self._settings_bus.font_size_changed.connect(self._on_font_changed)
            
            self._setup_ui(msg)
            self._apply_theme()
            
            # Install event filter to block keyboard entries
            self.installEventFilter(self)
        
        def _setup_ui(self, message):
            """Setup the dialog UI."""
            layout = QVBoxLayout()
            layout.setSpacing(Spacing.MD)
            layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
            
            # Header
            header = QLabel("Existing session found")
            header.setFont(self.get_font('h2', QFont.Bold))
            layout.addWidget(header)
            
            # Info frame with message
            info_frame = QFrame()
            info_frame.setFrameShape(QFrame.StyledPanel)
            info_layout = QVBoxLayout(info_frame)
            info_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
            
            info_label = QLabel(f"{message.capitalize()}\n\nWould you like to resume where you left off?")
            info_label.setFont(self.get_font('body'))
            info_label.setWordWrap(True)
            info_layout.addWidget(info_label)
            
            layout.addWidget(info_frame)
            
            # Button layout
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(Spacing.SM)
            
            # Resume button (primary)
            resume_btn = PrimaryButton("Resume")
            resume_btn.clicked.connect(self._on_resume)
            btn_layout.addWidget(resume_btn)
            
            # Start fresh button (secondary)
            new_btn = SecondaryButton("Start Fresh")
            new_btn.clicked.connect(self._on_new)
            btn_layout.addWidget(new_btn)
            
            layout.addLayout(btn_layout)
            self.setLayout(layout)
        
        def _apply_theme(self):
            """Apply current theme to dialog."""
            theme_mode = self._settings_bus.theme
            colors = self._theme_service.colors_for(theme_mode)
            
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['window_bg']};
                    color: {colors['text_primary']};
                }}
                QFrame {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['surface_border']};
                    border-radius: {BorderRadius.MD}px;
                }}
                QLabel {{
                    color: {colors['text_primary']};
                    background: transparent;
                    border: none;
                }}
            """)
        
        def _on_theme_changed(self, theme_mode):
            """Handle theme change."""
            self._apply_theme()
        
        def _on_font_changed(self, font_size):
            """Handle font size change."""
            self.apply_typography()
            self._apply_theme()  # Reapply to refresh font-dependent styles
        
        def eventFilter(self, obj, event):
            """Block keyboard entries at dialog level."""
            if event.type() == QEvent.KeyPress:
                key = event.key()
                if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, Qt.Key_Tab, Qt.Key_Backtab):
                    print(f"[EVENT FILTER] Blocked key in CompaniesResumeDialog: {key}")
                    return True
            return super().eventFilter(obj, event)
        
        def _on_resume(self):
            """Handle resume button click."""
            self.user_choice = "RESUME"
            self.accept()
        
        def _on_new(self):
            """Handle start fresh button click."""
            self.user_choice = "NEW"
            self.accept()
        
        def keyPressEvent(self, event):
            """
            Override keyPressEvent to prevent accidental button activation.
            Blocks: Enter, Space, Tab, Shift+Tab, Arrow keys
            Allows: Mouse clicks only
            """
            key = event.key()
            print(f"[CompaniesResumeDialog] keyPressEvent called with key: {key}")
            
            # Block keyboard-based selections that might trigger buttons
            if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space, 
                      Qt.Key_Tab, Qt.Key_Backtab,
                      Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
                print(f"[KEYBOARD BLOCKED] Blocked key in CompaniesResumeDialog: {key}")
                event.ignore()
                return
            
            # Allow other keys (unlikely but be safe)
            super().keyPressEvent(event)
        
        def closeEvent(self, event):
            """Cleanup on close."""
            self._settings_bus.theme_changed.disconnect(self._on_theme_changed)
            self._settings_bus.font_size_changed.disconnect(self._on_font_changed)
            super().closeEvent(event)

    # Ensure QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dlg = CompaniesResumeDialog()
    dlg.exec_()
    return dlg.user_choice

def show_per_case_outcomes_dialog(email, cases, batch_index=1, total_batches=1):
    """
    Shows a dialog allowing the user to set individual outcomes for each case in a company batch.
    
    Phase 6.8: Modernized with V2 styling and components.
    
    Args:
        email: Company email address
        cases: List of case dictionaries with case_number, serial, mtm
        batch_index: Current batch number (1-based)
        total_batches: Total number of batches
    
    Returns:
        dict: Mapping of case_number -> outcome string, or None if cancelled
    """
    # Outcome options
    outcomes = [
        "Resolved",
        "Not Reached",
        "Not Fixed",
        "Not yet tested",
        "Voicemail",
        "Wrong Number",
        "DND"
    ]
    
    class PerCaseOutcomesDialog(QDialog, V2TypographyMixin):
        """Modernized per-case outcomes dialog with V2 styling."""
        
        def __init__(self):
            QDialog.__init__(self)
            V2TypographyMixin.__init__(self)
            
            self.setWindowTitle(f"Case Outcomes - {email}")
            self.setMinimumSize(700, 500)
            self.setWindowModality(Qt.ApplicationModal)
            
            # Initialize V2 systems
            self._theme_manager = get_theme_manager()
            self._settings_bus = get_v2_settings_bus()
            self._theme_service = V2ThemeService()
            
            # Subscribe to theme changes
            self._settings_bus.theme_changed.connect(self._on_theme_changed)
            self._settings_bus.font_size_changed.connect(self._on_font_changed)
            
            # Store combo boxes for later access
            self.combos = {}
            
            self._setup_ui()
            self._apply_theme()
        
        def _setup_ui(self):
            """Setup the dialog UI."""
            main_layout = QVBoxLayout()
            main_layout.setSpacing(Spacing.MD)
            main_layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
            
            # Header
            header = QLabel(f"Set Outcome for Each Case")
            header.setFont(self.get_font('h2', QFont.Bold))
            main_layout.addWidget(header)
            
            # Subtitle with batch info
            subtitle = QLabel(f"Company: {email} | Batch {batch_index} of {total_batches} | {len(cases)} cases")
            subtitle.setFont(self.get_font('body'))
            main_layout.addWidget(subtitle)
            
            # Divider line
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            main_layout.addWidget(line)
            
            # Scroll area for cases
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(Spacing.SM)
            
            # Create row for each case
            for case in cases:
                case_num = case['case_number']
                serial = case.get('serial', '')
                
                row_widget = QFrame()
                row_widget.setFrameShape(QFrame.StyledPanel)
                row_widget.setMinimumHeight(60)
                
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
                
                # Case info label
                info_label = QLabel(f"Case: {case_num}\nSerial: {serial}")
                info_label.setFont(self.get_font('body'))
                info_label.setMinimumWidth(250)
                row_layout.addWidget(info_label)
                
                # Outcome combo box
                combo = QComboBox()
                combo.addItems(outcomes)
                combo.setFont(self.get_font('body'))
                combo.setMinimumWidth(200)
                row_layout.addWidget(combo)
                
                scroll_layout.addWidget(row_widget)
                self.combos[case_num] = combo
            
            scroll.setWidget(scroll_widget)
            main_layout.addWidget(scroll)
            
            # Quick action buttons
            quick_label = QLabel("Quick Actions:")
            quick_label.setFont(self.get_font('caption', QFont.Bold))
            main_layout.addWidget(quick_label)
            
            quick_layout = QHBoxLayout()
            quick_layout.setSpacing(Spacing.SM)
            
            # Quick action buttons
            set_all_resolved = QPushButton("Set All: Resolved")
            set_all_resolved.setFont(self.get_font('button'))
            set_all_resolved.clicked.connect(lambda: self.set_all("Resolved"))
            quick_layout.addWidget(set_all_resolved)
            
            set_all_not_reached = QPushButton("Set All: Not Reached")
            set_all_not_reached.setFont(self.get_font('button'))
            set_all_not_reached.clicked.connect(lambda: self.set_all("Not Reached"))
            quick_layout.addWidget(set_all_not_reached)
            
            set_all_not_fixed = QPushButton("Set All: Not Fixed")
            set_all_not_fixed.setFont(self.get_font('button'))
            set_all_not_fixed.clicked.connect(lambda: self.set_all("Not Fixed"))
            quick_layout.addWidget(set_all_not_fixed)
            
            main_layout.addLayout(quick_layout)
            
            # Action buttons
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(Spacing.SM)
            
            cancel_btn = SecondaryButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
            
            apply_btn = PrimaryButton("Apply Outcomes")
            apply_btn.clicked.connect(self.accept)
            btn_layout.addWidget(apply_btn)
            
            main_layout.addLayout(btn_layout)
            self.setLayout(main_layout)
        
        def set_all(self, outcome):
            """Set all combo boxes to the same outcome."""
            for combo in self.combos.values():
                index = combo.findText(outcome)
                if index >= 0:
                    combo.setCurrentIndex(index)
        
        def get_outcomes(self):
            """Get the selected outcomes as a dictionary."""
            return {case_num: combo.currentText() for case_num, combo in self.combos.items()}
        
        def _apply_theme(self):
            """Apply current theme to dialog."""
            theme_mode = self._settings_bus.theme
            colors = self._theme_service.colors_for(theme_mode)
            
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['window_bg']};
                    color: {colors['text_primary']};
                }}
                QFrame {{
                    background-color: {colors['surface']};
                    border: 1px solid {colors['surface_border']};
                    border-radius: {BorderRadius.SM}px;
                }}
                QLabel {{
                    color: {colors['text_primary']};
                    background: transparent;
                    border: none;
                }}
                QComboBox {{
                    background-color: {colors['surface']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['surface_border']};
                    border-radius: {BorderRadius.SM}px;
                    padding: 8px 12px;
                    min-height: 40px;
                }}
                QComboBox:hover {{
                    border-color: {colors['accent']};
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 32px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {colors['surface']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['surface_border']};
                    selection-background-color: {colors['accent']};
                    selection-color: {colors['window_bg']};
                }}
                QPushButton {{
                    background-color: {colors['surface']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['surface_border']};
                    border-radius: {BorderRadius.SM}px;
                    padding: 8px 16px;
                    min-height: 36px;
                }}
                QPushButton:hover {{
                    background-color: {colors['surface_alt']};
                    border-color: {colors['accent']};
                }}
                QScrollArea {{
                    border: none;
                    background: transparent;
                }}
            """)
        
        def _on_theme_changed(self, theme_mode):
            """Handle theme change."""
            self._apply_theme()
        
        def _on_font_changed(self, font_size):
            """Handle font size change."""
            self.apply_typography()
            self._apply_theme()  # Reapply to refresh font-dependent styles
        
        def closeEvent(self, event):
            """Cleanup on close."""
            self._settings_bus.theme_changed.disconnect(self._on_theme_changed)
            self._settings_bus.font_size_changed.disconnect(self._on_font_changed)
            super().closeEvent(event)
    
    # Ensure QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = PerCaseOutcomesDialog()
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        return dialog.get_outcomes()
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

    total_cases_all = sum(len(grouped[e]['cases']) for e in all_emails)

    for batch_index, (email, data) in enumerate(grouped.items(), start=1):
        cases = data['cases']
        
        print(f"\n[INFO] ========== Processing Company Email: {email} ({len(cases)} cases) ==========")
        print(f"[INFO] Batch progress: {batch_index}/{total_groups}")
        
        # Compute progress figures for current batch
        cases_processed_so_far = sum(
            len(grouped[e]['cases']) for e in all_emails[:batch_index - 1]
        )
        cases_left_before_batch = total_cases_all - cases_processed_so_far
        cases_left_after_batch = total_cases_all - (cases_processed_so_far + len(cases))
        groups_left = total_groups - batch_index  # groups AFTER this one
        
        # ===== Phase 5.2: Show Company Metadata =====
        try:
            from ui.company_metadata_display import CompanyMetadataDialog
            
            # Extract company metadata from first case (now has company_name and state_province)
            first_case_row = cases[0]

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
                'cases_left': cases_left_before_batch,
                'groups_left': groups_left,
            }

            # Create a fresh dialog instance per batch so UI content always reflects current case data
            metadata_confirmed = CompanyMetadataDialog.show_company_info(company_metadata)
            if not metadata_confirmed:
                print(f"[INFO] Company metadata dialog cancelled for {email} - skipping company")
                continue
            print(f"[INFO] ✓ Company metadata displayed for {email}")
        except Exception as e:
            print(f"[WARNING] Could not display company metadata for {email}: {e}")
        
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
                is_solution_or_closed, crm_status = solution_provided_check_and_skip_companies(
                    driver, case_num, df_companies, cache_file
                )

                if is_solution_or_closed:
                    solution_provided_cases.append({
                        'case_number': case_num,
                        'serial': case.get('serial', ''),
                        'mtm': case.get('mtm', ''),
                        'row_idx': case.get('row_idx'),
                        'crm_status': crm_status,   # "closed" or "solution provided"
                    })
                else:
                    print(f"[INFO] ✗ Case {case_num}: Neither Solution Provided nor Closed - marking as Skipped")
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
        first_case_crm_status = solution_provided_cases[0].get('crm_status', '')

        try:
            if first_case_crm_status == "closed":
                # Closed case: open WITHOUT Edit, skip e-ticket check entirely
                print(f"\n[INFO] Step 4-5: First case {first_case} is Closed — opening WITHOUT Edit, skipping e-ticket check")
                case_search_and_open_no_edit(driver, first_case)
            else:
                # Solution Provided: open WITH Edit, run e-ticket check as normal
                print(f"\n[INFO] Step 4-5: Opening first case {first_case} WITH Edit...")
                case_search_and_open(driver, first_case)
                time.sleep(1)
                print(f"[INFO] Checking for e-ticketing...")
                eticket_check_and_skip(driver, first_case, df_companies, cache_file)
            time.sleep(2)
            
            # =====================================================================
            # STEP 6: Build email and confirm
            # =====================================================================
            print(f"[INFO] Step 6: Building email for confirmation...")
            email_body = build_companies_email_body(solution_provided_cases, agent_name)
            print(f"[INFO] Showing email confirmation for {email} with {len(solution_provided_cases)} cases")
            confirmed = show_companies_email_confirmation(
                email,
                solution_provided_cases,
                email_body,
                cases_left=cases_left_after_batch,
                email_groups_left=groups_left
            )
            
            if not confirmed:
                print(f"[INFO] Email confirmation cancelled for {email} - skipping this company")
                continue
            
            print(f"[INFO] ✓ Email confirmed for {email}")
            
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
            case_outcomes = show_per_case_outcomes_dialog(email, solution_provided_cases, batch_index, total_groups)
            
            if case_outcomes is None:
                print("[INFO] Per-case outcomes cancelled - skipping this company")
                continue
            
            print(f"[INFO] ✓ Received outcomes for {len(case_outcomes)} cases")
            
            # =====================================================================
            # STEP 10: Leave note on first case with all outcomes summary (reference flow)
            # =====================================================================
            serials_str = "\n".join([
                f"{c['case_number']} | {c.get('serial') or c.get('mtm') or 'N/A'}: {case_outcomes.get(c['case_number'], 'N/A')}"
                for c in solution_provided_cases
            ])
            first_case_note = (
                f"Date: {today_str}\n"
                "Queue: ART Project - Follow up\n"
                f"Agent: {agent_name}\n"
                f"Action: Sent Company Email with devices:\n{serials_str}\n"
                " \n ------------------------"
            )
            
            print(f"[INFO] Step 10: Leaving note on first case {first_case}...")
            add_Case_Note(driver, first_case_note)
            print(f"[INFO] ✓ Note added to first case {first_case}")
            time.sleep(1)

            # Save the first case record only if Edit was opened (Solution Provided path)
            if first_case_crm_status != "closed":
                print(f"[INFO] Step 10a: Saving first case {first_case} (Edit was opened)...")
                click_safe(
                    driver,
                    By.XPATH,
                    "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckIn.Command') and contains(@id,'-button')]",
                    timeout=2,
                    retries=2
                )
                time.sleep(2)
            else:
                print(f"[INFO] Step 10a: First case {first_case} is Closed — skipping Save (no Edit was opened)")

            # Mark first case as Closed in cache
            for case in solution_provided_cases:
                if case['case_number'] == first_case:
                    idx = case.get('row_idx')
                    if idx is not None:
                        df_companies.at[idx, 'Status'] = 'Closed'
                        print(f"[INFO] ✓ First case {first_case} marked as Closed")
                    break
            
            # =====================================================================
            # STEP 11: Update Companies sheet with INDIVIDUAL outcomes (reference flow)
            # =====================================================================
            print("[INFO] Step 11: Updating Companies sheet with individual outcomes...")
            
            for case in solution_provided_cases:
                case_num = case['case_number']
                idx = case.get('row_idx')
                outcome = case_outcomes.get(case_num, "Resolved")  # Default to dialog format
                
                if idx is not None:
                    df_companies.at[idx, 'Action 2'] = 'Sent Email'
                    df_companies.at[idx, 'Action 3'] = 'Called the Customer'
                    df_companies.at[idx, 'Final Action'] = excelCaseClosingCode(outcome)
                    df_companies.at[idx, 'Status'] = 'closed'
                    print(f"[INFO] Case {case_num}: {outcome} -> {excelCaseClosingCode(outcome)}")
            
            # Save to cache immediately after the reference-style sheet update
            update_cache_file(cache_file, df_companies, sheet_name)
            print(f"[INFO] Updated {len(solution_provided_cases)} cases in Companies sheet with individual outcomes")
            
            # =====================================================================
            # STEP 12-13: Go to other cases and leave note that call was on first case
            # =====================================================================
            for case_position, case in enumerate(solution_provided_cases[1:], start=2):
                case_num = case['case_number']
                outcome = case_outcomes.get(case_num, "Issue Resolved")
                
                print(f"\n[INFO] Step 12: Processing case {case_num} ({case_position}/{len(solution_provided_cases)})...")
                
                try:
                    sub_crm_status = case.get('crm_status', '')

                    if sub_crm_status == "closed":
                        # Closed case: open WITHOUT Edit, skip e-ticket check and Save
                        print(f"[INFO] Case {case_num} is Closed — opening WITHOUT Edit, skipping e-ticket check & Save")
                        case_search_and_open_no_edit(driver, case_num)
                        time.sleep(2)
                    else:
                        # Solution Provided: open WITH Edit, run e-ticket check as normal
                        print(f"[INFO] Opening case {case_num} WITH Edit...")
                        case_search_and_open(driver, case_num)
                        time.sleep(2)
                        print(f"[INFO] Checking for e-ticketing on case {case_num}...")
                        eticket_check_and_skip(driver, case_num, df_companies, cache_file)
                        time.sleep(2)

                    # Leave note referencing first case with this case's outcome
                    # (runs for both Closed and Solution Provided)
                    other_case_note = (
                        f"Date: {today_str}\n"
                        "Queue: ART Project - Follow up\n"
                        f"Agent: {agent_name}\n"
                        f"Action: Company Bulk Email sent and Call performed on Case Number: {first_case}\n"
                        f"Case Outcome: {outcome}\n"
                        " \n ------------------------"
                    )
                    print(f"[INFO] Adding follow-up note to case {case_num}...")
                    add_Case_Note(driver, other_case_note)
                    time.sleep(1)

                    if sub_crm_status != "closed":
                        # Solution Provided: press Save (Edit was opened, must save)
                        print(f"[INFO] Step 13: Saving case {case_num}...")
                        click_safe(
                            driver,
                            By.XPATH,
                            "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckIn.Command') and contains(@id,'-button')]",
                            timeout=2,
                            retries=2
                        )
                        time.sleep(2)
                    else:
                        print(f"[INFO] Case {case_num}: Closed — skipping Save (no Edit was opened)")

                    # Mark as Closed in cache (both paths)
                    idx = case.get('row_idx')
                    if idx is not None:
                        df_companies.at[idx, 'Status'] = 'Closed'
                        print(f"[INFO] ✓ Case {case_num} marked as Closed")
                    
                except Exception as e:
                    print(f"[WARN] Failed to process case {case_num}: {e}")
                    traceback.print_exc()
                    idx = case.get('row_idx')
                    if idx is not None and 'Status' in df_companies.columns:
                        current_status = str(df_companies.at[idx, 'Status']).strip()
                        if not current_status:
                            df_companies.at[idx, 'Status'] = 'New'
                    continue
            
            # Save progress to cache after all note/closing operations for the company
            update_cache_file(cache_file, df_companies, sheet_name)
            print(f"[INFO] ✓ Cache updated after processing company {email}")
            print(f"[INFO] ✓ Completed processing company {email}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process company {email}: {e}")
            traceback.print_exc()
            continue
    
    print("\n[INFO] === Companies Process Complete ===")


# ============================================================================
# COMPLETION DIALOG
# ============================================================================

def show_companies_completion_dialog():
    """Show a UI completion dialog so the user can close with a button instead of pressing Enter in the terminal."""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Companies Process Complete")
        msg.setText("✓  All company cases have been processed.")
        msg.setInformativeText("Click Close to exit and close the browser.")
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Close)
        msg.setDefaultButton(QMessageBox.Close)
        msg.exec_()
    except Exception as e:
        print(f"[WARN] Could not show completion dialog: {e}")


def run_companies_process_standalone(support_agents=None, support_agent=None):
    """
    Standalone entry point for Company Process mode (isolated execution).
    Can be called directly from Dispatcher without auto-trigger.

    Phase 6.8: Modernized with V2 foundation systems.

    Args:
        support_agents: List of agent names being supported (DEV MODE: multiple).
                        Cases are pulled from each agent's Companies sheet in turn.
                        Signatures / notes always use the config AGENT_NAME.
        support_agent:  Legacy single-name parameter (backward compat).
    """
    # Normalise
    if support_agents is None:
        support_agents = [support_agent] if support_agent else []
    global theme_manager, accessibility_manager, error_logger, v2_settings_bus, v2_theme_service
    
    print("=" * 60)
    print("       COMPANY PROCESS - Isolated Mode")
    print("=" * 60)
    
    # ===== FIX: Initialize QApplication FIRST to prevent QWidget errors =====
    app = QApplication.instance()
    if app is None:
        print("[INFO] Initializing QApplication...")
        app = QApplication(sys.argv)
    print("[INFO] ✓ QApplication ready")
    
    # ===== PHASE 6.8: Initialize V2 Foundation Systems =====
    theme_manager = None
    accessibility_manager = None
    error_logger = None
    v2_settings_bus = None
    v2_theme_service = None
    font_settings = None  # Cache font settings to prevent garbage collection issues
    
    try:
        from ui.theme_manager import get_theme_manager
        from ui.accessibility_helper import get_accessibility_manager
        from utils.error_logger import get_error_logger
        from ui.services import get_v2_settings_bus, V2ThemeService
        
        theme_manager = get_theme_manager()
        accessibility_manager = get_accessibility_manager()
        error_logger = get_error_logger("CompaniesProcess")
        v2_settings_bus = get_v2_settings_bus()
        v2_theme_service = V2ThemeService()
        
        # Extract font settings immediately to prevent garbage collection issues
        try:
            if v2_settings_bus:
                font_settings = {'font_size': v2_settings_bus.font_size}
                print("[INFO] ✓ Font settings cached")
        except Exception as e:
            font_settings = None
        
        print("[INFO] ✓ V2 Foundation Systems initialized (Phase 6.8)")
        print("[INFO] ✓ Theme Manager initialized")
        print("[INFO] ✓ Accessibility Manager initialized")
        print("[INFO] ✓ Error Logger initialized")
    except Exception as e:
        print(f"[WARNING] Could not initialize V2 systems: {e}")
        theme_manager = None
        accessibility_manager = None
        error_logger = None
        v2_settings_bus = None
        v2_theme_service = None
        font_settings = None
    
    # Build the list of agents to process.
    # NOTE: Signatures / notes always use AGENT_NAME from config — never overridden.
    if support_agents:
        agents_to_process = support_agents          # e.g. ['Adam', 'Ehab', 'Ibrahim', …]
        print(f"[INFO] Support Mode: Working on agents: {', '.join(agents_to_process)}")
        if len(agents_to_process) > 1:
            print(f"[INFO] DEV MODE: will process {len(agents_to_process)} agents in sequence")
    else:
        # Own-agent mode: derive handler name from own sheet name (e.g. "Ehab's Cases" → "Ehab")
        own_handler = EXCEL_SHEET_NAME.replace("'s Cases", "").replace("'s cases", "").strip()
        if not own_handler:
            own_handler = AGENT_NAME.split()[0]
        agents_to_process = [own_handler]
        print(f"[INFO] Agent: {AGENT_NAME}  (handler key: {own_handler})")

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
            todays_excel_path,
            show_file_search_popup,
            find_column_case_insensitive as find_col,
        )
        import time

        # Enable Windows sleep inhibit
        enable_windows_inhibit()

        # ── Resolve the Excel file once (shared across all agents) ────────
        excel_path = todays_excel_path()
        print(f"[INFO] Using Excel file: {excel_path}")
        if not os.path.exists(excel_path):
            print("[INFO] Excel file not found. Showing search popup...")
            action, path = show_file_search_popup(excel_path, retry_interval_seconds=10)
            if action == "ABORT":
                print("[INFO] User aborted. Exiting Companies Process.")
                return
            elif action in ("MANUAL", "FOUND"):
                excel_path = path
                print(f"[INFO] Using file: {excel_path}")

        # ── Read the Companies sheet from Excel once ───────────────────────
        try:
            with pd.ExcelFile(excel_path) as xls:
                companies_sheet_name = next(
                    (s for s in xls.sheet_names if 'companies' in str(s).lower()), None
                )
            if not companies_sheet_name:
                print("[INFO] No Companies sheet found in Excel file")
                print("[INFO] Please ensure Excel file has a 'Companies' sheet")
                return
            print(f"[INFO] Loading Companies data from '{companies_sheet_name}'")
            df_companies_all = pd.read_excel(excel_path, sheet_name=companies_sheet_name)
        except Exception as e:
            print(f"[ERROR] Failed to load Companies data: {e}")
            traceback.print_exc()
            return

        comp_assigned_col = find_col(df_companies_all, 'Assigned To')
        if not comp_assigned_col:
            print("[WARN] No 'Assigned To' column found in Companies sheet")
            return

        # ── Build per-agent cache files ────────────────────────────────────
        # Maps  agent_name → cache_file_path  for agents that have ≥1 NEW case.
        os.makedirs(CACHE_DIRECTORY, exist_ok=True)
        agent_cache_map: dict = {}   # {agent_name: cache_file_path}

        for agent_name in agents_to_process:
            cache_file = get_todays_cache_path(agent_name, mode="companies")
            resume_choice = check_companies_cache_and_ask(cache_file)

            if resume_choice == "RESUME":
                print(f"[INFO] [{agent_name}] Resuming from existing cache: {cache_file}")
                agent_cache_map[agent_name] = cache_file
            else:
                print(f"[INFO] [{agent_name}] Creating fresh cache from Excel…")
                # Filter Companies sheet for this agent
                df_agent = df_companies_all[
                    df_companies_all[comp_assigned_col].astype(str).str.strip() == agent_name
                ].copy()

                # Keep only NEW cases
                status_col = find_col(df_agent, 'Status')
                if status_col:
                    df_agent = df_agent[
                        df_agent[status_col].astype(str).str.strip().str.lower() == 'new'
                    ].copy()

                if len(df_agent) == 0:
                    print(f"[INFO] [{agent_name}] No NEW Companies cases — skipping")
                    continue

                print(f"[INFO] [{agent_name}] ✓ Found {len(df_agent)} NEW Companies cases")
                with pd.ExcelWriter(cache_file, engine='openpyxl', mode='w') as writer:
                    df_agent.to_excel(writer, sheet_name='Companies', index=False)
                print(f"[INFO] [{agent_name}] ✓ Cache created: {cache_file}")
                agent_cache_map[agent_name] = cache_file

        if not agent_cache_map:
            print("[INFO] No NEW Companies cases found for any agent. Exiting.")
            return

        # ===== Initialize Chrome driver (once for all agents) =====
        print("[INFO] Initializing Chrome driver...")
        chrome_options = Chrome_ART_Profile()
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()
        print("[INFO] ✓ Chrome driver initialized")

        # ===== Perform dialer login =====
        print("[INFO] Logging into dialer...")
        perform_dialer_login(driver)
        time.sleep(3)
        print("[INFO] ✓ Dialer login complete")

        # ===== Navigate to CRM =====
        print("[INFO] Navigating to CRM...")
        driver.get(CRM_URL)
        time.sleep(5)
        switch_to_crm_window(driver)
        print("[INFO] ✓ CRM ready")

        # ===== Process each agent in sequence =====
        total_agents = len(agent_cache_map)
        for idx, (agent_name, cache_file) in enumerate(agent_cache_map.items(), start=1):
            print(f"\n[INFO] ── Agent {idx}/{total_agents}: {agent_name} ──")
            run_companies_process(
                driver, cache_file, agent_name,
                sheet_name="Companies", font_settings=font_settings
            )
            print(f"[INFO] ✓ Done: {agent_name}")

        print("\n[INFO] === Companies Process Complete ===")
        show_companies_completion_dialog()

    except KeyboardInterrupt:
        print("\n[INFO] Process interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] Fatal error in Companies Process: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        if driver:
            try:
                driver.quit()
                print("[INFO] ✓ Browser closed")
            except Exception:
                pass
        
        try:
            disable_windows_inhibit()
            print("[INFO] ✓ Windows sleep inhibit disabled")
        except Exception:
            pass


if __name__ == "__main__":
    run_companies_process_standalone()

# Made with Bob
