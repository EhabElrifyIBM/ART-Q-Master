"""
Theme System - Simplified Theme Management
===========================================

This module provides a modern, simplified theme management system that uses
the design_system.py tokens and integrates with V2SettingsBus.

Features:
- Light/Dark/Auto theme modes
- Uses design_system.py for color tokens
- Generates QSS stylesheets from design tokens
- Integrates with V2SettingsBus for reactive updates
- Simpler than the legacy theme_manager.py

Usage:
    from ui.theme import Theme, ThemeMode
    from ui.services import get_v2_settings_bus
    
    # Create theme instance
    theme = Theme()
    
    # Get current colors
    colors = theme.get_colors()
    primary = colors['primary']
    
    # Generate stylesheet
    stylesheet = theme.generate_stylesheet()
    widget.setStyleSheet(stylesheet)
    
    # Listen for theme changes
    bus = get_v2_settings_bus()
    bus.theme_changed.connect(lambda mode: theme.set_mode(mode))
"""

import sys
from enum import Enum
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from ui.design_system import Colors, Spacing, BorderRadius, Shadows, Typography


class ThemeMode(Enum):
    """
    Theme mode enumeration.
    
    Attributes:
        LIGHT: Light theme (bright backgrounds, dark text)
        DARK: Dark theme (dark backgrounds, light text)
        AUTO: Automatic theme based on system preference
    """
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    
    @classmethod
    def from_string(cls, value: str) -> 'ThemeMode':
        """
        Convert string to ThemeMode enum.
        
        Args:
            value: String value ('light', 'dark', 'auto')
        
        Returns:
            ThemeMode: Corresponding enum value, defaults to LIGHT if invalid
        """
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            return cls.LIGHT


class Theme(QObject):
    """
    Simplified theme manager using design system tokens.
    
    Manages theme switching and stylesheet generation using the centralized
    design tokens from design_system.py. Integrates with V2SettingsBus for
    reactive theme updates across the application.
    
    Signals:
        theme_changed: Emitted when theme mode changes (str: new mode)
        colors_changed: Emitted when colors change (Dict[str, str]: new colors)
    
    Attributes:
        mode: Current theme mode (ThemeMode)
        colors: Current color palette (Dict[str, str])
    """
    
    # Signals
    theme_changed = pyqtSignal(str)  # Emits mode name
    colors_changed = pyqtSignal(dict)  # Emits color dictionary
    
    def __init__(self, mode: ThemeMode = ThemeMode.LIGHT):
        """
        Initialize theme manager.
        
        Args:
            mode: Initial theme mode (default: LIGHT)
        """
        super().__init__()
        self._mode = mode
        self._colors = self._resolve_colors(mode)
    
    @property
    def mode(self) -> ThemeMode:
        """Get current theme mode."""
        return self._mode
    
    @property
    def colors(self) -> Dict[str, str]:
        """Get current color palette."""
        return self._colors.copy()
    
    def set_mode(self, mode: ThemeMode) -> None:
        """
        Set theme mode and update colors.
        
        Args:
            mode: New theme mode to apply
        """
        if isinstance(mode, str):
            mode = ThemeMode.from_string(mode)
        
        if mode == self._mode:
            return
        
        self._mode = mode
        self._colors = self._resolve_colors(mode)
        
        # Emit signals
        self.theme_changed.emit(mode.value)
        self.colors_changed.emit(self._colors)
    
    def set_mode_from_string(self, mode_str: str) -> None:
        """
        Set theme mode from string value.
        
        Args:
            mode_str: Mode string ('light', 'dark', 'auto')
        """
        mode = ThemeMode.from_string(mode_str)
        self.set_mode(mode)
    
    def get_colors(self) -> Dict[str, str]:
        """
        Get current color palette.
        
        Returns:
            Dict[str, str]: Dictionary of color tokens and hex values
        """
        return self._colors.copy()
    
    def get_color(self, color_name: str, fallback: str = "#000000") -> str:
        """
        Get a specific color from the current palette.
        
        Args:
            color_name: Name of the color token (e.g., 'primary', 'text_primary')
            fallback: Fallback color if token not found (default: black)
        
        Returns:
            str: Hex color code
        """
        return self._colors.get(color_name, fallback)
    
    def _resolve_colors(self, mode: ThemeMode) -> Dict[str, str]:
        """
        Resolve colors for the given theme mode.
        
        For AUTO mode, detects system preference. Falls back to LIGHT if detection fails.
        
        Args:
            mode: Theme mode to resolve
        
        Returns:
            Dict[str, str]: Color palette for the resolved mode
        """
        if mode == ThemeMode.AUTO:
            # Detect system theme preference
            resolved_mode = self._detect_system_theme()
        else:
            resolved_mode = mode
        
        # Return appropriate color palette
        if resolved_mode == ThemeMode.DARK:
            return Colors.DARK.copy()
        else:
            return Colors.LIGHT.copy()
    
    def _detect_system_theme(self) -> ThemeMode:
        """
        Detect system theme preference.
        
        Attempts to detect dark mode from system settings. Falls back to LIGHT
        if detection is not possible.
        
        Returns:
            ThemeMode: DARK if system is in dark mode, LIGHT otherwise
        """
        try:
            # Try to detect Windows dark mode
            if sys.platform == 'win32':
                import winreg
                try:
                    registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                    key = winreg.OpenKey(
                        registry,
                        r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
                    )
                    value, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
                    winreg.CloseKey(key)
                    # Value is 0 for dark mode, 1 for light mode
                    return ThemeMode.DARK if value == 0 else ThemeMode.LIGHT
                except (OSError, FileNotFoundError):
                    pass
            
            # Try to detect from Qt palette (cross-platform)
            app = QApplication.instance()
            if app:
                palette = app.palette()
                # Check if window background is dark
                bg_color = palette.color(palette.Window)
                # Consider dark if luminance < 128
                luminance = (0.299 * bg_color.red() + 
                           0.587 * bg_color.green() + 
                           0.114 * bg_color.blue())
                return ThemeMode.DARK if luminance < 128 else ThemeMode.LIGHT
        
        except Exception:
            pass
        
        # Default to light theme
        return ThemeMode.LIGHT
    
    def generate_stylesheet(self, font_preset: str = "normal") -> str:
        """
        Generate complete QSS stylesheet using design tokens and typography system.
        
        Creates a comprehensive stylesheet for the application using the current
        theme colors and preset-based typography.
        
        Args:
            font_preset: Font size preset ('small', 'normal', 'large', 'xlarge')
                        Default: 'normal'
        
        Returns:
            str: Complete QSS stylesheet
        
        Note:
            This method now uses the TypographySystem for consistent font scaling.
            The old font_size parameter is deprecated in favor of font_preset.
        """
        from ui.typography import TypographySystem, FontSizePreset
        
        c = self._colors
        
        # Convert preset to typography system
        try:
            preset_enum = FontSizePreset.from_string(font_preset)
        except Exception:
            preset_enum = FontSizePreset.NORMAL
        
        typography_sys = TypographySystem(preset_enum)
        
        # Get font sizes from typography system
        body_size = typography_sys.get_size('body')
        body_sm_size = typography_sys.get_size('body_sm')
        button_size = typography_sys.get_size('button')
        h1_size = typography_sys.get_size('h1')
        h2_size = typography_sys.get_size('h2')
        h3_size = typography_sys.get_size('h3')
        caption_size = typography_sys.get_size('caption')
        
        return f"""
        /* ===== Global Styles ===== */
        QWidget {{
            background-color: {c['background']};
            color: {c['text_primary']};
            font-size: {body_size}px;
            font-family: {Typography.FONT_FAMILY_SANS};
        }}
        
        /* ===== Buttons ===== */
        QPushButton {{
            background-color: {c['primary']};
            color: {c['text_inverse']};
            border: none;
            border-radius: {BorderRadius.MD}px;
            padding: {Spacing.SM}px {Spacing.MD}px;
            font-size: {button_size}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
            min-height: 36px;
        }}
        
        QPushButton:hover {{
            background-color: {c['primary_hover']};
        }}
        
        QPushButton:pressed {{
            background-color: {c['primary_active']};
        }}
        
        QPushButton:disabled {{
            background-color: {c['surface']};
            color: {c['text_disabled']};
        }}
        
        QPushButton[secondary="true"] {{
            background-color: transparent;
            color: {c['primary']};
            border: 2px solid {c['primary']};
        }}
        
        QPushButton[secondary="true"]:hover {{
            background-color: {c['surface_hover']};
        }}
        
        /* ===== Input Fields ===== */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {c['input_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['input_border']};
            border-radius: {BorderRadius.SM}px;
            padding: {Spacing.SM}px;
            selection-background-color: {c['primary']};
            selection-color: {c['text_inverse']};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {c['focus']};
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {c['surface']};
            color: {c['text_disabled']};
            border-color: {c['border_subtle']};
        }}
        
        /* ===== Combo Boxes ===== */
        QComboBox {{
            background-color: {c['input_bg']};
            color: {c['text_primary']};
            border: 1px solid {c['input_border']};
            border-radius: {BorderRadius.SM}px;
            padding: {Spacing.SM}px;
            min-height: 32px;
        }}
        
        QComboBox:hover {{
            border-color: {c['primary']};
        }}
        
        QComboBox:focus {{
            border: 2px solid {c['focus']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            selection-background-color: {c['primary']};
            selection-color: {c['text_inverse']};
        }}
        
        /* ===== Labels ===== */
        QLabel {{
            color: {c['text_primary']};
            background-color: transparent;
            font-size: {body_size}px;
        }}
        
        QLabel[heading="true"] {{
            font-size: {h1_size}px;
            font-weight: {Typography.WEIGHT_BOLD};
        }}
        
        QLabel[subheading="true"] {{
            font-size: {h2_size}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        }}
        
        QLabel[secondary="true"] {{
            color: {c['text_secondary']};
            font-size: {body_sm_size}px;
        }}
        
        QLabel[caption="true"] {{
            font-size: {caption_size}px;
            color: {c['text_tertiary']};
        }}
        
        /* ===== Checkboxes & Radio Buttons ===== */
        QCheckBox, QRadioButton {{
            color: {c['text_primary']};
            spacing: {Spacing.SM}px;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {c['input_border']};
            background-color: {c['input_bg']};
        }}
        
        QCheckBox::indicator {{
            border-radius: {BorderRadius.SM}px;
        }}
        
        QRadioButton::indicator {{
            border-radius: 9px;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {c['primary']};
            border-color: {c['primary']};
        }}
        
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {c['primary']};
        }}
        
        /* ===== Tables ===== */
        QTableWidget, QTableView {{
            background-color: {c['surface']};
            alternate-background-color: {c['surface_hover']};
            gridline-color: {c['border']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: {BorderRadius.SM}px;
        }}
        
        QTableWidget::item, QTableView::item {{
            padding: {Spacing.SM}px;
        }}
        
        QTableWidget::item:selected, QTableView::item:selected {{
            background-color: {c['primary']};
            color: {c['text_inverse']};
        }}
        
        QHeaderView::section {{
            background-color: {c['surface_hover']};
            color: {c['text_primary']};
            padding: {Spacing.SM}px;
            border: none;
            border-bottom: 2px solid {c['border']};
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        }}
        
        /* ===== Scroll Bars ===== */
        QScrollBar:vertical {{
            background-color: {c['surface']};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c['border']};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c['text_tertiary']};
        }}
        
        QScrollBar:horizontal {{
            background-color: {c['surface']};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c['border']};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {c['text_tertiary']};
        }}
        
        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}
        
        /* ===== Progress Bars ===== */
        QProgressBar {{
            background-color: {c['surface']};
            border: 1px solid {c['border']};
            border-radius: {BorderRadius.SM}px;
            text-align: center;
            color: {c['text_primary']};
        }}
        
        QProgressBar::chunk {{
            background-color: {c['primary']};
            border-radius: {BorderRadius.SM}px;
        }}
        
        /* ===== Tabs ===== */
        QTabWidget::pane {{
            border: 1px solid {c['border']};
            border-radius: {BorderRadius.SM}px;
            background-color: {c['surface']};
        }}
        
        QTabBar::tab {{
            background-color: {c['surface']};
            color: {c['text_secondary']};
            border: 1px solid {c['border']};
            padding: {Spacing.SM}px {Spacing.MD}px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {c['primary']};
            color: {c['text_inverse']};
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        }}
        
        QTabBar::tab:hover:!selected {{
            background-color: {c['surface_hover']};
        }}
        
        /* ===== Group Boxes ===== */
        QGroupBox {{
            border: 1px solid {c['border']};
            border-radius: {BorderRadius.MD}px;
            margin-top: {Spacing.MD}px;
            padding-top: {Spacing.MD}px;
            font-weight: {Typography.WEIGHT_SEMIBOLD};
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 {Spacing.SM}px;
            color: {c['text_primary']};
        }}
        
        /* ===== Dialogs ===== */
        QDialog {{
            background-color: {c['background']};
        }}
        
        /* ===== Menus ===== */
        QMenuBar {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border-bottom: 1px solid {c['border']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {c['surface_hover']};
        }}
        
        QMenu {{
            background-color: {c['surface']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: {BorderRadius.SM}px;
        }}
        
        QMenu::item {{
            padding: {Spacing.SM}px {Spacing.MD}px;
        }}
        
        QMenu::item:selected {{
            background-color: {c['primary']};
            color: {c['text_inverse']};
        }}
        
        /* ===== Tool Tips ===== */
        QToolTip {{
            background-color: {c['surface_active']};
            color: {c['text_primary']};
            border: 1px solid {c['border']};
            border-radius: {BorderRadius.SM}px;
            padding: {Spacing.SM}px;
        }}
        """
    
    def __repr__(self) -> str:
        """String representation of the theme."""
        return f"Theme(mode={self._mode.value})"


# Singleton instance
_theme_instance: Optional[Theme] = None


def get_theme() -> Theme:
    """
    Get the singleton theme instance.
    
    Returns:
        Theme: Global theme instance
    """
    global _theme_instance
    if _theme_instance is None:
        _theme_instance = Theme()
    return _theme_instance


# Export public API
__all__ = [
    'Theme',
    'ThemeMode',
    'get_theme',
]

# Made with Bob
