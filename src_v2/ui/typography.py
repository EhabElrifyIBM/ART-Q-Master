"""
Typography System - Modern Font Scaling and Management
=======================================================

This module provides a unified typography system with preset-based font scaling.
Replaces the fragmented font size management across the application.

Features:
- FontSizePreset enum for user-friendly size selection
- TypographySystem class for calculating scaled font sizes
- Type scale based on professional design principles
- Easy integration with PyQt5 widgets
- Accessibility-focused with readable defaults

Usage:
    from ui.typography import FontSizePreset, TypographySystem
    
    # Create typography system with NORMAL preset
    typo = TypographySystem(FontSizePreset.NORMAL)
    
    # Get scaled font sizes
    body_size = typo.get_size('body')      # 16px
    heading_size = typo.get_size('h1')     # 28px
    
    # Apply to widgets
    typo.apply_to_widget(my_label, 'body')
    typo.apply_to_widget(my_button, 'button')
"""

from enum import Enum
from typing import Dict, Optional
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget


class FontSizePreset(Enum):
    """
    Font size presets for user selection.
    
    Provides four preset sizes to accommodate different user preferences
    and accessibility needs. NORMAL is the recommended default.
    
    Attributes:
        SMALL: 87.5% scale - More content visible, compact UI
        NORMAL: 100% scale - Recommended default, balanced readability
        LARGE: 112.5% scale - Better readability, comfortable viewing
        XLARGE: 125% scale - Maximum readability, accessibility focus
    """
    SMALL = "small"      # 87.5% - More content
    NORMAL = "normal"    # 100% - Recommended ⭐
    LARGE = "large"      # 112.5% - Better readability
    XLARGE = "xlarge"    # 125% - Accessibility
    
    def get_multiplier(self) -> float:
        """
        Get the scale multiplier for this preset.
        
        Returns:
            float: Scale multiplier (0.875 to 1.25)
        """
        multipliers = {
            FontSizePreset.SMALL: 0.875,   # 87.5%
            FontSizePreset.NORMAL: 1.0,    # 100%
            FontSizePreset.LARGE: 1.125,   # 112.5%
            FontSizePreset.XLARGE: 1.25,   # 125%
        }
        return multipliers[self]
    
    @classmethod
    def from_string(cls, value: str) -> 'FontSizePreset':
        """
        Convert string to FontSizePreset enum.
        
        Args:
            value: String value ('small', 'normal', 'large', 'xlarge')
        
        Returns:
            FontSizePreset: Corresponding enum value, defaults to NORMAL if invalid
        """
        try:
            return cls(value.lower())
        except (ValueError, AttributeError):
            return cls.NORMAL


class TypographySystem:
    """
    Modern typography system with preset-based scaling.
    
    Provides a professional type scale based on a 16px base size.
    All sizes are calculated relative to the base and scaled by the preset.
    
    Type Scale:
        - display_xl: 3.0× base (48px at NORMAL) - Hero text
        - display_lg: 2.5× base (40px at NORMAL) - Large displays
        - display_md: 2.0× base (32px at NORMAL) - Medium displays
        - h1: 1.75× base (28px at NORMAL) - Main headings
        - h2: 1.5× base (24px at NORMAL) - Section headings
        - h3: 1.25× base (20px at NORMAL) - Subsection headings
        - body: 1.0× base (16px at NORMAL) - Body text
        - body_sm: 0.875× base (14px at NORMAL) - Small body text
        - button: 0.875× base (14px at NORMAL) - Button text
        - caption: 0.75× base (12px at NORMAL) - Captions, labels
        - overline: 0.625× base (10px at NORMAL) - Overline text
    
    Attributes:
        BASE_SIZE: Base font size in pixels (16px - professional standard)
        MIN_SIZE: Minimum allowed font size (12px - accessibility minimum)
        MAX_SIZE: Maximum allowed font size (32px - practical maximum)
    """
    
    # Base configuration
    BASE_SIZE = 16  # Professional default (16px)
    MIN_SIZE = 12   # Accessibility minimum
    MAX_SIZE = 32   # Practical maximum
    
    # Type scale - multipliers relative to base size
    SCALE: Dict[str, float] = {
        # Display sizes (hero text, large headings)
        'display_xl': 3.0,    # 48px at base
        'display_lg': 2.5,    # 40px at base
        'display_md': 2.0,    # 32px at base
        
        # Heading sizes
        'h1': 1.75,           # 28px at base
        'h2': 1.5,            # 24px at base
        'h3': 1.25,           # 20px at base
        'h4': 1.125,          # 18px at base
        
        # Body sizes
        'body': 1.0,          # 16px at base (default)
        'body_lg': 1.125,     # 18px at base
        'body_sm': 0.875,     # 14px at base
        
        # UI component sizes
        'button': 0.875,      # 14px at base
        'input': 1.0,         # 16px at base
        'label': 0.875,       # 14px at base
        
        # Small text
        'caption': 0.75,      # 12px at base
        'overline': 0.625,    # 10px at base
    }
    
    def __init__(self, preset: FontSizePreset = FontSizePreset.NORMAL):
        """
        Initialize typography system with a font size preset.
        
        Args:
            preset: Font size preset to use (default: NORMAL)
        """
        self.preset = preset
        self.multiplier = preset.get_multiplier()
    
    def set_preset(self, preset: FontSizePreset) -> None:
        """
        Change the font size preset.
        
        Args:
            preset: New font size preset to use
        """
        self.preset = preset
        self.multiplier = preset.get_multiplier()
    
    def get_size(self, scale_name: str) -> int:
        """
        Get font size for a specific scale name.
        
        Calculates the final font size by applying both the type scale
        and the preset multiplier to the base size.
        
        Args:
            scale_name: Name from SCALE dict (e.g., 'body', 'h1', 'button')
        
        Returns:
            int: Calculated font size in pixels, clamped to MIN_SIZE and MAX_SIZE
        
        Example:
            >>> typo = TypographySystem(FontSizePreset.NORMAL)
            >>> typo.get_size('body')
            16
            >>> typo.get_size('h1')
            28
        """
        if scale_name not in self.SCALE:
            # Default to body size if scale name not found
            scale_name = 'body'
        
        scale_multiplier = self.SCALE[scale_name]
        calculated_size = self.BASE_SIZE * scale_multiplier * self.multiplier
        
        # Clamp to valid range
        return max(self.MIN_SIZE, min(self.MAX_SIZE, int(round(calculated_size))))
    
    def get_all_sizes(self) -> Dict[str, int]:
        """
        Get all font sizes for the current preset.
        
        Returns:
            Dict[str, int]: Dictionary mapping scale names to pixel sizes
        
        Example:
            >>> typo = TypographySystem(FontSizePreset.NORMAL)
            >>> sizes = typo.get_all_sizes()
            >>> sizes['body']
            16
            >>> sizes['h1']
            28
        """
        return {name: self.get_size(name) for name in self.SCALE.keys()}
    
    def create_font(self, scale_name: str, weight: Optional[int] = None, 
                   family: Optional[str] = None) -> QFont:
        """
        Create a QFont with the specified scale and optional weight/family.
        
        Args:
            scale_name: Name from SCALE dict (e.g., 'body', 'h1')
            weight: Font weight (QFont.Light, QFont.Normal, QFont.Bold, etc.)
            family: Font family name (default: system default)
        
        Returns:
            QFont: Configured QFont object
        
        Example:
            >>> typo = TypographySystem(FontSizePreset.NORMAL)
            >>> heading_font = typo.create_font('h1', QFont.Bold)
            >>> body_font = typo.create_font('body')
        """
        font = QFont()
        
        if family:
            font.setFamily(family)
        
        # Set point size (convert from pixels)
        pixel_size = self.get_size(scale_name)
        font.setPixelSize(pixel_size)
        
        if weight is not None:
            font.setWeight(weight)
        
        return font
    
    def apply_to_widget(self, widget: QWidget, scale_name: str, 
                       weight: Optional[int] = None,
                       family: Optional[str] = None) -> None:
        """
        Apply typography to a widget and optionally its children.
        
        Args:
            widget: QWidget to apply font to
            scale_name: Name from SCALE dict (e.g., 'body', 'h1')
            weight: Optional font weight
            family: Optional font family
        
        Example:
            >>> typo = TypographySystem(FontSizePreset.NORMAL)
            >>> typo.apply_to_widget(my_label, 'h1', QFont.Bold)
            >>> typo.apply_to_widget(my_button, 'button')
        """
        if not hasattr(widget, 'setFont'):
            return
        
        font = self.create_font(scale_name, weight, family)
        widget.setFont(font)
    
    def apply_to_widget_tree(self, widget: QWidget, scale_name: str,
                            weight: Optional[int] = None,
                            family: Optional[str] = None) -> None:
        """
        Apply typography to a widget and all its children recursively.
        
        Useful for applying consistent typography to entire dialogs or panels.
        
        Args:
            widget: Root QWidget to start from
            scale_name: Name from SCALE dict (e.g., 'body', 'h1')
            weight: Optional font weight
            family: Optional font family
        
        Example:
            >>> typo = TypographySystem(FontSizePreset.LARGE)
            >>> typo.apply_to_widget_tree(my_dialog, 'body')
        """
        # Apply to root widget
        self.apply_to_widget(widget, scale_name, weight, family)
        
        # Apply to all children
        if hasattr(widget, 'findChildren'):
            children = widget.findChildren(QWidget)
            for child in children:
                self.apply_to_widget(child, scale_name, weight, family)
    
    def get_line_height(self, scale_name: str, multiplier: float = 1.5) -> int:
        """
        Calculate line height for a given scale.
        
        Args:
            scale_name: Name from SCALE dict
            multiplier: Line height multiplier (default: 1.5 for comfortable reading)
        
        Returns:
            int: Line height in pixels
        
        Example:
            >>> typo = TypographySystem(FontSizePreset.NORMAL)
            >>> typo.get_line_height('body')
            24
        """
        font_size = self.get_size(scale_name)
        return int(round(font_size * multiplier))
    
    def __repr__(self) -> str:
        """String representation of the typography system."""
        return f"TypographySystem(preset={self.preset.value}, multiplier={self.multiplier})"


# Convenience function for quick access
def create_typography_system(preset_name: str = "normal") -> TypographySystem:
    """
    Create a TypographySystem from a preset name string.
    
    Args:
        preset_name: Preset name ('small', 'normal', 'large', 'xlarge')
    
    Returns:
        TypographySystem: Configured typography system
    
    Example:
        >>> typo = create_typography_system('large')
        >>> body_size = typo.get_size('body')
    """
    preset = FontSizePreset.from_string(preset_name)
    return TypographySystem(preset)


# Export public API
__all__ = [
    'FontSizePreset',
    'TypographySystem',
    'create_typography_system',
]

# Made with Bob
