# ============================================================================
# Dispatcher.py - ART Q Control Entry Point
# ============================================================================
# This is the main entry point for ART Q Control.
# Displays a welcome dialog with two main options:
# - Auto Sender: Process NEW cases (no dialer)
# - Case Reviewer: Review IN-PROGRESS cases (with dialer)
# ============================================================================

import os
import sys
import subprocess

# Ensure both src and this directory are in path for proper imports
src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

art_q_dir = os.path.dirname(os.path.abspath(__file__))
if art_q_dir not in sys.path:
    sys.path.insert(0, art_q_dir)

from PyQt5.QtWidgets import (
    QApplication, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFrame, QFileDialog, QMessageBox, QCheckBox, QInputDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Import shared functions for configuration
from SharedFunctions import (
    CONFIG_MANAGER,
    AGENT_NAME,
    DIALER_USERNAME,
    EXCEL_BASE_PATH,
    CACHE_DIRECTORY,
    EXCEL_SHEET_NAME,
)

# Import the two main modules
from AutoSender import run_auto_sender
from CaseReviewer import run_case_reviewer


# Store result with support agent info
_mode_result = {"mode": 0, "support_agent": None}

def show_mode_selector():
    """
    Display welcome window with mode selection:
    - Auto Sender (process new cases, no dialer)
    - Case Reviewer (review in-progress cases with dialer)
    - Update Configuration
    - Main Menu
    
    Returns the selected mode.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = QDialog()
    dialog.setWindowTitle("ART Q Control - Mode Selector")
    dialog.setMinimumSize(750, 720)
    dialog.resize(750, 720)
    dialog.setStyleSheet("""
        QDialog {
            background-color: #FAFAFA;
        }
    """)
    
    layout = QVBoxLayout()
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)
    
    # ========== TITLE ==========
    title = QLabel("=== ART AUTOMATION SYSTEM ===")
    title.setAlignment(Qt.AlignCenter)
    title.setStyleSheet("""
        font-weight: bold;
        font-size: 20px;
        color: #1976D2;
        padding: 10px;
    """)
    layout.addWidget(title)
    
    # ========== CONFIGURATION INFO ==========
    config_frame = QFrame()
    config_frame.setStyleSheet("""
        QFrame {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
        }
    """)
    config_layout = QVBoxLayout(config_frame)
    config_layout.setContentsMargins(20, 15, 20, 15)
    
    config_title = QLabel("Current Configuration:")
    config_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #333;")
    config_layout.addWidget(config_title)
    
    config_info = QLabel(
        f"<table cellpadding='5'>"
        f"<tr><td><b>Agent Name:</b></td><td>{AGENT_NAME}</td></tr>"
        f"<tr><td><b>User ID:</b></td><td>{DIALER_USERNAME}</td></tr>"
        f"<tr><td><b>Excel Base Path:</b></td><td>{EXCEL_BASE_PATH}</td></tr>"
        f"<tr><td><b>Cache Directory:</b></td><td>{CACHE_DIRECTORY}</td></tr>"
        f"<tr><td><b>Sheet Name:</b></td><td>{EXCEL_SHEET_NAME}</td></tr>"
        f"</table>"
    )
    config_info.setStyleSheet("color: #555; font-size: 15px;")
    config_layout.addWidget(config_info)
    
    layout.addWidget(config_frame)
    
    # ========== AUTO SENDER BUTTON ==========
    auto_sender_frame = QFrame()
    auto_sender_frame.setStyleSheet("""
        QFrame {
            background-color: #E8F5E9;
            border: 2px solid #4CAF50;
            border-radius: 10px;
        }
        QFrame:hover {
            background-color: #C8E6C9;
        }
    """)
    auto_sender_layout = QVBoxLayout(auto_sender_frame)
    auto_sender_layout.setContentsMargins(20, 15, 20, 15)
    
    auto_sender_btn = QPushButton("🚀 AUTO SENDER")
    auto_sender_btn.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            font-size: 18px;
            padding: 18px;
            border-radius: 8px;
            border: none;
        }
        QPushButton:hover {
            background-color: #43A047;
        }
        QPushButton:pressed {
            background-color: #388E3C;
        }
    """)
    auto_sender_btn.clicked.connect(lambda: dialog.done(1))
    auto_sender_layout.addWidget(auto_sender_btn)
    
    layout.addWidget(auto_sender_frame)
    
    # ========== CASE REVIEWER BUTTON ==========
    case_reviewer_frame = QFrame()
    case_reviewer_frame.setStyleSheet("""
        QFrame {
            background-color: #E3F2FD;
            border: 2px solid #1976D2;
            border-radius: 10px;
        }
        QFrame:hover {
            background-color: #BBDEFB;
        }
    """)
    case_reviewer_layout = QVBoxLayout(case_reviewer_frame)
    case_reviewer_layout.setContentsMargins(20, 15, 20, 15)
    
    case_reviewer_btn = QPushButton("📞 CASE REVIEWER")
    case_reviewer_btn.setStyleSheet("""
        QPushButton {
            background-color: #1976D2;
            color: white;
            font-weight: bold;
            font-size: 18px;
            padding: 18px;
            border-radius: 8px;
            border: none;
        }
        QPushButton:hover {
            background-color: #1565C0;
        }
        QPushButton:pressed {
            background-color: #0D47A1;
        }
    """)
    case_reviewer_btn.clicked.connect(lambda: dialog.done(2))
    case_reviewer_layout.addWidget(case_reviewer_btn)
    
    layout.addWidget(case_reviewer_frame)
    
    # ========== BOTTOM BUTTONS ==========
    bottom_layout = QHBoxLayout()
    bottom_layout.setSpacing(15)
    
    update_btn = QPushButton("⚙ Update Configuration")
    update_btn.setStyleSheet("""
        QPushButton {
            background-color: #FF9800;
            color: white;
            font-weight: bold;
            font-size: 15px;
            padding: 12px 20px;
            border-radius: 6px;
            border: none;
        }
        QPushButton:hover {
            background-color: #FB8C00;
        }
        QPushButton:pressed {
            background-color: #F57C00;
        }
    """)
    update_btn.clicked.connect(lambda: dialog.done(3))
    bottom_layout.addWidget(update_btn)
    
    main_menu_btn = QPushButton("☰ Main Menu")
    main_menu_btn.setStyleSheet("""
        QPushButton {
            background-color: #607D8B;
            color: white;
            font-weight: bold;
            font-size: 15px;
            padding: 12px 20px;
            border-radius: 6px;
            border: none;
        }
        QPushButton:hover {
            background-color: #546E7A;
        }
        QPushButton:pressed {
            background-color: #455A64;
        }
    """)
    main_menu_btn.clicked.connect(lambda: dialog.done(4))
    bottom_layout.addWidget(main_menu_btn)
    
    layout.addLayout(bottom_layout)
    
    # ========== SUPPORT MODE CHECKBOX ==========
    support_checkbox = QCheckBox("🤝 Supporting another agent")
    support_checkbox.setStyleSheet("font-size: 15px; padding: 8px; color: #161616;")
    layout.addWidget(support_checkbox)
    
    # ========== FOOTER ==========
    footer = QLabel(
        '<span style="color:#666; font-size: 15px;">'
        'Developed by: Ehab Elrify | Adam Maged<br>'
        'Email: <a href="mailto:ehab.elrify@ibm.com" style="color:#1976D2;">ehab.elrify@ibm.com</a> | '
        '<a href="mailto:abdelrahman.maged@ibm.com" style="color:#1976D2;">abdelrahman.maged@ibm.com</a><br>'
        'Assurance Resolution Team</span>'
    )
    footer.setAlignment(Qt.AlignCenter)
    footer.setOpenExternalLinks(True)
    layout.addWidget(footer)
    
    dialog.setLayout(layout)
    result = dialog.exec_()
    
    # Handle Support Mode
    support_agent = None
    if support_checkbox.isChecked() and result in [1, 2]:
        agent_name, ok = QInputDialog.getText(
            None, "Support Mode", 
            "Enter the name of the agent you are supporting:\n(This will be used for the sheet name: '[AgentName]'s Cases')")
        if ok and agent_name.strip():
            support_agent = agent_name.strip()
            print(f"[INFO] Support mode enabled for agent: {support_agent}")
    
    _mode_result["mode"] = result
    _mode_result["support_agent"] = support_agent
    
    return result, support_agent


def ask_for_excel_path():
    """
    Simple dialog to ask for Excel file path for AutoSender mode.
    Returns the selected file path or None if cancelled.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Open file dialog directly
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Select Today's Excel File (Main Sheet)",
        EXCEL_BASE_PATH,
        "Excel Files (*.xlsx *.xls);;All Files (*)"
    )
    
    if file_path:
        print(f"[INFO] Selected Excel file: {file_path}")
        return file_path
    else:
        print("[INFO] File selection cancelled.")
        return None


def launch_main_menu():
    """Return to the main menu of the application.

    In a frozen .exe the main menu is the parent process — nothing to relaunch.
    In development, re-launch main.py in a subprocess.
    """
    try:
        if getattr(sys, 'frozen', False):
            # In-process: main menu window is already open — nothing to do here.
            # The caller is responsible for closing the current tool window.
            print("[INFO] launch_main_menu() called in frozen mode — main menu already running.")
            return
        import subprocess as _sp
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        main_menu_path = os.path.join(src_dir, 'main.py')
        if os.path.exists(main_menu_path):
            _sp.Popen([sys.executable, main_menu_path])
        else:
            print(f"[ERROR] Main menu not found at {main_menu_path}")
    except Exception as e:
        print(f"[ERROR] Failed to launch main menu: {e}")


def launch_config_update():
    """Launch configuration update dialog"""
    try:
        from config_loader import create_config_setup_dialog

        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        config_dialog = create_config_setup_dialog(CONFIG_MANAGER)
        config_dialog.exec_()
        
        # After config update, show mode selector again
        return show_mode_selector()
    except Exception as e:
        print(f"[ERROR] Failed to launch config dialog: {e}")
        return 0, None


def main():
    """Main entry point"""
    print("=" * 60)
    print("       ART Q CONTROL - Dispatcher")
    print("=" * 60)
    
    result, support_agent = show_mode_selector()
    
    if result == 1:  # Auto Sender
        print("[INFO] Starting Auto Sender mode...")
        # AutoSender will auto-load Excel from configured path, show popup if not found
        run_auto_sender(support_agent=support_agent)
        
    elif result == 2:  # Case Reviewer
        print("[INFO] Starting Case Reviewer mode...")
        run_case_reviewer(support_agent=support_agent)
        
    elif result == 3:  # Update Configuration
        print("[INFO] Opening configuration dialog...")
        new_result, new_support_agent = launch_config_update()
        
        # Handle result from config dialog recursively
        if new_result == 1:
            run_auto_sender(support_agent=new_support_agent)
        elif new_result == 2:
            run_case_reviewer(support_agent=new_support_agent)
        elif new_result == 4:
            launch_main_menu()
            sys.exit(0)
        
    elif result == 4:  # Main Menu
        print("[INFO] Returning to main menu...")
        launch_main_menu()
        sys.exit(0)
        
    else:  # Dialog closed
        print("[INFO] Dialog closed without selection. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()

