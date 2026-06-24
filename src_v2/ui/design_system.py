"""
Design System - Central Design Tokens
======================================

This module provides the foundational design tokens for the modern UI system.
Based on IBM Carbon Design System principles with an 8px grid system.

Design Tokens Include:
- Spacing system (8px grid)
- Border radius values
- Shadow definitions
- Color palette (IBM Carbon)
- Breakpoints for responsive design
- Z-index layers for proper stacking

Usage:
    from ui.design_system import Spacing, Colors, Shadows, BorderRadius
    
    # Use spacing tokens
    padding = Spacing.MD  # 16px
    
    # Use colors
    primary_color = Colors.LIGHT['primary']
    
    # Use shadows
    card_shadow = Shadows.MD
"""

from typing import Dict


class Spacing:
    """
    Spacing system based on 8px grid.
    
    All spacing values are multiples of 8px for consistent rhythm.
    Use these tokens for margins, padding, and gaps.
    """
    XS = 4   # 0.5 × base (4px)
    SM = 8   # 1 × base (8px)
    MD = 16  # 2 × base (16px)
    LG = 24  # 3 × base (24px)
    XL = 32  # 4 × base (32px)
    XXL = 48 # 6 × base (48px)
    
    # Semantic spacing
    COMPONENT_GAP = SM      # Gap between related components
    SECTION_GAP = LG        # Gap between sections
    PAGE_PADDING = XL       # Page/container padding
    CARD_PADDING = MD       # Card internal padding


class BorderRadius:
    """
    Border radius values for consistent rounded corners.
    
    Use these tokens for buttons, cards, inputs, and other UI elements.
    """
    NONE = 0      # No rounding
    SM = 4        # Subtle rounding (small buttons, badges)
    MD = 8        # Standard rounding (buttons, inputs)
    LG = 12       # Prominent rounding (cards, dialogs)
    XL = 16       # Large rounding (hero cards)
    FULL = 9999   # Pill shape (badges, tags)


class Shadows:
    """
    Shadow definitions for depth and elevation.
    
    Shadows create visual hierarchy and indicate interactive elements.
    Use sparingly for best effect.
    """
    # No shadow
    NONE = "none"
    
    # Small shadow - subtle elevation (buttons, small cards)
    SM = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    
    # Medium shadow - standard elevation (cards, dropdowns)
    MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
    
    # Large shadow - prominent elevation (modals, popovers)
    LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
    
    # Extra large shadow - maximum elevation (dialogs, overlays)
    XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"
    
    # Focus shadow - for keyboard navigation
    FOCUS = "0 0 0 3px rgba(15, 98, 254, 0.3)"


class Colors:
    """
    IBM Carbon Design System color palette.
    
    Provides comprehensive color tokens for both light and dark themes.
    All colors are carefully selected for accessibility (WCAG AA compliance).
    """
    
    # Light Theme Colors (IBM Carbon-inspired)
    LIGHT: Dict[str, str] = {
        # Primary brand colors
        'primary': '#0f62fe',           # IBM Blue 60
        'primary_hover': '#0353e9',     # IBM Blue 70
        'primary_active': '#0043ce',    # IBM Blue 80
        'primary_inverse': '#4589ff',   # IBM Blue 50
        
        # Background colors
        'background': '#ffffff',        # Pure white
        'surface': '#f4f4f4',          # Gray 10
        'surface_hover': '#e8e8e8',    # Gray 20
        'surface_active': '#d0d0d0',   # Gray 30
        
        # Text colors
        'text_primary': '#161616',      # Gray 100
        'text_secondary': '#525252',    # Gray 70
        'text_tertiary': '#8d8d8d',    # Gray 50
        'text_disabled': '#c6c6c6',    # Gray 30
        'text_inverse': '#ffffff',      # White on dark backgrounds
        
        # Semantic colors
        'success': '#24a148',           # Green 50
        'success_bg': '#defbe6',        # Green 10
        'warning': '#f1c21b',           # Yellow 30
        'warning_bg': '#fcf4d6',        # Yellow 10
        'danger': '#da1e28',            # Red 60
        'danger_bg': '#fff1f1',         # Red 10
        'info': '#0043ce',              # Blue 80
        'info_bg': '#edf5ff',           # Blue 10
        
        # Border and divider colors
        'border': '#e0e0e0',            # Gray 20
        'border_subtle': '#f4f4f4',     # Gray 10
        'divider': '#e0e0e0',           # Gray 20
        
        # Interactive colors
        'link': '#0f62fe',              # IBM Blue 60
        'link_visited': '#8e24aa',      # Purple 60
        'focus': '#0f62fe',             # IBM Blue 60
        
        # Component-specific colors
        'input_bg': '#ffffff',
        'input_border': '#8d8d8d',
        'button_secondary_bg': 'transparent',
        'button_secondary_border': '#0f62fe',
    }
    
    # Dark Theme Colors (IBM Carbon-inspired)
    DARK: Dict[str, str] = {
        # Primary brand colors
        'primary': '#4589ff',           # IBM Blue 50
        'primary_hover': '#0353e9',     # IBM Blue 70
        'primary_active': '#0043ce',    # IBM Blue 80
        'primary_inverse': '#0f62fe',   # IBM Blue 60
        
        # Background colors
        'background': '#161616',        # Gray 100
        'surface': '#262626',          # Gray 90
        'surface_hover': '#393939',    # Gray 80
        'surface_active': '#525252',   # Gray 70
        
        # Text colors
        'text_primary': '#f4f4f4',      # Gray 10
        'text_secondary': '#c6c6c6',    # Gray 30
        'text_tertiary': '#8d8d8d',    # Gray 50
        'text_disabled': '#525252',    # Gray 70
        'text_inverse': '#161616',      # Gray 100 on light backgrounds
        
        # Semantic colors
        'success': '#42be65',           # Green 40
        'success_bg': '#044317',        # Green 90
        'warning': '#f1c21b',           # Yellow 30
        'warning_bg': '#3e3c00',        # Yellow 90
        'danger': '#ff5050',            # Red 50
        'danger_bg': '#520408',         # Red 90
        'info': '#4589ff',              # Blue 50
        'info_bg': '#001d6c',           # Blue 90
        
        # Border and divider colors
        'border': '#393939',            # Gray 80
        'border_subtle': '#262626',     # Gray 90
        'divider': '#393939',           # Gray 80
        
        # Interactive colors
        'link': '#4589ff',              # IBM Blue 50
        'link_visited': '#be95ff',      # Purple 40
        'focus': '#4589ff',             # IBM Blue 50
        
        # Component-specific colors
        'input_bg': '#262626',
        'input_border': '#8d8d8d',
        'button_secondary_bg': 'transparent',
        'button_secondary_border': '#4589ff',
    }


class Breakpoints:
    """
    Responsive design breakpoints.
    
    Use these breakpoints for responsive layouts and adaptive UI.
    Based on common device sizes.
    """
    XS = 480   # Extra small devices (phones)
    SM = 768   # Small devices (tablets portrait)
    MD = 1024  # Medium devices (tablets landscape, small laptops)
    LG = 1366  # Large devices (laptops, desktops)
    XL = 1920  # Extra large devices (large desktops)


class ZIndex:
    """
    Z-index layers for proper element stacking.
    
    Use these values to ensure correct layering of UI elements.
    Higher values appear on top of lower values.
    """
    BASE = 0           # Default layer (most content)
    DROPDOWN = 1000    # Dropdowns and popovers
    STICKY = 1100      # Sticky headers/footers
    OVERLAY = 1200     # Overlays and backdrops
    MODAL = 1300       # Modal dialogs
    POPOVER = 1400     # Popovers and tooltips
    TOAST = 1500       # Toast notifications
    TOOLTIP = 1600     # Tooltips (highest priority)


class Typography:
    """
    Typography scale and font families.
    
    Defines the type scale and font stacks for the design system.
    """
    # Font families
    FONT_FAMILY_SANS = "'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    FONT_FAMILY_MONO = "'IBM Plex Mono', 'Courier New', Courier, monospace"
    
    # Font weights
    WEIGHT_LIGHT = 300
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700
    
    # Line heights
    LINE_HEIGHT_TIGHT = 1.2
    LINE_HEIGHT_NORMAL = 1.5
    LINE_HEIGHT_RELAXED = 1.75


class Animation:
    """
    Animation timing and easing functions.
    
    Use these values for consistent motion design.
    """
    # Duration (in milliseconds)
    DURATION_FAST = 150
    DURATION_NORMAL = 250
    DURATION_SLOW = 350
    
    # Easing functions (CSS timing functions)
    EASE_IN = "cubic-bezier(0.4, 0, 1, 1)"
    EASE_OUT = "cubic-bezier(0, 0, 0.2, 1)"
    EASE_IN_OUT = "cubic-bezier(0.4, 0, 0.2, 1)"
    EASE_STANDARD = "cubic-bezier(0.4, 0, 0.6, 1)"


# Export all design tokens
__all__ = [
    'Spacing',
    'BorderRadius',
    'Shadows',
    'Colors',
    'Breakpoints',
    'ZIndex',
    'Typography',
    'Animation',
]

# Made with Bob
