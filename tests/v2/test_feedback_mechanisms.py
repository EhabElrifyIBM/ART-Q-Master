"""
Test Feedback Mechanisms
=========================

Comprehensive test script for all feedback components in src_v2.
Tests toasts, loading indicators, progress bars, badges, and dialogs.

Run this script to verify:
- All feedback types work correctly
- Duration standards are enforced
- Theme integration works
- Components use design_system.py colors
- Typography scaling works

Usage:
    python src_v2/test_feedback_mechanisms.py
"""

import sys
from pathlib import Path

# Add src_v2 to path
src_v2_path = Path(__file__).parent
sys.path.insert(0, str(src_v2_path))

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import QTimer, Qt

from ui.components_v2 import Toast, ModernSpinner, ModernProgressBar, Badge
from ui.components_v2.dialogs import MessageDialog, ConfirmDialog, ProgressDialog
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from ui.design_system import Colors, Spacing
from ui.typography import TypographySystem, FontSizePreset
from ui.services import get_v2_settings_bus


class FeedbackTestWindow(QMainWindow):
    """Test window for all feedback mechanisms."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Feedback Mechanisms Test - Phase 4 Day 3")
        self.setMinimumSize(900, 700)
        
        # Initialize services
        self._settings_bus = get_v2_settings_bus()
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        
        # Connect to theme changes
        self._settings_bus.theme_changed.connect(self._on_theme_changed)
        
        self._setup_ui()
        self._apply_theme()
    
    def _setup_ui(self):
        """Set up test UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)
        
        # Title
        title = QLabel("Feedback Mechanisms Test Suite")
        self._typography.apply_to_widget(title, 'h2')
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Test all feedback types with duration standards and theme integration.\n"
            "Toggle theme to verify all components adapt correctly."
        )
        self._typography.apply_to_widget(desc, 'body')
        layout.addWidget(desc)
        
        # Theme toggle
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self._typography.apply_to_widget(theme_label, 'body')
        theme_layout.addWidget(theme_label)
        
        self._theme_button = PrimaryButton("Toggle Theme (Light)")
        self._theme_button.clicked.connect(self._toggle_theme)
        theme_layout.addWidget(self._theme_button)
        theme_layout.addStretch()
        layout.addLayout(theme_layout)
        
        # Section 1: Toast Notifications
        layout.addWidget(self._create_section_label("1. Toast Notifications (Duration Standards)"))
        toast_layout = QHBoxLayout()
        
        success_btn = PrimaryButton("Success Toast (3s)")
        success_btn.clicked.connect(lambda: self._test_success_toast())
        toast_layout.addWidget(success_btn)
        
        info_btn = PrimaryButton("Info Toast (4s)")
        info_btn.clicked.connect(lambda: self._test_info_toast())
        toast_layout.addWidget(info_btn)
        
        warning_btn = PrimaryButton("Warning Toast (5s)")
        warning_btn.clicked.connect(lambda: self._test_warning_toast())
        toast_layout.addWidget(warning_btn)
        
        error_btn = PrimaryButton("Error Dialog")
        error_btn.clicked.connect(lambda: self._test_error_dialog())
        toast_layout.addWidget(error_btn)
        
        layout.addLayout(toast_layout)
        
        # Section 2: Loading Indicators
        layout.addWidget(self._create_section_label("2. Loading Indicators (Duration-Based)"))
        loading_layout = QHBoxLayout()
        
        spinner_btn = PrimaryButton("Spinner (< 2s)")
        spinner_btn.clicked.connect(lambda: self._test_spinner())
        loading_layout.addWidget(spinner_btn)
        
        progress_btn = PrimaryButton("Progress Bar (2-30s)")
        progress_btn.clicked.connect(lambda: self._test_progress_bar())
        loading_layout.addWidget(progress_btn)
        
        dialog_btn = PrimaryButton("Progress Dialog (> 30s)")
        dialog_btn.clicked.connect(lambda: self._test_progress_dialog())
        loading_layout.addWidget(dialog_btn)
        
        layout.addLayout(loading_layout)
        
        # Spinner display area
        self._spinner_container = QWidget()
        spinner_container_layout = QHBoxLayout(self._spinner_container)
        spinner_container_layout.setContentsMargins(0, 0, 0, 0)
        self._spinner = ModernSpinner()
        spinner_container_layout.addWidget(self._spinner)
        spinner_container_layout.addWidget(QLabel("Spinner animation"))
        spinner_container_layout.addStretch()
        layout.addWidget(self._spinner_container)
        self._spinner_container.hide()
        
        # Progress bar display area
        self._progress_bar = ModernProgressBar()
        layout.addWidget(self._progress_bar)
        self._progress_bar.hide()
        
        # Section 3: Badges
        layout.addWidget(self._create_section_label("3. Status Badges"))
        badge_layout = QHBoxLayout()
        
        self._badge_default = Badge("Default", "default")
        badge_layout.addWidget(self._badge_default)
        
        self._badge_success = Badge("Success", "success")
        badge_layout.addWidget(self._badge_success)
        
        self._badge_warning = Badge("Warning", "warning")
        badge_layout.addWidget(self._badge_warning)
        
        self._badge_error = Badge("Error", "error")
        badge_layout.addWidget(self._badge_error)
        
        self._badge_info = Badge("Info", "info")
        badge_layout.addWidget(self._badge_info)
        
        badge_layout.addStretch()
        layout.addLayout(badge_layout)
        
        # Section 4: Message Dialogs
        layout.addWidget(self._create_section_label("4. Message Dialogs"))
        dialog_layout = QHBoxLayout()
        
        info_dialog_btn = SecondaryButton("Info Dialog")
        info_dialog_btn.clicked.connect(lambda: self._test_info_dialog())
        dialog_layout.addWidget(info_dialog_btn)
        
        warning_dialog_btn = SecondaryButton("Warning Dialog")
        warning_dialog_btn.clicked.connect(lambda: self._test_warning_dialog())
        dialog_layout.addWidget(warning_dialog_btn)
        
        error_dialog_btn = SecondaryButton("Error Dialog")
        error_dialog_btn.clicked.connect(lambda: self._test_error_dialog())
        dialog_layout.addWidget(error_dialog_btn)
        
        success_dialog_btn = SecondaryButton("Success Dialog")
        success_dialog_btn.clicked.connect(lambda: self._test_success_dialog())
        dialog_layout.addWidget(success_dialog_btn)
        
        confirm_btn = SecondaryButton("Confirm Dialog")
        confirm_btn.clicked.connect(lambda: self._test_confirm_dialog())
        dialog_layout.addWidget(confirm_btn)
        
        layout.addLayout(dialog_layout)
        
        # Section 5: Test Results
        layout.addWidget(self._create_section_label("5. Test Results"))
        self._results_label = QLabel("Click buttons above to test feedback mechanisms")
        self._typography.apply_to_widget(self._results_label, 'body')
        layout.addWidget(self._results_label)
        
        layout.addStretch()
    
    def _create_section_label(self, text: str) -> QLabel:
        """Create a section header label."""
        label = QLabel(text)
        self._typography.apply_to_widget(label, 'h4')
        return label
    
    def _toggle_theme(self):
        """Toggle between light and dark theme."""
        self._theme_mode = "dark" if self._theme_mode == "light" else "light"
        self._settings_bus.theme_changed.emit(self._theme_mode)
        self._theme_button.setText(f"Toggle Theme ({self._theme_mode.title()})")
        self._update_results(f"Theme changed to {self._theme_mode}")
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        self._theme_mode = theme
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply theme to window."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['background']};
            }}
            QWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
        """)
        
        # Update badges theme
        self._badge_default.set_theme(self._theme_mode)
        self._badge_success.set_theme(self._theme_mode)
        self._badge_warning.set_theme(self._theme_mode)
        self._badge_error.set_theme(self._theme_mode)
        self._badge_info.set_theme(self._theme_mode)
        
        # Update spinner theme
        self._spinner.set_theme(self._theme_mode)
        
        # Update progress bar theme
        self._progress_bar.set_theme(self._theme_mode)
    
    def _update_results(self, message: str):
        """Update results label."""
        self._results_label.setText(f"✓ {message}")
    
    # Toast tests
    def _test_success_toast(self):
        """Test success toast (3s)."""
        Toast.success(self, "Operation completed successfully!")
        self._update_results("Success toast shown (3 seconds, green)")
    
    def _test_info_toast(self):
        """Test info toast (4s)."""
        Toast.info(self, "Processing 10 items...")
        self._update_results("Info toast shown (4 seconds, blue)")
    
    def _test_warning_toast(self):
        """Test warning toast (5s)."""
        Toast.warning(self, "Some items were skipped during processing")
        self._update_results("Warning toast shown (5 seconds, yellow)")
    
    def _test_error_dialog(self):
        """Test error dialog (requires acknowledgment)."""
        Toast.error(self, "Failed to save file: Permission denied", "Save Error")
        self._update_results("Error dialog shown (requires acknowledgment, red)")
    
    # Loading indicator tests
    def _test_spinner(self):
        """Test spinner (< 2s)."""
        self._spinner_container.show()
        self._spinner.start()
        self._update_results("Spinner started (< 2 seconds)")
        
        # Stop after 2 seconds
        QTimer.singleShot(2000, self._stop_spinner)
    
    def _stop_spinner(self):
        """Stop spinner."""
        self._spinner.stop()
        self._spinner_container.hide()
        self._update_results("Spinner stopped")
    
    def _test_progress_bar(self):
        """Test progress bar (2-30s)."""
        self._progress_bar.show()
        self._progress_bar.setValue(0)
        self._update_results("Progress bar started (2-30 seconds)")
        
        # Simulate progress
        self._progress_value = 0
        self._progress_timer = QTimer()
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start(100)
    
    def _update_progress(self):
        """Update progress bar."""
        self._progress_value += 5
        self._progress_bar.setValue(self._progress_value)
        
        if self._progress_value >= 100:
            self._progress_timer.stop()
            QTimer.singleShot(1000, self._hide_progress_bar)
            self._update_results("Progress bar completed")
    
    def _hide_progress_bar(self):
        """Hide progress bar."""
        self._progress_bar.hide()
    
    def _test_progress_dialog(self):
        """Test progress dialog (> 30s)."""
        dialog = ProgressDialog(self, "Processing large batch...", "Batch Process")
        dialog.show()
        self._update_results("Progress dialog shown (> 30 seconds)")
        
        # Simulate progress
        self._dialog_progress = 0
        self._dialog_timer = QTimer()
        self._dialog_timer.timeout.connect(lambda: self._update_dialog_progress(dialog))
        self._dialog_timer.start(100)
    
    def _update_dialog_progress(self, dialog):
        """Update progress dialog."""
        self._dialog_progress += 2
        dialog.set_progress(self._dialog_progress)
        dialog.set_message(f"Processing item {self._dialog_progress}/100...")
        
        if self._dialog_progress >= 100:
            self._dialog_timer.stop()
            dialog.close()
            self._update_results("Progress dialog completed")
    
    # Dialog tests
    def _test_info_dialog(self):
        """Test info dialog."""
        MessageDialog.information(self, "Information", "This is an informational message")
        self._update_results("Info dialog shown and acknowledged")
    
    def _test_warning_dialog(self):
        """Test warning dialog."""
        MessageDialog.warning(self, "Warning", "This action cannot be undone")
        self._update_results("Warning dialog shown and acknowledged")
    
    def _test_success_dialog(self):
        """Test success dialog."""
        MessageDialog.success(self, "Success", "All items processed successfully")
        self._update_results("Success dialog shown and acknowledged")
    
    def _test_confirm_dialog(self):
        """Test confirm dialog."""
        dialog = ConfirmDialog(self, "Are you sure you want to delete this item?", "Confirm Delete")
        result = dialog.exec_()
        
        if result == ConfirmDialog.Accepted:
            self._update_results("Confirm dialog: User clicked Yes")
        else:
            self._update_results("Confirm dialog: User clicked No")


def main():
    """Run feedback mechanisms test."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = FeedbackTestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# Made with Bob
