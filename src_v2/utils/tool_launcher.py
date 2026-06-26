"""
Safe launcher adapters for src_v2.

In development (running as .py), tools are launched in a subprocess so each
tool gets its own Qt event loop without conflicting with the main menu.

In a frozen bundle (.exe built with PyInstaller), .py files no longer exist on
disk, so subprocess launching is impossible.  Instead we launch each tool
in-process by importing its window class and showing it as a top-level window
inside the *existing* QApplication.  The main menu stays open — users can
switch back to it at any time.

Import notes for the frozen build
----------------------------------
- "ART Q Control" has a space in its folder name — Python cannot use it as a
  dotted import.  The spec adds that directory to sys.path (via pathex +
  art_q_control_dir), so ``import Dispatcher_v2`` works directly.
- "Reach Rate Calculator" has the same issue; its files are importable
  directly as ``import ReachRateCalculatorUI_v2``.
- Merger, Archiver, Assigner, DailyMerger and MonthlyMerger are proper
  packages and import normally.
"""

import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict

from utils.runtime import ensure_runtime_paths, get_runtime_paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_frozen() -> bool:
    """Return True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


@dataclass(frozen=True)
class ToolLaunchResult:
    """Represents the result of a launch request."""

    launched: bool
    message: str


# ---------------------------------------------------------------------------
# GC guard — keep open windows alive until the user closes them
# ---------------------------------------------------------------------------

_open_windows: list = []


def _keep_alive(widget) -> None:
    """Prevent a window from being garbage-collected after launch."""
    _open_windows.append(widget)
    try:
        widget.destroyed.connect(
            lambda: _open_windows.remove(widget) if widget in _open_windows else None
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# In-process window helpers
# ---------------------------------------------------------------------------

def _show_window(window) -> None:
    """Show a QMainWindow / QWidget without starting a new event loop."""
    from PyQt5.QtCore import Qt
    window.setAttribute(Qt.WA_DeleteOnClose, True)
    window.show()
    window.raise_()
    window.activateWindow()


# ---------------------------------------------------------------------------
# Individual in-process launchers
# ---------------------------------------------------------------------------

def _launch_qcontrol_inprocess() -> None:
    # "ART Q Control" dir is on sys.path — import Dispatcher_v2 directly
    import Dispatcher_v2  # type: ignore[import]
    Dispatcher_v2.show_mode_selector()


def _launch_assigner_inprocess() -> None:
    from Assigner.main_window_assigner import MainWindow
    w = MainWindow()
    _show_window(w)
    _keep_alive(w)


def _launch_archiver_inprocess() -> None:
    from Archiver.archiver_window import ArchiverWindow
    w = ArchiverWindow()
    _show_window(w)
    _keep_alive(w)


def _launch_daily_merger_inprocess() -> None:
    from DailyMerger.daily_merger_window import DailyMergerWindow
    w = DailyMergerWindow()
    _show_window(w)
    _keep_alive(w)


def _launch_monthly_merger_inprocess() -> None:
    from MonthlyMerger.monthly_merger_window import MonthlyMergerWindow
    w = MonthlyMergerWindow()
    _show_window(w)
    _keep_alive(w)


def _launch_merger_inprocess() -> None:
    # Merger has a modern PyQt5 MergerWindow — use that, not the old tkinter app
    from Merger.merger_window import MergerWindow
    w = MergerWindow()
    _show_window(w)
    _keep_alive(w)


def _launch_reachrate_inprocess() -> None:
    # "Reach Rate Calculator" dir is on sys.path — import the module directly
    import ReachRateCalculatorUI_v2  # type: ignore[import]
    w = ReachRateCalculatorUI_v2.ReachRateCalculatorWindow()
    _show_window(w)
    _keep_alive(w)


# ---------------------------------------------------------------------------
# In-process launcher dispatch table
# ---------------------------------------------------------------------------

_INPROCESS_LAUNCHERS: Dict[str, Callable[[], None]] = {
    "qcontrol":       _launch_qcontrol_inprocess,
    "assigner":       _launch_assigner_inprocess,
    "archiver":       _launch_archiver_inprocess,
    "daily_merger":   _launch_daily_merger_inprocess,
    "monthly_merger": _launch_monthly_merger_inprocess,
    "merger":         _launch_merger_inprocess,
    "reachrate":      _launch_reachrate_inprocess,
}


# ---------------------------------------------------------------------------
# Subprocess launcher helpers  (development / .py run only)
# ---------------------------------------------------------------------------

def _get_v2_file_map() -> Dict[str, str]:
    """Return the .py entry-point path for each tool (dev mode only)."""
    paths = get_runtime_paths()
    return {
        "assigner":       os.path.join(paths.src_v2_root, "Assigner", "main_window_assigner.py"),
        "merger":         os.path.join(paths.src_v2_root, "Merger", "Merger.py"),
        "archiver":       os.path.join(paths.src_v2_root, "Archiver", "run_archiver.py"),
        "qcontrol":       os.path.join(paths.art_q_control_dir, "Dispatcher_v2.py"),
        "reachrate":      os.path.join(paths.src_v2_root, "Reach Rate Calculator", "ReachRateCalculatorUI_v2.py"),
        "daily_merger":   os.path.join(paths.src_v2_root, "DailyMerger", "run_daily_merger.py"),
        "monthly_merger": os.path.join(paths.src_v2_root, "MonthlyMerger", "run_monthly_merger.py"),
    }


def _can_launch_subprocess(tool_id: str) -> bool:
    tool_file = _get_v2_file_map().get(tool_id)
    return bool(tool_file and os.path.exists(tool_file))


def _build_launch_command(tool_id: str) -> list:
    file_map = _get_v2_file_map()
    target = file_map.get(tool_id)
    if not target or not os.path.exists(target):
        raise FileNotFoundError(
            f"V2 launcher target not found for '{tool_id}': {target}"
        )
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
    import subprocess as _sp

    ensure_runtime_paths()
    paths = get_runtime_paths()
    env = os.environ.copy()

    existing = env.get("PYTHONPATH", "")
    parts = [paths.src_v2_root]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    _sp.Popen(
        _build_launch_command(tool_id),
        cwd=paths.src_v2_root,
        env=env,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def can_launch_tool(tool_id: str) -> bool:
    """
    Return True when a confirmed launcher exists for *tool_id*.

    * Frozen build (.exe)  → True for every tool that has an in-process launcher.
    * Dev run (.py)        → True when the tool's .py entry-point exists on disk.
    """
    if _is_frozen():
        return tool_id in _INPROCESS_LAUNCHERS
    return _can_launch_subprocess(tool_id)


def launch_tool(tool_id: str) -> ToolLaunchResult:
    """
    Launch a tool by ID.

    * Frozen build (.exe)  → opens the tool window in-process (no subprocess).
    * Dev run (.py)        → spawns a separate Python subprocess as before.
    """
    if _is_frozen():
        launcher = _INPROCESS_LAUNCHERS.get(tool_id)
        if launcher is None:
            return ToolLaunchResult(
                launched=False,
                message=f"No in-process launcher registered for '{tool_id}'.",
            )
        try:
            launcher()
            return ToolLaunchResult(launched=True, message=f"Launched '{tool_id}' in-process.")
        except Exception as exc:
            return ToolLaunchResult(
                launched=False,
                message=f"In-process launch failed for '{tool_id}': {exc}",
            )

    # ---- development path ------------------------------------------------
    if not _can_launch_subprocess(tool_id):
        return ToolLaunchResult(
            launched=False,
            message=f"No confirmed v2 launcher registered for '{tool_id}'.",
        )
    try:
        _launch_in_subprocess(tool_id)
        return ToolLaunchResult(launched=True, message=f"V2 subprocess launched for '{tool_id}'.")
    except Exception as exc:
        return ToolLaunchResult(
            launched=False,
            message=f"Subprocess launch failed for '{tool_id}': {exc}",
        )


# Made with Bob
