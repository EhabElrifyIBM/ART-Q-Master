"""
Typography Mixin - Reusable Typography Integration for PyQt5 Widgets
====================================================================

This module provides a mixin class for easy integration of the typography system
into PyQt5 widgets. It handles font preset changes, provides convenient font
access methods, and manages typography application.

Features:
- Automatic typography system initialization
- Reactive font preset changes via V2SettingsBus
- Convenient font access methods
- Easy integration with any QWidget subclass

Usage:
    from ui.typography_mixin import V2TypographyMixin
    from PyQt5.QtWidgets import QMainWindow
    
    class MyWindow(QMainWindow, V2TypographyMixin):
        def __init__(self):
            super().__init__()
            V2TypographyMixin.__init__(self)  # Initialize mixin
            
            # Use typography methods
            label = QLabel("Hello")
            label.setFont(self.get_font('h1', weight=QFont.Bold))
            
            # Apply typography to all widgets
            self.apply_typography()
        
        def apply_typography(self):
            '''Override to apply typography to your widgets.'''
            # Update all your widgets here
            self.my_label.setFont(self.get_font('body'))
            self.my_button.setFont(self.get_font('button'))
"""

from typing import Optional
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget

from ui.typography import TypographySystem, FontSizePreset
from ui.services import get_v2_settings_bus


class V2TypographyMixin:
    """
    Mixin class for integrating typography system into PyQt5 widgets.
    
    This mixin provides:
    - Automatic typography system initialization
    - Reactive font preset changes
    - Convenient font access methods
    - Typography application framework
    
    The mixin automatically connects to V2SettingsBus to receive font preset
    changes and calls apply_typography() when changes occur.
    
    Attributes:
        typography: TypographySystem instance for font calculations
        settings_bus: V2SettingsBus instance for reactive updates
    
    Methods:
        get_font: Get QFont for a specific scale
        get_size: Get pixel size for a specific scale
        apply_typography: Override to apply typography to widgets
    
    Example:
        class MyDialog(QDialog, V2TypographyMixin):
            def __init__(self):
                super().__init__()
                V2TypographyMixin.__init__(self)
                
                self.title_label = QLabel("Title")
                self.body_label = QLabel("Body text")
                
                self.apply_typography()
            
            def apply_typography(self):
                self.title_label.setFont(self.get_font('h1', QFont.Bold))
                self.body_label.setFont(self.get_font('body'))
    """
    
    def __init__(self):
        """
        Initialize the typography mixin.
        
        This should be called in the __init__ method of the class using the mixin,
        after calling super().__init__().
        
        Example:
            class MyWindow(QMainWindow, V2TypographyMixin):
                def __init__(self):
                    super().__init__()
                    V2TypographyMixin.__init__(self)  # Initialize mixin
        """
        # Initialize typography system with NORMAL preset
        self.typography = TypographySystem(FontSizePreset.NORMAL)
        
        # Get settings bus for reactive updates
        self.settings_bus = get_v2_settings_bus()
        
        # Load current font preset from settings
        try:
            from ui.settings import SettingsManager
            settings = SettingsManager()
            current_preset = settings.appearance.font_size_preset
            preset = FontSizePreset.from_string(current_preset)
            self.typography.set_preset(preset)
        except Exception:
            # If settings can't be loaded, use NORMAL preset
            pass
        
        # Connect to font preset changes
        self.settings_bus.font_preset_changed.connect(self._on_font_preset_changed)
    
    def _on_font_preset_changed(self, preset_name: str):
        """
        Handle font preset changes from settings bus.
        
        This method is automatically called when the user changes the font preset
        in the settings dialog. It updates the typography system and calls
        apply_typography() to update all widgets.
        
        Args:
            preset_name: Name of the new preset ('small', 'normal', 'large', 'xlarge')
        """
        preset = FontSizePreset.from_string(preset_name)
        self.typography.set_preset(preset)
        self.apply_typography()
    
    def get_font(self, scale_name: str = 'body', 
                 weight: Optional[int] = None,
                 family: Optional[str] = None) -> QFont:
        """
        Get a QFont for a specific typography scale.
        
        This is a convenience method that wraps typography.create_font() for
        easy access to fonts with the current preset applied.
        
        Args:
            scale_name: Typography scale name (e.g., 'body', 'h1', 'button')
                       Available scales: display_xl, display_lg, display_md,
                       h1, h2, h3, h4, body, body_lg, body_sm, button, input,
                       label, caption, overline
            weight: Optional font weight (QFont.Light, QFont.Normal, QFont.Bold, etc.)
            family: Optional font family name (default: system default)
        
        Returns:
            QFont: Configured QFont object with the specified scale and options
        
        Example:
            # Get a bold heading font
            heading_font = self.get_font('h1', QFont.Bold)
            
            # Get a body font with custom family
            body_font = self.get_font('body', family='IBM Plex Sans')
            
            # Get a button font
            button_font = self.get_font('button')
        """
        return self.typography.create_font(scale_name, weight, family)
    
    def get_size(self, scale_name: str = 'body') -> int:
        """
        Get the pixel size for a specific typography scale.
        
        This is useful when you need just the size value for stylesheets or
        manual font configuration.
        
        Args:
            scale_name: Typography scale name (e.g., 'body', 'h1', 'button')
        
        Returns:
            int: Font size in pixels for the current preset
        
        Example:
            # Get size for stylesheet
            body_size = self.get_size('body')
            stylesheet = f"font-size: {body_size}px;"
            
            # Get size for calculations
            button_size = self.get_size('button')
            button_height = button_size + 20  # Add padding
        """
        return self.typography.get_size(scale_name)
    
    def get_line_height(self, scale_name: str = 'body', multiplier: float = 1.5) -> int:
        """
        Get the line height for a specific typography scale.
        
        Line height is calculated as font size × multiplier, useful for
        text areas and multi-line labels.
        
        Args:
            scale_name: Typography scale name (e.g., 'body', 'h1')
            multiplier: Line height multiplier (default: 1.5 for comfortable reading)
        
        Returns:
            int: Line height in pixels
        
        Example:
            # Get line height for text area
            line_height = self.get_line_height('body')
            text_area.setLineHeight(line_height)
        """
        return self.typography.get_line_height(scale_name, multiplier)
    
    def apply_typography(self):
        """
        Apply typography to all widgets.
        
        This method should be overridden in subclasses to apply typography
        to all relevant widgets. It is automatically called when:
        - The mixin is initialized
        - The font preset changes
        
        Override this method to update fonts on all your widgets:
        
        Example:
            def apply_typography(self):
                '''Apply typography to all widgets.'''
                # Update labels
                self.title_label.setFont(self.get_font('h1', QFont.Bold))
                self.subtitle_label.setFont(self.get_font('h2'))
                self.body_label.setFont(self.get_font('body'))
                
                # Update buttons
                self.primary_button.setFont(self.get_font('button', QFont.Bold))
                self.secondary_button.setFont(self.get_font('button'))
                
                # Update inputs
                self.text_input.setFont(self.get_font('input'))
                
                # Regenerate stylesheet if needed
                self.setStyleSheet(self.generate_stylesheet())
        
        Note:
            If you don't override this method, font preset changes will not
            automatically update your widgets. You must implement this method
            to enable reactive typography updates.
        """
        # Default implementation does nothing
        # Subclasses should override this method
        pass
    
    def apply_typography_to_widget(self, widget: QWidget, scale_name: str,
                                   weight: Optional[int] = None,
                                   family: Optional[str] = None):
        """
        Apply typography to a single widget.
        
        Convenience method for applying typography to individual widgets.
        
        Args:
            widget: QWidget to apply typography to
            scale_name: Typography scale name
            weight: Optional font weight
            family: Optional font family
        
        Example:
            # Apply to a single widget
            self.apply_typography_to_widget(my_label, 'h1', QFont.Bold)
        """
        if hasattr(widget, 'setFont'):
            font = self.get_font(scale_name, weight, family)
            widget.setFont(font)
    
    def apply_typography_to_children(self, parent: QWidget, scale_name: str,
                                     weight: Optional[int] = None,
                                     family: Optional[str] = None):
        """
        Apply typography to a widget and all its children recursively.
        
        Useful for applying consistent typography to entire sections or dialogs.
        
        Args:
            parent: Parent QWidget to start from
            scale_name: Typography scale name
            weight: Optional font weight
            family: Optional font family
        
        Example:
            # Apply to entire dialog
            self.apply_typography_to_children(self.content_frame, 'body')
        """
        self.typography.apply_to_widget_tree(parent, scale_name, weight, family)


# Export public API
__all__ = [
    'V2TypographyMixin',
]

# Made with Bob