"""Subprocess entry point for the Merger tool (dev mode)."""
import sys
import os

_src_v2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src_v2 not in sys.path:
    sys.path.insert(0, _src_v2)

from PyQt5.QtWidgets import QApplication
from Merger.merger_window import MergerWindow


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
