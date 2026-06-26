#import pytest
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException, NoAlertPresentException, UnexpectedAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from datetime import datetime, timedelta, timezone
import tkinter as tk
from openpyxl import load_workbook
import time
import json
import os
import pandas as pd
import pyautogui
import traceback
import ctypes
import shutil
import pyaudio
import wave
import struct
import math
import imageio_ffmpeg
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QDialog, QLabel, QPushButton, QVBoxLayout,
    QGridLayout, QInputDialog, QWidget, QProgressBar,
    QGroupBox, QHBoxLayout
)
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtCore import Qt, QTimer
import sys
try:
    import zoneinfo
except ImportError:
    try:
        from backports import zoneinfo
    except ImportError:
        zoneinfo = None

try:
    import pytz
except ImportError:
    pytz = None

# OS Inhibit constants
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ES_DISPLAY_REQUIRED = 0x00000002
_inhibit_active = False

# ART Team Variables
SMSText = ("Hello {CX_Name} , \n\nPlease reply with 1, 2, or 3 regarding your recent Lenovo Service for serial number: {case_number} . \n\n1. Issue Resolved\n2. Need Assistance\n3. Stop Text Messages\n\nIf there is no reply, we will contact you by phone within 24 hours between 8:00 AM - 6:00 PM local time.")
today_str = datetime.now().strftime("%b %d, %Y")
AgentName = "Adam Maged"

STATE_TIMEZONE_MAP = {
    'CT': 'America/New_York', 'DE': 'America/New_York', 'DC': 'America/New_York', 'FL': 'America/New_York', 
    'GA': 'America/New_York', 'IN': 'America/Indianapolis', 'KY': 'America/New_York', 'ME': 'America/New_York', 
    'MD': 'America/New_York', 'MA': 'America/New_York', 'MI': 'America/Detroit', 'NH': 'America/New_York', 
    'NJ': 'America/New_York', 'NY': 'America/New_York', 'NC': 'America/New_York', 'OH': 'America/New_York', 
    'PA': 'America/New_York', 'RI': 'America/New_York', 'SC': 'America/New_York', 'TN': 'America/New_York', 
    'VT': 'America/New_York', 'VA': 'America/New_York', 'WV': 'America/New_York',
    'Connecticut': 'America/New_York', 'Delaware': 'America/New_York', 'District of Columbia': 'America/New_York', 
    'Florida': 'America/New_York', 'Georgia': 'America/New_York', 'Indiana': 'America/Indianapolis', 
    'Kentucky': 'America/New_York', 'Maine': 'America/New_York', 'Maryland': 'America/New_York', 
    'Massachusetts': 'America/New_York', 'Michigan': 'America/Detroit', 'New Hampshire': 'America/New_York', 
    'New Jersey': 'America/New_York', 'New York': 'America/New_York', 'North Carolina': 'America/New_York', 
    'Ohio': 'America/New_York', 'Pennsylvania': 'America/New_York', 'Rhode Island': 'America/New_York', 
    'South Carolina': 'America/New_York', 'Tennessee': 'America/New_York', 'Vermont': 'America/New_York', 
    'Virginia': 'America/New_York', 'West Virginia': 'America/New_York',
    'AL': 'America/Chicago', 'AR': 'America/Chicago', 'IL': 'America/Chicago', 'IA': 'America/Chicago', 
    'KS': 'America/Chicago', 'LA': 'America/Chicago', 'MN': 'America/Chicago', 'MS': 'America/Chicago', 
    'MO': 'America/Chicago', 'NE': 'America/Chicago', 'ND': 'America/Chicago', 'OK': 'America/Chicago', 
    'SD': 'America/Chicago', 'TX': 'America/Chicago', 'WI': 'America/Chicago',
    'Alabama': 'America/Chicago', 'Arkansas': 'America/Chicago', 'Illinois': 'America/Chicago', 
    'Iowa': 'America/Chicago', 'Kansas': 'America/Chicago', 'Louisiana': 'America/Chicago', 
    'Minnesota': 'America/Chicago', 'Mississippi': 'America/Chicago', 'Missouri': 'America/Chicago', 
    'Nebraska': 'America/Chicago', 'North Dakota': 'America/Chicago', 'Oklahoma': 'America/Chicago', 
    'South Dakota': 'America/Chicago', 'Texas': 'America/Chicago', 'Wisconsin': 'America/Chicago',
    'AZ': 'America/Phoenix', 'CO': 'America/Denver', 'ID': 'America/Denver', 'MT': 'America/Denver', 
    'NM': 'America/Denver', 'UT': 'America/Denver', 'WY': 'America/Denver',
    'Arizona': 'America/Phoenix', 'Colorado': 'America/Denver', 'Idaho': 'America/Denver', 
    'Montana': 'America/Denver', 'New Mexico': 'America/Denver', 'Utah': 'America/Denver', 
    'Wyoming': 'America/Denver',
    'CA': 'America/Los_Angeles', 'NV': 'America/Los_Angeles', 'OR': 'America/Los_Angeles', 'WA': 'America/Los_Angeles',
    'California': 'America/Los_Angeles', 'Nevada': 'America/Los_Angeles', 'Oregon': 'America/Los_Angeles', 
    'Washington': 'America/Los_Angeles',
    'AK': 'America/Anchorage', 'Alaska': 'America/Anchorage',
    'HI': 'Pacific/Honolulu', 'Hawaii': 'Pacific/Honolulu',
    'ON': 'America/Toronto', 'Ontario': 'America/Toronto',
    'QC': 'America/Montreal', 'Quebec': 'America/Montreal',
    'BC': 'America/Vancouver', 'British Columbia': 'America/Vancouver',
    'AB': 'America/Edmonton', 'Alberta': 'America/Edmonton',
    'MB': 'America/Winnipeg', 'Manitoba': 'America/Winnipeg',
    'SK': 'America/Regina', 'Saskatchewan': 'America/Regina',
    'NS': 'America/Halifax', 'Nova Scotia': 'America/Halifax',
}

CaseNote = f"Date: {today_str}\nQueue: ART Project - Follow up \nAgent: {AgentName} \nAction: Sent SMS // Sent Email \n \n ------------------------"
CaseEmailOnSite_Depot = (
    " Hello {CX_Name}\n\n"
    "I hope you are doing well.\n\n"
    "I hope your device of Serial Number: {serial_val} is performing well after its recent repair.\n\n"
    "To ensure everything is working as expected, please reply with one of the following options:\n\n"
    "1 for Issue Resolved — Everything is working properly.\n"
    "2 for Need Assistance — Please include details of any ongoing issues.\n"
    "3 for STOP — To stop receiving follow-up messages.\n\n"
    "If we do not receive a response, a member of our team may follow up with a phone call on the next business day (Monday—Friday) between\n"
    "8:00 AM and 6:00 PM local time.\n\n"
    "Thank you for choosing Lenovo Services.\n\n"
    "We appreciate your business and are here to support you.\n\n"
    "Thanks and Regards,\n"
    "{AgentName}\n"
    "NA Lenovo PC Assurance Resolution Team"
)
CaseEmailCRU = (
    " Hello {CX_Name}\n\n"
    "I hope you are doing well.\n\n"
    "Regarding the device of Serial number:  {serial_val}\n\n"
    "I am contacting you to verify that the Lenovo replacement part is functioning properly and performing to your expectations.\n\n"
    "To ensure everything is working as expected, please reply with one of the following options:\n\n"
    "1 for Issue Resolved — Everything is working properly.\n"
    "2 for Need Assistance — Please include details of any ongoing issues.\n"
    "3 for STOP — To stop receiving follow-up messages.\n\n"
    "If we do not receive a response, a member of our team may follow up with a phone call on the next business day (Monday—Friday) between\n"
    "8:00 AM and 6:00 PM local time.\n\n"
    "Thank you for choosing Lenovo Services.\n\n"
    "We appreciate your business and are here to support you.\n\n"
    "Thanks and Regards,\n"
    "{AgentName}\n"
    "NA Lenovo PC Assurance Resolution Team"
)

def _ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass

def create_backup(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"[WARN] Backup failed: Source file not found: {file_path}")
            return
        backup_dir = os.path.join(os.path.dirname(file_path), 'Backups')
        _ensure_dir(backup_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        backup_filename = f"{name}_{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(file_path, backup_path)
        print(f"[INFO] Backup created: {backup_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create backup: ")

def save_excel_safely(df, file_path, sheet_name="Sheet1"):
    temp_path = None
    try:
        dir_name = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        temp_path = os.path.join(dir_name, f"~temp_{file_name}")
        if os.path.exists(file_path):
            try:
                shutil.copy2(file_path, temp_path)
                with pd.ExcelWriter(temp_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception as e:
                print(f"[WARN] Failed to preserve sheets, falling back to overwrite: {e}")
                df.to_excel(temp_path, sheet_name=sheet_name, index=False)
        else:
             df.to_excel(temp_path, sheet_name=sheet_name, index=False)
        
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
             print(f"[ERROR] Temp file write failed (empty or missing): {temp_path}")
             return
        max_retries = 3
        for i in range(max_retries):
            try:
                if os.path.exists(file_path):
                    os.replace(temp_path, file_path)
                else:
                    os.rename(temp_path, file_path)
                break
            except OSError as e:
                if i < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    try:
                         if os.path.exists(file_path):
                             os.remove(file_path)
                         os.rename(temp_path, file_path)
                    except Exception as final_e:
                        print(f"[ERROR] Failed to replace Excel file after retries: {final_e}")
                        raise final_e
    except Exception as e:
        print(f"[ERROR] Failed to save Excel safely: {e}")
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path) 
            except: pass

def handle_genesys_popup(driver):
    try:
        alert = driver.switch_to.alert
        text = alert.text
        if "Genesys WWE" in text and "Integration Enabled" in text:
            print(f"[INFO] Handling Genesys popup: {text}")
            alert.accept()
            return True
    except NoAlertPresentException:
        pass
    except Exception as e:
        print(f"[DEBUG] Error checking for alert: {e}")
    return False

def check_driver_alive(driver):
    try:
        _ = driver.current_url
        return True
    except (WebDriverException, AttributeError) as e:
        print("\n" + "="*60)
        print("[CRITICAL] Browser has been closed!")
        print("[INFO] Terminating script...")
        print("="*60)
        sys.exit(0)

def safe_find(driver, by, locator, timeout=1, clickable=False, retries=3, poll=0.5):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            handle_genesys_popup(driver)
            wait = WebDriverWait(driver, timeout)
            if clickable:
                el = wait.until(EC.element_to_be_clickable((by, locator)))
            else:
                el = wait.until(EC.presence_of_element_located((by, locator)))
            return el
        except (UnexpectedAlertPresentException, Exception) as e:
            if handle_genesys_popup(driver):
                print(f"[INFO] Genesys popup dismissed in safe_find, retrying... ({attempt}/{retries})")
                time.sleep(poll)
                continue
            last_exc = e
            # print(f"[WARN] safe_find attempt {attempt}/{retries} for {locator} failed: {e}")
            time.sleep(poll)

    _ensure_dir('errors')
    safe_name = locator.replace('/', '_').replace(' ', '_')[:100]
    img_path = os.path.join('errors', f'failure_{safe_name}.png')
    try:
        driver.save_screenshot(img_path)
    except Exception:
        pass
    return None

def click_safe(driver, by, locator, timeout=1, retries=3, poll=0.5):
    el = safe_find(driver, by, locator, timeout=timeout, clickable=True, retries=retries, poll=poll)
    if not el:
        return False
    try:
        el.click()
        return True
    except (UnexpectedAlertPresentException, Exception) as e:
        if handle_genesys_popup(driver):
            print(f"[INFO] Genesys popup dismissed in click_safe, retrying click...")
            try:
                el.click()
                return True
            except Exception:
                pass
        print(f"[ERROR] click_safe failed on {locator}: ")
        return False

def send_keys_safe(driver, by, locator, value, timeout=1, retries=3, poll=0.5, enter=False):
    el = safe_find(driver, by, locator, timeout=timeout, clickable=True, retries=retries, poll=poll)
    if not el:
        return False
    try:
        try:
            el.clear()
        except Exception:
            pass
        el.send_keys(value)
        if enter:
            el.send_keys(Keys.ENTER)
        return True
    except Exception as e:
        print(f"[ERROR] send_keys_safe failed on {locator}: ")
        return False

def switch_to_window_safe(driver, target_index, max_retries=5, wait_time=0.5):
    for attempt in range(1, max_retries + 1):
        try:
            handles = driver.window_handles
            if target_index >= len(handles):
                print(f"[WARN] Window index {target_index} not available (only {len(handles)} windows). Attempt {attempt}/{max_retries}")
                time.sleep(wait_time)
                continue
            driver.switch_to.window(handles[target_index])
            time.sleep(wait_time)
            _ = driver.current_url
            print(f"[INFO] Successfully switched to window index {target_index}")
            return True
        except (UnexpectedAlertPresentException, Exception) as e:
            if handle_genesys_popup(driver):
                print(f"[INFO] Genesys popup dismissed in switch_to_window_safe. Retrying...")
                time.sleep(wait_time)
                continue
            print(f"[WARN] Failed to switch to window index {target_index} (attempt {attempt}/{max_retries}): {str(e)}")
            time.sleep(wait_time)
    print(f"[ERROR] Failed to switch to window index {target_index} after {max_retries} attempts")
    return False

def enable_windows_inhibit():
    global _inhibit_active
    try:
        if platform.system().lower().startswith('win'):
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED)
            _inhibit_active = True
            print("[INFO] Windows sleep/display inhibit enabled")
    except Exception as e:
        print(f"[WARN] Failed to enable Windows inhibit: ")

def disable_windows_inhibit():
    global _inhibit_active
    try:
        if _inhibit_active and platform.system().lower().startswith('win'):
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            _inhibit_active = False
            print("[INFO] Windows sleep/display inhibit disabled")
    except Exception as e:
        print(f"[WARN] Failed to disable Windows inhibit: ")
def smart_switch_to_window(driver, target_type, max_retries=5, wait_time=0.5):
    """
    Safely switch to a window based on URL content.
    
    Args:
        driver: Selenium WebDriver
        target_type: 'dialer' or 'crm'
    """
    # User provided specifics
    check_str = ""
    if target_type == 'dialer':
        check_str = "104.232.254.43" # Part of IP from user
    elif target_type == 'crm':
        check_str = "lenovo-plrs-prod.crm5.dynamics.com"
    else:
        return False
        
    for attempt in range(1, max_retries + 1):
        try:
            handles = driver.window_handles
            current_handle = driver.current_window_handle
            
            # First check if we are already there
            try:
                if check_str in driver.current_url:
                    print(f"[INFO] Already on {target_type} window.")
                    return True
            except: pass

            found_handle = None
            
            # Iterate and find
            for h in handles:
                try:
                    driver.switch_to.window(h)
                    url = driver.current_url
                    if check_str in url:
                        found_handle = h
                        break
                except Exception:
                    continue
            
            if found_handle:
                print(f"[INFO] Successfully switched to {target_type} window")
                return True
            else:
                print(f"[WARN] Could not find window matching '{check_str}'. Attempt {attempt}/{max_retries}")
                
        except (UnexpectedAlertPresentException, Exception) as e:
            if handle_genesys_popup(driver):
                 time.sleep(wait_time)
                 continue
            print(f"[WARN] Error in smart switch: {e}")
            
        time.sleep(wait_time)
        
    print(f"[ERROR] Failed to find/switch to {target_type} window")
    return False

def perform_call_flow(driver):
    try:
        # Read mobile phone
        mobile_input = safe_find(driver, By.XPATH, "//input[@type='tel' and @aria-label='Mobile Phone']", timeout=1, retries=7)
        if mobile_input:
            mobile_value = (mobile_input.get_attribute('value') or '').strip()
            if not mobile_value:
                # fallback to title if value not populated
                mobile_value = (mobile_input.get_attribute('title') or '').strip()
        else:
            mobile_value = ''

        # Prepare dial number: replace leading '+' with '9'
        if mobile_value:
            number_core = mobile_value.lstrip('+')
            dialed_number = f"9{number_core}"
        else:
            print("[WARN] No mobile phone value found to dial")
            return (None)
        
        # Switch to the dialer tab
        if not smart_switch_to_window(driver, 'dialer', max_retries=5):
            print("[ERROR] Failed to switch to dialer tab")
            return (None)
        
        # Click the "mark done" button
        click_safe(driver, By.XPATH, '//span[contains(@class,"wwe-sprite-mark-done")]', timeout=1, retries=1)
        
        # Enter the dialed number
        send_keys_safe(driver, By.ID, 'wweTeamCommunicatorDialerField', dialed_number, timeout=1, retries=5, poll=0.5, enter=True)
        
        # Switch back to CRM tab
        if not smart_switch_to_window(driver, 'crm', max_retries=5):
            print("[ERROR] Failed to switch back to CRM tab")
            return (None)
        
        print("[INFO] Call flow completed successfully")
        
    except Exception as e:
        print(f"[WARN] perform_call_flow encountered an error: {str(e)}")

def get_case_closing_code(case_number, current_index, total_count, can_go_back=False, state_province=""):

    """Creates a modal popup and returns the selected case closing code."""
    closing_code = {"value": None, "add_note": False}

    class Popup(QDialog):
        def __init__(self, state_province=""):
            super().__init__()
            self.setWindowTitle("Case Reviewer")
            self.resize(400, 450)

            # --- Main layout ---
            main_layout = QVBoxLayout(self)

            # Progress Bar
            progress = QProgressBar()
            progress.setRange(0, total_count)
            progress.setValue(current_index)
            progress.setFormat(f"Case {current_index}/{total_count} (%p%)")
            main_layout.addWidget(progress)

            # Navigation Buttons (Next / Previous)
            nav_layout = QHBoxLayout()
            
            self.btn_prev = QPushButton("Previous Case")
            self.btn_prev.setEnabled(can_go_back) # Only enable if we can go back
            self.btn_prev.clicked.connect(lambda: self.close_with_nav("NAV_PREV"))
            nav_layout.addWidget(self.btn_prev)

            self.btn_next = QPushButton("Next Case")
            self.btn_next.clicked.connect(lambda: self.close_with_nav("NAV_NEXT")) # Or some skip code
            nav_layout.addWidget(self.btn_next)

            main_layout.addLayout(nav_layout)


            label = QLabel(f"Select Action for Case: {case_number}")
            label.setStyleSheet("font-family: Arial; font-size: 14px; font-weight: bold; margin-top: 10px;")
            main_layout.addWidget(label)
            
            # --- Display Time if State Provided ---
            if state_province:
                time_str = get_current_time_for_state(state_province)
                if time_str:
                    time_lbl = QLabel(f"Local Time in {state_province}: {time_str}")
                    time_lbl.setStyleSheet("font-size: 12px; color: White; margin-bottom: 5px;font-weight: bold")
                    main_layout.addWidget(time_lbl)
                else:
                    time_lbl = QLabel(f"State: {state_province} (Time Unknown)")
                    time_lbl.setStyleSheet("font-size: 12px; color: White; margin-bottom: 5px;font-weight: italic")
                    main_layout.addWidget(time_lbl)


            # --- Button Groups ---
            def create_button_group(title, buttons):
                group = QGroupBox(title)
                layout = QGridLayout()
                for i, (label_text, code) in enumerate(buttons):
                    btn = QPushButton(label_text)
                    btn.setMinimumHeight(35)
                    btn.clicked.connect(lambda checked=False, c=code: set_code_and_close(c))
                    layout.addWidget(btn, i // 2, i % 2)
                group.setLayout(layout)
                return group

            # --- Define Categories ---
            resolution_buttons = [
                ("Fixed", "Issue Resolved"),
                ("Issue Not Fixed", "Issue Not Fixed"),
                ("Not Reached", "Customer Not Reached"),
                ("Not Yet Tested", "Machine Not Yet Tested"),
                ("DND", "DND"),
                ("Escalated", "Escalated"),
            ]
            
        
            action_buttons = [
                ("Send SMS", "Send SMS"),
                ("Send Email", "Send Email"),
                ("Send SMS and Email", "Send SMS and Email"),
                ("Call the Customer", "Call the Customer"),
            ]

            # --- Inner helper functions ---
            def set_code_and_close(code):
                closing_code["value"] = code
                try:
                    closing_code["add_note"] = bool(self.add_note_checkbox.isChecked())
                except Exception:
                    closing_code["add_note"] = False
                self.accept()

            def ask_other_code():
                try:
                    text, ok = QInputDialog.getText(self, "Other Closing Code", "Enter custom closing code:")
                    if ok and text.strip():
                        set_code_and_close(text.strip())
                except Exception:
                    pass  # ignore and keep popup open

            # --- Add Groups to Main Layout ---
            main_layout.addWidget(create_button_group("Resolution Status", resolution_buttons))
            main_layout.addWidget(create_button_group("Communication Actions", action_buttons))

            # --- "Others" button ---
            other_btn = QPushButton("Others")
            other_btn.setMinimumHeight(40)
            other_btn.clicked.connect(ask_other_code)
            main_layout.addWidget(other_btn)

            # --- Add Case Note checkbox ---
            try:
                self.add_note_checkbox = QCheckBox("Add Case Note")
                self.add_note_checkbox.setChecked(False)
                main_layout.addWidget(self.add_note_checkbox)
            except Exception:
                pass

        def close_with_nav(self, nav_code):
            closing_code["value"] = nav_code
            closing_code["add_note"] = False
            self.accept()

    # --- Ensure QApplication exists ---
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    popup = Popup(state_province)
    popup.exec()

    if created_app:
        app.quit()

    return closing_code.get("value"), bool(closing_code.get("add_note", False))


# --- Audio Helper Functions ---
def convert_to_wav(input_path, target_rate=44100, target_channels=2):
    """Convert any audio file to 16-bit PCM stereo WAV using ffmpeg.
    target_rate and target_channels are queried from the output device first,
    so the resulting WAV always matches exactly what the device expects.
    """
    try:
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        output_path = os.path.splitext(input_path)[0] + "_temp_conv_eticket.wav"
    
        cmd = [
            ffmpeg_exe,
            '-y',                              # overwrite output
            '-i', input_path,
            '-acodec', 'pcm_s16le',            # 16-bit PCM
            '-ar', str(target_rate),           # match device sample rate
            '-ac', str(target_channels),       # match device channel count (stereo)
            output_path
        ]
        
        # Hide console window on Windows
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        subprocess.check_call(cmd, startupinfo=startupinfo, stderr=subprocess.DEVNULL)
        print(f"[INFO] Converted audio → {target_channels}ch {target_rate}Hz WAV: {output_path}")
        return output_path
    except Exception as e:
        print(f"[ERROR] ffmpeg conversion failed: {e}")
        return None

def get_audio_device_index(p, name_fragment, is_input=False):
    """Find pyaudio device index by name fragment. Logs all devices on failure."""
    try:
        count = p.get_device_count()
        index = None
        all_names = []
        for i in range(count):
            dev_info = p.get_device_info_by_index(i)
            dev_name = dev_info.get('name', '')
            channels = dev_info.get('maxInputChannels') if is_input else dev_info.get('maxOutputChannels')
            all_names.append(f"  [{i}] {dev_name} (ch={channels}{'  <INPUT>' if is_input else '  <OUTPUT>'})")    
            if channels > 0 and name_fragment.lower() in dev_name.lower():
                index = i
                dev_rate  = int(dev_info.get('defaultSampleRate', 0))
                print(f"[INFO] Found Audio Device: {dev_name} (ID: {i}, default_rate={dev_rate}Hz, channels={channels})")
                break
        if index is None:
            print(f"[WARN] Device '{name_fragment}' not found. Available devices:")
            for line in all_names:
                print(line)
        return index
    except Exception as e:
        print(f"[ERROR] Failed to list audio devices: {e}")
        return None

def play_audio_to_device(file_path, device_name_fragment="CABLE Input"):
    """
    Play a WAV/M4A/MP3 file directly into a specific output device.
    Queries the device's default sample rate first, then converts the audio
    to exactly that rate + stereo so pyaudio never gets a format mismatch.
    """
    p = pyaudio.PyAudio()
    stream = None
    wf = None
    temp_wav = None

    try:
        # 1. Find the output device
        device_index = get_audio_device_index(p, device_name_fragment, is_input=False)
        if device_index is None:
            print(f"[ERROR] Output device '{device_name_fragment}' not found.")
            p.terminate()
            return False

        # 2. Read device capabilities BEFORE converting audio
        dev_info     = p.get_device_info_by_index(device_index)
        dev_channels = min(int(dev_info.get('maxOutputChannels', 2)), 2)  # cap at stereo
        dev_rate     = int(dev_info.get('defaultSampleRate', 44100))
        print(f"[INFO] Device #{device_index} — default {dev_rate}Hz, max {dev_info.get('maxOutputChannels')}ch")

        # 3. Locate file
        if not os.path.exists(file_path):
            print(f"[ERROR] Audio file not found: {file_path}")
            p.terminate()
            return False

        # 4. Convert to WAV matching the device's exact rate & channels
        play_path = file_path
        if not file_path.lower().endswith('.wav'):
            temp_wav = convert_to_wav(file_path,
                                      target_rate=dev_rate,
                                      target_channels=dev_channels)
            if temp_wav:
                play_path = temp_wav
            else:
                print(f"[ERROR] Audio conversion failed, cannot inject.")
                p.terminate()
                return False

        # 5. Open WAV and confirm it matches device
        wf = wave.open(play_path, 'rb')
        wav_channels = wf.getnchannels()
        wav_rate     = wf.getframerate()
        wav_width    = wf.getsampwidth()
        wav_format   = p.get_format_from_width(wav_width)
        print(f"[INFO] WAV — channels={wav_channels}, rate={wav_rate}Hz, width={wav_width}bytes")

        # 6. Open pyaudio stream
        print(f"[INFO] Injecting audio to device #{device_index} ({device_name_fragment})...")
        stream = p.open(
            format=wav_format,
            channels=wav_channels,
            rate=wav_rate,
            output=True,
            output_device_index=device_index,
            frames_per_buffer=1024
        )

        # 7. Stream in chunks, keeping GUI alive
        chunk = 1024
        data = wf.readframes(chunk)
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(chunk)
            QApplication.processEvents()

        stream.stop_stream()
        print("[INFO] Audio injection complete.")
        return True

    except Exception as e:
        print(f"[ERROR] Audio injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except: pass
        if p:
            p.terminate()
        if wf:
            try: wf.close()
            except: pass
        if temp_wav and os.path.exists(temp_wav):
            try: os.remove(temp_wav)
            except: pass

def get_call_closing_code(driver=None):

    """Creates a modal popup and returns the selected case closing code."""
    closing_code = {"value": None, "add_note": False}

    class Popup(QDialog):
        def __init__(self, driver_instance):
            super().__init__()
            self.driver = driver_instance
            self.setWindowTitle("Case Reviewer")
            self.resize(300, 270) 

            # --- Main layout ---
            main_layout = QVBoxLayout(self)

            label = QLabel("Select Call Closing Code")
            label.setStyleSheet("font-family: Bold Arial; font-size: 14px;")
            main_layout.addWidget(label)

            # --- Button grid ---
            btn_frame = QWidget()
            grid = QGridLayout(btn_frame)
            grid.setSpacing(10)
            grid.setColumnStretch(0, 1)
            grid.setColumnStretch(1, 1)

            buttons = [
                ("Resolved", "Issue Resolved"),
                ("Issue Not Fixed", "Issue Not Fixed"),
                ("Not Reached", "Customer Not Reached"),
                ("Not Yet Tested", "Customer Claims that the Machine Not Yet Tested")
            ]

            # --- Inner helper functions ---
            def set_code_and_close(code):
                closing_code["value"] = code
                try:
                    closing_code["add_note"] = bool(self.add_note_checkbox.isChecked())
                except Exception:
                    closing_code["add_note"] = False
                self.accept()

            def ask_other_code():
                try:
                    text, ok = QInputDialog.getText(self, "Other Closing Code", "Enter custom closing code:")
                    if ok and text.strip():
                        set_code_and_close(text.strip())
                except Exception:
                    pass  # ignore and keep popup open
                    
            def play_voicemail_handler():
                # Plays audio and then automates hangup/closing
                QApplication.processEvents()
                
                audio_path = r"C:\Users\AdamMaged\OneDrive - IBM\Documents\Sound Recordings\ART General II.m4a"
                
                # Robustness: Check for dummy/default if missing
                if not os.path.exists(audio_path):
                     print(f"[WARN] Audio file not found at {audio_path}")

                # Attempt audio injection
                success = play_audio_to_device(audio_path, "CABLE Input")
                
                if not success:
                    print("[WARN] Audio injection FAILED (or file missing). Proceeding with hangup anyway.")
                else:
                    print("[INFO] Audio Injection Complete")
                    
                # Always proceed to hangup sequence
                # 1. Switch to Dialer and Hangup
                if not smart_switch_to_window(self.driver, 'dialer', max_retries=3):
                        print("[WARN] Could not switch to dialer for hangup")
                
                # XPath for end call
                hangup_xpath = '//button[contains(@id,"HangupButton")]/span'
                click_safe(self.driver, By.XPATH, hangup_xpath, timeout=1, retries=3)
                    
                # 2. Switch back to CRM and click OK
                if not smart_switch_to_window(self.driver, 'crm', max_retries=3):
                        print("[WARN] Could not switch back to CRM")
                    
                click_safe(
                    self.driver,
                    By.XPATH,
                    "//button[contains(@id,'okButton_')]/div",
                    timeout=1,
                    retries=2,
                )
                # Force add_note to True
                closing_code["value"] = "Customer Not Reached"
                closing_code["add_note"] = True
                self.accept()

            # --- Add buttons to grid ---
            # Wait, `buttons` was defined at line 733.
            # `grid` was defined at line 728.
            # `btn_frame` was defined at line 727.
            
            for idx, (label_text, code) in enumerate(buttons):
                r = idx // 2
                c = idx % 2
                btn = QPushButton(label_text)
                btn.setMinimumHeight(40)
                # Use lambda to capture `code` correctly in loop
                btn.clicked.connect(lambda checked=False, c=code: set_code_and_close(c))
                grid.addWidget(btn, r, c)

             # Add the button frame to the main layout!
            main_layout.addWidget(btn_frame)


            # --- "Others" button ---
            other_btn = QPushButton("Others")
            other_btn.setMinimumHeight(40)
            other_btn.clicked.connect(ask_other_code)
            main_layout.addWidget(other_btn)

            # --- "Play Voicemail" button ---
            self.play_btn = QPushButton("Play Voicemail")
            self.play_btn.setMinimumHeight(40)
            self.play_btn.setStyleSheet("background-color: #d1e7dd; color: #0f5132; font-weight: bold;") # Light green
            self.play_btn.clicked.connect(play_voicemail_handler)
            main_layout.addWidget(self.play_btn)

            # --- Add Case Note checkbox ---
            try:
                self.add_note_checkbox = QCheckBox("Add Case Note")
                self.add_note_checkbox.setChecked(False)
                main_layout.addWidget(self.add_note_checkbox)
            except Exception:
                pass

    # --- Ensure QApplication exists ---
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True

    popup = Popup(driver)
    popup.exec()

    if created_app:
        app.quit()

    return closing_code.get("value"), bool(closing_code.get("add_note", False))


def Company_solution_provided_check_and_skip(driver, case_number, df, excel_path):
    # Verify the case has 'Solution Provided' in the header. The headerControlsList_<n> id suffix is variable,
    # so use starts-with on the id. If not present, mark the case as skipped in Excel and progress and continue.
    #<div role="presentation" class="pa-ro pa-gi pa-dk pa-rq pa-ve pa-vf pa-vg pa-dl flexbox">Solution Provided</div>
    #xpath=//div[@id='headerControlsList_2']/div/div/div Solution Provided
    solutionProv_case = True
    case_status_xpath = "//div[contains(@id,'headerControlsList')]/div[3]/div/div"
    case_status_el = safe_find(driver, By.XPATH, case_status_xpath, timeout=1, retries=6)
    if case_status_el:
        case_status = case_status_el.text.strip()
        if case_status.lower() == "solution provided" or case_status.lower() == "closed":
            solutionProv_case = True
        else:
            solutionProv_case = False
    else:
        solutionProv_case = False

    return solutionProv_case

class ConfirmCallDialog(QDialog):
    def __init__(self, company_name, email):
        super().__init__()
        self.setWindowTitle("Confirm Call Flow")
        self.resize(300, 150)
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"Processing Company: {company_name}"))
        layout.addWidget(QLabel(f"Email: {email}"))
        layout.addWidget(QLabel("BulK Email sent. Do you want to call the customer?"))

        btn_layout = QHBoxLayout()
        self.call_btn = QPushButton("Call Customer")
        self.call_btn.clicked.connect(self.accept) # Returns 1 (Accepted)
        self.skip_btn = QPushButton("Skip Call")
        self.skip_btn.clicked.connect(self.reject) # Returns 0 (Rejected)

        btn_layout.addWidget(self.call_btn)
        btn_layout.addWidget(self.skip_btn)
        layout.addLayout(btn_layout)




def cases_needing_processing_by_closing(df, case_col='case_number', closing_col='CaseClosingCode'):

    try:
        if case_col not in df.columns:
            return []
        if closing_col not in df.columns:
            return df[case_col].dropna().astype(str).tolist()

        def _emptyish(v):
            try:
                s = str(v).strip()
                return (s == '' or s.lower() == 'nan')
            except Exception:
                return True

        mask = df[closing_col].apply(_emptyish)
        return df.loc[mask, case_col].dropna().astype(str).tolist()
    except Exception as e:
        print(f"[WARN] cases_needing_processing_by_closing failed: ")
        return []

def DND_CX(driver, case_number):
    # Contact Card
    contact_xpath = "//a[contains(@id,'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id,'sec_tab_contact-associatedEntityRecordName')]"
    if not click_safe(driver, By.XPATH, contact_xpath, timeout=1, retries=5):
        print(f"[WARN] Contact card not found for {case_number}")
    else:
        # click on edit button
        edit_xpath = "//button[contains(@id,'contact|NoRelationship|Form|lvidg.contact.TimeTrackingCheckOut.Command') and contains(@id,'-button')]"
        click_safe(driver, By.XPATH, edit_xpath, timeout=1, retries=5)

        # click on Details Tab
        details_xpath = "//li[contains(@id,'tab4') and @title='Details']"
        click_safe(driver, By.XPATH, details_xpath, timeout=1, retries=5)
        # click on Communication Preferences (Do Not Disturb)
        comm_pref_xpath = "//div[contains(@id,'lvidg_hasdonotdisturbf9a8a302')]/div[3]/div/div"
        click_safe(driver, By.XPATH, comm_pref_xpath, timeout=1, retries=5)

        time.sleep(2)

        # Save and Close
        save_xpath = "//button[contains(@id,'contact|NoRelationship|Form|lvidg.contact.TimeTrackingCheckIn.Command') and contains(@id,'button')]"
        click_safe(driver, By.XPATH, save_xpath, timeout=1, retries=5)    

def Chrome_ART_Profile():
    chrome_options = Options()
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    
    user_data_dir = os.environ.get('CHROME_USER_DATA_DIR') or os.path.join(os.path.expanduser('~'), '@')
    profile_dir = os.environ.get('CHROME_PROFILE_DIR') or 'Default'
    if user_data_dir and os.path.exists(user_data_dir):
        try:
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument(f'--profile-directory={profile_dir}')
            print(f"[INFO] Using Chrome profile: {user_data_dir}")
        except Exception as e:
            print(f"[WARN] Failed to set Chrome profile: ")
    else:
        try:
            os.makedirs(user_data_dir, exist_ok=True)
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
            chrome_options.add_argument(f'--profile-directory={profile_dir}')
            print(f"[INFO] Created new Chrome profile at: {user_data_dir}")
        except Exception as e:
            print(f"[WARN] Failed to create Chrome profile: ")
    return chrome_options

def send_SMS(driver, sms_text):

    sms_sent = False

    # Wait for plus sign and open menu (Send SMS)
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id, 'notescontrol-action_bar_add_command')]",
        timeout=1,
        retries=5,
    )

    # SMS Button
    click_SMS_button = click_safe(
        driver,
        By.XPATH,
        "//li[contains(@id, 'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id, 'notescontrol-createNewRecord_flyoutMenuItem_lvidg_sms')]",
        timeout=1,
        retries=5,
    )

    # If SMS Button not found, try again once
    if not click_SMS_button:
        # open menu (Send SMS)
        click_safe(
            driver,
            By.XPATH,
            "//button[starts-with(@id, 'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id, 'notescontrol-action_bar_add_command')]",
            timeout=1,
            retries=5,
        )

        # SMS Button
        click_SMS_button = click_safe(
            driver,
            By.XPATH,
            "//li[contains(@id, 'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id, 'notescontrol-createNewRecord_flyoutMenuItem_lvidg_sms')]",
            timeout=1,
            retries=5,
        )
        #Save and continue dialog
        click_safe(
            driver,
            By.XPATH,
            "//button[starts-with(@id, 'confirmButton_') and .//div[text()='Save and continue']]",
            timeout=1,
            retries=2,
        )
        # USFC discard dialog (if appears) - best-effort
        click_safe(
            driver,
            By.XPATH,
            "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]",
            timeout=1,
            retries=5,
        )

    else:
        pass    


    #Save and continue dialog
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'confirmButton_') and .//div[text()='Save and continue']]",
        timeout=1,
        retries=2,
    )

    # USFC discard dialog - best-effort
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]",
        timeout=1,
        retries=5,
    )

    # SMS TextBox -> enter text
    send_keys_safe(
        driver,
        By.XPATH,
        "//input[starts-with(@id,'id-3145bfd3-91e7-4364-92ed-5ca0cf0d65b8') and contains(@id,'subject.fieldControl-text-input-component')]",
        sms_text,
        timeout=1,
        retries=5,
    )

    # SMS Save & Close
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'lvidg_sms|NoRelationship|Form|Mscrm.SaveAndClosePrimary') and contains(@id, '-button')]",
        timeout=1,
        retries=5,
    )

    #SMS sent failed
    SMS_error_el = safe_find(driver, By.XPATH, "//div[contains(@id,'message') and contains(@id,'+lvidg_phonenumber')]/div/span", timeout=1, retries=2)
    if SMS_error_el:
        click_safe(
            driver,
            By.XPATH,
            "//button[@id='navigateBackButtontab-id-0']/span",
            timeout=1,
            retries=5,
        )
        sms_sent = False
    else:
        sms_sent = True


    # USFC discard dialog - best-effort
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]",
        timeout=1,
        retries=5,
    )

    return sms_sent

def add_Case_Note(driver, CaseNote):
    # To Create a Case Note: open add menu
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id, 'notescontrol-action_bar_add_command')]",
        timeout=1,
        retries=5,
    )

    # Case Notes button
    note_button = click_safe(
        driver,
        By.XPATH,
        "//li[starts-with(@id,'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id,'notescontrol-createNewRecord_flyoutMenuItem_notes')]",
        timeout=1,
        retries=5,
    )
    if not note_button:
        click_safe(
            driver,
            By.XPATH,
            "//button[starts-with(@id, 'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id, 'notescontrol-action_bar_add_command')]",
            timeout=1,
            retries=5,
        )

        note_button = click_safe(
            driver,
            By.XPATH,
            "//li[starts-with(@id,'id-915f6055-2e07-4276-ae08-2b96c8d02c57') and contains(@id,'notescontrol-createNewRecord_flyoutMenuItem_notes')]",
            timeout=1,
            retries=5,
        )

        click_safe(
            driver,
            By.XPATH,
            "//button[starts-with(@id, 'confirmButton_') and .//div[text()='Save and continue']]",
            timeout=1,
            retries=2,
        )
        click_safe(
            driver,
            By.XPATH,
            "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]",
            timeout=1,
            retries=5,
        )

    else:
        pass

    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'confirmButton_') and .//div[text()='Save and continue']]",
        timeout=1,
        retries=2,
    )
    click_safe(
        driver,
        By.XPATH,
        "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]",
        timeout=1,
        retries=5,
    )

    # Case Notes editor -> enter notes
    send_keys_safe(driver, By.XPATH, "//*[contains(@id, 'rtev')]", CaseNote, timeout=1, retries=5)
    time.sleep(2) 

    note_saved = False
    try:
        saved = click_safe(driver, By.XPATH, "//span[contains(@class,'ms-Button-label') and text()='Add note and close']", timeout=1, retries=4)
        time.sleep(2)
        if saved:
            note_saved = True
        else:
            try:
                pyautogui.press(['tab', 'tab', 'enter'])
                time.sleep(2)
                note_saved = True
            except Exception as e:
                print(f"[WARN] Failed to send Tab/Tab/Enter for : ")
    except Exception as e:
        print(f"[WARN] Save note step failed for : ")
    return note_saved

def perform_dialer_login(driver):
        dialer_url = "https://104.232.254.43/ui/ad/v1/index.html"

        # Navigate to dialer
        print("[INFO] Opening dialer...")
        driver.get(dialer_url)
        time.sleep(3)  # Wait for page to load


        #Security Flag I
        try:
            click_safe(driver, By.XPATH, '/html/body/div/div[2]/button[3]' , timeout=1, retries=2)
            click_safe(driver, By.ID, 'proceed-link' , timeout=1, retries=2)
        except Exception:
            pass

        
        # 1. Enter username
        print("[INFO] Entering username...")
        send_keys_safe(driver, By.ID, 'wweLoginUserNameField', "Agent_Cairo_US_920", timeout=1, retries=120)

        # 2. Enter Password
        print("[INFO] Entering password...")
        send_keys_safe(driver, By.ID, 'wweLoginPasswordField', "123456", timeout=1, retries=120, enter=True)

        
        if safe_find(driver, By.XPATH, '//*[@id="wweLoginErrorText"]', timeout=1, retries=2):
            print("[ERROR] Dialer login failed due to incorrect credentials.")
            # Enter username
            print("[INFO] Entering username...")
            send_keys_safe(driver, By.ID, 'wweLoginUserNameField', "Agent_Cairo_US_920", timeout=1, retries=120)
    
            # Enter Password
            print("[INFO] Entering password...")
            send_keys_safe(driver, By.ID, 'wweLoginPasswordField', "123456", timeout=1, retries=120, enter=True)
   
        
        # 3. Enter PlaceID
        print("[INFO] Entering placeholder...")
        send_keys_safe(driver, By.ID, 'wweLoginPlaceInput', "Place_57078_SIPSwitch_US", timeout=1, retries=30, enter=True)
        time.sleep(10)

        
        if not switch_to_window_safe(driver, 0, max_retries=3):
            print("[WARN] Could not switch to dialer tab")

        time.sleep(2)
        try:
            click_safe(driver, By.XPATH, '//span[contains(@class,"wwe-sprite-mark-done")]', timeout=1, retries=3) 
        except Exception:
            pass
        
        click_safe(driver, By.XPATH, "//table[@id='DataTables_Table_0']/tbody/tr/td[2]", timeout=1, retries=3)
        click_safe(driver, By.ID, "wweAgentSetNotReadyReason4Item_MyChannelsView", timeout=1, retries=3)
        
        time.sleep(2)
        
        if not switch_to_window_safe(driver, 1, max_retries=3):
            print("[WARN] Could not switch back to CRM tab")      
        return True

def verify_email_domain_selected(driver, expected_title="NA Think Care", expected_text="NA Think Care", timeout=1, poll=0.5, retries= 3):
    xpath = "//*[@data-id='from.fieldControl-LookupResultsDropdown_from_selected_tag_text']"
    def _check(d):
        try:
            el = d.find_element(By.XPATH, xpath)
            title = (el.get_attribute('title') or '').strip()
            text = (el.text or '').strip()
            return title == expected_title and text == expected_text
        except Exception:
            return False
    return _check(driver)

LOCATORS = {
    "ADD_MENU_BUTTON": (By.XPATH, "//button[contains(@id, 'notescontrol-action_bar_add_command')]"),
    "EMAIL_FLYOUT_BUTTON": (By.XPATH, "//li[contains(@id, 'notescontrol-createNewRecord_flyoutMenuItem_email')]"),
    "DISCARD_CHANGES_BUTTON": (By.XPATH, "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]"),
    "CLEAR_FROM_BUTTON": (By.XPATH, "//*[contains(@id, 'from.fieldControl-LookupResultsDropdown_from') and contains(@id, 'microsoftIcon_cancelButton_')]"),
    "FROM_EMAIL_INPUT": (By.XPATH, "//*[contains(@id, 'from.fieldControl-LookupResultsDropdown_from') and contains(@id, 'textInputBox_with_filter_new')]"),
    "PICK_EMAIL_ENTRY": (By.ID, "id-1d5ad078-3edb-4edc-98c6-c0c21e3125e3-45-fromcbfb742c-14e7-4a17-96bb-1a13f7f64aa2-from.fieldControl-name0_0_0"),
    "EMAIL_BODY_INPUT": (By.XPATH, "//div[starts-with(@id, 'rtev')]/p"),
    "SEND_BUTTON": (By.XPATH, "//button[starts-with(@id, 'email|NoRelationship|Form|Mscrm.Form.email.Send')]"),
    "NAVIGATE_BACK_BUTTON": (By.XPATH, "//button[@id='navigateBackButtontab-id-0']/span")
}

def select_from_email(driver, email_address="na_thinkcare@lenovo.com", expected_title="NA Think Care"):
    click_safe(driver, *LOCATORS["CLEAR_FROM_BUTTON"], timeout=1, retries=3)
    send_keys_safe(driver, *LOCATORS["FROM_EMAIL_INPUT"], email_address, timeout=1, retries=5)
    if not click_safe(driver, *LOCATORS["PICK_EMAIL_ENTRY"], timeout=1, retries=5):
         return False
    time.sleep(2)
    return verify_email_domain_selected(driver, expected_title=expected_title, expected_text=expected_title, timeout=1, poll=0.5, retries=3)

def send_Email(driver, email_text):
    if not click_safe(driver, *LOCATORS["ADD_MENU_BUTTON"], timeout=1, retries=3):
        return False
    if not click_safe(driver, *LOCATORS["EMAIL_FLYOUT_BUTTON"], timeout=1, retries=5):
        click_safe(driver, *LOCATORS["ADD_MENU_BUTTON"], timeout=1, retries=3)
        if not click_safe(driver, *LOCATORS["EMAIL_FLYOUT_BUTTON"], timeout=1, retries=5):
             return False
    click_safe(driver, *LOCATORS["DISCARD_CHANGES_BUTTON"], timeout=1, retries=3) 
    time.sleep(2)
    if not select_from_email(driver):
        click_safe(driver, *LOCATORS["NAVIGATE_BACK_BUTTON"], timeout=1, retries=3)
        click_safe(driver, *LOCATORS["DISCARD_CHANGES_BUTTON"], timeout=1, retries=3)
        return False
    if not send_keys_safe(driver, *LOCATORS["EMAIL_BODY_INPUT"], email_text, timeout=1, retries=5):
        return False
    if not click_safe(driver, *LOCATORS["SEND_BUTTON"], timeout=1, retries=5):
        return False
    time.sleep(3)
    return True
def solution_provided_check_and_skip(driver, case_number, df, excel_path):
    solutionProv_case = True
    try:
        case_status_xpath = "//div[contains(@id,'headerControlsList')]/div[3]/div/div"
        case_status_el = safe_find(driver, By.XPATH, case_status_xpath, timeout=1, retries=6)
        if case_status_el:
            case_status = case_status_el.text.strip()
            if not case_status.lower() == "solution provided":
                solutionProv_case = False
            else:
                solutionProv_case = True
        else:
            solutionProv_case = False
    except Exception:
        pass
    return solutionProv_case

def serial_extraction(driver, case_number, df):
    serial_val = ''
    try:
        serial_xpath = "//*[contains(@id,'productserialnumber.fieldControl-text-input-component')]"
        el_serial = safe_find(driver, By.XPATH, serial_xpath, timeout=1, retries=2)
        if el_serial:
            try:
                serial_val = el_serial.get_attribute('value') or el_serial.text or ''
            except Exception:
                try:
                    serial_val = el_serial.text or ''
                except Exception:
                    serial_val = ''
    except Exception as e:
        print(f"[WARN] Could not read serial number for {case_number}: ")
    
    try:
        serial_val = str(serial_val).strip()
    except Exception:
        serial_val = ''
    return serial_val

def customer_name_extraction(driver, case_number):
    CX_Name = ''
    try:
        name_el = safe_find(driver, By.XPATH, "//*[contains(@id,'sec_tab_contact-associatedEntityRecordName')]", timeout=1, retries=2)
        if name_el:
            try:
                raw_name = name_el.get_attribute('aria-label') or name_el.get_attribute('title') or name_el.text or ''
            except Exception:
                raw_name = name_el.text or ''
            try:
                CX_Name = ' '.join([w.capitalize() for w in str(raw_name).split() if w])
            except Exception:
                CX_Name = str(raw_name)
    except Exception as e:
        print(f"[WARN] Could not read customer name for {case_number}: ")

    if not CX_Name:
        CX_Name = 'Our Valued Customer'
    return CX_Name

def formatting_texts_sms(CX_Name, serial_val, case_number, df):
    try:
        sms_text = SMSText.format(CX_Name=CX_Name, case_number=case_number)
    except Exception:
        sms_text = SMSText.format(CX_Name='Our Valued Customer', case_number=case_number)
    return sms_text

def formatting_texts_email(CX_Name, serial_val, case_number, df):
    chosen_template = None
    try:
        mask = df["case_number"].astype(str) == str(case_number)
        if mask.any() and "Work Order Type" in df.columns:
            wot_val = df.loc[mask, "Work Order Type"].iloc[0]
            wot = str(wot_val).strip() if not (pd.isna(wot_val) or str(wot_val).strip() == "") else ""
        else:
            wot = ""
    except Exception:
        wot = ""

    if wot.lower() in ("onsite", "depot"):
        chosen_template = CaseEmailOnSite_Depot
    elif wot.lower() == "cru":
        chosen_template = CaseEmailCRU
    else:
        chosen_template = CaseEmailOnSite_Depot

    email_text = chosen_template.format(
        CX_Name=CX_Name or "Our Valued Customer",
        serial_val=serial_val,
        AgentName=AgentName
    )
    return email_text

def find_column_case_insensitive(df, col_name):
    for col in df.columns:
        if col.strip().lower() == col_name.strip().lower():
            return col
    return col_name

def todays_excel_path():
    now = datetime.now()
    dd = now.strftime('%d')
    mm = now.strftime('%m')
    base = r"C:\Users\AdamMaged\OneDrive - IBM\ART Project\Active Cases PA {MM}-{DD}.xlsx"
    path = base.format(DD=dd, MM=mm)
    return path 

def excelCaseClosingCode(CaseClosingCode):
    match CaseClosingCode:
        case "Issue Resolved": return "Fixed"
        case "Not yet Tested": return "Not yet Tested"
        case "Issue Not Fixed": return "Issue Not Fixed"
        case "Customer Not Reached": return "Not Reached"
        case "Not reached": return "Not Reached"
        case "Customer Claims that the Machine Not Yet Tested": return "Not yet Tested"
        case "DND": return "DND"
        case "Escalated": return "Escalation"
        case "Called - Company NO. Extension Found: Not Reached": return "Not Reached"
        case "Called: Not Reached // left Voicemail": return "Not Reached"
        case "Called - Answered: Issue Resolved": return "Fixed"
        case "Called - Answered: Issue Not Resolved": return "Issue Not Fixed"
        case "Need Third Action": return "In Progress"
        case "New": return "New"
        case "Skipped": return "Skipped"
        case "Send SMS": return "Sent Email"
        case "Send Email": return "Sent Email"
        case "Send SMS and Email": return "Sent Email"
        case "Call the Customer": return "Called the Customer"
        case _: return ""

def wait_until_time(hour: int, minute: int, check_interval: int = 30):
    now = datetime.now()
    target = datetime(now.year, now.month, now.day, hour, minute)
    if now >= target:
        target = target + timedelta(days=1)
    
    total_seconds = int((target - now).total_seconds())
    print(f"[INFO] Current time {now.strftime('%Y-%m-%d %H:%M:%S')}. Waiting until {target.strftime('%Y-%m-%d %H:%M:%S')} ({total_seconds}s)")
    while True:
        now = datetime.now()
        rem = (target - now).total_seconds()
        if rem <= 0:
            break
        if rem > check_interval:
            mins = int(rem // 60)
            secs = int(rem % 60)
            print(f"[INFO] Time until start/close: {mins} minute(s) {secs} second(s)")
            time.sleep(check_interval)
        else:
            time.sleep(1)
    print("[INFO] Target start time reached — continuing.")

def wait_for_excel_file(path, check_interval=900):
    if os.path.exists(path):
        print(f"[INFO] Excel file found: {path}")
        return True
    print(f"[INFO] Excel file not available yet: {path}")
    print(f"[INFO] Starting retry loop: checking every {check_interval} seconds (15 minutes)")
    attempt = 0
    while True:
        attempt += 1
        print(f"[INFO] Retry attempt {attempt}: waiting {check_interval} seconds before next check...")
        time.sleep(check_interval)
        if os.path.exists(path):
            print(f"[INFO] Excel file found on attempt {attempt}: {path}")
            return True
        else:
            print(f"[INFO] Excel file still not available on attempt {attempt}, will retry")

def keep_driver_alive(driver, check_interval=60):
    try:
        driver.refresh()
        print(f"[DEBUG] Driver refreshed to keep alive")
        return True
    except Exception as e:
        print(f"[DEBUG] Could not refresh driver (may not be at valid URL yet): ")
        return False

def ask_wait_choice():
    choice = {"wait": True} 
    class WaitDialog(QDialog):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Wait Time Check")
            self.resize(350, 150)
            layout = QVBoxLayout(self)
            lbl = QLabel("Scheduled start time is 14:55.\nDo you want to Wait until then or Skip waiting?")
            lbl.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
            layout.addWidget(lbl)
            btn_layout = QHBoxLayout()
            btn_wait = QPushButton("Wait until 14:55")
            btn_wait.setMinimumHeight(40)
            btn_wait.clicked.connect(lambda: self.done_with_choice(True))
            btn_layout.addWidget(btn_wait)
            btn_skip = QPushButton("Skip Waiting")
            btn_skip.setMinimumHeight(40)
            btn_skip.clicked.connect(lambda: self.done_with_choice(False))
            btn_layout.addWidget(btn_skip)
            layout.addLayout(btn_layout)
        def done_with_choice(self, should_wait):
            choice["wait"] = should_wait
            self.accept()

    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    popup = WaitDialog()
    popup.exec()
    if created_app:
        app.quit()
    return choice["wait"]

class GenericChoiceDialog(QDialog):
    def __init__(self, title, message, btn1_text, btn2_text, timeout_secs=None):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(400, 220)
        self.choice = None
        self._btn1_text = btn1_text
        self._remaining = timeout_secs

        layout = QVBoxLayout(self)
        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 14px; margin-bottom: 15px;")
        layout.addWidget(lbl)

        # Countdown label (only shown when timeout is set)
        self._countdown_lbl = QLabel("")
        self._countdown_lbl.setStyleSheet("font-size: 12px; color: gray; margin-bottom: 5px;")
        self._countdown_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._countdown_lbl)

        btn_layout = QHBoxLayout()
        self.btn1 = QPushButton(btn1_text)
        self.btn1.setMinimumHeight(45)
        self.btn1.clicked.connect(lambda: self.set_choice(btn1_text))
        btn_layout.addWidget(self.btn1)
        self.btn2 = QPushButton(btn2_text)
        self.btn2.setMinimumHeight(45)
        self.btn2.clicked.connect(lambda: self.set_choice(btn2_text))
        btn_layout.addWidget(self.btn2)
        layout.addLayout(btn_layout)

        # Start countdown timer if timeout_secs provided
        if timeout_secs is not None and timeout_secs > 0:
            self._update_countdown_label()
            self._timer = QTimer(self)
            self._timer.setInterval(1000)
            self._timer.timeout.connect(self._tick)
            self._timer.start()

    def _update_countdown_label(self):
        self._countdown_lbl.setText(
            f"Auto-selecting '{self._btn1_text}' in {self._remaining}s ..."
        )

    def _tick(self):
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            self.set_choice(self._btn1_text)
        else:
            self._update_countdown_label()

    def set_choice(self, text):
        self.choice = text
        self.accept()

def show_choice_dialog(title, message, btn1_text, btn2_text, timeout_secs=None):
    app = QApplication.instance()
    created_app = False
    if app is None:
        app = QApplication(sys.argv)
        created_app = True
    dialog = GenericChoiceDialog(title, message, btn1_text, btn2_text, timeout_secs=timeout_secs)
    dialog.exec()
    result = dialog.choice
    if created_app:
        app.quit()
    return result

class TimeTriggerHandler:
    def __init__(self):
        self.triggered_5pm = False
        self.triggered_930pm = False
        self.monitor_930pm_active = False
        self.last_930pm_prompt_time = 0
        self.prompt_interval_930pm = 15 * 60
        
    def check_triggers(self):
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute
        
        if not self.triggered_5pm and current_hour == 17 and 0 <= current_minute <= 30:
            self.triggered_5pm = True
            choice = show_choice_dialog(
                "5:00 PM Check",
                "It is 5:00 PM. How do you want to proceed?",
                "Start the inprogress",
                "Complete the new"
            )
            if choice == "Start the inprogress":
                return "PRIORITIZE_IN_PROGRESS"
            else:
                return "COMPLETE_NEW"
                
        if current_hour == 21 and current_minute >= 30:
            if not self.triggered_930pm:
                self.triggered_930pm = True
                self.monitor_930pm_active = True
                return self._handle_930_prompt()
            
            if self.monitor_930pm_active:
                if (time.time() - self.last_930pm_prompt_time) > self.prompt_interval_930pm:
                    return self._handle_930_prompt()
        return None

    def _handle_930_prompt(self):
        self.last_930pm_prompt_time = time.time()
        choice = show_choice_dialog(
            "9:30 PM Check",
            "It is past 9:30 PM. Status check:",
            "Complete the in_progress",
            "finish the new"
        )
        if choice == "Complete the in_progress":
            self.monitor_930pm_active = True
            return "CONTINUE_IN_PROGRESS"
        else:
            self.monitor_930pm_active = False 
            return "FINISH_NEW"

def save_to_checkpoint(df, original_path):
    try:
        dir_name = os.path.dirname(original_path)
        base_name = os.path.basename(original_path)
        name, ext = os.path.splitext(base_name)
        checkpoint_path = os.path.join(dir_name, f"CHECKPOINT_{name}.csv")
        df.to_csv(checkpoint_path, index=False)
        return checkpoint_path
    except Exception as e:
        print(f"[WARN] Failed to save checkpoint: {e}")
        return None

def reorder_indices_priority(to_process_indices, current_pointer, df):
    if current_pointer >= len(to_process_indices) - 1:
        return to_process_indices
    done_indices = to_process_indices[:current_pointer+1]
    future_indices = to_process_indices[current_pointer+1:]
    status_col = find_column_case_insensitive(df, 'Status')
    priority_indices = []
    normal_indices = []
    
    for idx in future_indices:
        status = str(df.at[idx, status_col]).strip().lower()
        if status in ('in_progress', 'skipped'):
            priority_indices.append(idx)
        else:
            normal_indices.append(idx)
    new_order = done_indices + priority_indices + normal_indices
    print(f"[INFO] Reordered queue: {len(priority_indices)} priority cases moved to front.")
    return new_order

def get_current_time_for_state(state):
    if not state:
        return None
    tz_name = STATE_TIMEZONE_MAP.get(state)
    if not tz_name:
        for k, v in STATE_TIMEZONE_MAP.items():
            if k.lower() == str(state).strip().lower():
                tz_name = v
                break
    if not tz_name:
        return None
    try:
        now_utc = datetime.now(timezone.utc)
        if zoneinfo:
            try:
                tz = zoneinfo.ZoneInfo(tz_name)
                local_time = now_utc.astimezone(tz)
                return local_time.strftime("%I:%M %p")
            except Exception:
                pass
        if pytz:
            try:
                tz = pytz.timezone(tz_name)
                local_time = now_utc.astimezone(tz)
                return local_time.strftime("%I:%M %p")
            except Exception:
                pass
    except Exception as e:
        return None
    return None

def case_search_and_open(driver, case_number):
    handle_genesys_popup(driver)
    safe_find(driver, By.ID, "GlobalSearchBox", timeout=1, retries=3)
    send_keys_safe(driver, By.ID, "GlobalSearchBox", case_number, timeout=1, retries=5)
    click_safe(driver, By.XPATH, "//div[@id='id-globalSearchFlyout-1']/div/div/div/div/div/div[2]/div/button/span", timeout=1, retries=2)
    click_safe(driver, By.XPATH, "//button[starts-with(@id, 'cancelButton_') and .//div[text()='Discard changes']]", timeout=1, retries=2)
    click_safe(driver, By.XPATH, "//button[starts-with(@id, 'confirmButton_') and .//div[text()='Save and continue']]", timeout=1, retries=2)
    click_safe(driver, By.XPATH, "//button[starts-with(@id, 'confirmButton_') and .//div[text()='OK']]", timeout=1, retries=2)
    
def edit_case(driver):
    click_safe(driver, By.XPATH, "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckOut.Command.') and contains(@id,'button')]", timeout=1, retries=4)
    time.sleep(2)

def save_case(driver):
    click_safe(driver, By.XPATH, "//button[contains(@id,'incident|NoRelationship|Form|lvdcg.incident.TimeTrackingCheckIn.Command.') and contains(@id,'button')]", timeout=1, retries=4)
    time.sleep(2)

def Care_call_modify(driver):
    try:
            click_safe(driver, By.XPATH, "//div[contains(@id, 'MscrmControls.Containers.ProcessBreadCrumb-stageIndicatorContainer2d827664-559a-4937-beb1-52b3f836b967')]/div", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//div[contains(@id, 'header_process_lvidg_casestatuscode-header_process_lvidg_casestatuscode') and contains(@id, 'header_process_lvidg_casestatuscode.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='Care Call']", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//div[contains(@id, 'header_process_casetypecode-header_process_casetypecode') and contains(@id, 'header_process_casetypecode.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='Escalation/Complaint']", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//div[contains(@id, 'header_process_lvidg_callreasoncode-header_process_lvidg_callreasoncode') and contains(@id, 'header_process_lvidg_callreasoncode.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='Follow up - Complaint']", timeout=1, retries=5)
            time.sleep(1)
            click_safe(driver, By.XPATH, "//button[contains(@id,'MscrmControls.Containers.ProcessStageControl-stageContentClose') and @aria-label='Close']", timeout=1, retries=5)
    except Exception as e:
        print(f"[WARN] Care Call modification failed: ")

def eticket_check_and_modify(driver):
    eticket_case = True
    case_channel_xpath = "//div[contains(@id,'headerControlsList')]/div[7]/div/div"
    case_channel_el = safe_find(driver, By.XPATH, case_channel_xpath, timeout=1, retries=6)
    
    if case_channel_el:
        case_channel = case_channel_el.text.strip()
        if not case_channel.lower() == "e-ticketing":
            eticket_case = False
        else:
            eticket_case = True
            click_safe(driver, By.XPATH, "//div[contains(@id, 'MscrmControls.Containers.ProcessBreadCrumb-stageIndicatorContainer2d827664-559a-4937-beb1-52b3f836b967')]/div", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//div[contains(@id, 'header_process_casetypecode-header_process_casetypecode') and contains(@id, 'header_process_casetypecode.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='Service Call']", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//div[contains(@id, 'header_process_lvidg_callreasoncode-header_process_lvidg_callreasoncode') and contains(@id, 'header_process_lvidg_callreasoncode.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='Hardware Repair']", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//div[contains(@id,'header_process_lvidg_techsavvy-header_process_lvidg_techsavvy') and contains(@id, 'header_process_lvidg_techsavvy.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='Undetermined']", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//div[contains(@id,'header_process_lvidg_isusedlenovopdtree-header_process_lvidg_isusedlenovopdtree') and contains(@id, 'header_process_lvidg_isusedlenovopdtree.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='No']", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//div[contains(@id,'header_process_lvidg_pdtreereasoncode-header_process_lvidg_pdtreereasoncode') and contains(@id, 'header_process_lvidg_pdtreereasoncode.fieldControl-pcf-container-id')]/div/div/div/div/div/button", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//*[contains(@id, 'fluent-option') and text()='e-Ticketing']", timeout=1, retries=5)
            time.sleep(2)
            click_safe(driver, By.XPATH, "//button[contains(@id,'MscrmControls.Containers.ProcessStageControl-stageContentClose') and @aria-label='Close']", timeout=1, retries=5)
            time.sleep(2)
            
    else:
        eticket_case = False 
    return eticket_case
