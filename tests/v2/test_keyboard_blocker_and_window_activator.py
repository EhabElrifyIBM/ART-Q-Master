"""
Regression tests for ui/keyboard_blocker.py.

Bug investigation history (see utils/tool_launcher.py for the actual fix
that resulted): ART Q Control runs in its own OS subprocess so its legacy
sys.exit()/app.quit() calls can't take down the shared v2 shell. Typing into
its config setup dialog's text fields did nothing. Diagnosed step by step:
  - Disabling this module's keyboard blocker (ARTQ_DISABLE_KEYBOARD_BLOCKER=1)
    did NOT fix it — rules out this filter as the cause.
  - Instrumenting every keyPressEvent showed literally zero KeyPress events
    ever arrived at any field, across repeated real attempts, even though
    mouse clicks visibly gave fields focus (the text cursor genuinely
    blinked — real Qt focus, not just a hover highlight).
  - raise_()/activateWindow(), AllowSetForegroundWindow(child_pid) from the
    parent, and AttachThreadInput+SetForegroundWindow from the child were
    all tried. None fixed it. AttachThreadInput was reverted rather than
    kept for no benefit, since it's also literally the technique some
    endpoint security software watches for as a keylogging indicator.

The actual fix lives in utils/tool_launcher.py: do the one-time ART Q
Control config setup in the main shell process (proven to receive keyboard
input normally) before ever spawning the subprocess, instead of continuing
to fight cross-process focus from inside it. These tests just cover this
module's own two event filters in isolation.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_v2_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "src_v2"))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PyQt5.QtTest import QTest

_qapp = None


def _app():
    global _qapp
    if _qapp is None:
        _qapp = QApplication.instance() or QApplication(sys.argv)
    return _qapp


def _build_dialog():
    dlg = QDialog()
    layout = QVBoxLayout(dlg)
    edit = QLineEdit(dlg)
    btn = QPushButton("Delete Everything", dlg)
    layout.addWidget(edit)
    layout.addWidget(btn)
    dlg.edit = edit
    dlg.btn = btn
    return dlg


def test_typing_in_a_text_field_still_works():
    _app()
    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()

    dlg = _build_dialog()
    dlg.show()
    dlg.edit.setFocus()
    _app().processEvents()

    QTest.keyClicks(dlg.edit, "hello")
    _app().processEvents()

    assert dlg.edit.text() == "hello"
    dlg.close()


def test_enter_and_space_do_not_trigger_a_focused_button():
    """The whole point of the original keyboard blocker: stray Enter/Space
    must not activate a button."""
    _app()
    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()

    dlg = _build_dialog()
    clicked = {"count": 0}
    dlg.btn.clicked.connect(lambda: clicked.__setitem__("count", clicked["count"] + 1))
    dlg.show()
    dlg.btn.setFocus()
    _app().processEvents()

    QTest.keyClick(dlg.btn, Qt.Key_Return)
    QTest.keyClick(dlg.btn, Qt.Key_Space)
    _app().processEvents()

    assert clicked["count"] == 0, "a stray Enter/Space activated the button — keyboard blocker regressed"
    dlg.close()


def test_new_window_gets_activated_when_shown():
    _app()
    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()

    dlg = _build_dialog()
    activate_calls = {"count": 0}
    original_activate = dlg.activateWindow

    def spy_activate():
        activate_calls["count"] += 1
        return original_activate()

    dlg.activateWindow = spy_activate
    dlg.show()
    _app().processEvents()

    assert activate_calls["count"] >= 1, "window activator did not call activateWindow() on Show"
    dlg.close()


def test_window_activator_does_not_cause_a_modal_dialog_to_self_reject():
    """Regression test for a real bug: an earlier version of the window
    activator toggled Qt.WindowStaysOnTopHint to force focus. QDialog.exec_()
    treats the native-window recreation that setWindowFlags() triggers as
    the dialog being closed, so it silently self-rejected within ~0.1s of
    opening — this is exactly what caused ART Q Control to "crash back to
    the main menu" immediately after showing the config setup dialog."""
    _app()
    from ui.keyboard_blocker import install_keyboard_blocker
    install_keyboard_blocker()

    dlg = _build_dialog()
    from PyQt5.QtCore import QTimer
    import time

    QTimer.singleShot(400, dlg.close)
    start = time.time()
    dlg.exec_()
    elapsed = time.time() - start

    assert elapsed > 0.3, (
        f"dialog.exec_() returned after only {elapsed:.3f}s instead of waiting "
        f"for the 0.4s timer — the window activator is self-rejecting the dialog"
    )


def test_disable_env_var_skips_only_the_blocker_not_the_activator():
    """ARTQ_DISABLE_KEYBOARD_BLOCKER=1 is a diagnostic escape hatch to
    isolate whether a "can't type" report is this Qt-level filter rejecting
    keystrokes it shouldn't, vs. Windows never routing real keystrokes to
    the window at all (which the blocker can't be the cause of)."""
    _app()
    import ui.keyboard_blocker as kb

    kb.uninstall_keyboard_blocker()
    os.environ["ARTQ_DISABLE_KEYBOARD_BLOCKER"] = "1"
    try:
        kb.install_keyboard_blocker()
        assert kb._blocker_instance is None, "blocker should be skipped when the env var is set"
        assert kb._activator_instance is not None, "activator should still install"
    finally:
        del os.environ["ARTQ_DISABLE_KEYBOARD_BLOCKER"]
        kb.uninstall_keyboard_blocker()
        kb.install_keyboard_blocker()  # restore normal state for any tests that run after this one


def test_no_raw_winapi_or_focus_stealing_calls():
    """Guard against reintroducing ctypes/WinAPI foreground-stealing calls
    (SetForegroundWindow, AttachThreadInput) in this module — tried twice,
    didn't fix the underlying problem, and is exactly the kind of pattern
    security tooling flags. The real fix belongs in utils/tool_launcher.py
    (do the keyboard-heavy work in the process that already works), not
    here."""
    import ui.keyboard_blocker as kb
    import inspect

    source = inspect.getsource(kb)
    for banned in ("ctypes", "windll", "win32gui", "win32process", "AttachThreadInput", "SetForegroundWindow"):
        assert banned not in source, f"keyboard_blocker.py should not reference {banned!r}"


if __name__ == "__main__":
    test_typing_in_a_text_field_still_works()
    test_enter_and_space_do_not_trigger_a_focused_button()
    test_new_window_gets_activated_when_shown()
    test_window_activator_does_not_cause_a_modal_dialog_to_self_reject()
    test_disable_env_var_skips_only_the_blocker_not_the_activator()
    test_no_raw_winapi_or_focus_stealing_calls()
    print("OK: keyboard blocker still protects buttons, window activator is a harmless no-op fix, no focus-stealing WinAPI calls")
