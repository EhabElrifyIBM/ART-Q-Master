"""
Integration tests for Assigner modernization (Phase 6.4).

Tests the complete integration of modern UI systems in the Assigner tool:
- Typography system integration
- Theme manager integration
- Keyboard shortcuts
- Settings bus connectivity
"""
import sys
import io
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def test_assigner_window_creation(window):
    """Test window creation with modern systems."""
    # Verify window properties
    assert window.windowTitle() == "ART Q Master V2 - Assigner"
    assert window.isVisible() == False  # Not shown yet
    
    # Verify modern systems initialized
    assert hasattr(window, 'theme_manager'), "Theme manager not initialized"
    assert hasattr(window, 'settings_bus'), "Settings bus not initialized"
    assert hasattr(window, 'typography'), "Typography system not initialized"
    
    print("[PASS] Window creation test passed")


def test_typography_integration(window):
    """Test typography system integration."""
    
    # Verify typography methods available
    assert hasattr(window, 'apply_typography'), "apply_typography method missing"
    assert hasattr(window, 'get_font'), "get_font method missing"
    assert hasattr(window, 'get_size'), "get_size method missing"
    
    # Test get_size returns valid values
    body_size = window.get_size('body')
    assert isinstance(body_size, int), "get_size should return int"
    assert body_size > 0, "Font size should be positive"
    
    # Test get_font returns QFont
    from PyQt5.QtGui import QFont
    body_font = window.get_font('body')
    assert isinstance(body_font, QFont), "get_font should return QFont"
    
    print("[PASS] Typography integration test passed")


def test_keyboard_shortcuts(window):
    """Test keyboard shortcuts integration."""
    
    # Verify shortcut manager initialized
    assert hasattr(window, 'shortcut_manager'), "Shortcut manager not initialized"
    
    # Verify shortcuts registered
    registry = window.shortcut_manager.get_registry()
    shortcuts = registry.get_all()
    
    # Should have at least 7 shortcuts registered
    assert len(shortcuts) >= 7, f"Expected at least 7 shortcuts, got {len(shortcuts)}"
    
    # Verify specific shortcuts exist
    shortcut_ids = list(shortcuts.keys())
    expected_shortcuts = [
        'assigner_open_file',
        'assigner_assign_cases',
        'assigner_reset',
        'assigner_close',
        'assigner_settings',
        'assigner_help',
        'assigner_main_menu'
    ]
    
    for expected_id in expected_shortcuts:
        assert expected_id in shortcut_ids, f"Shortcut '{expected_id}' not registered"
    
    print("[PASS] Keyboard shortcuts test passed")


def test_theme_integration(window):
    """Test theme manager integration."""
    
    # Verify theme change handler exists
    assert hasattr(window, '_on_theme_changed'), "_on_theme_changed handler missing"
    
    # Verify theme manager can get colors
    bg_color = window.theme_manager.get_color('background')
    assert bg_color is not None, "Theme manager should return background color"
    assert bg_color.startswith('#'), "Color should be hex format"
    
    primary_color = window.theme_manager.get_color('interactive')
    assert primary_color is not None, "Theme manager should return interactive color"
    
    print("[PASS] Theme integration test passed")


def test_stylesheet_generation(window):
    """Test modern stylesheet generation."""
    
    # Generate stylesheet
    stylesheet = window.ibm_stylesheet()
    
    # Verify stylesheet is not empty
    assert len(stylesheet) > 0, "Stylesheet should not be empty"
    
    # Verify it contains modern color references (not hardcoded)
    # The stylesheet should use theme_manager.get_color() results
    assert 'QWidget' in stylesheet, "Stylesheet should style QWidget"
    assert 'QPushButton' in stylesheet, "Stylesheet should style QPushButton"
    assert 'QLabel' in stylesheet, "Stylesheet should style QLabel"
    
    print("[PASS] Stylesheet generation test passed")


def test_validation_feedback(window):
    """Test validation with Toast feedback."""
    
    # Verify validation method exists
    assert hasattr(window, '_validate_inputs'), "_validate_inputs method missing"
    
    # Test validation returns False when no inputs
    result = window._validate_inputs()
    assert result == False, "Validation should fail with no inputs"
    
    print("[PASS] Validation feedback test passed")


def test_settings_bus_connectivity(window):
    """Test settings bus connectivity."""
    
    # Verify settings bus connected
    assert window.settings_bus is not None, "Settings bus should be initialized"
    
    # Verify theme change handler exists and is callable
    assert hasattr(window, '_on_theme_changed'), "Theme change handler should exist"
    assert callable(window._on_theme_changed), "Theme change handler should be callable"
    
    print("[PASS] Settings bus connectivity test passed")


def test_no_legacy_code(window):
    """Test that legacy code has been removed."""
    
    # Verify legacy methods removed
    assert not hasattr(window, '_apply_dynamic_widget_scaling'), \
        "Legacy _apply_dynamic_widget_scaling should be removed"
    
    # Verify no _scale attribute
    assert not hasattr(window, '_scale'), \
        "Legacy _scale attribute should be removed"
    
    print("[PASS] No legacy code test passed")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("Running Assigner Modernization Integration Tests (Phase 6.4)")
    print("="*60 + "\n")
    
    window = None
    try:
        # Create QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Import after QApplication exists
        sys.path.insert(0, 'src_v2')
        from Assigner.main_window_assigner import MainWindow
        
        # Create single window instance for all tests
        window = MainWindow()
        
        # Run all tests with the same window instance
        test_assigner_window_creation(window)
        test_typography_integration(window)
        test_keyboard_shortcuts(window)
        test_theme_integration(window)
        test_stylesheet_generation(window)
        test_validation_feedback(window)
        test_settings_bus_connectivity(window)
        test_no_legacy_code(window)
        
        print("\n" + "="*60)
        print("[SUCCESS] ALL TESTS PASSED - Phase 6.4 Complete!")
        print("="*60 + "\n")
        return True
        
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up window
        if window:
            window.close()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
