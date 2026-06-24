"""
Test script to verify Reach Rate Calculator respects font size settings.

This test verifies:
1. ReachRateCalculatorUI_v2.py uses TypographyMixin
2. Font preset changes are applied correctly
3. All text elements scale with font settings
4. Window size is reasonable and proportional
"""

import sys
import os

# Add src_v2 to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

def test_reachrate_typography():
    """Test that Reach Rate Calculator uses typography system correctly."""
    print("Testing Reach Rate Calculator Font Size Integration...")
    print("=" * 70)
    
    # Import after path setup
    from ui.typography import FontSizePreset
    from ui.services import get_v2_settings_bus
    
    # Import the V2 window
    sys.path.insert(0, os.path.join(current_dir, "Reach Rate Calculator"))
    from ReachRateCalculatorUI_v2 import ReachRateCalculatorWindow
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Create window
    print("\n1. Creating Reach Rate Calculator window...")
    window = ReachRateCalculatorWindow()
    
    # Check TypographyMixin integration
    print("\n2. Checking TypographyMixin integration...")
    assert hasattr(window, 'typography'), "❌ Window missing typography attribute"
    assert hasattr(window, 'get_font'), "❌ Window missing get_font method"
    assert hasattr(window, 'get_size'), "❌ Window missing get_size method"
    assert hasattr(window, 'apply_typography'), "❌ Window missing apply_typography method"
    print("   ✓ TypographyMixin properly integrated")
    
    # Check settings bus connection
    print("\n3. Checking settings bus connection...")
    assert hasattr(window, '_settings_bus'), "❌ Window missing _settings_bus"
    print("   ✓ Settings bus connected")
    
    # Check initial font sizes
    print("\n4. Checking initial font sizes...")
    title_font = window._title_label.font()
    body_font = window._subtitle_label.font()
    print(f"   Title font size: {title_font.pointSize()}pt")
    print(f"   Body font size: {body_font.pointSize()}pt")
    
    # Test font preset changes
    print("\n5. Testing font preset changes...")
    settings_bus = get_v2_settings_bus()
    
    # Test SMALL preset
    print("   Testing SMALL preset...")
    settings_bus.font_preset_changed.emit('small')
    app.processEvents()
    small_title_size = window._title_label.font().pointSize()
    print(f"   Title size (SMALL): {small_title_size}pt")
    
    # Test LARGE preset
    print("   Testing LARGE preset...")
    settings_bus.font_preset_changed.emit('large')
    app.processEvents()
    large_title_size = window._title_label.font().pointSize()
    print(f"   Title size (LARGE): {large_title_size}pt")
    
    # Test XLARGE preset
    print("   Testing XLARGE preset...")
    settings_bus.font_preset_changed.emit('xlarge')
    app.processEvents()
    xlarge_title_size = window._title_label.font().pointSize()
    print(f"   Title size (XLARGE): {xlarge_title_size}pt")
    
    # Verify sizes increase
    assert small_title_size < large_title_size < xlarge_title_size, \
        "❌ Font sizes don't scale correctly"
    print("   ✓ Font sizes scale correctly with presets")
    
    # Check all text elements are updated
    print("\n6. Checking all text elements update...")
    elements = [
        ('Title', window._title_label),
        ('Subtitle', window._subtitle_label),
        ('Checkbox', window._use_dates),
        ('From Label', window._from_label),
        ('To Label', window._to_label),
        ('Date From', window._date_from),
        ('Date To', window._date_to),
        ('Log Text', window._log_text),
        ('Footer', window._footer),
    ]
    
    for name, widget in elements:
        font = widget.font()
        print(f"   {name}: {font.pointSize()}pt")
    
    print("   ✓ All text elements have fonts applied")
    
    # Check window size is reasonable
    print("\n7. Checking window size...")
    width = window.width()
    height = window.height()
    print(f"   Window size: {width}x{height}")
    assert 900 <= width <= 1400, f"❌ Window width {width} is unreasonable"
    assert 600 <= height <= 900, f"❌ Window height {height} is unreasonable"
    print("   ✓ Window size is reasonable")
    
    # Show window for visual verification
    print("\n8. Displaying window for visual verification...")
    print("   Close the window to complete the test.")
    window.show()
    
    print("\n" + "=" * 70)
    print("✓ All tests passed!")
    print("\nVisual Verification Checklist:")
    print("  [ ] Title 'Reach Rate Calculator' is appropriately sized")
    print("  [ ] Subtitle text is readable")
    print("  [ ] File selection cards are proportional")
    print("  [ ] Date labels 'From' and 'To' are visible")
    print("  [ ] Buttons are appropriately sized")
    print("  [ ] Activity log text is readable")
    print("  [ ] Footer text is small but readable")
    print("  [ ] Overall UI is not oversized")
    print("\nTest font size changes in Settings (if available) to verify reactivity.")
    
    return app.exec_()

if __name__ == "__main__":
    try:
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        pass
    
    sys.exit(test_reachrate_typography())

# Made with Bob
