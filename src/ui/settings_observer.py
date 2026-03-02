# ============================================================================
# settings_observer.py - Settings Change Observer/Broadcaster
# ============================================================================
# Phase 5.4: Settings Integration
#
# Provides centralized settings change notification system.
# Allows all windows/dialogs to listen for and respond to settings changes.
# ============================================================================

from PyQt5.QtCore import QObject, pyqtSignal

# Singleton instance
_settings_observer = None


class SettingsObserver(QObject):
    """
    Centralized observer for settings changes.
    
    Signals broadcast to all connected windows when settings change.
    """
    
    # Signals
    theme_changed = pyqtSignal(str)  # 'light' or 'dark'
    font_size_changed = pyqtSignal(float)  # 0.8 to 2.0
    
    def __init__(self):
        super().__init__()
    
    def notify_theme_changed(self, theme: str):
        """Notify all observers of theme change."""
        print(f"[SETTINGS OBSERVER] Broadcasting theme change: {theme}")
        self.theme_changed.emit(theme)
    
    def notify_font_size_changed(self, scale: float):
        """Notify all observers of font size change."""
        print(f"[SETTINGS OBSERVER] Broadcasting font size change: {scale}")
        self.font_size_changed.emit(scale)


def get_settings_observer() -> SettingsObserver:
    """Get or create settings observer singleton."""
    global _settings_observer
    if _settings_observer is None:
        _settings_observer = SettingsObserver()
    return _settings_observer
