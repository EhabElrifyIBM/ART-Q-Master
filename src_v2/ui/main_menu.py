"""
Unified v2 main menu entry.

This menu uses the shared Phase 6 shell so running src_v2/main.py opens the
responsive launcher first instead of starting ART Q Control directly.
"""

import sys

from PyQt5.QtWidgets import QApplication

from ui.shell import UnifiedToolShell
from ui.settings import get_settings_manager, integrate_with_v2_settings_bus
from utils.runtime import ensure_runtime_paths
from utils.tool_registry import get_shell_cards
from utils.crash_handler import enable_qt_sigint_heartbeat


class V2MainMenu(UnifiedToolShell):
    """Responsive unified launcher window for all duplicated v2 tools with full accessibility support."""

    def __init__(self):
        super().__init__(
            title="ART Q Master V2",
            subtitle="",  # Clean, professional appearance - no technical details
            tools=get_shell_cards(),
        )
        # Accessibility is handled by parent UnifiedToolShell


def launch_v2_main_menu() -> int:
    """Launch the unified v2 main menu and start the Qt event loop."""
    ensure_runtime_paths()
    app = QApplication.instance() or QApplication(sys.argv)

    # Enable Ctrl+C in terminal while Qt event loop is running (Windows fix)
    enable_qt_sigint_heartbeat(app)

    # CRITICAL: Wire SettingsManager to V2SettingsBus for reactive settings propagation
    # This enables all settings changes in the dialog to automatically update UI components
    # Must be called after QApplication exists but before any windows are created
    settings_manager = get_settings_manager()
    integrate_with_v2_settings_bus(settings_manager)

    window = V2MainMenu()
    window.show()
    app._art_q_v2_main_menu = window  # type: ignore[attr-defined]

    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(launch_v2_main_menu())

# Made with Bob
