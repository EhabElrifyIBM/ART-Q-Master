"""
Configuration Backup System - Phase 7.4
Automatic and manual backup/restore functionality for configurations.
"""

import json
import os
import shutil
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime


class ConfigBackup:
    """
    Manages configuration backups with automatic rotation and restore capabilities.
    """
    
    def __init__(self, config_path: str = "config.json", max_backups: int = 5):
        """
        Initialize backup manager.
        
        Args:
            config_path: Path to configuration file
            max_backups: Maximum number of backups to keep
        """
        self.config_path = Path(config_path)
        self.max_backups = max_backups
        self.backup_dir = self.config_path.parent / ".config_backups"
    
    def create_backup(self, label: Optional[str] = None) -> Tuple[bool, str]:
        """
        Create a backup of the current configuration.
        
        Args:
            label: Optional label for the backup (e.g., 'before_update')
            
        Returns:
            Tuple of (success, backup_path or error_message)
        """
        try:
            if not self.config_path.exists():
                return False, f"Configuration file not found: {self.config_path}"
            
            # Create backup directory if it doesn't exist
            self.backup_dir.mkdir(exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if label:
                backup_name = f"config_backup_{label}_{timestamp}.json"
            else:
                backup_name = f"config_backup_{timestamp}.json"
            
            backup_path = self.backup_dir / backup_name
            
            # Copy configuration file
            shutil.copy2(self.config_path, backup_path)
            
            # Rotate old backups
            self._rotate_backups()
            
            return True, str(backup_path)
            
        except Exception as e:
            return False, f"Backup failed: {str(e)}"
    
    def list_backups(self) -> List[Tuple[str, datetime, int]]:
        """
        List all available backups.
        
        Returns:
            List of tuples (filename, timestamp, size_bytes)
        """
        backups = []
        
        try:
            if not self.backup_dir.exists():
                return backups
            
            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                stat = backup_file.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                size = stat.st_size
                backups.append((backup_file.name, mtime, size))
            
            # Sort by timestamp (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
        except Exception as e:
            print(f"Error listing backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_name: str, 
                      create_backup_before: bool = True) -> Tuple[bool, str]:
        """
        Restore configuration from a backup.
        
        Args:
            backup_name: Name of backup file to restore
            create_backup_before: Whether to backup current config first
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return False, f"Backup not found: {backup_name}"
            
            # Validate backup file
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Just validate it's valid JSON
            except json.JSONDecodeError:
                return False, f"Backup file is corrupted: {backup_name}"
            
            # Create backup of current config if requested
            if create_backup_before and self.config_path.exists():
                success, result = self.create_backup(label="before_restore")
                if not success:
                    return False, f"Failed to backup current config: {result}"
            
            # Restore backup
            shutil.copy2(backup_path, self.config_path)
            
            return True, f"Configuration restored from {backup_name}"
            
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
    
    def delete_backup(self, backup_name: str) -> Tuple[bool, str]:
        """
        Delete a specific backup.
        
        Args:
            backup_name: Name of backup file to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return False, f"Backup not found: {backup_name}"
            
            backup_path.unlink()
            return True, f"Backup deleted: {backup_name}"
            
        except Exception as e:
            return False, f"Delete failed: {str(e)}"
    
    def _rotate_backups(self):
        """Remove old backups if exceeding max_backups limit."""
        try:
            backups = self.list_backups()
            
            if len(backups) > self.max_backups:
                # Delete oldest backups
                for backup_name, _, _ in backups[self.max_backups:]:
                    backup_path = self.backup_dir / backup_name
                    if backup_path.exists():
                        backup_path.unlink()
                        
        except Exception as e:
            print(f"Error rotating backups: {e}")
    
    def get_backup_info(self, backup_name: str) -> Optional[dict]:
        """
        Get detailed information about a backup.
        
        Args:
            backup_name: Name of backup file
            
        Returns:
            Dictionary with backup info or None if not found
        """
        try:
            backup_path = self.backup_dir / backup_name
            
            if not backup_path.exists():
                return None
            
            stat = backup_path.stat()
            
            # Try to load and get config info
            with open(backup_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return {
                'name': backup_name,
                'path': str(backup_path),
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime),
                'agent_name': config_data.get('automation', {}).get('agent_name', 'Unknown'),
                'has_credentials': bool(config_data.get('credentials', {}).get('username'))
            }
            
        except Exception as e:
            print(f"Error getting backup info: {e}")
            return None
    
    def cleanup_old_backups(self, days: int = 30) -> int:
        """
        Delete backups older than specified days.
        
        Args:
            days: Delete backups older than this many days
            
        Returns:
            Number of backups deleted
        """
        deleted = 0
        
        try:
            if not self.backup_dir.exists():
                return 0
            
            cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            for backup_file in self.backup_dir.glob("config_backup_*.json"):
                if backup_file.stat().st_mtime < cutoff:
                    backup_file.unlink()
                    deleted += 1
                    
        except Exception as e:
            print(f"Error cleaning up backups: {e}")
        
        return deleted


class AutoBackup:
    """
    Automatic backup manager that creates backups on configuration changes.
    """
    
    def __init__(self, config_path: str = "config.json", 
                 interval_minutes: int = 60):
        """
        Initialize auto-backup manager.
        
        Args:
            config_path: Path to configuration file
            interval_minutes: Minimum interval between auto-backups
        """
        self.backup_manager = ConfigBackup(config_path)
        self.interval_minutes = interval_minutes
        self.last_backup: Optional[datetime] = None
    
    def should_backup(self) -> bool:
        """Check if enough time has passed for another backup."""
        if self.last_backup is None:
            return True
        
        elapsed = (datetime.now() - self.last_backup).total_seconds() / 60
        return elapsed >= self.interval_minutes
    
    def backup_if_needed(self) -> bool:
        """
        Create backup if interval has passed.
        
        Returns:
            True if backup was created, False otherwise
        """
        if not self.should_backup():
            return False
        
        success, _ = self.backup_manager.create_backup(label="auto")
        if success:
            self.last_backup = datetime.now()
        
        return success

# Made with Bob
