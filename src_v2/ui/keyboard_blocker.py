from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtWidgets import QApplication, QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox

_blocker_instance = None


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


def install_keyboard_blocker():
    """
    Install the application-level keyboard blocker.
    Must be called after QApplication has been created.
    Safe to call multiple times — only installs once per process.
    """
    global _blocker_instance
    app = QApplication.instance()
    if app is not None and _blocker_instance is None:
        _blocker_instance = _ApplicationKeyboardBlocker()
        app.installEventFilter(_blocker_instance)
        print("[INFO] Keyboard blocker installed — keyboard input restricted to text fields only")


def uninstall_keyboard_blocker():
    """Remove the keyboard blocker (call this only if keyboard access needs to be restored)."""
    global _blocker_instance
    app = QApplication.instance()
    if app is not None and _blocker_instance is not None:
        app.removeEventFilter(_blocker_instance)
        _blocker_instance = None
        print("[INFO] Keyboard blocker removed")
