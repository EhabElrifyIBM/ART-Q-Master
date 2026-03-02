# ============================================================================
# settings_aware_dialog.py - Settings-Aware Dialog Mixin
# ============================================================================
# Phase 5.4: Settings Integration
#
# Provides mixin class for dialogs/windows to respond to settings changes.
# Allows automatic theme and font size updates when settings change.
# ============================================================================

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QWidget


class SettingsAwareMixin:
    """
    Mixin class to make dialogs/windows respond to settings changes.
    
    Usage:
        class MyDialog(QDialog, SettingsAwareMixin):
            def __init__(self):
                super().__init__()
                self.setup_settings_awareness()
            
            def on_theme_changed(self, theme):
                # Override to respond to theme changes
                pass
            
            def on_font_size_changed(self, scale):
                # Override to respond to font size changes
                pass
    """
    
    def setup_settings_awareness(self):
        """Setup dialog to listen for settings changes."""
        try:
            from ui.settings_observer import get_settings_observer
            
            observer = get_settings_observer()
            observer.theme_changed.connect(self.on_theme_changed)
            observer.font_size_changed.connect(self.on_font_size_changed)
            print(f"[SETTINGS AWARE] {self.__class__.__name__} now listening for settings changes")
        except Exception as e:
            print(f"[WARNING] Could not setup settings awareness: {e}")
    
    def on_theme_changed(self, theme: str):
        """Called when theme changes. Override in subclass."""
        print(f"[{self.__class__.__name__}] Theme changed to: {theme}")
    
    def on_font_size_changed(self, scale: float):
        """Called when font size changes. Override in subclass."""
        print(f"[{self.__class__.__name__}] Font size changed to: {scale}px")
    
    def apply_dynamic_font_size(self, size_in_pixels: float):
        """
        Apply font size to this widget and all children recursively.
        
        Args:
            size_in_pixels: Font size in pixels (10-40)
        """
        try:
            app = QApplication.instance()
            if not app:
                return
            
            # Clamp to valid range (10-40 pixels)
            size_in_pixels = max(10, min(40, int(size_in_pixels)))
            
            # Apply using static helper
            apply_font_to_widget_and_children(self, size_in_pixels)
            
            print(f"[SETTINGS AWARE] Applied font size {size_in_pixels}px to {self.__class__.__name__} and children")
        except Exception as e:
            print(f"[WARNING] Could not apply font size to {self.__class__.__name__}: {e}")


def apply_font_to_widget_and_children(widget, size_in_pixels):
    """
    Static helper to apply font size to a widget and all its children recursively.
    
    Args:
        widget: The parent widget
        size_in_pixels: Font size in pixels (10-40)
    """
    try:
        size_in_pixels = max(10, min(40, int(size_in_pixels)))
        
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
