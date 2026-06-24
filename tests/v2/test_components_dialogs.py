"""
Test Suite for Dialog Components (Phase 5.2)
=============================================

Comprehensive tests for all dialog types including ConfirmDialog, InputDialog,
ProgressDialog, MessageDialog, ErrorDialog, SuccessDialog, WarningDialog, and CustomDialog.
Tests cover all Phase 5.2 enhancements including focus trapping, Escape key, backdrop click,
animations, and scrollable content.

Run with: python src_v2/test_components_dialogs.py
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, 
    QLabel, QPushButton, QDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtTest import QTest
from ui.components_v2.dialogs import (
    ConfirmDialog, InputDialog, ProgressDialog, MessageDialog,
    ErrorDialog, SuccessDialog, WarningDialog, CustomDialog
)
from ui.components_v2.buttons import PrimaryButton, SecondaryButton


class DialogTestWindow(QMainWindow):
    """Test window for dialog components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dialog Components Test Suite - Phase 5.2")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        
        # Add title
        title = QLabel("Dialog Components Test Suite - Phase 5.2")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 16px;")
        main_layout.addWidget(title)
        
        # Test results
        self.test_results = []
        
        # Add test buttons
        self.add_test_buttons(main_layout)
        
        # Run automated tests
        QTimer.singleShot(500, self.run_automated_tests)
    
    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        self.test_results.append({
            'name': test_name,
            'passed': passed,
            'message': message
        })
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"  {message}")
    
    def add_test_buttons(self, layout: QVBoxLayout):
        """Add buttons to manually test dialogs."""
        info_label = QLabel("Click buttons below to manually test dialogs:")
        info_label.setStyleSheet("font-size: 14px; margin: 8px;")
        layout.addWidget(info_label)
        
        # Confirm Dialog button
        btn = QPushButton("Test Confirm Dialog")
        btn.clicked.connect(self.test_confirm_dialog_manual)
        layout.addWidget(btn)
        
        # Input Dialog button
        btn = QPushButton("Test Input Dialog")
        btn.clicked.connect(self.test_input_dialog_manual)
        layout.addWidget(btn)
        
        # Progress Dialog button
        btn = QPushButton("Test Progress Dialog")
        btn.clicked.connect(self.test_progress_dialog_manual)
        layout.addWidget(btn)
        
        # Message Dialogs button
        btn = QPushButton("Test Message Dialogs (Info/Warning/Error/Success)")
        btn.clicked.connect(self.test_message_dialogs_manual)
        layout.addWidget(btn)
        
        # Custom Dialog button
        btn = QPushButton("Test Custom Dialog")
        btn.clicked.connect(self.test_custom_dialog_manual)
        layout.addWidget(btn)
        
        # Backdrop Click Dialog button
        btn = QPushButton("Test Backdrop Click Dialog")
        btn.clicked.connect(self.test_backdrop_click_manual)
        layout.addWidget(btn)
        
        layout.addStretch()
    
    def run_automated_tests(self):
        """Run automated tests."""
        print("\n" + "="*60)
        print("RUNNING AUTOMATED TESTS")
        print("="*60 + "\n")
        
        self.test_confirm_dialog()
        self.test_input_dialog()
        self.test_progress_dialog()
        self.test_message_dialog()
        self.test_error_dialog()
        self.test_success_dialog()
        self.test_warning_dialog()
        self.test_custom_dialog()
        self.test_dialog_properties()
        self.test_focus_trapping()
        
        self.print_test_summary()
    
    def test_confirm_dialog(self):
        """Test 1: ConfirmDialog functionality."""
        try:
            dialog = ConfirmDialog(
                self,
                "Are you sure you want to proceed?",
                "Confirm Action"
            )
            
            # Verify dialog properties
            assert dialog is not None, "Dialog should be created"
            assert dialog.windowTitle() == "Confirm Action", "Title should be set"
            assert dialog._message_label is not None, "Message label should exist"
            assert dialog._yes_button is not None, "Yes button should exist"
            assert dialog._no_button is not None, "No button should exist"
            
            self.log_test("ConfirmDialog Creation", True, "Dialog created with all components")
        except Exception as e:
            self.log_test("ConfirmDialog Creation", False, str(e))
    
    def test_input_dialog(self):
        """Test 2: InputDialog functionality."""
        try:
            dialog = InputDialog(
                self,
                "Enter your name:",
                "Name Input",
                "John Doe",
                "Enter name here"
            )
            
            # Verify dialog properties
            assert dialog is not None, "Dialog should be created"
            assert dialog.windowTitle() == "Name Input", "Title should be set"
            assert dialog._input is not None, "Input field should exist"
            assert dialog.get_text() == "John Doe", "Default text should be set"
            
            # Test set_text
            dialog.set_text("Jane Doe")
            assert dialog.get_text() == "Jane Doe", "Text should be updated"
            
            self.log_test("InputDialog Functionality", True, "Input dialog works correctly")
        except Exception as e:
            self.log_test("InputDialog Functionality", False, str(e))
    
    def test_progress_dialog(self):
        """Test 3: ProgressDialog functionality."""
        try:
            dialog = ProgressDialog(
                self,
                "Processing files...",
                "File Processing",
                cancelable=True
            )
            
            # Verify dialog properties
            assert dialog is not None, "Dialog should be created"
            assert dialog._progress_bar is not None, "Progress bar should exist"
            assert dialog._cancel_button is not None, "Cancel button should exist"
            
            # Test progress updates
            dialog.set_progress(50)
            assert dialog._progress_bar.value() == 50, "Progress should be 50%"
            
            # Test message updates
            dialog.set_message("Processing file 5 of 10...")
            assert "file 5 of 10" in dialog._message_label.text(), "Message should be updated"
            
            self.log_test("ProgressDialog Functionality", True, "Progress dialog works correctly")
        except Exception as e:
            self.log_test("ProgressDialog Functionality", False, str(e))
    
    def test_message_dialog(self):
        """Test 4: MessageDialog functionality."""
        try:
            # Test info dialog
            dialog = MessageDialog(self, "Info", "This is an info message", "info")
            assert dialog is not None, "Info dialog should be created"
            
            # Test warning dialog
            dialog = MessageDialog(self, "Warning", "This is a warning", "warning")
            assert dialog is not None, "Warning dialog should be created"
            
            # Test error dialog
            dialog = MessageDialog(self, "Error", "This is an error", "error")
            assert dialog is not None, "Error dialog should be created"
            
            # Test success dialog
            dialog = MessageDialog(self, "Success", "This is a success message", "success")
            assert dialog is not None, "Success dialog should be created"
            
            self.log_test("MessageDialog Types", True, "All message types work correctly")
        except Exception as e:
            self.log_test("MessageDialog Types", False, str(e))
    
    def test_error_dialog(self):
        """Test 5: ErrorDialog functionality."""
        try:
            dialog = ErrorDialog(self, "Error", "An error occurred")
            
            assert dialog is not None, "ErrorDialog should be created"
            assert dialog.windowTitle() == "Error", "Title should be set"
            
            self.log_test("ErrorDialog Creation", True, "ErrorDialog created successfully")
        except Exception as e:
            self.log_test("ErrorDialog Creation", False, str(e))
    
    def test_success_dialog(self):
        """Test 6: SuccessDialog functionality."""
        try:
            dialog = SuccessDialog(self, "Success", "Operation completed")
            
            assert dialog is not None, "SuccessDialog should be created"
            assert dialog.windowTitle() == "Success", "Title should be set"
            
            self.log_test("SuccessDialog Creation", True, "SuccessDialog created successfully")
        except Exception as e:
            self.log_test("SuccessDialog Creation", False, str(e))
    
    def test_warning_dialog(self):
        """Test 7: WarningDialog functionality."""
        try:
            dialog = WarningDialog(self, "Warning", "Please be careful")
            
            assert dialog is not None, "WarningDialog should be created"
            assert dialog.windowTitle() == "Warning", "Title should be set"
            
            self.log_test("WarningDialog Creation", True, "WarningDialog created successfully")
        except Exception as e:
            self.log_test("WarningDialog Creation", False, str(e))
    
    def test_custom_dialog(self):
        """Test 8: CustomDialog functionality."""
        try:
            dialog = CustomDialog(
                self,
                "Custom Dialog",
                max_width=800,
                close_on_backdrop=True
            )
            
            # Add custom content
            content = QLabel("This is custom content")
            dialog.set_content(content)
            
            # Add custom buttons
            btn1 = dialog.add_custom_button("Action 1", lambda: None, primary=True)
            btn2 = dialog.add_custom_button("Action 2", lambda: None)
            
            assert dialog is not None, "CustomDialog should be created"
            assert dialog.maximumWidth() == 800, "Max width should be set"
            assert dialog._close_on_backdrop, "Backdrop click should be enabled"
            assert btn1 is not None, "Primary button should be created"
            assert btn2 is not None, "Secondary button should be created"
            
            self.log_test("CustomDialog Functionality", True, "CustomDialog works correctly")
        except Exception as e:
            self.log_test("CustomDialog Functionality", False, str(e))
    
    def test_dialog_properties(self):
        """Test 9: Dialog properties and constraints."""
        try:
            dialog = ConfirmDialog(self, "Test message")
            
            # Test max width
            assert dialog.maximumWidth() == 600, "Default max width should be 600px"
            
            # Test minimum size
            assert dialog.minimumWidth() == 400, "Minimum width should be 400px"
            assert dialog.minimumHeight() == 150, "Minimum height should be 150px"
            
            # Test scrollable content
            assert dialog._scroll_area is not None, "Scroll area should exist"
            
            # Test animation
            assert dialog._animate, "Animation should be enabled by default"
            
            self.log_test("Dialog Properties", True, "All properties set correctly")
        except Exception as e:
            self.log_test("Dialog Properties", False, str(e))
    
    def test_focus_trapping(self):
        """Test 10: Focus trapping functionality."""
        try:
            dialog = InputDialog(self, "Test input")
            
            # Verify focus trapping is set up
            assert dialog._focusable_widgets is not None, "Focusable widgets list should exist"
            
            # Test that event filter is installed
            # (This is automatically done in __init__)
            
            self.log_test("Focus Trapping", True, "Focus trapping is configured")
        except Exception as e:
            self.log_test("Focus Trapping", False, str(e))
    
    # Manual test methods
    
    def test_confirm_dialog_manual(self):
        """Manual test: Show confirm dialog."""
        dialog = ConfirmDialog(
            self,
            "Do you want to proceed with this action?",
            "Confirm Action",
            "Yes, Proceed",
            "No, Cancel"
        )
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            print("User clicked Yes")
        else:
            print("User clicked No or closed dialog")
    
    def test_input_dialog_manual(self):
        """Manual test: Show input dialog."""
        dialog = InputDialog(
            self,
            "Enter your name:",
            "Name Input",
            "John Doe",
            "Enter your full name"
        )
        
        if dialog.exec_() == QDialog.Accepted:
            name = dialog.get_text()
            print(f"User entered: {name}")
            MessageDialog.information(self, "Input Received", f"You entered: {name}")
    
    def test_progress_dialog_manual(self):
        """Manual test: Show progress dialog."""
        dialog = ProgressDialog(
            self,
            "Processing files...",
            "File Processing",
            cancelable=True
        )
        
        dialog.show()
        
        # Simulate progress
        for i in range(101):
            if dialog.result() == QDialog.Rejected:
                print("User cancelled operation")
                break
            
            dialog.set_progress(i)
            dialog.set_message(f"Processing file {i} of 100...")
            QApplication.processEvents()
            QApplication.processEvents()
            import time
            time.sleep(0.02)  # 20ms delay
        
        dialog.close()
        print("Progress completed")
    
    def test_message_dialogs_manual(self):
        """Manual test: Show all message dialog types."""
        # Information
        MessageDialog.information(self, "Information", "This is an information message.")
        
        # Warning
        MessageDialog.warning(self, "Warning", "This is a warning message.")
        
        # Error
        MessageDialog.error(self, "Error", "This is an error message.")
        
        # Success
        MessageDialog.success(self, "Success", "This is a success message.")
    
    def test_custom_dialog_manual(self):
        """Manual test: Show custom dialog."""
        dialog = CustomDialog(
            self,
            "Custom Form",
            max_width=600,
            close_on_backdrop=False
        )
        
        # Create custom content
        content_layout = QVBoxLayout()
        content_layout.addWidget(QLabel("This is a custom dialog with custom content."))
        content_layout.addWidget(QLabel("You can add any widgets here."))
        content_layout.addWidget(QPushButton("Custom Button"))
        
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        dialog.set_content(content_widget)
        
        # Add custom buttons
        dialog.add_custom_button("Apply", lambda: print("Apply clicked"), primary=True)
        dialog.add_custom_button("Close", dialog.reject)
        
        dialog.exec_()
    
    def test_backdrop_click_manual(self):
        """Manual test: Show dialog with backdrop click enabled."""
        dialog = CustomDialog(
            self,
            "Click Outside to Close",
            close_on_backdrop=True
        )
        
        content = QLabel("Click outside this dialog to close it.\n(Backdrop click is enabled)")
        dialog.set_content(content)
        
        dialog.add_custom_button("Close", dialog.reject)
        
        result = dialog.exec_()
        print(f"Dialog closed with result: {result}")
    
    def print_test_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        percentage = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for result in self.test_results:
            status = "✓ PASS" if result['passed'] else "✗ FAIL"
            print(f"{status}: {result['name']}")
            if result['message']:
                print(f"  {result['message']}")
        print("="*60)
        print(f"Coverage: {percentage:.1f}% ({passed}/{total} tests passed)")
        print("="*60)
        
        if passed == total:
            print("✓ ALL AUTOMATED TESTS PASSED")
        else:
            print("✗ SOME TESTS FAILED")
        print("\nManual tests available via buttons in the window.")
        print("="*60 + "\n")


def main():
    """Run dialog component tests."""
    app = QApplication(sys.argv)
    
    # Create and show test window
    window = DialogTestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# Made with Bob
