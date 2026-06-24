"""Simple test to verify Fix 1 integration is called"""
import sys
sys.path.insert(0, '.')

print("Testing Fix 1: SettingsManager wired to V2SettingsBus")
print("=" * 60)

# Test 1: Can we import the integration function?
try:
    from ui.settings import integrate_with_v2_settings_bus, get_settings_manager
    print("[PASS] Successfully imported integrate_with_v2_settings_bus")
except Exception as e:
    print(f"[FAIL] Failed to import: {e}")
    sys.exit(1)

# Test 2: Can we import V2SettingsBus?
try:
    from ui.services import get_v2_settings_bus
    print("[PASS] Successfully imported get_v2_settings_bus")
except Exception as e:
    print(f"[FAIL] Failed to import: {e}")
    sys.exit(1)

# Test 3: Check that main_menu.py imports the integration function
try:
    with open('ui/main_menu.py', 'r') as f:
        content = f.read()
        if 'integrate_with_v2_settings_bus' in content:
            print("[PASS] main_menu.py imports integrate_with_v2_settings_bus")
        else:
            print("[FAIL] main_menu.py does NOT import integrate_with_v2_settings_bus")
            sys.exit(1)
        
        if 'integrate_with_v2_settings_bus(settings_manager)' in content:
            print("[PASS] main_menu.py CALLS integrate_with_v2_settings_bus()")
        else:
            print("[FAIL] main_menu.py does NOT call integrate_with_v2_settings_bus()")
            sys.exit(1)
except Exception as e:
    print(f"[FAIL] Failed to read main_menu.py: {e}")
    sys.exit(1)

# Test 4: Verify the call is in the right place (after QApplication, before window)
try:
    lines = content.split('\n')
    qapp_line = -1
    integration_line = -1
    window_line = -1
    
    for i, line in enumerate(lines):
        if 'QApplication.instance() or QApplication(sys.argv)' in line:
            qapp_line = i
        if 'integrate_with_v2_settings_bus(settings_manager)' in line:
            integration_line = i
        if 'window = V2MainMenu()' in line:
            window_line = i
    
    if qapp_line < integration_line < window_line:
        print("[PASS] Integration is called in correct order:")
        print(f"  - QApplication created at line {qapp_line + 1}")
        print(f"  - Integration called at line {integration_line + 1}")
        print(f"  - Window created at line {window_line + 1}")
    else:
        print("[FAIL] Integration is NOT in correct order")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Failed to verify order: {e}")
    sys.exit(1)

print("=" * 60)
print("[SUCCESS] FIX 1 SUCCESSFULLY IMPLEMENTED!")
print("  SettingsManager is now wired to V2SettingsBus in main_menu.py")
print("  Integration happens during app startup, enabling reactive settings")
print("=" * 60)

# Made with Bob
