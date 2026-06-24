"""
Settings Management - Modern Settings System
=============================================

This module provides modern settings management with data classes, validation,
and integration with V2SettingsBus for reactive updates.

Features:
- Settings data classes with type safety
- Validation and defaults
- Integration with V2SettingsBus
- Preparation for future SQLite storage (Phase 7)
- Clean separation of concerns

Usage:
    from ui.settings import SettingsManager, AppearanceSettings
    from ui.services import get_v2_settings_bus
    
    # Get settings manager
    settings = SettingsManager()
    
    # Get appearance settings
    appearance = settings.appearance
    theme = appearance.theme_mode
    font_size = appearance.font_size_preset
    
    # Update settings
    settings.update_appearance(theme_mode='dark', font_size_preset='large')
    
    # Listen for changes via V2SettingsBus
    bus = get_v2_settings_bus()
    bus.theme_changed.connect(on_theme_changed)
"""

import json
import os
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, Callable, List
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal


@dataclass
class AppearanceSettings:
    """
    Appearance settings for the UI.
    
    Attributes:
        theme_mode: Theme mode ('light', 'dark', 'auto')
        font_size_preset: Font size preset ('small', 'normal', 'large', 'xlarge')
        enable_animations: Whether to enable UI animations
        compact_mode: Whether to use compact spacing
    """
    theme_mode: str = "light"
    font_size_preset: str = "normal"
    enable_animations: bool = True
    compact_mode: bool = False
    
    def validate(self) -> None:
        """Validate settings values and apply defaults if invalid."""
        valid_themes = {'light', 'dark', 'auto'}
        if self.theme_mode not in valid_themes:
            self.theme_mode = 'light'
        
        valid_presets = {'small', 'normal', 'large', 'xlarge'}
        if self.font_size_preset not in valid_presets:
            self.font_size_preset = 'normal'
        
        # Ensure booleans
        self.enable_animations = bool(self.enable_animations)
        self.compact_mode = bool(self.compact_mode)


@dataclass
class ToolSettings:
    """
    Settings for automation tools.
    
    Attributes:
        auto_resume: Whether to automatically resume interrupted sessions
        show_progress_monitor: Whether to show progress monitor during automation
        enable_notifications: Whether to show desktop notifications
        cache_enabled: Whether to enable caching for resume functionality
    """
    auto_resume: bool = True
    show_progress_monitor: bool = True
    enable_notifications: bool = True
    cache_enabled: bool = True
    
    def validate(self) -> None:
        """Validate settings values."""
        self.auto_resume = bool(self.auto_resume)
        self.show_progress_monitor = bool(self.show_progress_monitor)
        self.enable_notifications = bool(self.enable_notifications)
        self.cache_enabled = bool(self.cache_enabled)


@dataclass
class AccessibilitySettings:
    """
    Accessibility settings.
    
    Attributes:
        high_contrast: Whether to use high contrast mode
        reduce_motion: Whether to reduce animations
        keyboard_navigation: Whether to enhance keyboard navigation
        screen_reader_mode: Whether to optimize for screen readers
    """
    high_contrast: bool = False
    reduce_motion: bool = False
    keyboard_navigation: bool = True
    screen_reader_mode: bool = False
    
    def validate(self) -> None:
        """Validate settings values."""
        self.high_contrast = bool(self.high_contrast)
        self.reduce_motion = bool(self.reduce_motion)
        self.keyboard_navigation = bool(self.keyboard_navigation)
        self.screen_reader_mode = bool(self.screen_reader_mode)


@dataclass
class DeveloperSettings:
    """
    Developer/debug settings.
    
    Attributes:
        debug_mode: Whether to enable debug mode
        verbose_logging: Whether to enable verbose logging
        show_performance_metrics: Whether to show performance metrics
        enable_experimental_features: Whether to enable experimental features
    """
    debug_mode: bool = False
    verbose_logging: bool = False
    show_performance_metrics: bool = False
    enable_experimental_features: bool = False
    
    def validate(self) -> None:
        """Validate settings values."""
        self.debug_mode = bool(self.debug_mode)
        self.verbose_logging = bool(self.verbose_logging)
        self.show_performance_metrics = bool(self.show_performance_metrics)
        self.enable_experimental_features = bool(self.enable_experimental_features)


class SettingsManager(QObject):
    """
    Modern settings manager with validation and persistence.
    
    Manages all application settings with type safety, validation, and
    integration with V2SettingsBus for reactive updates.
    
    Signals:
        settings_changed: Emitted when any settings change (str: category)
        appearance_changed: Emitted when appearance settings change
        tool_settings_changed: Emitted when tool settings change
        accessibility_changed: Emitted when accessibility settings change
    
    Attributes:
        appearance: Appearance settings
        tools: Tool settings
        accessibility: Accessibility settings
        developer: Developer settings
    """
    
    # Signals
    settings_changed = pyqtSignal(str)  # Emits category name
    appearance_changed = pyqtSignal()
    tool_settings_changed = pyqtSignal()
    accessibility_changed = pyqtSignal()
    developer_changed = pyqtSignal()
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize settings manager.
        
        Args:
            config_path: Path to settings file (default: settings.json in current dir)
        """
        super().__init__()
        
        # Set config path
        if config_path is None:
            config_path = os.path.join(os.getcwd(), 'settings.json')
        self.config_path = config_path
        
        # Initialize settings with defaults
        self.appearance = AppearanceSettings()
        self.tools = ToolSettings()
        self.accessibility = AccessibilitySettings()
        self.developer = DeveloperSettings()
        
        # Load settings from file
        self.load()
        
        # Validate all settings
        self._validate_all()
    
    def load(self) -> bool:
        """
        Load settings from file.
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_path):
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load each category
            if 'appearance' in data:
                self.appearance = AppearanceSettings(**data['appearance'])
            
            if 'tools' in data:
                self.tools = ToolSettings(**data['tools'])
            
            if 'accessibility' in data:
                self.accessibility = AccessibilitySettings(**data['accessibility'])
            
            if 'developer' in data:
                self.developer = DeveloperSettings(**data['developer'])
            
            return True
        
        except Exception as e:
            print(f"[WARNING] Failed to load settings: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save settings to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Validate before saving
            self._validate_all()
            
            # Convert to dictionary
            data = {
                'appearance': asdict(self.appearance),
                'tools': asdict(self.tools),
                'accessibility': asdict(self.accessibility),
                'developer': asdict(self.developer),
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path) or '.', exist_ok=True)
            
            # Write to file
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to save settings: {e}")
            return False
    
    def _validate_all(self) -> None:
        """Validate all settings categories."""
        self.appearance.validate()
        self.tools.validate()
        self.accessibility.validate()
        self.developer.validate()
    
    def update_appearance(self, **kwargs) -> None:
        """
        Update appearance settings.
        
        Args:
            **kwargs: Appearance settings to update (theme_mode, font_size_preset, etc.)
        
        Example:
            >>> settings.update_appearance(theme_mode='dark', font_size_preset='large')
        """
        for key, value in kwargs.items():
            if hasattr(self.appearance, key):
                setattr(self.appearance, key, value)
        
        self.appearance.validate()
        self.save()
        self.appearance_changed.emit()
        self.settings_changed.emit('appearance')
    
    def update_tools(self, **kwargs) -> None:
        """
        Update tool settings.
        
        Args:
            **kwargs: Tool settings to update
        """
        for key, value in kwargs.items():
            if hasattr(self.tools, key):
                setattr(self.tools, key, value)
        
        self.tools.validate()
        self.save()
        self.tool_settings_changed.emit()
        self.settings_changed.emit('tools')
    
    def update_accessibility(self, **kwargs) -> None:
        """
        Update accessibility settings.
        
        Args:
            **kwargs: Accessibility settings to update
        """
        for key, value in kwargs.items():
            if hasattr(self.accessibility, key):
                setattr(self.accessibility, key, value)
        
        self.accessibility.validate()
        self.save()
        self.accessibility_changed.emit()
        self.settings_changed.emit('accessibility')
    
    def update_developer(self, **kwargs) -> None:
        """
        Update developer settings.
        
        Args:
            **kwargs: Developer settings to update
        """
        for key, value in kwargs.items():
            if hasattr(self.developer, key):
                setattr(self.developer, key, value)
        
        self.developer.validate()
        self.save()
        self.developer_changed.emit()
        self.settings_changed.emit('developer')
    
    def reset_to_defaults(self, category: Optional[str] = None) -> None:
        """
        Reset settings to defaults.
        
        Args:
            category: Category to reset ('appearance', 'tools', 'accessibility', 'developer')
                     If None, resets all categories
        """
        if category is None or category == 'appearance':
            self.appearance = AppearanceSettings()
            self.appearance_changed.emit()
        
        if category is None or category == 'tools':
            self.tools = ToolSettings()
            self.tool_settings_changed.emit()
        
        if category is None or category == 'accessibility':
            self.accessibility = AccessibilitySettings()
            self.accessibility_changed.emit()
        
        if category is None or category == 'developer':
            self.developer = DeveloperSettings()
            self.developer_changed.emit()
        
        self.save()
        self.settings_changed.emit(category or 'all')
    
    def get_all_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all settings as a dictionary.
        
        Returns:
            Dict[str, Dict[str, Any]]: All settings organized by category
        """
        return {
            'appearance': asdict(self.appearance),
            'tools': asdict(self.tools),
            'accessibility': asdict(self.accessibility),
            'developer': asdict(self.developer),
        }
    
    def export_settings(self, path: str) -> bool:
        """
        Export settings to a file.
        
        Args:
            path: Path to export file
        
        Returns:
            bool: True if exported successfully
        """
        try:
            data = self.get_all_settings()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to export settings: {e}")
            return False
    
    def import_settings(self, path: str) -> bool:
        """
        Import settings from a file.
        
        Args:
            path: Path to import file
        
        Returns:
            bool: True if imported successfully
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update each category
            if 'appearance' in data:
                self.appearance = AppearanceSettings(**data['appearance'])
                self.appearance_changed.emit()
            
            if 'tools' in data:
                self.tools = ToolSettings(**data['tools'])
                self.tool_settings_changed.emit()
            
            if 'accessibility' in data:
                self.accessibility = AccessibilitySettings(**data['accessibility'])
                self.accessibility_changed.emit()
            
            if 'developer' in data:
                self.developer = DeveloperSettings(**data['developer'])
                self.developer_changed.emit()
            
            self._validate_all()
            self.save()
            self.settings_changed.emit('all')
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to import settings: {e}")
            return False
    
    def __repr__(self) -> str:
        """String representation of settings manager."""
        return f"SettingsManager(config_path='{self.config_path}')"


# Singleton instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """
    Get the singleton settings manager instance.
    
    Returns:
        SettingsManager: Global settings manager instance
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def integrate_with_v2_settings_bus(settings_manager: SettingsManager) -> None:
    """
    Integrate SettingsManager with V2SettingsBus for reactive updates.
    
    This function connects the settings manager to the V2SettingsBus so that
    changes to appearance settings automatically propagate to all UI components.
    
    Args:
        settings_manager: SettingsManager instance to integrate
    
    Example:
        >>> from ui.settings import get_settings_manager, integrate_with_v2_settings_bus
        >>> from ui.services import get_v2_settings_bus
        >>> 
        >>> settings = get_settings_manager()
        >>> integrate_with_v2_settings_bus(settings)
        >>> 
        >>> # Now changes to settings will automatically update V2SettingsBus
        >>> settings.update_appearance(theme_mode='dark')
    """
    try:
        from ui.services import get_v2_settings_bus
        from ui.typography import FontSizePreset
        
        bus = get_v2_settings_bus()
        
        # Connect appearance changes to bus
        def on_appearance_changed():
            # Update theme
            bus.set_theme(settings_manager.appearance.theme_mode)
            
            # Update font size (convert preset to pixel size)
            preset = FontSizePreset.from_string(settings_manager.appearance.font_size_preset)
            base_size = 16  # Base size from typography system
            pixel_size = int(base_size * preset.get_multiplier())
            bus.set_font_size(pixel_size)
        
        settings_manager.appearance_changed.connect(on_appearance_changed)
        
        # Initialize bus with current settings
        on_appearance_changed()
    
    except Exception as e:
        print(f"[WARNING] Failed to integrate with V2SettingsBus: {e}")


# Export public API
__all__ = [
    'AppearanceSettings',
    'ToolSettings',
    'AccessibilitySettings',
    'DeveloperSettings',
    'SettingsManager',
    'get_settings_manager',
    'integrate_with_v2_settings_bus',
]

# Made with Bob
