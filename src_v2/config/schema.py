"""
Configuration Schema for ART Q Master V2
========================================

This module defines the complete configuration schema using Python dataclasses.
All configuration sections are type-safe and validated.

Schema Structure:
- CredentialsConfig: User credentials for CRM/Dialer access
- AutomationConfig: Automation settings for ART Q Control
- UIConfig: UI appearance and behavior settings
- AccessibilityConfig: Accessibility features
- DeveloperConfig: Developer/debug settings
- Configuration: Root configuration object containing all sections

Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class ThemeMode(Enum):
    """Theme mode options"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class FontPreset(Enum):
    """Font size presets"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"


@dataclass
class CredentialsConfig:
    """
    User credentials for CRM/Dialer access
    
    Attributes:
        username: Dialer username (e.g., Agent_Cairo_US_925)
        password: Dialer password (will be encrypted in Phase 7.6)
        user_id: User ID for authentication
        place_id: Dialer place ID (e.g., Place_57080_SIPSwitch_US)
    """
    username: str
    password: str
    user_id: str
    place_id: str
    
    def __post_init__(self):
        """Validate credentials after initialization"""
        if not self.username:
            raise ValueError("Username cannot be empty")
        if not self.password:
            raise ValueError("Password cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.place_id:
            raise ValueError("Place ID cannot be empty")


@dataclass
class FilePathsConfig:
    """
    File system paths configuration
    
    Attributes:
        excel_base_path: Base directory for Excel files
        cache_directory: Directory for cache files
    """
    excel_base_path: str
    cache_directory: str
    
    def __post_init__(self):
        """Validate paths after initialization"""
        if not self.excel_base_path:
            raise ValueError("Excel base path cannot be empty")
        if not self.cache_directory:
            raise ValueError("Cache directory cannot be empty")


@dataclass
class AutomationConfig:
    """
    Automation settings for ART Q Control
    
    Attributes:
        agent_name: Agent's full name for signatures
        sheet_name: Excel sheet name to process
        refresh_interval: Refresh interval in cases (1-100)
        start_time: Optional automation start time (HH:MM format)
        end_time: Optional automation end time (HH:MM format)
    """
    agent_name: str
    sheet_name: str
    refresh_interval: int = 10
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    
    def __post_init__(self):
        """Validate automation settings after initialization"""
        if not self.agent_name:
            raise ValueError("Agent name cannot be empty")
        if not self.sheet_name:
            raise ValueError("Sheet name cannot be empty")
        if not isinstance(self.refresh_interval, int):
            raise ValueError("Refresh interval must be an integer")
        if self.refresh_interval < 1 or self.refresh_interval > 100:
            raise ValueError("Refresh interval must be between 1 and 100")


@dataclass
class UIConfig:
    """
    UI appearance and behavior settings
    
    Attributes:
        theme: Theme mode (light, dark, auto)
        font_size: Font size in pixels (10-30)
        font_preset: Font size preset (small, medium, large, extra_large)
        window_geometry: Optional window position/size dict
        show_tooltips: Whether to show tooltips
        animation_enabled: Whether animations are enabled
    """
    theme: ThemeMode = ThemeMode.AUTO
    font_size: int = 16
    font_preset: FontPreset = FontPreset.MEDIUM
    window_geometry: Optional[Dict[str, int]] = None
    show_tooltips: bool = True
    animation_enabled: bool = True
    
    def __post_init__(self):
        """Validate UI settings after initialization"""
        # Convert string to enum if needed
        if isinstance(self.theme, str):
            self.theme = ThemeMode(self.theme.lower())
        if isinstance(self.font_preset, str):
            self.font_preset = FontPreset(self.font_preset.lower())
        
        if not isinstance(self.font_size, int):
            raise ValueError("Font size must be an integer")
        if self.font_size < 10 or self.font_size > 30:
            raise ValueError("Font size must be between 10 and 30")


@dataclass
class AccessibilityConfig:
    """
    Accessibility features configuration
    
    Attributes:
        high_contrast: Enable high contrast mode
        screen_reader: Enable screen reader support
        keyboard_navigation: Enable enhanced keyboard navigation
        reduce_motion: Reduce animations and motion
        focus_indicators: Show enhanced focus indicators
    """
    high_contrast: bool = False
    screen_reader: bool = False
    keyboard_navigation: bool = True
    reduce_motion: bool = False
    focus_indicators: bool = True


@dataclass
class DeveloperConfig:
    """
    Developer and debug settings
    
    Attributes:
        debug_mode: Enable debug mode
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_profiling: Enable performance profiling
        show_debug_info: Show debug information in UI
        verbose_logging: Enable verbose logging
    """
    debug_mode: bool = False
    log_level: str = "INFO"
    enable_profiling: bool = False
    show_debug_info: bool = False
    verbose_logging: bool = False
    
    def __post_init__(self):
        """Validate developer settings after initialization"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_log_levels)}")
        self.log_level = self.log_level.upper()


@dataclass
class Configuration:
    """
    Complete application configuration
    
    This is the root configuration object that contains all configuration sections.
    All sections are required except ui, accessibility, and developer which have defaults.
    
    Attributes:
        credentials: User credentials for CRM/Dialer access
        file_paths: File system paths
        automation: Automation settings
        ui: UI appearance settings (optional, has defaults)
        accessibility: Accessibility features (optional, has defaults)
        developer: Developer settings (optional, has defaults)
        version: Configuration schema version
    """
    credentials: CredentialsConfig
    file_paths: FilePathsConfig
    automation: AutomationConfig
    ui: UIConfig = field(default_factory=UIConfig)
    accessibility: AccessibilityConfig = field(default_factory=AccessibilityConfig)
    developer: DeveloperConfig = field(default_factory=DeveloperConfig)
    version: str = "2.0.0"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format
        
        Returns:
            Dictionary representation of configuration
        """
        return {
            "credentials": {
                "username": self.credentials.username,
                "password": self.credentials.password,
                "user_id": self.credentials.user_id,
                "place_id": self.credentials.place_id,
            },
            "file_paths": {
                "excel_base_path": self.file_paths.excel_base_path,
                "cache_directory": self.file_paths.cache_directory,
            },
            "automation": {
                "agent_name": self.automation.agent_name,
                "sheet_name": self.automation.sheet_name,
                "refresh_interval": self.automation.refresh_interval,
                "start_time": self.automation.start_time,
                "end_time": self.automation.end_time,
            },
            "ui": {
                "theme": self.ui.theme.value,
                "font_size": self.ui.font_size,
                "font_preset": self.ui.font_preset.value,
                "window_geometry": self.ui.window_geometry,
                "show_tooltips": self.ui.show_tooltips,
                "animation_enabled": self.ui.animation_enabled,
            },
            "accessibility": {
                "high_contrast": self.accessibility.high_contrast,
                "screen_reader": self.accessibility.screen_reader,
                "keyboard_navigation": self.accessibility.keyboard_navigation,
                "reduce_motion": self.accessibility.reduce_motion,
                "focus_indicators": self.accessibility.focus_indicators,
            },
            "developer": {
                "debug_mode": self.developer.debug_mode,
                "log_level": self.developer.log_level,
                "enable_profiling": self.developer.enable_profiling,
                "show_debug_info": self.developer.show_debug_info,
                "verbose_logging": self.developer.verbose_logging,
            },
            "version": self.version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Configuration':
        """
        Create configuration from dictionary
        
        Args:
            data: Dictionary containing configuration data
            
        Returns:
            Configuration object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract required sections
        creds_data = data.get("credentials") or data.get("agent_settings", {})
        paths_data = data.get("file_paths", {})
        auto_data = data.get("automation") or data.get("crm_settings", {})
        exec_data = data.get("execution_settings", {})
        
        # Merge automation data from multiple sources (backward compatibility)
        # Try new format first, then legacy format
        automation_merged = {
            "agent_name": auto_data.get("agent_name") or creds_data.get("agent_name", ""),
            "sheet_name": auto_data.get("sheet_name") or auto_data.get("excel_sheet_name", ""),
            "refresh_interval": auto_data.get("refresh_interval") or exec_data.get("refresh_interval", 10),
            "start_time": auto_data.get("start_time") or exec_data.get("start_time"),
            "end_time": auto_data.get("end_time") or exec_data.get("end_time"),
        }
        
        # Create credentials config
        # Prefer 'username' field (new format), fallback to 'user_id' (legacy format)
        credentials = CredentialsConfig(
            username=creds_data.get("username") or creds_data.get("user_id", ""),
            password=creds_data.get("password", ""),
            user_id=creds_data.get("user_id", ""),
            place_id=creds_data.get("place_id", ""),
        )
        
        # Create file paths config
        file_paths = FilePathsConfig(
            excel_base_path=paths_data.get("excel_base_path", ""),
            cache_directory=paths_data.get("cache_directory", ""),
        )
        
        # Create automation config
        automation = AutomationConfig(**automation_merged)
        
        # Create UI config (with defaults)
        ui_data = data.get("ui") or data.get("ui_settings", {})
        # Theme can be in ui section or top-level theme_mode (legacy)
        theme_value = ui_data.get("theme") or data.get("theme_mode", "auto")
        ui = UIConfig(
            theme=ThemeMode(theme_value.lower()),
            font_size=ui_data.get("font_size", 16),
            font_preset=FontPreset(ui_data.get("font_preset", "medium").lower()),
            window_geometry=ui_data.get("window_geometry"),
            show_tooltips=ui_data.get("show_tooltips", True),
            animation_enabled=ui_data.get("animation_enabled", True),
        )
        
        # Create accessibility config (with defaults)
        access_data = data.get("accessibility", {})
        accessibility = AccessibilityConfig(
            high_contrast=access_data.get("high_contrast", False),
            screen_reader=access_data.get("screen_reader", False),
            keyboard_navigation=access_data.get("keyboard_navigation", True),
            reduce_motion=access_data.get("reduce_motion", False),
            focus_indicators=access_data.get("focus_indicators", True),
        )
        
        # Create developer config (with defaults)
        dev_data = data.get("developer", {})
        developer = DeveloperConfig(
            debug_mode=dev_data.get("debug_mode", False),
            log_level=dev_data.get("log_level", "INFO"),
            enable_profiling=dev_data.get("enable_profiling", False),
            show_debug_info=dev_data.get("show_debug_info", False),
            verbose_logging=dev_data.get("verbose_logging", False),
        )
        
        return cls(
            credentials=credentials,
            file_paths=file_paths,
            automation=automation,
            ui=ui,
            accessibility=accessibility,
            developer=developer,
            version=data.get("version", "2.0.0"),
        )

# Made with Bob
