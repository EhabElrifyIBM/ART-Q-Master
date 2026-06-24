"""
Test Suite for Input Components (Phase 5.1)
============================================

Comprehensive test suite for all input types with Phase 5.1 enhancements.
Tests cover functionality, validation, accessibility, and WCAG 2.1 AA compliance.

Run with: python src_v2/test_components_inputs.py
"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

from ui.components_v2.inputs import (
    ModernLineEdit,
    ModernTextEdit,
    ModernComboBox,
    ModernCheckBox,
    ModernRadioButton
)
from ui.typography import FontSizePreset


class InputTestSuite:
    """Test suite for input components."""
    
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
    
    def test_input_creation(self):
        """Test input creation and initialization."""
        print("\n=== Test: Input Creation ===")
        
        # Test ModernLineEdit creation
        line_edit = ModernLineEdit()
        self.assert_true(line_edit is not None, "ModernLineEdit created")
        self.assert_true(line_edit.isEnabled(), "ModernLineEdit enabled by default")
        
        # Test ModernTextEdit creation
        text_edit = ModernTextEdit()
        self.assert_true(text_edit is not None, "ModernTextEdit created")
        
        # Test ModernComboBox creation
        combo = ModernComboBox()
        self.assert_true(combo is not None, "ModernComboBox created")
        
        # Test ModernCheckBox creation
        checkbox = ModernCheckBox("Test")
        self.assert_equal(checkbox.text(), "Test", "ModernCheckBox text set")
        
        # Test ModernRadioButton creation
        radio = ModernRadioButton("Option")
        self.assert_equal(radio.text(), "Option", "ModernRadioButton text set")
    
    def test_minimum_size(self):
        """Test WCAG 2.1 AA minimum touch target size (44x44px)."""
        print("\n=== Test: Minimum Size (WCAG 2.1 AA) ===")
        
        inputs = [
            ("ModernLineEdit", ModernLineEdit()),
            ("ModernComboBox", ModernComboBox()),
            ("ModernCheckBox", ModernCheckBox("Test")),
            ("ModernRadioButton", ModernRadioButton("Test"))
        ]
        
        for name, input_widget in inputs:
            min_height = input_widget.minimumHeight()
            
            self.assert_greater_equal(
                min_height, 44,
                f"{name} minimum height >= 44px (got {min_height}px)"
            )
    
    def test_validation_support(self):
        """Test validation support."""
        print("\n=== Test: Validation Support ===")
        
        # Test ModernLineEdit validation
        line_edit = ModernLineEdit()
        line_edit.set_required(True)
        
        # Empty required field should fail validation
        self.assert_true(not line_edit.validate(), "Empty required field fails validation")
        self.assert_true(line_edit._has_error, "Error state set after failed validation")
        
        # Non-empty required field should pass validation
        line_edit.setText("Test")
        self.assert_true(line_edit.validate(), "Non-empty required field passes validation")
        self.assert_true(not line_edit._has_error, "Error state cleared after successful validation")
        
        # Test ModernTextEdit validation
        text_edit = ModernTextEdit()
        text_edit.set_required(True)
        self.assert_true(not text_edit.validate(), "Empty required text area fails validation")
        
        text_edit.setPlainText("Test content")
        self.assert_true(text_edit.validate(), "Non-empty required text area passes validation")
        
        # Test ModernComboBox validation
        combo = ModernComboBox()
        combo.addItems(["Option 1", "Option 2"])
        combo.set_required(True)
        combo.setCurrentIndex(-1)  # No selection
        self.assert_true(not combo.validate(), "Combo with no selection fails validation")
        
        combo.setCurrentIndex(0)
        self.assert_true(combo.validate(), "Combo with selection passes validation")
    
    def test_error_state(self):
        """Test error state functionality."""
        print("\n=== Test: Error State ===")
        
        line_edit = ModernLineEdit()
        
        # Test setting error
        line_edit.set_error(True, "This field is required")
        self.assert_true(line_edit._has_error, "Error state set")
        self.assert_equal(line_edit.get_error_message(), "This field is required", "Error message set")
        
        # Test clearing error
        line_edit.set_error(False)
        self.assert_true(not line_edit._has_error, "Error state cleared")
        self.assert_equal(line_edit.get_error_message(), "", "Error message cleared")
    
    def test_helper_text(self):
        """Test helper text support."""
        print("\n=== Test: Helper Text ===")
        
        line_edit = ModernLineEdit()
        
        # Test setting helper text
        line_edit.set_helper_text("Enter your email address")
        self.assert_equal(
            line_edit.get_helper_text(),
            "Enter your email address",
            "Helper text set correctly"
        )
        
        # Test clearing helper text
        line_edit.set_helper_text("")
        self.assert_equal(line_edit.get_helper_text(), "", "Helper text cleared")
    
    def test_required_field(self):
        """Test required field indicator."""
        print("\n=== Test: Required Field ===")
        
        line_edit = ModernLineEdit()
        
        # Test initial state
        self.assert_true(not line_edit.is_required(), "Field not required by default")
        
        # Test setting required
        line_edit.set_required(True)
        self.assert_true(line_edit.is_required(), "Field marked as required")
        
        # Test clearing required
        line_edit.set_required(False)
        self.assert_true(not line_edit.is_required(), "Field no longer required")
    
    def test_clear_button(self):
        """Test clear button for text inputs."""
        print("\n=== Test: Clear Button ===")
        
        # Test with clear button enabled
        line_edit = ModernLineEdit(show_clear_button=True)
        self.assert_true(line_edit.isClearButtonEnabled(), "Clear button enabled")
        
        # Test with clear button disabled
        line_edit_no_clear = ModernLineEdit(show_clear_button=False)
        self.assert_true(not line_edit_no_clear.isClearButtonEnabled(), "Clear button disabled")
    
    def test_text_input_signals(self):
        """Test text input signals."""
        print("\n=== Test: Text Input Signals ===")
        
        line_edit = ModernLineEdit()
        text_changed = [False]
        validation_changed = [False, True, ""]
        
        def on_text_changed():
            text_changed[0] = True
        
        def on_validation_changed(is_valid, message):
            validation_changed[0] = True
            validation_changed[1] = is_valid
            validation_changed[2] = message
        
        line_edit.textChanged.connect(on_text_changed)
        line_edit.validationChanged.connect(on_validation_changed)
        
        # Test text changed signal
        line_edit.setText("Test")
        self.assert_true(text_changed[0], "textChanged signal emitted")
        
        # Test validation changed signal
        line_edit.set_error(True, "Error message")
        self.assert_true(validation_changed[0], "validationChanged signal emitted")
        self.assert_true(not validation_changed[1], "validationChanged reports invalid state")
        self.assert_equal(validation_changed[2], "Error message", "validationChanged includes message")
    
    def test_combo_box_items(self):
        """Test combo box item management."""
        print("\n=== Test: Combo Box Items ===")
        
        combo = ModernComboBox()
        
        # Test adding single item
        combo.addItem("Option 1")
        self.assert_equal(combo.count(), 1, "Single item added")
        self.assert_equal(combo.itemText(0), "Option 1", "Item text correct")
        
        # Test adding multiple items
        combo.addItems(["Option 2", "Option 3"])
        self.assert_equal(combo.count(), 3, "Multiple items added")
        
        # Test current selection
        combo.setCurrentIndex(1)
        self.assert_equal(combo.currentText(), "Option 2", "Current text correct")
        self.assert_equal(combo.currentIndex(), 1, "Current index correct")
    
    def test_checkbox_state(self):
        """Test checkbox state management."""
        print("\n=== Test: Checkbox State ===")
        
        checkbox = ModernCheckBox("Test")
        
        # Test initial state
        self.assert_true(not checkbox.isChecked(), "Checkbox unchecked by default")
        
        # Test checking
        checkbox.setChecked(True)
        self.assert_true(checkbox.isChecked(), "Checkbox checked")
        
        # Test unchecking
        checkbox.setChecked(False)
        self.assert_true(not checkbox.isChecked(), "Checkbox unchecked")
    
    def test_radio_button_state(self):
        """Test radio button state management."""
        print("\n=== Test: Radio Button State ===")
        
        radio = ModernRadioButton("Option")
        
        # Test initial state
        self.assert_true(not radio.isChecked(), "Radio button unchecked by default")
        
        # Test checking
        radio.setChecked(True)
        self.assert_true(radio.isChecked(), "Radio button checked")
    
    def test_theme_support(self):
        """Test theme switching."""
        print("\n=== Test: Theme Support ===")
        
        inputs = [
            ("ModernLineEdit", ModernLineEdit()),
            ("ModernTextEdit", ModernTextEdit()),
            ("ModernComboBox", ModernComboBox()),
            ("ModernCheckBox", ModernCheckBox("Test")),
            ("ModernRadioButton", ModernRadioButton("Test"))
        ]
        
        for name, input_widget in inputs:
            # Test initial theme
            self.assert_equal(input_widget._theme_mode, "light", f"{name} initial theme is light")
            
            # Test switching to dark theme
            input_widget.set_theme("dark")
            self.assert_equal(input_widget._theme_mode, "dark", f"{name} theme switched to dark")
            
            # Test switching back to light theme
            input_widget.set_theme("light")
            self.assert_equal(input_widget._theme_mode, "light", f"{name} theme switched back to light")
    
    def test_font_preset(self):
        """Test font preset changes."""
        print("\n=== Test: Font Preset ===")
        
        line_edit = ModernLineEdit()
        
        # Test initial preset
        self.assert_equal(
            line_edit._typography.preset,
            FontSizePreset.NORMAL,
            "Initial preset is NORMAL"
        )
        
        # Test changing preset via internal method
        line_edit._on_preset_changed("large")
        self.assert_equal(
            line_edit._typography.preset,
            FontSizePreset.LARGE,
            "Preset changed to LARGE"
        )
    
    def test_focus_policy(self):
        """Test focus policy for keyboard navigation."""
        print("\n=== Test: Focus Policy ===")
        
        inputs = [
            ("ModernLineEdit", ModernLineEdit()),
            ("ModernTextEdit", ModernTextEdit()),
            ("ModernComboBox", ModernComboBox()),
            ("ModernCheckBox", ModernCheckBox("Test")),
            ("ModernRadioButton", ModernRadioButton("Test"))
        ]
        
        for name, input_widget in inputs:
            # Qt.StrongFocus = 11
            focus_policy = input_widget.focusPolicy()
            self.assert_true(
                focus_policy == Qt.FocusPolicy(11),
                f"{name} has StrongFocus policy"
            )
    
    def test_placeholder_text(self):
        """Test placeholder text support."""
        print("\n=== Test: Placeholder Text ===")
        
        line_edit = ModernLineEdit()
        
        # Test setting placeholder
        line_edit.setPlaceholderText("Enter text here")
        self.assert_equal(
            line_edit.placeholderText(),
            "Enter text here",
            "Placeholder text set correctly"
        )
    
    def test_disabled_state(self):
        """Test disabled state."""
        print("\n=== Test: Disabled State ===")
        
        inputs = [
            ("ModernLineEdit", ModernLineEdit()),
            ("ModernComboBox", ModernComboBox()),
            ("ModernCheckBox", ModernCheckBox("Test"))
        ]
        
        for name, input_widget in inputs:
            # Test initial enabled state
            self.assert_true(input_widget.isEnabled(), f"{name} enabled initially")
            
            # Test disabling
            input_widget.setEnabled(False)
            self.assert_true(not input_widget.isEnabled(), f"{name} disabled after setEnabled(False)")
            
            # Test re-enabling
            input_widget.setEnabled(True)
            self.assert_true(input_widget.isEnabled(), f"{name} enabled after setEnabled(True)")
    
    def test_text_area_multiline(self):
        """Test text area multi-line support."""
        print("\n=== Test: Text Area Multi-line ===")
        
        text_edit = ModernTextEdit()
        
        # Test setting multi-line text
        multi_line_text = "Line 1\nLine 2\nLine 3"
        text_edit.setPlainText(multi_line_text)
        
        self.assert_equal(
            text_edit.toPlainText(),
            multi_line_text,
            "Multi-line text set correctly"
        )
    
    def test_validation_signal_emission(self):
        """Test that validation signals are emitted correctly."""
        print("\n=== Test: Validation Signal Emission ===")
        
        line_edit = ModernLineEdit()
        signal_data = []
        
        def on_validation_changed(is_valid, message):
            signal_data.append((is_valid, message))
        
        line_edit.validationChanged.connect(on_validation_changed)
        
        # Trigger validation change
        line_edit.set_error(True, "Test error")
        
        self.assert_equal(len(signal_data), 1, "Validation signal emitted once")
        self.assert_true(not signal_data[0][0], "Signal reports invalid state")
        self.assert_equal(signal_data[0][1], "Test error", "Signal includes error message")
    
    def run_all_tests(self):
        """Run all tests and print summary."""
        print("\n" + "="*60)
        print("INPUT COMPONENTS TEST SUITE - PHASE 5.1")
        print("="*60)
        
        # Run all test methods
        self.test_input_creation()
        self.test_minimum_size()
        self.test_validation_support()
        self.test_error_state()
        self.test_helper_text()
        self.test_required_field()
        self.test_clear_button()
        self.test_text_input_signals()
        self.test_combo_box_items()
        self.test_checkbox_state()
        self.test_radio_button_state()
        self.test_theme_support()
        self.test_font_preset()
        self.test_focus_policy()
        self.test_placeholder_text()
        self.test_disabled_state()
        self.test_text_area_multiline()
        self.test_validation_signal_emission()
        
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
    suite = InputTestSuite()
    success = suite.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
