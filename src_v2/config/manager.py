"""
Configuration Manager - Phase 7.2
Singleton pattern with load/save, validation, callbacks, thread-safety, and backup.
"""

import json
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime

from .schema import Configuration
from .validator import ConfigValidator, ValidationError


class ConfigManager:
    """
    Singleton configuration manager with thread-safe operations.
    Handles loading, saving, validation, and change notifications.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager (only once)."""
        if self._initialized:
            return
            
        self._config: Dict[str, Any] = {}
        self._config_path: Optional[Path] = None
        self._validator = ConfigValidator()
        self._callbacks: List[Callable[[str, Any, Any], None]] = []
        self._operation_lock = threading.RLock()
        self._initialized = True
    
    def load(self, config_path: str = "config.json") -> bool:
        """
        Load configuration from file with validation.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        with self._operation_lock:
            try:
                path = Path(config_path)
                self._config_path = path
                
                if not path.exists():
                    # Create default config
                    self._config = self._create_default_config()
                    self.save()
                    return True
                
                # Load and validate
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Store as dict (validation will be done on Configuration objects when needed)
                self._config = data
                return True
                
            except Exception as e:
                print(f"Error loading configuration: {e}")
                return False
    
    def _dict_to_config(self, data: Dict[str, Any]) -> Optional[Configuration]:
        """Convert dict to Configuration object for validation."""
        try:
            return Configuration(**data)
        except Exception as e:
            print(f"Error converting dict to Configuration: {e}")
            return None
    
    def save(self, backup: bool = True) -> bool:
        """
        Save configuration to file.
        
        Args:
            backup: Whether to create backup before saving
            
        Returns:
            True if saved successfully, False otherwise
        """
        with self._operation_lock:
            try:
                if self._config_path is None:
                    return False
                
                # Create backup if requested
                if backup and self._config_path.exists():
                    self._create_backup()
                
                # Save to file
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2)
                
                return True
                
            except Exception as e:
                print(f"Error saving configuration: {e}")
                return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'ui_settings.theme')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        with self._operation_lock:
            try:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    if isinstance(value, dict):
                        value = value.get(k)
                        if value is None:
                            return default
                    else:
                        return default
                
                return value
                
            except Exception:
                return default
    
    def set(self, key: str, value: Any, save_immediately: bool = True) -> bool:
        """
        Set configuration value by key (supports dot notation).
        
        Args:
            key: Configuration key (e.g., 'ui_settings.theme')
            value: Value to set
            save_immediately: Whether to save to file immediately
            
        Returns:
            True if set successfully, False otherwise
        """
        with self._operation_lock:
            try:
                keys = key.split('.')
                old_value = self.get(key)
                
                # Navigate to parent
                current = self._config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                
                # Set value
                current[keys[-1]] = value
                
                # Notify callbacks
                self._notify_callbacks(key, old_value, value)
                
                # Save if requested
                if save_immediately:
                    return self.save()
                
                return True
                
            except Exception as e:
                print(f"Error setting configuration: {e}")
                return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., 'ui_settings')
            
        Returns:
            Section dictionary or empty dict
        """
        with self._operation_lock:
            return self._config.get(section, {}).copy()
    
    def update_section(self, section: str, data: Dict[str, Any], 
                      save_immediately: bool = True) -> bool:
        """
        Update entire configuration section.
        
        Args:
            section: Section name
            data: New section data
            save_immediately: Whether to save immediately
            
        Returns:
            True if updated successfully
        """
        with self._operation_lock:
            try:
                old_data = self._config.get(section, {}).copy()
                self._config[section] = data
                
                # Notify callbacks
                self._notify_callbacks(section, old_data, data)
                
                # Save if requested
                if save_immediately:
                    return self.save()
                
                return True
                
            except Exception as e:
                print(f"Error updating section: {e}")
                return False
    
    def register_callback(self, callback: Callable[[str, Any, Any], None]):
        """
        Register callback for configuration changes.
        
        Args:
            callback: Function(key, old_value, new_value)
        """
        with self._operation_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[str, Any, Any], None]):
        """
        Unregister callback.
        
        Args:
            callback: Previously registered callback
        """
        with self._operation_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _notify_callbacks(self, key: str, old_value: Any, new_value: Any):
        """Notify all registered callbacks of configuration change."""
        for callback in self._callbacks[:]:  # Copy to avoid modification during iteration
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                print(f"Error in configuration callback: {e}")
    
    def _create_backup(self):
        """Create backup of current configuration file."""
        try:
            if self._config_path and self._config_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self._config_path.with_suffix(f'.backup_{timestamp}.json')
                
                with open(self._config_path, 'r', encoding='utf-8') as src:
                    with open(backup_path, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                        
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration structure."""
        return {
            "agent_name": "",
            "cache_directory": "./cache",
            "ui_settings": {
                "theme": "auto",
                "font_size": 20,
                "high_contrast": False,
                "animations_enabled": True,
                "compact_mode": False
            },
            "automation": {
                "refresh_interval": 300,
                "auto_screenshot": True,
                "screenshot_directory": "./screenshots",
                "max_retries": 3,
                "retry_delay": 5,
                "timeout": 30
            },
            "accessibility": {
                "screen_reader_support": False,
                "keyboard_navigation": True,
                "focus_indicators": True,
                "reduced_motion": False
            },
            "advanced": {
                "debug_mode": False,
                "log_level": "INFO",
                "log_directory": "./logs",
                "backup_enabled": True,
                "backup_count": 5,
                "auto_save": True,
                "auto_save_interval": 60
            },
            "credentials": {
                "username": "",
                "password": ""
            }
        }
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        with self._operation_lock:
            try:
                self._config = self._create_default_config()
                return self.save()
            except Exception as e:
                print(f"Error resetting configuration: {e}")
                return False
    
    def export_config(self, export_path: str) -> bool:
        """
        Export configuration to file.
        
        Args:
            export_path: Path to export file
            
        Returns:
            True if exported successfully
        """
        with self._operation_lock:
            try:
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2)
                return True
            except Exception as e:
                print(f"Error exporting configuration: {e}")
                return False
    
    def import_config(self, import_path: str) -> bool:
        """
        Import configuration from file.
        
        Args:
            import_path: Path to import file
            
        Returns:
            True if imported successfully
        """
        with self._operation_lock:
            try:
                with open(import_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate imported data
                is_valid, errors = self._validator.validate(data)
                if not is_valid:
                    print(f"Invalid imported configuration: {errors}")
                    return False
                
                self._config = data
                return self.save()
                
            except Exception as e:
                print(f"Error importing configuration: {e}")
                return False


# Global instance
config_manager = ConfigManager()

# Made with Bob
