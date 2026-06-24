"""
Test script for keyboard shortcuts system.

This script verifies that all keyboard shortcuts are properly registered
and functional in the src_v2 UI system.

Run this script to test:
- All 6 global shortcuts are registered
- No conflicts exist
- F1 help dialog displays correctly
- Shortcuts integrate with UnifiedToolShell
- Visual indicators (tooltips) are present

Usage:
    python src_v2/test_keyboard_shortcuts.py
"""

import sys
from pathlib import Path

# Add src_v2 to path
src_v2_path = Path(__file__).parent
sys.path.insert(0, str(src_v2_path))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from ui.main_menu import V2MainMenu
from ui.keyboard_shortcuts import ShortcutCategory


def test_shortcuts():
    """Test keyboard shortcuts system."""
    print("\n" + "="*60)
    print("KEYBOARD SHORTCUTS SYSTEM TEST")
    print("="*60 + "\n")
    
    # Create application
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create main menu (which uses UnifiedToolShell)
    window = V2MainMenu()
    
    # Get shortcut manager
    shortcut_manager = window.get_shortcut_manager()
    registry = shortcut_manager.get_registry()
    
    # Test 1: Check all global shortcuts are registered
    print("Test 1: Checking global shortcuts registration...")
    global_shortcuts = registry.get_by_category(ShortcutCategory.GLOBAL)
    
    expected_shortcuts = {
        "global_quit": "Ctrl+Q",
        "global_close_window": "Ctrl+W",
        "global_settings": "Ctrl+,",
        "global_help": "Ctrl+H",
        "global_main_menu": "Ctrl+M",
        "global_context_help": "F1",
    }
    
    print(f"  Expected: {len(expected_shortcuts)} shortcuts")
    print(f"  Found: {len(global_shortcuts)} shortcuts")
    
    all_registered = True
    for shortcut_id, expected_key in expected_shortcuts.items():
        if shortcut_id in global_shortcuts:
            actual_key = global_shortcuts[shortcut_id].key_sequence
            if actual_key == expected_key:
                print(f"  [OK] {shortcut_id}: {actual_key}")
            else:
                print(f"  [FAIL] {shortcut_id}: Expected {expected_key}, got {actual_key}")
                all_registered = False
        else:
            print(f"  [FAIL] {shortcut_id}: NOT REGISTERED")
            all_registered = False
    
    if all_registered:
        print("  [OK] All global shortcuts registered correctly\n")
    else:
        print("  [FAIL] Some shortcuts missing or incorrect\n")
    
    # Test 2: Check for conflicts
    print("Test 2: Checking for shortcut conflicts...")
    if registry.has_conflicts():
        conflicts = registry.get_conflicts()
        print(f"  [FAIL] Found {len(conflicts)} conflicts:")
        for conflict in conflicts:
            print(f"    - {conflict[0]} vs {conflict[1]}")
    else:
        print("  [OK] No conflicts detected\n")
    
    # Test 3: Check all shortcuts are enabled
    print("Test 3: Checking shortcuts are enabled...")
    all_enabled = True
    for shortcut_id, shortcut_def in global_shortcuts.items():
        if not shortcut_def.enabled:
            print(f"  [FAIL] {shortcut_id} is disabled")
            all_enabled = False
    
    if all_enabled:
        print("  [OK] All shortcuts are enabled\n")
    else:
        print("  [FAIL] Some shortcuts are disabled\n")
    
    # Test 4: Check tooltips
    print("Test 4: Checking UI tooltips...")
    settings_button = None
    help_button = None
    
    for button in window.findChildren(type(window.findChild(type(window).__bases__[0]))):
        obj_name = button.objectName() if hasattr(button, 'objectName') else None
        if obj_name == "settingsButton":
            settings_button = button
        elif obj_name == "helpButton":
            help_button = button
    
    # Find buttons by object name
    from PyQt5.QtWidgets import QPushButton
    for button in window.findChildren(QPushButton):
        if button.objectName() == "settingsButton":
            settings_button = button
        elif button.objectName() == "helpButton":
            help_button = button
    
    if settings_button:
        tooltip = settings_button.toolTip()
        if "Ctrl+," in tooltip:
            print(f"  [OK] Settings button has shortcut tooltip")
        else:
            print(f"  [FAIL] Settings button missing shortcut in tooltip: {tooltip}")
    else:
        print("  [FAIL] Settings button not found")
    
    if help_button:
        tooltip = help_button.toolTip()
        if "F1" in tooltip:
            print(f"  [OK] Help button has shortcut tooltip")
        else:
            print(f"  [FAIL] Help button missing shortcut in tooltip: {tooltip}")
    else:
        print("  [FAIL] Help button not found")
    
    print()
    
    # Test 5: Summary
    print("="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Global shortcuts registered: {len(global_shortcuts)}/{len(expected_shortcuts)}")
    print(f"Conflicts detected: {len(registry.get_conflicts())}")
    print(f"All shortcuts enabled: {'Yes' if all_enabled else 'No'}")
    print(f"UI integration: {'Complete' if settings_button and help_button else 'Incomplete'}")
    print()
    
    # Show the window for manual testing
    print("Opening main menu for manual testing...")
    print("\nManual Test Instructions:")
    print("-" * 60)
    print("1. Press F1 to open keyboard shortcuts help dialog")
    print("2. Press Ctrl+, to open settings dialog")
    print("3. Press Ctrl+H to open help (should show shortcuts)")
    print("4. Press Ctrl+W to close the window")
    print("5. Press Ctrl+Q to quit the application")
    print("6. Click the [?] help button to verify it shows shortcuts")
    print("-" * 60)
    print("\nWindow will open in 2 seconds...\n")
    
    # Show window after delay
    QTimer.singleShot(2000, window.show)
    
    # Run application
    return app.exec_()


if __name__ == "__main__":
    try:
        exit_code = test_shortcuts()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob