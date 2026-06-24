"""
Entry point for the Monthly Case Merger tool.
Launched via:  python -m MonthlyMerger.run_monthly_merger
"""

import sys
from PyQt5.QtWidgets import QApplication


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    from MonthlyMerger.monthly_merger_window import MonthlyMergerWindow
    window = MonthlyMergerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
