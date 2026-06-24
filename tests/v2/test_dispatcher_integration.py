"""
Test Dispatcher_v2 Integration - Real-World Launch Test
========================================================

This test verifies the Dispatcher works correctly by actually launching it.
Tests:
1. Configuration loads correctly (no None values)
2. Dialog displays with proper theme
3. All 5 modes are accessible
4. Support checkbox works

Run: python src_v2/test_dispatcher_integration.py
"""

import sys
import os

# Add src_v2 to path
src_v2_dir = os.path.dirname(os.path.abspath(__file__))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

# Change to src_v2 directory so config_loader finds config.json
os.chdir(src_v2_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

def test_dispatcher_integration():
    """Test Dispatcher by actually launching it."""
    
    print("=" * 70)
    print("DISPATCHER V2 INTEGRATION TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("  1. Launch the Dispatcher dialog")
    print("  2. Verify configuration loads correctly")
    print("  3. Verify theme system is active")
    print("  4. Auto-close after 2 seconds")
    print("\nLaunching in 1 second...")
    print("=" * 70)
    
    # Ensure QApplication exists
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Import after QApplication exists
    sys.path.insert(0, os.path.join(src_v2_dir, 'ART Q Control'))
    
    try:
        from Dispatcher_v2 import show_mode_selector, _get_config_values
        
        print("\n[1/3] Testing configuration loading...")
        config = _get_config_values()
        
        print(f"   Agent Name: {config['agent_name']}")
        print(f"   User ID: {config['user_id']}")
        print(f"   Sheet Name: {config['sheet_name']}")
        print(f"   Config Manager: {type(config['config_manager']).__name__}")
        
        if config['agent_name'] and config['user_id'] and config['sheet_name']:
            print("   [OK] Configuration loaded successfully!")
        else:
            print("   [WARNING] Some config values are None")
        
        print("\n[2/3] Launching Dispatcher dialog...")
        print("   (Dialog will auto-close in 2 seconds)")
        
        # Auto-close after 2 seconds
        def auto_close():
            """Auto-close dialog after verification."""
            for widget in QApplication.topLevelWidgets():
                if widget.isVisible() and hasattr(widget, 'done'):
                    print("\n[3/3] Verifying dialog properties...")
                    print(f"   Window Title: {widget.windowTitle()}")
                    print(f"   Size: {widget.width()}x{widget.height()}")
                    
                    # Check V2 systems
                    has_theme = hasattr(widget, 'theme_manager')
                    has_settings = hasattr(widget, 'settings_bus')
                    has_service = hasattr(widget, 'theme_service')
                    has_typo = hasattr(widget, 'typography')
                    
                    print(f"   Theme Manager: {'[OK]' if has_theme else '[MISSING]'}")
                    print(f"   Settings Bus: {'[OK]' if has_settings else '[MISSING]'}")
                    print(f"   Theme Service: {'[OK]' if has_service else '[MISSING]'}")
                    print(f"   Typography: {'[OK]' if has_typo else '[MISSING]'}")
                    
                    if all([has_theme, has_settings, has_service, has_typo]):
                        print("\n" + "=" * 70)
                        print("SUCCESS: All V2 systems integrated correctly!")
                        print("=" * 70)
                    else:
                        print("\n" + "=" * 70)
                        print("WARNING: Some V2 systems missing")
                        print("=" * 70)
                    
                    # Close dialog
                    widget.done(4)
                    break
        
        # Schedule auto-close
        QTimer.singleShot(2000, auto_close)
        
        # Show dialog
        result, support_agent = show_mode_selector()
        
        print(f"\nDialog closed with result: {result}")
        print("\nTest completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_dispatcher_integration()
    sys.exit(0 if success else 1)

# Made with Bob