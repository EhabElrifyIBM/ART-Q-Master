# ============================================================================
# CompaniesProcess.py - Process Company Cases
# ============================================================================
# This module handles processing of company cases grouped by email.
# Called automatically after AutoSender completes NEW cases processing.
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

# Import PyQt5 for dialog
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QScrollArea, QWidget, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt

# Import shared functions
from SharedFunctions import (
    AGENT_NAME,
    CACHE_DIRECTORY,
    EXCEL_SHEET_NAME,
    find_column_case_insensitive,
    case_search_and_open,
    case_search_and_open_no_edit,
    solution_provided_check_and_skip,
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
)

# Import call closing code dialog from CaseReviewer
from CaseReviewer import get_call_closing_code

# CRM URL for navigation
CRM_URL = "https://lenovo-plrs-prod.crm5.dynamics.com/main.aspx?appid=00fd771a-9081-e911-a83a-000d3a07fba2&forceUCI=1&pagetype=dashboard&id=4e76815a-1f63-df11-ae90-00155d2e3002&type=system&_canOverride=true"


def show_per_case_outcomes_dialog(email, cases):
    """
    Shows a dialog allowing the user to set individual outcomes for each case in a company batch.
    
    Args:
        email: Company email address
        cases: List of case dicts with 'case_number', 'serial', 'mtm', 'row_idx'
    
    Returns:
        dict: {case_number: outcome} mapping, or None if cancelled
        Example: {2028926072: 'Issue Resolved', 2028926073: 'Issue Not Fixed'}
    """
    outcomes = {}
    
    class PerCaseOutcomesDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Company Call Results")
            self.setMinimumWidth(550)
            self.setMinimumHeight(400)
            self.combos = {}
            
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(15, 15, 15, 15)
            main_layout.setSpacing(12)
            
            # Header
            header = QLabel(f"📞 Call Results for: {email}")
            header.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
            main_layout.addWidget(header)
            
            subtitle = QLabel(f"Select outcome for each case ({len(cases)} machines)")
            subtitle.setStyleSheet("font-size: 15px; color: #666;")
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
                
                row_widget = QWidget()
                row_layout = QHBoxLayout(row_widget)
                row_layout.setContentsMargins(5, 5, 5, 5)
                
                # Case info
                info_label = QLabel(f"Case {case_num}  |  {serial}")
                info_label.setStyleSheet("font-size: 15px; font-weight: bold;")
                info_label.setMinimumWidth(250)
                row_layout.addWidget(info_label)
                
                # Outcome dropdown
                combo = QComboBox()
                combo.addItems(outcome_options)
                combo.setCurrentIndex(0)  # Default to "Issue Resolved"
                combo.setMinimumWidth(180)
                combo.setStyleSheet("""
                    QComboBox {
                        font-size: 15px;
                        padding: 5px;
                        background: white;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                    }
                    QComboBox:hover {
                        border: 1px solid #1976D2;
                    }
                """)
                row_layout.addWidget(combo)
                
                self.combos[case_num] = combo
                scroll_layout.addWidget(row_widget)
            
            scroll_layout.addStretch()
            scroll.setWidget(scroll_widget)
            main_layout.addWidget(scroll)
            
            # Quick actions
            quick_layout = QHBoxLayout()
            
            set_all_resolved = QPushButton("✓ All Resolved")
            set_all_resolved.setStyleSheet("background: #4CAF50; color: white; padding: 8px; border-radius: 4px;")
            set_all_resolved.clicked.connect(lambda: self.set_all("Issue Resolved"))
            quick_layout.addWidget(set_all_resolved)
            
            set_all_not_reached = QPushButton("📞 All Not Reached")
            set_all_not_reached.setStyleSheet("background: #FFC107; color: black; padding: 8px; border-radius: 4px;")
            set_all_not_reached.clicked.connect(lambda: self.set_all("Customer Not Reached"))
            quick_layout.addWidget(set_all_not_reached)
            
            set_all_not_fixed = QPushButton("✗ All Not Fixed")
            set_all_not_fixed.setStyleSheet("background: #FF5722; color: white; padding: 8px; border-radius: 4px;")
            set_all_not_fixed.clicked.connect(lambda: self.set_all("Issue Not Fixed"))
            quick_layout.addWidget(set_all_not_fixed)
            
            main_layout.addLayout(quick_layout)
            
            # Buttons
            btn_layout = QHBoxLayout()
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setStyleSheet("padding: 10px 25px; font-size: 15px;")
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
            
            btn_layout.addStretch()
            
            apply_btn = QPushButton("✓ Apply Results")
            apply_btn.setStyleSheet("""
                QPushButton {
                    background: #1976D2; 
                    color: white; 
                    padding: 10px 30px; 
                    font-size: 15px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background: #1565C0;
                }
            """)
            apply_btn.clicked.connect(self.accept)
            btn_layout.addWidget(apply_btn)
            
            main_layout.addLayout(btn_layout)
            
            self.setLayout(main_layout)
        
        def set_all(self, outcome):
            """Set all dropdowns to the same outcome"""
            for combo in self.combos.values():
                index = combo.findText(outcome)
                if index >= 0:
                    combo.setCurrentIndex(index)
        
        def get_outcomes(self):
            """Get outcome for each case"""
            return {case_num: combo.currentText() for case_num, combo in self.combos.items()}
    
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



def run_companies_process(driver, cache_file, agent_name, sheet_name="Companies"):
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
    # NEW SETUP: Restart Driver, Login to Dialer, Open CRM
    # =========================================================================
    if driver:
        try:
            print("[INFO] Closing existing driver to prepare for Dialer/CRM setup...")
            driver.quit()
        except Exception as e:
            print(f"[WARN] Error closing driver: {e}")

    # Initialize new driver
    print("[INFO] Initializing new Chrome driver...")
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
    
    # =========================================================================
    
    grouped, df_companies = load_companies_for_handler(cache_file, agent_name, sheet_name)
    
    if not grouped:
        print("[INFO] No company cases to process for this handler")
        return
    
    print(f"[INFO] Found {len(grouped)} distinct companies (emails) to process")
    
    today_str = datetime.now().strftime("%b %d, %Y")
    
    for email, data in grouped.items():
        cases = data['cases']
        
        print(f"\n[INFO] ========== Processing Company Email: {email} ({len(cases)} cases) ==========")
        
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
                
                # Step 3: Check if solution provided using solution_provided_check_and_skip
                print(f"[INFO] Step 3: Checking Solution Provided status...")
                is_solution_provided = solution_provided_check_and_skip(driver, case_num, df_companies, cache_file)
                
                if is_solution_provided:
                    solution_provided_cases.append({
                        'case_number': case_num,
                        'serial': case.get('serial', ''),
                        'mtm': case.get('mtm', ''),
                        'row_idx': case.get('row_idx')
                    })
                    print(f"[INFO] ✓ Case {case_num}: Solution Provided - added to batch")
                else:
                    print(f"[INFO] ✗ Case {case_num}: NOT Solution Provided - marking as Skipped")
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


if __name__ == "__main__":
    print("[INFO] CompaniesProcess module - run via AutoSender or Dispatcher")
