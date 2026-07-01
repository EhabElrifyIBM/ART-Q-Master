import os

from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox

_blocker_instance = None
_activator_instance = None


class _ApplicationKeyboardBlocker(QObject):
    """
    Application-level keyboard blocker installed on QApplication.
    Passes key events only to text-input widgets; suppresses them everywhere else.
    This prevents accidental button activation when the user types in another window
    and the ART Q Control window inadvertently has focus.
    """

    _TEXT_INPUT_TYPES = (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox)

    def eventFilter(self, obj, event):
        event_type = event.type()
        if event_type in (QEvent.KeyPress, QEvent.KeyRelease, QEvent.ShortcutOverride):
            if isinstance(obj, self._TEXT_INPUT_TYPES):
                return False  # let text-input widgets receive keyboard events normally
            return True  # block keyboard events for buttons, dialogs, labels, etc.
        return False  # all non-keyboard events pass through unchanged


class _WindowActivator(QObject):
    """
    Application-level event filter that brings every new top-level window in
    this process to the foreground as it's shown.

    ART Q Control runs in its own OS subprocess (see utils/tool_launcher.py)
    so it can call sys.exit()/QApplication.quit() internally without taking
    down the shared v2 shell.

    NOTE on the "can't type in ART Q Control" investigation: this alone does
    NOT fix that — confirmed by testing. Two other cross-process focus
    APIs were also tried and reverted: one from the parent process granting
    this process permission to become foreground, and one from here that
    additionally merged the input queues of this thread and whichever
    thread owned the keyboard. Neither fixed it: real focus was confirmed
    (the field showed a genuine blinking text cursor) yet zero keystrokes
    ever arrived. That strongly suggests something below Qt/the Windows API
    is intercepting keyboard input for this specific subprocess (e.g.
    endpoint security software — the queue-merging technique in particular
    is also what that kind of software watches for as a keylogging
    indicator), so it was removed rather than kept for no benefit. The
    actual fix for the config dialog specifically is in
    utils/tool_launcher.py: do that one-time setup in the main shell
    process, which is proven to receive keyboard input normally, instead of
    in this subprocess. raise_()/activateWindow() are kept here only
    because they're harmless and still worth doing for window
    ordering/visibility.
    """

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Show and hasattr(obj, "isWindow") and obj.isWindow():
            obj.raise_()
            obj.activateWindow()
        return False  # never consume Show events — just piggyback on them


def install_keyboard_blocker():
    """
    Install the application-level keyboard blocker and window activator.
    Must be called after QApplication has been created.
    Safe to call multiple times — only installs once per process.

    Diagnostic escape hatch: set ARTQ_DISABLE_KEYBOARD_BLOCKER=1 in the
    environment to skip installing the blocker (the window activator still
    installs). Used to isolate whether a "can't type" report is caused by
    this Qt-level filter rejecting keystrokes it shouldn't, versus Windows
    never routing real keystrokes to this process's window at all — the
    blocker can only be the cause of the former, not the latter.
    """
    global _blocker_instance, _activator_instance
    app = QApplication.instance()
    if app is None:
        return
    if _blocker_instance is None and not os.environ.get("ARTQ_DISABLE_KEYBOARD_BLOCKER"):
        _blocker_instance = _ApplicationKeyboardBlocker()
        app.installEventFilter(_blocker_instance)
        print("[INFO] Keyboard blocker installed — keyboard input restricted to text fields only")
    if _activator_instance is None:
        _activator_instance = _WindowActivator()
        app.installEventFilter(_activator_instance)
        print("[INFO] Window activator installed — new windows now receive real keyboard focus")


def uninstall_keyboard_blocker():
    """Remove the keyboard blocker and window activator (call this only if
    keyboard access needs to be restored)."""
    global _blocker_instance, _activator_instance
    app = QApplication.instance()
    if app is None:
        return
    if _blocker_instance is not None:
        app.removeEventFilter(_blocker_instance)
        _blocker_instance = None
        print("[INFO] Keyboard blocker removed")
    if _activator_instance is not None:
        app.removeEventFilter(_activator_instance)
        _activator_instance = None
        print("[INFO] Window activator removed")
