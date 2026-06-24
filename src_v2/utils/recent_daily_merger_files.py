"""
Recent Daily Merger Files Tracking
====================================

Singleton manager that persists the last-used output folders for the
Daily Case Merger tool.

Stored at: ~/.art_q_master/recent_daily_merger.json
Thread-safe singleton.

Usage::

    from utils.recent_daily_merger_files import get_recent_daily_merger_manager

    manager = get_recent_daily_merger_manager()
    manager.add_output_folder("/path/to/folder")
    recent = manager.get_recent_folders(limit=5)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional


class RecentDailyMergerManager:
    """
    Singleton manager for tracking recently used output folders in
    the Daily Case Merger tool.

    Attributes:
        _recent_folders: List of folder-info dicts (path, timestamp)
        _max_entries:    Maximum entries to keep (default 10)
        _storage_path:   Path to the JSON persistence file
        _lock:           Thread lock for safe concurrent access
    """

    _instance: Optional["RecentDailyMergerManager"] = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self._recent_folders: List[Dict[str, str]] = []
        self._max_entries = 10

        home_dir = Path.home()
        storage_dir = home_dir / ".art_q_master"
        storage_dir.mkdir(exist_ok=True)
        self._storage_path = storage_dir / "recent_daily_merger.json"

        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_output_folder(self, folder_path: str) -> None:
        """
        Record an output folder path.  Moves existing entry to front.

        Args:
            folder_path: Absolute path to the output folder.
        """
        with self._lock:
            folder_path = str(Path(folder_path).resolve())

            # Remove existing entry if present
            self._recent_folders = [
                f for f in self._recent_folders if f.get("path") != folder_path
            ]

            self._recent_folders.insert(
                0,
                {
                    "path":      folder_path,
                    "name":      Path(folder_path).name,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            if len(self._recent_folders) > self._max_entries:
                self._recent_folders = self._recent_folders[: self._max_entries]

            self._save()

    def get_recent_folders(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Return recent folder info dicts (path, name, timestamp).

        Only returns folders that still exist on disk.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of dicts with keys 'path', 'name', 'timestamp'.
        """
        with self._lock:
            existing = [
                f for f in self._recent_folders if Path(f["path"]).exists()
            ]
            if len(existing) < len(self._recent_folders):
                self._recent_folders = existing
                self._save()
            return existing[:limit]

    def get_recent_folder_paths(self, limit: int = 5) -> List[str]:
        """Return a plain list of recent folder path strings."""
        return [f["path"] for f in self.get_recent_folders(limit=limit)]

    def clear(self) -> None:
        """Remove all stored entries."""
        with self._lock:
            self._recent_folders = []
            self._save()

    def get_storage_path(self) -> Path:
        return self._storage_path

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        try:
            if self._storage_path.exists():
                with open(self._storage_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                    entries = data.get("recent_folders", [])
                    if not isinstance(entries, list):
                        entries = []
                    valid = []
                    for item in entries:
                        if isinstance(item, dict) and "path" in item:
                            item.setdefault("name", Path(item["path"]).name)
                            item.setdefault("timestamp", datetime.now().isoformat())
                            valid.append(item)
                    self._recent_folders = valid
        except Exception as exc:
            print(f"Warning: Could not load recent daily merger data: {exc}")
            self._recent_folders = []

    def _save(self) -> None:
        try:
            with open(self._storage_path, "w", encoding="utf-8") as fh:
                json.dump(
                    {"recent_folders": self._recent_folders, "version": "1.0"},
                    fh,
                    indent=2,
                )
        except Exception as exc:
            print(f"Warning: Could not save recent daily merger data: {exc}")


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_manager_instance: Optional[RecentDailyMergerManager] = None


def get_recent_daily_merger_manager() -> RecentDailyMergerManager:
    """Return the singleton RecentDailyMergerManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = RecentDailyMergerManager()
    return _manager_instance


__all__ = [
    "RecentDailyMergerManager",
    "get_recent_daily_merger_manager",
]

# Made with Bob
