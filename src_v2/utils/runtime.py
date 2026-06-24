"""
Shared runtime helpers for src_v2.

This copy exists in utils so all v2 packages can import the same runtime
services through a normal package path.
"""

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved path set for the src_v2 workspace."""

    project_root: str
    src_v2_root: str
    art_q_control_dir: str
    ui_dir: str
    utils_dir: str
    config_file: str


def _utils_dir() -> str:
    """Return the absolute directory of the utils package."""
    return os.path.dirname(os.path.abspath(__file__))


def get_src_v2_root() -> str:
    """Return the absolute src_v2 root directory."""
    return os.path.dirname(_utils_dir())


def get_project_root() -> str:
    """Return the repository root containing src and src_v2."""
    return os.path.dirname(get_src_v2_root())


def get_runtime_paths() -> RuntimePaths:
    """Build the common runtime path set."""
    src_v2_root = get_src_v2_root()
    project_root = get_project_root()
    return RuntimePaths(
        project_root=project_root,
        src_v2_root=src_v2_root,
        art_q_control_dir=os.path.join(src_v2_root, "ART Q Control"),
        ui_dir=os.path.join(src_v2_root, "ui"),
        utils_dir=_utils_dir(),
        config_file=os.path.join(project_root, "config.json"),
    )


def ensure_runtime_paths() -> RuntimePaths:
    """Ensure the required src_v2 paths are available on sys.path."""
    paths = get_runtime_paths()
    for path in (paths.src_v2_root, paths.art_q_control_dir, paths.ui_dir, paths.utils_dir):
        if path not in sys.path:
            sys.path.insert(0, path)
    return paths


def ensure_directory(path: str) -> str:
    """Create a directory if it does not exist and return the same path."""
    os.makedirs(path, exist_ok=True)
    return path


def read_json_file(path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Read JSON data from disk, returning a default dictionary when unavailable."""
    if not os.path.exists(path):
        return dict(default or {})
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            return data if isinstance(data, dict) else dict(default or {})
    except Exception:
        return dict(default or {})


def get_ui_font_size(default: int = 22) -> int:
    """
    Get default UI font size.
    
    Note: Font size is now managed through V2SettingsBus and not persisted to config.json.
    This function returns the default value for initial setup.
    """
    return max(10, min(40, default))


def get_theme_mode(default: str = "light") -> str:
    """
    Read the persisted theme mode from config.json.
    Falls back to theme_config.json for backward compatibility.
    """
    paths = get_runtime_paths()
    
    # Try config.json first (new location)
    config = read_json_file(paths.config_file, default={})
    value = config.get("theme_mode")
    if value in {"light", "dark", "auto"}:
        return value
    
    # Fallback to theme_config.json (legacy location)
    theme_config_path = os.path.join(paths.project_root, "theme_config.json")
    theme_config = read_json_file(theme_config_path, default={})
    value = theme_config.get("theme_mode", default)
    if value in {"light", "dark", "auto"}:
        return value
    
    return default


def build_daily_cache_name(agent_name: str, mode: str, extension: str = ".xlsx") -> str:
    """Build the standardized v2 daily cache filename."""
    date_str = datetime.now().strftime("%m%d")
    agent_token = (agent_name or "agent").split()[0].strip().replace(" ", "_") or "agent"
    mode_token = (mode or "default").strip().replace(" ", "_").lower()
    return f"working_cases_{agent_token}_{mode_token}_{date_str}{extension}"


def build_cache_path(cache_directory: str, agent_name: str, mode: str) -> str:
    """Build the full cache file path using the v2 naming convention."""
    ensure_directory(cache_directory)
    return os.path.join(cache_directory, build_daily_cache_name(agent_name, mode))

# Made with Bob
