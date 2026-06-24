"""
Recent Merger Files Tracking System (Phase 6.3)
================================================

This module provides a singleton manager for tracking recently used
file sets in the Merger tool.

Features:
- Track last 10 merge operations (with file lists)
- Persist to ~/.art_q_master/recent_merger_files.json
- Thread-safe singleton pattern
- Automatic cleanup of non-existent files

Usage:
    from utils.recent_merger_files import get_recent_merger_files_manager
    
    # Get singleton instance
    manager = get_recent_merger_files_manager()
    
    # Add merge operation when completed
    manager.add_merge_operation(
        file_paths=["/path/to/file1.xlsx", "/path/to/file2.xlsx"],
        output_path="/path/to/merged.xlsx"
    )
    
    # Get recent merge operations for display
    recent = manager.get_recent_operations(limit=5)
    
    # Clear all recent operations
    manager.clear()
"""

import json
import os
from pathlib import Path
from typing import List, Optional, Dict
from threading import Lock
from datetime import datetime


class RecentMergerFilesManager:
    """
    Singleton manager for tracking recent merge operations in Merger tool.
    
    Maintains a list of recent merge operations with file lists and metadata,
    persisted to JSON. Thread-safe for concurrent access.
    
    Attributes:
        _recent_operations: List of operation info dicts in reverse chronological order
        _max_operations: Maximum number of operations to track (default: 10)
        _storage_path: Path to JSON storage file
        _lock: Thread lock for safe concurrent access
    """
    
    _instance: Optional['RecentMergerFilesManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize recent merger files manager."""
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._recent_operations: List[Dict] = []
        self._max_operations = 10
        
        # Set up storage path
        home_dir = Path.home()
        storage_dir = home_dir / ".art_q_master"
        storage_dir.mkdir(exist_ok=True)
        self._storage_path = storage_dir / "recent_merger_files.json"
        
        # Load existing recent operations
        self._load()
        
        # Clean up non-existent files
        self._cleanup_missing_files()
    
    def add_merge_operation(
        self,
        file_paths: List[str],
        output_path: str,
        column_count: int = 0,
        row_count: int = 0
    ) -> None:
        """
        Add a merge operation to recent operations list.
        
        Args:
            file_paths: List of source file paths
            output_path: Path to output file
            column_count: Number of columns in output
            row_count: Number of rows in output
        """
        with self._lock:
            # Normalize paths
            file_paths = [str(Path(p).resolve()) for p in file_paths]
            output_path = str(Path(output_path).resolve())
            
            # Create operation info
            operation_info = {
                'file_paths': file_paths,
                'file_names': [Path(p).name for p in file_paths],
                'output_path': output_path,
                'output_name': Path(output_path).name,
                'column_count': column_count,
                'row_count': row_count,
                'timestamp': datetime.now().isoformat(),
            }
            
            # Remove if similar operation already exists (same file set)
            self._recent_operations = [
                op for op in self._recent_operations
                if set(op.get('file_paths', [])) != set(file_paths)
            ]
            
            # Add to front
            self._recent_operations.insert(0, operation_info)
            
            # Trim to max size
            if len(self._recent_operations) > self._max_operations:
                self._recent_operations = self._recent_operations[:self._max_operations]
            
            # Persist to disk
            self._save()
    
    def get_recent_operations(self, limit: int = 5) -> List[Dict]:
        """
        Get list of recent merge operation info dicts.
        
        Args:
            limit: Maximum number of operations to return (default: 5)
        
        Returns:
            List[Dict]: Operation info dicts with file_paths, output_path, etc.
        """
        with self._lock:
            # Filter out operations with missing files
            existing_operations = []
            for op in self._recent_operations:
                file_paths = op.get('file_paths', [])
                # Check if at least one source file still exists
                if any(Path(p).exists() for p in file_paths):
                    existing_operations.append(op)
            
            # Update list if any were removed
            if len(existing_operations) < len(self._recent_operations):
                self._recent_operations = existing_operations
                self._save()
            
            return self._recent_operations[:limit]
    
    def clear(self) -> None:
        """Clear all recent operations."""
        with self._lock:
            self._recent_operations = []
            self._save()
    
    def remove_operation(self, index: int) -> None:
        """
        Remove a specific operation by index.
        
        Args:
            index: Index of operation to remove
        """
        with self._lock:
            if 0 <= index < len(self._recent_operations):
                self._recent_operations.pop(index)
                self._save()
    
    def _cleanup_missing_files(self) -> None:
        """Remove operations where all source files no longer exist."""
        with self._lock:
            original_count = len(self._recent_operations)
            
            self._recent_operations = [
                op for op in self._recent_operations
                if any(Path(p).exists() for p in op.get('file_paths', []))
            ]
            
            # Save if any were removed
            if len(self._recent_operations) < original_count:
                self._save()
    
    def _load(self) -> None:
        """Load recent operations from JSON file."""
        try:
            if self._storage_path.exists():
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._recent_operations = data.get('recent_operations', [])
                    
                    # Validate format
                    if not isinstance(self._recent_operations, list):
                        self._recent_operations = []
                    
                    # Ensure all items are dicts with required keys
                    valid_operations = []
                    for item in self._recent_operations:
                        if isinstance(item, dict) and 'file_paths' in item:
                            # Add missing keys with defaults
                            if 'file_names' not in item:
                                item['file_names'] = [Path(p).name for p in item.get('file_paths', [])]
                            if 'timestamp' not in item:
                                item['timestamp'] = datetime.now().isoformat()
                            if 'column_count' not in item:
                                item['column_count'] = 0
                            if 'row_count' not in item:
                                item['row_count'] = 0
                            valid_operations.append(item)
                    
                    self._recent_operations = valid_operations
        except Exception as e:
            print(f"Warning: Could not load recent merger files: {e}")
            self._recent_operations = []
    
    def _save(self) -> None:
        """Save recent operations to JSON file."""
        try:
            data = {
                'recent_operations': self._recent_operations,
                'version': '1.0'
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save recent merger files: {e}")
    
    def get_storage_path(self) -> Path:
        """
        Get path to storage file.
        
        Returns:
            Path: Path to recent_merger_files.json
        """
        return self._storage_path


# Singleton accessor
_manager_instance: Optional[RecentMergerFilesManager] = None


def get_recent_merger_files_manager() -> RecentMergerFilesManager:
    """
    Get the singleton RecentMergerFilesManager instance.
    
    Returns:
        RecentMergerFilesManager: Singleton manager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RecentMergerFilesManager()
    return _manager_instance


# Export public API
__all__ = [
    'RecentMergerFilesManager',
    'get_recent_merger_files_manager',
]

# Made with Bob