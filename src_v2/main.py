"""
V2 application entry point.

This module is intentionally isolated from the production-ready `src/` tree.
Running this file opens the unified responsive v2 main menu first, and each
tool then launches from duplicated files inside `src_v2/`.
"""

import os
import sys


def _src_v2_root() -> str:
    """Return the absolute path to the src_v2 directory."""
    return os.path.dirname(os.path.abspath(__file__))


def _art_q_control_dir() -> str:
    """Return the ART Q Control directory inside src_v2."""
    return os.path.join(_src_v2_root(), "ART Q Control")


def _ensure_import_paths() -> None:
    """Ensure src_v2 paths are available for runtime imports."""
    root = _src_v2_root()
    control_dir = _art_q_control_dir()

    for path in (root, control_dir):
        if path not in sys.path:
            sys.path.insert(0, path)


def launch_main_menu() -> None:
    """Launch the unified responsive v2 main menu."""
    import os
    _ensure_import_paths()

    from utils.crash_handler import install_crash_handler
    install_crash_handler()

    from ui.main_menu import launch_v2_main_menu
    launch_v2_main_menu()

    # app.exec_() has returned — the last window was closed.
    # Force-exit immediately so background threads (QThread workers,
    # timers, etc.) do not keep the process alive in the terminal.
    os._exit(0)


if __name__ == "__main__":
    launch_main_menu()


# Made with Bob
