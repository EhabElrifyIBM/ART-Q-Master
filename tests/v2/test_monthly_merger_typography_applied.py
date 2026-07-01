"""
Regression test for: MonthlyMerger's apply_typography() was a no-op, and its
labels were built from a throwaway local TypographySystem() (always NORMAL
preset) instead of the reactive self.typography from V2TypographyMixin. As a
result font-preset changes had zero visible effect — not live, and not even
on a fresh reopen with a different persisted preset.

This test constructs the window at the 'small' and 'xlarge' presets and
checks that its own labels/table/log-toggle button actually differ in size.
(PrimaryButton/SecondaryButton instances already self-update via
ModernButton's own font_preset_changed subscription, so they're not
re-checked here.)
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication

from MonthlyMerger.monthly_merger_window import MonthlyMergerWindow


_qapp = None  # keep QApplication alive across test functions (avoids sip cleanup cascading into the settings bus)


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


def _label_sizes(w):
    return {
        "title": w._title_lbl.font().pixelSize(),
        "subtitle": w._subtitle_lbl.font().pixelSize(),
        "files_section_title": w._files_section_lbl.font().pixelSize(),
        "month_lbl": w._month_lbl.font().pixelSize(),
        "table": w._table.font().pixelSize(),
        "output_label": w._output_label.font().pixelSize(),
        "output_edit": w._output_edit.font().pixelSize(),
        "log_title": w._log_title_lbl.font().pixelSize(),
        "clear_log_btn": w._clear_log_btn.font().pixelSize(),
        "log_toggle_btn": w._log_toggle_btn.font().pixelSize(),
        "dz_title": w._dz_title.font().pixelSize(),
        "dz_sub": w._dz_sub.font().pixelSize(),
        "summary_lbl": w._summary_lbl.font().pixelSize(),
    }


_keep_alive = []  # PyQt/sip deletes the C++ side once a widget is unreferenced


def test_monthly_merger_labels_scale_with_persisted_preset():
    app = _app()

    try:
        _set_preset("small")
        w_small = MonthlyMergerWindow()
        _keep_alive.append(w_small)
        small_sizes = _label_sizes(w_small)

        _set_preset("xlarge")
        w_xl = MonthlyMergerWindow()
        _keep_alive.append(w_xl)
        xl_sizes = _label_sizes(w_xl)

        unchanged = [k for k in small_sizes if small_sizes[k] >= xl_sizes[k]]
        assert not unchanged, f"widgets that did not grow from small->xlarge: {unchanged} ({small_sizes} vs {xl_sizes})"
    finally:
        _set_preset("normal")


def test_monthly_merger_live_update_on_open_window():
    app = _app()
    from ui.services import get_v2_settings_bus
    bus = get_v2_settings_bus()

    try:
        _set_preset("normal")
        w = MonthlyMergerWindow()
        w.show()
        app.processEvents()
        before = _label_sizes(w)

        bus.font_preset_changed.emit("xlarge")
        app.processEvents()
        after = _label_sizes(w)

        w.close()
        unchanged = [k for k in before if before[k] >= after[k]]
        assert not unchanged, f"widgets that did not update live: {unchanged} ({before} vs {after})"
    finally:
        bus.font_preset_changed.emit("normal")
        _set_preset("normal")


if __name__ == "__main__":
    test_monthly_merger_labels_scale_with_persisted_preset()
    test_monthly_merger_live_update_on_open_window()
    print("OK: MonthlyMerger typography applies on construction and live updates")
