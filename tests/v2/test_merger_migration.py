"""Integration tests for Merger migration (Phase 6.3)."""
import sys

from PyQt5.QtWidgets import QApplication

from Merger import MergerWindow, MergerService
from Merger.components.sheet_selector import SheetSelectorWidget
from Merger.components.column_mapper import ColumnMapperWidget
from Merger.components.preview_dialog import PreviewDialog
from utils.tool_registry import get_tool_definition


def test_merger_window_creation():
    """Test window creation."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    assert window.windowTitle() == "Excel Merger"
    assert window.isVisible() is False
    assert window.minimumWidth() == 1200
    assert window.minimumHeight() == 800
    window.close()
    print("✓ Window creation test passed")


def test_service_integration():
    """Test merger service integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    assert window.service is not None
    assert isinstance(window.service, MergerService)
    assert hasattr(window.service, "load_file")
    assert hasattr(window.service, "preview_merge")
    assert hasattr(window.service, "merge_files")
    window.close()
    print("✓ Service integration test passed")


def test_component_integration():
    """Test component integration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    assert window.file_list is not None
    assert window.sheet_selector is not None
    assert window.column_mapper is not None
    assert isinstance(window.sheet_selector, SheetSelectorWidget)
    assert isinstance(window.column_mapper, ColumnMapperWidget)
    window.close()
    print("✓ Component integration test passed")


def test_action_button_initial_state():
    """Test action buttons initial state."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    assert window.preview_btn.isEnabled() is False
    assert window.merge_btn.isEnabled() is False
    window.close()
    print("✓ Action button initial state test passed")


def test_keyboard_shortcuts():
    """Test keyboard shortcuts registration."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    assert window.shortcut_manager is not None
    assert hasattr(window.shortcut_manager, "_registry")
    registry = window.shortcut_manager.get_registry().get_all()
    assert "merger_open" in registry
    assert "merger_preview" in registry
    assert "merger_save" in registry
    assert "merger_close" in registry
    window.close()
    print("✓ Keyboard shortcuts test passed")


def test_menu_and_status_bar():
    """Test menu and status bar setup."""
    app = QApplication.instance() or QApplication(sys.argv)
    window = MergerWindow()
    menubar = window.menuBar()
    assert menubar is not None
    actions = menubar.actions()
    assert len(actions) >= 2
    assert window.status_bar is not None
    assert window.statusBar() is not None
    window.close()
    print("✓ Menu and status bar test passed")


def test_sheet_selector_component():
    """Test sheet selector component behavior."""
    app = QApplication.instance() or QApplication(sys.argv)
    widget = SheetSelectorWidget()
    widget.set_files({})
    assert widget.get_selections() == {}
    widget.close()
    print("✓ Sheet selector component test passed")


def test_column_mapper_component():
    """Test column mapper component behavior."""
    app = QApplication.instance() or QApplication(sys.argv)
    widget = ColumnMapperWidget()
    widget.set_columns(["Name", "Email", "Phone"])
    assert widget.all_columns == ["Name", "Email", "Phone"]
    widget.set_mappings({"Customer Name": ["Name"]})
    assert widget.get_mappings() == {"Customer Name": ["Name"]}
    widget.clear_mappings()
    assert widget.get_mappings() == {}
    widget.close()
    print("✓ Column mapper component test passed")


def test_preview_dialog_creation():
    """Test preview dialog creation."""
    import pandas as pd

    app = QApplication.instance() or QApplication(sys.argv)
    df = pd.DataFrame(
        [
            {"Name": "Alice", "Email": "alice@example.com"},
            {"Name": "Bob", "Email": "bob@example.com"},
        ]
    )
    dialog = PreviewDialog(
        df,
        {
            "total_rows": 2,
            "total_columns": 2,
            "file_count": 1,
        },
    )
    assert dialog.windowTitle() == "Merge Preview"
    assert dialog.minimumWidth() == 900
    assert dialog.minimumHeight() == 650
    dialog.close()
    print("✓ Preview dialog creation test passed")


def test_tool_registry_updated():
    """Test Merger tool registry status."""
    definition = get_tool_definition("merger")
    assert definition.tool_id == "merger"
    assert definition.status == "migrated-phase-6.3"
    assert definition.icon == "🔗"
    print("✓ Tool registry update test passed")


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("Running Merger Migration Integration Tests (Phase 6.3)")
    print("=" * 60 + "\n")

    try:
        test_merger_window_creation()
        test_service_integration()
        test_component_integration()
        test_action_button_initial_state()
        test_keyboard_shortcuts()
        test_menu_and_status_bar()
        test_sheet_selector_component()
        test_column_mapper_component()
        test_preview_dialog_creation()
        test_tool_registry_updated()

        print("\n" + "=" * 60)
        print("✅ All tests passed! Phase 6.3 integration complete.")
        print("=" * 60 + "\n")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob