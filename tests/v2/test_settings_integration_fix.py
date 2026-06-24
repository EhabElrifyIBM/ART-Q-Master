"""
Test to verify Fix 1: SettingsManager is wired to V2SettingsBus
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Add src_v2 to path
sys.path.insert(0, '.')

from ui.settings import get_settings_manager, integrate_with_v2_settings_bus
from ui.services import get_v2_settings_bus


def test_integration():
    """Test that integrate_with_v2_settings_bus() properly wires signals."""
    app = QApplication(sys.argv)
    
    # Get instances
    settings_manager = get_settings_manager()
    bus = get_v2_settings_bus()
    
    print("=" * 60)
    print("Testing Fix 1: SettingsManager -> V2SettingsBus Integration")
    print("=" * 60)
    
    # Track if signals were received
    theme_changed = []
    font_changed = []
    
    def on_theme_changed(theme):
        theme_changed.append(theme)
        print(f"✓ V2SettingsBus.theme_changed signal received: {theme}")
    
    def on_font_changed(size):
        font_changed.append(size)
        print(f"✓ V2SettingsBus.font_size_changed signal received: {size}pt")
    
    # Connect to bus signals
    bus.theme_changed.connect(on_theme_changed)
    bus.font_size_changed.connect(on_font_changed)
    
    print("\n1. Before integration:")
    print(f"   SettingsManager: {settings_manager}")
    print(f"   V2SettingsBus: {bus}")
    print(f"   Current theme: {settings_manager.appearance.theme_mode}")
    print(f"   Current font preset: {settings_manager.appearance.font_size_preset}")
    
    # Call the integration function
    print("\n2. Calling integrate_with_v2_settings_bus()...")
    integrate_with_v2_settings_bus(settings_manager)
    print("   ✓ Integration function called successfully")
    
    # Test that changes propagate
    print("\n3. Testing signal propagation:")
    print("   Changing theme to 'dark'...")
    settings_manager.update_appearance(theme_mode='dark')
    
    print("   Changing font preset to 'large'...")
    settings_manager.update_appearance(font_size_preset='large')
    
    # Process events to ensure signals are delivered
    app.processEvents()
    
    # Verify results
    print("\n4. Verification:")
    success = True
    
    if len(theme_changed) > 0:
        print(f"   ✓ Theme change propagated to V2SettingsBus: {theme_changed}")
    else:
        print("   ✗ Theme change did NOT propagate to V2SettingsBus")
        success = False
    
    if len(font_changed) > 0:
        print(f"   ✓ Font size change propagated to V2SettingsBus: {font_changed}")
    else:
        print("   ✗ Font size change did NOT propagate to V2SettingsBus")
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✓ FIX 1 VERIFIED: Integration is working correctly!")
        print("  Settings changes now propagate from SettingsManager to V2SettingsBus")
    else:
        print("✗ FIX 1 FAILED: Integration is not working")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(test_integration())

# Made with Bob
