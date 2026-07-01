"""
Regression test for: the "processing complete" QMessageBox popups in
AutoSender_v2, CaseReviewer_v2, and CompaniesProcess_v2 were built with
QMessageBox.information(...) / a bare QMessageBox() with no stylesheet at
all, so they always rendered in default OS/Qt light styling regardless of
the app's theme setting (dark mode included). This is independent of
process isolation — it would be true even running in the main shell's
process.

Fix: each completion dialog now applies a stylesheet derived from the
current v2_settings_bus theme, matching how the rest of ART Q Control's
"Modern*Dialog" classes already look.
"""

import os
import sys
from unittest.mock import patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
control_dir = os.path.join(src_v2_dir, "ART Q Control")
for p in (src_v2_dir, control_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from PyQt5.QtWidgets import QApplication, QMessageBox

_qapp = None


def _app():
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


class _StubConfigManager:
    """Avoids the real (interactive, disk-touching) config setup dialog during import."""

    _VALUES = {
        ("agent_settings", "agent_name"): "Test Agent",
    }

    def get_value(self, section, key):
        return self._VALUES.get((section, key), "test")


def _stub_init_config():
    return _StubConfigManager()


def _import_without_config_dialog(module_name):
    """Import an ART Q Control tool module with config_loader.init_config stubbed
    out, so importing it never opens the real (interactive) setup dialog or
    touches the real config.json on disk."""
    import config_loader
    with patch.object(config_loader, "init_config", _stub_init_config):
        return __import__(module_name)


def _capture_styled_messagebox(call):
    """Call `call()` with QMessageBox.exec_ intercepted; return the instance's stylesheet."""
    captured = {}

    original_exec = QMessageBox.exec_

    def fake_exec(self):
        captured["stylesheet"] = self.styleSheet()
        return QMessageBox.Ok

    with patch.object(QMessageBox, "exec_", fake_exec):
        call()

    return captured.get("stylesheet")


def test_autosender_completion_dialog_is_themed():
    _app()
    from ui.services import get_v2_settings_bus
    bus = get_v2_settings_bus()
    try:
        bus.set_theme("dark")
        AutoSender_v2 = _import_without_config_dialog("AutoSender_v2")
        stylesheet = _capture_styled_messagebox(lambda: AutoSender_v2.show_completion_dialog(5, 5))
        assert stylesheet, "AutoSender completion dialog has no stylesheet — not theme-aware"
        assert "#161616" in stylesheet or "161616" in stylesheet.lower() or "0f172a" not in stylesheet, (
            "sanity check: stylesheet should reference dark-theme colors"
        )
    finally:
        bus.set_theme("light")


def test_casereviewer_completion_dialog_is_themed():
    _app()
    from ui.services import get_v2_settings_bus
    bus = get_v2_settings_bus()
    try:
        bus.set_theme("dark")
        CaseReviewer_v2 = _import_without_config_dialog("CaseReviewer_v2")
        stylesheet = _capture_styled_messagebox(lambda: CaseReviewer_v2.show_completion_dialog(5, 5))
        assert stylesheet, "CaseReviewer completion dialog has no stylesheet — not theme-aware"
    finally:
        bus.set_theme("light")


def test_companies_process_completion_dialog_is_themed():
    _app()
    from ui.services import get_v2_settings_bus
    bus = get_v2_settings_bus()
    try:
        bus.set_theme("dark")
        CompaniesProcess_v2 = _import_without_config_dialog("CompaniesProcess_v2")
        stylesheet = _capture_styled_messagebox(CompaniesProcess_v2.show_companies_completion_dialog)
        assert stylesheet, "CompaniesProcess completion dialog has no stylesheet — not theme-aware"
    finally:
        bus.set_theme("light")


if __name__ == "__main__":
    test_autosender_completion_dialog_is_themed()
    test_casereviewer_completion_dialog_is_themed()
    test_companies_process_completion_dialog_is_themed()
    print("OK: all 3 ART Q Control completion dialogs are theme-aware")
