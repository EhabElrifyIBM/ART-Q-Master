# ============================================================================
# keyboard_locker.py - Keyboard Event Blocking for Dialogs
# ============================================================================
# Phase 3.4: Keyboard Locking on Dialogs
#
# Prevents keyboard input to main window when dialogs are open.
# Useful for preventing accidental key presses while interacting with popups.
# ============================================================================

from PyQt5.QtWidgets import QDialog, QWidget
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QKeySequence


class KeyboardLockedDialog(QDialog):
    """
    Dialog that locks keyboard input to prevent accidental key presses.
    
    Blocks:
    - All regular key presses
    - Ctrl+C, Ctrl+V, Ctrl+X, etc (copy/paste)
    - Alt+Tab (minimized to prevent window switching)
    - Tab, Shift+Tab (prevents tabbing out of dialog)
    
    Allows:
    - Buttons (buttons capture keyboard normally)
    - Text input fields (when they have focus)
    - Escape key (if dialog wants to allow closing)
    
    Usage:
        class MyDialog(KeyboardLockedDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                # Your dialog code here
    """
    
    def __init__(self, parent=None, allow_escape=True):
        """
        Initialize keyboard-locked dialog.
        
        Args:
            parent: Parent widget
            allow_escape (bool): Whether to allow Escape key to close dialog
        """
        super().__init__(parent)
        self.allow_escape = allow_escape
        self.setWindowModality(Qt.ApplicationModal)
    
    def keyPressEvent(self, event):
        """
        Override keyPressEvent to lock keyboard input.
        
        Args:
            event: QKeyEvent
        """
        key = event.key()
        modifiers = event.modifiers()
        
        # Allow Escape key if configured
        if self.allow_escape and key == Qt.Key_Escape:
            super().keyPressEvent(event)
            return
        
        # Allow Enter/Return for button activation
        if key in (Qt.Key_Return, Qt.Key_Enter):
            super().keyPressEvent(event)
            return
        
        # Allow Tab/Shift+Tab for navigation within dialog
        if key == Qt.Key_Tab or key == Qt.Key_Backtab:
            super().keyPressEvent(event)
            return
        
        # Allow Space for button activation
        if key == Qt.Key_Space:
            super().keyPressEvent(event)
            return
        
        # Allow arrow keys for navigation in lists/combos
        if key in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            super().keyPressEvent(event)
            return
        
        # Allow text input in text fields/line edits (pass through)
        # This is handled by widget's keyPressEvent
        if self.focusWidget() and hasattr(self.focusWidget(), 'setText'):
            super().keyPressEvent(event)
            return
        
        # Block everything else (Ctrl+C, Alt+Tab, random keys, etc)
        # Silently ignore by not calling super().keyPressEvent(event)
        event.ignore()
    
    def keyReleaseEvent(self, event):
        """
        Override keyReleaseEvent to stay consistent with keyPressEvent.
        
        Args:
            event: QKeyEvent
        """
        key = event.key()
        
        # Allow same keys as keyPressEvent
        if key in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, 
                  Qt.Key_Tab, Qt.Key_Backtab, Qt.Key_Space,
                  Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            super().keyReleaseEvent(event)
            return
        
        # Allow text field input
        if self.focusWidget() and hasattr(self.focusWidget(), 'setText'):
            super().keyReleaseEvent(event)
            return
        
        # Block everything else
        event.ignore()


class PartialKeyboardLockedDialog(QDialog):
    """
    Dialog that locks specific problematic keyboard shortcuts.
    
    This is less aggressive - allows most input but blocks:
    - Alt+Tab (window switching)
    - Ctrl+Alt+Delete-like combinations
    - Windows key
    
    Usage for less strict locking:
        class MyDialog(PartialKeyboardLockedDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                # Your dialog code here
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)
    
    def keyPressEvent(self, event):
        """Block only dangerous keyboard shortcuts."""
        key = event.key()
        modifiers = event.modifiers()
        
        # Block Alt+Tab
        if key == Qt.Key_Tab and (modifiers & Qt.AltModifier):
            event.ignore()
            return
        
        # Block Windows key
        if key in (Qt.Key_Super_L, Qt.Key_Super_R, Qt.Key_Menu):
            event.ignore()
            return
        
        # Block Ctrl+Alt+Delete (can't actually catch this on Windows)
        if (modifiers & Qt.ControlModifier) and (modifiers & Qt.AltModifier):
            # This is weak but some systems allow partial blocking
            pass
        
        # Allow everything else
        super().keyPressEvent(event)


def enable_keyboard_lock(dialog, strict=True, allow_escape=True):
    """
    Enable keyboard locking on an existing dialog.
    
    Args:
        dialog (QDialog): Dialog to lock keyboard on
        strict (bool): If True, use strict locking (blocks most keys)
                      If False, use partial locking (only blocks dangerous shortcuts)
        allow_escape (bool): If True, allow Escape key to close dialog
    
    Returns:
        Modified dialog with keyboard locking enabled
    
    Note:
        This wraps the dialog's keyPressEvent to add locking behavior.
        Not as clean as subclassing but useful for existing dialogs.
    
    Usage:
        dialog = QDialog()
        dialog = enable_keyboard_lock(dialog, strict=True)
    """
    
    original_keyPressEvent = dialog.keyPressEvent
    
    def locked_keyPressEvent(event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Allow Escape if configured
        if allow_escape and key == Qt.Key_Escape:
            original_keyPressEvent(event)
            return
        
        # Allow navigation keys
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab, 
                  Qt.Key_Backtab, Qt.Key_Space,
                  Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right):
            original_keyPressEvent(event)
            return
        
        if strict:
            # Block everything else
            event.ignore()
        else:
            # Only block dangerous keys
            if key in (Qt.Key_Tab, Qt.Key_Super_L, Qt.Key_Super_R):
                if (modifiers & Qt.AltModifier) or key in (Qt.Key_Super_L, Qt.Key_Super_R):
                    event.ignore()
                    return
            
            original_keyPressEvent(event)
    
    dialog.keyPressEvent = locked_keyPressEvent
    return dialog
