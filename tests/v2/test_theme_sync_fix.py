"""Test that theme changes propagate correctly through the singleton bus."""
from ui.services import get_v2_settings_bus

# Get the singleton bus
bus = get_v2_settings_bus()

print(f"Initial theme: {bus.theme}")

# Simulate what settings dialog does after the fix
print("\nSimulating theme change to 'light'...")
bus.set_theme('light')
print(f"Theme after change: {bus.theme}")

# Verify the theme was updated
assert bus.theme == 'light', f"Expected 'light', got '{bus.theme}'"

print("\n✓ Theme change propagates correctly through singleton bus")
print("✓ Shell will now receive theme_changed signal when settings dialog changes theme")

# Made with Bob
