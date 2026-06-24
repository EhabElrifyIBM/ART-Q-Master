"""
Configuration Validator for ART Q Master V2
===========================================

This module provides comprehensive validation for configuration objects.
Validates all configuration sections with clear, user-friendly error messages.

Features:
- Field-level validation with specific error messages
- Path existence validation
- Range validation for numeric fields
- Format validation for time strings
- Comprehensive error reporting

Version: 2.0.0
"""

import os
from pathlib import Path
from typing import List, Optional
from .schema import (
    Configuration,
    CredentialsConfig,
    FilePathsConfig,
    AutomationConfig,
    UIConfig,
    AccessibilityConfig,
    DeveloperConfig,
)


class ValidationError(Exception):
    """
    Configuration validation error
    
    Attributes:
        field: The configuration field that failed validation
        message: Human-readable error message
    """
    
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
    
    def __repr__(self):
        return f"ValidationError(field='{self.field}', message='{self.message}')"


class ConfigValidator:
    """
    Validates configuration objects
    
    Provides static methods for validating each configuration section
    and a comprehensive validate() method for the entire configuration.
    """
    
    @staticmethod
    def validate_credentials(creds: CredentialsConfig) -> List[ValidationError]:
        """
        Validate credentials section
        
        Args:
            creds: Credentials configuration object
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Username validation
        if not creds.username or not creds.username.strip():
            errors.append(ValidationError(
                "credentials.username",
                "Username is required and cannot be empty"
            ))
        elif len(creds.username.strip()) < 3:
            errors.append(ValidationError(
                "credentials.username",
                "Username must be at least 3 characters long"
            ))
        
        # Password validation
        if not creds.password or not creds.password.strip():
            errors.append(ValidationError(
                "credentials.password",
                "Password is required and cannot be empty"
            ))
        elif len(creds.password) < 4:
            errors.append(ValidationError(
                "credentials.password",
                "Password must be at least 4 characters long"
            ))
        
        # User ID validation
        if not creds.user_id or not creds.user_id.strip():
            errors.append(ValidationError(
                "credentials.user_id",
                "User ID is required and cannot be empty"
            ))
        
        # Place ID validation
        if not creds.place_id or not creds.place_id.strip():
            errors.append(ValidationError(
                "credentials.place_id",
                "Place ID is required and cannot be empty"
            ))
        
        return errors
    
    @staticmethod
    def validate_file_paths(paths: FilePathsConfig) -> List[ValidationError]:
        """
        Validate file paths section
        
        Args:
            paths: File paths configuration object
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Excel base path validation
        if not paths.excel_base_path or not paths.excel_base_path.strip():
            errors.append(ValidationError(
                "file_paths.excel_base_path",
                "Excel base path is required and cannot be empty"
            ))
        else:
            excel_path = Path(paths.excel_base_path)
            if not excel_path.exists():
                errors.append(ValidationError(
                    "file_paths.excel_base_path",
                    f"Excel base path does not exist: {paths.excel_base_path}"
                ))
            elif not excel_path.is_dir():
                errors.append(ValidationError(
                    "file_paths.excel_base_path",
                    f"Excel base path is not a directory: {paths.excel_base_path}"
                ))
        
        # Cache directory validation
        if not paths.cache_directory or not paths.cache_directory.strip():
            errors.append(ValidationError(
                "file_paths.cache_directory",
                "Cache directory is required and cannot be empty"
            ))
        else:
            cache_path = Path(paths.cache_directory)
            cache_parent = cache_path.parent
            
            # Check if parent directory exists (cache dir will be created if needed)
            if not cache_parent.exists():
                errors.append(ValidationError(
                    "file_paths.cache_directory",
                    f"Cache directory parent does not exist: {cache_parent}"
                ))
        
        return errors
    
    @staticmethod
    def validate_automation(auto: AutomationConfig) -> List[ValidationError]:
        """
        Validate automation section
        
        Args:
            auto: Automation configuration object
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Agent name validation
        if not auto.agent_name or not auto.agent_name.strip():
            errors.append(ValidationError(
                "automation.agent_name",
                "Agent name is required and cannot be empty"
            ))
        elif len(auto.agent_name.strip()) < 2:
            errors.append(ValidationError(
                "automation.agent_name",
                "Agent name must be at least 2 characters long"
            ))
        
        # Sheet name validation
        if not auto.sheet_name or not auto.sheet_name.strip():
            errors.append(ValidationError(
                "automation.sheet_name",
                "Sheet name is required and cannot be empty"
            ))
        
        # Refresh interval validation
        if not isinstance(auto.refresh_interval, int):
            errors.append(ValidationError(
                "automation.refresh_interval",
                f"Refresh interval must be an integer, got {type(auto.refresh_interval).__name__}"
            ))
        elif auto.refresh_interval < 1:
            errors.append(ValidationError(
                "automation.refresh_interval",
                f"Refresh interval must be at least 1, got {auto.refresh_interval}"
            ))
        elif auto.refresh_interval > 100:
            errors.append(ValidationError(
                "automation.refresh_interval",
                f"Refresh interval must be at most 100, got {auto.refresh_interval}"
            ))
        
        # Start time validation (optional)
        if auto.start_time is not None:
            if not ConfigValidator._is_valid_time(auto.start_time):
                errors.append(ValidationError(
                    "automation.start_time",
                    f"Start time must be in HH:MM format, got '{auto.start_time}'"
                ))
        
        # End time validation (optional)
        if auto.end_time is not None:
            if not ConfigValidator._is_valid_time(auto.end_time):
                errors.append(ValidationError(
                    "automation.end_time",
                    f"End time must be in HH:MM format, got '{auto.end_time}'"
                ))
        
        return errors
    
    @staticmethod
    def validate_ui(ui: UIConfig) -> List[ValidationError]:
        """
        Validate UI section
        
        Args:
            ui: UI configuration object
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Font size validation
        if not isinstance(ui.font_size, int):
            errors.append(ValidationError(
                "ui.font_size",
                f"Font size must be an integer, got {type(ui.font_size).__name__}"
            ))
        elif ui.font_size < 10:
            errors.append(ValidationError(
                "ui.font_size",
                f"Font size must be at least 10, got {ui.font_size}"
            ))
        elif ui.font_size > 30:
            errors.append(ValidationError(
                "ui.font_size",
                f"Font size must be at most 30, got {ui.font_size}"
            ))
        
        # Window geometry validation (optional)
        if ui.window_geometry is not None:
            if not isinstance(ui.window_geometry, dict):
                errors.append(ValidationError(
                    "ui.window_geometry",
                    f"Window geometry must be a dictionary, got {type(ui.window_geometry).__name__}"
                ))
            else:
                required_keys = ['x', 'y', 'width', 'height']
                missing_keys = [k for k in required_keys if k not in ui.window_geometry]
                if missing_keys:
                    errors.append(ValidationError(
                        "ui.window_geometry",
                        f"Window geometry missing required keys: {', '.join(missing_keys)}"
                    ))
        
        return errors
    
    @staticmethod
    def validate_accessibility(access: AccessibilityConfig) -> List[ValidationError]:
        """
        Validate accessibility section
        
        Args:
            access: Accessibility configuration object
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # All accessibility fields are boolean, so just validate types
        bool_fields = [
            ('high_contrast', access.high_contrast),
            ('screen_reader', access.screen_reader),
            ('keyboard_navigation', access.keyboard_navigation),
            ('reduce_motion', access.reduce_motion),
            ('focus_indicators', access.focus_indicators),
        ]
        
        for field_name, field_value in bool_fields:
            if not isinstance(field_value, bool):
                errors.append(ValidationError(
                    f"accessibility.{field_name}",
                    f"Must be a boolean (true/false), got {type(field_value).__name__}"
                ))
        
        return errors
    
    @staticmethod
    def validate_developer(dev: DeveloperConfig) -> List[ValidationError]:
        """
        Validate developer section
        
        Args:
            dev: Developer configuration object
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Boolean fields validation
        bool_fields = [
            ('debug_mode', dev.debug_mode),
            ('enable_profiling', dev.enable_profiling),
            ('show_debug_info', dev.show_debug_info),
            ('verbose_logging', dev.verbose_logging),
        ]
        
        for field_name, field_value in bool_fields:
            if not isinstance(field_value, bool):
                errors.append(ValidationError(
                    f"developer.{field_name}",
                    f"Must be a boolean (true/false), got {type(field_value).__name__}"
                ))
        
        # Log level validation
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if not isinstance(dev.log_level, str):
            errors.append(ValidationError(
                "developer.log_level",
                f"Log level must be a string, got {type(dev.log_level).__name__}"
            ))
        elif dev.log_level.upper() not in valid_log_levels:
            errors.append(ValidationError(
                "developer.log_level",
                f"Log level must be one of {', '.join(valid_log_levels)}, got '{dev.log_level}'"
            ))
        
        return errors
    
    @staticmethod
    def validate(config: Configuration) -> List[ValidationError]:
        """
        Validate entire configuration
        
        Args:
            config: Complete configuration object
            
        Returns:
            List of all validation errors (empty if valid)
        """
        errors = []
        
        # Validate each section
        errors.extend(ConfigValidator.validate_credentials(config.credentials))
        errors.extend(ConfigValidator.validate_file_paths(config.file_paths))
        errors.extend(ConfigValidator.validate_automation(config.automation))
        errors.extend(ConfigValidator.validate_ui(config.ui))
        errors.extend(ConfigValidator.validate_accessibility(config.accessibility))
        errors.extend(ConfigValidator.validate_developer(config.developer))
        
        return errors
    
    @staticmethod
    def validate_and_raise(config: Configuration) -> None:
        """
        Validate configuration and raise exception if invalid
        
        Args:
            config: Complete configuration object
            
        Raises:
            ValidationError: If configuration is invalid (first error encountered)
        """
        errors = ConfigValidator.validate(config)
        if errors:
            raise errors[0]
    
    @staticmethod
    def _is_valid_time(time_str: str) -> bool:
        """
        Check if time string is in HH:MM format
        
        Args:
            time_str: Time string to validate
            
        Returns:
            True if valid HH:MM format, False otherwise
        """
        try:
            if not isinstance(time_str, str):
                return False
            if ':' not in time_str:
                return False
            
            parts = time_str.split(':')
            if len(parts) != 2:
                return False
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            return 0 <= hour < 24 and 0 <= minute < 60
        except (ValueError, AttributeError):
            return False


def get_validation_summary(errors: List[ValidationError]) -> str:
    """
    Get a formatted summary of validation errors
    
    Args:
        errors: List of validation errors
        
    Returns:
        Formatted string with all errors
    """
    if not errors:
        return "Configuration is valid ✓"
    
    summary = f"Configuration has {len(errors)} error(s):\n\n"
    for i, error in enumerate(errors, 1):
        summary += f"{i}. {error.field}:\n   {error.message}\n\n"
    
    return summary.strip()

# Made with Bob
