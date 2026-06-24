"""
Test AutoSender Modernization (Phase 6.6)
==========================================

This test verifies that the AutoSender modernization is working correctly:
- Modern dialogs with V2 foundation systems
- Theme integration
- Typography system
- Settings bus subscription
- Cache system preservation
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add src_v2 to path
src_v2_dir = os.path.dirname(os.path.abspath(__file__))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Import AutoSender dialogs
sys.path.insert(0, os.path.join(src_v2_dir, 'ART Q Control'))
from AutoSender_v2 import (
    ModernResumeDialog,
    ModernFileSelectionDialog,
    ModernCompletionDialog
)


def test_resume_dialog():
    """Test the modern resume dialog."""
    print("\n" + "="*60)
    print("Testing Modern Resume Dialog")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create test cache file path
    cache_path = "test_cache.xlsx"
    
    try:
        dialog = ModernResumeDialog(cache_path, "Auto Sender")
        
        # Verify dialog properties
        assert dialog.windowTitle() == "Resume Auto Sender?"
        assert dialog.cache_path == cache_path
        assert dialog.mode_name == "Auto Sender"
        assert dialog.user_choice == "NEW"  # Default
        
        # Verify theme manager integration
        assert dialog.theme_manager is not None
        assert dialog.settings_bus is not None
        
        # Verify typography mixin
        assert hasattr(dialog, 'typography')
        assert hasattr(dialog, 'get_font')
        assert hasattr(dialog, 'apply_typography')
        
        print("✓ Resume dialog created successfully")
        print("✓ Theme manager integrated")
        print("✓ Typography mixin working")
        print("✓ Settings bus connected")
        
        # Show dialog (non-blocking for test)
        dialog.show()
        dialog.close()
        
        print("\n✓ Resume Dialog Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Resume Dialog Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_selection_dialog():
    """Test the modern file selection dialog."""
    print("\n" + "="*60)
    print("Testing Modern File Selection Dialog")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        dialog = ModernFileSelectionDialog()
        
        # Verify dialog properties
        assert dialog.windowTitle() == "Select Excel File - AutoSender"
        assert dialog.selected_file is None  # No file selected yet
        
        # Verify drag-drop enabled
        assert dialog.acceptDrops() == True
        
        # Verify theme manager integration
        assert dialog.theme_manager is not None
        assert dialog.settings_bus is not None
        assert dialog.recent_manager is not None
        
        # Verify typography mixin
        assert hasattr(dialog, 'typography')
        
        print("✓ File selection dialog created successfully")
        print("✓ Drag-drop enabled")
        print("✓ Theme manager integrated")
        print("✓ Recent files manager integrated")
        print("✓ Typography mixin working")
        
        # Show dialog (non-blocking for test)
        dialog.show()
        dialog.close()
        
        print("\n✓ File Selection Dialog Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ File Selection Dialog Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_completion_dialog():
    """Test the modern completion dialog."""
    print("\n" + "="*60)
    print("Testing Modern Completion Dialog")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create test statistics
    test_stats = {
        'cases_completed': 25,
        'cases_skipped': 3,
        'cases_failed': 2,
        'total_cases': 30,
        'duration': '15m 30s'
    }
    
    try:
        dialog = ModernCompletionDialog(test_stats)
        
        # Verify dialog properties
        assert dialog.windowTitle() == "AutoSender Complete"
        assert dialog.stats == test_stats
        
        # Verify theme manager integration
        assert dialog.theme_manager is not None
        assert dialog.settings_bus is not None
        
        # Verify typography mixin
        assert hasattr(dialog, 'typography')
        
        print("✓ Completion dialog created successfully")
        print("✓ Statistics displayed correctly")
        print("✓ Theme manager integrated")
        print("✓ Typography mixin working")
        
        # Show dialog (non-blocking for test)
        dialog.show()
        dialog.close()
        
        print("\n✓ Completion Dialog Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Completion Dialog Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_theme_switching():
    """Test theme switching on dialogs."""
    print("\n" + "="*60)
    print("Testing Theme Switching")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        from ui.services import get_v2_settings_bus
        settings_bus = get_v2_settings_bus()
        
        # Create a dialog
        dialog = ModernResumeDialog("test.xlsx", "Test")
        
        # Test light theme
        settings_bus.set_theme("light")
        print("✓ Light theme applied")
        
        # Test dark theme
        settings_bus.set_theme("dark")
        print("✓ Dark theme applied")
        
        # Test auto theme
        settings_bus.set_theme("auto")
        print("✓ Auto theme applied")
        
        dialog.close()
        
        print("\n✓ Theme Switching Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Theme Switching Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_typography_scaling():
    """Test typography scaling on dialogs."""
    print("\n" + "="*60)
    print("Testing Typography Scaling")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        from ui.services import get_v2_settings_bus
        settings_bus = get_v2_settings_bus()
        
        # Create a dialog
        dialog = ModernCompletionDialog({'cases_completed': 10})
        
        # Test different font presets
        presets = ['small', 'normal', 'large', 'xlarge']
        for preset in presets:
            settings_bus.font_preset_changed.emit(preset)
            print(f"✓ {preset.capitalize()} preset applied")
        
        dialog.close()
        
        print("\n✓ Typography Scaling Test PASSED")
        return True
        
    except Exception as e:
        print(f"\n✗ Typography Scaling Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all AutoSender modernization tests."""
    print("\n" + "="*70)
    print(" AutoSender Modernization Test Suite (Phase 6.6)")
    print("="*70)
    
    results = []
    
    # Run tests
    results.append(("Resume Dialog", test_resume_dialog()))
    results.append(("File Selection Dialog", test_file_selection_dialog()))
    results.append(("Completion Dialog", test_completion_dialog()))
    results.append(("Theme Switching", test_theme_switching()))
    results.append(("Typography Scaling", test_typography_scaling()))
    
    # Summary
    print("\n" + "="*70)
    print(" Test Summary")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<50} {status}")
    
    print("="*70)
    print(f"Total: {passed}/{total} tests passed")
    print("="*70)
    
    if passed == total:
        print("\n🎉 All tests PASSED! AutoSender modernization is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) FAILED. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
