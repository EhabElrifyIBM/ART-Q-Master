import json
import os
import sys
from pathlib import Path
from datetime import datetime


class ConfigManager:
    """Manages configuration for the ART automation script"""
    
    def __init__(self, config_dir=None):
        """
        Initialize ConfigManager
        
        Args:
            config_dir: Directory to store config.json. If None, uses current working directory.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = Path.cwd()
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_path = self.config_dir / "config.json"
        self.config_data = None
    
    def config_exists(self):
        """Check if config file exists"""
        return self.config_path.exists()
    
    def load_config(self):
        """
        Load configuration from file
        
        Returns:
            dict: Configuration data
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid or missing required fields
        """
        if not self.config_exists():
            raise FileNotFoundError(f"Config file not found at {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        
        # Validate required fields
        self._validate_config(self.config_data)
        return self.config_data
    
    def _validate_config(self, config):
        """
        Validate that all required fields are present and valid
        
        Raises:
            ValueError: If any required field is missing or invalid
        """
        required_fields = {
            'agent_settings': ['agent_name', 'user_id', 'password', 'place_id'],
            'file_paths': ['excel_base_path', 'cache_directory'],
            'execution_settings': ['refresh_interval'],
            'crm_settings': ['excel_sheet_name']
        }
        
        for section, fields in required_fields.items():
            if section not in config:
                raise ValueError(f"Missing section: {section}")
            
            for field in fields:
                if field not in config[section]:
                    raise ValueError(f"Missing field: {section}.{field}")
                
                # Check for empty strings
                if isinstance(config[section][field], str):
                    if not config[section][field].strip():
                        raise ValueError(f"Empty value for: {section}.{field}")
        
        # Validate paths exist and are accessible
        excel_path = config['file_paths']['excel_base_path']
        cache_dir = config['file_paths']['cache_directory']
        
        if not Path(excel_path).exists():
            raise ValueError(f"Excel base path does not exist: {excel_path}")
        
        # Cache directory will be created if needed, but parent should exist
        cache_parent = Path(cache_dir).parent
        if not cache_parent.exists():
            raise ValueError(f"Cache directory parent path does not exist: {cache_parent}")
        
        # Validate refresh_interval is positive integer
        refresh = config['execution_settings']['refresh_interval']
        if not isinstance(refresh, int) or refresh <= 0:
            raise ValueError(f"refresh_interval must be positive integer, got: {refresh}")
    
    @staticmethod
    def _is_valid_time(time_str):
        """Check if time string is in HH:MM format"""
        try:
            if ':' not in str(time_str):
                return False
            parts = str(time_str).split(':')
            if len(parts) != 2:
                return False
            hour = int(parts[0])
            minute = int(parts[1])
            return 0 <= hour < 24 and 0 <= minute < 60
        except (ValueError, AttributeError):
            return False
    
    def save_config(self, config_data):
        """
        Save configuration to file
        
        Args:
            config_data: Configuration dictionary
            
        Raises:
            ValueError: If config data is invalid
        """
        self._validate_config(config_data)
        
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=4)
        
        self.config_data = config_data
        print(f"[INFO] Config saved to: {self.config_path}")
    
    def get_value(self, section, key):
        """
        Get a configuration value
        
        Args:
            section: Config section (e.g., 'agent_settings')
            key: Config key
            
        Returns:
            Configuration value
            
        Raises:
            KeyError: If section or key doesn't exist
            ValueError: If config not loaded
        """
        if self.config_data is None:
            raise ValueError("Config not loaded. Call load_config() first.")
        
        if section not in self.config_data:
            raise KeyError(f"Section not found: {section}")
        
        if key not in self.config_data[section]:
            raise KeyError(f"Key not found: {section}.{key}")
        
        return self.config_data[section][key]


def ConfigSetupDialog(config_manager):
    """
    Factory function that creates ConfigSetupDialog class with lazy PyQt5 imports.
    This avoids QApplication errors by only importing PyQt5 when dialog is actually created.
    """
    # Lazy import PyQt5 - only when dialog is actually needed
    from PyQt5.QtWidgets import (
        QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout,
        QGridLayout, QWidget, QMessageBox, QFileDialog, QTimeEdit, QSpinBox, QFrame
    )
    from PyQt5.QtCore import QTime, Qt
    from PyQt5.QtGui import QFont
    
    # Import V2 design system
    from ui.design_system import Colors, Spacing, BorderRadius
    from ui.services import get_v2_settings_bus, V2ThemeService
    from ui.typography_mixin import V2TypographyMixin
    
    class _ConfigSetupDialog(QDialog, V2TypographyMixin):
        """Modern configuration setup dialog with V2 design system"""
        
        def __init__(self, config_manager):
            QDialog.__init__(self)
            V2TypographyMixin.__init__(self)
            
            self.config_manager = config_manager
            self.config_result = None  # Renamed to avoid conflict with QDialog.result()
            
            # Initialize V2 systems
            self.settings_bus = get_v2_settings_bus()
            self.theme_service = V2ThemeService()
            
            # Load current config if it exists to show as placeholder
            self.current_config = None
            try:
                self.current_config = config_manager.load_config()
            except:
                pass  # Config doesn't exist yet
            
            self.init_ui()
            self._apply_theme()
            
            # Subscribe to theme changes
            self.settings_bus.theme_changed.connect(self._on_theme_changed)
            self.settings_bus.font_size_changed.connect(self._on_font_changed)
        
        def init_ui(self):
            """Initialize UI components with V2 design system"""
            self.setWindowTitle("ART Automation - Configuration Update")
            self.setMinimumSize(750, 800)
            
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
            main_layout.setSpacing(Spacing.LG)
            
            # Title
            title = QLabel("Update ART Automation Configuration")
            title.setObjectName("dialogTitle")
            title.setFont(self.get_font('h1', QFont.Bold))
            main_layout.addWidget(title)
            
            # Info message
            info = QLabel("Leave fields empty to keep previous values (shown in grey)")
            info.setObjectName("infoText")
            info.setFont(self.get_font('body'))
            info.setWordWrap(True)
            main_layout.addWidget(info)
            
            # Scroll area for form
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            scroll_layout.setSpacing(Spacing.LG)
            
            # AGENT SETTINGS SECTION
            scroll_layout.addWidget(self._create_section_header("Agent Settings"))
            
            agent_grid = QGridLayout()
            agent_grid.setSpacing(Spacing.MD)
            agent_grid.setColumnStretch(1, 1)
            
            agent_grid.addWidget(self._create_label("Agent Name:"), 0, 0)
            self.agent_name_input = self._create_input(self._get_placeholder('agent_settings', 'agent_name'))
            agent_grid.addWidget(self.agent_name_input, 0, 1)
            
            agent_grid.addWidget(self._create_label("User ID (Dialer Username):"), 1, 0)
            self.user_id_input = self._create_input(self._get_placeholder('agent_settings', 'user_id'))
            agent_grid.addWidget(self.user_id_input, 1, 1)
            
            agent_grid.addWidget(self._create_label("Password (Dialer Password):"), 2, 0)
            self.password_input = self._create_input(self._get_placeholder('agent_settings', 'password', hide=True))
            self.password_input.setEchoMode(QLineEdit.Password)
            agent_grid.addWidget(self.password_input, 2, 1)
            
            agent_grid.addWidget(self._create_label("Place ID (Dialer Place ID):"), 3, 0)
            self.place_id_input = self._create_input(self._get_placeholder('agent_settings', 'place_id'))
            agent_grid.addWidget(self.place_id_input, 3, 1)
            
            scroll_layout.addLayout(agent_grid)
            
            # FILE PATHS SECTION
            scroll_layout.addWidget(self._create_section_header("File Paths"))
            
            paths_grid = QGridLayout()
            paths_grid.setSpacing(Spacing.MD)
            paths_grid.setColumnStretch(1, 1)
            
            paths_grid.addWidget(self._create_label("Excel Base Path:"), 0, 0)
            excel_layout = QVBoxLayout()
            excel_layout.setSpacing(Spacing.SM)
            self.excel_path_input = self._create_input(self._get_placeholder('file_paths', 'excel_base_path'))
            excel_button = self._create_browse_button("Browse...")
            excel_button.clicked.connect(self.browse_excel_path)
            excel_layout.addWidget(self.excel_path_input)
            excel_layout.addWidget(excel_button)
            paths_grid.addLayout(excel_layout, 0, 1)
            
            paths_grid.addWidget(self._create_label("Cache Directory:"), 1, 0)
            cache_layout = QVBoxLayout()
            cache_layout.setSpacing(Spacing.SM)
            self.cache_path_input = self._create_input(self._get_placeholder('file_paths', 'cache_directory'))
            cache_button = self._create_browse_button("Browse...")
            cache_button.clicked.connect(self.browse_cache_path)
            cache_layout.addWidget(self.cache_path_input)
            cache_layout.addWidget(cache_button)
            paths_grid.addLayout(cache_layout, 1, 1)
            
            scroll_layout.addLayout(paths_grid)
            
            # CRM SETTINGS SECTION
            scroll_layout.addWidget(self._create_section_header("CRM Settings"))
            
            crm_grid = QGridLayout()
            crm_grid.setSpacing(Spacing.MD)
            crm_grid.setColumnStretch(1, 1)
            
            crm_grid.addWidget(self._create_label("Excel Sheet Name:"), 0, 0)
            self.sheet_name_input = self._create_input(self._get_placeholder('crm_settings', 'excel_sheet_name'))
            crm_grid.addWidget(self.sheet_name_input, 0, 1)
            
            scroll_layout.addLayout(crm_grid)
            
            # EXECUTION SETTINGS SECTION
            scroll_layout.addWidget(self._create_section_header("Execution Settings"))
            
            exec_grid = QGridLayout()
            exec_grid.setSpacing(Spacing.MD)
            exec_grid.setColumnStretch(1, 1)
            
            exec_grid.addWidget(self._create_label("Refresh Interval (cases):"), 0, 0)
            self.refresh_interval_input = QSpinBox()
            self.refresh_interval_input.setObjectName("spinBox")
            self.refresh_interval_input.setFont(self.get_font('body'))
            interval = self._get_placeholder('execution_settings', 'refresh_interval')
            if interval:
                try:
                    self.refresh_interval_input.setValue(int(interval))
                except:
                    self.refresh_interval_input.setValue(10)
            else:
                self.refresh_interval_input.setValue(10)
            self.refresh_interval_input.setMinimum(1)
            self.refresh_interval_input.setMaximum(100)
            exec_grid.addWidget(self.refresh_interval_input, 0, 1)
            
            scroll_layout.addLayout(exec_grid)
            
            main_layout.addWidget(scroll_widget)
            
            # BUTTONS
            button_layout = QVBoxLayout()
            button_layout.setSpacing(Spacing.MD)
            
            self.save_button = self._create_primary_button("Save Configuration")
            self.save_button.clicked.connect(self.save_configuration)
            button_layout.addWidget(self.save_button)
            
            self.cancel_button = self._create_secondary_button("Cancel")
            self.cancel_button.clicked.connect(self.reject)
            button_layout.addWidget(self.cancel_button)
            
            main_layout.addLayout(button_layout)
            self.setLayout(main_layout)
        
        def _create_section_header(self, title):
            """Create a section header with V2 styling"""
            header = QLabel(title.upper())
            header.setObjectName("sectionHeader")
            header.setFont(self.get_font('h3', QFont.Bold))
            return header
        
        def _create_label(self, text):
            """Create a form label with V2 styling"""
            label = QLabel(text)
            label.setObjectName("formLabel")
            label.setFont(self.get_font('body'))
            return label
        
        def _create_input(self, placeholder):
            """Create an input field with V2 styling"""
            input_field = QLineEdit()
            input_field.setObjectName("formInput")
            input_field.setFont(self.get_font('body'))
            input_field.setPlaceholderText(placeholder)
            input_field.setMinimumHeight(44)
            return input_field
        
        def _create_browse_button(self, text):
            """Create a browse button with V2 styling"""
            button = QPushButton(text)
            button.setObjectName("browseButton")
            button.setFont(self.get_font('button'))
            button.setMinimumHeight(44)
            return button
        
        def _create_primary_button(self, text):
            """Create a primary button with V2 styling"""
            button = QPushButton(text)
            button.setObjectName("primaryButton")
            button.setFont(self.get_font('button', QFont.Bold))
            button.setMinimumHeight(48)
            return button
        
        def _create_secondary_button(self, text):
            """Create a secondary button with V2 styling"""
            button = QPushButton(text)
            button.setObjectName("secondaryButton")
            button.setFont(self.get_font('button'))
            button.setMinimumHeight(48)
            return button
        
        def _apply_theme(self, theme=None):
            """Apply theme-aware styling"""
            theme_mode = theme or self.settings_bus.theme
            colors = self.theme_service.colors_for(theme_mode)
            
            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {colors['window_bg']};
                }}
                
                QLabel#dialogTitle {{
                    color: {colors['accent']};
                }}
                
                QLabel#infoText {{
                    color: {colors['text_secondary']};
                    font-style: italic;
                }}
                
                QLabel#sectionHeader {{
                    color: {colors['text_primary']};
                    border-bottom: 2px solid {colors['accent']};
                    padding-bottom: {Spacing.SM}px;
                    margin-top: {Spacing.MD}px;
                }}
                
                QLabel#formLabel {{
                    color: {colors['text_primary']};
                }}
                
                QLineEdit#formInput {{
                    background-color: {colors['surface']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['surface_border']};
                    border-radius: {BorderRadius.SM}px;
                    padding: {Spacing.SM}px {Spacing.MD}px;
                }}
                
                QLineEdit#formInput:focus {{
                    border: 2px solid {colors['accent']};
                }}
                
                QSpinBox#spinBox {{
                    background-color: {colors['surface']};
                    color: {colors['text_primary']};
                    border: 1px solid {colors['surface_border']};
                    border-radius: {BorderRadius.SM}px;
                    padding: {Spacing.SM}px {Spacing.MD}px;
                }}
                
                QPushButton#browseButton {{
                    background-color: {colors['surface']};
                    color: {colors['accent']};
                    border: 1px solid {colors['accent']};
                    border-radius: {BorderRadius.SM}px;
                    padding: {Spacing.SM}px {Spacing.LG}px;
                }}
                
                QPushButton#browseButton:hover {{
                    background-color: {colors['accent_soft']};
                }}
                
                QPushButton#primaryButton {{
                    background-color: {colors['accent']};
                    color: #ffffff;
                    border: none;
                    border-radius: {BorderRadius.MD}px;
                    padding: {Spacing.MD}px {Spacing.XL}px;
                    font-weight: 600;
                }}
                
                QPushButton#primaryButton:hover {{
                    background-color: {colors['accent_hover']};
                }}
                
                QPushButton#primaryButton:pressed {{
                    background-color: {colors['accent_pressed']};
                }}
                
                QPushButton#secondaryButton {{
                    background-color: transparent;
                    color: {colors['text_primary']};
                    border: 2px solid {colors['surface_border']};
                    border-radius: {BorderRadius.MD}px;
                    padding: {Spacing.MD}px {Spacing.XL}px;
                }}
                
                QPushButton#secondaryButton:hover {{
                    background-color: {colors['surface_alt']};
                    border-color: {colors['accent']};
                }}
            """)
        
        def _on_theme_changed(self, theme: str):
            """Handle theme changes"""
            self._apply_theme(theme)
        
        def _on_font_changed(self, font_size: int):
            """Handle font size changes"""
            self.apply_typography()  # Refresh typography with new font size
            self._apply_theme()  # Reapply theme to refresh font-dependent styles
        
        def _get_placeholder(self, section, key, hide=False):
            """Get placeholder text from current config"""
            if not self.current_config:
                return ""
            
            try:
                value = self.current_config[section][key]
                if hide and isinstance(value, str):
                    return "••• (unchanged)"
                return str(value) if value else ""
            except:
                return ""
        
        def browse_excel_path(self):
            """Browse for Excel base path"""
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Excel Base Directory",
                str(Path.home())
            )
            if path:
                self.excel_path_input.setText(path)
        
        def browse_cache_path(self):
            """Browse for cache directory"""
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Cache Directory",
                str(Path.home())
            )
            if path:
                self.cache_path_input.setText(path)
        
        def save_configuration(self):
            """Validate and save configuration - allows empty fields to keep previous values"""
            # Get values, use placeholders if empty
            agent_name = self.agent_name_input.text().strip() or self._get_placeholder('agent_settings', 'agent_name')
            user_id = self.user_id_input.text().strip() or self._get_placeholder('agent_settings', 'user_id')
            password = self.password_input.text().strip() or self._get_placeholder('agent_settings', 'password')
            place_id = self.place_id_input.text().strip() or self._get_placeholder('agent_settings', 'place_id')
            excel_path = self.excel_path_input.text().strip() or self._get_placeholder('file_paths', 'excel_base_path')
            cache_path = self.cache_path_input.text().strip() or self._get_placeholder('file_paths', 'cache_directory')
            sheet_name = self.sheet_name_input.text().strip() or self._get_placeholder('crm_settings', 'excel_sheet_name')
            
            # Validate all fields have values (either entered or from placeholder)
            if not agent_name:
                QMessageBox.warning(self, "Validation Error", "Agent Name cannot be empty")
                return
            
            if not user_id:
                QMessageBox.warning(self, "Validation Error", "User ID cannot be empty")
                return
            
            if not password or password == "••• (unchanged)":
                QMessageBox.warning(self, "Validation Error", "Password cannot be empty")
                return
            
            if not place_id:
                QMessageBox.warning(self, "Validation Error", "Place ID cannot be empty")
                return
            
            if not excel_path:
                QMessageBox.warning(self, "Validation Error", "Excel Base Path must be provided")
                return
            
            if not cache_path:
                QMessageBox.warning(self, "Validation Error", "Cache Directory must be provided")
                return
            
            if not sheet_name:
                QMessageBox.warning(self, "Validation Error", "Excel Sheet Name cannot be empty")
                return
            
            # Validate paths exist
            if not Path(excel_path).exists():
                QMessageBox.warning(self, "Validation Error", f"Excel path does not exist: {excel_path}")
                return
            
            cache_parent = Path(cache_path).parent
            if not cache_parent.exists():
                QMessageBox.warning(self, "Validation Error", f"Cache path parent does not exist: {cache_parent}")
                return
            
            # Create cache directory if needed
            Path(cache_path).mkdir(parents=True, exist_ok=True)
            
            # Build config data
            config_data = {
                "agent_settings": {
                    "agent_name": agent_name,
                    "user_id": user_id,
                    "password": password,
                    "place_id": place_id
                },
                "file_paths": {
                    "excel_base_path": excel_path,
                    "cache_directory": cache_path
                },
                "crm_settings": {
                    "excel_sheet_name": sheet_name
                },
                "execution_settings": {
                    "refresh_interval": self.refresh_interval_input.value()
                }
            }
            
            try:
                self.config_manager.save_config(config_data)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Configuration saved successfully to:\n{self.config_manager.config_path}"
                )
                self.config_result = config_data
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{str(e)}")
    
    # Return instance of the dialog
    return _ConfigSetupDialog(config_manager)


def init_config():
    """
    Initialize configuration. If config doesn't exist, show setup dialog.
    Returns config_manager with loaded config.
    
    Returns:
        ConfigManager: Initialized and loaded config manager
        
    Raises:
        SystemExit: If setup is cancelled or config cannot be loaded
    """
    # Determine config directory - use src_v2 directory
    script_dir = Path(__file__).parent.parent  # Go up from 'ART Q Control' to 'src_v2'
    config_manager = ConfigManager(config_dir=script_dir)
    
    # If config doesn't exist, show setup dialog
    if not config_manager.config_exists():
        print("[INFO] Config file not found. Starting first-time setup...")
        
        # Lazy import PyQt5 ONLY when dialog is needed
        from PyQt5.QtWidgets import QApplication, QDialog
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        dialog = ConfigSetupDialog(config_manager)
        
        if dialog.exec_() != QDialog.Accepted:
            print("[ERROR] Configuration setup cancelled. Exiting application.")
            sys.exit(1)
    
    # Load and validate config
    try:
        config_manager.load_config()
        print("[INFO] Configuration loaded successfully")
        
        # Now that we have config, move config file to cache directory for future use
        if config_manager.config_data:
            cache_dir = Path(config_manager.config_data['file_paths']['cache_directory'])
            cache_dir.mkdir(parents=True, exist_ok=True)
            cache_config_path = cache_dir / "config.json"
            
            # If config is not already in cache directory, move it
            if config_manager.config_path != cache_config_path:
                try:
                    import shutil
                    shutil.copy2(config_manager.config_path, cache_config_path)
                    # Update manager to use cache directory location
                    config_manager.config_path = cache_config_path
                    config_manager.config_dir = cache_dir
                    print(f"[INFO] Config moved to cache directory: {cache_config_path}")
                except Exception as e:
                    print(f"[WARN] Could not move config to cache directory: {e}")
        
        return config_manager
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"[ERROR] Failed to load configuration: {e}")
        print("[ERROR] Application cannot proceed without valid configuration. Exiting.")
        sys.exit(1)

# Made with Bob
