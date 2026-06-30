# ============================================================================
# Dispatcher_v2.py - ART Q Control Entry Point (V2 Modernized)
# ============================================================================
# This is the main entry point for ART Q Control.
# Displays a welcome dialog with mode selection.
#
# CRITICAL: All PyQt5 and SharedFunctions imports are INSIDE functions
# to avoid "QWidget: Must construct a QApplication before a QWidget" error.
#
# Phase 6.10: Dispatcher Modernization
# - Integrated V2 design system (Colors, Spacing, BorderRadius)
# - Theme-aware styling (light/dark/auto support)
# - Typography system integration
# - Settings bus subscription for reactive updates
# - Lazy config loading after QApplication initialization
# ============================================================================

import os
import sys

# Ensure both src_v2 and this directory are in path for proper imports
# (path manipulation must happen before utils imports below)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_V2_DIR = os.path.dirname(CURRENT_DIR)

if SRC_V2_DIR not in sys.path:
    sys.path.insert(0, SRC_V2_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from utils.error_logger import log

# DO NOT import SharedFunctions at module level - lazy load after QApplication exists
# DO NOT import AutoSender_v2 or CaseReviewer_v2 at module level - they have PyQt5 imports!
# Import them inside functions when needed

_mode_result = {"mode": 0, "support_agent": None}
_app_instance = None  # Keep reference to QApplication to prevent garbage collection


def _ensure_app():
    """Ensure QApplication exists before any PyQt5 widget creation."""
    global _app_instance
    from PyQt5.QtWidgets import QApplication
    if _app_instance is None:
        _app_instance = QApplication.instance()
        if _app_instance is None:
            _app_instance = QApplication(sys.argv)
    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()
    return _app_instance


def _get_config_values():
    """
    Lazy load config after QApplication exists.
    
    SharedFunctions uses lazy loading via __getattr__, but import timing
    prevents proper initialization. This function ensures config is loaded
    after QApplication is created.
    
    Returns:
        dict: Configuration values (all config fields + config_manager)
    """
    import SharedFunctions
    
    # Trigger lazy loading by accessing CONFIG_MANAGER first (initializes everything)
    # config_loader.init_config() now correctly looks in src_v2 directory
    config_manager = SharedFunctions.CONFIG_MANAGER
    
    # Now all values should be loaded - return ALL config fields
    return {
        'agent_name': SharedFunctions.AGENT_NAME,
        'user_id': SharedFunctions.DIALER_USERNAME,
        'sheet_name': SharedFunctions.EXCEL_SHEET_NAME,
        'excel_base_path': SharedFunctions.EXCEL_BASE_PATH,
        'cache_directory': SharedFunctions.CACHE_DIRECTORY,
        'refresh_interval': SharedFunctions.REFRESH_INTERVAL,
        'place_id': SharedFunctions.DIALER_PLACE_ID,
        'config_manager': config_manager
    }


def show_mode_selector():
    """
    Display welcome window with mode selection.
    All PyQt5 imports are done INSIDE this function to avoid QApplication errors.
    
    Returns:
        tuple: (mode, support_agent) where mode is:
            1 = Auto Sender
            2 = Case Reviewer
            3 = Update Configuration
            4 = Main Menu
            5 = Companies Process
    """
    print("[DEBUG] Entered show_mode_selector()")
    # Ensure QApplication exists BEFORE importing any PyQt5 widgets
    print("[DEBUG] About to call _ensure_app()")
    _ensure_app()
    print("[DEBUG] _ensure_app() completed - QApplication exists")
    
    # Load config after QApplication exists
    print("[DEBUG] Loading configuration values")
    config = _get_config_values()
    print(f"[DEBUG] Config loaded: agent={config['agent_name']}, user={config['user_id']}, sheet={config['sheet_name']}")
    
    # NOW it's safe to import PyQt5 widgets and V2 systems
    print("[DEBUG] About to import PyQt5 widgets and V2 systems")
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
        QWidget, QFrame, QFileDialog, QMessageBox, QCheckBox, QLineEdit,
        QTextEdit, QSizePolicy, QScrollArea
    )
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QFont
    
    # Import V2 design system
    from ui.theme_manager import get_theme_manager
    from ui.services import get_v2_settings_bus, V2ThemeService
    from ui.design_system import Colors, Spacing, BorderRadius, Typography
    from ui.typography_mixin import V2TypographyMixin
    print("[DEBUG] PyQt5 widgets and V2 systems imported successfully")
    
    # Create dialog with V2 systems
    class ModeSelectionDialog(QDialog, V2TypographyMixin):
        """Mode selection dialog with V2 theme support."""
        
        def __init__(self, config_values):
            super().__init__()
            V2TypographyMixin.__init__(self)
            
            self.config = config_values
            
            # Initialize V2 systems
            self.theme_manager = get_theme_manager()
            self.settings_bus = get_v2_settings_bus()
            self.theme_service = V2ThemeService()
            
            # Subscribe to changes
            self.settings_bus.theme_changed.connect(self._apply_theme)
            self.settings_bus.font_size_changed.connect(self._apply_typography)
            self.settings_bus.dev_mode_changed.connect(self._on_dev_mode_changed)
            
            self.setWindowTitle("ART Q Control - Mode Selector")
            self.setMinimumSize(750, 720)
            self.resize(750, 720)
            
            self._setup_ui()
            self._apply_theme()
            self._apply_typography()
            QTimer.singleShot(0, self._position_dialog)
        
        def _get_stylesheet(self):
            """Generate theme-aware stylesheet using main menu and assigner styling patterns."""
            colors = self.theme_service.colors_for(self.settings_bus.theme)

            window_bg = colors.get('window_bg', '#eaf1ff')
            surface = colors.get('surface', '#ffffff')
            surface_alt = colors.get('surface_alt', '#f7faff')
            surface_border = colors.get('surface_border', '#c6d6f5')
            accent = colors.get('accent', '#0f62fe')
            accent_hover = colors.get('accent_hover', '#0353e9')
            accent_pressed = colors.get('accent_pressed', '#002d9c')
            accent_soft = colors.get('accent_soft', '#dbeafe')
            text_primary = colors.get('text_primary', '#0f172a')
            text_secondary = colors.get('text_secondary', '#334155')
            text_muted = colors.get('badge_border', surface_border)
            text_inverse = "#ffffff"
            footer_link = accent
            return f"""
                QDialog {{
                    background-color: {window_bg};
                    color: {text_primary};
                    font-family: 'IBM Plex Sans', Arial, sans-serif;
                }}

                QLabel {{
                    color: {text_primary};
                    background: transparent;
                }}

                QFrame#heroFrame {{
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 {surface},
                        stop: 1 {surface_alt}
                    );
                    border: 1px solid {surface_border};
                    border-radius: 20px;
                }}

                QLabel#eyebrowLabel {{
                    font-size: {self.get_size('body_sm')}px;
                    font-weight: 600;
                    color: {accent};
                    letter-spacing: 0.5px;
                    text-transform: uppercase;
                }}

                QLabel#titleLabel {{
                    font-size: {self.get_size('h1')}px;
                    font-weight: 700;
                    color: {text_primary};
                }}

                QLabel#subtitleLabel {{
                    font-size: {self.get_size('body')}px;
                    color: {text_secondary};
                    line-height: 1.4;
                }}

                QFrame#configFrame {{
                    background: {surface};
                    border: 1px solid {surface_border};
                    border-radius: 18px;
                }}

                QLabel#sectionTitleLabel {{
                    font-size: {self.get_size('h3')}px;
                    font-weight: 600;
                    color: {text_primary};
                }}

                QLabel#sectionHintLabel {{
                    font-size: {self.get_size('body_sm')}px;
                    color: {text_secondary};
                }}

                QLabel#configLabel {{
                    font-size: {self.get_size('body')}px;
                    padding: {Spacing.MD}px;
                    background-color: {surface_alt};
                    border: 1px solid {surface_border};
                    border-radius: 16px;
                    color: {text_secondary};
                }}

                QFrame.modeFrame,
                QFrame#supportFrame,
                QFrame#footerFrame {{
                    background: {surface};
                    border: 1px solid {surface_border};
                    border-radius: 18px;
                }}

                QFrame.modeFrame:hover {{
                    background: {surface_alt};
                    border: 2px solid {accent};
                }}

                QLabel#footerLabel {{
                    color: {text_secondary};
                    font-size: {self.get_size('body_sm')}px;
                }}

                QPushButton.modeButton {{
                    background: transparent;
                    color: {text_primary};
                    font-weight: 700;
                    font-size: {self.get_size('button')}px;
                    text-align: left;
                    padding: {Spacing.LG}px;
                    border-radius: 16px;
                    border: none;
                }}

                QPushButton.modeButton:hover {{
                    background-color: {surface_alt};
                }}

                QPushButton.modeButton:pressed {{
                    background-color: {accent_soft};
                }}

                QLabel.toolIcon {{
                    color: {accent};
                    font-size: {self.get_size('h2')}px;
                    font-weight: 600;
                    min-width: 40px;
                    background: transparent;
                }}

                QLabel.toolTitle {{
                    color: {text_primary};
                    font-size: {self.get_size('h3')}px;
                    font-weight: 600;
                    background: transparent;
                }}

                QLabel.toolDescription {{
                    color: {text_secondary};
                    font-size: {self.get_size('body_sm')}px;
                    background: transparent;
                }}

                QLabel.toolArrow {{
                    color: {text_muted};
                    font-size: {self.get_size('h3')}px;
                    font-weight: 600;
                    background: transparent;
                }}

                QPushButton.secondaryButton {{
                    background: transparent;
                    color: {accent};
                    border: 2px solid {accent};
                    border-radius: 12px;
                    padding: 12px 20px;
                    font-size: {self.get_size('button')}px;
                    font-weight: 700;
                    min-height: 48px;
                }}

                QPushButton.secondaryButton:hover {{
                    background: {accent_soft};
                }}

                QPushButton.secondaryButton:pressed {{
                    background: {surface_alt};
                }}

                QPushButton.primaryAction {{
                    background: {accent};
                    color: {text_inverse};
                    font-weight: 700;
                    font-size: {self.get_size('button')}px;
                    padding: 14px 22px;
                    border-radius: 12px;
                    border: none;
                    min-height: 48px;
                }}

                QPushButton.primaryAction:hover {{
                    background: {accent_hover};
                }}

                QPushButton.primaryAction:pressed {{
                    background: {accent_pressed};
                }}

                QCheckBox {{
                    color: {text_primary};
                    spacing: {Spacing.SM}px;
                    font-size: {self.get_size('body')}px;
                    font-weight: 500;
                }}

                QCheckBox::indicator {{
                    width: 20px;
                    height: 20px;
                    border-radius: {BorderRadius.SM}px;
                    border: 2px solid {surface_border};
                    background-color: {surface_alt};
                }}

                QCheckBox::indicator:hover {{
                    border-color: {accent};
                }}

                QCheckBox::indicator:checked {{
                    background-color: {accent};
                    border-color: {accent};
                }}

                QLabel#linkLabel a {{
                    color: {footer_link};
                    text-decoration: none;
                }}
            """
        
        def _apply_theme(self, theme=None):
            """Apply theme changes."""
            self.setStyleSheet(self._get_stylesheet())
        
        def _apply_typography(self, font_size=None):
            """Apply typography changes."""
            self._apply_theme()
            self._refresh_dynamic_content()
        
        def _position_dialog(self):
            """Position dialog higher on screen to avoid taskbar overlap."""
            from PyQt5.QtWidgets import QApplication
            desktop = QApplication.desktop()
            if desktop is None:
                return
            screen_geo = desktop.availableGeometry(self)
            x = screen_geo.x() + max(24, (screen_geo.width() - self.width()) // 2)
            y = screen_geo.y() + max(16, (screen_geo.height() - self.height()) // 8)
            self.move(x, y)

        def _truncate_path(self, path_str, max_length=54):
            """Truncate path in the middle if too long."""
            if len(path_str) <= max_length:
                return path_str
            start_len = max_length // 2 - 2
            end_len = max_length // 2 - 2
            return f"{path_str[:start_len]}...{path_str[-end_len:]}"

        def _on_dev_mode_changed(self, enabled: bool):
            """React live when DEV MODE changes (either from toggle in this dialog or from Settings)."""
            # Keep the toggle checkbox in sync with the bus
            if hasattr(self, 'dev_mode_toggle'):
                self.dev_mode_toggle.blockSignals(True)
                self.dev_mode_toggle.setChecked(enabled)
                self.dev_mode_toggle.blockSignals(False)
            # Swap name-input rows only when the support container is open
            if hasattr(self, 'support_single_row') and hasattr(self, 'support_name_container'):
                if self.support_name_container.isVisible():
                    self.support_single_row.setVisible(not enabled)
                    self.support_dev_row.setVisible(enabled)
                    if hasattr(self, 'support_name_input'):
                        self.support_name_input.clear()
                    if hasattr(self, 'support_names_multi'):
                        self.support_names_multi.clear()

        def _refresh_dynamic_content(self):
            """Refresh rich-text content so theme and font-size changes are reflected."""
            colors = self.theme_service.colors_for(self.settings_bus.theme)
            accent = colors.get('accent', colors.get('primary', '#0f62fe'))
            text_secondary = colors.get('text_secondary', '#525252')

            if hasattr(self, 'config_info'):
                excel_path_display = self._truncate_path(self.config.get('excel_base_path', 'Not configured'), 64)
                cache_path_display = self._truncate_path(self.config.get('cache_directory', 'Not configured'), 64)
                self.config_info.setText(
                    f"<table cellpadding='6' cellspacing='0' style='width: 100%;'>"
                    f"<tr><td style='width: 38%;'><b>Agent Name</b></td><td>{self.config.get('agent_name', 'Not configured')}</td></tr>"
                    f"<tr><td><b>User ID</b></td><td>{self.config.get('user_id', 'Not configured')}</td></tr>"
                    f"<tr><td><b>Place ID</b></td><td>{self.config.get('place_id', 'Not configured')}</td></tr>"
                    f"<tr><td><b>Sheet Name</b></td><td>{self.config.get('sheet_name', 'Not configured')}</td></tr>"
                    f"<tr><td><b>Excel Base Path</b></td><td title='{self.config.get('excel_base_path', '')}'>{excel_path_display}</td></tr>"
                    f"<tr><td><b>Cache Directory</b></td><td title='{self.config.get('cache_directory', '')}'>{cache_path_display}</td></tr>"
                    f"<tr><td><b>Refresh Interval</b></td><td>{self.config.get('refresh_interval', 'Not configured')} cases</td></tr>"
                    f"</table>"
                )

            if hasattr(self, 'footer_label'):
                self.footer_label.setText(
                    f'<span style="color:{text_secondary}; font-size: {self.get_size("body_sm")}px;">'
                    'Developed by: Ehab Elrify | Adam Maged<br>'
                    f'Email: <a href="mailto:ehab.elrify@ibm.com" style="color:{accent}; text-decoration:none;">ehab.elrify@ibm.com</a> | '
                    f'<a href="mailto:abdelrahman.maged@ibm.com" style="color:{accent}; text-decoration:none;">abdelrahman.maged@ibm.com</a><br>'
                    'Assurance Resolution Team</span>'
                )
        
        def _setup_ui(self):
            """Setup the UI components."""
            layout = QVBoxLayout()
            layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
            layout.setSpacing(Spacing.LG)

            # ========== HERO HEADER ==========
            hero_frame = QFrame()
            hero_frame.setObjectName("heroFrame")
            hero_layout = QVBoxLayout(hero_frame)
            hero_layout.setContentsMargins(26, 26, 26, 26)
            hero_layout.setSpacing(10)

            eyebrow = QLabel("ART Q MASTER V2")
            eyebrow.setObjectName("eyebrowLabel")
            eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hero_layout.addWidget(eyebrow)

            title = QLabel("ART Q Control")
            title.setObjectName("titleLabel")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hero_layout.addWidget(title)

            subtitle = QLabel("Choose a workflow to continue with the same modern experience used across the main menu and assigner.")
            subtitle.setObjectName("subtitleLabel")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setWordWrap(True)
            hero_layout.addWidget(subtitle)

            layout.addWidget(hero_frame)

            # ========== CONFIGURATION INFO ==========
            config_frame = QFrame()
            config_frame.setObjectName("configFrame")
            config_layout = QVBoxLayout(config_frame)
            config_layout.setContentsMargins(24, 24, 24, 24)
            config_layout.setSpacing(Spacing.SM)

            config_title = QLabel("Current Configuration")
            config_title.setObjectName("sectionTitleLabel")
            config_layout.addWidget(config_title)

            config_hint = QLabel("Loaded from the active configuration source. Values are read-only here and can be updated from configuration settings.")
            config_hint.setObjectName("sectionHintLabel")
            config_hint.setWordWrap(True)
            config_layout.addWidget(config_hint)

            excel_path_display = self._truncate_path(self.config.get('excel_base_path', 'Not configured'), 64)
            cache_path_display = self._truncate_path(self.config.get('cache_directory', 'Not configured'), 64)

            self.config_info = QLabel(
                f"<table cellpadding='6' cellspacing='0' style='width: 100%;'>"
                f"<tr><td style='width: 38%;'><b>Agent Name</b></td><td>{self.config.get('agent_name', 'Not configured')}</td></tr>"
                f"<tr><td><b>User ID</b></td><td>{self.config.get('user_id', 'Not configured')}</td></tr>"
                f"<tr><td><b>Place ID</b></td><td>{self.config.get('place_id', 'Not configured')}</td></tr>"
                f"<tr><td><b>Sheet Name</b></td><td>{self.config.get('sheet_name', 'Not configured')}</td></tr>"
                f"<tr><td><b>Excel Base Path</b></td><td title='{self.config.get('excel_base_path', '')}'>{excel_path_display}</td></tr>"
                f"<tr><td><b>Cache Directory</b></td><td title='{self.config.get('cache_directory', '')}'>{cache_path_display}</td></tr>"
                f"<tr><td><b>Refresh Interval</b></td><td>{self.config.get('refresh_interval', 'Not configured')} cases</td></tr>"
                f"</table>"
            )
            self.config_info.setObjectName("configLabel")
            self.config_info.setWordWrap(True)
            self.config_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            config_layout.addWidget(self.config_info)

            layout.addWidget(config_frame)

            # ========== MODE CARDS ==========
            mode_title = QLabel("Select a Mode")
            mode_title.setObjectName("sectionTitleLabel")
            layout.addWidget(mode_title)

            def build_mode_card(icon_text, title_text, description_text, result_code):
                frame = QFrame()
                frame.setProperty("class", "modeFrame")
                frame_layout = QVBoxLayout(frame)
                frame_layout.setContentsMargins(0, 0, 0, 0)
                frame_layout.setSpacing(0)

                button = QPushButton()
                button.setProperty("class", "modeButton")
                button.setCursor(Qt.CursorShape.PointingHandCursor)
                button.setMinimumHeight(112)
                button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                button.clicked.connect(lambda: self.done(result_code))

                button_layout = QHBoxLayout(button)
                button_layout.setContentsMargins(24, 20, 24, 20)
                button_layout.setSpacing(16)

                icon_label = QLabel(icon_text)
                icon_label.setProperty("class", "toolIcon")
                button_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

                text_container = QWidget()
                text_layout = QVBoxLayout(text_container)
                text_layout.setContentsMargins(0, 0, 0, 0)
                text_layout.setSpacing(Spacing.XS)

                title_label = QLabel(title_text)
                title_label.setProperty("class", "toolTitle")
                text_layout.addWidget(title_label)

                description_label = QLabel(description_text)
                description_label.setProperty("class", "toolDescription")
                description_label.setWordWrap(True)
                text_layout.addWidget(description_label)

                button_layout.addWidget(text_container, 1)

                arrow_label = QLabel("→")
                arrow_label.setProperty("class", "toolArrow")
                button_layout.addWidget(arrow_label, 0, Qt.AlignmentFlag.AlignCenter)

                frame_layout.addWidget(button)
                return frame

            auto_sender_frame = build_mode_card(
                "🚀",
                "AUTO SENDER",
                "Launch the automated sending workflow with the same polished card-based visual treatment as the main menu.",
                1
            )
            layout.addWidget(auto_sender_frame)

            case_reviewer_frame = build_mode_card(
                "📞",
                "CASE REVIEWER",
                "Open case review mode using the same modern surface, spacing, and action hierarchy as other upgraded v2 tools.",
                2
            )
            layout.addWidget(case_reviewer_frame)

            companies_frame = build_mode_card(
                "🏢",
                "COMPANIES PROCESS",
                "Start companies processing from a consistent tool card layout with improved readability and hover affordance.",
                5
            )
            layout.addWidget(companies_frame)

            # ========== SUPPORT MODE ==========
            support_frame = QFrame()
            support_frame.setObjectName("supportFrame")
            support_layout = QVBoxLayout(support_frame)
            support_layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
            support_layout.setSpacing(Spacing.SM)

            # Title row: "Optional Support Mode" + DEV MODE toggle on the right
            support_header_row = QHBoxLayout()
            support_title = QLabel("Optional Support Mode")
            support_title.setObjectName("sectionTitleLabel")
            support_header_row.addWidget(support_title)
            support_header_row.addStretch()
            self.dev_mode_toggle = QCheckBox("🛠 DEV MODE")
            self.dev_mode_toggle.setToolTip(
                "Enable multi-agent sheet names.\n"
                "Your own Agent Name (from config) is always used for signatures / notes."
            )
            # Style: red text when checked
            self.dev_mode_toggle.setStyleSheet(
                "QCheckBox { color: #6f6f6f; font-size: 11px; font-weight: bold; }"
                "QCheckBox:checked { color: #da1e28; }"
            )
            # Initialise from settings bus
            self.dev_mode_toggle.setChecked(self.settings_bus.dev_mode)
            support_header_row.addWidget(self.dev_mode_toggle)
            support_layout.addLayout(support_header_row)

            self.support_checkbox = QCheckBox("🤝 Supporting another agent")
            support_layout.addWidget(self.support_checkbox)

            # ── Name field container (shown only when support checkbox is checked) ──
            self.support_name_container = QWidget()
            support_name_layout = QVBoxLayout(self.support_name_container)
            support_name_layout.setContentsMargins(20, 4, 0, 0)
            support_name_layout.setSpacing(4)

            # Normal mode: single name
            self.support_single_row = QWidget()
            single_row_layout = QHBoxLayout(self.support_single_row)
            single_row_layout.setContentsMargins(0, 0, 0, 0)
            single_name_label = QLabel("Agent Name  (sheet: \"<Name>'s Cases\"):")
            single_name_label.setObjectName("sectionHintLabel")
            single_row_layout.addWidget(single_name_label)
            self.support_name_input = QLineEdit()
            self.support_name_input.setPlaceholderText("e.g.  Adam")
            self.support_name_input.setMaximumWidth(180)
            single_row_layout.addWidget(self.support_name_input)
            single_row_layout.addStretch()
            support_name_layout.addWidget(self.support_single_row)

            # DEV MODE: multi-name text area
            self.support_dev_row = QWidget()
            dev_row_layout = QVBoxLayout(self.support_dev_row)
            dev_row_layout.setContentsMargins(0, 0, 0, 0)
            dev_row_layout.setSpacing(3)
            dev_label = QLabel("Agent Sheet Names — one per line:")
            dev_label.setStyleSheet("font-weight: bold; color: #da1e28;")
            dev_row_layout.addWidget(dev_label)
            self.support_names_multi = QTextEdit()
            self.support_names_multi.setPlaceholderText(
                "Enter one agent name per line, e.g.:\nAdam\nEhab\nTeama"
            )
            self.support_names_multi.setFixedHeight(72)
            self.support_names_multi.setMaximumWidth(260)
            dev_row_layout.addWidget(self.support_names_multi)
            dev_hint = QLabel(
                "Each name → its own working sheet.  "
                "Your Agent Name (from config) is used for all signatures / notes."
            )
            dev_hint.setObjectName("sectionHintLabel")
            dev_hint.setWordWrap(True)
            dev_row_layout.addWidget(dev_hint)
            support_name_layout.addWidget(self.support_dev_row)

            # Start fully hidden; support checkbox reveals it
            self.support_name_container.setVisible(False)
            support_layout.addWidget(self.support_name_container)

            # ── Helper: swap single/multi rows based on dev-mode state ──
            def _refresh_name_rows():
                is_dev = self.dev_mode_toggle.isChecked()
                self.support_single_row.setVisible(not is_dev)
                self.support_dev_row.setVisible(is_dev)
                # clear stale input on switch
                self.support_name_input.clear()
                self.support_names_multi.clear()

            # Wire support checkbox
            def _on_support_toggled(state):
                is_checked = bool(state)
                self.support_name_container.setVisible(is_checked)
                if not is_checked:
                    self.support_name_input.clear()
                    self.support_names_multi.clear()
                else:
                    # ensure correct row is visible when container opens
                    _refresh_name_rows()
            self.support_checkbox.stateChanged.connect(_on_support_toggled)

            # Wire DEV MODE toggle
            def _on_dev_toggle(state):
                is_dev = bool(state)
                # persist to settings bus so other windows stay in sync
                self.settings_bus.set_dev_mode(is_dev)
                if self.support_name_container.isVisible():
                    _refresh_name_rows()
            self.dev_mode_toggle.stateChanged.connect(_on_dev_toggle)

            # Initial sub-row visibility
            _refresh_name_rows()

            layout.addWidget(support_frame)

            # ========== BOTTOM BUTTONS ==========
            bottom_layout = QHBoxLayout()
            bottom_layout.setSpacing(Spacing.MD)

            update_btn = QPushButton("⚙ Update Configuration")
            update_btn.setMinimumWidth(170)
            update_btn.setProperty("class", "primaryAction")
            update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            update_btn.clicked.connect(lambda: self.done(3))
            bottom_layout.addWidget(update_btn)

            main_menu_btn = QPushButton("☰ Main Menu")
            main_menu_btn.setMinimumWidth(170)
            main_menu_btn.setProperty("class", "secondaryButton")
            main_menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            main_menu_btn.clicked.connect(lambda: self.done(4))
            bottom_layout.addWidget(main_menu_btn)

            layout.addLayout(bottom_layout)

            # ========== FOOTER ==========
            footer_frame = QFrame()
            footer_frame.setObjectName("footerFrame")
            footer_layout = QVBoxLayout(footer_frame)
            footer_layout.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
            footer_layout.setSpacing(Spacing.XS)

            self.footer_label = QLabel()
            self.footer_label.setObjectName("footerLabel")
            self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.footer_label.setOpenExternalLinks(True)
            self.footer_label.setTextFormat(Qt.TextFormat.RichText)
            footer_layout.addWidget(self.footer_label)

            layout.addWidget(footer_frame)

            self.setLayout(layout)
            self._refresh_dynamic_content()
    
    # Create and show dialog
    dialog = ModeSelectionDialog(config)
    result = dialog.exec_()

    # ── Collect support-agent names from the inline fields ──────────────
    # support_agents is now a list[str] (may be empty, single, or multi).
    # Signatures / case notes always use the config AGENT_NAME (never the supported names).
    support_agents: list = []
    if dialog.support_checkbox.isChecked() and result in [1, 2, 5]:
        is_dev = dialog.dev_mode_toggle.isChecked()   # use the dialog's own toggle
        if is_dev:
            raw = dialog.support_names_multi.toPlainText()
            support_agents = [n.strip() for n in raw.splitlines() if n.strip()]
        else:
            single = dialog.support_name_input.text().strip()
            if single:
                support_agents = [single]

        if support_agents:
            log("info", f"Support mode enabled for: {', '.join(support_agents)}", "Dispatcher")
        else:
            log("info", "Support checkbox was checked but no agent name entered — running in own-agent mode", "Dispatcher")

    # Backward-compat: expose the first name (or None) as a single value
    support_agent = support_agents[0] if support_agents else None

    _mode_result["mode"] = result
    _mode_result["support_agent"] = support_agent
    _mode_result["support_agents"] = support_agents

    return result, support_agents


def main():
    """Main entry point for ART Q Control."""
    # Install crash handler so Ctrl+C in the terminal exits cleanly
    try:
        from utils.crash_handler import install_crash_handler, enable_qt_sigint_heartbeat
        install_crash_handler()
        # Enable Ctrl+C in terminal while Qt event loop is running (Windows fix)
        enable_qt_sigint_heartbeat(_ensure_app())
    except Exception:
        pass

    print("=" * 60)
    print("       ART Q CONTROL - Dispatcher (v2 Enhanced)")
    print("=" * 60)
    print("[DEBUG] About to call show_mode_selector()")

    result, support_agents = show_mode_selector()
    # support_agents is list[str]; may be [] (own-agent mode), [name] (single), or [n1, n2, …] (DEV MODE)
    print(f"[DEBUG] show_mode_selector() returned: result={result}, support_agents={support_agents}")

    if result == 1:  # Auto Sender
        log("info", "Starting Auto Sender mode...", "Dispatcher")
        from AutoSender_v2 import run_auto_sender
        run_auto_sender(support_agents=support_agents)
        main()

    elif result == 2:  # Case Reviewer
        log("info", "Starting Case Reviewer mode...", "Dispatcher")
        from CaseReviewer_v2 import run_case_reviewer
        run_case_reviewer(support_agents=support_agents)
        main()

    elif result == 5:  # Companies Process
        log("info", "Starting Companies Process mode...", "Dispatcher")
        from CompaniesProcess_v2 import run_companies_process_standalone
        run_companies_process_standalone(support_agents=support_agents)
        main()

    elif result == 3:  # Update Configuration
        log("info", "Opening configuration setup...", "Dispatcher")
        from config_loader import ConfigSetupDialog
        from PyQt5.QtWidgets import QDialog
        # Load config again to get CONFIG_MANAGER
        config = _get_config_values()
        dialog = ConfigSetupDialog(config['config_manager'])

        if dialog.exec_() == QDialog.Accepted:
            log("info", "Configuration updated successfully", "Dispatcher")
            # After config update, return to mode selector
            main()
        else:
            log("info", "Configuration update cancelled", "Dispatcher")

    elif result == 4:  # Main Menu
        log("info", "Returning to main menu...", "Dispatcher")
        # Return to main menu (handled by caller)
        return

    else:
        log("info", "Exiting ART Q Control.", "Dispatcher")


if __name__ == "__main__":
    import os
    main()
    # All dialogs closed — exit immediately so any lingering threads don't
    # keep the process alive in the background / terminal.
    os._exit(0)

# Made with Bob
