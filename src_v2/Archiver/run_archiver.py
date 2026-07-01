"""
Case Archiver — standalone entry point.

Run via:
    python -m Archiver.run_archiver
"""

import sys
import os

# Ensure src_v2 is on path when run standalone
_here = os.path.dirname(os.path.abspath(__file__))
_src_v2 = os.path.dirname(_here)
if _src_v2 not in sys.path:
    sys.path.insert(0, _src_v2)

from PyQt5.QtWidgets import QApplication
from Archiver.archiver_window import ArchiverWindow


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
