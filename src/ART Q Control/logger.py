"""
logger.py — ART Q Master centralised logging
=============================================
Usage:
    from logger import log, set_monitor

    log("Case opened", "INFO")     # terminal only (unless monitor attached)
    log("Email sent", "SUCCESS")   # green in central log
    log("Not reached", "WARNING")  # orange in terminal + log
    log("Fatal error", "ERROR")    # red + bold in terminal + log

Call set_monitor(progress_monitor_instance) once the monitor dialog is open.
"""

import sys
from datetime import datetime

# Optional reference to a ProgressMonitor instance (set at runtime)
_monitor = None

# Terminal prefix symbols per level
_SYMBOLS = {
    "DEBUG":   "·",
    "INFO":    "›",
    "SUCCESS": "✓",
    "WARNING": "⚠",
    "ERROR":   "✗",
    "ETICKET": "⚡",
    "STEP":    "→",
}

# Which levels are printed to terminal (DEBUG is suppressed)
_TERMINAL_LEVELS = {"INFO", "SUCCESS", "WARNING", "ERROR", "ETICKET", "STEP"}


def set_monitor(monitor_instance):
    """Attach a ProgressMonitor so log() also writes to its central log panel."""
    global _monitor
    _monitor = monitor_instance


def clear_monitor():
    """Detach the monitor (e.g. when dialog closes)."""
    global _monitor
    _monitor = None


def log(message: str, level: str = "INFO"):
    """
    Emit a log message.

    Args:
        message: Human-readable message.
        level: One of DEBUG / INFO / SUCCESS / WARNING / ERROR / ETICKET / STEP.
               DEBUG messages are suppressed from terminal output.
    """
    level = level.upper()
    sym   = _SYMBOLS.get(level, "·")
    ts    = datetime.now().strftime("%H:%M:%S")

    # ── Terminal ────────────────────────────────────────────────────────────
    if level in _TERMINAL_LEVELS:
        line = f"[{ts}] {sym} [{level}] {message}"
        print(line, file=sys.stdout, flush=True)

    # ── Central log panel ───────────────────────────────────────────────────
    if _monitor is not None:
        try:
            _monitor.log_message(message, level)
        except Exception:
            pass


# Convenience shortcuts
def debug(msg: str):   log(msg, "DEBUG")
def info(msg: str):    log(msg, "INFO")
def success(msg: str): log(msg, "SUCCESS")
def warning(msg: str): log(msg, "WARNING")
def error(msg: str):   log(msg, "ERROR")
def step(msg: str):    log(msg, "STEP")
def eticket(msg: str): log(msg, "ETICKET")
