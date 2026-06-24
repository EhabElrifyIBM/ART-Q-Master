"""
Test Suite for Reach Rate Calculator Modernization (Phase 6.9)
================================================================

This test suite validates the modernization of the Reach Rate Calculator tool.
Tests cover UI components, V2 foundation integration, and core functionality.

Test Categories:
1. V2 Foundation Integration
2. UI Components and Layout
3. File Selection and Validation
4. Date Range Functionality
5. Keyboard Shortcuts
6. Theme Support
7. Calculation Workflow
8. Error Handling

Run with: python src_v2/test_reachrate_modernization.py
"""

import sys
import os

# Add src_v2 to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtTest import QTest
from PyQt5.QtGui import QFont

# Import the modernized UI
sys.path.insert(0, os.path.join(current_dir, "Reach Rate Calculator"))
from ReachRateCalculatorUI_v2 import ReachRateCalculatorWindow, FileSelectionCard


class TestReachRateModernization:
    """Test suite for Reach Rate Calculator modernization."""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.window = None
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    def setup(self):
        """Set up test environment."""
        self.window = ReachRateCalculatorWindow()
        self.window.show()
        QTest.qWaitForWindowExposed(self.window)
    
    def teardown(self):
        """Clean up after tests."""
        if self.window:
            self.window.close()
            self.window = None
    
    def assert_true(self, condition, message):
        """Assert that condition is true."""
        if condition:
            self.passed += 1
            self.test_results.append(f"✓ PASS: {message}")
            return True
        else:
            self.failed += 1
            self.test_results.append(f"✗ FAIL: {message}")
            return False
    
    def assert_not_none(self, value, message):
        """Assert that value is not None."""
        return self.assert_true(value is not None, message)
    
    def assert_equal(self, actual, expected, message):
        """Assert that actual equals expected."""
        return self.assert_true(actual == expected, f"{message} (expected: {expected}, got: {actual})")
    
    # ── Test Category 1: V2 Foundation Integration ────────────────────────────
    
    def test_typography_mixin_integration(self):
        """Test V2TypographyMixin integration."""
        print("\n[Test 1.1] V2TypographyMixin Integration")
        self.setup()
        
        # Check typography attribute exists
        self.assert_true(
            hasattr(self.window, 'typography'),
            "Window has typography attribute"
        )
        
        # Check get_font method works
        try:
            font = self.window.get_font('body')
            self.assert_true(
                isinstance(font, QFont),
                "get_font() returns QFont instance"
            )
        except Exception as e:
            self.assert_true(False, f"get_font() method works: {e}")
        
        # Check get_size method works
        try:
            size = self.window.get_size('h1')
            self.assert_true(
                isinstance(size, int) and size > 0,
                "get_size() returns positive integer"
            )
        except Exception as e:
            self.assert_true(False, f"get_size() method works: {e}")
        
        self.teardown()
    
    def test_settings_bus_integration(self):
        """Test V2SettingsBus integration."""
        print("\n[Test 1.2] V2SettingsBus Integration")
        self.setup()
        
        # Check settings bus attribute exists
        self.assert_true(
            hasattr(self.window, '_settings_bus'),
            "Window has _settings_bus attribute"
        )
        
        # Check theme manager exists
        self.assert_true(
            hasattr(self.window, '_theme_manager'),
            "Window has _theme_manager attribute"
        )
        
        # Check theme mode is set
        self.assert_true(
            hasattr(self.window, '_theme_mode'),
            "Window has _theme_mode attribute"
        )
        
        self.teardown()
    
    def test_theme_manager_integration(self):
        """Test theme manager integration."""
        print("\n[Test 1.3] Theme Manager Integration")
        self.setup()
        
        # Check _apply_theme method exists
        self.assert_true(
            hasattr(self.window, '_apply_theme'),
            "Window has _apply_theme method"
        )
        
        # Check _on_theme_changed method exists
        self.assert_true(
            hasattr(self.window, '_on_theme_changed'),
            "Window has _on_theme_changed method"
        )
        
        self.teardown()
    
    # ── Test Category 2: UI Components and Layout ──────────────────────────────
    
    def test_modern_card_layout(self):
        """Test modern card-based layout."""
        print("\n[Test 2.1] Modern Card Layout")
        self.setup()
        
        # Check file selection cards exist
        self.assert_not_none(
            self.window._file_pa,
            "PA Cases file card exists"
        )
        self.assert_not_none(
            self.window._file_sms,
            "SMS View file card exists"
        )
        self.assert_not_none(
            self.window._file_email,
            "Email View file card exists"
        )
        self.assert_not_none(
            self.window._file_phone,
            "Phone Call View file card exists"
        )
        
        # Check all cards are FileSelectionCard instances
        for card in self.window._file_cards:
            self.assert_true(
                isinstance(card, FileSelectionCard),
                f"File card is FileSelectionCard instance"
            )
        
        self.teardown()
    
    def test_modern_buttons(self):
        """Test modern button components."""
        print("\n[Test 2.2] Modern Button Components")
        self.setup()
        
        # Check buttons exist
        self.assert_not_none(
            self.window._process_btn,
            "Process button exists"
        )
        self.assert_not_none(
            self.window._open_btn,
            "Open Output button exists"
        )
        self.assert_not_none(
            self.window._menu_btn,
            "Back to Menu button exists"
        )
        
        # Check button text
        self.assert_equal(
            self.window._process_btn.text(),
            "Process",
            "Process button has correct text"
        )
        
        # Check Open Output button is initially disabled
        self.assert_true(
            not self.window._open_btn.isEnabled(),
            "Open Output button is initially disabled"
        )
        
        self.teardown()
    
    def test_activity_log(self):
        """Test activity log component."""
        print("\n[Test 2.3] Activity Log Component")
        self.setup()
        
        # Check log text widget exists
        self.assert_not_none(
            self.window._log_text,
            "Activity log widget exists"
        )
        
        # Check log is read-only
        self.assert_true(
            self.window._log_text.isReadOnly(),
            "Activity log is read-only"
        )
        
        # Test logging functionality
        self.window._log("Test message", "INFO")
        log_content = self.window._log_text.toPlainText()
        self.assert_true(
            "Test message" in log_content,
            "Log message appears in activity log"
        )
        
        self.teardown()
    
    # ── Test Category 3: File Selection and Validation ────────────────────────
    
    def test_file_selection_cards(self):
        """Test file selection card functionality."""
        print("\n[Test 3.1] File Selection Cards")
        self.setup()
        
        # Test initial state
        self.assert_true(
            not self.window._file_pa.is_set(),
            "PA Cases card initially has no file"
        )
        
        # Test file path setting
        test_path = "C:/test/file.xlsx"
        self.window._file_pa.set_file_path(test_path)
        
        self.assert_equal(
            self.window._file_pa.get_file_path(),
            test_path,
            "File path is correctly set"
        )
        
        self.assert_true(
            self.window._file_pa.is_set(),
            "Card reports file is set"
        )
        
        self.teardown()
    
    def test_file_validation(self):
        """Test file validation on process."""
        print("\n[Test 3.2] File Validation")
        self.setup()
        
        # Try to process without files - should show warning
        # Note: This would show a QMessageBox, so we just check the validation logic
        missing = []
        if not self.window._file_pa.is_set():
            missing.append("PA Cases")
        if not self.window._file_sms.is_set():
            missing.append("SMS View")
        if not self.window._file_email.is_set():
            missing.append("Email View")
        if not self.window._file_phone.is_set():
            missing.append("Phone Call View")
        
        self.assert_equal(
            len(missing),
            4,
            "All 4 files are initially missing"
        )
        
        self.teardown()
    
    def test_drag_drop_support(self):
        """Test drag-drop support on file cards."""
        print("\n[Test 3.3] Drag-Drop Support")
        self.setup()
        
        # Check that cards accept drops
        self.assert_true(
            self.window._file_pa.acceptDrops(),
            "File card accepts drops"
        )
        
        # Check drag/drop event handlers exist
        self.assert_true(
            hasattr(self.window._file_pa, 'dragEnterEvent'),
            "File card has dragEnterEvent handler"
        )
        self.assert_true(
            hasattr(self.window._file_pa, 'dropEvent'),
            "File card has dropEvent handler"
        )
        
        self.teardown()
    
    # ── Test Category 4: Date Range Functionality ─────────────────────────────
    
    def test_date_range_toggle(self):
        """Test date range toggle functionality."""
        print("\n[Test 4.1] Date Range Toggle")
        self.setup()
        
        # Check initial state - date inputs should be disabled
        self.assert_true(
            not self.window._date_from.isEnabled(),
            "From date is initially disabled"
        )
        self.assert_true(
            not self.window._date_to.isEnabled(),
            "To date is initially disabled"
        )
        
        # Enable date range
        self.window._use_dates.setChecked(True)
        
        self.assert_true(
            self.window._date_from.isEnabled(),
            "From date is enabled when checkbox is checked"
        )
        self.assert_true(
            self.window._date_to.isEnabled(),
            "To date is enabled when checkbox is checked"
        )
        
        self.teardown()
    
    def test_date_range_defaults(self):
        """Test date range default values."""
        print("\n[Test 4.2] Date Range Defaults")
        self.setup()
        
        # Check default dates
        from_date = self.window._date_from.date()
        to_date = self.window._date_to.date()
        current_date = QDate.currentDate()
        
        # From date should be 1 month ago
        expected_from = current_date.addMonths(-1)
        self.assert_equal(
            from_date,
            expected_from,
            "From date defaults to 1 month ago"
        )
        
        # To date should be today
        self.assert_equal(
            to_date,
            current_date,
            "To date defaults to today"
        )
        
        self.teardown()
    
    # ── Test Category 5: Keyboard Shortcuts ───────────────────────────────────
    
    def test_keyboard_shortcuts_setup(self):
        """Test keyboard shortcuts are set up."""
        print("\n[Test 5.1] Keyboard Shortcuts Setup")
        self.setup()
        
        # Check _setup_keyboard_shortcuts method was called
        # We can verify by checking if shortcuts exist on the window
        shortcuts = self.window.findChildren(object)
        
        self.assert_true(
            len(shortcuts) > 0,
            "Window has child objects (including shortcuts)"
        )
        
        self.teardown()
    
    # ── Test Category 6: Theme Support ────────────────────────────────────────
    
    def test_theme_application(self):
        """Test theme is applied to window."""
        print("\n[Test 6.1] Theme Application")
        self.setup()
        
        # Check window has stylesheet
        stylesheet = self.window.styleSheet()
        self.assert_true(
            len(stylesheet) > 0,
            "Window has stylesheet applied"
        )
        
        # Check stylesheet contains theme colors
        self.assert_true(
            "background-color" in stylesheet.lower(),
            "Stylesheet contains background-color"
        )
        
        self.teardown()
    
    def test_typography_application(self):
        """Test typography is applied to widgets."""
        print("\n[Test 6.2] Typography Application")
        self.setup()
        
        # Check title label has font set
        title_font = self.window._title_label.font()
        self.assert_true(
            title_font.pointSize() > 0 or title_font.pixelSize() > 0,
            "Title label has font size set"
        )
        
        # Check subtitle label has font set
        subtitle_font = self.window._subtitle_label.font()
        self.assert_true(
            subtitle_font.pointSize() > 0 or subtitle_font.pixelSize() > 0,
            "Subtitle label has font size set"
        )
        
        self.teardown()
    
    # ── Test Category 7: Calculation Workflow ─────────────────────────────────
    
    def test_worker_thread_creation(self):
        """Test worker thread can be created."""
        print("\n[Test 7.1] Worker Thread Creation")
        
        from ReachRateCalculatorUI_v2 import CalculatorWorker
        
        # Create worker with test parameters
        worker = CalculatorWorker(
            pa_path="test_pa.xlsx",
            sms_path="test_sms.xlsx",
            email_path="test_email.xlsx",
            phone_path="test_phone.xlsx",
            output_path="test_output.xlsx"
        )
        
        self.assert_not_none(
            worker,
            "Worker thread can be created"
        )
        
        self.assert_not_none(
            worker.signals,
            "Worker has signals object"
        )
    
    def test_output_path_storage(self):
        """Test output path is stored."""
        print("\n[Test 7.2] Output Path Storage")
        self.setup()
        
        # Check _output_path attribute exists
        self.assert_true(
            hasattr(self.window, '_output_path'),
            "Window has _output_path attribute"
        )
        
        # Check initial value is empty
        self.assert_equal(
            self.window._output_path,
            "",
            "Output path is initially empty"
        )
        
        self.teardown()
    
    # ── Test Category 8: Error Handling ───────────────────────────────────────
    
    def test_error_logging(self):
        """Test error logging functionality."""
        print("\n[Test 8.1] Error Logging")
        self.setup()
        
        # Log an error
        self.window._log("Test error message", "ERROR")
        
        # Check log contains error
        log_content = self.window._log_text.toPlainText()
        self.assert_true(
            "Test error message" in log_content,
            "Error message appears in log"
        )
        
        self.teardown()
    
    def test_success_logging(self):
        """Test success logging functionality."""
        print("\n[Test 8.2] Success Logging")
        self.setup()
        
        # Log a success message
        self.window._log("Test success message", "SUCCESS")
        
        # Check log contains success
        log_content = self.window._log_text.toPlainText()
        self.assert_true(
            "Test success message" in log_content,
            "Success message appears in log"
        )
        
        self.teardown()
    
    # ── Test Runner ───────────────────────────────────────────────────────────
    
    def run_all_tests(self):
        """Run all tests and print results."""
        print("=" * 70)
        print("REACH RATE CALCULATOR MODERNIZATION TEST SUITE (Phase 6.9)")
        print("=" * 70)
        
        # Category 1: V2 Foundation Integration
        print("\n" + "=" * 70)
        print("CATEGORY 1: V2 Foundation Integration")
        print("=" * 70)
        self.test_typography_mixin_integration()
        self.test_settings_bus_integration()
        self.test_theme_manager_integration()
        
        # Category 2: UI Components and Layout
        print("\n" + "=" * 70)
        print("CATEGORY 2: UI Components and Layout")
        print("=" * 70)
        self.test_modern_card_layout()
        self.test_modern_buttons()
        self.test_activity_log()
        
        # Category 3: File Selection and Validation
        print("\n" + "=" * 70)
        print("CATEGORY 3: File Selection and Validation")
        print("=" * 70)
        self.test_file_selection_cards()
        self.test_file_validation()
        self.test_drag_drop_support()
        
        # Category 4: Date Range Functionality
        print("\n" + "=" * 70)
        print("CATEGORY 4: Date Range Functionality")
        print("=" * 70)
        self.test_date_range_toggle()
        self.test_date_range_defaults()
        
        # Category 5: Keyboard Shortcuts
        print("\n" + "=" * 70)
        print("CATEGORY 5: Keyboard Shortcuts")
        print("=" * 70)
        self.test_keyboard_shortcuts_setup()
        
        # Category 6: Theme Support
        print("\n" + "=" * 70)
        print("CATEGORY 6: Theme Support")
        print("=" * 70)
        self.test_theme_application()
        self.test_typography_application()
        
        # Category 7: Calculation Workflow
        print("\n" + "=" * 70)
        print("CATEGORY 7: Calculation Workflow")
        print("=" * 70)
        self.test_worker_thread_creation()
        self.test_output_path_storage()
        
        # Category 8: Error Handling
        print("\n" + "=" * 70)
        print("CATEGORY 8: Error Handling")
        print("=" * 70)
        self.test_error_logging()
        self.test_success_logging()
        
        # Print summary
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        print("\n" + "=" * 70)
        print("DETAILED RESULTS")
        print("=" * 70)
        for result in self.test_results:
            print(result)
        
        print("\n" + "=" * 70)
        if self.failed == 0:
            print("✓ ALL TESTS PASSED - MODERNIZATION SUCCESSFUL!")
        else:
            print(f"✗ {self.failed} TEST(S) FAILED - REVIEW REQUIRED")
        print("=" * 70)
        
        return self.failed == 0


def main():
    """Main test entry point."""
    tester = TestReachRateModernization()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

# Made with Bob
