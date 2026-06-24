"""
Crash handler for ART Q Master V2.

Scope: Ctrl+C (SIGINT) pressed in the terminal kills the process cleanly.

Nothing here touches window-close behaviour — Qt and tkinter handle their own
close events exactly as they always did.  This module only intercepts signals
that come from the terminal (SIGINT / Ctrl+C, SIGTERM, Windows SIGBREAK).

Usage
-----
Call install_crash_handler() once at process startup, then call
enable_qt_sigint_heartbeat(app) right after creating QApplication::

    install_crash_handler()
    app = QApplication(sys.argv)
    enable_qt_sigint_heartbeat(app)   # makes Ctrl+C work inside Qt event loop

WHY THE HEARTBEAT IS NEEDED
============================
On Windows, Qt's C++ event loop blocks Python indefinitely inside app.exec_().
Python can only deliver signals between its own bytecode instructions, so
SIGINT is received by the OS but Python never acts on it while Qt is spinning.
A 200 ms no-op QTimer forces Qt to hand control back to Python regularly so
the signal gets delivered within ~200 ms of pressing Ctrl+C.
"""

import os
import signal
import sys
import threading
from typing import List

# ──────────────────────────────────────────────────────────────────────────────
# Internal state
# ──────────────────────────────────────────────────────────────────────────────

_qt_heartbeat_timers: List = []  # Keeps QTimer references alive (prevents GC)


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def install_crash_handler() -> None:
    """Install SIGINT/SIGTERM handlers so Ctrl+C in the terminal exits cleanly.

    Call once near the very start of the entry point, before Qt or tkinter
    objects are created.
    """
    for sig in _handleable_signals():
        try:
            signal.signal(sig, _signal_handler)
        except (OSError, ValueError):
            pass  # Cannot set signal in a sub-thread — skip silently


def enable_qt_sigint_heartbeat(app=None) -> None:
    """Start a 200 ms QTimer so Python can deliver SIGINT while Qt is running.

    Call right after QApplication is created::

        app = QApplication(sys.argv)
        enable_qt_sigint_heartbeat(app)

    The ``app`` argument is accepted for readability but is not used; the timer
    attaches itself to the running Qt event loop automatically.
    """
    try:
        from PyQt5.QtCore import QTimer
        heartbeat = QTimer()
        heartbeat.setInterval(200)               # ms
        heartbeat.timeout.connect(lambda: None)  # no-op — just wakes Python
        heartbeat.start()
        _qt_heartbeat_timers.append(heartbeat)   # prevent GC
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# tkinter helper
# ──────────────────────────────────────────────────────────────────────────────

def attach_tkinter_sigint_guard(root) -> None:
    """Make Ctrl+C in the terminal close a tkinter window cleanly.

    Call after creating the Tk root but before mainloop()::

        root = tk.Tk()
        attach_tkinter_sigint_guard(root)
        root.mainloop()

    This only overrides the *signal* handler so Ctrl+C works.
    It does NOT touch the WM_DELETE_WINDOW protocol — closing the window
    with the X button behaves exactly as before.
    """
    def _on_sigint(signum, frame):
        _print(f"[ART Q Master] Signal {signal.Signals(signum).name} — closing")
        try:
            root.after(0, root.destroy)
        except Exception:
            try:
                root.destroy()
            except Exception:
                pass
        _hard_exit(delay_ms=400)

    for sig in _handleable_signals():
        try:
            signal.signal(sig, _on_sigint)
        except (OSError, ValueError):
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _handleable_signals() -> List[signal.Signals]:
    sigs = [signal.SIGINT, signal.SIGTERM]
    if hasattr(signal, "SIGBREAK"):       # Windows Ctrl+Break
        sigs.append(signal.SIGBREAK)      # type: ignore[attr-defined]
    return sigs


def _signal_handler(signum: int, frame) -> None:
    """Signal handler: print a message, ask Qt to quit, then hard-exit."""
    _print(f"\n[ART Q Master] {signal.Signals(signum).name} received — exiting")
    _quit_qt()
    _hard_exit(delay_ms=500)


def _quit_qt() -> None:
    """Ask the running QApplication to quit (safe from signal context)."""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QTimer
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)
    except Exception:
        pass


def _hard_exit(delay_ms: int = 500) -> None:
    """Force-exit after delay_ms if the event loop hasn't stopped yet."""
    def _exit():
        import time
        time.sleep(delay_ms / 1000.0)
        os._exit(0)

    t = threading.Thread(target=_exit, daemon=True, name="sigint-exit-watchdog")
    t.start()


def _print(msg: str) -> None:
    try:
        print(msg, flush=True)
    except Exception:
        pass


# Made with Bob
