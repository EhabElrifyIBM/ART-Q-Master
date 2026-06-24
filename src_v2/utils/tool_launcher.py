"""
Safe launcher adapters for src_v2.

These adapters launch only the duplicated files inside src_v2 so updates can be
applied in the isolated workspace without affecting the current src/ codebase.
"""

import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict

from utils.runtime import ensure_runtime_paths, get_runtime_paths


@dataclass(frozen=True)
class ToolLaunchResult:
    """Represents the result of a launch request."""

    launched: bool
    message: str


def _get_v2_file_map() -> Dict[str, str]:
    """Return the confirmed v2-local file path for each tool."""
    paths = get_runtime_paths()
    return {
        "assigner":       os.path.join(paths.src_v2_root, "Assigner", "main_window_assigner.py"),
        "merger":         os.path.join(paths.src_v2_root, "Merger", "Merger.py"),
        # archiver now launches the modern PyQt5 ArchiverWindow (not the old tkinter Archiver.py)
        "archiver":       os.path.join(paths.src_v2_root, "Archiver", "run_archiver.py"),
        "qcontrol":       os.path.join(paths.art_q_control_dir, "Dispatcher_v2.py"),
        "reachrate":      os.path.join(paths.src_v2_root, "Reach Rate Calculator", "ReachRateCalculatorUI_v2.py"),
        "daily_merger":   os.path.join(paths.src_v2_root, "DailyMerger", "run_daily_merger.py"),
        "monthly_merger": os.path.join(paths.src_v2_root, "MonthlyMerger", "run_monthly_merger.py"),
    }


def can_launch_tool(tool_id: str) -> bool:
    """Return whether a tool has a confirmed safe v2-local launcher."""
    tool_file = _get_v2_file_map().get(tool_id)
    return bool(tool_file and os.path.exists(tool_file))


def _build_launch_command(tool_id: str) -> list[str]:
    """Build the subprocess command for a duplicated v2 tool."""
    file_map = _get_v2_file_map()
    target = file_map.get(tool_id)
    if not target or not os.path.exists(target):
        raise FileNotFoundError(f"V2 launcher target was not found for '{tool_id}': {target}")

    if tool_id == "assigner":
        return [sys.executable, "-m", "Assigner.main_window_assigner"]
    if tool_id == "archiver":
        return [sys.executable, "-m", "Archiver.run_archiver"]
    if tool_id == "daily_merger":
        return [sys.executable, "-m", "DailyMerger.run_daily_merger"]
    if tool_id == "monthly_merger":
        return [sys.executable, "-m", "MonthlyMerger.run_monthly_merger"]
    return [sys.executable, target]


def _launch_in_subprocess(tool_id: str) -> None:
    """Launch the tool in a separate Python process to avoid Qt event-loop conflicts."""
    ensure_runtime_paths()
    paths = get_runtime_paths()
    env = os.environ.copy()

    existing_pythonpath = env.get("PYTHONPATH", "")
    python_paths = [paths.src_v2_root]
    if existing_pythonpath:
        python_paths.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    subprocess.Popen(
        _build_launch_command(tool_id),
        cwd=paths.src_v2_root,
        env=env,
    )


def launch_tool(tool_id: str) -> ToolLaunchResult:
    """Launch a tool using its duplicated src_v2 entry point when available."""
    if not can_launch_tool(tool_id):
        return ToolLaunchResult(
            launched=False,
            message=f"No confirmed v2 launcher is registered for tool_id '{tool_id}'.",
        )

    _launch_in_subprocess(tool_id)
    return ToolLaunchResult(
        launched=True,
        message=f"V2 launcher executed for '{tool_id}'.",
    )


# Made with Bob