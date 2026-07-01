"""
Regression test for the actual fix to "can't type in ART Q Control's config
dialog": ART Q Control's one-time config setup now happens in the main v2
shell process — proven to receive keyboard input normally — instead of in
ART Q Control's own subprocess, whose windows never reliably got real
keyboard focus no matter which OS-level focus-forcing technique was tried
(raise_/activateWindow, AllowSetForegroundWindow from the parent,
AttachThreadInput from the child — confirmed on the reporting machine that
none of them worked: a field could show a genuine blinking text cursor
while zero keystrokes ever arrived).

_ensure_qcontrol_config_valid() reuses ART Q Control's own ConfigManager /
create_config_setup_dialog (config_loader.py) so there's exactly one
validation implementation, just invoked from a different process.
"""

import os
import sys
from unittest.mock import MagicMock, patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from utils import tool_launcher


def _patch_config_loader(config_exists, load_config_side_effect, dialog_accepted):
    fake_config_manager_cls = MagicMock()
    fake_config_manager = fake_config_manager_cls.return_value
    fake_config_manager.config_exists.return_value = config_exists
    fake_config_manager.load_config.side_effect = load_config_side_effect

    fake_dialog = MagicMock()
    from PyQt5.QtWidgets import QDialog
    fake_dialog.exec_.return_value = QDialog.Accepted if dialog_accepted else QDialog.Rejected
    fake_create_dialog = MagicMock(return_value=fake_dialog)

    fake_module = MagicMock()
    fake_module.ConfigManager = fake_config_manager_cls
    fake_module.create_config_setup_dialog = fake_create_dialog
    return fake_module, fake_config_manager, fake_dialog


def test_config_already_valid_skips_the_dialog_entirely():
    fake_module, fake_config_manager, fake_dialog = _patch_config_loader(
        config_exists=True, load_config_side_effect=None, dialog_accepted=True
    )
    with patch.dict(sys.modules, {"config_loader": fake_module}):
        result = tool_launcher._ensure_qcontrol_config_valid()

    assert result is True
    fake_dialog.exec_.assert_not_called()


def test_missing_config_shows_dialog_and_returns_true_when_accepted():
    fake_module, fake_config_manager, fake_dialog = _patch_config_loader(
        config_exists=False, load_config_side_effect=None, dialog_accepted=True
    )
    with patch.dict(sys.modules, {"config_loader": fake_module}):
        result = tool_launcher._ensure_qcontrol_config_valid()

    assert result is True
    fake_dialog.exec_.assert_called_once()


def test_missing_config_returns_false_when_dialog_cancelled():
    fake_module, fake_config_manager, fake_dialog = _patch_config_loader(
        config_exists=False, load_config_side_effect=None, dialog_accepted=False
    )
    with patch.dict(sys.modules, {"config_loader": fake_module}):
        result = tool_launcher._ensure_qcontrol_config_valid()

    assert result is False


def test_invalid_existing_config_reshows_dialog():
    # First load_config() call fails validation (triggers the setup
    # dialog); second call (after the user fixes it) succeeds.
    fake_module, fake_config_manager, fake_dialog = _patch_config_loader(
        config_exists=True, load_config_side_effect=[ValueError("bad path"), None], dialog_accepted=True
    )
    with patch.dict(sys.modules, {"config_loader": fake_module}):
        result = tool_launcher._ensure_qcontrol_config_valid()

    assert result is True
    fake_dialog.exec_.assert_called_once()


def test_launch_tool_reports_cancelled_not_launched_when_setup_is_cancelled():
    with patch.object(tool_launcher, "_ensure_qcontrol_config_valid", return_value=False), \
         patch("subprocess.Popen") as mock_popen:
        result = tool_launcher.launch_tool("qcontrol")

    assert result.launched is False
    assert "cancelled" in result.message.lower()
    mock_popen.assert_not_called()


if __name__ == "__main__":
    test_config_already_valid_skips_the_dialog_entirely()
    test_missing_config_shows_dialog_and_returns_true_when_accepted()
    test_missing_config_returns_false_when_dialog_cancelled()
    test_invalid_existing_config_reshows_dialog()
    test_launch_tool_reports_cancelled_not_launched_when_setup_is_cancelled()
    print("OK: ART Q Control config validation/setup now happens in the main shell process before the subprocess is spawned")
