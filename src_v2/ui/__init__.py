"""
UI Package - Modern UI Components and Systems
==============================================

This package provides the modern UI infrastructure for ART Q Master V2.

Key Modules:
- design_system: Design tokens (colors, spacing, typography, shadows)
- typography: Typography system with font presets
- typography_mixin: Mixin for easy typography integration
- theme: Theme management (Light/Dark/Auto)
- theme_manager: V2ThemeManager for color management
- settings: Settings management with V2SettingsBus
- services: Singleton services (V2SettingsBus)
- keyboard_shortcuts: Keyboard shortcut management
- accessibility_helper: Accessibility utilities
- feedback_guide: User feedback mechanisms guide

Component Libraries:
- components/: Legacy components (being phased out)
- components_v2/: Modern component library (buttons, inputs, dialogs, etc.)
"""

# Export commonly used classes for convenience
from ui.typography_mixin import V2TypographyMixin
from ui.theme_manager import ThemeManager
from ui.services import get_v2_settings_bus

__all__ = [
    'V2TypographyMixin',
    'ThemeManager',
    'get_v2_settings_bus',
]
