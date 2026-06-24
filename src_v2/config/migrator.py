"""
Configuration Migration System - Phase 7.3
Automatically detects and migrates legacy configuration formats.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from datetime import datetime


class ConfigMigrator:
    """
    Handles migration from legacy configuration formats to V2 schema.
    Supports automatic detection and conversion of old config structures.
    """
    
    @staticmethod
    def detect_version(config_data: Dict[str, Any]) -> str:
        """
        Detect configuration version.
        
        Args:
            config_data: Configuration dictionary
            
        Returns:
            Version string: 'v1', 'v2', or 'unknown'
        """
        # V2 has structured sections
        if all(key in config_data for key in ['credentials', 'file_paths', 'automation', 'ui']):
            return 'v2'
        
        # V1 has flat structure with specific keys
        if 'agent_name' in config_data and 'cache_directory' in config_data:
            # Check if it's the old flat structure
            if 'ui_settings' not in config_data or not isinstance(config_data.get('ui_settings'), dict):
                return 'v1'
        
        return 'unknown'
    
    @staticmethod
    def needs_migration(config_path: str) -> bool:
        """
        Check if configuration file needs migration.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            True if migration needed, False otherwise
        """
        try:
            if not os.path.exists(config_path):
                return False
            
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            version = ConfigMigrator.detect_version(data)
            return version == 'v1' or version == 'unknown'
            
        except Exception:
            return False
    
    @staticmethod
    def migrate_v1_to_v2(v1_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Migrate V1 configuration to V2 format.
        
        Args:
            v1_config: V1 configuration dictionary
            
        Returns:
            V2 configuration dictionary
        """
        v2_config = {
            'credentials': {
                'username': v1_config.get('username', ''),
                'password': v1_config.get('password', ''),
                'user_id': v1_config.get('user_id', ''),
                'place_id': v1_config.get('place_id', '')
            },
            'file_paths': {
                'excel_base_path': v1_config.get('excel_base_path', ''),
                'cache_directory': v1_config.get('cache_directory', './cache')
            },
            'automation': {
                'agent_name': v1_config.get('agent_name', ''),
                'sheet_name': v1_config.get('sheet_name', 'Sheet1'),
                'refresh_interval': v1_config.get('refresh_interval', 5),
                'start_time': v1_config.get('start_time'),
                'end_time': v1_config.get('end_time')
            },
            'ui': {
                'theme': 'auto',
                'font_size': v1_config.get('font_size', 20),
                'window_geometry': v1_config.get('window_geometry')
            },
            'accessibility': {
                'high_contrast': v1_config.get('high_contrast', False),
                'screen_reader': False,
                'keyboard_navigation': True,
                'reduce_motion': False,
                'focus_indicators': True
            },
            'developer': {
                'debug_mode': v1_config.get('debug_mode', False),
                'log_level': v1_config.get('log_level', 'INFO'),
                'enable_profiling': False,
                'show_debug_info': False,
                'verbose_logging': False
            }
        }
        
        # Handle old ui_settings if present
        if 'ui_settings' in v1_config and isinstance(v1_config['ui_settings'], dict):
            ui_settings = v1_config['ui_settings']
            v2_config['ui']['theme'] = ui_settings.get('theme', 'auto')
            v2_config['ui']['font_size'] = ui_settings.get('font_size', 20)
            v2_config['accessibility']['high_contrast'] = ui_settings.get('high_contrast', False)
        
        return v2_config
    
    @staticmethod
    def migrate_file(config_path: str, backup: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Migrate configuration file in place.
        
        Args:
            config_path: Path to configuration file
            backup: Whether to create backup before migration
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            path = Path(config_path)
            
            if not path.exists():
                return False, f"Configuration file not found: {config_path}"
            
            # Load current config
            with open(path, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
            
            # Detect version
            version = ConfigMigrator.detect_version(old_config)
            
            if version == 'v2':
                return True, "Configuration is already V2 format"
            
            if version == 'unknown':
                return False, "Unknown configuration format, cannot migrate"
            
            # Create backup if requested
            if backup:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = path.with_suffix(f'.v1_backup_{timestamp}.json')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(old_config, f, indent=2)
            
            # Migrate
            new_config = ConfigMigrator.migrate_v1_to_v2(old_config)
            
            # Save migrated config
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=2)
            
            return True, "Migration successful"
            
        except Exception as e:
            return False, f"Migration failed: {str(e)}"
    
    @staticmethod
    def create_migration_report(old_config: Dict[str, Any], 
                               new_config: Dict[str, Any]) -> str:
        """
        Create a human-readable migration report.
        
        Args:
            old_config: Original configuration
            new_config: Migrated configuration
            
        Returns:
            Formatted migration report
        """
        report = ["Configuration Migration Report", "=" * 50, ""]
        
        # Version info
        old_version = ConfigMigrator.detect_version(old_config)
        new_version = ConfigMigrator.detect_version(new_config)
        report.append(f"Migrated from: {old_version}")
        report.append(f"Migrated to: {new_version}")
        report.append("")
        
        # Changes summary
        report.append("Changes:")
        report.append("-" * 50)
        
        # Credentials section
        if 'credentials' in new_config:
            report.append("✓ Credentials section created")
        
        # File paths section
        if 'file_paths' in new_config:
            report.append("✓ File paths section created")
        
        # Automation section
        if 'automation' in new_config:
            report.append("✓ Automation section created")
        
        # UI section
        if 'ui' in new_config:
            report.append("✓ UI section created")
        
        # Accessibility section
        if 'accessibility' in new_config:
            report.append("✓ Accessibility section created")
        
        # Developer section
        if 'developer' in new_config:
            report.append("✓ Developer section created")
        
        report.append("")
        report.append("Migration completed successfully!")
        
        return "\n".join(report)


def migrate_if_needed(config_path: str = "config.json") -> bool:
    """
    Convenience function to migrate configuration if needed.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        True if migration was performed or not needed, False on error
    """
    if not ConfigMigrator.needs_migration(config_path):
        return True
    
    success, message = ConfigMigrator.migrate_file(config_path)
    if success:
        print(f"✓ Configuration migrated: {message}")
    else:
        print(f"✗ Migration failed: {message}")
    
    return success

# Made with Bob
