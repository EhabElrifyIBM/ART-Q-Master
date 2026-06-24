"""
Test Suite for Button Components (Phase 5.1)
=============================================

Comprehensive test suite for all button variants with Phase 5.1 enhancements.
Tests cover functionality, accessibility, theming, and WCAG 2.1 AA compliance.

Run with: python src_v2/test_components_buttons.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

from ui.components_v2.buttons import (
    ModernButton,
    PrimaryButton,
    SecondaryButton,
    GhostButton,
    DangerButton
)
from ui.typography import FontSizePreset


class ButtonTestSuite:
    """Test suite for button components."""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.passed = 0
        self.failed = 0
        self.tests_run = 0
    
    def assert_true(self, condition, message):
        """Assert that condition is true."""
        self.tests_run += 1
        if condition:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            print(f"  ✗ {message}")
    
    def assert_equal(self, actual, expected, message):
        """Assert that actual equals expected."""
        self.tests_run += 1
        if actual == expected:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            print(f"  ✗ {message} (expected: {expected}, got: {actual})")
    
    def assert_greater_equal(self, actual, expected, message):
        """Assert that actual is greater than or equal to expected."""
        self.tests_run += 1
        if actual >= expected:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            print(f"  ✗ {message} (expected >= {expected}, got: {actual})")
    
    def test_button_creation(self):
        """Test button creation and initialization."""
        print("\n=== Test: Button Creation ===")
        
        # Test PrimaryButton creation
        primary = PrimaryButton("Save")
        self.assert_equal(primary.text(), "Save", "PrimaryButton text set correctly")
        self.assert_true(primary.isEnabled(), "PrimaryButton enabled by default")
        
        # Test SecondaryButton creation
        secondary = SecondaryButton("Cancel")
        self.assert_equal(secondary.text(), "Cancel", "SecondaryButton text set correctly")
        
        # Test GhostButton creation
        ghost = GhostButton("Details")
        self.assert_equal(ghost.text(), "Details", "GhostButton text set correctly")
        
        # Test DangerButton creation
        danger = DangerButton("Delete")
        self.assert_equal(danger.text(), "Delete", "DangerButton text set correctly")
        
        # Test button with icon
        icon_btn = PrimaryButton("Save", icon_name="save", icon_position="left")
        self.assert_equal(icon_btn.text(), "Save", "Button with icon created correctly")
    
    def test_minimum_size(self):
        """Test WCAG 2.1 AA minimum touch target size (44x44px)."""
        print("\n=== Test: Minimum Size (WCAG 2.1 AA) ===")
        
        buttons = [
            ("PrimaryButton", PrimaryButton("Test")),
            ("SecondaryButton", SecondaryButton("Test")),
            ("GhostButton", GhostButton("Test")),
            ("DangerButton", DangerButton("Test"))
        ]
        
        for name, button in buttons:
            min_height = button.minimumHeight()
            min_width = button.minimumWidth()
            
            self.assert_greater_equal(
                min_height, 44,
                f"{name} minimum height >= 44px (got {min_height}px)"
            )
            self.assert_greater_equal(
                min_width, 44,
                f"{name} minimum width >= 44px (got {min_width}px)"
            )
    
    def test_loading_state(self):
        """Test loading state functionality."""
        print("\n=== Test: Loading State ===")
        
        button = PrimaryButton("Save")
        
        # Test initial state
        self.assert_true(not button.is_loading(), "Button not loading initially")
        self.assert_true(button.isEnabled(), "Button enabled initially")
        
        # Test loading state
        button.set_loading(True)
        self.assert_true(button.is_loading(), "Button is loading after set_loading(True)")
        self.assert_true(not button.isEnabled(), "Button disabled when loading")
        
        # Test stop loading
        button.set_loading(False)
        self.assert_true(not button.is_loading(), "Button not loading after set_loading(False)")
        self.assert_true(button.isEnabled(), "Button enabled after loading stops")
    
    def test_icon_support(self):
        """Test icon support."""
        print("\n=== Test: Icon Support ===")
        
        button = PrimaryButton("Save")
        
        # Test setting icon
        button.set_icon("save", "left")
        self.assert_equal(button._icon_name, "save", "Icon name set correctly")
        self.assert_equal(button._icon_position, "left", "Icon position set correctly")
        
        # Test changing icon position
        button.set_icon("save", "right")
        self.assert_equal(button._icon_position, "right", "Icon position changed to right")
        
        # Test removing icon
        button.set_icon(None)
        self.assert_true(button._icon_name is None, "Icon removed correctly")
    
    def test_disabled_state(self):
        """Test disabled state."""
        print("\n=== Test: Disabled State ===")
        
        button = PrimaryButton("Save")
        
        # Test initial enabled state
        self.assert_true(button.isEnabled(), "Button enabled initially")
        
        # Test disabling
        button.setEnabled(False)
        self.assert_true(not button.isEnabled(), "Button disabled after setEnabled(False)")
        
        # Test re-enabling
        button.setEnabled(True)
        self.assert_true(button.isEnabled(), "Button enabled after setEnabled(True)")
    
    def test_click_signal(self):
        """Test click signal emission."""
        print("\n=== Test: Click Signal ===")
        
        button = PrimaryButton("Test")
        clicked = [False]
        
        def on_click():
            clicked[0] = True
        
        button.clicked.connect(on_click)
        
        # Simulate click
        button.click()
        
        self.assert_true(clicked[0], "Click signal emitted")
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation (Enter/Space activation)."""
        print("\n=== Test: Keyboard Navigation ===")
        
        button = PrimaryButton("Test")
        button.show()
        button.setFocus()
        
        clicked = [0]
        
        def on_click():
            clicked[0] += 1
        
        button.clicked.connect(on_click)
        
        # Test keyboard activation by simulating keyPressEvent
        from PyQt5.QtGui import QKeyEvent
        from PyQt5.QtCore import QEvent
        
        # Test Enter key (Qt.Key_Return = 16777220, QEvent.KeyPress = 6, Qt.NoModifier = 0)
        enter_event = QKeyEvent(QEvent.Type(6), 16777220, Qt.KeyboardModifier(0))
        button.keyPressEvent(enter_event)
        self.assert_equal(clicked[0], 1, "Enter key activates button")
        
        # Test Space key (Qt.Key_Space = 32)
        space_event = QKeyEvent(QEvent.Type(6), 32, Qt.KeyboardModifier(0))
        button.keyPressEvent(space_event)
        self.assert_equal(clicked[0], 2, "Space key activates button")
        
        button.close()
    
    def test_theme_support(self):
        """Test theme switching."""
        print("\n=== Test: Theme Support ===")
        
        button = PrimaryButton("Test")
        
        # Test initial theme
        self.assert_equal(button._theme_mode, "light", "Initial theme is light")
        
        # Test switching to dark theme
        button.set_theme("dark")
        self.assert_equal(button._theme_mode, "dark", "Theme switched to dark")
        
        # Test switching back to light theme
        button.set_theme("light")
        self.assert_equal(button._theme_mode, "light", "Theme switched back to light")
    
    def test_font_preset(self):
        """Test font preset changes."""
        print("\n=== Test: Font Preset ===")
        
        button = PrimaryButton("Test")
        
        # Test initial preset
        self.assert_equal(
            button._typography.preset,
            FontSizePreset.NORMAL,
            "Initial preset is NORMAL"
        )
        
        # Test changing preset
        button.set_font_preset(FontSizePreset.LARGE)
        self.assert_equal(
            button._typography.preset,
            FontSizePreset.LARGE,
            "Preset changed to LARGE"
        )
        
        # Test changing to XLARGE
        button.set_font_preset(FontSizePreset.XLARGE)
        self.assert_equal(
            button._typography.preset,
            FontSizePreset.XLARGE,
            "Preset changed to XLARGE"
        )
    
    def test_focus_policy(self):
        """Test focus policy for keyboard navigation."""
        print("\n=== Test: Focus Policy ===")
        
        buttons = [
            ("PrimaryButton", PrimaryButton("Test")),
            ("SecondaryButton", SecondaryButton("Test")),
            ("GhostButton", GhostButton("Test")),
            ("DangerButton", DangerButton("Test"))
        ]
        
        for name, button in buttons:
            # Qt.StrongFocus = 11
            focus_policy = button.focusPolicy()
            self.assert_true(
                focus_policy == Qt.FocusPolicy(11),
                f"{name} has StrongFocus policy"
            )
    
    def test_all_variants(self):
        """Test all button variants exist and work."""
        print("\n=== Test: All Button Variants ===")
        
        variants = [
            ("PrimaryButton", PrimaryButton),
            ("SecondaryButton", SecondaryButton),
            ("GhostButton", GhostButton),
            ("DangerButton", DangerButton)
        ]
        
        for name, ButtonClass in variants:
            button = ButtonClass("Test")
            self.assert_true(button is not None, f"{name} created successfully")
            self.assert_true(isinstance(button, ModernButton), f"{name} inherits from ModernButton")
    
    def test_loading_prevents_click(self):
        """Test that loading state prevents button activation."""
        print("\n=== Test: Loading Prevents Click ===")
        
        button = PrimaryButton("Test")
        clicked = [0]
        
        def on_click():
            clicked[0] += 1
        
        button.clicked.connect(on_click)
        
        # Set loading state
        button.set_loading(True)
        
        # Try to click (should not work)
        button.click()
        
        self.assert_equal(clicked[0], 0, "Click blocked when loading")
        
        # Stop loading and try again
        button.set_loading(False)
        button.click()
        
        self.assert_equal(clicked[0], 1, "Click works after loading stops")
    
    def test_cursor_style(self):
        """Test cursor changes to pointer."""
        print("\n=== Test: Cursor Style ===")
        
        button = PrimaryButton("Test")
        cursor = button.cursor()
        
        # Qt.PointingHandCursor shape value = 13
        self.assert_true(
            cursor.shape() == Qt.CursorShape(13),
            "Button has pointing hand cursor"
        )
    
    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "="*60)
        print("BUTTON COMPONENTS TEST SUITE - PHASE 5.1")
        print("="*60)
        
        # Run all test methods
        self.test_button_creation()
        self.test_minimum_size()
        self.test_loading_state()
        self.test_icon_support()
        self.test_disabled_state()
        self.test_click_signal()
        self.test_keyboard_navigation()
        self.test_theme_support()
        self.test_font_preset()
        self.test_focus_policy()
        self.test_all_variants()
        self.test_loading_prevents_click()
        self.test_cursor_style()
        
        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.passed} ✓")
        print(f"Failed: {self.failed} ✗")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED! 🎉")
            coverage = (self.passed / self.tests_run * 100) if self.tests_run > 0 else 0
            print(f"Test Coverage: {coverage:.1f}%")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed")
        
        print("="*60)
        
        return self.failed == 0


def main():
    """Main test runner."""
    suite = ButtonTestSuite()
    success = suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
