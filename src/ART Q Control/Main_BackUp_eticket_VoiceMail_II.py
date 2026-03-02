import importlib
import Functions
importlib.reload(Functions)
from Functions import *
import sys
import os
import pandas as pd
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from datetime import datetime
import time


class Companies:
    def __init__(self, driver, excel_path):
        self.driver = driver
        self.excel_path = excel_path

    def load_and_filter_data(self):
        print(f"[INFO] Loading 'Companies' sheet from {self.excel_path}...")
        try:
            df = pd.read_excel(self.excel_path, sheet_name="Companies")
        except Exception as e:
            print(f"[ERROR] Failed to read 'Companies' sheet: {e}")
            return {}, None

        # Checkpoint logic
        base_dir = os.path.dirname(self.excel_path)
        base_name = os.path.splitext(os.path.basename(self.excel_path))[0]
        checkpoint_path = os.path.join(base_dir, f"CHECKPOINT_{base_name}_Companies.csv")

        if os.path.exists(checkpoint_path):
            print(f"[INFO] Found checkpoint: {checkpoint_path}")
            try:
                df = pd.read_csv(checkpoint_path)
            except Exception as e:
                print(f"[WARN] Failed to read checkpoint, using Excel: {e}")

        # Filter for Assigned To = 'Adam' AND Status = 'new'
        assigned_col = find_column_case_insensitive(df, 'Assigned To')
        status_col = find_column_case_insensitive(df, 'Status')

        filtered_df = df
        
        if assigned_col:
             # Case insensitive check for 'Adam'
             mask_assigned = df[assigned_col].astype(str).str.strip().str.lower() == 'adam'
             filtered_df = df[mask_assigned]
        else:
             print("[WARN] 'Assigned To' column not found.")

        if status_col:
             # Case insensitive check for 'new'
             mask_status = filtered_df[status_col].astype(str).str.strip().str.lower() == 'new'
             filtered_df = filtered_df[mask_status]
        else:
             print("[WARN] 'Status' column not found. Skipping status filter.")

        if filtered_df.empty:
            print("[INFO] No companies found assigned to 'Adam'.")
            return {}, df

        # Group by Email
        email_col = find_column_case_insensitive(filtered_df, 'Email') or find_column_case_insensitive(filtered_df, 'Company Email')
        if not email_col:
            print("[ERROR] Email column not found.")
            return {}, df

        grouped_data = {}
        for idx, row in filtered_df.iterrows():
            email = str(row.get(email_col, '')).strip()
            if not email or email.lower() == 'nan':
                continue
            
            if email not in grouped_data:
                grouped_data[email] = {
                    'company_name': str(row.get('Company Name', 'Unknown')).strip(),
                    'cases': []
                }
            
            grouped_data[email]['cases'].append({
                'case_number': str(row.get('Case Number', '')).strip(),
                'serial_number': str(row.get('Serial Number', '')).strip(),
                'row_index': idx,
                'original_row': row
            })

        return grouped_data, df, checkpoint_path

    def process_companies(self):
        companies_data, df, checkpoint_path = self.load_and_filter_data()
        if not companies_data:
            return

        for email, data in companies_data.items():
            company_name = data['company_name']
            all_cases = data['cases']
            
            print(f"\n[INFO] --- Processing Company: {company_name} ({len(all_cases)} cases) ---")
            
            valid_cases_for_email = []
            
            # 1. Validate Cases
            for case in all_cases:
                case_num = case['case_number']
                print(f"[INFO] Checking status for Case: {case_num}")
                try:
                    case_search_and_open(self.driver, case_num)
                    handle_genesys_popup(self.driver)

                    # Use shared function
                    if Company_solution_provided_check_and_skip(self.driver, case_num, df, self.excel_path):
                        valid_cases_for_email.append(case)
                    else:
                        print(f"[INFO] Case {case_num} skipped (Status/Solution Provided check failed).")
                        # Optionally mark skipped in DF here?
                except Exception as e:
                    print(f"[ERROR] Error checking case {case_num}: {e}")

            if not valid_cases_for_email:
                print("[INFO] No valid cases for this company. Moving to next.")
                continue

            # 2. Send Email (on the LAST valid case)
            last_case = valid_cases_for_email[-1]
            last_case_num = last_case['case_number']
            
            print(f"[INFO] Formatting Email for {len(valid_cases_for_email)} cases...")
            
            # Prepare Email Body
            formatted_lines = []
            has_serials = False
            case_numbers = [c['case_number'] for c in valid_cases_for_email]
            cases_str = ", ".join(case_numbers)

            for c in valid_cases_for_email:
                 sn = c['serial_number']
                 cn = c['case_number']
                 if sn and sn.lower() != 'nan':
                     formatted_lines.append(f"{sn} | {cn}")
                     has_serials = True
            
            formatted_str = "\n".join(formatted_lines)
            
            if has_serials:
                email_body = (
                    " Hello All \n\n"
                    "I hope you are doing well.\n\n"
                    f"Regarding the devices of Serial numbers:\n"
                    f"{formatted_str}\n"
                    "I am contacting you to verify that the devices are functioning properly and performing to your expectations.\n\n"
                    "Thank you for choosing Lenovo Services.\n\n"
                    "We appreciate your business and are here to support you.\n\n"
                    "Thanks and Regards,\n"
                    f"{AgentName}\n"
                    "NA Lenovo PC Assurance Resolution Team"
                )
            else:
                 email_body = (
                    " Hello All \n\n"
                    "I hope you are doing well.\n\n"
                    f"Regarding the Accessories for cases numbers:\n"
                    f"{cases_str}\n"
                    "I am contacting you to verify that the devices are functioning properly and performing to your expectations.\n\n"
                    "Thank you for choosing Lenovo Services.\n\n"
                    "We appreciate your business and are here to support you.\n\n"
                    "Thanks and Regards,\n"
                    f"{AgentName}\n"
                    "NA Lenovo PC Assurance Resolution Team"
                 )

            # Navigate to last case to send email
            print(f"[INFO] Navigating to last case {last_case_num} to send email...")
            if last_case_num != all_cases[0]['case_number']: # Optimization: If not already there? Logic says we iterated.
                 case_search_and_open(self.driver, last_case_num)

            # Send Email
            email_sent = send_Email(self.driver, email_body)
            action_status = "Company Email Sent" if email_sent else "Email Failed"

            # 3. Add Note & Call Flow
            # Add note to *current* case (last one)? Or all?
            # User said: "then add a case_note, then open dialogue..."
            # Usually notes are added to all relevant cases, but let's stick to the flow described:
            # "sent email on last case ... then add a case_note ... then open dialogue"
            


            # Dialog
            dialog = ConfirmCallDialog(company_name, email)
            result = dialog.exec()
            
            call_closing_code = "Skipped"
            final_status = "Customer Not Reached" # Default for skipped per request
            
            if result == 1: # Call
                perform_call_flow(self.driver)
                code, _ = get_call_closing_code(self.driver)
                call_closing_code = code
                final_status = code
            else:
                # Skipped
                call_closing_code = "Skipped"
                final_status = "Customer Not Reached"

            # Update Excel for ALL processed cases in this group
            # Note Content (with Closing Code)
            note_content = f"Date: {today_str}\nQueue: ART Project - Follow up \nAgent: {AgentName} \nAction: {action_status} - Bulk Follow up - {final_status}\n \n ------------------------"
            
            for c in valid_cases_for_email:
                idx = c['row_index']
                case_num_val = c['case_number']
                
                # Add Note to EACH case
                print(f"[INFO] Adding note to {case_num_val}...")
                # We need to be on the case page to add a note.
                # Optimization: last_case_num is where we are currently (if we didn't move).
                # But we might have moved if we did call flow? 
                # Actually, perform_call_flow ends... where? It ends after closing code.
                # Case might be closed. But we can still add notes? Yes usually.
                
                try:
                    if case_num_val != last_case_num or (len(valid_cases_for_email) > 1):
                         # If we have multiple cases, we likely need to open each one. 
                         # Even for the last one, if we navigated away or if we are iterating, safe to search.
                         # BUT, if we just finished the last case logic, we might be on it.
                         # Let's be safe and search/open.
                         case_search_and_open(self.driver, case_num_val)
                    
                    # If we are already on the page (last case), we might skip search, 
                    # but case_search_and_open handles "already open" check usually? 
                    # Let's assume we need to ensure we are on the right case.
                    
                    add_Case_Note(self.driver, note_content)
                except Exception as e:
                     print(f"[ERROR] Failed to add note to {case_num_val}: {e}")

                df.at[idx, "Action 1"] = "Company Email Sent"
                df.at[idx, "Action 2"] = "Company Email Sent"
                if call_closing_code == "Skipped":
                     df.at[idx, "Action 3"] = "Skipped"
                     df.at[idx, "Final Action"] = "Customer Not Reached"
                     df.at[idx, "Status"] = "Closed" # Request didn't specify, but implied?
                else:
                     df.at[idx, "Action 3"] = "Called The Company Agent"
                     df.at[idx, "Final Action"] = call_closing_code
                     df.at[idx, "Status"] = "Closed"
            
            # Save Checkpoint
            if checkpoint_path:
                df.to_csv(checkpoint_path, index=False)
                print(f"[INFO] Checkpoint updated for company {company_name}")

        # Final Sync
        print("[INFO] Syncing to Main Excel...")
        save_excel_safely(df, self.excel_path, sheet_name="Companies", sheet_password="artadmin")
        
        # Cleanup
        if checkpoint_path and os.path.exists(checkpoint_path):
             os.remove(checkpoint_path)

if __name__ == "__main__":
    excel_path = todays_excel_path()
    
    # Enable Windows sleep/display inhibit while waiting
    try:
        enable_windows_inhibit()
    except Exception:
        pass

    try:
        now = datetime.now()
        target = datetime(now.year, now.month, now.day, 14, 55)
        
        should_wait = True
        if now < target:
            should_wait = ask_wait_choice()
            
        if should_wait:
            if now >= target:
                print("[INFO] Current time is already past 2:55 PM — running immediately.")
            else:
                wait_until_time(14, 55)
        else:
            print("[INFO] User chose to SKIP waiting. Proceeding immediately.")

    except Exception as e:
        print(f"[WARN] wait_until_time check failed or was interrupted: ")

    # Check if Excel file exists; if not, start driver and wait for it
    if not os.path.exists(excel_path):
        print(f"[INFO] Excel file does not exist: {excel_path}")
        print(f"[INFO] Starting driver now and waiting for Excel file...")

        # Set Chrome to use ART Profile
        chrome_options = Chrome_ART_Profile()

        # Start driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.maximize_window()

        try:
            perform_dialer_login(driver)
        except Exception as e:
            print(f"[WARN] Dialer login failed (optional): ")

        print(f"[INFO] Driver started. Now waiting for Excel file...")

        # Wait for Excel file, keeping driver alive by refreshing periodically
        attempt = 0
        while not os.path.exists(excel_path):
            attempt += 1
            print(f"[INFO] Excel check attempt {attempt}: waiting 5 minutes...")

            # Sleep in 1-minute intervals, refreshing driver every minute to keep session alive
            for minute in range(5):
                time.sleep(180)  # sleep 3 minutes
                keep_driver_alive(driver)
                if os.path.exists(excel_path):
                    print(f"[INFO] Excel file found on minute {minute+1} of attempt {attempt}")
                    break

        print(f"[INFO] Excel file is now available. Proceeding with main loop...")
    else:
        # Excel file exists; proceed normally
        print(f"[INFO] Excel file exists: {excel_path}")
        print(f"[INFO] Starting driver and proceeding with case processing...")

        # Set Chrome to use ART Profile
        chrome_options = Chrome_ART_Profile()

        # Start driver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.maximize_window()
        try:
            perform_dialer_login(driver)
        except Exception as e:
            print(f"[WARN] Dialer login failed (optional): ")

    # Create a backup before starting processing
    create_backup(excel_path)

    # --- Mode Selection ---
    prompt_app = QApplication.instance()
    if not prompt_app:
        prompt_app = QApplication(sys.argv)

    mode_choice = show_choice_dialog(
        "Select Mode",
        "Choose operation mode:",
        "Standard Case Processing",
        "Companies Bulk Processing",
        timeout_secs=60
    )
    
    if mode_choice == "Companies Bulk Processing":
         print("[INFO] Starting Companies Bulk Processing Mode...")
         companies_processor = Companies(driver, excel_path)
         companies_processor.process_companies()
         print("[INFO] Companies processing complete.")
         disable_windows_inhibit()
         driver.quit()
         sys.exit(0)
    
    # --- End Mode Selection ---


    # --- Checkpoint Loading Logic ---
    dir_name = os.path.dirname(excel_path)
    base_name = os.path.basename(excel_path)
    name, ext = os.path.splitext(base_name)
    checkpoint_path = os.path.join(dir_name, f"CHECKPOINT_{name}.csv")

    if os.path.exists(checkpoint_path):
        print(f"[INFO] Found checkpoint file: {checkpoint_path}")
        print("[INFO] Resuming from checkpoint...")
        try:
            df = pd.read_csv(checkpoint_path)
            print(f"[INFO] Checkpoint loaded successfully: {len(df)} rows.")
        except Exception as e:
            print(f"[ERROR] Failed to read checkpoint: {e}")
            print("[INFO] Falling back to main Excel file...")
            df = pd.read_excel(excel_path, sheet_name="Adam's Cases")
    else:
        print("[INFO] No checkpoint found. Loading main Excel file...")
        # Read case numbers from Excel sheet
        df = pd.read_excel(excel_path, sheet_name="Adam's Cases") 
    status_col = find_column_case_insensitive(df, 'Status')
    worktype_col = find_column_case_insensitive(df, 'Work Order Type')
    state_col = find_column_case_insensitive(df, 'State/Province')
    case_col = find_column_case_insensitive(df, 'Case Number')

    print(f"Agent Name: {AgentName}")
    time.sleep(10)  # wait for manual login if needed
    today_str = datetime.now().strftime("%b %d, %Y")

    # Filter out rows where Status == 'closed' (case-insensitive)
    try:
        filtered_df = df[~df[status_col].astype(str).str.strip().str.lower().eq('closed')]
    except Exception:
        filtered_df = df.copy()

    # Pre-calculate indices of cases to process
    to_process_indices = []
    new_case_count = 0 
    for idx, row in filtered_df.iterrows():
        status = str(row.get(status_col, '')).strip().lower()
        case_number = row.get(case_col)
        if pd.isna(case_number) or not str(case_number).strip():
            continue
        if status in ('new', 'in_progress', 'skipped'):
            to_process_indices.append(idx)
            if status == 'new':
                new_case_count += 1

    # Map row index to its "In Progress" sequence number (1-based)
    index_to_progress_num = {}
    curr_prog = 0
    for idx in to_process_indices:
        status = str(filtered_df.at[idx, status_col]).strip().lower()
        if status == 'in_progress' or status == 'skipped':
            curr_prog += 1
            index_to_progress_num[idx] = curr_prog

    # Initialize Time Trigger Handler
    time_handler = TimeTriggerHandler()

    refresh_interval = 5  # Refresh every 5 cases
    case_counter = 0 
    pointer = 0

    # Calculate total in-progress cases for progress bar
    total_in_progress_cases = curr_prog

    # --- 5:00 PM Startup Check ---
    # If starting fresh after 5 PM, optionally reorder immediately
    if datetime.now().hour >= 17:
        print("[INFO] Startup time is past 5:00 PM.")
        choice = show_choice_dialog(
            "5:00 PM Check",
            "It is past 5:00 PM. How do you want to proceed?",
            "Start the inprogress",
            "Complete the new"
        )
        if choice == "Start the inprogress":
            print("[INFO] User chose to prioritize In-Progress cases from start.")
            try:
                # pass pointer=-1 to indicate we are at the very beginning (or 0 and force reorder)
                # reorder_indices_priority expects a pointer to 'done' items. 
                # If we haven't started, pointer=0 means first item is 'current'.
                # Actually, reorder logic splits at pointer+1.
                # If we want to reorder the WHOLE list, we can act as if we are before the first item.
                # But reorder_indices_priority implementation:
                # done_indices = to_process_indices[:current_pointer+1]
                # future_indices = to_process_indices[current_pointer+1:]
                # If pointer is 0, done is [0], future is [1:]
                # This keeps the first item as 'done' or 'next to do'.
                
                # Let's adapt slightly: if pointer is 0, we might want to sort everything.
                # But simpler is to use existing reorder function with pointer=-1 if possible, 
                # OR just manually reorder here since logic is simple.
                
                # Manual reorder for startup:
                priority_indices = []
                normal_indices = []
                for idx in to_process_indices:
                     status = str(df.at[idx, status_col]).strip().lower()
                     if status in ('in_progress', 'skipped'):
                         priority_indices.append(idx)
                     else:
                         normal_indices.append(idx)
                to_process_indices = priority_indices + normal_indices
                print(f"[INFO] Queue reordered: {len(priority_indices)} priority cases moved to front.")
                
            except Exception as e:
                print(f"[ERROR] Failed to reorder queue at startup: {e}")
                
    # --- Hot Reload Init ---
    functions_path = os.path.join(os.getcwd(), 'Functions.py')
    try:
        functions_mod_time = os.path.getmtime(functions_path)
    except:
        functions_mod_time = 0

    while pointer < len(to_process_indices):
        # --- Hot Reload Check ---
        try:
            current_mod_time = os.path.getmtime(functions_path)
            if current_mod_time > functions_mod_time:
                print("[INFO] Change detected in Functions.py - reloading...")
                importlib.reload(Functions)
                from Functions import *
                functions_mod_time = current_mod_time
        except Exception as e:
            print(f"[WARN] Hot reload check failed: {e}")
        # --- Time Trigger Check ---
        trigger_action = time_handler.check_triggers()
        
        if trigger_action == "PRIORITIZE_IN_PROGRESS":
            print("[INFO] User chose to prioritize In-Progress cases. Reordering queue...")
            try:
                to_process_indices = reorder_indices_priority(to_process_indices, pointer, df)
            except Exception as e:
                print(f"[ERROR] Failed to reorder queue: {e}")
                
        elif trigger_action == "FINISH_NEW":
            print("[INFO] User chose to finish New cases. Queue remains as is.")
            
        elif trigger_action == "CONTINUE_IN_PROGRESS":
             print("[INFO] User chose to continue In-Progress. Will prompt again in 15 mins.")

        elif trigger_action == "COMPLETE_NEW":
             print("[INFO] User chose to complete new. Queue remains as is.")
             
        # ---------------------------

        idx = to_process_indices[pointer]
        row = filtered_df.loc[idx]

        try:
            # Check for popup before starting a new case iteration
            handle_genesys_popup(driver)

            status = str(row.get(status_col, '')).strip().lower()
            case_number = row.get(case_col)
            if pd.isna(case_number) or not str(case_number).strip():
                pointer += 1
                continue
            case_number = str(case_number).strip()
            # Search and Open Case
            if status not in ('new', 'in_progress','skipped'):
                pointer += 1
                continue


            case_search_and_open(driver, case_number)
            
            # Extract Serial Number
            serial_val = serial_extraction(driver, case_number, df)         
            # Extract Customer Name
            CX_Name = customer_name_extraction(driver, case_number)  

            # Format SMS Text
            sms_text = formatting_texts_sms(CX_Name, serial_val, case_number, df)

            # Format Email Text
            email_text = formatting_texts_email(CX_Name, serial_val, case_number, df)


            if status == 'new':
                    # Check if Solution Provided, skip if not
                if not solution_provided_check_and_skip(driver, case_number, df, excel_path):
                    df.at[idx, "Assigned To"] = 'Adam'
                    df.at[idx, "Status"] = 'Skipped'
                    save_to_checkpoint(df, excel_path)
                    pointer += 1
                    continue
                
                #edit the case
                edit_case(driver)
                
                #check if eticket
                eticket_check_and_modify(driver)

                # Check if each column is empty (NaN or blank string) and call helpers with correct args
                if pd.isna(row["Action 1"]) or str(row["Action 1"]).strip() == "":
                    sms_sent = send_SMS(driver, sms_text)
                else:
                    sms_sent = True  # Already sent

                if pd.isna(row["Action 2"]) or str(row["Action 2"]).strip() == "":
                    email_sent = send_Email(driver, email_text)
                else:
                    email_sent = True  # Already sent
                
                note_saved = add_Case_Note(driver, CaseNote)

                #save the case
                save_case(driver)
                
                if sms_sent:
                    df.at[idx, "Action 1"] = 'Sent SMS'
                if email_sent:
                    df.at[idx, "Action 2"] = 'Sent Email'
                df.at[idx, "Action 3"] = ''
                df.at[idx, "Final Action"] = 'Sent Email'
                df.at[idx, "Assigned To"] = 'Adam'
                if sms_sent and email_sent and note_saved:
                    df.at[idx, "Status"] = 'In Progress Today'       
        
                save_to_checkpoint(df, excel_path)

                new_case_count -= 1
                print(f"[INFO] New cases remaining: {new_case_count}")  
                case_counter += 1
                pointer += 1 # Move next
                if case_counter % refresh_interval == 0:
                    keep_driver_alive(driver)
                    time.sleep(5)  # wait for refresh to complete

            elif status == 'in_progress' or status == 'skipped':
                current_prog_num = index_to_progress_num.get(idx, 0)
    
                # Determine if we can go back (can't go back if at start of list or if previous items aren't 'in_progress'
                can_go_back = (pointer > 0)
            
                # Extract State/Province
                state_val = ""
                if state_col:
                    try:
                        val = row.get(state_col)
                        if not pd.isna(val):
                            state_val = str(val).strip()
                    except:
                        state_val = ""

                CaseClosingCode, add_note = get_case_closing_code(case_number, current_prog_num, total_in_progress_cases, can_go_back=can_go_back, state_province=state_val)
                
                # Handle Navigation
                if CaseClosingCode == "NAV_PREV":
                    print("[INFO] Navigating to Previous Case...")
                    pointer -= 1
                    if pointer < 0: pointer = 0
                    continue
    
                if CaseClosingCode == "NAV_NEXT":
                    print("[INFO] Navigating to Next Case...")
                    pointer += 1
                    continue
    
                ReviewedCaseNote = f"Date: {today_str}\nQueue: ART Project - Follow up \nAgent: {AgentName} \nAction: Case is Reviewed with closing code {CaseClosingCode}\n \n ------------------------"

                # If user requested adding a Case Note via the popup, create a small note and add it
                if add_note:
                    try:
                        add_Case_Note(driver, CaseNote=ReviewedCaseNote)
                    except Exception as e:
                        print(f"[WARN] add_Case_Note failed for {case_number}: ")
    

                # If DND selected, update contact preferences
                if CaseClosingCode == "DND":
                    DND_CX(driver, case_number)

                #Care call Status
                if CaseClosingCode == "Issue Not Fixed":
                    edit_case(driver)
                    Care_call_modify(driver)
                    save_case(driver)

                if CaseClosingCode == "Call the Customer":
                    perform_call_flow(driver)

                    # after call, re-open closing code dialog to capture outcome
                    CaseClosingCode, add_note = get_call_closing_code(driver)

                    # recompute case note to reflect any new CaseClosingCode outcome
                    
                    #Care call Modify if Issue not Fixed
                    if CaseClosingCode == "Issue Not Fixed":
                        edit_case(driver)
                        Care_call_modify(driver)
                        save_case(driver)

                    try:
                        case_note_text = f"Date: {today_str}\nQueue: ART Project - Follow up\nAgent: {AgentName}\nAction: Called the Customer //  {CaseClosingCode}"
                    except Exception:
                        case_note_text = f"Date: {today_str}\nQueue: ART Project - Follow up\nAgent: {AgentName}\nAction: Called the Customer //  {CaseClosingCode}"
        
                    try:
                        click_safe(
                        driver,
                        By.XPATH,
                        "//button[contains(@id,'okButton_')]/div",
                        timeout=1,
                        retries=2,
                        )
                        
                        add_Case_Note(driver, CaseNote=case_note_text)
                    except Exception as e:
                        print(f"[WARN] add_Case_Note failed for {case_number} after call: ")


                # Prepare sms/email texts if any of those actions are requested
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
                    except Exception as e:
                        print(f"[WARN] send_SMS failed for {case_number}: ")
        

                if CaseClosingCode == "Send Email":
                    try:
                        send_Email(driver, email_text)
                        add_Case_Note(driver, CaseNote=CaseNote)  
                    except Exception as e:
                        print(f"[WARN] send_Email failed for {case_number}: ")

                if CaseClosingCode == "Send SMS and Email" or CaseClosingCode == "New":
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

                    # Update DataFrame
                    df.at[idx, "Status"] = 'In Progress Today'
                    df.at[idx, "Final Action"] = "Sent Email"
                    df.at[idx, "Assigned To"] = 'Adam'

                    # Save to Excel
                    save_to_checkpoint(df, excel_path)

                if CaseClosingCode == "Need Third Action" or CaseClosingCode == "Skipped":
                    # Determine status based on code
                    new_status = "In Progress" if CaseClosingCode == "Need Third Action" else "Skipped"

                    # Update DataFrame
                    df.at[idx, "Status"] = new_status
                    df.at[idx, "Final Action"] = excelCaseClosingCode(CaseClosingCode)
                    df.at[idx, "Assigned To"] = 'Adam'

                    # Save to Excel
                    save_to_checkpoint(df, excel_path)

                    pointer += 1
                    continue
                
                
                if 'called' in str(CaseClosingCode).lower():
                    df.at[idx, "Action 3"] = 'Called the Customer'

                df.at[idx, "Final Action"] = excelCaseClosingCode(CaseClosingCode)
                df.at[idx, "Assigned To"] = 'Adam'
                df.at[idx, "Status"] = 'Closed'
                save_to_checkpoint(df, excel_path)
    
                # in_progress_cases_remaining calc is now dynamic based on where we are
                print(f"[INFO] Processed case. Moving to next.")
                case_counter += 1
                pointer += 1 # Move next
                if case_counter % refresh_interval == 0:
                    keep_driver_alive(driver)
                    time.sleep(5)  # wait for refresh to complete

        except Exception as e:
            print(f"[ERROR] Exception processing case {case_number if 'case_number' in locals() else 'unknown'}: ")
            pointer += 1
            continue       


    print("All done for today 👌")
    
    # --- FINAL SYNC TO MAIN EXCEL ---
    print("\n[INFO] syncing changes to main Excel file...")
    try:
        # Re-save dataframe to main Excel file
        save_excel_safely(df, excel_path, sheet_name="Adam's Cases")
        print("[INFO] Main Excel file updated successfully.")
        
        # Clean up checkpoint if successful
        try:
            checkpoint_file = os.path.join(os.path.dirname(excel_path), f"CHECKPOINT_{os.path.splitext(os.path.basename(excel_path))[0]}.csv")
            if os.path.exists(checkpoint_file):
                os.remove(checkpoint_file)
        except:
             pass
             
    except Exception as e:
        print(f"[CRITICAL] Failed to save final changes to Excel: {e}")
        print(f"[INFO] Your progress is saved in the CHECKPOINT csv file in the same folder.")
    # --------------------------------

    # --- Ask to start Companies Bulk Processing ---
    try:
        companies_choice = show_choice_dialog(
            "Standard Cases Done ✅",
            "All standard cases are finished!\nWould you like to start Companies Bulk Processing now?",
            "Yes, Start Companies",
            "No, I'm Done"
        )
        if companies_choice == "Yes, Start Companies":
            print("[INFO] Starting Companies Bulk Processing Mode...")
            companies_processor = Companies(driver, excel_path)
            companies_processor.process_companies()
            print("[INFO] Companies processing complete.")
        else:
            print("[INFO] Skipping Companies processing.")
    except Exception as e:
        print(f"[WARN] Companies prompt failed: {e}")
    # -----------------------------------------------

    try:
        wait_until_time(23, 59)
    except Exception as e:
        print(f"[WARN] wait_until_time check failed or was interrupted: ")
    finally:
        disable_windows_inhibit()
        driver.quit()