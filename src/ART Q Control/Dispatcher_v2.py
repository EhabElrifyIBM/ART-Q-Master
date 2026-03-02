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
from ibm_theme import get_qss, get_mode_card_style, IBM, _read_font_size

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
    # Detect current theme
    try:
        import json as _json
        _theme_cfg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'theme_config.json')
        _current_theme = 'light'
        if os.path.exists(_theme_cfg):
            with open(_theme_cfg, 'r') as _f:
                _current_theme = _json.load(_f).get('theme', 'light')
        if _current_theme == 'auto':
            try:
                import winreg
                _key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize')
                _val, _ = winreg.QueryValueEx(_key, 'AppsUseLightTheme')
                _current_theme = 'light' if _val else 'dark'
            except Exception:
                _current_theme = 'light'
    except Exception:
        _current_theme = 'light'

    _font_size = _read_font_size()

    class ModeSelectionDialog(QDialog):
        def __init__(self):
            super().__init__()
            self._theme = _current_theme
            self._apply_theme(self._theme)
            font = QFont('IBM Plex Sans', _font_size)
            self.setFont(font)

        def _apply_theme(self, theme: str):
            self._theme = theme
            self.setStyleSheet(get_qss(theme, _font_size))

        def on_theme_changed(self, theme: str):
            """Handle theme changes — now actually applies the new QSS."""
            self._apply_theme(theme)

        def on_font_size_changed(self, scale: float):
            pass  # Font is set at dialog creation from config

    dialog = ModeSelectionDialog()
    font = QFont('IBM Plex Sans', _font_size)
    dialog.setWindowTitle("ART Q Control — Mode Selector")
    dialog.setMinimumSize(560, 720)
    dialog.setMaximumSize(700, 820)
    dialog.resize(580, 740)
    dialog.setFont(font)
    
    # Root layout
    layout = QVBoxLayout()
    layout.setContentsMargins(28, 20, 28, 16)
    layout.setSpacing(0)

    # ========== HEADER ==========
    c = IBM.DARK if _current_theme == 'dark' else IBM.LIGHT

    # App logo row
    header_row = QHBoxLayout()
    header_row.setSpacing(0)
    badge = QLabel("ART")
    badge.setFixedSize(44, 44)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(
        f"background: {c['interactive']}; color: #ffffff;"
        f" font-family: 'IBM Plex Sans','Segoe UI',Arial;"
        f" font-size: {_font_size}pt; font-weight: 800;"
        f" border-radius: 4px;"
    )
    header_row.addWidget(badge)
    header_row.addSpacing(12)

    title_col = QVBoxLayout()
    title_col.setSpacing(0)
    title = QLabel("ART Q Control")
    title.setFont(QFont('IBM Plex Sans', _font_size + 2, QFont.Bold))
    title.setStyleSheet(f"font-weight: 700; color: {c['text_primary']}; background: transparent;")
    subtitle_lbl = QLabel("Automation · IBM Assurance Resolution Team")
    subtitle_lbl.setFont(QFont('IBM Plex Sans', _font_size - 3))
    subtitle_lbl.setStyleSheet(f"color: {c['text_secondary']}; background: transparent;")
    title_col.addWidget(title)
    title_col.addWidget(subtitle_lbl)
    header_row.addLayout(title_col)
    header_row.addStretch()
    layout.addLayout(header_row)
    layout.addSpacing(16)

    # ========== CONFIG INFO CARD (Compact) ==========
    config_frame = QFrame()
    config_frame.setStyleSheet(
        f"background-color: {c['layer_01']};"
        f"border-left: 3px solid {c['interactive']};"
        f"border-top: 1px solid {c['border_subtle']};"
        f"border-right: 1px solid {c['border_subtle']};"
        f"border-bottom: 1px solid {c['border_subtle']};"
        f"border-radius: 0px;"
    )
    config_layout = QVBoxLayout(config_frame)
    config_layout.setContentsMargins(12, 8, 12, 8)
    config_layout.setSpacing(2)

    config_title = QLabel("SESSION CONFIG")
    config_title.setFont(QFont('IBM Plex Sans', _font_size - 4, QFont.Bold))
    config_title.setStyleSheet(
        f"font-weight: 700; color: {c['text_secondary']};"
        f" letter-spacing: 1px; background: transparent; border: none;"
    )
    config_layout.addWidget(config_title)

    config_info = QLabel(
        f"<table cellpadding='2'>"
        f"<tr><td style='color:{c['text_secondary']};'><b>Agent</b></td>"
        f"<td style='padding-left:12px;color:{c['text_primary']};'>{AGENT_NAME}</td>"
        f"<td style='padding-left:20px;color:{c['text_secondary']};'><b>User&nbsp;ID</b></td>"
        f"<td style='padding-left:12px;color:{c['text_primary']};'>{DIALER_USERNAME}</td></tr>"
        f"<tr><td style='color:{c['text_secondary']};'><b>Sheet</b></td>"
        f"<td style='padding-left:12px;color:{c['text_primary']};'>{EXCEL_SHEET_NAME}</td>"
        f"<td style='padding-left:20px;color:{c['text_secondary']};'><b>Excel</b></td>"
        f"<td style='padding-left:12px;color:{c['text_primary']};font-size:{_font_size-4}pt;'>{EXCEL_BASE_PATH}</td></tr>"
        f"</table>"
    )
    config_info.setFont(QFont('IBM Plex Sans', _font_size - 2))
    config_info.setStyleSheet(f"background: transparent; border: none;")
    config_info.setWordWrap(True)
    config_layout.addWidget(config_info)
    layout.addWidget(config_frame)
    layout.addSpacing(20)

    # ========== SECTION LABEL: SELECT MODE ==========
    mode_label = QLabel("SELECT MODE")
    mode_label.setFont(QFont('IBM Plex Sans', _font_size - 4, QFont.Bold))
    mode_label.setStyleSheet(
        f"color: {c['text_secondary']}; letter-spacing: 1px;"
        f" font-weight: 700; background: transparent;"
        f" border-bottom: 1px solid {c['border_subtle']};"
        f" padding-bottom: 4px;"
    )
    layout.addWidget(mode_label)
    layout.addSpacing(8)

    # ========== MODE BUTTONS — IBM Accent Cards ==========
    _mode_btn_style_base = (
        "QPushButton {{ "
        "  background-color: {bg}; color: #ffffff;"
        "  border: none; border-radius: 4px;"
        "  font-family: 'IBM Plex Sans','Segoe UI',Arial;"
        "  font-size: {fs}pt; font-weight: 700;"
        "  padding: 0 20px;"
        "  text-align: left;"
        "}}"
        "QPushButton:hover {{ background-color: {hover}; }}"
        "QPushButton:pressed {{ background-color: {active}; }}"
    )

    # Auto Sender — IBM Blue
    auto_sender_btn = QPushButton()
    auto_sender_btn.setText(
        f"Auto Sender\n"
        f"Process new cases  ·  SMS + Email + Case Note"
    )
    auto_sender_btn.setFont(QFont('IBM Plex Sans', _font_size, QFont.Bold))
    auto_sender_btn.setFixedHeight(76)
    auto_sender_btn.setStyleSheet(
        _mode_btn_style_base.format(
            bg=c['interactive'],
            hover=c['interactive_hover'],
            active=c.get('interactive_active', c['interactive_hover']),
            fs=_font_size
        )
    )
    auto_sender_btn.clicked.connect(lambda: dialog.done(1))
    layout.addWidget(auto_sender_btn)
    layout.addSpacing(8)

    # Case Reviewer — IBM Purple
    case_reviewer_btn = QPushButton()
    case_reviewer_btn.setText(
        f"Case Reviewer\n"
        f"Review in-progress cases  ·  With Dialer"
    )
    case_reviewer_btn.setFont(QFont('IBM Plex Sans', _font_size, QFont.Bold))
    case_reviewer_btn.setFixedHeight(76)
    case_reviewer_btn.setStyleSheet(
        _mode_btn_style_base.format(
            bg=c['purple'],
            hover=c['purple_hover'],
            active=c['purple_hover'],
            fs=_font_size
        )
    )
    case_reviewer_btn.clicked.connect(lambda: dialog.done(2))
    layout.addWidget(case_reviewer_btn)
    layout.addSpacing(8)

    # Company Process — IBM Teal
    company_process_btn = QPushButton()
    company_process_btn.setText(
        f"Company Process\n"
        f"Batch process grouped company cases"
    )
    company_process_btn.setFont(QFont('IBM Plex Sans', _font_size, QFont.Bold))
    company_process_btn.setFixedHeight(76)
    company_process_btn.setStyleSheet(
        _mode_btn_style_base.format(
            bg=c['teal'],
            hover=c['teal_hover'],
            active=c['teal_hover'],
            fs=_font_size
        )
    )
    company_process_btn.clicked.connect(lambda: dialog.done(5))
    layout.addWidget(company_process_btn)
    layout.addSpacing(16)

    # ========== SUPPORT CHECKBOX ==========
    support_checkbox = QCheckBox("Supporting another agent")
    support_checkbox.setFont(QFont('IBM Plex Sans', _font_size - 1))
    support_checkbox.setStyleSheet(f"color: {c['text_primary']}; background: transparent;")
    layout.addWidget(support_checkbox)
    layout.addSpacing(12)

    # ========== UTILITY ROW: ghost buttons on one line ==========
    _ghost = (
        f"QPushButton {{ background-color: transparent; color: {c['text_secondary']};"
        f" border: 1px solid {c['border_subtle']}; border-radius: 4px;"
        f" font-family: 'IBM Plex Sans','Segoe UI',Arial; font-size: {_font_size - 2}pt;"
        f" padding: 8px 14px; min-height: 36px; }}"
        f"QPushButton:hover {{ background-color: {c['layer_02']}; color: {c['text_primary']}; }}"
    )
    bottom_layout = QHBoxLayout()
    bottom_layout.setSpacing(10)

    update_btn = QPushButton("Update Configuration")
    update_btn.setFont(QFont('IBM Plex Sans', _font_size - 2))
    update_btn.setStyleSheet(_ghost)
    update_btn.clicked.connect(lambda: dialog.done(3))
    bottom_layout.addWidget(update_btn)

    main_menu_btn = QPushButton("Main Menu")
    main_menu_btn.setFont(QFont('IBM Plex Sans', _font_size - 2))
    main_menu_btn.setStyleSheet(_ghost)
    main_menu_btn.clicked.connect(lambda: dialog.done(4))
    bottom_layout.addWidget(main_menu_btn)
    bottom_layout.addStretch()
    layout.addLayout(bottom_layout)

    layout.addStretch(1)

    # ========== FOOTER ==========
    footer = QLabel(
        f'<span style="color:{c["text_secondary"]};font-size:{_font_size - 4}pt;">'
        'Developed by Ehab Elrify · Adam Maged · Assurance Resolution Team</span>'
    )
    footer.setFont(QFont('IBM Plex Sans', _font_size - 4))
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
