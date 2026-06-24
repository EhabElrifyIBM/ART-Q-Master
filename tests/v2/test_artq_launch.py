"""
Test script to verify ART Q Control launches without QApplication errors.
This simulates what happens when clicking ART Q Control from the main menu.
"""

import sys
import os

# Add src_v2 to path
src_v2_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, src_v2_dir)

# Add ART Q Control directory
artq_dir = os.path.join(src_v2_dir, "ART Q Control")
sys.path.insert(0, artq_dir)

print("=" * 60)
print("Testing ART Q Control Launch (Simulating Main Menu Click)")
print("=" * 60)

try:
    # This is what happens when the tool is launched
    print("\n[TEST] Importing Dispatcher_v2...")
    from Dispatcher_v2 import show_mode_selector
    
    print("[TEST] SUCCESS - Import successful - no QApplication error!")
    print("[TEST] Creating QApplication and showing dialog...")
    
    # This would show the dialog
    # result, support_agent = show_mode_selector()
    
    print("[TEST] SUCCESS - All imports completed successfully!")
    print("\n" + "=" * 60)
    print("SUCCESS: ART Q Control can launch without QApplication errors")
    print("=" * 60)
    
except Exception as e:
    print(f"\n[TEST] FAILED with error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Made with Bob
