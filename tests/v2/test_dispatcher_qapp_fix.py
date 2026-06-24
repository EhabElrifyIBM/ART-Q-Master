"""
Test script to verify QApplication fix in Dispatcher_v2.
This simulates the exact execution flow when launching ART Q Control.
"""
import sys
import os

# Set UTF-8 encoding for console output
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Add src_v2/ART Q Control to path
CURRENT_DIR = os.path.join(os.path.dirname(__file__), "ART Q Control")
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

print("=" * 60)
print("Testing Dispatcher_v2 QApplication Fix")
print("=" * 60)

# Step 1: Import Dispatcher_v2 module
print("\n[TEST 1] Importing Dispatcher_v2 module...")
try:
    import Dispatcher_v2
    print("[PASS] Module imported successfully (no QApplication error at import time)")
except Exception as e:
    print(f"[FAIL] {e}")
    sys.exit(1)

# Step 2: Check that PyQt5 is NOT imported yet
print("\n[TEST 2] Checking PyQt5 import status...")
if 'PyQt5.QtWidgets' in sys.modules:
    print("[FAIL] PyQt5.QtWidgets was imported at module level!")
    sys.exit(1)
else:
    print("[PASS] PyQt5.QtWidgets NOT imported yet (lazy import working)")

# Step 3: Check that AutoSender_v2 and CaseReviewer_v2 are NOT imported yet
print("\n[TEST 3] Checking AutoSender_v2/CaseReviewer_v2 import status...")
if 'AutoSender_v2' in sys.modules:
    print("[FAIL] AutoSender_v2 was imported at module level!")
    sys.exit(1)
if 'CaseReviewer_v2' in sys.modules:
    print("[FAIL] CaseReviewer_v2 was imported at module level!")
    sys.exit(1)
print("[PASS] AutoSender_v2 and CaseReviewer_v2 NOT imported yet (lazy import working)")

# Step 4: Create QApplication (simulating what main() does)
print("\n[TEST 4] Creating QApplication...")
from PyQt5.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
print("[PASS] QApplication created successfully")

# Step 5: Now try to call show_mode_selector (this should work)
print("\n[TEST 5] Calling show_mode_selector()...")
try:
    # Mock the dialog to return immediately without showing UI
    from unittest.mock import patch
    with patch.object(Dispatcher_v2, 'ModeSelectorDialog') as mock_dialog:
        # Make the dialog return mode=0 (exit) immediately
        mock_instance = mock_dialog.return_value
        mock_instance.exec_.return_value = 0
        mock_instance.get_result.return_value = (0, None)
        
        result, agent = Dispatcher_v2.show_mode_selector()
        print(f"[PASS] show_mode_selector() executed successfully (result={result}, agent={agent})")
except Exception as e:
    print(f"[FAIL] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
print("\nConclusion:")
print("- Dispatcher_v2 no longer imports PyQt5 at module level")
print("- AutoSender_v2 and CaseReviewer_v2 are lazy imported")
print("- QApplication can be created before any QWidget")
print("- The QApplication error should be fixed!")

# Made with Bob
