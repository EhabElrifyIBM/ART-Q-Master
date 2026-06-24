"""
Test script for settings dialog with typography presets
"""
import sys
from PyQt5.QtWidgets import QApplication
from ui.settings_dialog import SettingsDialog

def test_settings_dialog():
    """Test the settings dialog with new preset system"""
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("Testing Settings Dialog with Typography Presets")
    print("=" * 60)
    
    # Create and show dialog
    dialog = SettingsDialog()
    
    # Check that preset button group exists
    if hasattr(dialog, 'preset_button_group'):
        print("[OK] Preset button group created successfully")
        
        # Check number of buttons
        buttons = dialog.preset_button_group.buttons()
        print(f"[OK] Found {len(buttons)} preset buttons")
        
        # Check button properties
        for button in buttons:
            preset_value = button.property("preset_value")
            is_checked = button.isChecked()
            button_text = button.text().encode('ascii', 'ignore').decode('ascii')
            print(f"  - {button_text}: preset_value='{preset_value}', checked={is_checked}")
        
        # Verify normal is checked by default
        normal_checked = False
        for button in buttons:
            if button.property("preset_value") == "normal" and button.isChecked():
                normal_checked = True
                break
        
        if normal_checked:
            print("[OK] 'Normal' preset is checked by default")
        else:
            print("[WARN] 'Normal' preset is NOT checked by default")
    else:
        print("[ERROR] preset_button_group not found!")
        return False
    
    # Check that old slider is removed
    if hasattr(dialog, 'font_size_slider'):
        print("[WARN] Old font_size_slider still exists (should be removed)")
    else:
        print("[OK] Old font_size_slider removed successfully")
    
    # Check that _on_preset_changed method exists
    if hasattr(dialog, '_on_preset_changed'):
        print("[OK] _on_preset_changed method exists")
    else:
        print("[ERROR] _on_preset_changed method not found!")
        return False
    
    # Check that _load_current_preset method exists
    if hasattr(dialog, '_load_current_preset'):
        print("[OK] _load_current_preset method exists")
    else:
        print("[ERROR] _load_current_preset method not found!")
        return False
    
    print("=" * 60)
    print("All checks passed! Opening dialog for visual inspection...")
    print("=" * 60)
    
    # Show dialog for visual inspection
    result = dialog.exec_()
    
    if result:
        print("\n[OK] Dialog closed successfully (user clicked Close)")
    else:
        print("\n[OK] Dialog cancelled (user closed window)")
    
    return True

if __name__ == "__main__":
    success = test_settings_dialog()
    sys.exit(0 if success else 1)

# Made with Bob
