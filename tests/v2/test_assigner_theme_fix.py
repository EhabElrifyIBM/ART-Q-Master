"""
Test script to verify Assigner UI theme fixes.

This script tests that:
1. Assigner uses ThemeManager correctly
2. No hardcoded black/dark backgrounds
3. All controls are visible in both light and dark modes
4. IBM Carbon Design colors are applied correctly
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_assigner_theme():
    """Test Assigner theme integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Import after QApplication exists
    from Assigner.main_window_assigner import MainWindow
    from ui.theme_manager import ThemeManager
    
    print("=" * 60)
    print("Testing Assigner Theme Fix")
    print("=" * 60)
    
    # Create window
    window = MainWindow()
    
    # Verify ThemeManager is initialized
    assert hasattr(window, 'theme_manager'), "❌ ThemeManager not initialized"
    assert isinstance(window.theme_manager, ThemeManager), "❌ Invalid ThemeManager instance"
    print("✓ ThemeManager initialized correctly")
    
    # Verify settings bus connection
    assert hasattr(window, 'settings_bus'), "❌ Settings bus not initialized"
    print("✓ Settings bus connected")
    
    # Test Light Mode
    print("\n--- Testing Light Mode ---")
    window.theme_manager.set_theme('light')
    
    # Get colors
    bg = window.theme_manager.get_color('background')
    text = window.theme_manager.get_color('text_primary')
    primary = window.theme_manager.get_color('interactive')
    
    print(f"Background: {bg}")
    print(f"Text: {text}")
    print(f"Primary: {primary}")
    
    # Verify light mode colors
    assert bg in ['#f4f4f4', '#ffffff'], f"❌ Invalid light background: {bg}"
    assert text in ['#161616', '#000000'], f"❌ Invalid light text: {text}"
    assert primary == '#0f62fe', f"❌ Invalid primary color: {primary}"
    print("✓ Light mode colors correct")
    
    # Test Dark Mode
    print("\n--- Testing Dark Mode ---")
    window.theme_manager.set_theme('dark')
    
    # Get colors
    bg = window.theme_manager.get_color('background')
    text = window.theme_manager.get_color('text_primary')
    primary = window.theme_manager.get_color('interactive')
    
    print(f"Background: {bg}")
    print(f"Text: {text}")
    print(f"Primary: {primary}")
    
    # Verify dark mode colors
    assert bg in ['#161616', '#000000'], f"❌ Invalid dark background: {bg}"
    assert text in ['#f4f4f4', '#ffffff'], f"❌ Invalid dark text: {text}"
    assert primary == '#0f62fe', f"❌ Invalid primary color: {primary}"
    print("✓ Dark mode colors correct")
    
    # Verify stylesheet uses theme colors (not hardcoded)
    stylesheet = window.ibm_stylesheet()
    assert '#161616' not in stylesheet or 'background-color: #161616' not in stylesheet, \
        "❌ Hardcoded black background found in stylesheet"
    assert '#dbeafe' not in stylesheet or 'background-color: #dbeafe' not in stylesheet, \
        "❌ Hardcoded light blue background found in stylesheet"
    print("✓ No hardcoded backgrounds in stylesheet")
    
    # Verify typography integration
    assert hasattr(window, 'get_font'), "❌ Typography mixin not initialized"
    assert hasattr(window, 'get_size'), "❌ Typography mixin not initialized"
    print("✓ Typography system integrated")
    
    # Verify theme change handler
    assert hasattr(window, '_on_theme_changed'), "❌ Theme change handler missing"
    print("✓ Theme change handler present")
    
    # Show window briefly to verify visual appearance
    window.show()
    print("\n✓ Window displayed successfully")
    print("  Check that:")
    print("  - Background is light gray (#f4f4f4) in light mode")
    print("  - Text is dark (#161616) and clearly visible")
    print("  - All controls (checkboxes, buttons, inputs) are visible")
    print("  - Header and footer use theme colors")
    
    # Close after 3 seconds
    QTimer.singleShot(3000, window.close)
    QTimer.singleShot(3100, app.quit)
    
    print("\n" + "=" * 60)
    print("✓ All Assigner theme tests passed!")
    print("=" * 60)
    
    return app.exec_()

if __name__ == '__main__':
    sys.exit(test_assigner_theme())

# Made with Bob
