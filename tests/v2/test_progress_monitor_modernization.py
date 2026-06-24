"""
Test script for Progress Monitor V2 Modernization
=================================================

This script tests the modernized Progress Monitor dialog with:
- V2 shell styling (window_bg, surface, borders)
- Typography system integration
- Theme switching (light/dark/auto)
- Progress tracking functionality
- Control buttons (pause/resume/stop/abort)
- Activity logging with color-coded messages

Run this script to verify the Progress Monitor matches the main menu
and Dispatcher styling.
"""

import sys
import os
import time
from datetime import datetime

# Add src_v2 to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

from ui.components.progress_monitor import ProgressMonitor
from ui.services import get_v2_settings_bus


class ProgressMonitorTestWindow(QWidget):
    """Test window for Progress Monitor with theme controls."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Progress Monitor V2 Test")
        self.resize(400, 300)
        
        self.settings_bus = get_v2_settings_bus()
        self.progress_monitor = None
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("Progress Monitor V2 Modernization Test")
        title.setFont(QFont('IBM Plex Sans', 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Test buttons
        test_btn = QPushButton("Launch Progress Monitor")
        test_btn.setMinimumHeight(44)
        test_btn.clicked.connect(self.launch_progress_monitor)
        layout.addWidget(test_btn)
        
        simulate_btn = QPushButton("Launch with Simulated Progress")
        simulate_btn.setMinimumHeight(44)
        simulate_btn.clicked.connect(self.launch_with_simulation)
        layout.addWidget(simulate_btn)
        
        # Theme controls
        theme_label = QLabel("Theme Controls:")
        theme_label.setFont(QFont('IBM Plex Sans', 12, QFont.Bold))
        layout.addWidget(theme_label)
        
        theme_row = QHBoxLayout()
        
        light_btn = QPushButton("Light")
        light_btn.clicked.connect(lambda: self.change_theme('light'))
        theme_row.addWidget(light_btn)
        
        dark_btn = QPushButton("Dark")
        dark_btn.clicked.connect(lambda: self.change_theme('dark'))
        theme_row.addWidget(dark_btn)
        
        auto_btn = QPushButton("Auto")
        auto_btn.clicked.connect(lambda: self.change_theme('auto'))
        theme_row.addWidget(auto_btn)
        
        layout.addLayout(theme_row)
        
        # Font preset controls
        font_label = QLabel("Font Preset Controls:")
        font_label.setFont(QFont('IBM Plex Sans', 12, QFont.Bold))
        layout.addWidget(font_label)
        
        font_row = QHBoxLayout()
        
        small_btn = QPushButton("Small")
        small_btn.clicked.connect(lambda: self.change_font_preset('small'))
        font_row.addWidget(small_btn)
        
        normal_btn = QPushButton("Normal")
        normal_btn.clicked.connect(lambda: self.change_font_preset('normal'))
        font_row.addWidget(normal_btn)
        
        large_btn = QPushButton("Large")
        large_btn.clicked.connect(lambda: self.change_font_preset('large'))
        font_row.addWidget(large_btn)
        
        layout.addLayout(font_row)
        
        layout.addStretch()
        
        # Info
        info = QLabel(
            "Test Features:\n"
            "• V2 shell styling (cards, borders, colors)\n"
            "• Typography system integration\n"
            "• Theme switching (light/dark/auto)\n"
            "• Progress tracking with stats\n"
            "• Control buttons (pause/resume/stop/abort)\n"
            "• Activity log with color-coded messages"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(info)
        
        self.setLayout(layout)
    
    def launch_progress_monitor(self):
        """Launch Progress Monitor without simulation."""
        self.progress_monitor = ProgressMonitor(
            title="Test Progress Monitor",
            total_cases=10,
            parent=self
        )
        
        # Add some initial log messages
        self.progress_monitor.log_message("Progress Monitor initialized", "INFO")
        self.progress_monitor.log_success("V2 shell styling applied")
        self.progress_monitor.log_message("Typography system integrated", "STEP")
        self.progress_monitor.log_warning("This is a test warning message")
        self.progress_monitor.log_message("Theme-aware colors active", "INFO")
        
        self.progress_monitor.show()
    
    def launch_with_simulation(self):
        """Launch Progress Monitor with simulated progress."""
        self.progress_monitor = ProgressMonitor(
            title="Simulated Progress",
            total_cases=20,
            parent=self
        )
        
        self.progress_monitor.log_message("Starting simulated automation...", "INFO")
        self.progress_monitor.show()
        
        # Simulate progress updates
        self.current_case = 0
        self.completed = 0
        self.skipped = 0
        self.failed = 0
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.simulate_progress)
        self.timer.start(1000)  # Update every second
    
    def simulate_progress(self):
        """Simulate progress updates."""
        if self.current_case >= 20:
            self.timer.stop()
            self.progress_monitor.finish_process("Completed")
            return
        
        self.current_case += 1
        case_number = f"CASE-{self.current_case:04d}"
        
        # Randomly complete, skip, or fail
        import random
        outcome = random.choice(['complete', 'complete', 'complete', 'skip', 'fail'])
        
        if outcome == 'complete':
            self.completed += 1
            self.progress_monitor.log_success(f"Case {case_number} completed successfully")
        elif outcome == 'skip':
            self.skipped += 1
            self.progress_monitor.log_warning(f"Case {case_number} skipped")
        else:
            self.failed += 1
            self.progress_monitor.log_error(f"Case {case_number} failed")
        
        # Update progress
        self.progress_monitor.update_progress(
            current_case_num=self.current_case,
            case_number=case_number,
            completed=self.completed,
            skipped=self.skipped,
            failed=self.failed,
            total=20
        )
        
        # Add variety to logs
        if self.current_case % 5 == 0:
            self.progress_monitor.log_message(f"Processed {self.current_case} cases", "STEP")
    
    def change_theme(self, theme: str):
        """Change theme and notify all dialogs."""
        print(f"[TEST] Changing theme to: {theme}")
        self.settings_bus.set_theme(theme)
    
    def change_font_preset(self, preset: str):
        """Change font preset and notify all dialogs."""
        print(f"[TEST] Changing font preset to: {preset}")
        self.settings_bus.font_preset_changed.emit(preset)


def main():
    """Run the Progress Monitor test."""
    app = QApplication.instance() or QApplication(sys.argv)
    
    print("=" * 70)
    print("Progress Monitor V2 Modernization Test")
    print("=" * 70)
    print("\nFeatures being tested:")
    print("  [OK] V2 shell styling (window_bg, surface, borders)")
    print("  [OK] Typography system integration")
    print("  [OK] Theme switching (light/dark/auto)")
    print("  [OK] Progress tracking with stat cards")
    print("  [OK] Control buttons (pause/resume/stop/abort)")
    print("  [OK] Activity log with color-coded messages")
    print("  [OK] Reactive theme/font updates")
    print("\nInstructions:")
    print("  1. Click 'Launch Progress Monitor' for static view")
    print("  2. Click 'Launch with Simulated Progress' for animated demo")
    print("  3. Use theme buttons to test light/dark/auto modes")
    print("  4. Use font buttons to test typography scaling")
    print("  5. Test control buttons (pause/resume/stop/abort)")
    print("=" * 70)
    print()
    
    window = ProgressMonitorTestWindow()
    window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
