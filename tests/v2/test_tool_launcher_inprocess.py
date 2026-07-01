"""
Regression test for Finding B (settings-propagation handover doc): in dev
mode (`python main.py`, not a frozen .exe), every sub-tool used to launch in
its own OS subprocess via subprocess.Popen. Each subprocess got its own
V2SettingsBus, so a tool already open could never hear about a settings
change made later in the main shell.

Fix: launch_tool() now uses the in-process launcher (same code path already
used for frozen builds) for the six v2-native tools, so they share the main
shell's QApplication and V2SettingsBus regardless of how the app was
started. ART Q Control is the one exception — see
test_qcontrol_subprocess_isolation.py for why it still needs its own
subprocess.
"""

import os
import sys
from unittest.mock import MagicMock, patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from utils import tool_launcher


def test_launch_tool_uses_inprocess_launcher():
    with patch.dict(tool_launcher._INPROCESS_LAUNCHERS, {"assigner": MagicMock()}), \
         patch("subprocess.Popen", side_effect=AssertionError("should not spawn a subprocess")):
        result = tool_launcher.launch_tool("assigner")

        assert result.launched is True
        tool_launcher._INPROCESS_LAUNCHERS["assigner"].assert_called_once()


def test_can_launch_tool_true_for_every_registered_tool():
    for tool_id in tool_launcher._INPROCESS_LAUNCHERS:
        assert tool_launcher.can_launch_tool(tool_id) is True
    assert tool_launcher.can_launch_tool("not_a_real_tool") is False


def test_tool_launcher_has_no_frozen_dev_split():
    assert not hasattr(tool_launcher, "_is_frozen"), (
        "tool_launcher should no longer distinguish frozen vs. dev-mode launching"
    )
    assert not hasattr(tool_launcher, "_launch_in_subprocess")


if __name__ == "__main__":
    test_launch_tool_uses_inprocess_launcher()
    test_can_launch_tool_true_for_every_registered_tool()
    test_tool_launcher_has_no_frozen_dev_split()
    print("OK: launch_tool() and can_launch_tool() use the in-process path for v2-native tools")
