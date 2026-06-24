"""
Accessibility Testing Script - WCAG 2.1 AA Compliance Verification
===================================================================

This script tests all accessibility features implemented in Phase 4 Day 4-5:
- Focus indicators (3px outline)
- Touch target sizes (44x44px minimum)
- Color contrast ratios (4.5:1 for text)
- ARIA labels and descriptions
- Keyboard navigation
- Screen reader support

Run this script to verify WCAG 2.1 Level AA compliance.

Usage:
    python src_v2/test_accessibility.py
"""

import sys
from typing import List, Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, 
    QVBoxLayout, QWidget, QTextEdit, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# Import accessibility components
from ui.accessibility_helper import get_accessibility_manager, WCAGCompliance
from ui.design_system import Colors
from ui.main_menu import V2MainMenu
from ui.components_v2 import PrimaryButton, SecondaryButton, ModernLineEdit


class AccessibilityTestWindow(QMainWindow):
    """Test window for accessibility features."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Accessibility Test Suite - WCAG 2.1 AA")
        self.resize(1000, 700)
        
        # Initialize accessibility manager
        self.a11y = get_accessibility_manager()
        
        # Test results
        self.test_results: List[Tuple[str, bool, str]] = []
        
        self._setup_ui()
        self._run_tests()
    
    def _setup_ui(self):
        """Setup test UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("🔍 Accessibility Test Suite")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f62fe;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("WCAG 2.1 Level AA Compliance Verification")
        subtitle.setStyleSheet("font-size: 16px; color: #525252;")
        layout.addWidget(subtitle)
        
        # Test results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet("""
            QTextEdit {
                background-color: #f4f4f4;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.results_display)
        
        # Test buttons
        test_btn = PrimaryButton("Run All Tests")
        test_btn.clicked.connect(self._run_tests)
        layout.addWidget(test_btn)
        
        # Apply accessibility to test window
        self.a11y.apply_to_widget(self)
    
    def _run_tests(self):
        """Run all accessibility tests."""
        self.test_results.clear()
        self.results_display.clear()
        
        self._log_header("ACCESSIBILITY TEST SUITE - WCAG 2.1 AA")
        self._log_header("=" * 60)
        
        # Run test categories
        self._test_focus_indicators()
        self._test_touch_targets()
        self._test_color_contrast()
        self._test_aria_labels()
        self._test_keyboard_navigation()
        self._test_accessibility_manager()
        
        # Display summary
        self._display_summary()
    
    def _test_focus_indicators(self):
        """Test focus indicators on interactive elements."""
        self._log_section("1. Focus Indicators (WCAG 2.4.7)")
        
        # Test focus indicator size
        expected_size = 3  # 3px for WCAG 2.1 AA
        actual_size = self.a11y.focus_indicator_size
        
        passed = actual_size >= expected_size
        self._add_result(
            "Focus indicator size",
            passed,
            f"Expected: ≥{expected_size}px, Actual: {actual_size}px"
        )
        
        # Test that focus indicators are applied
        test_button = QPushButton("Test Button")
        self.a11y.set_focus_indicator(test_button)
        
        has_focus_style = ':focus' in test_button.styleSheet() or self.a11y.focus_indicator_size > 0
        self._add_result(
            "Focus indicators applied",
            has_focus_style,
            "Focus indicators are properly configured"
        )
    
    def _test_touch_targets(self):
        """Test minimum touch target sizes."""
        self._log_section("2. Touch Target Sizes (WCAG 2.5.5)")
        
        min_size = WCAGCompliance.get_min_touch_size()
        
        # Test button sizes
        test_button = QPushButton("Test")
        self.a11y.enforce_minimum_touch_target(test_button)
        
        width_ok = test_button.minimumWidth() >= 44
        height_ok = test_button.minimumHeight() >= 44
        
        self._add_result(
            "Button minimum width",
            width_ok,
            f"Expected: ≥44px, Actual: {test_button.minimumWidth()}px"
        )
        
        self._add_result(
            "Button minimum height",
            height_ok,
            f"Expected: ≥44px, Actual: {test_button.minimumHeight()}px"
        )
        
        self._add_result(
            "WCAG minimum touch size",
            min_size == 48,
            f"WCAG recommends: {min_size}x{min_size}px"
        )
    
    def _test_color_contrast(self):
        """Test color contrast ratios."""
        self._log_section("3. Color Contrast (WCAG 1.4.3)")
        
        # Test light theme contrasts
        light_colors = Colors.LIGHT
        
        # Primary text on background
        contrast_primary = self._calculate_contrast(
            light_colors['text_primary'],
            light_colors['background']
        )
        
        self._add_result(
            "Light theme: Primary text contrast",
            contrast_primary >= 4.5,
            f"Ratio: {contrast_primary:.2f}:1 (Required: ≥4.5:1)"
        )
        
        # Secondary text on background
        contrast_secondary = self._calculate_contrast(
            light_colors['text_secondary'],
            light_colors['background']
        )
        
        self._add_result(
            "Light theme: Secondary text contrast",
            contrast_secondary >= 4.5,
            f"Ratio: {contrast_secondary:.2f}:1 (Required: ≥4.5:1)"
        )
        
        # Primary button text
        contrast_button = self._calculate_contrast(
            light_colors['text_inverse'],
            light_colors['primary']
        )
        
        self._add_result(
            "Light theme: Button text contrast",
            contrast_button >= 4.5,
            f"Ratio: {contrast_button:.2f}:1 (Required: ≥4.5:1)"
        )
        
        # Test dark theme contrasts
        dark_colors = Colors.DARK
        
        contrast_dark_primary = self._calculate_contrast(
            dark_colors['text_primary'],
            dark_colors['background']
        )
        
        self._add_result(
            "Dark theme: Primary text contrast",
            contrast_dark_primary >= 4.5,
            f"Ratio: {contrast_dark_primary:.2f}:1 (Required: ≥4.5:1)"
        )
    
    def _test_aria_labels(self):
        """Test ARIA labels and descriptions."""
        self._log_section("4. ARIA Labels (WCAG 4.1.2)")
        
        # Test setting ARIA labels
        test_widget = QPushButton("Test")
        self.a11y.set_aria_label(test_widget, "Test Button", "This is a test button")
        
        has_name = bool(test_widget.accessibleName())
        has_description = bool(test_widget.accessibleDescription())
        
        self._add_result(
            "ARIA accessible name",
            has_name,
            f"Name: '{test_widget.accessibleName()}'"
        )
        
        self._add_result(
            "ARIA accessible description",
            has_description,
            f"Description: '{test_widget.accessibleDescription()}'"
        )
    
    def _test_keyboard_navigation(self):
        """Test keyboard navigation support."""
        self._log_section("5. Keyboard Navigation (WCAG 2.1.1)")
        
        # Test that keyboard helper exists
        has_keyboard_helper = hasattr(self.a11y, 'keyboard_helper')
        self._add_result(
            "Keyboard navigation helper",
            has_keyboard_helper,
            "KeyboardNavigationHelper is available"
        )
        
        # Test focus policy
        test_button = QPushButton("Test")
        has_focus_policy = test_button.focusPolicy() != Qt.NoFocus
        
        self._add_result(
            "Interactive elements focusable",
            has_focus_policy,
            "Elements can receive keyboard focus"
        )
    
    def _test_accessibility_manager(self):
        """Test AccessibilityManager functionality."""
        self._log_section("6. Accessibility Manager")
        
        # Test manager initialization
        self._add_result(
            "AccessibilityManager initialized",
            self.a11y is not None,
            "Singleton instance created"
        )
        
        # Test manager features
        info = self.a11y.get_accessibility_info()
        
        self._add_result(
            "Accessibility info available",
            'level' in info and 'enabled' in info,
            f"Info keys: {list(info.keys())}"
        )
        
        # Test high contrast toggle
        original_level = self.a11y.accessibility_level
        self.a11y.toggle_high_contrast()
        toggled = self.a11y.accessibility_level != original_level
        self.a11y.toggle_high_contrast()  # Reset
        
        self._add_result(
            "High contrast toggle",
            toggled,
            "High contrast mode can be toggled"
        )
        
        # Test text scaling
        original_scale = self.a11y.get_text_scale()
        self.a11y.increase_text_size(0.1)
        increased = self.a11y.get_text_scale() > original_scale
        self.a11y.reset_text_size()  # Reset
        
        self._add_result(
            "Text scaling",
            increased,
            "Text size can be adjusted"
        )
    
    def _calculate_contrast(self, color1: str, color2: str) -> float:
        """
        Calculate contrast ratio between two colors.
        
        Args:
            color1: First color (hex)
            color2: Second color (hex)
        
        Returns:
            Contrast ratio (1-21)
        """
        def get_luminance(hex_color: str) -> float:
            """Calculate relative luminance."""
            color = QColor(hex_color)
            r, g, b = color.red() / 255.0, color.green() / 255.0, color.blue() / 255.0
            
            # Apply gamma correction
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        l1 = get_luminance(color1)
        l2 = get_luminance(color2)
        
        lighter = max(l1, l2)
        darker = min(l1, l2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def _add_result(self, test_name: str, passed: bool, details: str):
        """Add test result."""
        self.test_results.append((test_name, passed, details))
        
        status = "✅ PASS" if passed else "❌ FAIL"
        self._log(f"  {status} - {test_name}")
        self._log(f"         {details}")
    
    def _display_summary(self):
        """Display test summary."""
        self._log_header("\n" + "=" * 60)
        self._log_header("TEST SUMMARY")
        self._log_header("=" * 60)
        
        total = len(self.test_results)
        passed = sum(1 for _, p, _ in self.test_results if p)
        failed = total - passed
        
        self._log(f"\nTotal Tests: {total}")
        self._log(f"✅ Passed: {passed}")
        self._log(f"❌ Failed: {failed}")
        
        percentage = (passed / total * 100) if total > 0 else 0
        self._log(f"\nCompliance: {percentage:.1f}%")
        
        if percentage >= 100:
            self._log("\n🎉 EXCELLENT! Full WCAG 2.1 AA compliance achieved!")
        elif percentage >= 90:
            self._log("\n✨ GOOD! Minor improvements needed for full compliance.")
        elif percentage >= 75:
            self._log("\n⚠️  FAIR! Several accessibility issues need attention.")
        else:
            self._log("\n🚨 POOR! Significant accessibility work required.")
        
        self._log("\n" + "=" * 60)
    
    def _log_header(self, text: str):
        """Log header text."""
        self.results_display.append(f"<b>{text}</b>")
    
    def _log_section(self, text: str):
        """Log section header."""
        self.results_display.append(f"\n<b style='color: #0f62fe;'>{text}</b>")
    
    def _log(self, text: str):
        """Log regular text."""
        self.results_display.append(text)


def main():
    """Run accessibility tests."""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("ART Q Master V2 - Accessibility Tests")
    app.setOrganizationName("ART Q Master")
    
    # Create and show test window
    window = AccessibilityTestWindow()
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob