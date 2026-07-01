"""
Regression test for: Archiver's apply_typography() was a no-op, and its two
child components (FileSelectorWidget, AnalysisViewWidget — plus AnalysisView's
nested _StatCard) built fonts from a throwaway local TypographySystem()
(always NORMAL preset), never wired to V2TypographyMixin at all. Font-preset
changes had no visible effect on Archiver's own content, live or on reopen.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication

from Archiver.archiver_window import ArchiverWindow

_qapp = None


def _app():
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


def _set_preset(preset: str) -> None:
    # Matches the real Settings dialog's save path (ui/settings_dialog.py
    # _save_preset_to_config), not ui.settings.SettingsManager.
    from config.manager import get_config_manager
    get_config_manager().set("ui_settings.font_preset", preset)


def _sizes(w):
    fs = w.file_selector
    av = w.analysis_view
    return {
        "fs.drop_text": fs._drop_text_lbl.font().pixelSize(),
        "fs.or_label": fs._or_lbl.font().pixelSize(),
        "fs.file_label": fs._file_label.font().pixelSize(),
        "fs.file_meta_label": fs._file_meta_label.font().pixelSize(),
        "fs.recent_label": fs._recent_label.font().pixelSize(),
        "fs.recent_list": fs._recent_list.font().pixelSize(),
        "av.title_label": av._title_label.font().pixelSize(),
        "av.summary_label": av._summary_label.font().pixelSize(),
        "av.stat_cases.value": av._stat_cases._value_label.font().pixelSize(),
        "av.stat_cases.desc": av._stat_cases._desc_label.font().pixelSize(),
    }


_keep_alive = []


def test_archiver_widgets_scale_with_persisted_preset():
    app = _app()
    try:
        _set_preset("small")
        w_small = ArchiverWindow()
        _keep_alive.append(w_small)
        small_sizes = _sizes(w_small)

        _set_preset("xlarge")
        w_xl = ArchiverWindow()
        _keep_alive.append(w_xl)
        xl_sizes = _sizes(w_xl)

        unchanged = [k for k in small_sizes if small_sizes[k] >= xl_sizes[k]]
        assert not unchanged, f"widgets that did not grow small->xlarge: {unchanged} ({small_sizes} vs {xl_sizes})"
    finally:
        _set_preset("normal")


def test_archiver_live_update_on_open_window():
    app = _app()
    from ui.services import get_v2_settings_bus
    bus = get_v2_settings_bus()

    try:
        _set_preset("normal")
        w = ArchiverWindow()
        w.show()
        app.processEvents()
        before = _sizes(w)

        bus.font_preset_changed.emit("xlarge")
        app.processEvents()
        after = _sizes(w)

        w.close()
        unchanged = [k for k in before if before[k] >= after[k]]
        assert not unchanged, f"widgets that did not update live: {unchanged} ({before} vs {after})"
    finally:
        bus.font_preset_changed.emit("normal")
        _set_preset("normal")


if __name__ == "__main__":
    test_archiver_widgets_scale_with_persisted_preset()
    test_archiver_live_update_on_open_window()
    print("OK: Archiver typography applies on construction and live updates")
