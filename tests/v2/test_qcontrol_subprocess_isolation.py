"""
Regression test: ART Q Control (Dispatcher_v2 + its legacy Main.py /
Functions.py / CaseReviewer_v2.py / AutoSender_v2.py / CompaniesProcess_v2.py
dependents) calls sys.exit() / app.quit() throughout as internal control
flow. That was safe while it ran in its own OS subprocess (only that
subprocess died). Once tool_launcher started launching every tool
in-process (Finding B fix), those calls kill the single shared QApplication
— e.g. cancelling ART Q Control's config setup dialog took down the entire
v2 shell.

Fix: ART Q Control keeps launching in its own subprocess, like before. The
other six v2-native tools (Assigner, Merger, Archiver, DailyMerger,
MonthlyMerger, ReachRate) still launch in-process so live settings
propagation keeps working for them.
"""

import os
import sys
from unittest.mock import MagicMock, patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from utils import tool_launcher


def test_qcontrol_launches_via_subprocess_not_inprocess():
    with patch("subprocess.Popen") as mock_popen, \
         patch.object(tool_launcher, "_ensure_qcontrol_config_valid", return_value=True):
        result = tool_launcher.launch_tool("qcontrol")

        assert result.launched is True
        mock_popen.assert_called_once()


def test_other_tools_still_launch_inprocess():
    with patch.dict(tool_launcher._INPROCESS_LAUNCHERS, {"assigner": MagicMock()}), \
         patch("subprocess.Popen", side_effect=AssertionError("should not spawn a subprocess")):
        result = tool_launcher.launch_tool("assigner")

        assert result.launched is True
        tool_launcher._INPROCESS_LAUNCHERS["assigner"].assert_called_once()


def test_can_launch_tool_true_for_qcontrol():
    assert tool_launcher.can_launch_tool("qcontrol") is True


if __name__ == "__main__":
    test_qcontrol_launches_via_subprocess_not_inprocess()
    test_other_tools_still_launch_inprocess()
    test_can_launch_tool_true_for_qcontrol()
    print("OK: ART Q Control launches via subprocess; other tools stay in-process")
