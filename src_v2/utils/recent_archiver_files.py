"""
Recent Archiver Files Tracking System (Phase 6.2)
==================================================

This module provides a singleton manager for tracking recently opened
Excel files in the Archiver tool.

Features:
- Track last 10 files opened
- Persist to ~/.art_q_master/recent_archiver_files.json
- Thread-safe singleton pattern
- Automatic cleanup of non-existent files

Usage:
    from utils.recent_archiver_files import get_recent_archiver_files_manager
    
    # Get singleton instance
    manager = get_recent_archiver_files_manager()
    
    # Add file when opened
    manager.add_file("/path/to/workbook.xlsx")
    
    # Get recent files for display
    recent = manager.get_recent_files(limit=5)
    
    # Clear all recent files
    manager.clear()
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from threading import Lock
from datetime import datetime


class RecentArchiverFilesManager:
    """
    Singleton manager for tracking recently opened Excel files in Archiver.
    
    Maintains a list of recently opened file paths with metadata,
    persisted to JSON. Thread-safe for concurrent access.
    
    Attributes:
        _recent_files: List of file info dicts in reverse chronological order
        _max_files: Maximum number of files to track (default: 10)
        _storage_path: Path to JSON storage file
        _lock: Thread lock for safe concurrent access
    """
    
    _instance: Optional['RecentArchiverFilesManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize recent files manager."""
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._recent_files: List[Dict[str, str]] = []
        self._max_files = 10
        
        # Set up storage path
        home_dir = Path.home()
        storage_dir = home_dir / ".art_q_master"
        storage_dir.mkdir(exist_ok=True)
        self._storage_path = storage_dir / "recent_archiver_files.json"
        
        # Load existing recent files
        self._load()
        
        # Clean up non-existent files
        self._cleanup_missing_files()
    
    def add_file(self, file_path: str) -> None:
        """
        Add a file to recent files list.
        
        If file already exists, it's moved to the front with updated timestamp.
        If list exceeds max_files, oldest is removed.
        
        Args:
            file_path: Full path to Excel file
        """
        with self._lock:
            # Normalize path
            file_path = str(Path(file_path).resolve())
            
            # Remove if already exists
            self._recent_files = [
                f for f in self._recent_files
                if f.get('path') != file_path
            ]
            
            # Add to front with metadata
            file_info = {
                'path': file_path,
                'name': Path(file_path).name,
                'timestamp': datetime.now().isoformat(),
            }
            self._recent_files.insert(0, file_info)
            
            # Trim to max size
            if len(self._recent_files) > self._max_files:
                self._recent_files = self._recent_files[:self._max_files]
            
            # Persist to disk
            self._save()
    
    def get_recent_files(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get list of recent file info dicts.
        
        Args:
            limit: Maximum number of files to return (default: 5)
        
        Returns:
            List[Dict]: File info dicts with 'path', 'name', 'timestamp'
        """
        with self._lock:
            # Filter out files that no longer exist
            existing_files = [
                f for f in self._recent_files
                if Path(f['path']).exists()
            ]
            
            # Update list if any were removed
            if len(existing_files) < len(self._recent_files):
                self._recent_files = existing_files
                self._save()
            
            return self._recent_files[:limit]
    
    def clear(self) -> None:
        """Clear all recent files."""
        with self._lock:
            self._recent_files = []
            self._save()
    
    def remove_file(self, file_path: str) -> None:
        """
        Remove a specific file from recent files.
        
        Args:
            file_path: Full path to file to remove
        """
        with self._lock:
            file_path = str(Path(file_path).resolve())
            original_count = len(self._recent_files)
            
            self._recent_files = [
                f for f in self._recent_files
                if f.get('path') != file_path
            ]
            
            # Save if any were removed
            if len(self._recent_files) < original_count:
                self._save()
    
    def _cleanup_missing_files(self) -> None:
        """Remove files that no longer exist from the list."""
        with self._lock:
            original_count = len(self._recent_files)
            
            self._recent_files = [
                f for f in self._recent_files
                if Path(f.get('path', '')).exists()
            ]
            
            # Save if any were removed
            if len(self._recent_files) < original_count:
                self._save()
    
    def _load(self) -> None:
        """Load recent files from JSON file."""
        try:
            if self._storage_path.exists():
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._recent_files = data.get('recent_files', [])
                    
                    # Validate format
                    if not isinstance(self._recent_files, list):
                        self._recent_files = []
                    
                    # Ensure all items are dicts with required keys
                    valid_files = []
                    for item in self._recent_files:
                        if isinstance(item, dict) and 'path' in item:
                            # Add missing keys with defaults
                            if 'name' not in item:
                                item['name'] = Path(item['path']).name
                            if 'timestamp' not in item:
                                item['timestamp'] = datetime.now().isoformat()
                            valid_files.append(item)
                    
                    self._recent_files = valid_files
        except Exception as e:
            print(f"Warning: Could not load recent archiver files: {e}")
            self._recent_files = []
    
    def _save(self) -> None:
        """Save recent files to JSON file."""
        try:
            data = {
                'recent_files': self._recent_files,
                'version': '1.0'
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save recent archiver files: {e}")
    
    def get_storage_path(self) -> Path:
        """
        Get path to storage file.
        
        Returns:
            Path: Path to recent_archiver_files.json
        """
        return self._storage_path


# Singleton accessor
_manager_instance: Optional[RecentArchiverFilesManager] = None


def get_recent_archiver_files_manager() -> RecentArchiverFilesManager:
    """
    Get the singleton RecentArchiverFilesManager instance.
    
    Returns:
        RecentArchiverFilesManager: Singleton manager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RecentArchiverFilesManager()
    return _manager_instance


# Export public API
__all__ = [
    'RecentArchiverFilesManager',
    'get_recent_archiver_files_manager',
]

# Made with Bob