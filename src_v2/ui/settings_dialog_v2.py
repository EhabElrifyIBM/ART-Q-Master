"""
Enhanced Settings Dialog V2 - Phase 7.5
Modern settings dialog with 5 tabs, import/export, and V2 styling.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QSpinBox, QGroupBox, QFileDialog, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..config.manager import config_manager
from ..config.backup import ConfigBackup
from ..config.security import ConfigSecurity
from .services import get_v2_settings_bus


class SettingsDialogV2(QDialog):
    """
    Enhanced settings dialog with 5 tabs:
    1. Appearance - Theme, fonts, animations
    2. Automation - Agent settings, automation options
    3. Accessibility - High contrast, screen reader, keyboard nav
    4. Advanced - Debug, logging, backups
    5. About - Version info, credits
    """
    
    settings_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(700, 600)
        self.setModal(True)
        
        # Get settings bus
        self.settings_bus = get_v2_settings_bus()
        
        # Setup fonts
        self.base_font = QFont("Segoe UI", 10)
        self.heading_font = QFont("Segoe UI", 11, QFont.Bold)
        
        # Setup UI
        self._setup_ui()
        
        # Load current settings
        self._load_settings()
        
        # Apply theme
        self._apply_theme()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setFont(self.base_font)
        
        # Create tabs
        self.appearance_tab = self._create_appearance_tab()
        self.automation_tab = self._create_automation_tab()
        self.accessibility_tab = self._create_accessibility_tab()
        self.advanced_tab = self._create_advanced_tab()
        self.about_tab = self._create_about_tab()
        
        # Add tabs
        self.tabs.addTab(self.appearance_tab, "Appearance")
        self.tabs.addTab(self.automation_tab, "Automation")
        self.tabs.addTab(self.accessibility_tab, "Accessibility")
        self.tabs.addTab(self.advanced_tab, "Advanced")
        self.tabs.addTab(self.about_tab, "About")
        
        layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Import/Export buttons
        self.import_btn = QPushButton("Import Settings")
        self.import_btn.setFont(self.base_font)
        self.import_btn.clicked.connect(self._import_settings)
        button_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("Export Settings")
        self.export_btn.setFont(self.base_font)
        self.export_btn.clicked.connect(self._export_settings)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addSpacing(20)
        
        # OK/Cancel buttons
        self.ok_btn = QPushButton("OK")
        self.ok_btn.setFont(self.base_font)
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setFont(self.base_font)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_appearance_tab(self) -> QWidget:
        """Create appearance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_group.setFont(self.heading_font)
        theme_layout = QVBoxLayout()
        
        theme_label = QLabel("Theme Mode:")
        theme_label.setFont(self.base_font)
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.setFont(self.base_font)
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        theme_layout.addWidget(self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Font group
        font_group = QGroupBox("Font")
        font_group.setFont(self.heading_font)
        font_layout = QVBoxLayout()
        
        font_label = QLabel("Font Size:")
        font_label.setFont(self.base_font)
        font_layout.addWidget(font_label)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setFont(self.base_font)
        self.font_size_spin.setRange(10, 30)
        self.font_size_spin.setSuffix(" pt")
        font_layout.addWidget(self.font_size_spin)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # UI Options group
        ui_group = QGroupBox("UI Options")
        ui_group.setFont(self.heading_font)
        ui_layout = QVBoxLayout()
        
        self.animations_check = QCheckBox("Enable Animations")
        self.animations_check.setFont(self.base_font)
        ui_layout.addWidget(self.animations_check)
        
        self.compact_check = QCheckBox("Compact Mode")
        self.compact_check.setFont(self.base_font)
        ui_layout.addWidget(self.compact_check)
        
        ui_group.setLayout(ui_layout)
        layout.addWidget(ui_group)
        
        layout.addStretch()
        return widget
    
    def _create_automation_tab(self) -> QWidget:
        """Create automation settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Agent group
        agent_group = QGroupBox("Agent Information")
        agent_group.setFont(self.heading_font)
        agent_layout = QVBoxLayout()
        
        agent_label = QLabel("Agent Name:")
        agent_label.setFont(self.base_font)
        agent_layout.addWidget(agent_label)
        
        self.agent_name_edit = QLineEdit()
        self.agent_name_edit.setFont(self.base_font)
        agent_layout.addWidget(self.agent_name_edit)
        
        agent_group.setLayout(agent_layout)
        layout.addWidget(agent_group)
        
        # Automation options group
        auto_group = QGroupBox("Automation Options")
        auto_group.setFont(self.heading_font)
        auto_layout = QVBoxLayout()
        
        refresh_label = QLabel("Refresh Interval (seconds):")
        refresh_label.setFont(self.base_font)
        auto_layout.addWidget(refresh_label)
        
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setFont(self.base_font)
        self.refresh_spin.setRange(1, 100)
        auto_layout.addWidget(self.refresh_spin)
        
        self.auto_screenshot_check = QCheckBox("Auto Screenshot on Error")
        self.auto_screenshot_check.setFont(self.base_font)
        auto_layout.addWidget(self.auto_screenshot_check)
        
        retry_label = QLabel("Max Retries:")
        retry_label.setFont(self.base_font)
        auto_layout.addWidget(retry_label)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setFont(self.base_font)
        self.max_retries_spin.setRange(1, 10)
        auto_layout.addWidget(self.max_retries_spin)
        
        auto_group.setLayout(auto_layout)
        layout.addWidget(auto_group)
        
        # Cache group
        cache_group = QGroupBox("Cache")
        cache_group.setFont(self.heading_font)
        cache_layout = QVBoxLayout()
        
        cache_label = QLabel("Cache Directory:")
        cache_label.setFont(self.base_font)
        cache_layout.addWidget(cache_label)
        
        cache_path_layout = QHBoxLayout()
        self.cache_dir_edit = QLineEdit()
        self.cache_dir_edit.setFont(self.base_font)
        cache_path_layout.addWidget(self.cache_dir_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setFont(self.base_font)
        browse_btn.clicked.connect(self._browse_cache_dir)
        cache_path_layout.addWidget(browse_btn)
        
        cache_layout.addLayout(cache_path_layout)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        layout.addStretch()
        return widget
    
    def _create_accessibility_tab(self) -> QWidget:
        """Create accessibility settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Visual group
        visual_group = QGroupBox("Visual Accessibility")
        visual_group.setFont(self.heading_font)
        visual_layout = QVBoxLayout()
        
        self.high_contrast_check = QCheckBox("High Contrast Mode")
        self.high_contrast_check.setFont(self.base_font)
        visual_layout.addWidget(self.high_contrast_check)
        
        self.focus_indicators_check = QCheckBox("Enhanced Focus Indicators")
        self.focus_indicators_check.setFont(self.base_font)
        visual_layout.addWidget(self.focus_indicators_check)
        
        self.reduce_motion_check = QCheckBox("Reduce Motion")
        self.reduce_motion_check.setFont(self.base_font)
        visual_layout.addWidget(self.reduce_motion_check)
        
        visual_group.setLayout(visual_layout)
        layout.addWidget(visual_group)
        
        # Input group
        input_group = QGroupBox("Input Accessibility")
        input_group.setFont(self.heading_font)
        input_layout = QVBoxLayout()
        
        self.keyboard_nav_check = QCheckBox("Enhanced Keyboard Navigation")
        self.keyboard_nav_check.setFont(self.base_font)
        input_layout.addWidget(self.keyboard_nav_check)
        
        self.screen_reader_check = QCheckBox("Screen Reader Support")
        self.screen_reader_check.setFont(self.base_font)
        input_layout.addWidget(self.screen_reader_check)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # ── Developer Options ──────────────────────────────────────────────
        dev_group = QGroupBox("Developer Options")
        dev_group.setFont(self.heading_font)
        dev_layout = QVBoxLayout()

        self.dev_mode_check = QCheckBox("🛠  DEV MODE  —  enable multi-agent sheet names")
        self.dev_mode_check.setFont(self.base_font)
        self.dev_mode_check.setToolTip(
            "When ON, the Support Mode name field and the Chat Agent name field\n"
            "accept multiple agent / sheet names (one per line).\n\n"
            "Signatures and case notes always use your own Agent Name from config."
        )
        dev_layout.addWidget(self.dev_mode_check)

        dev_note = QLabel(
            "Signing / notes always use your own Agent Name from config."
        )
        dev_note.setFont(self.base_font)
        dev_note.setStyleSheet("color: #6f6f6f;")
        dev_layout.addWidget(dev_note)

        dev_group.setLayout(dev_layout)
        layout.addWidget(dev_group)

        # Debug group
        debug_group = QGroupBox("Debug & Logging")
        debug_group.setFont(self.heading_font)
        debug_layout = QVBoxLayout()
        
        self.debug_mode_check = QCheckBox("Debug Mode")
        self.debug_mode_check.setFont(self.base_font)
        debug_layout.addWidget(self.debug_mode_check)
        
        log_label = QLabel("Log Level:")
        log_label.setFont(self.base_font)
        debug_layout.addWidget(log_label)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.setFont(self.base_font)
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        debug_layout.addWidget(self.log_level_combo)
        
        debug_group.setLayout(debug_layout)
        layout.addWidget(debug_group)
        
        # Backup group
        backup_group = QGroupBox("Backups")
        backup_group.setFont(self.heading_font)
        backup_layout = QVBoxLayout()
        
        self.backup_enabled_check = QCheckBox("Enable Automatic Backups")
        self.backup_enabled_check.setFont(self.base_font)
        backup_layout.addWidget(self.backup_enabled_check)
        
        backup_count_label = QLabel("Keep Last N Backups:")
        backup_count_label.setFont(self.base_font)
        backup_layout.addWidget(backup_count_label)
        
        self.backup_count_spin = QSpinBox()
        self.backup_count_spin.setFont(self.base_font)
        self.backup_count_spin.setRange(1, 20)
        backup_layout.addWidget(self.backup_count_spin)
        
        # Backup buttons
        backup_btn_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("Create Backup Now")
        create_backup_btn.setFont(self.base_font)
        create_backup_btn.clicked.connect(self._create_backup)
        backup_btn_layout.addWidget(create_backup_btn)
        
        restore_backup_btn = QPushButton("Restore Backup...")
        restore_backup_btn.setFont(self.base_font)
        restore_backup_btn.clicked.connect(self._restore_backup)
        backup_btn_layout.addWidget(restore_backup_btn)
        
        backup_layout.addLayout(backup_btn_layout)
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Reset button
        reset_btn = QPushButton("Reset All Settings to Defaults")
        reset_btn.setFont(self.base_font)
        reset_btn.clicked.connect(self._reset_to_defaults)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        return widget
    
    def _create_about_tab(self) -> QWidget:
        """Create about tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("ART Q Master V2")
        title.setFont(self.heading_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Version info
        version_text = QTextEdit()
        version_text.setFont(self.base_font)
        version_text.setReadOnly(True)
        version_text.setMaximumHeight(200)
        version_text.setPlainText(
            "Version: 2.0.0\n"
            "Build Date: 2024\n\n"
            "Configuration System: Phase 7 Complete\n"
            "- Modern schema & validation\n"
            "- Configuration manager with callbacks\n"
            "- Automatic migration from legacy formats\n"
            "- Backup & restore functionality\n"
            "- Basic credential encryption\n"
        )
        layout.addWidget(version_text)
        
        # Credits
        credits = QLabel("Made with Bob")
        credits.setFont(self.base_font)
        credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits)
        
        layout.addStretch()
        return widget
    
    def _load_settings(self):
        """Load current settings into UI."""
        # Appearance
        theme = config_manager.get('ui_settings.theme', 'auto')
        theme_index = {'light': 0, 'dark': 1, 'auto': 2}.get(theme.lower(), 2)
        self.theme_combo.setCurrentIndex(theme_index)
        
        font_size = config_manager.get('ui_settings.font_size', 20)
        self.font_size_spin.setValue(font_size)
        
        animations = config_manager.get('ui_settings.animations_enabled', True)
        self.animations_check.setChecked(animations)
        
        compact = config_manager.get('ui_settings.compact_mode', False)
        self.compact_check.setChecked(compact)
        
        # Automation
        agent_name = config_manager.get('agent_name', '')
        self.agent_name_edit.setText(agent_name)
        
        refresh = config_manager.get('automation.refresh_interval', 300)
        self.refresh_spin.setValue(refresh)
        
        auto_screenshot = config_manager.get('automation.auto_screenshot', True)
        self.auto_screenshot_check.setChecked(auto_screenshot)
        
        max_retries = config_manager.get('automation.max_retries', 3)
        self.max_retries_spin.setValue(max_retries)
        
        cache_dir = config_manager.get('cache_directory', './cache')
        self.cache_dir_edit.setText(cache_dir)
        
        # Accessibility
        high_contrast = config_manager.get('accessibility.high_contrast', False)
        self.high_contrast_check.setChecked(high_contrast)
        
        focus_indicators = config_manager.get('accessibility.focus_indicators', True)
        self.focus_indicators_check.setChecked(focus_indicators)
        
        reduce_motion = config_manager.get('accessibility.reduced_motion', False)
        self.reduce_motion_check.setChecked(reduce_motion)
        
        keyboard_nav = config_manager.get('accessibility.keyboard_navigation', True)
        self.keyboard_nav_check.setChecked(keyboard_nav)
        
        screen_reader = config_manager.get('accessibility.screen_reader_support', False)
        self.screen_reader_check.setChecked(screen_reader)
        
        # Advanced — dev mode first so the bus is synced before any window reacts
        dev_mode = config_manager.get('advanced.dev_mode', False)
        self.dev_mode_check.setChecked(dev_mode)
        self.settings_bus.set_dev_mode(dev_mode)   # sync bus to stored state

        debug_mode = config_manager.get('advanced.debug_mode', False)
        self.debug_mode_check.setChecked(debug_mode)
        
        log_level = config_manager.get('advanced.log_level', 'INFO')
        log_index = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].index(log_level.upper())
        self.log_level_combo.setCurrentIndex(log_index)
        
        backup_enabled = config_manager.get('advanced.backup_enabled', True)
        self.backup_enabled_check.setChecked(backup_enabled)
        
        backup_count = config_manager.get('advanced.backup_count', 5)
        self.backup_count_spin.setValue(backup_count)
    
    def _save_and_close(self):
        """Save settings and close dialog."""
        # Appearance
        theme_map = {0: 'light', 1: 'dark', 2: 'auto'}
        theme = theme_map[self.theme_combo.currentIndex()]
        config_manager.set('ui_settings.theme', theme, save_immediately=False)
        config_manager.set('ui_settings.font_size', self.font_size_spin.value(), save_immediately=False)
        config_manager.set('ui_settings.animations_enabled', self.animations_check.isChecked(), save_immediately=False)
        config_manager.set('ui_settings.compact_mode', self.compact_check.isChecked(), save_immediately=False)
        
        # Automation
        config_manager.set('agent_name', self.agent_name_edit.text(), save_immediately=False)
        config_manager.set('automation.refresh_interval', self.refresh_spin.value(), save_immediately=False)
        config_manager.set('automation.auto_screenshot', self.auto_screenshot_check.isChecked(), save_immediately=False)
        config_manager.set('automation.max_retries', self.max_retries_spin.value(), save_immediately=False)
        config_manager.set('cache_directory', self.cache_dir_edit.text(), save_immediately=False)
        
        # Accessibility
        config_manager.set('accessibility.high_contrast', self.high_contrast_check.isChecked(), save_immediately=False)
        config_manager.set('accessibility.focus_indicators', self.focus_indicators_check.isChecked(), save_immediately=False)
        config_manager.set('accessibility.reduced_motion', self.reduce_motion_check.isChecked(), save_immediately=False)
        config_manager.set('accessibility.keyboard_navigation', self.keyboard_nav_check.isChecked(), save_immediately=False)
        config_manager.set('accessibility.screen_reader_support', self.screen_reader_check.isChecked(), save_immediately=False)
        
        # Advanced
        config_manager.set('advanced.dev_mode', self.dev_mode_check.isChecked(), save_immediately=False)
        config_manager.set('advanced.debug_mode', self.debug_mode_check.isChecked(), save_immediately=False)
        config_manager.set('advanced.log_level', self.log_level_combo.currentText(), save_immediately=False)
        config_manager.set('advanced.backup_enabled', self.backup_enabled_check.isChecked(), save_immediately=False)
        config_manager.set('advanced.backup_count', self.backup_count_spin.value(), save_immediately=False)
        
        # Save all changes
        if config_manager.save():
            # Broadcast new dev-mode state immediately to all open windows
            self.settings_bus.set_dev_mode(self.dev_mode_check.isChecked())
            self.settings_changed.emit()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings")
    
    def _browse_cache_dir(self):
        """Browse for cache directory."""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Cache Directory")
        if dir_path:
            self.cache_dir_edit.setText(dir_path)
    
    def _import_settings(self):
        """Import settings from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Settings", "", "JSON Files (*.json)"
        )
        if file_path:
            if config_manager.import_config(file_path):
                self._load_settings()
                QMessageBox.information(self, "Success", "Settings imported successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to import settings")
    
    def _export_settings(self):
        """Export settings to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Settings", "config_export.json", "JSON Files (*.json)"
        )
        if file_path:
            if config_manager.export_config(file_path):
                QMessageBox.information(self, "Success", "Settings exported successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to export settings")
    
    def _create_backup(self):
        """Create configuration backup."""
        backup = ConfigBackup()
        success, result = backup.create_backup(label="manual")
        if success:
            QMessageBox.information(self, "Success", f"Backup created:\n{result}")
        else:
            QMessageBox.warning(self, "Error", f"Backup failed:\n{result}")
    
    def _restore_backup(self):
        """Restore configuration from backup."""
        backup = ConfigBackup()
        backups = backup.list_backups()
        
        if not backups:
            QMessageBox.information(self, "No Backups", "No backups available")
            return
        
        # Show backup selection dialog (simplified)
        from PyQt5.QtWidgets import QInputDialog
        backup_names = [name for name, _, _ in backups]
        backup_name, ok = QInputDialog.getItem(
            self, "Restore Backup", "Select backup to restore:", backup_names, 0, False
        )
        
        if ok and backup_name:
            reply = QMessageBox.question(
                self, "Confirm Restore",
                f"Restore configuration from {backup_name}?\nCurrent config will be backed up first.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success, message = backup.restore_backup(backup_name)
                if success:
                    self._load_settings()
                    QMessageBox.information(self, "Success", message)
                else:
                    QMessageBox.warning(self, "Error", message)
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self, "Confirm Reset",
            "Reset all settings to defaults?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if config_manager.reset_to_defaults():
                self._load_settings()
                QMessageBox.information(self, "Success", "Settings reset to defaults")
            else:
                QMessageBox.warning(self, "Error", "Failed to reset settings")
    
    def _apply_theme(self):
        """Apply current theme to dialog."""
        # This would integrate with the theme system
        pass

# Made with Bob
