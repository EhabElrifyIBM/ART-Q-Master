"""
Test that MonthlyMergerWindow subscribes to font_preset_changed like every
other v2 tool window (Merger, Archiver, DailyMerger, ReachRateCalculator).

Regression test for: MonthlyMerger never wired font_preset_changed, so
font-size changes made in Settings never reached an already-open Monthly
Case Merger window.
"""

import os
import sys
from unittest.mock import patch

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication

from ui.services import get_v2_settings_bus
from MonthlyMerger.monthly_merger_window import MonthlyMergerWindow


def test_monthly_merger_connects_font_preset_changed():
    app = QApplication.instance() or QApplication(sys.argv)
    settings_bus = get_v2_settings_bus()

    with patch.object(MonthlyMergerWindow, "apply_typography", autospec=True) as mock_apply:
        window = MonthlyMergerWindow()
        try:
            settings_bus.font_preset_changed.emit("large")
            app.processEvents()
            assert mock_apply.called, (
                "MonthlyMergerWindow did not call apply_typography() when "
                "font_preset_changed was emitted"
            )
        finally:
            window.close()
            window.deleteLater()

    print("OK: MonthlyMergerWindow subscribes to font_preset_changed")


if __name__ == "__main__":
    test_monthly_merger_connects_font_preset_changed()
