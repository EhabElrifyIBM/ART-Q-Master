"""Modern Merger main window."""
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFileDialog,
    QLabel,
    QStatusBar,
)

from ui.typography_mixin import V2TypographyMixin
from ui.services import V2SettingsBus
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from ui.components_v2.dialogs import ProgressDialog
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory
from Merger.merger_service import (
    MergerService,
    ColumnMapping,
    MergeConfig,
    FileInfo,
)
from Merger.components.file_list import FileListWidget
from Merger.components.sheet_selector import SheetSelectorWidget
from Merger.components.column_mapper import ColumnMapperWidget
from Merger.components.preview_dialog import PreviewDialog
from utils.recent_merger_files import get_recent_merger_files_manager


class MergerWorker(QThread):
    """Worker thread for merger operations."""

    progress = pyqtSignal(int, str)
    preview_ready = pyqtSignal(bool, str, object, dict)
    merge_finished = pyqtSignal(bool, str, object)

    def __init__(self, service: MergerService, operation: str, payload=None):
        super().__init__()
        self.service = service
        self.operation = operation
        self.payload = payload

    def run(self):
        """Execute worker operation."""
        try:
            if self.operation == "preview":
                mappings: List[ColumnMapping] = self.payload or []
                self.progress.emit(20, "Building preview...")
                success, message, preview_df = self.service.preview_merge(mappings, max_rows=100)
                stats = self.service.get_merge_statistics()
                if preview_df is not None:
                    stats["total_columns"] = len(preview_df.columns)
                else:
                    stats["total_columns"] = 0
                stats["file_count"] = stats.get("total_files", 0)
                self.progress.emit(100, "Preview ready")
                self.preview_ready.emit(success, message, preview_df, stats)
                return

            if self.operation == "merge":
                if not isinstance(self.payload, MergeConfig):
                    raise ValueError("Invalid merge configuration payload")
                config = self.payload
                step = {"count": 0}

                def progress_callback(message: str):
                    step["count"] += 1
                    progress_value = min(95, 10 + step["count"] * 20)
                    self.progress.emit(progress_value, message)

                self.progress.emit(10, "Starting merge...")
                result = self.service.merge_files(config, progress_callback=progress_callback)
                self.progress.emit(100, "Merge finished")
                self.merge_finished.emit(result.success, result.output_file or "", result)
        except Exception as exc:
            if self.operation == "preview":
                self.preview_ready.emit(False, str(exc), None, {})
            else:
                self.merge_finished.emit(False, "", exc)


class MergerWindow(QMainWindow, V2TypographyMixin):
    """Modern Excel Merger tool main window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self.settings_bus = V2SettingsBus()
        self.service = MergerService()
        self.recent_manager = get_recent_merger_files_manager()
        self.worker: Optional[MergerWorker] = None

        self._current_preview_dialog: Optional[PreviewDialog] = None
        self._last_output_path: Optional[str] = None

        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._connect_signals()
        self.apply_typography()

    def _setup_ui(self):
        """Setup main UI."""
        self.setWindowTitle("Excel Merger")
        self.setMinimumSize(1200, 800)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.title_label = QLabel("Excel Merger")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(
            "Load multiple Excel files, choose sheets, map columns, preview, and merge."
        )
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.file_list = FileListWidget()
        layout.addWidget(self.file_list)

        self.sheet_selector = SheetSelectorWidget()
        self.sheet_selector.setVisible(False)
        layout.addWidget(self.sheet_selector)

        self.column_mapper = ColumnMapperWidget()
        self.column_mapper.setVisible(False)
        layout.addWidget(self.column_mapper)

        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.preview_btn = SecondaryButton("Preview Merge")
        self.preview_btn.setEnabled(False)
        action_layout.addWidget(self.preview_btn)

        self.merge_btn = PrimaryButton("Merge & Save")
        self.merge_btn.setEnabled(False)
        action_layout.addWidget(self.merge_btn)

        layout.addLayout(action_layout)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()
        if menubar is None:
            return

        file_menu = menubar.addMenu("&File")
        if file_menu is not None:
            file_menu.addAction("&Open Files...", self.file_list._browse_files, QKeySequence.Open)
            file_menu.addAction("&Preview Merge", self._preview_merge, "Ctrl+P")
            file_menu.addAction("&Merge and Save...", self._merge_files, "Ctrl+S")
            file_menu.addSeparator()
            file_menu.addAction("E&xit", self.close, QKeySequence.Quit)

        help_menu = menubar.addMenu("&Help")
        if help_menu is not None:
            help_menu.addAction("&About", self._show_about)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        self.shortcut_manager = ShortcutManager(self)

        self.shortcut_manager.register_shortcut(
            "merger_open",
            ShortcutDefinition(
                key_sequence="Ctrl+O",
                description="Open Excel files",
                category=ShortcutCategory.FILE,
                action=self.file_list._browse_files,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "merger_preview",
            ShortcutDefinition(
                key_sequence="Ctrl+P",
                description="Preview merge result",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=self._preview_merge,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "merger_save",
            ShortcutDefinition(
                key_sequence="Ctrl+S",
                description="Merge and save output",
                category=ShortcutCategory.FILE,
                action=self._merge_files,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "merger_close",
            ShortcutDefinition(
                key_sequence="Ctrl+W",
                description="Close window",
                category=ShortcutCategory.GLOBAL,
                action=self.close,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "merger_help",
            ShortcutDefinition(
                key_sequence="F1",
                description="Show help",
                category=ShortcutCategory.GLOBAL,
                action=self._show_about,
            ),
        )

    def _connect_signals(self):
        """Connect signals."""
        self.file_list.files_changed.connect(self._on_files_changed)
        self.file_list.file_loaded.connect(self._on_file_loaded)
        self.sheet_selector.sheets_changed.connect(self._on_sheets_changed)
        self.column_mapper.mapping_changed.connect(self._on_mappings_changed)
        self.preview_btn.clicked.connect(self._preview_merge)
        self.merge_btn.clicked.connect(self._merge_files)

        self.settings_bus.font_preset_changed.connect(lambda _: self.apply_typography())
        self.settings_bus.theme_changed.connect(self._on_theme_changed)

    def apply_typography(self):
        """Apply typography to main window widgets."""
        self.title_label.setFont(self.get_font("h2"))
        self.subtitle_label.setFont(self.get_font("body"))

    def _on_file_loaded(self, file_path: str):
        """Load file into merger service."""
        success, message, _file_info = self.service.load_file(file_path)
        self.status_bar.showMessage(message)
        if not success:
            QMessageBox.warning(self, "File Load Error", message)

    def _on_files_changed(self, file_paths: List[str]):
        """Handle file list changes."""
        current_loaded = set(self.service.loaded_files.keys())
        current_selected = {str(Path(path).resolve()) for path in file_paths}

        for removed_path in current_loaded - current_selected:
            self.service.remove_file(removed_path)

        self._refresh_sheet_selector()
        self._refresh_column_mapper()

        has_files = len(file_paths) > 0
        self.sheet_selector.setVisible(has_files)
        self.column_mapper.setVisible(has_files)
        self._update_action_buttons()

        if has_files:
            self.status_bar.showMessage(f"{len(file_paths)} file(s) selected")
        else:
            self.status_bar.showMessage("Ready")

    def _refresh_sheet_selector(self):
        """Refresh sheet selector from loaded files."""
        file_sheets: Dict[Path, List[str]] = {}
        for file_info in self.service.get_loaded_files():
            file_sheets[Path(file_info.path)] = list(file_info.sheets)

        self.sheet_selector.set_files(file_sheets)

        current_files = {Path(info.path): info for info in self.service.get_loaded_files()}
        for file_path, info in current_files.items():
            if info.selected_sheet:
                self.sheet_selector.set_selections({file_path: info.selected_sheet})

    def _refresh_column_mapper(self):
        """Refresh available columns from selected sheets."""
        columns = self.service.get_all_columns()
        self.column_mapper.set_columns(columns)

    def _on_sheets_changed(self, selections: Dict[Path, str]):
        """Handle selected sheet changes."""
        for file_path, sheet_name in selections.items():
            self.service.set_selected_sheet(str(file_path), sheet_name)

        self._refresh_column_mapper()
        self._update_action_buttons()
        self.status_bar.showMessage("Sheet selections updated")

    def _on_mappings_changed(self, mappings: Dict[str, List[str]]):
        """Handle column mapping changes."""
        self._update_action_buttons()
        self.status_bar.showMessage(f"{len(mappings)} mapping(s) configured")

    def _build_column_mappings(self) -> List[ColumnMapping]:
        """Build service mappings from UI mappings."""
        mappings = []
        for target, sources in self.column_mapper.get_mappings().items():
            if sources:
                mappings.append(
                    ColumnMapping(
                        output_name=target,
                        source_columns=sources,
                        merge_strategy="first_non_null",
                    )
                )
        return mappings

    def _update_action_buttons(self):
        """Update action button states."""
        has_files = len(self.service.get_loaded_files()) > 0
        has_mappings = len(self.column_mapper.get_mappings()) > 0
        self.preview_btn.setEnabled(has_files and has_mappings)
        self.merge_btn.setEnabled(has_files and has_mappings)

    def _preview_merge(self):
        """Preview merge result."""
        mappings = self._build_column_mappings()
        if not mappings:
            QMessageBox.information(self, "Preview Merge", "Configure at least one column mapping first.")
            return

        progress = ProgressDialog(self, message="Generating merge preview...", title="Preparing Preview")
        progress.show()

        self.worker = MergerWorker(self.service, "preview", mappings)
        self.worker.progress.connect(lambda v, msg: (progress.set_progress(v), progress.set_message(msg)))
        self.worker.preview_ready.connect(
            lambda success, message, preview_df, stats: self._on_preview_ready(
                success, message, preview_df, stats, progress
            )
        )
        self.worker.start()

    def _on_preview_ready(self, success: bool, message: str, preview_df, stats: dict, progress: ProgressDialog):
        """Handle preview completion."""
        progress.close()

        if not success or preview_df is None:
            QMessageBox.warning(self, "Preview Error", message)
            self.status_bar.showMessage("Preview failed")
            return

        dialog = PreviewDialog(preview_df, stats, self)
        self._current_preview_dialog = dialog
        dialog.exec_()
        self.status_bar.showMessage(message)

    def _merge_files(self):
        """Execute merge and save output."""
        mappings = self._build_column_mappings()
        if not mappings:
            QMessageBox.information(self, "Merge Files", "Configure at least one column mapping first.")
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged File",
            self._last_output_path or "merged_result.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv)",
        )
        if not output_path:
            return

        self._last_output_path = output_path

        config = MergeConfig(
            files=self.service.get_loaded_files(),
            column_mappings=mappings,
            output_path=output_path,
            include_source_info=True,
        )

        progress = ProgressDialog(self, message="Preparing merge...", title="Merging Files")
        progress.show()

        self.worker = MergerWorker(self.service, "merge", config)
        self.worker.progress.connect(lambda v, msg: (progress.set_progress(v), progress.set_message(msg)))
        self.worker.merge_finished.connect(
            lambda success, output_file, result: self._on_merge_complete(
                success, output_file, result, progress
            )
        )
        self.worker.start()

    def _on_merge_complete(self, success: bool, output_file: str, result, progress: ProgressDialog):
        """Handle merge completion."""
        progress.close()

        if not success:
            error_message = str(result)
            if hasattr(result, "errors") and result.errors:
                error_message = "\n".join(result.errors)
            QMessageBox.critical(self, "Merge Error", error_message)
            self.status_bar.showMessage("Merge failed")
            return

        if hasattr(result, "rows_merged") and hasattr(result, "columns_count"):
            self.recent_manager.add_merge_operation(
                file_paths=self.file_list.get_file_paths(),
                output_path=output_file,
                column_count=result.columns_count,
                row_count=result.rows_merged,
            )
            success_message = (
                f"Merged file saved to:\n{output_file}\n\n"
                f"Rows: {result.rows_merged}\n"
                f"Columns: {result.columns_count}"
            )
        else:
            success_message = f"Merged file saved to:\n{output_file}"

        QMessageBox.information(self, "Merge Complete", success_message)
        self.status_bar.showMessage("Merge complete")

    def _on_theme_changed(self, theme_mode: str):
        """Handle theme change."""
        self.file_list.set_theme_mode(theme_mode)
        self.sheet_selector.set_theme_mode(theme_mode)
        self.column_mapper.set_theme_mode(theme_mode)
        if self._current_preview_dialog is not None:
            self._current_preview_dialog.set_theme_mode(theme_mode)
        self.status_bar.showMessage(f"Theme changed to {theme_mode}")

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Excel Merger",
            "Excel Merger v2.0\n\n"
            "Modern tool for consolidating multiple Excel files into a single output.\n\n"
            "Features:\n"
            "• Multi-file selection\n"
            "• Per-file sheet selection\n"
            "• Flexible column mapping\n"
            "• Merge preview\n"
            "• Recent operations tracking",
        )

    def closeEvent(self, a0):
        """Handle window close."""
        if a0 is None:
            return

        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Operation in Progress",
                "A merge operation is in progress. Are you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                a0.ignore()
                return
            self.worker.terminate()
        a0.accept()


__all__ = ["MergerWindow", "MergerWorker"]

# Made with Bob