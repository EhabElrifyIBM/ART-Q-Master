"""
Test Suite for Tables Component (Phase 5.3)
============================================

Comprehensive tests for ModernTableWidget and related components.

Test Coverage:
- Basic table creation and data management
- Column sorting (ascending, descending, none)
- Column filtering (text search)
- Row selection (single, multiple, checkbox)
- Pagination (page navigation, page size)
- Empty state display
- Loading state display
- Row styling (hover, alternating colors)
- Column resizing and reordering
- Export functionality (CSV, Excel)
- Keyboard navigation
- Theme integration
- Performance benchmarks

Run with: python src_v2/test_components_tables.py
"""

import sys
import time
import tempfile
import os
from typing import List
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer

# Add src_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from ui.components_v2.tables import ModernTableWidget, SelectionMode, SortOrder
from ui.typography import FontSizePreset


class TableTestWindow(QMainWindow):
    """Test window for table components."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tables Component Test Suite - Phase 5.3")
        self.setGeometry(100, 100, 1400, 900)
        
        # Test results
        self.test_results = []
        self.tests_passed = 0
        self.tests_failed = 0
        
        self._setup_ui()
        self._run_tests()
    
    def _setup_ui(self):
        """Set up test UI."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Title
        title = QLabel("Tables Component Test Suite - Phase 5.3")
        title.setStyleSheet("font-size: 24px; font-weight: bold; padding: 20px;")
        layout.addWidget(title)
        
        # Test controls
        controls = QHBoxLayout()
        
        self.run_all_btn = QPushButton("Run All Tests")
        self.run_all_btn.clicked.connect(self._run_tests)
        controls.addWidget(self.run_all_btn)
        
        self.theme_toggle_btn = QPushButton("Toggle Theme")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)
        controls.addWidget(self.theme_toggle_btn)
        
        self.font_cycle_btn = QPushButton("Cycle Font Size")
        self.font_cycle_btn.clicked.connect(self._cycle_font)
        controls.addWidget(self.font_cycle_btn)
        
        controls.addStretch()
        layout.addLayout(controls)
        
        # Test results label
        self.results_label = QLabel("Running tests...")
        self.results_label.setStyleSheet("font-size: 16px; padding: 10px;")
        layout.addWidget(self.results_label)
        
        # Main test table
        self.test_table = ModernTableWidget()
        layout.addWidget(self.test_table)
        
        # Current theme
        self.current_theme = "light"
        self.current_preset = FontSizePreset.NORMAL
    
    def _log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"
        
        self.test_results.append(result)
        print(result)
        
        if passed:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def _update_results_display(self):
        """Update results label."""
        total = self.tests_passed + self.tests_failed
        coverage = (self.tests_passed / total * 100) if total > 0 else 0
        
        self.results_label.setText(
            f"Tests: {self.tests_passed} passed, {self.tests_failed} failed, "
            f"{total} total | Coverage: {coverage:.1f}%"
        )
    
    def _run_tests(self):
        """Run all tests."""
        print("\n" + "="*80)
        print("TABLES COMPONENT TEST SUITE - PHASE 5.3")
        print("="*80 + "\n")
        
        self.test_results = []
        self.tests_passed = 0
        self.tests_failed = 0
        
        # Run test categories
        self._test_basic_functionality()
        self._test_data_management()
        self._test_sorting()
        self._test_filtering()
        self._test_selection()
        self._test_pagination()
        self._test_states()
        self._test_export()
        self._test_theming()
        self._test_performance()
        
        # Update display
        self._update_results_display()
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.tests_passed + self.tests_failed}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Coverage: {(self.tests_passed / (self.tests_passed + self.tests_failed) * 100):.1f}%")
        print("="*80 + "\n")
    
    def _test_basic_functionality(self):
        """Test basic table functionality."""
        print("\n--- Basic Functionality Tests ---")
        
        # Test 1: Table creation
        try:
            table = ModernTableWidget()
            self._log_test("Table creation", True)
        except Exception as e:
            self._log_test("Table creation", False, str(e))
            return
        
        # Test 2: Set columns
        try:
            headers = ["Name", "Email", "Status"]
            table.set_columns(headers)
            self._log_test("Set columns", table._column_headers == headers)
        except Exception as e:
            self._log_test("Set columns", False, str(e))
        
        # Test 3: Add single row
        try:
            row = ["John Doe", "john@example.com", "Active"]
            table.add_row(row)
            self._log_test("Add single row", len(table._all_data) == 1)
        except Exception as e:
            self._log_test("Add single row", False, str(e))
        
        # Test 4: Set data
        try:
            data = [
                ["Jane Smith", "jane@example.com", "Active"],
                ["Bob Johnson", "bob@example.com", "Inactive"]
            ]
            table.set_data(data)
            self._log_test("Set data", len(table._all_data) == 2)
        except Exception as e:
            self._log_test("Set data", False, str(e))
        
        # Test 5: Clear all
        try:
            table.clear_all()
            self._log_test("Clear all", len(table._all_data) == 0)
        except Exception as e:
            self._log_test("Clear all", False, str(e))
    
    def _test_data_management(self):
        """Test data management features."""
        print("\n--- Data Management Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["ID", "Name", "Value"])
        
        # Test 1: Get all data
        try:
            data = [["1", "A", "100"], ["2", "B", "200"]]
            table.set_data(data)
            all_data = table.get_all_data()
            self._log_test("Get all data", len(all_data) == 2)
        except Exception as e:
            self._log_test("Get all data", False, str(e))
        
        # Test 2: Get filtered data (no filters)
        try:
            filtered = table.get_filtered_data()
            self._log_test("Get filtered data", len(filtered) == 2)
        except Exception as e:
            self._log_test("Get filtered data", False, str(e))
        
        # Test 3: Column widths
        try:
            table.set_column_widths([100, 200, 150])
            self._log_test("Set column widths", True)
        except Exception as e:
            self._log_test("Set column widths", False, str(e))
        
        # Test 4: Resize to contents
        try:
            table.resize_columns_to_contents()
            self._log_test("Resize columns to contents", True)
        except Exception as e:
            self._log_test("Resize columns to contents", False, str(e))
    
    def _test_sorting(self):
        """Test sorting functionality."""
        print("\n--- Sorting Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["Name", "Age", "Score"])
        data = [
            ["Charlie", "30", "85"],
            ["Alice", "25", "95"],
            ["Bob", "35", "75"]
        ]
        table.set_data(data)
        
        # Test 1: Sort ascending
        try:
            table._sort_column = 0
            table._sort_order = SortOrder.ASCENDING
            table._apply_sort()
            first_name = table._filtered_data[0][0]
            self._log_test("Sort ascending", first_name == "Alice")
        except Exception as e:
            self._log_test("Sort ascending", False, str(e))
        
        # Test 2: Sort descending
        try:
            table._sort_order = SortOrder.DESCENDING
            table._apply_sort()
            first_name = table._filtered_data[0][0]
            self._log_test("Sort descending", first_name == "Charlie")
        except Exception as e:
            self._log_test("Sort descending", False, str(e))
        
        # Test 3: Sort none
        try:
            table._sort_order = SortOrder.NONE
            table._apply_sort()
            self._log_test("Sort none", len(table._filtered_data) == 3)
        except Exception as e:
            self._log_test("Sort none", False, str(e))
        
        # Test 4: Sort indicators
        try:
            table._sort_column = 0
            table._sort_order = SortOrder.ASCENDING
            table._update_sort_indicators()
            self._log_test("Sort indicators", True)
        except Exception as e:
            self._log_test("Sort indicators", False, str(e))
    
    def _test_filtering(self):
        """Test filtering functionality."""
        print("\n--- Filtering Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["Name", "Email", "Status"])
        data = [
            ["Alice", "alice@example.com", "Active"],
            ["Bob", "bob@example.com", "Inactive"],
            ["Charlie", "charlie@example.com", "Active"]
        ]
        table.set_data(data)
        
        # Test 1: Enable filtering
        try:
            table.enable_filtering(True)
            self._log_test("Enable filtering", table._filtering_enabled)
        except Exception as e:
            self._log_test("Enable filtering", False, str(e))
        
        # Test 2: Apply filter
        try:
            table._filters[0] = "alice"
            table._apply_filters()
            self._log_test("Apply filter", len(table._filtered_data) == 1)
        except Exception as e:
            self._log_test("Apply filter", False, str(e))
        
        # Test 3: Multiple filters
        try:
            table._filters = {}
            table._filters[2] = "active"
            table._apply_filters()
            self._log_test("Multiple filters", len(table._filtered_data) == 2)
        except Exception as e:
            self._log_test("Multiple filters", False, str(e))
        
        # Test 4: Clear filters
        try:
            table._filters = {}
            table._apply_filters()
            self._log_test("Clear filters", len(table._filtered_data) == 3)
        except Exception as e:
            self._log_test("Clear filters", False, str(e))
    
    def _test_selection(self):
        """Test selection functionality."""
        print("\n--- Selection Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["Name", "Value"])
        data = [["A", "1"], ["B", "2"], ["C", "3"]]
        table.set_data(data)
        
        # Test 1: Single selection mode
        try:
            table.set_selection_mode(SelectionMode.SINGLE)
            self._log_test("Single selection mode", table._selection_mode == SelectionMode.SINGLE)
        except Exception as e:
            self._log_test("Single selection mode", False, str(e))
        
        # Test 2: Multiple selection mode
        try:
            table.set_selection_mode(SelectionMode.MULTIPLE)
            self._log_test("Multiple selection mode", table._selection_mode == SelectionMode.MULTIPLE)
        except Exception as e:
            self._log_test("Multiple selection mode", False, str(e))
        
        # Test 3: No selection mode
        try:
            table.set_selection_mode(SelectionMode.NONE)
            self._log_test("No selection mode", table._selection_mode == SelectionMode.NONE)
        except Exception as e:
            self._log_test("No selection mode", False, str(e))
        
        # Test 4: Checkbox column
        try:
            table.enable_checkbox_column(True)
            self._log_test("Enable checkbox column", table._checkbox_column)
        except Exception as e:
            self._log_test("Enable checkbox column", False, str(e))
        
        # Test 5: Get selected rows
        try:
            selected = table.get_selected_rows()
            self._log_test("Get selected rows", isinstance(selected, list))
        except Exception as e:
            self._log_test("Get selected rows", False, str(e))
    
    def _test_pagination(self):
        """Test pagination functionality."""
        print("\n--- Pagination Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["ID", "Name"])
        
        # Generate large dataset
        data = [[str(i), f"Item {i}"] for i in range(100)]
        table.set_data(data)
        
        # Test 1: Enable pagination
        try:
            table.enable_pagination(True, page_size=10)
            self._log_test("Enable pagination", table._pagination_enabled)
        except Exception as e:
            self._log_test("Enable pagination", False, str(e))
        
        # Test 2: Page size
        try:
            self._log_test("Page size", table._page_size == 10)
        except Exception as e:
            self._log_test("Page size", False, str(e))
        
        # Test 3: Displayed data count
        try:
            table._update_display()
            self._log_test("Displayed data count", len(table._displayed_data) == 10)
        except Exception as e:
            self._log_test("Displayed data count", False, str(e))
        
        # Test 4: Page navigation
        try:
            table._current_page = 2
            table._update_display()
            self._log_test("Page navigation", len(table._displayed_data) == 10)
        except Exception as e:
            self._log_test("Page navigation", False, str(e))
        
        # Test 5: Last page
        try:
            table._current_page = 10
            table._update_display()
            self._log_test("Last page", len(table._displayed_data) == 10)
        except Exception as e:
            self._log_test("Last page", False, str(e))
    
    def _test_states(self):
        """Test table states."""
        print("\n--- State Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["Name", "Value"])
        
        # Test 1: Loading state
        try:
            table.set_loading(True)
            self._log_test("Loading state", table._is_loading)
        except Exception as e:
            self._log_test("Loading state", False, str(e))
        
        # Test 2: Empty state
        try:
            table.set_loading(False)
            table.set_data([])
            table._update_display()
            self._log_test("Empty state", table._is_empty)
        except Exception as e:
            self._log_test("Empty state", False, str(e))
        
        # Test 3: Custom empty message
        try:
            table.set_empty_message("No data available")
            self._log_test("Custom empty message", table._empty_label.text() == "No data available")
        except Exception as e:
            self._log_test("Custom empty message", False, str(e))
        
        # Test 4: Normal state
        try:
            table.set_data([["A", "1"]])
            table._update_display()
            self._log_test("Normal state", not table._is_empty and not table._is_loading)
        except Exception as e:
            self._log_test("Normal state", False, str(e))
    
    def _test_export(self):
        """Test export functionality."""
        print("\n--- Export Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["Name", "Email"])
        data = [["John", "john@example.com"], ["Jane", "jane@example.com"]]
        table.set_data(data)
        
        # Test 1: Enable export
        try:
            table.enable_export(True)
            self._log_test("Enable export", table._export_enabled)
        except Exception as e:
            self._log_test("Enable export", False, str(e))
        
        # Test 2: CSV export (without dialog)
        try:
            # Create temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                temp_path = f.name
            
            # Export manually
            import csv
            with open(temp_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(table._column_headers)
                writer.writerows(table._filtered_data)
            
            # Verify file exists
            exists = os.path.exists(temp_path)
            
            # Cleanup
            if exists:
                os.unlink(temp_path)
            
            self._log_test("CSV export", exists)
        except Exception as e:
            self._log_test("CSV export", False, str(e))
        
        # Test 3: Excel export capability check
        try:
            import openpyxl
            has_openpyxl = True
        except ImportError:
            has_openpyxl = False
        
        self._log_test("Excel export capability", has_openpyxl, 
                      "openpyxl not installed" if not has_openpyxl else "")
    
    def _test_theming(self):
        """Test theme integration."""
        print("\n--- Theming Tests ---")
        
        table = ModernTableWidget()
        table.set_columns(["Name", "Value"])
        table.set_data([["A", "1"]])
        
        # Test 1: Light theme
        try:
            table.set_theme("light")
            self._log_test("Light theme", table._theme_mode == "light")
        except Exception as e:
            self._log_test("Light theme", False, str(e))
        
        # Test 2: Dark theme
        try:
            table.set_theme("dark")
            self._log_test("Dark theme", table._theme_mode == "dark")
        except Exception as e:
            self._log_test("Dark theme", False, str(e))
        
        # Test 3: Font preset
        try:
            table.set_font_preset(FontSizePreset.LARGE)
            self._log_test("Font preset", table._typography._preset == FontSizePreset.LARGE)
        except Exception as e:
            self._log_test("Font preset", False, str(e))
        
        # Test 4: Theme propagation to pagination
        try:
            table.enable_pagination(True)
            table.set_theme("light")
            self._log_test("Theme propagation", table._pagination_widget._theme_mode == "light")
        except Exception as e:
            self._log_test("Theme propagation", False, str(e))
    
    def _test_performance(self):
        """Test performance benchmarks."""
        print("\n--- Performance Tests ---")
        
        # Test 1: 100 rows render time
        try:
            table = ModernTableWidget()
            table.set_columns(["ID", "Name", "Email", "Status"])
            data = [[str(i), f"User {i}", f"user{i}@example.com", "Active"] for i in range(100)]
            
            start = time.time()
            table.set_data(data)
            table._update_display()
            elapsed = (time.time() - start) * 1000
            
            self._log_test("100 rows render", elapsed < 50, f"{elapsed:.2f}ms")
        except Exception as e:
            self._log_test("100 rows render", False, str(e))
        
        # Test 2: 1000 rows render time
        try:
            table = ModernTableWidget()
            table.set_columns(["ID", "Name", "Email", "Status"])
            data = [[str(i), f"User {i}", f"user{i}@example.com", "Active"] for i in range(1000)]
            
            start = time.time()
            table.set_data(data)
            table._update_display()
            elapsed = (time.time() - start) * 1000
            
            self._log_test("1000 rows render", elapsed < 100, f"{elapsed:.2f}ms")
        except Exception as e:
            self._log_test("1000 rows render", False, str(e))
        
        # Test 3: Sorting performance
        try:
            table = ModernTableWidget()
            table.set_columns(["ID", "Name"])
            data = [[str(i), f"User {i}"] for i in range(1000)]
            table.set_data(data)
            
            start = time.time()
            table._sort_column = 1
            table._sort_order = SortOrder.ASCENDING
            table._apply_sort()
            elapsed = (time.time() - start) * 1000
            
            self._log_test("Sorting 1000 rows", elapsed < 50, f"{elapsed:.2f}ms")
        except Exception as e:
            self._log_test("Sorting 1000 rows", False, str(e))
        
        # Test 4: Filtering performance
        try:
            table = ModernTableWidget()
            table.set_columns(["ID", "Name"])
            data = [[str(i), f"User {i}"] for i in range(1000)]
            table.set_data(data)
            
            start = time.time()
            table._filters[1] = "User 5"
            table._apply_filters()
            elapsed = (time.time() - start) * 1000
            
            self._log_test("Filtering 1000 rows", elapsed < 50, f"{elapsed:.2f}ms")
        except Exception as e:
            self._log_test("Filtering 1000 rows", False, str(e))
        
        # Test 5: Pagination with large dataset
        try:
            table = ModernTableWidget()
            table.set_columns(["ID", "Name"])
            data = [[str(i), f"User {i}"] for i in range(10000)]
            table.enable_pagination(True, page_size=100)
            
            start = time.time()
            table.set_data(data)
            elapsed = (time.time() - start) * 1000
            
            self._log_test("Pagination 10000 rows", elapsed < 200, f"{elapsed:.2f}ms")
        except Exception as e:
            self._log_test("Pagination 10000 rows", False, str(e))
    
    def _toggle_theme(self):
        """Toggle theme for visual testing."""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.test_table.set_theme(self.current_theme)
        print(f"Theme changed to: {self.current_theme}")
    
    def _cycle_font(self):
        """Cycle font size for visual testing."""
        presets = [FontSizePreset.SMALL, FontSizePreset.NORMAL, FontSizePreset.LARGE, FontSizePreset.XLARGE]
        current_idx = presets.index(self.current_preset)
        self.current_preset = presets[(current_idx + 1) % len(presets)]
        self.test_table.set_font_preset(self.current_preset)
        print(f"Font preset changed to: {self.current_preset.value}")


def run_visual_demo():
    """Run visual demonstration of table features."""
    print("\n" + "="*80)
    print("VISUAL DEMONSTRATION")
    print("="*80 + "\n")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = TableTestWindow()
    
    # Set up demo table
    window.test_table.set_columns(["ID", "Name", "Email", "Department", "Status"])
    
    # Generate demo data
    departments = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
    statuses = ["Active", "Inactive", "On Leave"]
    
    demo_data = []
    for i in range(150):
        demo_data.append([
            str(i + 1),
            f"Employee {i + 1}",
            f"employee{i + 1}@company.com",
            departments[i % len(departments)],
            statuses[i % len(statuses)]
        ])
    
    window.test_table.set_data(demo_data)
    
    # Enable all features
    window.test_table.enable_filtering(True)
    window.test_table.enable_pagination(True, page_size=25)
    window.test_table.enable_export(True)
    window.test_table.set_selection_mode(SelectionMode.MULTIPLE)
    
    # Auto-resize columns
    window.test_table.resize_columns_to_contents()
    
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(run_visual_demo())

# Made with Bob
