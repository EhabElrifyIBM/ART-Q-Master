"""
Regression test for: ART Q Control's config dialog (and every other dialog
it shows) never received real keyboard focus. Confirmed via diagnostic:
disabling the Qt-level keyboard blocker entirely (ARTQ_DISABLE_KEYBOARD_BLOCKER=1)
did NOT fix it, and neither did QWidget.raise_()/activateWindow() from the
child process.

The parent process (main shell) calling
ctypes.windll.user32.AllowSetForegroundWindow(child_pid) immediately after
spawning the ART Q Control subprocess — the documented, targeted mechanism
for a parent to hand off foreground rights to a specific child it just
launched (what Explorer/installers do, not the broad ASFW_ANY variant that
security tooling flags) — is kept here as a harmless assist for whichever
dialogs the subprocess shows later. It did NOT, on its own, fix the
original "can't type in the config dialog" report (confirmed on the
reporting machine). The actual fix for that specific dialog is
_ensure_qcontrol_config_valid() running the setup in this process instead
— see test_qcontrol_config_validated_in_parent_process.py.
"""

import os
import sys
from unittest.mock import MagicMock, patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from utils import tool_launcher


def test_launch_qcontrol_subprocess_grants_foreground_to_the_new_child_pid():
    fake_process = MagicMock()
    fake_process.pid = 4321

    with patch("subprocess.Popen", return_value=fake_process) as mock_popen, \
         patch.object(tool_launcher, "_ensure_qcontrol_config_valid", return_value=True), \
         patch.object(tool_launcher, "_allow_child_to_take_foreground") as mock_allow:
        tool_launcher._launch_qcontrol_subprocess()

    mock_popen.assert_called_once()
    mock_allow.assert_called_once_with(4321)


def test_allow_child_to_take_foreground_calls_targeted_winapi_with_that_pid():
    with patch.object(sys, "platform", "win32"):
        import ctypes
        with patch.object(ctypes, "windll", create=True) as mock_windll:
            tool_launcher._allow_child_to_take_foreground(1234)
            mock_windll.user32.AllowSetForegroundWindow.assert_called_once_with(1234)


def test_allow_child_to_take_foreground_never_uses_asfw_any():
    """Guard against ever widening this back to
    AllowSetForegroundWindow(-1) (ASFW_ANY) — the broad, flaggable variant
    this fix specifically avoids."""
    import inspect
    source = inspect.getsource(tool_launcher._allow_child_to_take_foreground)
    assert "-1" not in source, (
        "must call AllowSetForegroundWindow(pid) with the specific child PID, "
        "not AllowSetForegroundWindow(-1) / ASFW_ANY"
    )


def test_allow_child_to_take_foreground_noop_on_non_windows():
    with patch.object(sys, "platform", "linux"):
        # Must not raise even though ctypes.windll doesn't exist on non-Windows
        tool_launcher._allow_child_to_take_foreground(1234)


def test_allow_child_to_take_foreground_swallows_errors():
    with patch.object(sys, "platform", "win32"):
        import ctypes
        with patch.object(ctypes, "windll", create=True) as mock_windll:
            mock_windll.user32.AllowSetForegroundWindow.side_effect = OSError("boom")
            tool_launcher._allow_child_to_take_foreground(1234)  # must not raise


if __name__ == "__main__":
    test_launch_qcontrol_subprocess_grants_foreground_to_the_new_child_pid()
    test_allow_child_to_take_foreground_calls_targeted_winapi_with_that_pid()
    test_allow_child_to_take_foreground_never_uses_asfw_any()
    test_allow_child_to_take_foreground_noop_on_non_windows()
    test_allow_child_to_take_foreground_swallows_errors()
    print("OK: ART Q Control's subprocess now gets a targeted foreground-focus handoff from its parent")
