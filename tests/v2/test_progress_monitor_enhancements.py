"""
Test Progress Monitor Enhancements - Font Size & Settings Responsiveness
=========================================================================

Tests the enhanced Progress Monitor with:
1. Larger activity log font size (body instead of body_sm)
2. Increased log padding (LG instead of SM)
3. Better line height (1.8)
4. Full settings responsiveness (font preset and theme changes)

Author: ART Q Master Development
Version: 1.0
"""

import sys
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer

# Add src_v2 to path
sys.path.insert(0, 'src_v2')

from ui.components.progress_monitor import ProgressMonitor
from ui.services import get_v2_settings_bus


class TestWindow(QMainWindow):
    """Test window to launch Progress Monitor and test settings changes"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Monitor Enhancement Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Launch button
        launch_btn = QPushButton("Launch Progress Monitor")
        launch_btn.clicked.connect(self.launch_monitor)
        layout.addWidget(launch_btn)
        
        # Font preset buttons
        font_small_btn = QPushButton("Set Font: Small")
        font_small_btn.clicked.connect(lambda: self.change_font_preset('small'))
        layout.addWidget(font_small_btn)
        
        font_normal_btn = QPushButton("Set Font: Normal")
        font_normal_btn.clicked.connect(lambda: self.change_font_preset('normal'))
        layout.addWidget(font_normal_btn)
        
        font_large_btn = QPushButton("Set Font: Large")
        font_large_btn.clicked.connect(lambda: self.change_font_preset('large'))
        layout.addWidget(font_large_btn)
        
        # Theme buttons
        theme_light_btn = QPushButton("Set Theme: Light")
        theme_light_btn.clicked.connect(lambda: self.change_theme('light'))
        layout.addWidget(theme_light_btn)
        
        theme_dark_btn = QPushButton("Set Theme: Dark")
        theme_dark_btn.clicked.connect(lambda: self.change_theme('dark'))
        layout.addWidget(theme_dark_btn)
        
        layout.addStretch()
        
        self.monitor = None
        self.settings_bus = get_v2_settings_bus()
    
    def launch_monitor(self):
        """Launch Progress Monitor with test data"""
        if self.monitor is None or not self.monitor.isVisible():
            self.monitor = ProgressMonitor(
                title="Test Processing",
                total_cases=100,
                parent=self
            )
            
            # Simulate some progress and log messages
            self.monitor.update_progress(1, "CASE-001", 0, 0, 0, 100)
            self.monitor.log_message("Starting test process...", "INFO")
            self.monitor.log_success("Successfully initialized")
            self.monitor.log_message("Processing case CASE-001", "STEP")
            self.monitor.log_warning("This is a warning message with longer text to test wrapping behavior")
            self.monitor.log_error("This is an error message")
            self.monitor.log_eticket("eTicket created: TKT-12345")
            
            # Add more log entries to test scrolling
            for i in range(2, 11):
                self.monitor.update_progress(i, f"CASE-{i:03d}", i-1, 0, 0, 100)
                self.monitor.log_message(f"Processing case CASE-{i:03d}", "INFO")
                if i % 3 == 0:
                    self.monitor.log_success(f"Case CASE-{i:03d} completed successfully")
            
            self.monitor.show()
            print("✓ Progress Monitor launched")
            print("✓ Activity log: h3 font (20px - 43% LARGER!)")
            print("✓ Buttons: h4 font (18px - 28% LARGER!) with responsive sizing")
            print("✓ Log padding: LG (24px) with line-height 1.8")
            print("\nTest Instructions:")
            print("1. Check that activity log text is larger and more readable")
            print("2. Click font preset buttons to test real-time font changes")
            print("3. Click theme buttons to test real-time theme changes")
            print("4. Verify ALL text elements update immediately")
            print("5. Check that log messages have proper spacing and wrap correctly")
    
    def change_font_preset(self, preset):
        """Change font preset and verify it updates the monitor"""
        # Emit the signal directly to test responsiveness
        self.settings_bus.font_preset_changed.emit(preset)
        print(f"✓ Font preset changed to: {preset}")
        print("  → Check that Progress Monitor text updated immediately")
    
    def change_theme(self, theme):
        """Change theme and verify it updates the monitor"""
        # Use the proper setter method
        self.settings_bus.set_theme(theme)
        print(f"✓ Theme changed to: {theme}")
        print("  → Check that Progress Monitor colors updated immediately")


def main():
    """Run the test"""
    app = QApplication(sys.argv)
    
    print("=" * 70)
    print("Progress Monitor Enhancement Test")
    print("=" * 70)
    print("\nEnhancements Applied:")
    print("1. ✓ Activity log font: body_sm → h3 (HUGE - 14px → 20px = 43% larger!)")
    print("2. ✓ Button fonts: button → h4 (14px → 18px = 28% larger!)")
    print("3. ✓ Button sizes: Now RESPONSIVE to font size (dynamic height/width)")
    print("4. ✓ Log padding: SM (12px) → LG (24px)")
    print("5. ✓ Line height: 1.8 for better spacing")
    print("6. ✓ Log section spacing: SM → MD")
    print("\nSettings Responsiveness:")
    print("✓ Theme changes connected via settings_bus.theme_changed")
    print("✓ Font preset changes connected via settings_bus.font_preset_changed")
    print("✓ apply_typography() regenerates stylesheet with new font sizes")
    print("✓ _apply_theme() updates all colors and font sizes dynamically")
    print("\n" + "=" * 70)
    
    window = TestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

# Made with Bob
