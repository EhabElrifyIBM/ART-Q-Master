# ============================================================================
# theme_manager.py - Theme Management System for Dark/Light Mode
# ============================================================================
# Phase 3.2: Dark Mode & Accessibility
#
# Provides centralized theme management with dark/light mode switching,
# system preference detection, and accessibility features.
#
# NOTE: This is the legacy theme manager. New code should use ui.theme.py
# which has a cleaner architecture. This file is kept for backward compatibility
# with existing code (CaseReviewer_v2, CompaniesProcess_v2, settings_dialog).
# ============================================================================

import json
import os
from enum import Enum
from typing import Optional, Callable, List
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication, QWidget

# Import colors from centralized design system
from ui.design_system import Colors


class ThemeMode(Enum):
    """Theme mode enumeration."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system preference


def _map_colors_to_legacy_names(colors: dict) -> dict:
    """
    Map design system color names to legacy theme_manager names.
    
    Args:
        colors: Color dictionary from design_system.py
    
    Returns:
        dict: Colors with legacy naming convention
    """
    return {
        # Primary colors
        'primary': colors['primary'],
        'primary_hover': colors['primary_hover'],
        'primary_active': colors['primary_active'],
        'primary_inverse': colors['primary_inverse'],
        
        # UI colors (map new names to old names AND provide direct access)
        'ui_background': colors['background'],
        'background': colors['background'],  # Direct access
        'ui_surface': colors['surface'],
        'surface': colors['surface'],  # Direct access
        'ui_surface_hover': colors['surface_hover'],
        'surface_hover': colors['surface_hover'],  # Direct access
        'ui_surface_active': colors['surface_active'],
        'surface_active': colors['surface_active'],  # Direct access
        
        # Text colors
        'text_primary': colors['text_primary'],
        'text_secondary': colors['text_secondary'],
        'text_tertiary': colors['text_tertiary'],
        'text_disabled': colors['text_disabled'],
        'text_inverse': colors['text_inverse'],
        
        # Semantic colors
        'success': colors['success'],
        'warning': colors['warning'],
        'danger': colors['danger'],
        'info': colors['info'],
        
        # Border/divider
        'border': colors['border'],
        'divider': colors['divider'],
        
        # Interactive
        'link': colors['link'],
        'link_visited': colors['link_visited'],
        'focus_outline': colors['focus'],
        
        # Loading spinner (use primary colors)
        'spinner': colors['primary'],
        'spinner_bg': colors['surface_hover'],
    }


class ColorScheme:
    """
    Color scheme definitions for each theme.
    
    NOTE: Colors are now imported from ui.design_system.py to avoid duplication.
    This class provides backward compatibility by mapping the old color names
    to the new design system tokens.
    """
    
    # Light Theme - imported from design_system.py
    LIGHT = _map_colors_to_legacy_names(Colors.LIGHT)
    
    # Dark Theme - imported from design_system.py
    DARK = _map_colors_to_legacy_names(Colors.DARK)


class ThemeManager(QObject):
    """
    Centralized theme management system.
    
    Features:
    - Theme switching (light/dark/auto)
    - System preference detection
    - Dynamic stylesheet generation
    - Configuration persistence
    - Signal emission for theme changes
    
    Usage:
        manager = ThemeManager()
        manager.theme_changed.connect(on_theme_changed)
        manager.set_theme(ThemeMode.DARK)
        stylesheet = manager.get_stylesheet()
    """
    
    # Signals
    theme_changed = pyqtSignal(ThemeMode)
    colors_changed = pyqtSignal(dict)
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize theme manager.
        
        Args:
            config_dir (str): Directory for theme configuration. Default: project root
        """
        super().__init__()
        
        self.config_dir = config_dir or self._get_config_directory()
        self.config_file = os.path.join(self.config_dir, 'config.json')
        
        self.current_theme = ThemeMode.LIGHT
        self.current_colors = ColorScheme.LIGHT.copy()
        
        # Load theme from config.json
        self._load_theme_from_config()
        
        # Detect system preference
        self._detect_system_preference()
    
    def _get_config_directory(self) -> str:
        """Get configuration directory."""
        current = os.path.dirname(os.path.abspath(__file__))
        
        # Navigate up to project root
        while current != os.path.dirname(current):
            if os.path.exists(os.path.join(current, 'config.json')):
                return current
            current = os.path.dirname(current)
        
        # Fallback
        return os.path.expanduser('~/.art_q_master')
    
    def _load_theme_from_config(self):
        """Load theme mode from config.json."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    theme_str = config.get('theme_mode', 'light')
                    self.current_theme = ThemeMode(theme_str)
                    print(f"[INFO] Theme loaded from config.json: {theme_str}")
            except Exception as e:
                print(f"[WARN] Failed to load theme from config.json: {e}")
                self.current_theme = ThemeMode.LIGHT
        else:
            self.current_theme = ThemeMode.LIGHT
        
        self._apply_theme()
    
    def _save_theme_to_config(self):
        """Save theme mode to config.json."""
        try:
            # Read existing config
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Update theme_mode
            config['theme_mode'] = self.current_theme.value
            
            # Write back to config.json
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"[INFO] Theme saved to config.json: {self.current_theme.value}")
        except Exception as e:
            print(f"[WARN] Failed to save theme to config.json: {e}")
    
    def _detect_system_preference(self) -> ThemeMode:
        """
        Detect system dark mode preference.
        
        Returns:
            ThemeMode: System preferred theme
        """
        try:
            import winreg
            
            # Check Windows Registry for dark mode setting
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            
            # value == 1: Light theme, value == 0: Dark theme
            return ThemeMode.DARK if value == 0 else ThemeMode.LIGHT
        except:
            # Default to light if detection fails
            return ThemeMode.LIGHT
    
    def set_theme(self, theme: ThemeMode):
        """
        Set application theme.
        
        Args:
            theme (ThemeMode): Theme to apply
        """
        if theme == ThemeMode.AUTO:
            self.current_theme = self._detect_system_preference()
        else:
            self.current_theme = theme
        
        self._apply_theme()
        self._save_theme_to_config()
        self.theme_changed.emit(self.current_theme)
    
    def _apply_theme(self):
        """Apply theme colors."""
        if self.current_theme == ThemeMode.DARK:
            self.current_colors = ColorScheme.DARK.copy()
        elif self.current_theme == ThemeMode.AUTO:
            system_pref = self._detect_system_preference()
            colors = ColorScheme.DARK if system_pref == ThemeMode.DARK else ColorScheme.LIGHT
            self.current_colors = colors.copy()
        else:
            self.current_colors = ColorScheme.LIGHT.copy()
        
        self.colors_changed.emit(self.current_colors)
    
    def get_color(self, color_name: str) -> str:
        """
        Get color for current theme.
        
        Args:
            color_name (str): Color name (e.g., 'primary', 'text_primary')
        
        Returns:
            str: Hex color code
        """
        return self.current_colors.get(color_name, '#000000')
    
    def get_stylesheet(self, include_scrollbar: bool = True) -> str:
        """
        Generate complete application stylesheet.
        
        Args:
            include_scrollbar (bool): Include scrollbar styling
        
        Returns:
            str: Complete QSS stylesheet
        """
        colors = self.current_colors
        
        stylesheet = f"""
        /* Main Application Stylesheet */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['ui_background']};
            color: {colors['text_primary']};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {colors['ui_surface_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {colors['ui_surface_active']};
        }}
        
        QPushButton:disabled {{
            color: {colors['text_disabled']};
            background-color: {colors['ui_surface']};
        }}
        
        /* Primary Button Style */
        QPushButton#primaryButton {{
            background-color: {colors['primary']};
            color: {colors['text_inverse']};
            border: none;
        }}
        
        QPushButton#primaryButton:hover {{
            background-color: {colors['primary_hover']};
        }}
        
        QPushButton#primaryButton:pressed {{
            background-color: {colors['primary_active']};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 8px;
            selection-background-color: {colors['primary']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {colors['focus_outline']};
        }}
        
        QLineEdit:disabled {{
            background-color: {colors['ui_background']};
            color: {colors['text_disabled']};
            border: 1px solid {colors['border']};
        }}
        
        /* Labels */
        QLabel {{
            color: {colors['text_primary']};
        }}
        
        /* Dialogs */
        QDialog {{
            background-color: {colors['ui_background']};
        }}
        
        /* Group Boxes */
        QGroupBox {{
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
        }}
        
        /* Progress Bar */
        QProgressBar {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {colors['primary']};
            border-radius: 3px;
        }}
        
        /* Check Boxes */
        QCheckBox {{
            color: {colors['text_primary']};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {colors['border']};
            border-radius: 3px;
            background-color: {colors['ui_surface']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors['primary']};
            border: 1px solid {colors['primary']};
        }}
        
        /* Radio Buttons */
        QRadioButton {{
            color: {colors['text_primary']};
            spacing: 8px;
        }}
        
        QRadioButton::indicator {{
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 1px solid {colors['border']};
            background-color: {colors['ui_surface']};
        }}
        
        QRadioButton::indicator:checked {{
            background-color: {colors['primary']};
            border: 1px solid {colors['primary']};
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            border-radius: 4px;
            padding: 6px;
        }}
        
        QComboBox::drop-down {{
            border: none;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            selection-background-color: {colors['primary']};
            border: 1px solid {colors['border']};
        }}
        
        /* Tables */
        QTableWidget, QTableView {{
            background-color: {colors['ui_background']};
            alternate-background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            gridline-color: {colors['border']};
            border: 1px solid {colors['border']};
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: 4px;
            border: none;
        }}
        
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {colors['primary']};
            color: {colors['text_inverse']};
        }}
        
        QHeaderView::section {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            padding: 4px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {colors['border']};
        }}
        
        QTabBar::tab {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
            padding: 8px 20px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {colors['ui_background']};
            border-bottom: 2px solid {colors['primary']};
        }}
        
        QTabBar::tab:hover {{
            background-color: {colors['ui_surface_hover']};
        }}
        
        /* Menus */
        QMenuBar {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border-bottom: 1px solid {colors['border']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {colors['ui_surface_hover']};
        }}
        
        QMenu {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border: 1px solid {colors['border']};
        }}
        
        QMenu::item:selected {{
            background-color: {colors['primary']};
            color: {colors['text_inverse']};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {colors['ui_surface']};
            color: {colors['text_primary']};
            border-top: 1px solid {colors['border']};
        }}
        """
        
        if include_scrollbar:
            stylesheet += f"""
        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {colors['ui_background']};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {colors['ui_surface_hover']};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {colors['ui_surface_active']};
        }}
        
        QScrollBar:horizontal {{
            background-color: {colors['ui_background']};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {colors['ui_surface_hover']};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {colors['ui_surface_active']};
        }}
        
        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}
            """
        
        return stylesheet
    
    def get_high_contrast_stylesheet(self) -> str:
        """
        Generate high contrast stylesheet for accessibility.
        
        Returns:
            str: High contrast QSS stylesheet
        """
        colors = self.current_colors
        
        stylesheet = f"""
        /* High Contrast Stylesheet */
        QMainWindow, QDialog, QWidget {{
            background-color: {colors['ui_background']};
            color: {colors['text_primary']};
        }}
        
        /* Enhanced button contrast */
        QPushButton {{
            background-color: {colors['primary']};
            color: {colors['text_inverse']};
            border: 2px solid {colors['primary_active']};
            border-radius: 4px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 12px;
        }}
        
        QPushButton:hover {{
            background-color: {colors['primary_hover']};
            border: 2px solid {colors['primary_active']};
        }}
        
        QPushButton:focus {{
            outline: 3px solid {colors['focus_outline']};
        }}
        
        /* Enhanced focus indicators */
        QLineEdit:focus, QTextEdit:focus {{
            border: 3px solid {colors['focus_outline']};
            outline: 3px solid {colors['focus_outline']};
        }}
        
        /* Enhanced check boxes */
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {colors['text_primary']};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {colors['primary']};
            border: 2px solid {colors['primary']};
        }}
        """
        
        return stylesheet
    
    def get_current_theme(self) -> ThemeMode:
        """Get current theme mode."""
        return self.current_theme
    
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        if self.current_theme == ThemeMode.LIGHT:
            self.set_theme(ThemeMode.DARK)
        else:
            self.set_theme(ThemeMode.LIGHT)


# Singleton instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get or create theme manager singleton."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
    
    app = QApplication(sys.argv)
    
    # Initialize theme manager
    theme_mgr = get_theme_manager()
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Theme Manager Demo")
    window.resize(400, 300)
    
    # Create central widget with layout
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    
    # Create toggle button
    btn_toggle = QPushButton("Toggle Theme (Light <-> Dark)")
    btn_toggle.setObjectName("primaryButton")
    
    def on_toggle():
        theme_mgr.toggle_theme()
        app.setStyleSheet(theme_mgr.get_stylesheet())
        print(f"Theme switched to: {theme_mgr.get_current_theme().value}")
    
    btn_toggle.clicked.connect(on_toggle)
    layout.addWidget(btn_toggle)
    
    # Apply initial stylesheet
    app.setStyleSheet(theme_mgr.get_stylesheet())
    
    # Connect theme changes to window update
    def on_theme_changed(theme: ThemeMode):
        app.setStyleSheet(theme_mgr.get_stylesheet())
    
    theme_mgr.theme_changed.connect(on_theme_changed)
    
    window.setCentralWidget(central_widget)
    window.show()
    
    sys.exit(app.exec_())
