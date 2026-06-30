"""
Configuration System for ART Q Master V2
========================================

This module provides a unified configuration system with:
- Type-safe configuration schema using dataclasses
- Comprehensive validation with clear error messages
- Migration from legacy configuration formats
- Backup and restore functionality
- Support for encrypted credential storage (Phase 7.6)

Usage Example:
    from src_v2.config import Configuration, ConfigValidator, ValidationError
    
    # Load configuration from dictionary
    config_dict = {...}
    config = Configuration.from_dict(config_dict)
    
    # Validate configuration
    errors = ConfigValidator.validate(config)
    if errors:
        for error in errors:
            print(f"Error: {error}")
    
    # Access configuration values
    username = config.credentials.username
    theme = config.ui.theme
    
    # Convert to dictionary
    config_dict = config.to_dict()

Version: 2.0.0
"""

from .schema import (
    Configuration,
    CredentialsConfig,
    FilePathsConfig,
    AutomationConfig,
    UIConfig,
    AccessibilityConfig,
    DeveloperConfig,
    ThemeMode,
    FontPreset,
)

from .validator import (
    ConfigValidator,
    ValidationError,
    get_validation_summary,
)

from .manager import (
    ConfigManager,
    get_config_manager,
)

from .migrator import (
    ConfigMigrator,
    migrate_if_needed,
)

from .backup import (
    ConfigBackup,
    AutoBackup,
)

from .security import (
    ConfigSecurity,
    encrypt_password,
    decrypt_password,
    is_password_encrypted,
)

__version__ = "2.0.0"

__all__ = [
    # Schema classes
    'Configuration',
    'CredentialsConfig',
    'FilePathsConfig',
    'AutomationConfig',
    'UIConfig',
    'AccessibilityConfig',
    'DeveloperConfig',
    
    # Enums
    'ThemeMode',
    'FontPreset',
    
    # Validation
    'ConfigValidator',
    'ValidationError',
    'get_validation_summary',
    
    # Manager (Phase 7.2)
    'ConfigManager',
    'get_config_manager',
    
    # Migration (Phase 7.3)
    'ConfigMigrator',
    'migrate_if_needed',
    
    # Backup (Phase 7.4)
    'ConfigBackup',
    'AutoBackup',
    
    # Security (Phase 7.6)
    'ConfigSecurity',
    'encrypt_password',
    'decrypt_password',
    'is_password_encrypted',
    
    # Version
    '__version__',
]


# Convenience functions for common operations

def create_default_config() -> Configuration:
    """
    Create a configuration object with default values
    
    Note: This will fail validation as required fields are empty.
    Use this as a template and fill in required values.
    
    Returns:
        Configuration object with default values
    """
    return Configuration(
        credentials=CredentialsConfig(
            username="",
            password="",
            user_id="",
            place_id="",
        ),
        file_paths=FilePathsConfig(
            excel_base_path="",
            cache_directory="",
        ),
        automation=AutomationConfig(
            agent_name="",
            sheet_name="",
            refresh_interval=10,
        ),
    )


def validate_config_dict(config_dict: dict) -> tuple[Configuration | None, list[ValidationError]]:
    """
    Validate a configuration dictionary
    
    Args:
        config_dict: Dictionary containing configuration data
        
    Returns:
        Tuple of (Configuration object or None, list of validation errors)
        If validation errors exist, the Configuration object may be None or incomplete.
    """
    try:
        config = Configuration.from_dict(config_dict)
        errors = ConfigValidator.validate(config)
        return config, errors
    except Exception as e:
        # If we can't even create the config object, return a validation error
        error = ValidationError("configuration", str(e))
        return None, [error]


def is_valid_config(config: Configuration) -> bool:
    """
    Check if a configuration is valid
    
    Args:
        config: Configuration object to validate
        
    Returns:
        True if valid, False otherwise
    """
    errors = ConfigValidator.validate(config)
    return len(errors) == 0


# Module-level documentation
# Additional documentation is provided in the module docstring above

"""
Configuration Schema Overview
-----------------------------

The configuration system is organized into the following sections:

1. **Credentials** (CredentialsConfig)
   - username: Dialer username
   - password: Dialer password (will be encrypted in Phase 7.6)
   - user_id: User ID for authentication
   - place_id: Dialer place ID

2. **File Paths** (FilePathsConfig)
   - excel_base_path: Base directory for Excel files
   - cache_directory: Directory for cache files

3. **Automation** (AutomationConfig)
   - agent_name: Agent's full name for signatures
   - sheet_name: Excel sheet name to process
   - refresh_interval: Refresh interval in cases (1-100)
   - start_time: Optional automation start time (HH:MM)
   - end_time: Optional automation end time (HH:MM)

4. **UI** (UIConfig)
   - theme: Theme mode (light, dark, auto)
   - font_size: Font size in pixels (10-30)
   - font_preset: Font size preset (small, medium, large, extra_large)
   - window_geometry: Optional window position/size
   - show_tooltips: Whether to show tooltips
   - animation_enabled: Whether animations are enabled

5. **Accessibility** (AccessibilityConfig)
   - high_contrast: Enable high contrast mode
   - screen_reader: Enable screen reader support
   - keyboard_navigation: Enable enhanced keyboard navigation
   - reduce_motion: Reduce animations and motion
   - focus_indicators: Show enhanced focus indicators

6. **Developer** (DeveloperConfig)
   - debug_mode: Enable debug mode
   - log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - enable_profiling: Enable performance profiling
   - show_debug_info: Show debug information in UI
   - verbose_logging: Enable verbose logging

Validation Rules
---------------

The validator checks:
- Required fields are not empty
- Numeric values are within valid ranges
- File paths exist and are accessible
- Time strings are in HH:MM format
- Boolean fields are actual booleans
- Enum values are valid

All validation errors include:
- The specific field that failed validation
- A clear, user-friendly error message

Migration from Legacy Config
---------------------------

The system supports loading from legacy config.json formats:
- Maps agent_settings → credentials
- Maps crm_settings → automation
- Maps execution_settings → automation
- Maps ui_settings → ui
- Provides sensible defaults for new fields

Example:
    # Legacy format
    legacy_config = {
        "agent_settings": {
            "agent_name": "John Doe",
            "user_id": "Agent_123",
            "password": "pass123",
            "place_id": "Place_456"
        },
        "file_paths": {
            "excel_base_path": "/path/to/excel",
            "cache_directory": "/path/to/cache"
        },
        "crm_settings": {
            "excel_sheet_name": "My Sheet"
        },
        "execution_settings": {
            "refresh_interval": 10
        }
    }
    
    # Load and validate
    config = Configuration.from_dict(legacy_config)
    errors = ConfigValidator.validate(config)
    
    if not errors:
        print("Configuration is valid!")
"""

# Made with Bob
