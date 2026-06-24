"""
Quick verification script to confirm Reach Rate Calculator changes are present.
"""

import os

file_path = os.path.join(os.path.dirname(__file__), "Reach Rate Calculator", "ReachRateCalculatorUI_v2.py")

print("Verifying Reach Rate Calculator UI changes...")
print("=" * 70)

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

checks = [
    ("Font preset connection", "font_preset_changed.connect(self._on_font_preset_changed)"),
    ("Initial typography call", "self.apply_typography()"),
    ("Window size 1000x700", "self.resize(1000, 700)"),
    ("Minimum size 900x650", "self.setMinimumSize(900, 650)"),
    ("Title uses h2", "self._title_label.setFont(self.get_font('h2', QFont.Bold))"),
    ("Subtitle uses body_sm", "self._subtitle_label.setFont(self.get_font('body_sm'))"),
    ("Spacing.MD margins", "main_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)"),
    ("Spacing.SM spacing", "main_layout.setSpacing(Spacing.SM)"),
    ("Card title h4", "self._files_card._title_label.setFont(self.get_font('h4', QFont.DemiBold))"),
]

all_passed = True
for check_name, check_string in checks:
    if check_string in content:
        print(f"[OK] {check_name}")
    else:
        print(f"[FAIL] {check_name} - NOT FOUND")
        all_passed = False

print("=" * 70)
if all_passed:
    print("[OK] All changes verified in ReachRateCalculatorUI_v2.py")
    print("\nNEXT STEPS:")
    print("1. Close any running Reach Rate Calculator windows")
    print("2. Launch from V2 main menu (python src_v2/main.py)")
    print("3. Click 'Reach Rate Calculator' card")
    print("4. Verify the UI is now comfortable and proportional")
else:
    print("[FAIL] Some changes are missing - file may need to be re-edited")

# Made with Bob
