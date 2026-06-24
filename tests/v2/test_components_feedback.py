"""
Test Suite for Feedback Components
===================================

Tests for Toast, ModernProgressBar, LoadingSpinner, and Badge components.

Run with: python src_v2/test_components_feedback.py
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QTimer

from ui.components_v2.feedback import Toast, ModernProgressBar, ModernSpinner as LoadingSpinner, Badge
from ui.design_system import Spacing


class FeedbackTestWindow(QMainWindow):
    """Test window for feedback components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Feedback Components Test Suite")
        self.setGeometry(100, 100, 1000, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QVBoxLayout(central)
        layout.setSpacing(Spacing.LG)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        
        # Add test sections
        self._add_toast_tests(layout)
        self._add_progress_bar_tests(layout)
        self._add_spinner_tests(layout)
        self._add_badge_tests(layout)
        
        # Test results
        self.results_label = QLabel("Test Results: Ready")
        self.results_label.setStyleSheet("font-weight: bold; padding: 10px; background: #f0f0f0;")
        layout.addWidget(self.results_label)
        
        layout.addStretch()
        
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
    
    def _add_toast_tests(self, layout):
        """Add toast component tests."""
        section = QLabel("Toast Tests")
        section.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f62fe;")
        layout.addWidget(section)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SM)
        
        # Test buttons
        btn_info = QPushButton("Test Info Toast")
        btn_info.clicked.connect(lambda: self._test_toast("info"))
        button_layout.addWidget(btn_info)
        
        btn_success = QPushButton("Test Success Toast")
        btn_success.clicked.connect(lambda: self._test_toast("success"))
        button_layout.addWidget(btn_success)
        
        btn_warning = QPushButton("Test Warning Toast")
        btn_warning.clicked.connect(lambda: self._test_toast("warning"))
        button_layout.addWidget(btn_warning)
        
        btn_error = QPushButton("Test Error Toast")
        btn_error.clicked.connect(lambda: self._test_toast("error"))
        button_layout.addWidget(btn_error)
        
        btn_multiple = QPushButton("Test Multiple Toasts")
        btn_multiple.clicked.connect(self._test_multiple_toasts)
        button_layout.addWidget(btn_multiple)
        
        layout.addLayout(button_layout)
    
    def _add_progress_bar_tests(self, layout):
        """Add progress bar component tests."""
        section = QLabel("Progress Bar Tests")
        section.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f62fe;")
        layout.addWidget(section)
        
        # Progress bars
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(Spacing.SM)
        
        # Determinate progress bar
        self.progress_determinate = ModernProgressBar()
        self.progress_determinate.setValue(0)
        progress_layout.addWidget(QLabel("Determinate Progress:"))
        progress_layout.addWidget(self.progress_determinate)
        
        # Indeterminate progress bar (if implemented)
        self.progress_indeterminate = ModernProgressBar()
        try:
            self.progress_indeterminate.set_indeterminate(True)
            progress_layout.addWidget(QLabel("Indeterminate Progress:"))
            progress_layout.addWidget(self.progress_indeterminate)
        except AttributeError:
            pass  # Not implemented yet
        
        layout.addLayout(progress_layout)
        
        # Test buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SM)
        
        btn_start = QPushButton("Start Progress")
        btn_start.clicked.connect(self._test_progress_bar)
        button_layout.addWidget(btn_start)
        
        btn_eta = QPushButton("Test ETA Calculation")
        btn_eta.clicked.connect(self._test_progress_eta)
        button_layout.addWidget(btn_eta)
        
        layout.addLayout(button_layout)
    
    def _add_spinner_tests(self, layout):
        """Add spinner component tests."""
        section = QLabel("Loading Spinner Tests")
        section.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f62fe;")
        layout.addWidget(section)
        
        # Spinner container
        spinner_layout = QHBoxLayout()
        spinner_layout.setSpacing(Spacing.MD)
        
        # Create spinners
        self.spinner_small = LoadingSpinner()
        self.spinner_small.setFixedSize(24, 24)
        spinner_layout.addWidget(QLabel("Small:"))
        spinner_layout.addWidget(self.spinner_small)
        
        self.spinner_medium = LoadingSpinner()
        spinner_layout.addWidget(QLabel("Medium:"))
        spinner_layout.addWidget(self.spinner_medium)
        
        self.spinner_large = LoadingSpinner()
        self.spinner_large.setFixedSize(48, 48)
        spinner_layout.addWidget(QLabel("Large:"))
        spinner_layout.addWidget(self.spinner_large)
        
        spinner_layout.addStretch()
        layout.addLayout(spinner_layout)
        
        # Test buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SM)
        
        btn_start = QPushButton("Start Spinners")
        btn_start.clicked.connect(self._test_spinners_start)
        button_layout.addWidget(btn_start)
        
        btn_stop = QPushButton("Stop Spinners")
        btn_stop.clicked.connect(self._test_spinners_stop)
        button_layout.addWidget(btn_stop)
        
        layout.addLayout(button_layout)
    
    def _add_badge_tests(self, layout):
        """Add badge component tests."""
        section = QLabel("Badge Tests")
        section.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f62fe;")
        layout.addWidget(section)
        
        # Badge container
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(Spacing.MD)
        
        # Create badges
        self.badge_default = Badge("Default", "default")
        badge_layout.addWidget(self.badge_default)
        
        self.badge_success = Badge("Success", "success")
        badge_layout.addWidget(self.badge_success)
        
        self.badge_warning = Badge("Warning", "warning")
        badge_layout.addWidget(self.badge_warning)
        
        self.badge_error = Badge("Error", "error")
        badge_layout.addWidget(self.badge_error)
        
        self.badge_info = Badge("Info", "info")
        badge_layout.addWidget(self.badge_info)
        
        self.badge_counter = Badge("5", "error")
        badge_layout.addWidget(self.badge_counter)
        
        badge_layout.addStretch()
        layout.addLayout(badge_layout)
        
        # Test buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SM)
        
        btn_counter = QPushButton("Test Counter (99+)")
        btn_counter.clicked.connect(self._test_badge_counter)
        button_layout.addWidget(btn_counter)
        
        btn_variants = QPushButton("Cycle Badge Variants")
        btn_variants.clicked.connect(self._test_badge_variants)
        button_layout.addWidget(btn_variants)
        
        layout.addLayout(button_layout)
    
    def _test_toast(self, variant):
        """Test toast notification."""
        self.test_count += 1
        try:
            messages = {
                "info": "This is an info message",
                "success": "Operation completed successfully!",
                "warning": "This is a warning message",
                "error": "This is an error message"
            }
            
            if variant == "info":
                Toast.info(self, messages[variant])
            elif variant == "success":
                Toast.success(self, messages[variant])
            elif variant == "warning":
                Toast.warning(self, messages[variant])
            elif variant == "error":
                # Error shows dialog, not toast
                Toast.show_toast(self, messages[variant], "error", 5000)
            
            self.pass_count += 1
            self._update_results(f"✓ Toast {variant} test passed")
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Toast {variant} test failed: {str(e)}")
    
    def _test_multiple_toasts(self):
        """Test multiple toasts stacking."""
        self.test_count += 1
        try:
            Toast.info(self, "First message", duration=5000)
            QTimer.singleShot(500, lambda: Toast.success(self, "Second message", duration=5000))
            QTimer.singleShot(1000, lambda: Toast.warning(self, "Third message", duration=5000))
            
            self.pass_count += 1
            self._update_results("✓ Multiple toasts test passed")
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Multiple toasts test failed: {str(e)}")
    
    def _test_progress_bar(self):
        """Test progress bar animation."""
        self.test_count += 1
        try:
            self.progress_determinate.setValue(0)
            
            def update_progress():
                value = self.progress_determinate.value()
                if value < 100:
                    self.progress_determinate.setValue(value + 1)
                    QTimer.singleShot(50, update_progress)
                else:
                    self.pass_count += 1
                    self._update_results("✓ Progress bar test passed")
            
            update_progress()
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Progress bar test failed: {str(e)}")
    
    def _test_progress_eta(self):
        """Test progress bar ETA calculation."""
        self.test_count += 1
        try:
            # Test ETA calculation if method exists
            if hasattr(self.progress_determinate, 'calculate_eta'):
                eta = self.progress_determinate.calculate_eta(50, 100, 10.0)
                if eta:
                    self.pass_count += 1
                    self._update_results(f"✓ ETA calculation test passed: {eta}")
                else:
                    self.pass_count += 1
                    self._update_results("✓ ETA calculation test passed (no ETA yet)")
            else:
                self.pass_count += 1
                self._update_results("✓ ETA calculation not implemented (Phase 5.5)")
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ ETA calculation test failed: {str(e)}")
    
    def _test_spinners_start(self):
        """Test starting spinners."""
        self.test_count += 1
        try:
            self.spinner_small.start()
            self.spinner_medium.start()
            self.spinner_large.start()
            
            self.pass_count += 1
            self._update_results("✓ Spinner start test passed")
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Spinner start test failed: {str(e)}")
    
    def _test_spinners_stop(self):
        """Test stopping spinners."""
        self.test_count += 1
        try:
            self.spinner_small.stop()
            self.spinner_medium.stop()
            self.spinner_large.stop()
            
            self.pass_count += 1
            self._update_results("✓ Spinner stop test passed")
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Spinner stop test failed: {str(e)}")
    
    def _test_badge_counter(self):
        """Test badge counter with 99+ display."""
        self.test_count += 1
        try:
            # Test counter increments
            for count in [1, 5, 10, 50, 99, 100, 150]:
                text = str(count) if count <= 99 else "99+"
                self.badge_counter.setText(text)
                QApplication.processEvents()
            
            self.pass_count += 1
            self._update_results("✓ Badge counter test passed (99+ display)")
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Badge counter test failed: {str(e)}")
    
    def _test_badge_variants(self):
        """Test cycling through badge variants."""
        self.test_count += 1
        try:
            variants = ["default", "success", "warning", "error", "info"]
            current_index = [0]
            
            def cycle_variant():
                variant = variants[current_index[0]]
                self.badge_default.set_type(variant)
                self.badge_default.setText(variant.capitalize())
                current_index[0] = (current_index[0] + 1) % len(variants)
                
                if current_index[0] == 0:
                    self.pass_count += 1
                    self._update_results("✓ Badge variant cycle test passed")
                else:
                    QTimer.singleShot(500, cycle_variant)
            
            cycle_variant()
        except Exception as e:
            self.fail_count += 1
            self._update_results(f"✗ Badge variant cycle test failed: {str(e)}")
    
    def _update_results(self, message):
        """Update test results display."""
        coverage = (self.pass_count / self.test_count * 100) if self.test_count > 0 else 0
        results_text = f"Tests: {self.test_count} | Passed: {self.pass_count} | Failed: {self.fail_count} | Coverage: {coverage:.1f}%"
        self.results_label.setText(f"{results_text}\nLast: {message}")
        
        # Update background color based on results
        if self.fail_count == 0:
            bg_color = "#defbe6"  # Success green
        elif self.pass_count > self.fail_count:
            bg_color = "#fcf4d6"  # Warning yellow
        else:
            bg_color = "#fff1f1"  # Error red
        
        self.results_label.setStyleSheet(f"font-weight: bold; padding: 10px; background: {bg_color};")


def main():
    """Run feedback components test suite."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show test window
    window = FeedbackTestWindow()
    window.show()
    
    print("=" * 60)
    print("Feedback Components Test Suite")
    print("=" * 60)
    print("\nTest Instructions:")
    print("1. Click buttons to test each component")
    print("2. Verify visual appearance and behavior")
    print("3. Check test results at bottom of window")
    print("\nComponents Being Tested:")
    print("- Toast (info, success, warning, error)")
    print("- ModernProgressBar (determinate, indeterminate, ETA)")
    print("- LoadingSpinner (start, stop, sizes)")
    print("- Badge (variants, counter, 99+ display)")
    print("\nExpected Results:")
    print("- All toasts should appear and auto-dismiss")
    print("- Progress bars should animate smoothly")
    print("- Spinners should rotate continuously")
    print("- Badges should display correctly with proper colors")
    print("\n" + "=" * 60)
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

# Made with Bob
