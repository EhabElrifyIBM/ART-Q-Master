"""
Safe launcher adapters for src_v2.

Six v2-native tools (Assigner, Merger, Archiver, DailyMerger, MonthlyMerger,
ReachRate) launch in-process: we import the window class and show it as a
top-level window inside the *existing* QApplication, so they share one
QApplication and one V2SettingsBus with the main shell and live settings
changes (theme, font preset) reach every open tool window.

ART Q Control (Dispatcher_v2 and its legacy dependents — Main.py,
Functions.py, CaseReviewer_v2.py, AutoSender_v2.py, CompaniesProcess_v2.py)
still launches in its own OS subprocess. That legacy code calls sys.exit()
and app.quit() throughout as internal control flow (e.g. cancelling its
config setup dialog). That is safe when isolated in its own process — it is
NOT safe in-process, where it would tear down the shared QApplication and
close the entire v2 shell.

Before spawning that subprocess, we validate (and interactively fix, if
needed) ART Q Control's own config.json right here in the main shell
process — see _ensure_qcontrol_config_valid(). Its config setup dialog
needs real keyboard input, and its subprocess's windows don't reliably get
it (confirmed: OS-level focus-forcing techniques don't fix this, most
likely endpoint security software specifically restricting keyboard input
for a freshly-spawned child process). Doing the one-time setup in this
process — which is proven to receive keyboard input normally — sidesteps
that instead of continuing to fight it from the child side.

Import notes for the frozen build
----------------------------------
- "Reach Rate Calculator" has a space in its folder name — Python cannot use
  it as a dotted import. The spec adds that directory to sys.path (via
  pathex), so ``import ReachRateCalculatorUI_v2`` works directly; in dev
  mode, ``ensure_runtime_paths()`` adds it instead.
- Merger, Archiver, Assigner, DailyMerger and MonthlyMerger are proper
  packages and import normally.
"""

import os
import sys
from dataclasses import dataclass
from typing import Callable, Dict

from utils.runtime import ensure_runtime_paths, get_runtime_paths


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
    "assigner":       _launch_assigner_inprocess,
    "archiver":       _launch_archiver_inprocess,
    "daily_merger":   _launch_daily_merger_inprocess,
    "monthly_merger": _launch_monthly_merger_inprocess,
    "merger":         _launch_merger_inprocess,
    "reachrate":      _launch_reachrate_inprocess,
}


# ---------------------------------------------------------------------------
# ART Q Control — subprocess launcher (legacy code, needs process isolation)
# ---------------------------------------------------------------------------

_QCONTROL_TOOL_ID = "qcontrol"


def _qcontrol_entry_point() -> str:
    paths = get_runtime_paths()
    return os.path.join(paths.art_q_control_dir, "Dispatcher_v2.py")


def _can_launch_qcontrol_subprocess() -> bool:
    return os.path.exists(_qcontrol_entry_point())


def _ensure_qcontrol_config_valid() -> bool:
    """Validate (and, if needed, interactively fix) ART Q Control's own
    config.json — in THIS process, before ever spawning the subprocess.

    ART Q Control's config setup dialog needs real keyboard input on first
    run. Its subprocess's windows never reliably receive it: confirmed by
    direct testing that a field can show a genuine blinking text cursor
    (real Qt/OS focus) while zero keystrokes ever arrive, even after trying
    raise_()/activateWindow(), AllowSetForegroundWindow from the parent, and
    AttachThreadInput from the child — nothing changed it, which points at
    something below Qt/Win32 (e.g. endpoint security software) restricting
    keyboard input specifically for a freshly-spawned child process. This
    process (the main v2 shell) is proven to receive keyboard input
    normally, so the one-time setup happens here instead of fighting
    cross-process focus in the child. Returns True once config.json is
    known-valid (existing or freshly saved); False if the user cancels.
    """
    from config_loader import ConfigManager, create_config_setup_dialog  # type: ignore[import]
    from PyQt5.QtWidgets import QDialog

    paths = get_runtime_paths()
    config_manager = ConfigManager(config_dir=paths.src_v2_root)

    def _run_setup_dialog() -> bool:
        dialog = create_config_setup_dialog(config_manager)
        return dialog.exec_() == QDialog.Accepted

    if not config_manager.config_exists():
        if not _run_setup_dialog():
            return False

    try:
        config_manager.load_config()
        return True
    except Exception:
        if not _run_setup_dialog():
            return False
        try:
            config_manager.load_config()
            return True
        except Exception:
            return False


def _launch_qcontrol_subprocess() -> bool:
    import subprocess

    ensure_runtime_paths()
    paths = get_runtime_paths()

    if not _ensure_qcontrol_config_valid():
        return False

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    parts = [paths.src_v2_root]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)

    process = subprocess.Popen(
        [sys.executable, _qcontrol_entry_point()],
        cwd=paths.src_v2_root,
        env=env,
    )
    _allow_child_to_take_foreground(process.pid)
    return True


def _allow_child_to_take_foreground(pid: int) -> None:
    """Grant the just-spawned child process permission to bring its own
    windows to the foreground and receive real keyboard focus.

    ART Q Control runs as a separate OS process (see module docstring), so
    Windows' anti-focus-stealing protection stops its dialogs from ever
    getting real keyboard focus by default — the window appears on screen,
    but keystrokes keep going to whichever window the user was already in.
    (raise_()/activateWindow() alone, tried first, don't fix this: they
    call the same restricted API from the wrong side.)

    AllowSetForegroundWindow(pid), called by the parent process for a
    specific child it just spawned, is the Microsoft-documented mechanism
    for handing off focus in exactly this situation — the same one used by
    Windows Explorer and installers when launching an app, not the broad
    AllowSetForegroundWindow(ASFW_ANY) call that lets *any* process steal
    focus (the pattern security tooling actually flags).
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.user32.AllowSetForegroundWindow(pid)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def can_launch_tool(tool_id: str) -> bool:
    """Return True when a launcher (in-process or subprocess) exists for *tool_id*."""
    if tool_id == _QCONTROL_TOOL_ID:
        return _can_launch_qcontrol_subprocess()
    return tool_id in _INPROCESS_LAUNCHERS


def launch_tool(tool_id: str) -> ToolLaunchResult:
    """Launch a tool by ID.

    ART Q Control launches in its own subprocess (legacy code needs process
    isolation — see module docstring). Every other tool launches as a window
    inside the current QApplication.
    """
    if tool_id == _QCONTROL_TOOL_ID:
        if not _can_launch_qcontrol_subprocess():
            return ToolLaunchResult(
                launched=False,
                message="ART Q Control entry point not found.",
            )
        try:
            if not _launch_qcontrol_subprocess():
                return ToolLaunchResult(
                    launched=False,
                    message="ART Q Control configuration setup was cancelled.",
                )
            return ToolLaunchResult(launched=True, message="ART Q Control subprocess launched.")
        except Exception as exc:
            return ToolLaunchResult(
                launched=False,
                message=f"Subprocess launch failed for '{tool_id}': {exc}",
            )

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


# Made with Bob
