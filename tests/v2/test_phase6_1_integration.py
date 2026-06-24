"""
Test Phase 6.1 integration - verify all new components work together.
"""

import sys
from pathlib import Path

# Add src_v2 to path
src_v2_root = Path(__file__).parent
sys.path.insert(0, str(src_v2_root))

from PyQt5.QtWidgets import QApplication

def test_imports():
    """Test that all new components can be imported."""
    print("Testing imports...")
    
    try:
        from ui.components_v2 import SearchBar, CompactToolCard, EnhancedToolCard, ProfileButton
        print("[PASS] All components imported successfully")
    except Exception as e:
        print(f"[FAIL] Component import failed: {e}")
        return False
    
    try:
        from utils.recent_tools import get_recent_tools_manager
        print("[PASS] Recent tools manager imported successfully")
    except Exception as e:
        print(f"[FAIL] Recent tools manager import failed: {e}")
        return False
    
    try:
        from utils.tool_registry import get_tool_definition
        print("[PASS] Tool registry imported successfully")
    except Exception as e:
        print(f"[FAIL] Tool registry import failed: {e}")
        return False
    
    return True

def test_main_menu():
    """Test that main menu can be created."""
    print("\nTesting main menu creation...")
    
    try:
        app = QApplication.instance() or QApplication(sys.argv)
        
        from ui.main_menu import V2MainMenu
        window = V2MainMenu()
        
        print("[PASS] Main menu created successfully")
        print(f"  - Window title: {window.windowTitle()}")
        print(f"  - Window size: {window.width()}x{window.height()}")
        
        # Check for new components
        if hasattr(window, '_search_bar'):
            print("[PASS] SearchBar component found")
        else:
            print("[FAIL] SearchBar component NOT found")
        
        if hasattr(window, '_tools_grid'):
            print("[PASS] Tools grid found")
        else:
            print("[FAIL] Tools grid NOT found")
        
        if hasattr(window, '_tool_cards'):
            print(f"[PASS] Tool cards dictionary found ({len(window._tool_cards)} cards)")
        else:
            print("[FAIL] Tool cards dictionary NOT found")
        
        window.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] Main menu creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recent_tools():
    """Test recent tools manager."""
    print("\nTesting recent tools manager...")
    
    try:
        from utils.recent_tools import get_recent_tools_manager
        
        manager = get_recent_tools_manager()
        print("[PASS] Recent tools manager created")
        
        # Test adding a tool
        manager.add_tool("art_q_control")
        recent = manager.get_recent_tools(limit=3)
        
        if "art_q_control" in recent:
            print("[PASS] Tool tracking works")
        else:
            print("[FAIL] Tool tracking failed")
        
        # Clear for clean state
        manager.clear()
        print("[PASS] Recent tools cleared")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Recent tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 6.1 Integration Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Recent Tools", test_recent_tools()))
    results.append(("Main Menu", test_main_menu()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED")
    else:
        print("[ERROR] SOME TESTS FAILED")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
