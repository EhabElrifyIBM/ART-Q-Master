"""
Shared UI services for the src_v2 unified Phase 6 system.
"""

from enum import Enum
from typing import Dict

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget

from utils.runtime import get_theme_mode, get_ui_font_size


class ThemeMode(Enum):
    """Supported theme modes for the v2 UI layer."""

    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class V2SettingsBus(QObject):
    """Central broadcaster for unified v2 UI settings updates."""

    theme_changed = pyqtSignal(str)
    font_size_changed = pyqtSignal(int)
    font_preset_changed = pyqtSignal(str)  # 'small', 'normal', 'large', 'xlarge'
    dev_mode_changed = pyqtSignal(bool)    # DEV MODE toggled on/off

    def __init__(self):
        super().__init__()
        self._theme = get_theme_mode()
        self._font_size = max(20, get_ui_font_size(default=20))
        self._dev_mode: bool = False

    @property
    def theme(self) -> str:
        return self._theme

    @property
    def font_size(self) -> int:
        return self._font_size

    @property
    def dev_mode(self) -> bool:
        """True when DEV MODE is active (multi-agent sheet names enabled)."""
        return self._dev_mode

    def set_theme(self, theme: str) -> None:
        if theme not in {"light", "dark", "auto"}:
            return
        self._theme = theme
        self.theme_changed.emit(theme)

    def set_font_size(self, size: int) -> None:
        size = max(20, min(40, int(size)))
        self._font_size = size
        self.font_size_changed.emit(size)

    def set_dev_mode(self, enabled: bool) -> None:
        """Toggle DEV MODE and broadcast to all connected windows."""
        self._dev_mode = bool(enabled)
        self.dev_mode_changed.emit(self._dev_mode)

    def calculate_responsive_font_size(self, width: int, height: int) -> int:
        """Scale the global UI font from a 20px base according to window size."""
        base_width = 1280
        base_height = 820
        width_ratio = max(0.8, min(1.35, width / base_width))
        height_ratio = max(0.8, min(1.35, height / base_height))
        ratio = (width_ratio + height_ratio) / 2
        return max(20, min(32, int(round(20 * ratio))))


class V2ThemeService:
    """Lightweight unified theme token provider for v2 screens."""

    LIGHT: Dict[str, str] = {
        "window_bg": "#eaf1ff",
        "surface": "#ffffff",
        "surface_alt": "#f7faff",
        "surface_border": "#c6d6f5",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "accent": "#0f62fe",
        "accent_hover": "#0353e9",
        "accent_pressed": "#002d9c",
        "accent_soft": "#dbeafe",
        "badge_bg": "#dbeafe",
        "badge_text": "#1d4ed8",
        "badge_border": "#93c5fd",
        "success": "#198038",
        "warning": "#b76e00",
    }

    DARK: Dict[str, str] = {
        "window_bg": "#0f172a",
        "surface": "#111827",
        "surface_alt": "#1f2937",
        "surface_border": "#334155",
        "text_primary": "#f8fafc",
        "text_secondary": "#cbd5e1",
        "accent": "#60a5fa",
        "accent_hover": "#3b82f6",
        "accent_pressed": "#2563eb",
        "accent_soft": "#1e3a8a",
        "badge_bg": "#1e3a8a",
        "badge_text": "#dbeafe",
        "badge_border": "#60a5fa",
        "success": "#42be65",
        "warning": "#f1c21b",
    }

    def colors_for(self, theme: str) -> Dict[str, str]:
        """
        Get color palette for the specified theme.
        
        Args:
            theme: Theme mode ('light', 'dark', or 'auto')
            
        Returns:
            Dict of color tokens
        """
        # Handle 'auto' theme by detecting system dark mode
        if theme == ThemeMode.AUTO.value:
            is_dark = self._detect_system_dark_mode()
            return self.DARK.copy() if is_dark else self.LIGHT.copy()
        
        # Explicit dark or light theme
        if theme == ThemeMode.DARK.value:
            return self.DARK.copy()
        return self.LIGHT.copy()
    
    def _detect_system_dark_mode(self) -> bool:
        """
        Detect if system is in dark mode.
        
        Returns:
            True if dark mode is detected, False otherwise
        """
        try:
            # Windows 10/11 dark mode detection via registry
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            # Value is 0 for dark mode, 1 for light mode
            return value == 0
        except Exception:
            # Default to light mode if Windows registry detection fails
            return False

    def build_shell_stylesheet(self, theme: str, font_size: int = 20, font_preset: str = "normal") -> str:
        """
        Build stylesheet for shell/main menu.
        
        Args:
            theme: Theme mode ('light', 'dark', 'auto')
            font_size: Legacy font size parameter (deprecated, kept for backward compatibility)
            font_preset: Font preset ('small', 'normal', 'large', 'xlarge')
        
        Returns:
            str: QSS stylesheet
        """
        from ui.typography import TypographySystem, FontSizePreset
        
        colors = self.colors_for(theme)
        
        # Use typography system for consistent sizing
        try:
            preset_enum = FontSizePreset.from_string(font_preset)
        except Exception:
            preset_enum = FontSizePreset.NORMAL
        
        typography = TypographySystem(preset_enum)
        
        # Get sizes from typography system
        title_size = typography.get_size('h1')
        h2_size = typography.get_size('h2')
        subtitle_size = typography.get_size('body')
        section_size = typography.get_size('h3')
        card_title_size = typography.get_size('h3')
        body_size = typography.get_size('body')
        badge_size = typography.get_size('caption')
        footer_size = typography.get_size('caption')
        button_size = typography.get_size('button')

        return f"""
        QMainWindow {{
            background-color: {colors['window_bg']};
        }}
        QScrollArea {{
            border: none;
            background: transparent;
        }}
        QFrame#headerFrame {{
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 {colors['surface']},
                stop: 1 {colors['surface_alt']}
            );
            border: 1px solid {colors['surface_border']};
            border-radius: 20px;
        }}
        QFrame#toolCard, QFrame#emptyState, QFrame#footerFrame {{
            background: {colors['surface']};
            border: 1px solid {colors['surface_border']};
            border-radius: 18px;
        }}
        QFrame#toolCard:hover {{
            background: {colors['surface_alt']};
            border: 2px solid {colors['accent']};
        }}
        QLabel#titleLabel {{
            color: {colors['text_primary']};
            font-size: {title_size}px;
            font-weight: 800;
        }}
        QLabel#subtitleLabel {{
            color: {colors['text_secondary']};
            font-size: {subtitle_size}px;
            font-weight: 500;
        }}
        QLabel#welcomeLabel {{
            color: {colors['text_primary']};
            font-size: {h2_size}px;
            font-weight: 700;
            background: transparent;
        }}
        QLabel#sectionTitle, QLabel#toolName, QLabel#emptyTitle {{
            color: {colors['text_primary']};
            font-size: {section_size}px;
            font-weight: 700;
        }}
        QLabel#toolDescription, QLabel#emptyDescription {{
            color: {colors['text_secondary']};
            font-size: {body_size}px;
            line-height: 1.4em;
        }}
        QLabel#toolMeta, QLabel#footerLabel {{
            color: {colors['text_secondary']};
            font-size: {footer_size}px;
            font-weight: 500;
        }}
        QLabel#versionBadge {{
            color: {colors['badge_text']};
            background: {colors['badge_bg']};
            border: 1px solid {colors['badge_border']};
            border-radius: 999px;
            padding: 4px 12px;
            font-size: {badge_size}px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        QLabel#toolBadge {{
            background: {colors['badge_bg']};
            color: {colors['badge_text']};
            border: 1px solid {colors['badge_border']};
            border-radius: 999px;
            padding: 8px 14px;
            font-size: {badge_size}px;
            font-weight: 700;
        }}
        QPushButton#primaryButton {{
            background: {colors['accent']};
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 22px;
            font-size: {button_size}px;
            font-weight: 700;
            min-width: 150px;
        }}
        QPushButton#primaryButton:hover {{
            background: {colors['accent_hover']};
        }}
        QPushButton#primaryButton:pressed {{
            background: {colors['accent_pressed']};
        }}
        QPushButton#secondaryButton {{
            background: transparent;
            color: {colors['accent']};
            border: 2px solid {colors['accent']};
            border-radius: 12px;
            padding: 12px 20px;
            font-size: {button_size}px;
            font-weight: 700;
            min-width: 150px;
        }}
        QPushButton#secondaryButton:hover {{
            background: {colors['accent_soft']};
        }}
        QPushButton#settingsButton {{
            background: transparent;
            color: {colors['accent']};
            border: 2px solid {colors['accent']};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: {button_size}px;
            font-weight: 600;
        }}
        QPushButton#settingsButton:hover {{
            background: {colors['accent']};
            color: white;
        }}
        QPushButton#settingsButton:pressed {{
            background: {colors['accent_pressed']};
            color: white;
        }}
        QPushButton#helpButton {{
            background: transparent;
            color: {colors['accent']};
            border: 2px solid {colors['accent']};
            border-radius: 8px;
            padding: 8px;
            font-size: {button_size}px;
            font-weight: 600;
        }}
        QPushButton#helpButton:hover {{
            background: {colors['accent']};
            color: white;
        }}
        QPushButton#helpButton:pressed {{
            background: {colors['accent_pressed']};
            color: white;
        }}
        """

    def build_tool_dialog_stylesheet(self, theme: str, font_size: int = 20, font_preset: str = "normal") -> str:
        """
        Build stylesheet for tool dialogs.
        
        Args:
            theme: Theme mode ('light', 'dark', 'auto')
            font_size: Legacy font size parameter (deprecated, kept for backward compatibility)
            font_preset: Font preset ('small', 'normal', 'large', 'xlarge')
        
        Returns:
            str: QSS stylesheet
        """
        from ui.typography import TypographySystem, FontSizePreset
        
        colors = self.colors_for(theme)
        
        # Use typography system for consistent sizing
        try:
            preset_enum = FontSizePreset.from_string(font_preset)
        except Exception:
            preset_enum = FontSizePreset.NORMAL
        
        typography = TypographySystem(preset_enum)
        
        # Get sizes from typography system
        title_size = typography.get_size('h2')
        subtitle_size = typography.get_size('body')
        body_size = typography.get_size('body')
        button_size = typography.get_size('button')

        return f"""
        QWidget {{
            background-color: {colors['window_bg']};
            color: {colors['text_primary']};
        }}
        QFrame#dialogCard {{
            background: {colors['surface']};
            border: 1px solid {colors['surface_border']};
            border-radius: 20px;
        }}
        QLabel#dialogTitle {{
            color: {colors['text_primary']};
            font-size: {title_size}px;
            font-weight: 800;
        }}
        QLabel#dialogSubtitle, QLabel#dialogBody {{
            color: {colors['text_secondary']};
            font-size: {subtitle_size}px;
        }}
        QPushButton#primaryButton {{
            background: {colors['accent']};
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 20px;
            font-size: {button_size}px;
            font-weight: 700;
            min-width: 150px;
        }}
        QPushButton#primaryButton:hover {{
            background: {colors['accent_hover']};
        }}
        QPushButton#secondaryButton {{
            background: transparent;
            color: {colors['accent']};
            border: 2px solid {colors['accent']};
            border-radius: 12px;
            padding: 12px 20px;
            font-size: {button_size}px;
            font-size: {font_size}px;
            font-weight: 700;
            min-width: 150px;
        }}
        QPushButton#secondaryButton:hover {{
            background: {colors['accent_soft']};
        }}
        """


_settings_bus = None


def get_v2_settings_bus() -> V2SettingsBus:
    """Return the singleton v2 settings broadcaster."""
    global _settings_bus
    if _settings_bus is None:
        _settings_bus = V2SettingsBus()
    return _settings_bus

# Made with Bob


def apply_font_to_widget_and_children(widget, size_in_pixels):
    """
    Apply font size to a widget and all its children recursively.
    
    This utility function is used by CaseReviewer_v2 and CompaniesProcess_v2
    to apply dynamic font sizing from config settings.
    
    Args:
        widget: The parent widget (QWidget or subclass)
        size_in_pixels: Font size in pixels (10-40, will be clamped)
    
    Example:
        >>> from ui.services import apply_font_to_widget_and_children
        >>> apply_font_to_widget_and_children(my_dialog, 18)
    """
    try:
        # Clamp to valid range (10-40 pixels)
        size_in_pixels = max(10, min(40, int(size_in_pixels)))
        
        # Create font with specified size
        scaled_font = QFont()
        scaled_font.setPointSize(size_in_pixels)
        
        # Apply to the widget itself
        if hasattr(widget, 'setFont'):
            widget.setFont(scaled_font)
        
        # Recursively apply to all child widgets
        if hasattr(widget, 'findChildren'):
            children = widget.findChildren(QWidget)
            for child in children:
                if hasattr(child, 'setFont'):
                    try:
                        child.setFont(scaled_font)
                    except Exception as e:
                        print(f"[DEBUG] Could not set font on {child.__class__.__name__}: {e}")
    except Exception as e:
        print(f"[WARNING] Error in apply_font_to_widget_and_children: {e}")
