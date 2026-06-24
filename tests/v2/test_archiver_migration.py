"""Integration tests for Archiver migration (Phase 6.2)."""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

from Archiver import ArchiverWindow


def test_archiver_window_creation():
    """Test window creation."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.windowTitle() == "Case Archiver"
    assert window.isVisible() == False
    assert window.minimumWidth() == 1000
    assert window.minimumHeight() == 700
    window.close()
    print("✓ Window creation test passed")


def test_file_selector_integration():
    """Test file selector integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.file_selector is not None
    assert window.analyze_btn.isEnabled() == False
    window.close()
    print("✓ File selector integration test passed")


def test_analysis_view_integration():
    """Test analysis view integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.analysis_view is not None
    assert window.analysis_view.isVisible() == False
    window.close()
    print("✓ Analysis view integration test passed")


def test_keyboard_shortcuts():
    """Test keyboard shortcuts."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.shortcut_manager is not None
    # Check that shortcuts are registered
    assert hasattr(window.shortcut_manager, '_registry')
    window.close()
    print("✓ Keyboard shortcuts test passed")


def test_theme_integration():
    """Test theme integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.theme_manager is not None
    assert hasattr(window.theme_manager, 'current_theme')
    window.close()
    print("✓ Theme integration test passed")


def test_typography_integration():
    """Test typography integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    # Should have typography mixin methods
    assert hasattr(window, 'apply_typography')
    assert hasattr(window, 'get_font')
    assert hasattr(window, 'typography')
    window.close()
    print("✓ Typography integration test passed")


def test_service_integration():
    """Test archiver service integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.service is not None
    assert hasattr(window.service, 'load_workbook')
    assert hasattr(window.service, 'analyze_workbook')
    window.close()
    print("✓ Service integration test passed")


def test_menu_bar():
    """Test menu bar setup."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    menubar = window.menuBar()
    assert menubar is not None
    # Check that menus exist
    actions = menubar.actions()
    assert len(actions) >= 2  # File and Help menus
    window.close()
    print("✓ Menu bar test passed")


def test_status_bar():
    """Test status bar setup."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.status_bar is not None
    assert window.statusBar() is not None
    window.close()
    print("✓ Status bar test passed")


def test_settings_bus_integration():
    """Test settings bus integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = ArchiverWindow()
    assert window.settings_bus is not None
    assert hasattr(window.settings_bus, 'font_preset_changed')
    assert hasattr(window.settings_bus, 'theme_changed')
    window.close()
    print("✓ Settings bus integration test passed")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("Running Archiver Migration Integration Tests (Phase 6.2)")
    print("="*60 + "\n")
    
    try:
        test_archiver_window_creation()
        test_file_selector_integration()
        test_analysis_view_integration()
        test_keyboard_shortcuts()
        test_theme_integration()
        test_typography_integration()
        test_service_integration()
        test_menu_bar()
        test_status_bar()
        test_settings_bus_integration()
        
        print("\n" + "="*60)
        print("✅ All tests passed! Phase 6.2 integration complete.")
        print("="*60 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
