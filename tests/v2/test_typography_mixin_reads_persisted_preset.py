"""
Regression test for a significant, previously undiscovered bug: font preset
did not survive a fresh window construction (reopen, or a new subprocess for
ART Q Control), for ANY v2 tool — not just the ones with no-op
apply_typography() fixed earlier in this session.

Root cause: the real Settings dialog (ui/settings_dialog.py
_save_preset_to_config) persists the chosen preset via
config.manager.get_config_manager().set("ui_settings.font_preset", ...) —
i.e. into src_v2/config.json. But V2TypographyMixin.__init__ (the code that
determines the STARTING preset for every freshly-constructed window) read
from a completely different, unrelated file: ui.settings.SettingsManager,
which defaults to "<cwd>/settings.json" — a file the real Settings dialog
never writes to. Live, in-memory signal updates on already-open windows
still worked (that path never touched either file), which is why this went
unnoticed: everything looked fine as long as you didn't close and reopen a
tool after changing the font preset.

Fix: V2TypographyMixin.__init__ now reads the starting preset via
config.manager (the same source the Settings dialog actually writes to).
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication, QWidget

from utils.runtime import ensure_runtime_paths
from ui.typography_mixin import V2TypographyMixin

_qapp = None


def _app():
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance() or QApplication(sys.argv)
        ensure_runtime_paths()
    return _qapp


class _Probe(QWidget, V2TypographyMixin):
    def __init__(self):
        super().__init__()
        V2TypographyMixin.__init__(self)

    def apply_typography(self):
        pass


def test_fresh_widget_reads_preset_saved_via_the_real_settings_dialog_path():
    _app()
    from config.manager import get_config_manager

    try:
        get_config_manager().set("ui_settings.font_preset", "xlarge")

        probe = _Probe()

        assert probe.typography.preset.value == "xlarge", (
            f"fresh V2TypographyMixin widget did not pick up the preset saved via "
            f"config.manager; got {probe.typography.preset.value!r}"
        )
    finally:
        get_config_manager().set("ui_settings.font_preset", "normal")


if __name__ == "__main__":
    test_fresh_widget_reads_preset_saved_via_the_real_settings_dialog_path()
    print("OK: V2TypographyMixin reads the preset from the same place the Settings dialog writes it")
