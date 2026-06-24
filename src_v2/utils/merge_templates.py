"""
Merge Templates System (Phase 6.3)
===================================

This module provides a singleton manager for saving and loading
column mapping templates in the Merger tool.

Features:
- Save column mapping configurations as named templates
- Load templates for quick reuse
- Persist to ~/.art_q_master/merge_templates.json
- Thread-safe singleton pattern
- Template validation

Usage:
    from utils.merge_templates import get_merge_templates_manager
    
    # Get singleton instance
    manager = get_merge_templates_manager()
    
    # Save a template
    manager.save_template(
        name="Standard CRM Merge",
        description="Merge CRM exports with standard columns",
        column_mappings=[
            {'output_name': 'Customer Name', 'source_columns': ['Name', 'Contact Name']},
            {'output_name': 'Email', 'source_columns': ['Email Address', 'Contact Email']}
        ]
    )
    
    # Get all templates
    templates = manager.get_templates()
    
    # Load a specific template
    template = manager.get_template("Standard CRM Merge")
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from threading import Lock
from datetime import datetime


class MergeTemplatesManager:
    """
    Singleton manager for merge column mapping templates.
    
    Maintains a collection of named templates with column mappings,
    persisted to JSON. Thread-safe for concurrent access.
    
    Attributes:
        _templates: Dict of template name -> template info
        _storage_path: Path to JSON storage file
        _lock: Thread lock for safe concurrent access
    """
    
    _instance: Optional['MergeTemplatesManager'] = None
    _lock = Lock()
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize merge templates manager."""
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._templates: Dict[str, Dict[str, Any]] = {}
        
        # Set up storage path
        home_dir = Path.home()
        storage_dir = home_dir / ".art_q_master"
        storage_dir.mkdir(exist_ok=True)
        self._storage_path = storage_dir / "merge_templates.json"
        
        # Load existing templates
        self._load()
    
    def save_template(
        self,
        name: str,
        column_mappings: List[Dict[str, Any]],
        description: str = ""
    ) -> bool:
        """
        Save a column mapping template.
        
        Args:
            name: Template name (unique identifier)
            column_mappings: List of column mapping dicts
            description: Optional description of template
        
        Returns:
            bool: True if saved successfully
        """
        with self._lock:
            # Validate inputs
            if not name or not name.strip():
                return False
            
            if not column_mappings:
                return False
            
            # Validate column mappings format
            for mapping in column_mappings:
                if not isinstance(mapping, dict):
                    return False
                if 'output_name' not in mapping or 'source_columns' not in mapping:
                    return False
                if not isinstance(mapping['source_columns'], list):
                    return False
            
            # Create template info
            template_info = {
                'name': name.strip(),
                'description': description.strip(),
                'column_mappings': column_mappings,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat(),
            }
            
            # Update modified time if template already exists
            if name in self._templates:
                template_info['created'] = self._templates[name].get('created', template_info['created'])
            
            # Save template
            self._templates[name] = template_info
            
            # Persist to disk
            self._save()
            return True
    
    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by name.
        
        Args:
            name: Template name
        
        Returns:
            Optional[Dict]: Template info or None if not found
        """
        with self._lock:
            return self._templates.get(name)
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """
        Get all templates sorted by modified date (newest first).
        
        Returns:
            List[Dict]: List of template info dicts
        """
        with self._lock:
            templates = list(self._templates.values())
            # Sort by modified date, newest first
            templates.sort(
                key=lambda t: t.get('modified', ''),
                reverse=True
            )
            return templates
    
    def get_template_names(self) -> List[str]:
        """
        Get list of all template names.
        
        Returns:
            List[str]: Template names sorted alphabetically
        """
        with self._lock:
            return sorted(self._templates.keys())
    
    def delete_template(self, name: str) -> bool:
        """
        Delete a template.
        
        Args:
            name: Template name
        
        Returns:
            bool: True if deleted, False if not found
        """
        with self._lock:
            if name in self._templates:
                del self._templates[name]
                self._save()
                return True
            return False
    
    def rename_template(self, old_name: str, new_name: str) -> bool:
        """
        Rename a template.
        
        Args:
            old_name: Current template name
            new_name: New template name
        
        Returns:
            bool: True if renamed successfully
        """
        with self._lock:
            if old_name not in self._templates:
                return False
            
            if not new_name or not new_name.strip():
                return False
            
            if new_name in self._templates and new_name != old_name:
                return False  # Name already exists
            
            # Copy template with new name
            template = self._templates[old_name].copy()
            template['name'] = new_name.strip()
            template['modified'] = datetime.now().isoformat()
            
            # Remove old, add new
            del self._templates[old_name]
            self._templates[new_name] = template
            
            self._save()
            return True
    
    def clear_all(self) -> None:
        """Clear all templates."""
        with self._lock:
            self._templates = {}
            self._save()
    
    def export_template(self, name: str, file_path: str) -> bool:
        """
        Export a template to a JSON file.
        
        Args:
            name: Template name
            file_path: Path to export file
        
        Returns:
            bool: True if exported successfully
        """
        with self._lock:
            if name not in self._templates:
                return False
            
            try:
                template = self._templates[name]
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2)
                return True
            except Exception as e:
                print(f"Warning: Could not export template: {e}")
                return False
    
    def import_template(self, file_path: str) -> Optional[str]:
        """
        Import a template from a JSON file.
        
        Args:
            file_path: Path to import file
        
        Returns:
            Optional[str]: Template name if imported successfully, None otherwise
        """
        with self._lock:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                
                # Validate template format
                if not isinstance(template, dict):
                    return None
                
                if 'name' not in template or 'column_mappings' not in template:
                    return None
                
                name = template['name']
                column_mappings = template['column_mappings']
                description = template.get('description', '')
                
                # Save template
                if self.save_template(name, column_mappings, description):
                    return name
                
                return None
            except Exception as e:
                print(f"Warning: Could not import template: {e}")
                return None
    
    def _load(self) -> None:
        """Load templates from JSON file."""
        try:
            if self._storage_path.exists():
                with open(self._storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    templates = data.get('templates', {})
                    
                    # Validate format
                    if isinstance(templates, dict):
                        self._templates = templates
                    else:
                        self._templates = {}
        except Exception as e:
            print(f"Warning: Could not load merge templates: {e}")
            self._templates = {}
    
    def _save(self) -> None:
        """Save templates to JSON file."""
        try:
            data = {
                'templates': self._templates,
                'version': '1.0'
            }
            
            with open(self._storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save merge templates: {e}")
    
    def get_storage_path(self) -> Path:
        """
        Get path to storage file.
        
        Returns:
            Path: Path to merge_templates.json
        """
        return self._storage_path


# Singleton accessor
_manager_instance: Optional[MergeTemplatesManager] = None


def get_merge_templates_manager() -> MergeTemplatesManager:
    """
    Get the singleton MergeTemplatesManager instance.
    
    Returns:
        MergeTemplatesManager: Singleton manager instance
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = MergeTemplatesManager()
    return _manager_instance


# Export public API
__all__ = [
    'MergeTemplatesManager',
    'get_merge_templates_manager',
]

# Made with Bob