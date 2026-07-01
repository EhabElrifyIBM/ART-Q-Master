"""
Daily Case Merger — standalone entry point.

Run via:
    python -m DailyMerger.run_daily_merger
"""

import sys
import os

# Ensure src_v2 is on path when run standalone
_here = os.path.dirname(os.path.abspath(__file__))
_src_v2 = os.path.dirname(_here)
if _src_v2 not in sys.path:
    sys.path.insert(0, _src_v2)

from PyQt5.QtWidgets import QApplication
from DailyMerger.daily_merger_window import DailyMergerWindow


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = DailyMergerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
