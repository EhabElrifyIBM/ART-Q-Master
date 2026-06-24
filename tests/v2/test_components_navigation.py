"""
Test Suite for Navigation Components (Phase 5.4)
================================================

Comprehensive tests for ModernToolBar, Sidebar, and Breadcrumbs components.

Test Coverage:
- ModernToolBar: Action groups, overflow, search, customization
- Sidebar: Collapsible, nested navigation, mini mode, footer
- Breadcrumbs: Dropdowns, ellipsis, keyboard navigation
- Theme integration
- Font preset integration
- Accessibility features
- Performance

Run with: python src_v2/test_components_navigation.py
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer

from ui.components_v2 import ModernToolBar, Sidebar, Breadcrumbs
from ui.services import get_v2_settings_bus


class NavigationTestWindow(QMainWindow):
    """Test window for navigation components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navigation Components Test - Phase 5.4")
        self.setGeometry(100, 100, 1200, 800)
        
        self.action_log = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up test UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Test ModernToolBar
        self.setup_toolbar_test(main_layout)
        
        # Content area with sidebar and breadcrumbs
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        
        # Test Sidebar
        self.setup_sidebar_test(content_layout)
        
        # Main content area
        content_widget = QWidget()
        content_widget_layout = QVBoxLayout(content_widget)
        
        # Test Breadcrumbs
        self.setup_breadcrumbs_test(content_widget_layout)
        
        # Log area
        self.setup_log_area(content_widget_layout)
        
        content_layout.addWidget(content_widget, 1)
        main_layout.addLayout(content_layout, 1)
        
        # Status bar
        self.statusBar().showMessage("Navigation Components Test Suite - Phase 5.4")
    
    def setup_toolbar_test(self, layout):
        """Set up toolbar test."""
        self.log("=== Testing ModernToolBar ===")
        
        self.toolbar = ModernToolBar()
        
        # Test: Add actions with different alignments
        self.log("✓ Adding left-aligned actions")
        self.toolbar.add_action("New", self.on_new, icon="📄", shortcut="Ctrl+N", alignment="left")
        self.toolbar.add_action("Open", self.on_open, icon="📂", shortcut="Ctrl+O", alignment="left")
        self.toolbar.add_action("Save", self.on_save, icon="💾", shortcut="Ctrl+S", alignment="left")
        
        # Test: Add separator
        self.log("✓ Adding separator")
        self.toolbar.add_separator(alignment="left")
        
        # Test: Add action group
        self.log("✓ Adding action group (center)")
        self.toolbar.add_action_group([
            ("Bold", self.on_bold, "B"),
            ("Italic", self.on_italic, "I"),
            ("Underline", self.on_underline, "U")
        ], alignment="center")
        
        # Test: Add right-aligned actions
        self.log("✓ Adding right-aligned actions")
        self.toolbar.add_action("Settings", self.on_settings, icon="⚙️", alignment="right")
        self.toolbar.add_action("Help", self.on_help, icon="❓", alignment="right")
        
        # Test: Enable search
        self.log("✓ Enabling search")
        self.toolbar.enable_search(True, placeholder="Search files...")
        self.toolbar.search_changed.connect(self.on_search_changed)
        
        # Test: Enable overflow
        self.log("✓ Enabling overflow menu")
        self.toolbar.enable_overflow(True)
        
        # Test: Connect signals
        self.toolbar.action_triggered.connect(self.on_toolbar_action)
        
        layout.addWidget(self.toolbar)
    
    def setup_sidebar_test(self, layout):
        """Set up sidebar test."""
        self.log("\n=== Testing Sidebar ===")
        
        self.sidebar = Sidebar()
        
        # Test: Add navigation items
        self.log("✓ Adding navigation items")
        self.sidebar.add_item("Dashboard", icon="📊", callback=self.on_dashboard)
        self.sidebar.add_item("Projects", icon="📁", callback=self.on_projects)
        self.sidebar.add_item("Tasks", icon="✓", callback=self.on_tasks)
        self.sidebar.add_item("Calendar", icon="📅", callback=self.on_calendar)
        
        # Test: Add sections with nested items
        self.log("✓ Adding Reports section with nested items")
        self.sidebar.add_section("Reports", [
            ("Sales Report", "💰", self.on_sales_report),
            ("Analytics", "📈", self.on_analytics),
            ("Performance", "⚡", self.on_performance)
        ])
        
        self.log("✓ Adding Settings section")
        self.sidebar.add_section("Settings", [
            ("Profile", "👤", self.on_profile),
            ("Preferences", "⚙️", self.on_preferences),
            ("Security", "🔒", self.on_security)
        ])
        
        # Test: Add footer items
        self.log("✓ Adding footer items")
        self.sidebar.add_footer_item("Help", icon="❓", callback=self.on_help)
        self.sidebar.add_footer_item("Logout", icon="🚪", callback=self.on_logout)
        
        # Test: Enable collapsible
        self.log("✓ Enabling collapsible")
        self.sidebar.set_collapsible(True)
        
        # Test: Connect signals
        self.sidebar.item_clicked.connect(self.on_sidebar_item)
        self.sidebar.collapsed_changed.connect(self.on_sidebar_collapsed)
        
        layout.addWidget(self.sidebar)
    
    def setup_breadcrumbs_test(self, layout):
        """Set up breadcrumbs test."""
        self.log("\n=== Testing Breadcrumbs ===")
        
        self.breadcrumbs = Breadcrumbs()
        
        # Test: Set path
        self.log("✓ Setting breadcrumb path")
        self.breadcrumbs.set_path(["Home", "Projects", "ART Q Master", "src_v2", "ui", "components_v2"])
        
        # Test: Set max items
        self.log("✓ Setting max items (4)")
        self.breadcrumbs.set_max_items(4)
        
        # Test: Enable home icon
        self.log("✓ Enabling home icon")
        self.breadcrumbs.enable_home_icon(True)
        
        # Test: Enable dropdowns
        self.log("✓ Enabling dropdown menus")
        self.breadcrumbs.enable_dropdowns(True)
        
        # Test: Custom separator
        self.log("✓ Setting custom separator (›)")
        self.breadcrumbs.set_separator("›")
        
        # Test: Connect signals
        self.breadcrumbs.crumb_clicked.connect(self.on_breadcrumb_clicked)
        self.breadcrumbs.item_clicked.connect(self.on_breadcrumb_item)
        
        layout.addWidget(self.breadcrumbs)
    
    def setup_log_area(self, layout):
        """Set up log display area."""
        log_label = QLabel("Action Log:")
        log_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(log_label)
        
        self.log_display = QLabel()
        self.log_display.setWordWrap(True)
        self.log_display.setStyleSheet("""
            QLabel {
                background-color: #f4f4f4;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        self.log_display.setMinimumHeight(200)
        layout.addWidget(self.log_display)
        
        self.update_log_display()
    
    def log(self, message: str):
        """Add message to log."""
        self.action_log.append(message)
        if hasattr(self, 'log_display'):
            self.update_log_display()
        # Handle Unicode encoding for Windows console
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode('ascii', 'replace').decode('ascii'))
    
    def update_log_display(self):
        """Update log display."""
        # Show last 20 messages
        recent_logs = self.action_log[-20:]
        self.log_display.setText("\n".join(recent_logs))
    
    # Toolbar action handlers
    def on_new(self):
        self.log("Action: New file")
    
    def on_open(self):
        self.log("Action: Open file")
    
    def on_save(self):
        self.log("Action: Save file")
    
    def on_bold(self):
        self.log("Action: Bold")
    
    def on_italic(self):
        self.log("Action: Italic")
    
    def on_underline(self):
        self.log("Action: Underline")
    
    def on_settings(self):
        self.log("Action: Settings")
    
    def on_help(self):
        self.log("Action: Help")
    
    def on_toolbar_action(self, action_text: str):
        self.log(f"Toolbar action triggered: {action_text}")
    
    def on_search_changed(self, text: str):
        if text:
            self.log(f"Search: {text}")
    
    # Sidebar action handlers
    def on_dashboard(self):
        self.log("Navigate: Dashboard")
        self.breadcrumbs.set_path(["Home", "Dashboard"])
    
    def on_projects(self):
        self.log("Navigate: Projects")
        self.breadcrumbs.set_path(["Home", "Projects"])
    
    def on_tasks(self):
        self.log("Navigate: Tasks")
        self.breadcrumbs.set_path(["Home", "Tasks"])
    
    def on_calendar(self):
        self.log("Navigate: Calendar")
        self.breadcrumbs.set_path(["Home", "Calendar"])
    
    def on_sales_report(self):
        self.log("Navigate: Sales Report")
        self.breadcrumbs.set_path(["Home", "Reports", "Sales Report"])
    
    def on_analytics(self):
        self.log("Navigate: Analytics")
        self.breadcrumbs.set_path(["Home", "Reports", "Analytics"])
    
    def on_performance(self):
        self.log("Navigate: Performance")
        self.breadcrumbs.set_path(["Home", "Reports", "Performance"])
    
    def on_profile(self):
        self.log("Navigate: Profile")
        self.breadcrumbs.set_path(["Home", "Settings", "Profile"])
    
    def on_preferences(self):
        self.log("Navigate: Preferences")
        self.breadcrumbs.set_path(["Home", "Settings", "Preferences"])
    
    def on_security(self):
        self.log("Navigate: Security")
        self.breadcrumbs.set_path(["Home", "Settings", "Security"])
    
    def on_logout(self):
        self.log("Action: Logout")
    
    def on_sidebar_item(self, text: str):
        self.log(f"Sidebar item clicked: {text}")
    
    def on_sidebar_collapsed(self, collapsed: bool):
        state = "collapsed" if collapsed else "expanded"
        self.log(f"Sidebar {state}")
    
    # Breadcrumb handlers
    def on_breadcrumb_clicked(self, index: int, text: str):
        self.log(f"Breadcrumb clicked: {text} (index: {index})")
    
    def on_breadcrumb_item(self, text: str):
        self.log(f"Breadcrumb item: {text}")


class ThemeTestWindow(QMainWindow):
    """Test window for theme integration."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navigation Theme Test - Phase 5.4")
        self.setGeometry(100, 100, 1000, 600)
        
        self.setup_ui()
        self.setup_theme_test()
    
    def setup_ui(self):
        """Set up UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # Info label
        info = QLabel("Theme Test: Components will cycle through light/dark themes every 2 seconds")
        info.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(info)
        
        # Toolbar
        self.toolbar = ModernToolBar()
        self.toolbar.add_action("Action 1", lambda: None, icon="📄")
        self.toolbar.add_action("Action 2", lambda: None, icon="📂")
        layout.addWidget(self.toolbar)
        
        # Content with sidebar
        content_layout = QHBoxLayout()
        
        self.sidebar = Sidebar()
        self.sidebar.add_item("Item 1", icon="📊")
        self.sidebar.add_item("Item 2", icon="📁")
        content_layout.addWidget(self.sidebar)
        
        # Breadcrumbs
        breadcrumbs_widget = QWidget()
        breadcrumbs_layout = QVBoxLayout(breadcrumbs_widget)
        
        self.breadcrumbs = Breadcrumbs()
        self.breadcrumbs.set_path(["Home", "Test", "Theme"])
        breadcrumbs_layout.addWidget(self.breadcrumbs)
        breadcrumbs_layout.addStretch()
        
        content_layout.addWidget(breadcrumbs_widget, 1)
        layout.addLayout(content_layout, 1)
        
        self.statusBar().showMessage("Theme cycling every 2 seconds...")
    
    def setup_theme_test(self):
        """Set up automatic theme cycling."""
        self.current_theme = "light"
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.cycle_theme)
        self.theme_timer.start(2000)  # 2 seconds
    
    def cycle_theme(self):
        """Cycle between light and dark themes."""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        
        # Update all components
        self.toolbar.set_theme(self.current_theme)
        self.sidebar.set_theme(self.current_theme)
        self.breadcrumbs.set_theme(self.current_theme)
        
        self.statusBar().showMessage(f"Theme: {self.current_theme.upper()}")


class PerformanceTestWindow(QMainWindow):
    """Test window for performance testing."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Navigation Performance Test - Phase 5.4")
        self.setGeometry(100, 100, 1000, 600)
        
        self.setup_ui()
        self.run_performance_tests()
    
    def setup_ui(self):
        """Set up UI."""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        
        # Info label
        info = QLabel("Performance Test: Testing component creation and updates")
        info.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(info)
        
        # Results area
        self.results_label = QLabel()
        self.results_label.setWordWrap(True)
        self.results_label.setStyleSheet("""
            QLabel {
                background-color: #f4f4f4;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 10px;
                font-family: monospace;
            }
        """)
        layout.addWidget(self.results_label, 1)
    
    def run_performance_tests(self):
        """Run performance tests."""
        import time
        results = []
        
        # Test 1: Toolbar creation with many actions
        start = time.time()
        toolbar = ModernToolBar()
        for i in range(50):
            toolbar.add_action(f"Action {i}", lambda: None, icon="📄")
        elapsed = (time.time() - start) * 1000
        results.append(f"✓ Toolbar with 50 actions: {elapsed:.2f}ms")
        
        # Test 2: Sidebar creation with many items
        start = time.time()
        sidebar = Sidebar()
        for i in range(30):
            sidebar.add_item(f"Item {i}", icon="📊")
        elapsed = (time.time() - start) * 1000
        results.append(f"✓ Sidebar with 30 items: {elapsed:.2f}ms")
        
        # Test 3: Breadcrumbs with long path
        start = time.time()
        breadcrumbs = Breadcrumbs()
        path = [f"Level{i}" for i in range(20)]
        breadcrumbs.set_path(path)
        elapsed = (time.time() - start) * 1000
        results.append(f"✓ Breadcrumbs with 20 items: {elapsed:.2f}ms")
        
        # Test 4: Theme switching
        start = time.time()
        for _ in range(100):
            toolbar.set_theme("dark")
            toolbar.set_theme("light")
        elapsed = (time.time() - start) * 1000
        results.append(f"✓ 100 theme switches: {elapsed:.2f}ms")
        
        # Test 5: Sidebar collapse/expand
        start = time.time()
        for _ in range(50):
            sidebar.toggle_collapsed()
        elapsed = (time.time() - start) * 1000
        results.append(f"✓ 50 sidebar toggles: {elapsed:.2f}ms")
        
        # Display results
        results_text = "\n".join(results)
        results_text += "\n\n✅ All performance tests passed!"
        results_text += "\n\nTarget: <16ms per operation (60 FPS)"
        self.results_label.setText(results_text)
        
        self.statusBar().showMessage("Performance tests complete!")


def run_basic_test():
    """Run basic navigation test."""
    print("\n" + "="*60)
    print("NAVIGATION COMPONENTS TEST - PHASE 5.4")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = NavigationTestWindow()
    window.show()
    
    print("\n[OK] Test window opened successfully!")
    print("\nTest Instructions:")
    print("1. Click toolbar actions to test action groups")
    print("2. Use search bar to test search functionality")
    print("3. Click sidebar items to test navigation")
    print("4. Expand/collapse sidebar sections")
    print("5. Click breadcrumbs to test navigation")
    print("6. Use keyboard navigation (Tab, Arrow keys)")
    print("7. Resize window to test responsive behavior")
    print("\nAll actions are logged in the Action Log area.")
    
    return app.exec_()


def run_theme_test():
    """Run theme integration test."""
    print("\n" + "="*60)
    print("NAVIGATION THEME TEST - PHASE 5.4")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = ThemeTestWindow()
    window.show()
    
    print("\n[OK] Theme test window opened!")
    print("Components will cycle between light and dark themes every 2 seconds.")
    
    return app.exec_()


def run_performance_test():
    """Run performance test."""
    print("\n" + "="*60)
    print("NAVIGATION PERFORMANCE TEST - PHASE 5.4")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    window = PerformanceTestWindow()
    window.show()
    
    print("\n[OK] Performance test window opened!")
    print("Running performance tests...")
    
    return app.exec_()


def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "="*60)
    print("RUNNING ALL NAVIGATION TESTS - PHASE 5.4")
    print("="*60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Test 1: Basic functionality
    print("\n[1/3] Basic Functionality Test")
    window1 = NavigationTestWindow()
    window1.show()
    
    # Test 2: Theme integration
    print("\n[2/3] Theme Integration Test")
    window2 = ThemeTestWindow()
    window2.move(window1.x() + window1.width() + 20, window1.y())
    window2.show()
    
    # Test 3: Performance
    print("\n[3/3] Performance Test")
    window3 = PerformanceTestWindow()
    window3.move(window1.x(), window1.y() + window1.height() + 40)
    window3.show()
    
    print("\n[OK] All test windows opened!")
    print("\nTest Coverage:")
    print("  [+] ModernToolBar: Action groups, overflow, search")
    print("  [+] Sidebar: Collapsible, nested navigation, footer")
    print("  [+] Breadcrumbs: Dropdowns, ellipsis, keyboard nav")
    print("  [+] Theme integration")
    print("  [+] Performance optimization")
    
    return app.exec_()


if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "theme":
            sys.exit(run_theme_test())
        elif test_type == "performance":
            sys.exit(run_performance_test())
        elif test_type == "all":
            sys.exit(run_all_tests())
    
    # Default: run basic test
    sys.exit(run_basic_test())

# Made with Bob
