"""
Feedback Components - Modern User Feedback Widgets
===================================================

This module provides modern feedback components following IBM Carbon Design principles.
All feedback components integrate with the design system and support theming.

Feedback Components:
- Toast: Toast notification for temporary messages
- ModernSpinner: Loading spinner animation
- ModernProgressBar: Progress bar with percentage
- Badge: Status badge for labels

Features:
- Uses design_system.py for colors, spacing, borders
- Integrates with typography.py for font sizing
- Supports theme changes via V2SettingsBus
- Auto-dismiss for toasts
- Animated spinners
- Semantic colors (success, warning, error, info)

Usage:
    from ui.components_v2 import Toast, ModernSpinner, Badge
    
    # Show toast notification
    Toast.success(parent, "File saved successfully!")
    
    # Show loading spinner
    spinner = ModernSpinner()
    spinner.start()
    
    # Create status badge
    badge = Badge("Active", "success")
"""

from typing import Optional
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QProgressBar,
    QGraphicsOpacityEffect
)

from ui.design_system import Colors, Spacing, BorderRadius, ZIndex
from ui.typography import TypographySystem, FontSizePreset


class Toast(QFrame):
    """
    Toast notification for temporary messages.
    
    Auto-dismissing notification that appears at the top of the screen.
    
    Attributes:
        _theme_mode: Current theme mode
        _typography: Typography system
        _timer: Auto-dismiss timer
    """
    
    def __init__(self, message: str, message_type: str = "info",
                 parent: Optional[QWidget] = None, duration: Optional[int] = None):
        """
        Initialize toast notification.
        
        Args:
            message: Toast message text
            message_type: Type ('info', 'success', 'warning', 'error')
            parent: Parent widget
            duration: Duration in milliseconds (None = use default for type)
        """
        super().__init__(parent)
        
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        self._message_type = message_type
        
        # Set default duration based on message type if not specified
        if duration is None:
            if message_type == "success":
                duration = 3000  # 3 seconds
            elif message_type == "info":
                duration = 4000  # 4 seconds
            elif message_type == "warning":
                duration = 5000  # 5 seconds
            else:  # error
                duration = 5000  # 5 seconds
        
        self._duration = duration
        
        # Connect to preset changes
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in Toast: {e}")
        
        self._setup_ui(message)
        self._apply_style()
        self._setup_auto_dismiss(self._duration)
    
    def _setup_ui(self, message: str) -> None:
        """Set up toast UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        
        self._label = QLabel(message)
        self._label.setWordWrap(True)
        self._typography.apply_to_widget(self._label, 'body')
        
        layout.addWidget(self._label)
        
        # Set fixed properties
        self.setFixedHeight(60)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
        # Position at top center of parent
        if self.parent():
            parent_rect = self.parent().rect()
            x = (parent_rect.width() - self.width()) // 2
            self.move(x, 20)
        
        # Set high z-index
        self.raise_()
    
    def _apply_style(self) -> None:
        """Apply toast stylesheet based on message type."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        # Get colors based on message type
        if self._message_type == "success":
            bg_color = colors['success_bg']
            text_color = colors['success']
            border_color = colors['success']
        elif self._message_type == "warning":
            bg_color = colors['warning_bg']
            text_color = colors['warning']
            border_color = colors['warning']
        elif self._message_type == "error":
            bg_color = colors['danger_bg']
            text_color = colors['danger']
            border_color = colors['danger']
        else:  # info
            bg_color = colors['info_bg']
            text_color = colors['info']
            border_color = colors['info']
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {BorderRadius.MD}px;
            }}
        """)
        
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: transparent;
            }}
        """)
    
    def _setup_auto_dismiss(self, duration: int = 3000) -> None:
        """
        Set up auto-dismiss timer.
        
        Args:
            duration: Duration in milliseconds before auto-dismiss
        """
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self._timer.start(duration)
    
    def _fade_out(self) -> None:
        """Fade out and close toast."""
        self.hide()
        self.deleteLater()
    
    @staticmethod
    def show_toast(parent: Optional[QWidget], message: str,
                   message_type: str = "info", duration: Optional[int] = None) -> 'Toast':
        """
        Show a toast notification.
        
        Args:
            parent: Parent widget
            message: Toast message
            message_type: Message type
            duration: Duration in milliseconds (None = use default for type)
        
        Returns:
            Toast: Created toast instance
        """
        toast = Toast(message, message_type, parent, duration)
        toast.show()
        return toast
    
    @staticmethod
    def info(parent: Optional[QWidget], message: str, duration: int = 4000) -> 'Toast':
        """
        Show info toast (blue, 4s default).
        
        Args:
            parent: Parent widget
            message: Toast message
            duration: Duration in milliseconds (default: 4000ms = 4s)
        
        Returns:
            Toast: Created toast instance
        """
        return Toast.show_toast(parent, message, "info", duration)
    
    @staticmethod
    def success(parent: Optional[QWidget], message: str, duration: int = 3000) -> 'Toast':
        """
        Show success toast (green, 3s default).
        
        Args:
            parent: Parent widget
            message: Toast message
            duration: Duration in milliseconds (default: 3000ms = 3s)
        
        Returns:
            Toast: Created toast instance
        """
        return Toast.show_toast(parent, message, "success", duration)
    
    @staticmethod
    def warning(parent: Optional[QWidget], message: str, duration: int = 5000) -> 'Toast':
        """
        Show warning toast (yellow, 5s default).
        
        Args:
            parent: Parent widget
            message: Toast message
            duration: Duration in milliseconds (default: 5000ms = 5s)
        
        Returns:
            Toast: Created toast instance
        """
        return Toast.show_toast(parent, message, "warning", duration)
    
    @staticmethod
    def error(parent: Optional[QWidget], message: str, title: str = "Error") -> int:
        """
        Show error dialog (requires acknowledgment).
        
        Uses MessageDialog instead of toast for errors to ensure user sees the message.
        
        Args:
            parent: Parent widget
            message: Error message
            title: Dialog title (default: "Error")
        
        Returns:
            int: Dialog result code
        """
        from .dialogs import MessageDialog
        return MessageDialog.error(parent, title, message)
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            self._typography.apply_to_widget(self._label, 'body')
        except Exception as e:
            print(f"Warning: Could not update font preset in Toast: {e}")


class ModernSpinner(QWidget):
    """
    Modern loading spinner animation.
    
    Animated spinner for indicating loading states.
    
    Attributes:
        _theme_mode: Current theme mode
        _timer: Animation timer
        _angle: Current rotation angle
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize modern spinner.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._theme_mode = "light"
        self._timer = QTimer()
        self._angle = 0
        
        # Connect to preset changes (spinner doesn't use typography but keep for consistency)
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in ModernSpinner: {e}")
        
        self._setup_ui()
        self._timer.timeout.connect(self._rotate)
    
    def _setup_ui(self) -> None:
        """Set up spinner UI."""
        self.setFixedSize(32, 32)
    
    def start(self) -> None:
        """Start spinner animation."""
        self._timer.start(50)  # 20 FPS
    
    def stop(self) -> None:
        """Stop spinner animation."""
        self._timer.stop()
    
    def _rotate(self) -> None:
        """Rotate spinner."""
        self._angle = (self._angle + 15) % 360
        self.update()
    
    def paintEvent(self, event) -> None:
        """Paint spinner."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw spinner arcs
        rect = QRect(4, 4, 24, 24)
        pen = QPen()
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        
        # Background arc
        pen.setColor(colors['border'])
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        
        # Foreground arc
        pen.setColor(colors['primary'])
        painter.setPen(pen)
        painter.drawArc(rect, self._angle * 16, 90 * 16)
    
    def set_theme(self, theme_mode: str) -> None:
        """Update spinner theme."""
        self._theme_mode = theme_mode
        self.update()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        # Spinner doesn't use typography, but method needed for consistency
        pass


class ModernProgressBar(QProgressBar):
    """
    Modern progress bar with percentage display.
    
    Enhanced progress bar with design system integration.
    
    Attributes:
        _theme_mode: Current theme mode
        _typography: Typography system
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize modern progress bar.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        
        # Connect to preset changes
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in ModernProgressBar: {e}")
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up progress bar UI."""
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(0)
        self.setTextVisible(True)
        self.setMinimumHeight(24)
    
    def _apply_style(self) -> None:
        """Apply progress bar stylesheet."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        self.setStyleSheet(f"""
            QProgressBar {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.SM}px;
                text-align: center;
                color: {colors['text_primary']};
                font-weight: 600;
            }}
            
            QProgressBar::chunk {{
                background-color: {colors['primary']};
                border-radius: {BorderRadius.SM}px;
            }}
        """)
    
    def set_theme(self, theme_mode: str) -> None:
        """Update progress bar theme."""
        self._theme_mode = theme_mode
        self._apply_style()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            # Progress bar text size is controlled by stylesheet
            self._apply_style()
        except Exception as e:
            print(f"Warning: Could not update font preset in ModernProgressBar: {e}")


class Badge(QLabel):
    """
    Status badge for labels and indicators.
    
    Small badge for showing status or count information.
    
    Attributes:
        _theme_mode: Current theme mode
        _typography: Typography system
        _badge_type: Badge type for styling
    """
    
    def __init__(self, text: str = "", badge_type: str = "default",
                 parent: Optional[QWidget] = None):
        """
        Initialize badge.
        
        Args:
            text: Badge text
            badge_type: Badge type ('default', 'success', 'warning', 'error', 'info')
            parent: Parent widget
        """
        super().__init__(text, parent)
        
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        self._badge_type = badge_type
        
        # Connect to preset changes
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in Badge: {e}")
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up badge UI."""
        self.setAlignment(Qt.AlignCenter)
        self._typography.apply_to_widget(self, 'caption', QFont.Bold)
        
        # Set minimum size
        self.setMinimumHeight(20)
        self.setMinimumWidth(20)
    
    def _apply_style(self) -> None:
        """Apply badge stylesheet based on type."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        # Get colors based on badge type
        if self._badge_type == "success":
            bg_color = colors['success_bg']
            text_color = colors['success']
        elif self._badge_type == "warning":
            bg_color = colors['warning_bg']
            text_color = colors['warning']
        elif self._badge_type == "error":
            bg_color = colors['danger_bg']
            text_color = colors['danger']
        elif self._badge_type == "info":
            bg_color = colors['info_bg']
            text_color = colors['info']
        else:  # default
            bg_color = colors['surface_hover']
            text_color = colors['text_primary']
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: {BorderRadius.FULL}px;
                padding: {Spacing.XS}px {Spacing.SM}px;
            }}
        """)
    
    def set_theme(self, theme_mode: str) -> None:
        """Update badge theme."""
        self._theme_mode = theme_mode
        self._apply_style()
    
    def set_type(self, badge_type: str) -> None:
        """
        Update badge type.
        
        Args:
            badge_type: New badge type
        """
        self._badge_type = badge_type
        self._apply_style()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            self._typography.apply_to_widget(self, 'caption', QFont.Bold)
        except Exception as e:
            print(f"Warning: Could not update font preset in Badge: {e}")


# Export all feedback classes
__all__ = [
    'Toast',
    'ModernSpinner',
    'ModernProgressBar',
    'Badge',
]

# Made with Bob