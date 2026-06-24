"""
Recent Tools Tracking System (Phase 6.1)
=========================================

This module provides a singleton manager for tracking recently used tools.
Recent tools are persisted to JSON and displayed in the main menu.

Features:
- Track last 10 tools used
- Show top 3 most recent in UI
- Persist to ~/.art_q_master/recent_tools.json
- Thread-safe singleton pattern
- Automatic cleanup of invalid tool IDs

Usage:
    from utils.recent_tools import get_recent_tools_manager
    
    # Get singleton instance
    manager = get_recent_tools_manager()
    
    # Add tool when launched
    manager.add_tool("qcontrol")
    
    # Get recent tools for display
    recent = manager.get_recent_tools(limit=3)
    
    # Clear all recent tools
    manager.clear()
"""

import json
import os
from pathlib import Path
from typing import List, Optional
from threading import Lock


class RecentToolsManager:
    """
    Singleton manager for tracking recently used tools.
    
    Maintains a list of recently used tool IDs, persisted to JSON.
    Thread-safe for concurrent access.
    
    Attributes:
        _recent_tools: List of tool IDs in reverse chronological order
        _max_tools: Maximum number of tools to track (default: 10)
        _storage_path: Path to JSON storage file
        _lock: Thread lock for safe concurrent access
    """
    
    _instance: Optional['RecentToolsManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize recent tools manager."""
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._recent_tools: List[str] = []
        self._max_tools = 10
        
        # Set up storage path
        home_dir = Path.home()
        storage_dir = home_dir / ".art_q_master"
        storage_dir.mkdir(exist_ok=True)
        self._storage_path = storage_dir / "recent_tools.json"
        
        # Load existing recent tools
        self._load()
    
    def add_tool(self, tool_id: str) -> None:
        """
        Add a tool to recent tools list.
        
        If tool already exists, it's moved to the front.
        If list exceeds max_tools, oldest is removed.
        
        Args:
            tool_id: Tool identifier to add
        """
        with self._lock:
            # Remove if already exists
            if tool_id in self._recent_tools:
                self._recent_tools.remove(tool_id)
            
            # Add to front
            self._recent_tools.insert(0, tool_id)
            
            # Trim to max size
            if len(self._recent_tools) > self._max_tools:
                self._recent_tools = self._recent_tools[:self._max_tools]
            
            # Persist to disk
            self._save()
    
    def get_recent_tools(self, limit: int = 3) -> List[str]:
        """
        Get list of recent tool IDs.
        
        Args:
            limit: Maximum number of tools to return (default: 3)
        
        Returns:
            List[str]: Tool IDs in reverse chronological order
        """
        with self._lock:
            return self._recent_tools[:limit]
    
    def clear(self) -> None:
        """Clear all recent tools."""
        with self._lock:
            self._recent_tools = []
            self._save()
    
    def remove_tool(self, tool_id: str) -> None:
        """
        Remove a specific tool from recent tools.
        
        Args:
            tool_id: Tool identifier to remove
        """
        with self._lock:
            if tool_id in self._recent_tools:
                self._recent_tools.remove(tool_id)
                self._save()
    
    def validate_tools(self, valid_tool_ids: List[str]) -> None:
        """
        Remove any tools that are not in the valid list.
        
        Useful for cleaning up after tools are removed or renamed.
        
        Args:
            valid_tool_ids: List of valid tool identifiers
        """
        with self._lock:
            original_count = len(self._recent_tools)
            self._recent_tools = [
                tool_id for tool_id in self._recent_tools
                if tool_id in valid_tool_ids
            ]
            
            # Save if any were removed
            if len(self._recent_tools) < original_count:
                self._save()
    
    def _load(self) -> None:
        """Load recent tools from JSON file."""
        try:
            if self._storage_path.exists():
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._recent_tools = data.get('recent_tools', [])
                    
                    # Validate format
                    if not isinstance(self._recent_tools, list):
                        self._recent_tools = []
                    
                    # Ensure all items are strings
                    self._recent_tools = [
                        str(tool_id) for tool_id in self._recent_tools
                        if isinstance(tool_id, str)
                    ]
        except Exception as e:
            print(f"Warning: Could not load recent tools: {e}")
            self._recent_tools = []
    
    def _save(self) -> None:
        """Save recent tools to JSON file."""
        try:
            data = {
                'recent_tools': self._recent_tools,
                'version': '1.0'
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save recent tools: {e}")
    
    def get_storage_path(self) -> Path:
        """
        Get path to storage file.
        
        Returns:
            Path: Path to recent_tools.json
        """
        return self._storage_path


# Singleton accessor
_manager_instance: Optional[RecentToolsManager] = None


def get_recent_tools_manager() -> RecentToolsManager:
    """
    Get the singleton RecentToolsManager instance.
    
    Returns:
        RecentToolsManager: Singleton manager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RecentToolsManager()
    return _manager_instance


# Export public API
__all__ = [
    'RecentToolsManager',
    'get_recent_tools_manager',
]

# Made with Bob