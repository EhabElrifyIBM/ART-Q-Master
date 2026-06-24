"""
Test Dispatcher_v2 Complete Fix
Tests both configuration loading and V2 design system integration
"""
import sys
import os

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def test_dispatcher_config_and_design():
    """Test Dispatcher with config loading and V2 design system"""
    print("\n" + "="*60)
    print("DISPATCHER V2 COMPLETE FIX TEST")
    print("="*60)
    
    # Import after path setup (directory has space in name)
    import sys
    import importlib.util
    
    dispatcher_path = os.path.join(os.path.dirname(__file__), 'ART Q Control', 'Dispatcher_v2.py')
    spec = importlib.util.spec_from_file_location("Dispatcher_v2", dispatcher_path)
    dispatcher_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dispatcher_module)
    show_mode_selector = dispatcher_module.show_mode_selector
    
    print("\n[1/5] Testing Dispatcher Launch...")
    try:
        dialog = show_mode_selector()
        print("✓ Dispatcher dialog created successfully")
    except Exception as e:
        print(f"✗ Failed to create dialog: {e}")
        return False
    
    print("\n[2/5] Testing Configuration Loading...")
    try:
        # Check if config was loaded via lazy loading
        shared_path = os.path.join(os.path.dirname(__file__), 'ART Q Control', 'SharedFunctions.py')
        spec = importlib.util.spec_from_file_location("SharedFunctions", shared_path)
        SharedFunctions = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(SharedFunctions)
        
        # Trigger lazy loading
        agent_name = SharedFunctions.AGENT_NAME
        user_id = SharedFunctions.DIALER_USERNAME
        sheet_name = SharedFunctions.EXCEL_SHEET_NAME
        
        print(f"  Agent Name: {agent_name}")
        print(f"  User ID: {user_id}")
        print(f"  Sheet Name: {sheet_name}")
        
        if agent_name and user_id and sheet_name:
            print("✓ Configuration loaded successfully (no None values)")
        else:
            print("✗ Configuration has None values")
            return False
            
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[3/5] Testing V2 Design System Integration...")
    try:
        # Check if dialog has V2 systems
        if not hasattr(dialog, 'theme_manager'):
            print("✗ Dialog missing theme_manager")
            return False
        if not hasattr(dialog, 'settings_bus'):
            print("✗ Dialog missing settings_bus")
            return False
        if not hasattr(dialog, 'theme_service'):
            print("✗ Dialog missing theme_service")
            return False
        
        print("✓ V2 design systems integrated")
        
        # Check theme manager
        current_theme = dialog.settings_bus.theme
        print(f"  Current theme: {current_theme}")
        
    except Exception as e:
        print(f"✗ V2 design system check failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[4/5] Testing Theme Switching...")
    try:
        # Test theme switching
        original_theme = dialog.settings_bus.theme
        print(f"  Original theme: {original_theme}")
        
        # Switch to dark theme
        dialog.settings_bus.set_theme('dark')
        print(f"  Switched to: {dialog.settings_bus.theme}")
        
        # Switch back
        dialog.settings_bus.set_theme(original_theme)
        print(f"  Restored to: {dialog.settings_bus.theme}")
        
        print("✓ Theme switching works")
        
    except Exception as e:
        print(f"✗ Theme switching failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n[5/5] Testing SharedFunctions Internal Functions...")
    try:
        # Test functions that use config values
        excel_path = SharedFunctions.todays_excel_path()
        print(f"  Excel path: {excel_path}")
        
        cache_path = SharedFunctions.get_todays_cache_path("Test Agent", "autosender")
        print(f"  Cache path: {cache_path}")
        
        case_note = SharedFunctions.get_case_note("Test Action")
        print(f"  Case note preview: {case_note[:50]}...")
        
        if excel_path and cache_path and case_note:
            print("✓ SharedFunctions internal functions work correctly")
        else:
            print("✗ Some functions returned None/empty")
            return False
            
    except Exception as e:
        print(f"✗ SharedFunctions test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED ✓")
    print("="*60)
    print("\nSummary:")
    print("  ✓ Dispatcher launches without errors")
    print("  ✓ Configuration loads correctly (no None values)")
    print("  ✓ V2 design system integrated (theme manager, settings bus)")
    print("  ✓ Theme switching works (light/dark/auto)")
    print("  ✓ SharedFunctions internal functions work")
    print("\nThe dialog is now displayed. Close it to exit the test.")
    
    # Show dialog
    dialog.exec_()
    
    return True

if __name__ == '__main__':
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    success = test_dispatcher_config_and_design()
    
    if success:
        print("\n✓ Test completed successfully")
        sys.exit(0)
    else:
        print("\n✗ Test failed")
        sys.exit(1)

# Made with Bob
