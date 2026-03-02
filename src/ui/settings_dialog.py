# ============================================================================
# settings_dialog.py - Settings/Preferences Dialog
# ============================================================================
# Phase 5.4: UI Settings & Customization
#
# Provides user-facing controls for:
# - Theme switching (Light/Dark mode)
# - Font size adjustment (80% to 200%)
# - Keyboard navigation and screen reader options
# - Sound effects on/off
# - Auto-save preferences
# ============================================================================

import sys
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider,
    QComboBox, QCheckBox, QGroupBox, QWidget, QGridLayout, QSpinBox,
    QMessageBox, QFrame, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# Lazy imports to avoid QApplication issues
theme_manager = None
accessibility_manager = None
app = None


class SettingsDialog(QDialog):
    """
    Settings dialog for user preferences.
    
    Signals:
    - theme_changed(light/dark)
    - font_size_changed(scale: 0.8-2.0)
    - accessibility_changed(settings_dict)
    """
    
    theme_changed = pyqtSignal(str)  # 'light' or 'dark'
    font_size_changed = pyqtSignal(float)  # 0.8 to 2.0
    accessibility_changed = pyqtSignal(dict)  # Keyboard, screen reader, etc
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Preferences")
        self.setMinimumWidth(600)
        self.setMinimumHeight(650)
        self.setModal(True)
        
        # Initialize managers
        self._init_managers()
        
        # Get current settings
        self.current_theme = getattr(theme_manager, 'current_theme', None)
        if self.current_theme:
            self.current_theme = self.current_theme.value if hasattr(self.current_theme, 'value') else 'light'
        else:
            self.current_theme = 'light'
        
        self.current_scale = getattr(accessibility_manager, 'text_scaler', None)
        if self.current_scale:
            scale_value = getattr(self.current_scale, 'scale_factor', 22)
            # If scale_value is a percentage (e.g., 1.0, 1.5), convert to pixels
            # If it's already in pixels (15-30), use as-is
            if scale_value < 15:
                # It's a scale factor, convert to pixels (assume base 15px)
                self.current_scale = max(15, min(30, int(scale_value * 15)))
            else:
                # It's already in pixels
                self.current_scale = max(15, min(30, int(scale_value)))
        else:
            self.current_scale = 22  # Default to 22px
        
        # Setup UI
        self._setup_ui()
        
        # Apply theme to dialog
        if theme_manager:
            self._apply_theme()
    
    def _init_managers(self):
        """Initialize theme and accessibility managers."""
        global theme_manager, accessibility_manager, app
        
        try:
            from ui.theme_manager import get_theme_manager
            from ui.accessibility_helper import get_accessibility_manager
            
            theme_manager = get_theme_manager()
            accessibility_manager = get_accessibility_manager()
            app = QApplication.instance()
        except Exception as e:
            print(f"[WARNING] Could not load managers: {e}")
    
    def _setup_ui(self):
        """Setup dialog UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Title
        title = QLabel("Settings & Preferences")
        title_font = QFont()
        title_font.setPointSize(17)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # ===== APPEARANCE SECTION =====
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout()
        appearance_layout.setSpacing(12)
        
        # Theme selector
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        theme_font = QFont()
        theme_font.setPointSize(15)
        theme_label.setFont(theme_font)
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["☀️ Light", "🌙 Dark"])
        self.theme_combo.setCurrentIndex(0 if self.current_theme == 'light' else 1)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.theme_combo.setMinimumWidth(200)
        theme_font.setPointSize(13)
        self.theme_combo.setFont(theme_font)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)
        
        appearance_group.setLayout(appearance_layout)
        main_layout.addWidget(appearance_group)
        
        # ===== FONT & TEXT SECTION =====
        font_group = QGroupBox("Font & Text")
        font_layout = QVBoxLayout()
        font_layout.setSpacing(12)
        
        # Font size slider
        font_size_layout = QVBoxLayout()
        
        font_size_top = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        font_size_font = QFont()
        font_size_font.setPointSize(15)
        font_size_label.setFont(font_size_font)
        font_size_top.addWidget(font_size_label)
        
        self.font_size_percent = QLabel(f"{int(self.current_scale)}px")
        self.font_size_percent.setStyleSheet("color: #0f62fe; font-weight: bold;")
        font_percent_font = QFont()
        font_percent_font.setPointSize(13)
        self.font_size_percent.setFont(font_percent_font)
        font_size_top.addWidget(self.font_size_percent)
        font_size_top.addStretch()
        font_size_layout.addLayout(font_size_top)
        
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setMinimum(10)  # 10px minimum
        self.font_size_slider.setMaximum(40)  # 40px maximum (was 20px - too limited)
        self.font_size_slider.setValue(int(self.current_scale))
        self.font_size_slider.setTickPosition(QSlider.TicksBelow)
        self.font_size_slider.setTickInterval(5)  # Increased from 3 for 10-40 range
        self.font_size_slider.valueChanged.connect(self._on_font_size_changed)
        slider_font = QFont()
        slider_font.setPointSize(13)
        self.font_size_slider.setFont(slider_font)
        font_size_layout.addWidget(self.font_size_slider)
        
        # Enhanced size indicators with descriptions
        size_indicators = QHBoxLayout()
        
        small = QLabel("Small\n(10px)\nMore content fits")
        small_font = QFont()
        small_font.setPointSize(8)
        small.setFont(small_font)
        small.setAlignment(Qt.AlignCenter)
        size_indicators.addWidget(small)
        size_indicators.addStretch()
        
        medium = QLabel("Default\n(22px)\nOptimal readability")
        medium_font = QFont()
        medium_font.setPointSize(10)
        medium_font.setBold(True)
        medium.setFont(medium_font)
        medium.setAlignment(Qt.AlignCenter)
        size_indicators.addWidget(medium)
        size_indicators.addStretch()
        
        large = QLabel("Large\n(40px)\nBetter accessibility")
        large_font = QFont()
        large_font.setPointSize(8)
        large.setFont(large_font)
        large.setAlignment(Qt.AlignCenter)
        size_indicators.addWidget(large)
        
        font_size_layout.addLayout(size_indicators)
        
        font_layout.addLayout(font_size_layout)
        font_group.setLayout(font_layout)
        main_layout.addWidget(font_group)
        
        # ===== ACCESSIBILITY SECTION =====
        a11y_group = QGroupBox("Accessibility")
        a11y_layout = QVBoxLayout()
        a11y_layout.setSpacing(12)
        
        # Keyboard navigation
        self.keyboard_nav_check = QCheckBox("⌨️ Enable Keyboard Navigation")
        self.keyboard_nav_check.setChecked(True)
        self.keyboard_nav_check.stateChanged.connect(self._on_keyboard_nav_toggled)
        check_font = QFont()
        check_font.setPointSize(13)
        self.keyboard_nav_check.setFont(check_font)
        a11y_layout.addWidget(self.keyboard_nav_check)
        
        # Screen reader mode
        self.screen_reader_check = QCheckBox("🔊 Screen Reader Mode")
        self.screen_reader_check.setChecked(False)
        self.screen_reader_check.stateChanged.connect(self._on_screen_reader_toggled)
        self.screen_reader_check.setFont(check_font)
        a11y_layout.addWidget(self.screen_reader_check)
        
        a11y_group.setLayout(a11y_layout)
        main_layout.addWidget(a11y_group)
        
        # ===== AUDIO SECTION =====
        audio_group = QGroupBox("Audio & Feedback")
        audio_layout = QVBoxLayout()
        audio_layout.setSpacing(12)
        
        # Sound effects
        self.sound_effects_check = QCheckBox("🔔 Enable Sound Effects")
        self.sound_effects_check.setChecked(False)
        self.sound_effects_check.setFont(check_font)
        audio_layout.addWidget(self.sound_effects_check)
        
        # Dialog notifications
        self.notifications_check = QCheckBox("📬 Dialog Notifications")
        self.notifications_check.setChecked(True)
        self.notifications_check.setFont(check_font)
        audio_layout.addWidget(self.notifications_check)
        
        audio_group.setLayout(audio_layout)
        main_layout.addWidget(audio_group)
        
        # ===== BUTTONS SECTION =====
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        reset_btn = QPushButton("↺ Reset to Defaults")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self._on_reset_defaults)
        reset_font = QFont()
        reset_font.setPointSize(13)
        reset_btn.setFont(reset_font)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #333;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("✓ Close Settings")
        close_btn.setMinimumHeight(40)
        close_btn.setMinimumWidth(150)
        close_btn.clicked.connect(self.accept)
        close_btn.setFont(reset_font)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #0f62fe;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0353e9;
            }
        """)
        button_layout.addWidget(close_btn)
        
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
    
    def _on_theme_changed(self, index):
        """Handle theme selection change."""
        new_theme = 'light' if index == 0 else 'dark'
        
        if theme_manager and app:
            try:
                from ui.theme_manager import ThemeMode
                from ui.settings_observer import get_settings_observer
                
                # Set theme in manager
                theme_mode = ThemeMode.LIGHT if new_theme == 'light' else ThemeMode.DARK
                theme_manager.set_theme(theme_mode)
                
                # Apply stylesheet to entire application
                stylesheet = theme_manager.get_stylesheet()
                app.setStyleSheet(stylesheet)
                
                # Broadcast change to all observers
                observer = get_settings_observer()
                observer.notify_theme_changed(new_theme)
                
                self.current_theme = new_theme
                self._apply_theme()
                self.theme_changed.emit(new_theme)
                print(f"[INFO] ✓ Theme changed to {new_theme} and applied to application")
            except Exception as e:
                print(f"[ERROR] Failed to change theme: {e}")
    
    def _on_font_size_changed(self, value):
        """Handle font size slider change (value is in pixels)."""
        # value is now in pixels (15-30), not percentage
        self.font_size_percent.setText(f"{value}px")
        
        if accessibility_manager and app:
            try:
                from ui.settings_observer import get_settings_observer
                
                # Store the pixel size directly
                accessibility_manager.text_scaler.scale_factor = value
                
                # Apply font scaling to the entire application
                self._apply_font_scale_to_app(value)
                
                # Broadcast change to all observers (pass pixel size)
                observer = get_settings_observer()
                observer.notify_font_size_changed(value)
                
                # Save to config.json
                self._save_font_size_to_config(value)
                
                self.current_scale = value
                self.font_size_changed.emit(value)
                print(f"[INFO] ✓ Font size changed to {value}px and applied to application")
            except Exception as e:
                print(f"[ERROR] Failed to change font size: {e}")
    
    def _apply_font_scale_to_app(self, size_in_pixels):
        """Apply font size to entire application (size_in_pixels: 15-30)."""
        try:
            if not app:
                return
            
            # Clamp to valid range
            size_in_pixels = max(15, min(30, size_in_pixels))
            
            base_font = app.font()
            base_font.setPointSize(int(size_in_pixels))
            
            # Apply to application
            app.setFont(base_font)
            print(f"[INFO] Applied font size {size_in_pixels}px to application")
        except Exception as e:
            print(f"[WARNING] Could not apply font size: {e}")
    
    def _on_keyboard_nav_toggled(self, state):
        """Handle keyboard navigation toggle."""
        enabled = state == Qt.Checked
        self.accessibility_changed.emit({'keyboard_nav': enabled})
        status = "enabled" if enabled else "disabled"
        print(f"[INFO] ✓ Keyboard navigation {status}")
    
    def _on_screen_reader_toggled(self, state):
        """Handle screen reader toggle."""
        enabled = state == Qt.Checked
        self.accessibility_changed.emit({'screen_reader': enabled})
        status = "enabled" if enabled else "disabled"
        print(f"[INFO] ✓ Screen reader {status}")
    
    def _on_reset_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to defaults?\n\nTheme: Light\nFont Size: 22px (Default)\nAccessibility: Standard",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset theme
            self.theme_combo.setCurrentIndex(0)
            
            # Reset font size to default (22px)
            self.font_size_slider.setValue(22)
            
            # Reset accessibility
            self.keyboard_nav_check.setChecked(True)
            self.screen_reader_check.setChecked(False)
            
            print("[INFO] ✓ Settings reset to defaults")
    
    def _apply_theme(self):
        """Apply current theme to dialog."""
        if not theme_manager:
            return
        
        try:
            # Get theme colors
            bg_color = "#FAFAFA" if self.current_theme == 'light' else "#1E1E1E"
            text_color = "#333333" if self.current_theme == 'light' else "#FFFFFF"
            
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {bg_color};
                }}
                QLabel {{
                    color: {text_color};
                }}
                QGroupBox {{
                    color: {text_color};
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                    padding-top: 8px;
                    margin-top: 8px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px 0 3px;
                }}
                QCheckBox {{
                    color: {text_color};
                }}
                QComboBox {{
                    color: {text_color};
                    background-color: {"#FFFFFF" if self.current_theme == 'light' else "#2E2E2E"};
                    border: 1px solid #999;
                    border-radius: 4px;
                    padding: 6px;
                }}
            """)
        except Exception as e:
            print(f"[WARNING] Could not apply theme: {e}")
    
    def _save_font_size_to_config(self, font_size):
        """Save font size to config.json."""
        try:
            import json
            import os
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')
            
            # Read existing config
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            
            # Add or update ui_settings
            if 'ui_settings' not in config:
                config['ui_settings'] = {}
            
            config['ui_settings']['font_size'] = font_size
            
            # Write back to config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            print(f"[INFO] Font size {font_size}px saved to config.json")
        except Exception as e:
            print(f"[WARNING] Could not save font size to config: {e}")


def show_settings_dialog(parent=None):
    """
    Show settings dialog and return whether settings were saved.
    
    Returns:
        bool: True if user clicked Close (accepted), False if cancelled
    """
    dialog = SettingsDialog(parent)
    result = dialog.exec_()
    return result == QDialog.Accepted
