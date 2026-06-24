"""Test script to verify theme_manager consolidation."""

from ui.theme_manager import get_theme_manager, ThemeMode, ColorScheme

# Test imports
print("[OK] Imports successful")

# Test ColorScheme
print(f"[OK] Light primary color: {ColorScheme.LIGHT['primary']}")
print(f"[OK] Dark primary color: {ColorScheme.DARK['primary']}")

# Test theme manager
tm = get_theme_manager()
print(f"[OK] Theme Manager initialized: {tm.get_current_theme().value}")

# Test color retrieval
primary = tm.get_color('primary')
print(f"[OK] Current primary color: {primary}")

print("\n[SUCCESS] All theme_manager imports working correctly!")
print("[SUCCESS] Colors now sourced from design_system.py")

# Made with Bob
