"""
Regression test for: DailyMerger's apply_typography() was a no-op, and its
three child components (DailyFileListWidget, DailySummaryWidget,
DailyCalendarWidget + nested _MonthGrid) built fonts from a throwaway local
TypographySystem() (always NORMAL preset), never wired to V2TypographyMixin.
Font-preset changes had no visible effect on DailyMerger's own content,
live or on reopen.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication

from DailyMerger.daily_merger_window import DailyMergerWindow

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
    fl = w.file_list
    sm = w.summary
    cal = w.calendar
    sizes = {
        "fl.title": fl._title_lbl.font().pixelSize(),
        "fl.zip_toggle": fl._zip_toggle.font().pixelSize(),
        "fl.dz_title": fl._dz_title.font().pixelSize(),
        "fl.dz_sub": fl._dz_sub.font().pixelSize(),
        "fl.summary_label": fl._summary_label.font().pixelSize(),
        "sm.title": sm._title_lbl.font().pixelSize(),
        "sm.month_label": sm._month_label.font().pixelSize(),
        "sm.table": sm._table.font().pixelSize(),
        "sm.handlers_label": sm._handlers_label.font().pixelSize(),
        "sm.output_label": sm._output_label.font().pixelSize(),
        "sm.output_edit": sm._output_edit.font().pixelSize(),
        "cal.title": cal._title_lbl.font().pixelSize(),
        "cal.legend": cal._legend_lbl.font().pixelSize(),
        "cal.placeholder": cal._placeholder.font().pixelSize(),
    }
    return sizes


_keep_alive = []


def test_daily_merger_widgets_scale_with_persisted_preset():
    app = _app()
    try:
        _set_preset("small")
        w_small = DailyMergerWindow()
        _keep_alive.append(w_small)
        small_sizes = _sizes(w_small)

        _set_preset("xlarge")
        w_xl = DailyMergerWindow()
        _keep_alive.append(w_xl)
        xl_sizes = _sizes(w_xl)

        unchanged = [k for k in small_sizes if small_sizes[k] >= xl_sizes[k]]
        assert not unchanged, f"widgets that did not grow small->xlarge: {unchanged} ({small_sizes} vs {xl_sizes})"
    finally:
        _set_preset("normal")


def test_daily_merger_live_update_on_open_window():
    app = _app()
    from ui.services import get_v2_settings_bus
    bus = get_v2_settings_bus()

    try:
        _set_preset("normal")
        w = DailyMergerWindow()
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
    test_daily_merger_widgets_scale_with_persisted_preset()
    test_daily_merger_live_update_on_open_window()
    print("OK: DailyMerger typography applies on construction and live updates")
