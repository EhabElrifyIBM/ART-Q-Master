"""Test dark theme fix for main menu."""
from ui.services import V2ThemeService
from utils.runtime import get_theme_mode

# Get current theme
theme = get_theme_mode()
print(f"Current theme setting: {theme}")

# Get colors for the theme
svc = V2ThemeService()
colors = svc.colors_for(theme)

print(f"\nColors for '{theme}' theme:")
print(f"  Window BG: {colors['window_bg']}")
print(f"  Surface: {colors['surface']}")
print(f"  Surface Alt: {colors['surface_alt']}")
print(f"  Text Primary: {colors['text_primary']}")
print(f"  Text Secondary: {colors['text_secondary']}")

# Verify dark theme colors
if theme == "dark":
    expected_surface = "#111827"
    expected_window_bg = "#0f172a"
    expected_text = "#f8fafc"
    
    assert colors['surface'] == expected_surface, f"Surface should be {expected_surface}, got {colors['surface']}"
    assert colors['window_bg'] == expected_window_bg, f"Window BG should be {expected_window_bg}, got {colors['window_bg']}"
    assert colors['text_primary'] == expected_text, f"Text should be {expected_text}, got {colors['text_primary']}"
    
    print("\n✅ Dark theme colors are correct!")
    print("   - Cards/Header/Footer will have dark gray background (#111827)")
    print("   - Window background will be darker (#0f172a)")
    print("   - Text will be light (#f8fafc)")
else:
    print(f"\n✅ Theme '{theme}' colors loaded successfully!")

# Made with Bob
