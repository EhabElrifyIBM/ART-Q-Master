# ============================================================================
# AutoSender.py - Process NEW Cases (No Dialer)
# ============================================================================
# This module handles processing of NEW cases only:
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
    CompaniesProcessDialog,
    load_companies_for_handler,
    get_todays_cache_path,
    check_existing_cache_and_ask,
)

# CRM URL - Dynamics 365
CRM_URL = "https://lenovo-plrs-prod.crm5.dynamics.com/main.aspx?appid=00fd771a-9081-e911-a83a-000d3a07fba2&forceUCI=1&pagetype=dashboard&id=4e76815a-1f63-df11-ae90-00155d2e3002&type=system&_canOverride=true"


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


def run_auto_sender(excel_path=None, support_agent=None):
    """
    Main entry point for Auto Sender mode.
    Processes NEW cases only - sends SMS, Email, adds Notes.
    After NEW cases, runs Companies Process, then exits to Dispatcher.
    
    Args:
        excel_path: Optional path to the Excel file. If not provided, uses todays_excel_path()
        support_agent: Optional name of agent being supported (for dynamic sheet naming)
    """
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
    
    try:
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
        # CHECK FOR EXISTING CACHE - Resume Logic
        # =====================================================================
        cache_file = get_todays_cache_path(working_agent, mode="autosender")
        os.makedirs(CACHE_DIRECTORY, exist_ok=True)
        
        resume_choice = check_existing_cache_and_ask(cache_file, mode_name="Auto Sender")
        
        if resume_choice == "RESUME":
            # Resume from existing cache
            print(f"[INFO] Resuming from existing cache: {cache_file}")
            df = pd.read_excel(cache_file, sheet_name=sheet_name)
            new_case_count = len(df)
            print(f"[INFO] Loaded {new_case_count} cases from cache")
            
            # Check if Companies sheet exists in cache, if not add it from main file
            try:
                with pd.ExcelFile(cache_file) as xls:
                    if 'Companies' not in xls.sheet_names:
                        print(f"[INFO] Companies sheet not in cache, attempting to add from main file...")
                        # Find Companies sheet in main file (may have different name like '(Companies)')
                        with pd.ExcelFile(excel_path) as main_xls:
                            companies_sheet_name = None
                            for sheet in main_xls.sheet_names:
                                if 'companies' in str(sheet).lower():
                                    companies_sheet_name = sheet
                                    break
                            
                            if companies_sheet_name:
                                df_companies = pd.read_excel(excel_path, sheet_name=companies_sheet_name)
                                agent_first = working_agent.split()[0]
                                comp_assigned_col = find_column_case_insensitive(df_companies, 'Assigned To')
                                if comp_assigned_col:
                                    # DERIVE HANDLER FROM SHEET NAME for Companies (e.g. "Teama's Cases" -> "Teama")
                                    # Use local sheet_name instead of working_agent
                                    handler_from_sheet = sheet_name.replace("'s Cases", "").replace("'s cases", "").strip()
                                    if not handler_from_sheet:
                                        # Fallback if replace fails or empty
                                        handler_from_sheet = working_agent.split()[0]
                                    
                                    print(f"[DEBUG] Filtering Companies for handler: {handler_from_sheet} (derived from '{sheet_name}')")
                                    
                                    df_companies_handler = df_companies[df_companies[comp_assigned_col].astype(str).str.strip() == handler_from_sheet].copy()
                                    
                                    # NEW: Filter by Status 'New'
                                    status_col = find_column_case_insensitive(df_companies_handler, 'Status')
                                    if status_col:
                                        df_companies_handler = df_companies_handler[
                                            df_companies_handler[status_col].astype(str).str.strip().str.lower() == 'new'
                                        ].copy()
                                    
                                    if len(df_companies_handler) > 0:
                                        # Re-save cache with Companies sheet
                                        with pd.ExcelWriter(cache_file, engine='openpyxl') as writer:
                                            df.to_excel(writer, sheet_name=sheet_name, index=False)
                                            df_companies_handler.to_excel(writer, sheet_name='Companies', index=False)
                                        print(f"[INFO] Added {len(df_companies_handler)} Companies cases to cache (from '{companies_sheet_name}')")
                            else:
                                print(f"[INFO] No Companies sheet found in main file")
            except Exception as e:
                print(f"[WARN] Could not check/add Companies sheet: {e}")
            
            # Initialize columns for processing (needed for loop below)
            # Try to find columns in the loaded dataframe
            status_col = find_column_case_insensitive(df, 'Status') or 'Status'
            case_col = find_column_case_insensitive(df, 'Case Number') or 'Case Number'
            assigned_col = find_column_case_insensitive(df, 'Assigned To') or 'Assigned To'
            
            # Additional imports if needed locally (though should be global)
            import traceback
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
            
            # Filter for Status = "New" only (Ignore Assigned To)
            print(f"[INFO] Filtering for 'New' cases in sheet '{sheet_name}'")
            
            df_filtered = df_main[
                (df_main[status_col].astype(str).str.strip().str.lower() == 'new')
            ].copy()
            
            new_case_count = len(df_filtered)
            print(f"[INFO] Found {new_case_count} NEW cases to process")
            
            if new_case_count == 0:
                print("[INFO] No new 'Active Cases' to process. Proceeding to check Companies...")
                # Removed early return to allow Companies Process check logic to run
                # show_completion_dialog(0, 0)
                # return
            
            # Save filtered cases to cache WITH Companies sheet
            print(f"[INFO] Creating working cache file: {cache_file}")
            
            # FIRST: Load Companies data BEFORE opening ExcelWriter (to avoid nested context issues)
            df_companies_handler = None
            try:
                with pd.ExcelFile(excel_path) as main_xls:
                    print(f"[DEBUG] All sheets in main file: {main_xls.sheet_names}")
                    companies_sheet_name = None
                    for sheet in main_xls.sheet_names:
                        if 'companies' in str(sheet).lower():
                            companies_sheet_name = sheet
                            print(f"[DEBUG] Found Companies sheet: '{companies_sheet_name}'")
                            break
                    
                    if companies_sheet_name:
                        df_companies = pd.read_excel(excel_path, sheet_name=companies_sheet_name)
                        print(f"[DEBUG] Loaded {len(df_companies)} rows from '{companies_sheet_name}'")
                        # Filter for handler's cases only
                        comp_assigned_col = find_column_case_insensitive(df_companies, 'Assigned To')
                        if comp_assigned_col:
                            # DERIVE HANDLER FROM SHEET NAME
                            handler_from_sheet = sheet_name.replace("'s Cases", "").replace("'s cases", "").strip()
                            if not handler_from_sheet:
                                    handler_from_sheet = working_agent.split()[0]
                            
                            print(f"[DEBUG] Filtering Companies for handler: '{handler_from_sheet}'")
                            df_companies_handler = df_companies[df_companies[comp_assigned_col].astype(str).str.strip() == handler_from_sheet].copy()
                            
                            # NEW: Filter by Status 'New'
                            status_col_comp = find_column_case_insensitive(df_companies_handler, 'Status')
                            if status_col_comp:
                                df_companies_handler = df_companies_handler[
                                    df_companies_handler[status_col_comp].astype(str).str.strip().str.lower() == 'new'
                                ].copy()
                            
                            print(f"[DEBUG] Found {len(df_companies_handler)} cases for handler '{handler_from_sheet}'")
                        else:
                            print(f"[WARN] No 'Assigned To' column found in Companies sheet")
                    else:
                        print(f"[INFO] No Companies sheet found in main file")
            except Exception as ce:
                print(f"[ERROR] Failed to load Companies data: {ce}")
                import traceback
                traceback.print_exc()
            
            # SECOND: Write both sheets to cache file
            with pd.ExcelWriter(cache_file, engine='openpyxl') as writer:
                df_filtered.to_excel(writer, sheet_name=sheet_name, index=False)
                if df_companies_handler is not None and len(df_companies_handler) > 0:
                    df_companies_handler.to_excel(writer, sheet_name='Companies', index=False)
                    print(f"[INFO] ✓ Added {len(df_companies_handler)} handler cases to Companies sheet")
                else:
                    print(f"[INFO] No Companies cases to add for this handler")
            
            # Verify the cache file was written correctly
            try:
                with pd.ExcelFile(cache_file) as verify_xls:
                    print(f"[DEBUG] Verification - Cache file sheets: {verify_xls.sheet_names}")
            except Exception as ve:
                print(f"[WARN] Could not verify cache file: {ve}")
            print(f"[INFO] Working cache created with {len(df_filtered)} cases")
            
            # Use filtered dataframe for processing
            df = df_filtered.copy()
        
        # Process counters
        case_counter = 0
        processed_count = 0
        today_str = datetime.now().strftime("%b %d, %Y")
        CaseNote = get_case_note("Sent SMS  // Sent Email")
        
        # Get refresh interval dynamically from config
        try:
            refresh_interval_val = CONFIG_MANAGER.get_value('execution_settings', 'refresh_interval')
            refresh_interval = int(refresh_interval_val)
        except Exception:
            refresh_interval = 10  # Default fallback
        print(f"[INFO] Driver refresh interval set to: {refresh_interval} cases")
        
        # Process each new case
        for idx, row in df.iterrows():
            try:
                status = str(row.get(status_col, '')).strip().lower()
                case_number = row.get(case_col)
                
                if pd.isna(case_number) or not str(case_number).strip():
                    continue
                    
                case_number = str(case_number).strip()
                
                # Only process 'new' cases
                if status != 'new':
                    continue
                
                print(f"\n[INFO] Processing NEW case {case_counter + 1}/{new_case_count}: {case_number}")
                
                # Search and open case (WITHOUT clicking Edit)
                case_search_and_open_no_edit(driver, case_number)
                
                # Check if Solution Provided - skip if not (before editing)
                if not solution_provided_check_and_skip(driver, case_number, df, excel_path):
                    print(f"[INFO] Case {case_number} - Solution not provided, skipping...")
                    df.at[idx, "Status"] = 'Skipped'
                    update_cache_file(cache_file, df, EXCEL_SHEET_NAME)
                    case_counter += 1
                    continue
                
                # Solution provided - now click Edit button to start editing
                click_edit_button(driver)
                
                # Check for e-ticketing case and update fields if needed
                eticket_check_and_skip(driver, case_number, df, excel_path)
                
                # Extract Serial Number
                serial_val = serial_extraction(driver, case_number, df)
                
                # Extract Customer Name
                CX_Name = customer_name_extraction(driver, case_number)
                
                # Format SMS Text
                sms_text = formatting_texts_sms(CX_Name, serial_val, case_number, df)
                
                # Format Email Text
                email_text = formatting_texts_email(CX_Name, serial_val, case_number, df)
                
                # Send SMS (if Action 1 empty)
                sms_sent = False
                if pd.isna(row.get("Action 1", "")) or str(row.get("Action 1", "")).strip() == "":
                    print(f"[INFO] Sending SMS for case {case_number}...")
                    sms_sent = send_SMS(driver, sms_text)
                    if sms_sent:
                        print(f"[SUCCESS] SMS sent for case {case_number}")
                    else:
                        print(f"[WARN] SMS failed for case {case_number}")
                else:
                    sms_sent = True  # Already sent
                
                # Send Email (if Action 2 empty)
                email_sent = False
                if pd.isna(row.get("Action 2", "")) or str(row.get("Action 2", "")).strip() == "":
                    print(f"[INFO] Sending Email for case {case_number}...")
                    email_sent = send_Email(driver, email_text)
                    if email_sent:
                        print(f"[SUCCESS] Email sent for case {case_number}")
                    else:
                        print(f"[WARN] Email failed for case {case_number}")
                else:
                    email_sent = True  # Already sent
                
                # Add Case Note
                print(f"[INFO] Adding case note for {case_number}...")
                note_saved = add_Case_Note(driver, CaseNote)
                
                # Update DataFrame
                if sms_sent:
                    df.at[idx, "Action 1"] = 'Sent SMS'
                if email_sent:
                    df.at[idx, "Action 2"] = 'Sent Email'
                df.at[idx, "Action 3"] = ''
                df.at[idx, "Final Action"] = 'Sent Email'
                
                if sms_sent and email_sent and note_saved:
                    df.at[idx, "Status"] = 'In Progress Today'
                    processed_count += 1
                
                # Update cache file
                update_cache_file(cache_file, df, sheet_name)
                
                case_counter += 1
                print(f"[INFO] Completed case {case_number} - {case_counter}/{new_case_count} done")
                
                # Keep driver alive periodically
                if case_counter > 0 and case_counter % refresh_interval == 0:
                    keep_driver_alive(driver)
                    time.sleep(5)
                    
            except Exception as e:
                print(f"[ERROR] Exception processing case {case_number if 'case_number' in locals() else 'UNKNOWN'}: {type(e).__name__}: {str(e)}")
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 60)
        print(f"[INFO] Auto Sender Complete!")
        print(f"[INFO] Processed: {processed_count}/{new_case_count} cases")
        print(f"[INFO] Cache file: {cache_file}")
        print("=" * 60)
        
        # =====================================================================
        # COMPANIES PROCESS - Run BEFORE completion dialog
        # =====================================================================
        companies_processed = False
        try:
            # Load Companies directly from MAIN Excel file (more reliable than cache)
            print(f"\n[INFO] Checking for company cases in main file: {excel_path}")
            
            # Find Companies sheet in main file
            with pd.ExcelFile(excel_path) as main_xls:
                companies_sheet_name = None
                for sheet in main_xls.sheet_names:
                    if 'companies' in str(sheet).lower():
                        companies_sheet_name = sheet
                        break
                
                if companies_sheet_name:
                    df_companies = pd.read_excel(excel_path, sheet_name=companies_sheet_name)
                    print(f"[DEBUG] Loaded {len(df_companies)} rows from '{companies_sheet_name}'")
                    
                    # Filter for handler's cases only
                    agent_first = working_agent.split()[0]
                    comp_assigned_col = find_column_case_insensitive(df_companies, 'Assigned To')
                    email_col = find_column_case_insensitive(df_companies, 'Email')
                    
                    if comp_assigned_col:
                        # DERIVE HANDLER FROM SHEET NAME
                        handler_from_sheet = sheet_name.replace("'s Cases", "").replace("'s cases", "").strip()
                        if not handler_from_sheet:
                             handler_from_sheet = working_agent.split()[0]
                        
                        print(f"[DEBUG] Companies: Filtering for handler: {handler_from_sheet}")
                        
                        # Filter for handler first
                        df_companies_handler = df_companies[df_companies[comp_assigned_col].astype(str).str.strip() == handler_from_sheet].copy()
                        
                        # NEW: Filter by Status 'New'
                        status_col = find_column_case_insensitive(df_companies_handler, 'Status')
                        if status_col:
                            print(f"[DEBUG] Filtering Companies cases by Status='New' (col: {status_col})")
                            initial_count = len(df_companies_handler)
                            df_companies_handler = df_companies_handler[
                                df_companies_handler[status_col].astype(str).str.strip().str.lower() == 'new'
                            ].copy()
                            print(f"[DEBUG] Companies filtering: {initial_count} -> {len(df_companies_handler)} cases")
                        
                        if len(df_companies_handler) > 0 and email_col:
                            # Group by email
                            unique_emails = df_companies_handler[email_col].dropna().unique()
                            distinct_emails = len([e for e in unique_emails if str(e).strip().lower() not in ['', 'nan', 'none']])
                            total_company_cases = len(df_companies_handler)
                            
                            print(f"\n[INFO] Found {total_company_cases} company cases ({distinct_emails} companies)")
                            
                            # Save Companies to cache for CompaniesProcess to use
                            try:
                                # Read existing cache and add Companies sheet
                                with pd.ExcelFile(cache_file) as existing:
                                    existing_sheets = {sheet: pd.read_excel(cache_file, sheet_name=sheet) for sheet in existing.sheet_names}
                                
                                existing_sheets['Companies'] = df_companies_handler
                                
                                with pd.ExcelWriter(cache_file, engine='openpyxl') as writer:
                                    for sheet_name, sheet_df in existing_sheets.items():
                                        sheet_df.to_excel(writer, sheet_name=sheet_name, index=False)
                                print(f"[INFO] ✓ Added Companies sheet to cache file")
                            except Exception as cache_err:
                                print(f"[WARN] Could not add Companies to cache: {cache_err}")
                            
                            # Show dialog asking if user wants to process companies
                            app = QApplication.instance()
                            if app is None:
                                app = QApplication(sys.argv)
                            
                            dialog = CompaniesProcessDialog(total_company_cases, distinct_emails)
                            dialog.exec_()
                            
                            if dialog.result == "YES":
                                print("[INFO] User chose to process company cases...")
                                # Import and run companies process
                                from CompaniesProcess import run_companies_process
                                run_companies_process(driver, cache_file, working_agent, "Companies")
                                print("[INFO] Companies Process completed!")
                                companies_processed = True
                            else:
                                print("[INFO] User skipped company cases.")
                        else:
                            print(f"[INFO] No company cases assigned to {agent_first}")
                    else:
                        print("[WARN] No 'Assigned To' column in Companies sheet")
                else:
                    print("[INFO] No Companies sheet found in main file")
        except Exception as e:
            print(f"[WARN] Error checking for company cases: {e}")
            traceback.print_exc()
        
        # Show completion dialog AFTER companies process
        if companies_processed:
            print("\n[INFO] Auto Sender and Companies Process complete.")
        else:
            show_completion_dialog(processed_count, new_case_count)
        
        print("\n[INFO] Returning to Dispatcher.")
        
    except Exception as e:
        print(f"[CRITICAL ERROR] Auto Sender failed: {e}")
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
            "Auto Sender Complete",
            f"Auto Sender has finished processing.\n\n"
            f"Processed: {processed}/{total} cases\n\n"
            f"Click OK to exit."
        )
    except Exception as e:
        print(f"[WARN] Could not show completion dialog: {e}")


if __name__ == "__main__":
    run_auto_sender()
