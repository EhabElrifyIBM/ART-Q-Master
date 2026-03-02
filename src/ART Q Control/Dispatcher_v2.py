# ============================================================================
# Dispatcher_v2.py - ART Q Control Entry Point (Enhanced)
# ============================================================================
# Phase 5 Enhanced Version:
# - Company Process Isolation (separate button, not auto-run)
# - Improved UI/Navigation for Phase 3 enhancements to come
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

# Phase 3.2: Theme and Accessibility Managers (imported lazily after QApplication)

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

# Import the v2 enhanced modules (Phase 5 versions)
from AutoSender_v2 import run_auto_sender
from CaseReviewer_v2 import run_case_reviewer


# Store result with support agent info
_mode_result = {"mode": 0, "support_agent": None}

def _load_and_apply_font_size():
    """Load font size from config.json and apply it."""
    try:
        import json
        import os
        
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            if 'ui_settings' in config and 'font_size' in config['ui_settings']:
                font_size = config['ui_settings']['font_size']
                
                # Clamp to valid range (10-40px to match settings dialog)
                font_size = max(10, min(40, int(font_size)))
                
                # Apply to application
                app = QApplication.instance()
                if app:
                    base_font = app.font()
                    base_font.setPointSize(font_size)
                    app.setFont(base_font)
                    
                    # Store in accessibility manager
                    
                    print(f"[INFO] ✓ Applied saved font size {font_size}px from config.json")
                    return font_size
    except Exception as e:
        print(f"[WARNING] Could not load font size from config: {e}")
    
    return 22  # Default

def show_mode_selector():
    """
    Display welcome window with mode selection:
    - Auto Sender (process new cases, no dialer)
    - Case Reviewer (review in-progress cases with dialer)
    - Company Process (process company cases - NOW ISOLATED)
    - Update Configuration
    - Main Menu
    
    Returns the selected mode.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # ===== SETTINGS AWARENESS: Create settings-aware dialog =====
    class ModeSelectionDialog(QDialog):
        def __init__(self):
            super().__init__()
            # --- Apply Functions.py hard-coded styles ---
            self.setStyleSheet("""
                QDialog {
                    background-color: #f7f9fa;
                    border-radius: 16px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 21px;
                }
                QLabel {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 21px;
                    font-weight: 600;
                    color: #222;
                }
                QPushButton {
                    background-color: #1976D2;
                    color: #fff;
                    font-weight: 600;
                    padding: 12px 28px;
                    border-radius: 8px;
                    font-size: 21px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #1565C0;
                    color: #fff;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
                QProgressBar {
                    border: 1px solid #b0bec5;
                    border-radius: 6px;
                    text-align: center;
                    height: 14px;
                    font-size: 18px;
                    background: #eceff1;
                }
                QProgressBar::chunk {
                    background-color: #43A047;
                    border-radius: 6px;
                }
                QFrame {
                    background: #fff;
                    border-radius: 10px;
                }
                QCheckBox {
                    font-size: 21px;
                }
            """)
            from PyQt5.QtGui import QFont
            font = QFont('Segoe UI', 21)
            self.setFont(font)
        
        def _apply_current_font_size(self):
            """Apply current font size from config to all widgets."""
            try:
                import json
                import os
                config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.json')
                font_size = 22  # default (updated from 15)
                
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    if 'ui_settings' in config and 'font_size' in config['ui_settings']:
                        font_size = max(10, min(40, int(config['ui_settings']['font_size'])))  # Updated range to 10-40
                
            except Exception as e:
                print(f"[DEBUG] Could not apply initial font size: {e}")
        
        def on_theme_changed(self, theme: str):
            """Handle theme changes."""
            if theme == 'dark':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #1E1E1E;
                    }
                    QLabel {
                        color: #FFFFFF;
                    }
                    QPushButton {
                        color: #FFFFFF;
                    }
                """)
            else:
                self.setStyleSheet("""
                    QDialog {
                        background-color: #FAFAFA;
                    }
                    QLabel {
                        color: #161616;
                    }
                    QPushButton {
                        color: #333;
                    }
                """)
        
        def on_font_size_changed(self, scale: float):
            """Handle font size changes."""
            # Import and use the static helper
    
    dialog = ModeSelectionDialog()
    from PyQt5.QtGui import QFont
    font = QFont('Arial', 25)
    dialog.setWindowTitle("ART Q Control - Mode Selector")
    dialog.setMinimumSize(750, 850)
    dialog.resize(750, 850)
    dialog.setFont(font)
    
    layout = QVBoxLayout()
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setSpacing(20)
    
    # ========== TITLE ==========
    title = QLabel("=== ART AUTOMATION SYSTEM ===")
    title.setAlignment(Qt.AlignCenter)
    title.setFont(font)
    title.setStyleSheet("""
        font-weight: bold;
        color: #1976D2;
        padding: 10px;
        font-size: 25px;
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
    config_title.setFont(font)
    config_title.setStyleSheet("font-weight: bold; color: #333; font-size: 25px;")
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
    config_info.setFont(font)
    config_info.setStyleSheet("color: #555; font-size: 25px;")
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
    auto_sender_btn.setFont(font)
    auto_sender_btn.setStyleSheet("""
        QPushButton {
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
            padding: 18px;
            border-radius: 8px;
            border: none;
            font-size: 25px;
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
    case_reviewer_btn.setFont(font)
    case_reviewer_btn.setStyleSheet("""
        QPushButton {
            background-color: #1976D2;
            color: white;
            font-weight: bold;
            padding: 18px;
            border-radius: 8px;
            border: none;
            font-size: 25px;
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
    
    # ========== COMPANY PROCESS BUTTON (NEW - Phase 5.1) ==========
    company_process_frame = QFrame()
    company_process_frame.setStyleSheet("""
        QFrame {
            background-color: #FCE4EC;
            border: 2px solid #C2185B;
            border-radius: 10px;
        }
        QFrame:hover {
            background-color: #F8BBD0;
        }
    """)
    company_process_layout = QVBoxLayout(company_process_frame)
    company_process_layout.setContentsMargins(20, 15, 20, 15)
    
    company_process_btn = QPushButton("🏢 COMPANY PROCESS")
    company_process_btn.setFont(font)
    company_process_btn.setStyleSheet("""
        QPushButton {
            background-color: #C2185B;
            color: white;
            font-weight: bold;
            padding: 18px;
            border-radius: 8px;
            border: none;
            font-size: 25px;
        }
        QPushButton:hover {
            background-color: #A01647;
        }
        QPushButton:pressed {
            background-color: #880E4F;
        }
    """)
    company_process_btn.clicked.connect(lambda: dialog.done(5))
    company_process_layout.addWidget(company_process_btn)
    
    layout.addWidget(company_process_frame)
    
    # ========== BOTTOM BUTTONS ==========
    bottom_layout = QHBoxLayout()
    bottom_layout.setSpacing(15)
    
    # Phase 5.4: Settings button for UI customization
    # Settings button removed as requested
    
    update_btn = QPushButton("⚙ Update Configuration")
    update_btn.setFont(font)
    update_btn.setStyleSheet("""
        QPushButton {
            background-color: #FF9800;
            color: white;
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 6px;
            border: none;
            font-size: 25px;
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
    main_menu_btn.setFont(font)
    main_menu_btn.setStyleSheet("""
        QPushButton {
            background-color: #607D8B;
            color: white;
            font-weight: bold;
            padding: 12px 20px;
            border-radius: 6px;
            border: none;
            font-size: 25px;
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
    layout.addStretch()
    
    # ========== SUPPORT MODE CHECKBOX ==========
    support_checkbox = QCheckBox("🤝 Supporting another agent")
    support_checkbox.setFont(font)
    support_checkbox.setStyleSheet("padding: 8px; color: #161616; font-size: 25px;")
    layout.addWidget(support_checkbox)
    
    # ========== FOOTER ==========
    footer = QLabel(
        '<span style="color:#666;">'
        'Developed by: Ehab Elrify | Adam Maged<br>'
        'Email: <a href="mailto:ehab.elrify@ibm.com" style="color:#1976D2;">ehab.elrify@ibm.com</a> | '
        '<a href="mailto:abdelrahman.maged@ibm.com" style="color:#1976D2;">abdelrahman.maged@ibm.com</a><br>'
        'Assurance Resolution Team</span>'
    )
    footer.setFont(font)
    footer.setAlignment(Qt.AlignCenter)
    footer.setOpenExternalLinks(True)
    layout.addWidget(footer)
    
    dialog.setLayout(layout)
    result = dialog.exec_()
    
    # Handle Support Mode
    support_agent = None
    if support_checkbox.isChecked() and result in [1, 2, 5]:
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
    """Launch the main menu of the application"""
    try:
        # Prepare environment for subprocess
        env = os.environ.copy()
        
        # Clear PyInstaller-induced variables
        for var in ['_MEIPASS2', '_MEIPASS', 'PYTHONPATH']:
            if var in env:
                del env[var]
        
        if getattr(sys, 'frozen', False):
            # In frozen app, sys.executable is the EXE
            subprocess.Popen([sys.executable], env=env)
        else:
            # Resolve path to src/main.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(current_dir)
            main_menu_path = os.path.join(src_dir, 'main.py')
            
            if os.path.exists(main_menu_path):
                subprocess.Popen([sys.executable, main_menu_path], env=env)
            else:
                print(f"[ERROR] Main menu not found at {main_menu_path}")
    except Exception as e:
        print(f"[ERROR] Failed to launch main menu: {e}")


def launch_config_update():
    """Launch configuration update dialog"""
    try:
        from config_loader import ConfigSetupDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        config_dialog = ConfigSetupDialog(CONFIG_MANAGER)
        config_dialog.exec_()
        
        # After config update, show mode selector again
        return show_mode_selector()
    except Exception as e:
        print(f"[ERROR] Failed to launch config dialog: {e}")
        return 0, None


def _show_settings_dialog():
    """
    Phase 5.4: Show settings dialog for UI customization.
    """
    try:
        from ui.settings_dialog import show_settings_dialog
        result = show_settings_dialog()
        if result:
            print("[INFO] ✓ Settings saved")
        else:
            print("[INFO] Settings cancelled")
    except Exception as e:
        print(f"[ERROR] Failed to show settings: {e}")
        QMessageBox.warning(None, "Error", f"Could not open settings: {e}")


def main():
    """Main entry point"""
    print("=" * 60)
    print("       ART Q CONTROL - Dispatcher (v2 Enhanced)")
    print("=" * 60)
    
    result, support_agent = show_mode_selector()
    
    if result == 1:  # Auto Sender
        print("[INFO] Starting Auto Sender mode...")
        # AutoSender will auto-load Excel from configured path, show popup if not found
        run_auto_sender(support_agent=support_agent)
        
    elif result == 2:  # Case Reviewer
        print("[INFO] Starting Case Reviewer mode...")
        run_case_reviewer(support_agent=support_agent)
    
    elif result == 5:  # Company Process (Phase 5.1 - NEW ISOLATED)
        print("[INFO] Starting Company Process mode (isolated)...")
        from CompaniesProcess_v2 import run_companies_process_standalone
        run_companies_process_standalone(support_agent=support_agent)
        
    elif result == 3:  # Update Configuration
        print("[INFO] Opening configuration dialog...")
        new_result, new_support_agent = launch_config_update()
        
        # Handle result from config dialog recursively
        if new_result == 1:
            run_auto_sender(support_agent=new_support_agent)
        elif new_result == 2:
            run_case_reviewer(support_agent=new_support_agent)
        elif new_result == 5:
            from CompaniesProcess_v2 import run_companies_process_standalone
            run_companies_process_standalone(support_agent=new_support_agent)
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
