"""
Test script for CompaniesProcess_v2.py settings propagation.
Verifies that all dialogs properly respond to theme and font size changes.
"""

import sys
import os

# Add src_v2 to path
src_v2_dir = os.path.dirname(os.path.abspath(__file__))
if src_v2_dir not in sys.path:
    sys.path.insert(0, src_v2_dir)

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt5.QtCore import Qt
from ui.services import get_v2_settings_bus
from ui.theme_manager import get_theme_manager

# Import the dialog functions from CompaniesProcess_v2
sys.path.insert(0, os.path.join(src_v2_dir, 'ART Q Control'))
from CompaniesProcess_v2 import check_companies_cache_and_ask, show_per_case_outcomes_dialog


class TestWindow(QMainWindow):
    """Test window to verify settings propagation."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CompaniesProcess Settings Propagation Test")
        self.setMinimumSize(600, 400)
        
        # Get settings bus
        self.settings_bus = get_v2_settings_bus()
        self.theme_manager = get_theme_manager()
        
        self._setup_ui()
        self._apply_theme()
        
        # Subscribe to changes
        self.settings_bus.theme_changed.connect(self._apply_theme)
    
    def _setup_ui(self):
        """Setup the test UI."""
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("CompaniesProcess Settings Propagation Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "This test verifies that CompaniesProcess dialogs respond to settings changes.\n\n"
            "Instructions:\n"
            "1. Click a button to open a dialog\n"
            "2. While dialog is open, change theme or font size in Settings\n"
            "3. Verify the dialog updates immediately\n"
            "4. Test both dialogs"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Current settings display
        self.settings_label = QLabel()
        self._update_settings_display()
        layout.addWidget(self.settings_label)
        
        # Test buttons
        btn_resume = QPushButton("Test Resume Dialog")
        btn_resume.clicked.connect(self.test_resume_dialog)
        layout.addWidget(btn_resume)
        
        btn_outcomes = QPushButton("Test Per-Case Outcomes Dialog")
        btn_outcomes.clicked.connect(self.test_outcomes_dialog)
        layout.addWidget(btn_outcomes)
        
        # Settings controls
        btn_toggle_theme = QPushButton("Toggle Theme")
        btn_toggle_theme.clicked.connect(self.toggle_theme)
        layout.addWidget(btn_toggle_theme)
        
        btn_increase_font = QPushButton("Increase Font Size")
        btn_increase_font.clicked.connect(self.increase_font)
        layout.addWidget(btn_increase_font)
        
        btn_decrease_font = QPushButton("Decrease Font Size")
        btn_decrease_font.clicked.connect(self.decrease_font)
        layout.addWidget(btn_decrease_font)
        
        layout.addStretch()
        self.setCentralWidget(central)
        
        # Subscribe to settings changes
        self.settings_bus.theme_changed.connect(self._update_settings_display)
        self.settings_bus.font_size_changed.connect(self._update_settings_display)
    
    def _update_settings_display(self):
        """Update the settings display label."""
        theme = self.settings_bus.theme
        font_size = self.settings_bus.font_size
        self.settings_label.setText(
            f"Current Settings:\n"
            f"  Theme: {theme}\n"
            f"  Font Size: {font_size}px"
        )
    
    def _apply_theme(self):
        """Apply current theme."""
        theme = self.settings_bus.theme
        if theme == 'dark':
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #161616;
                    color: #f4f4f4;
                }
                QPushButton {
                    background-color: #393939;
                    color: #f4f4f4;
                    border: 1px solid #525252;
                    border-radius: 4px;
                    padding: 8px 16px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #4c4c4c;
                    border-color: #0f62fe;
                }
                QLabel {
                    color: #f4f4f4;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #ffffff;
                    color: #161616;
                }
                QPushButton {
                    background-color: #e0e0e0;
                    color: #161616;
                    border: 1px solid #8d8d8d;
                    border-radius: 4px;
                    padding: 8px 16px;
                    min-height: 36px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                    border-color: #0f62fe;
                }
                QLabel {
                    color: #161616;
                }
            """)
    
    def test_resume_dialog(self):
        """Test the resume dialog (simulated)."""
        print("\n=== Testing CompaniesResumeDialog ===")
        print("NOTE: This would normally check for an existing cache file.")
        print("For testing, we'll create a mock scenario.")
        
        # Create a temporary cache file to trigger the dialog
        import tempfile
        import pandas as pd
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as f:
            temp_cache = f.name
        
        try:
            # Create mock cache with some data
            df = pd.DataFrame({
                'Case Number': ['12345', '67890'],
                'Status': ['New', 'New']
            })
            df.to_excel(temp_cache, sheet_name='Companies', index=False)
            
            # Call the function
            result = check_companies_cache_and_ask(temp_cache)
            print(f"Dialog result: {result}")
            print("✓ Dialog opened and closed successfully")
            print("✓ Verify that theme/font changes were applied while dialog was open")
        finally:
            # Cleanup
            if os.path.exists(temp_cache):
                os.unlink(temp_cache)
    
    def test_outcomes_dialog(self):
        """Test the per-case outcomes dialog."""
        print("\n=== Testing PerCaseOutcomesDialog ===")
        
        # Mock case data
        cases = [
            {'case_number': '12345', 'serial': 'SN001', 'mtm': 'MTM001'},
            {'case_number': '67890', 'serial': 'SN002', 'mtm': 'MTM002'},
            {'case_number': '11111', 'serial': 'SN003', 'mtm': 'MTM003'},
        ]
        
        result = show_per_case_outcomes_dialog(
            email='test@company.com',
            cases=cases,
            batch_index=1,
            total_batches=3
        )
        
        if result:
            print(f"Dialog result: {result}")
            print("✓ Dialog opened and closed successfully")
            print("✓ Verify that theme/font changes were applied while dialog was open")
        else:
            print("Dialog was cancelled")
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        current = self.settings_bus.theme
        new_theme = 'dark' if current == 'light' else 'light'
        self.theme_manager.set_theme(new_theme)
        print(f"Theme changed: {current} -> {new_theme}")
    
    def increase_font(self):
        """Increase font size."""
        current = self.settings_bus.font_size
        new_size = min(current + 2, 30)
        self.settings_bus.set_font_size(new_size)
        print(f"Font size changed: {current}px -> {new_size}px")
    
    def decrease_font(self):
        """Decrease font size."""
        current = self.settings_bus.font_size
        new_size = max(current - 2, 15)
        self.settings_bus.set_font_size(new_size)
        print(f"Font size changed: {current}px -> {new_size}px")


def main():
    """Run the test."""
    print("=" * 60)
    print("CompaniesProcess Settings Propagation Test")
    print("=" * 60)
    
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("\nTest window opened. Follow the instructions in the window.")
    print("\nExpected behavior:")
    print("1. CompaniesResumeDialog should update theme/font immediately")
    print("2. PerCaseOutcomesDialog should update theme/font immediately")
    print("3. Both dialogs should call _apply_theme() on font changes")
    print("4. No errors should occur during theme/font changes")
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

# Made with Bob
