"""
Archiver Main Window (Phase 6.2 — Fixed & Upgraded)
=====================================================

Fixes applied:
 #1/#2  file_selected signal now emits Path → _on_file_selected receives Path
 #3     calls set_analysis_results() (not the non-existent set_analysis())
 #4     wires export_by_month_clicked / export_by_age_clicked (not export_requested)
 #5     ExportDialog uses add_content/add_buttons via ModernDialog API
 #6     ArchiveWorker 'export' calls export_by_month / export_by_age (not export_cases)
 #8     Both "Export by Month" and "Export by Age" buttons open the correct dialog
 #9     progress_callback is (percent: int, message: str) throughout
#15     calls dialog.get_export_options() which now exists
#16     menu calls self.file_selector.browse_file() which is now public

Upgrades:
- Window summary bar shows workbook stats after analysis
- Export button group disabled until analysis is complete
- Theme propagates to all child components
- Worker error messages shown with full detail in QMessageBox
"""

from pathlib import Path
from typing import Optional, Dict

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QStatusBar, QMessageBox, QLabel, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QKeySequence, QFont

from ui.typography_mixin import V2TypographyMixin
from ui.theme_manager import ThemeManager
from ui.services import get_v2_settings_bus
from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from ui.components_v2.dialogs import ProgressDialog
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory

from Archiver.archiver_service import (
    ArchiverService, MonthExportOptions, AgeExportOptions
)
from Archiver.components.file_selector import FileSelectorWidget
from Archiver.components.analysis_view import AnalysisViewWidget
from Archiver.components.export_dialog import ExportDialog


# ---------------------------------------------------------------------------
# Background worker
# ---------------------------------------------------------------------------

class ArchiveWorker(QThread):
    """
    Worker thread for long-running archiver operations.

    Signals:
        progress(int, str): percent (0-100) and status message
        finished(bool, str): success flag and result/error message
    """

    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, service: ArchiverService, operation: str, *args):
        super().__init__()
        self.service = service
        self.operation = operation   # 'analyze' | 'export_month' | 'export_age'
        self.args = args

    def run(self) -> None:
        # FIX #9: progress callback correctly matches (percent: int, message: str)
        def cb(percent: int, msg: str) -> None:
            self.progress.emit(percent, msg)

        try:
            if self.operation == "analyze":
                file_path: Path = self.args[0]
                self.progress.emit(10, "Loading workbook…")
                self.service.load_workbook(str(file_path))
                self.progress.emit(50, "Analysing sheets…")
                self.service.analyze_workbook()
                self.progress.emit(100, "Analysis complete")
                self.finished.emit(True, "Analysis complete")

            elif self.operation == "export_month":
                # FIX #6: call export_by_month(), not the non-existent export_cases()
                options: MonthExportOptions = self.args[0]
                success, msg = self.service.export_by_month(
                    options,
                    progress_callback=cb,
                )
                self.finished.emit(success, msg)

            elif self.operation == "export_age":
                # FIX #6: call export_by_age()
                options: AgeExportOptions = self.args[0]
                success, msg = self.service.export_by_age(
                    options,
                    progress_callback=cb,
                )
                self.finished.emit(success, msg)

            else:
                self.finished.emit(False, f"Unknown operation: {self.operation}")

        except Exception as exc:
            self.finished.emit(False, str(exc))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class ArchiverWindow(QMainWindow, V2TypographyMixin):
    """Modern Case Archiver main window."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self.theme_manager = ThemeManager()
        self.settings_bus = get_v2_settings_bus()
        self.service = ArchiverService()
        self.current_analysis: Optional[Dict] = None
        self.worker: Optional[ArchiveWorker] = None
        self._theme_mode = "light"

        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._connect_signals()
        self.apply_typography()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setWindowTitle("Case Archiver")
        self.setMinimumSize(820, 640)
        self.resize(960, 740)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setSpacing(0)
        outer.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.SM)

        # ── Top section: file selector + analyse button ───────────────
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(Spacing.SM)

        self.file_selector = FileSelectorWidget()
        top_layout.addWidget(self.file_selector)

        analyse_row = QHBoxLayout()
        analyse_row.addStretch()
        self.analyze_btn = PrimaryButton("🔍  Analyse File")
        self.analyze_btn.setMinimumHeight(44)
        self.analyze_btn.setEnabled(False)
        self.analyze_btn.setToolTip(
            "Analyse the selected Excel workbook for handler sheets and case dates  (Ctrl+↵)"
        )
        analyse_row.addWidget(self.analyze_btn)
        top_layout.addLayout(analyse_row)

        # ── Splitter: top (file) | bottom (analysis results) ─────────
        from PyQt5.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(top_widget)

        # Analysis view lives in a scroll area so it never clips at small sizes
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.analysis_view = AnalysisViewWidget()
        self.analysis_view.setVisible(True)
        scroll.setWidget(self.analysis_view)
        splitter.addWidget(scroll)

        # Give top section ~40% and analysis ~60% of initial space
        splitter.setSizes([300, 420])
        outer.addWidget(splitter, 1)

        # ── Status bar ───────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — select an Excel workbook to begin")

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        # FIX #16: browse_file() is now public
        file_menu.addAction(
            "&Open File…",
            self.file_selector.browse_file,
            QKeySequence.Open,
        )
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, QKeySequence.Quit)

        # Export menu (only enabled after analysis)
        self._export_menu = menubar.addMenu("&Export")
        self._export_month_action = self._export_menu.addAction(
            "Export by &Month…",
            lambda: self._show_export_dialog("month"),
        )
        self._export_age_action = self._export_menu.addAction(
            "Export by &Age…",
            lambda: self._show_export_dialog("age"),
        )
        self._export_menu.setEnabled(False)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self._show_about)
        help_menu.addAction("Keyboard &Shortcuts", self._show_shortcuts)

    # ------------------------------------------------------------------
    # Shortcuts
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        self.shortcut_manager = ShortcutManager(self)

        self.shortcut_manager.register_shortcut(
            "archiver_open",
            ShortcutDefinition(
                key_sequence="Ctrl+O",
                description="Open file",
                category=ShortcutCategory.FILE,
                # FIX #16: public method
                action=self.file_selector.browse_file,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "archiver_analyse",
            ShortcutDefinition(
                key_sequence="Ctrl+Return",
                description="Analyse selected file",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=self._analyse_file,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "archiver_export_month",
            ShortcutDefinition(
                key_sequence="Ctrl+M",
                description="Export by Month",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=lambda: self._show_export_dialog("month"),
            ),
        )
        self.shortcut_manager.register_shortcut(
            "archiver_export_age",
            ShortcutDefinition(
                key_sequence="Ctrl+G",
                description="Export by Age",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=lambda: self._show_export_dialog("age"),
            ),
        )
        self.shortcut_manager.register_shortcut(
            "archiver_close",
            ShortcutDefinition(
                key_sequence="Ctrl+W",
                description="Close window",
                category=ShortcutCategory.GLOBAL,
                action=self.close,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "archiver_help",
            ShortcutDefinition(
                key_sequence="F1",
                description="Show about",
                category=ShortcutCategory.GLOBAL,
                action=self._show_about,
            ),
        )

    # ------------------------------------------------------------------
    # Signal connections (all FIXes for signal wiring)
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        # FIX #1/#2: file_selected now emits Path; _on_file_selected receives Path
        self.file_selector.file_selected.connect(self._on_file_selected)

        self.analyze_btn.clicked.connect(self._analyse_file)

        # FIX #4: connect the correct signals that AnalysisViewWidget actually has
        self.analysis_view.export_by_month_clicked.connect(
            lambda: self._show_export_dialog("month")
        )
        self.analysis_view.export_by_age_clicked.connect(
            lambda: self._show_export_dialog("age")
        )

        self.settings_bus.font_preset_changed.connect(self.apply_typography)
        self.settings_bus.theme_changed.connect(self._on_theme_changed)

    # ------------------------------------------------------------------
    # File selection
    # ------------------------------------------------------------------

    def _on_file_selected(self, file_path: Path) -> None:
        """Handle a file being selected — enables the Analyse button."""
        self.analyze_btn.setEnabled(True)
        self.status_bar.showMessage(f"Selected: {file_path.name}  —  press Analyse to continue")
        # Reset analysis view if a new file is selected
        self.analysis_view.clear_results()
        self.current_analysis = None
        self._export_menu.setEnabled(False)

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def _analyse_file(self) -> None:
        file_path = self.file_selector.get_selected_file()
        if not file_path:
            return

        progress = ProgressDialog(self, "Analysing workbook structure…", "Analysing File")
        progress.show()

        self.worker = ArchiveWorker(self.service, "analyze", file_path)
        self.worker.progress.connect(
            lambda pct, msg: (progress.set_progress(pct), progress.set_message(msg))
        )
        self.worker.finished.connect(
            lambda ok, msg: self._on_analysis_complete(ok, msg, progress)
        )
        self.analyze_btn.setEnabled(False)
        self.worker.start()

    def _on_analysis_complete(
        self, success: bool, message: str, progress: ProgressDialog
    ) -> None:
        progress.close()
        self.analyze_btn.setEnabled(True)

        if success:
            self.current_analysis = self.service.analysis_results
            if self.current_analysis:
                self.analysis_view.set_analysis_results(self.current_analysis)
                self._export_menu.setEnabled(True)

                stats = self.service.get_summary_stats()
                companies_note = " + Companies" if stats.get("has_companies") else ""
                self.status_bar.showMessage(
                    f"✅  {stats.get('total_handlers', 0)} handler(s){companies_note}, "
                    f"{stats.get('total_cases', 0):,} case(s), "
                    f"{len(stats.get('all_months', []))} month(s) — ready to export"
                )
        else:
            QMessageBox.critical(self, "Analysis Error", message)
            self.status_bar.showMessage("Analysis failed — see error dialog for details")

    # ------------------------------------------------------------------
    # Export dialogs  (FIX #8: both month and age are reachable)
    # ------------------------------------------------------------------

    def _show_export_dialog(self, export_type: str) -> None:
        """Open the export dialog for 'month' or 'age' export type."""
        if not self.current_analysis:
            QMessageBox.information(
                self,
                "No Analysis",
                "Please analyse a workbook first before exporting.",
            )
            return

        dialog = ExportDialog(self, self.service, export_type=export_type)
        if dialog.exec_():
            # FIX #15: get_export_options() now exists in ExportDialog
            options = dialog.get_export_options()
            self._run_export(options)

    def _run_export(self, options: dict) -> None:
        """Start the export worker thread with the given options dict."""
        export_type = options.get("export_type", "month")

        # Build the strongly-typed options object the service expects
        if export_type == "month":
            typed_options = MonthExportOptions(
                handler=options["handler"],
                output_file=options["output_file"],
                cleanup=options.get("cleanup", False),
                merged=options.get("merged", False),
                months=options.get("months", []),
            )
            operation = "export_month"
        else:
            typed_options = AgeExportOptions(
                handler=options["handler"],
                output_file=options["output_file"],
                cleanup=options.get("cleanup", False),
                merged=options.get("merged", False),
                days=options.get("days", 30),
            )
            operation = "export_age"

        progress = ProgressDialog(
            self,
            f"Preparing {export_type} export…",
            "Exporting Cases",
        )
        progress.show()

        # FIX #6: operation is now 'export_month' / 'export_age', not 'export'
        self.worker = ArchiveWorker(self.service, operation, typed_options)
        self.worker.progress.connect(
            lambda pct, msg: (progress.set_progress(pct), progress.set_message(msg))
        )
        self.worker.finished.connect(
            lambda ok, msg: self._on_export_complete(ok, msg, progress)
        )
        self.analyze_btn.setEnabled(False)
        self.worker.start()

    def _on_export_complete(
        self, success: bool, message: str, progress: ProgressDialog
    ) -> None:
        progress.close()
        self.analyze_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Export Complete", message)
            self.status_bar.showMessage("Export complete")
        else:
            QMessageBox.critical(self, "Export Error", message)
            self.status_bar.showMessage("Export failed — see error dialog for details")

    # ------------------------------------------------------------------
    # Theme & typography
    # ------------------------------------------------------------------

    def _on_theme_changed(self, theme_mode: str) -> None:
        self._theme_mode = theme_mode
        self.file_selector.set_theme_mode(theme_mode)
        self.analysis_view.set_theme_mode(theme_mode)
        self.status_bar.showMessage(
            f"Theme changed to {theme_mode} — restart may be needed for full effect"
        )

    def apply_typography(self) -> None:
        """Reactive typography update (called by V2TypographyMixin on preset change)."""
        pass  # Child components manage their own fonts via TypographySystem

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Case Archiver",
            "Case Archiver v2.0\n\n"
            "Modern tool for archiving closed cases from Excel workbooks.\n\n"
            "Features:\n"
            "  • Drag-drop or browse file selection\n"
            "  • Month-based and age-based exports\n"
            "  • All-handler or single-handler exports\n"
            "  • Companies sheet archived together with handler sheets\n"
            "  • Merged sheet option for month exports\n"
            "  • Automatic timestamped backups\n"
            "  • Recent files tracking\n"
            "  • Live export preview\n\n"
            "Keyboard shortcuts:\n"
            "  Ctrl+O  Open file\n"
            "  Ctrl+↵  Analyse\n"
            "  Ctrl+M  Export by Month\n"
            "  Ctrl+G  Export by Age\n"
            "  Ctrl+W  Close window\n"
            "  F1      Show this dialog",
        )

    def _show_shortcuts(self) -> None:
        self.shortcut_manager.show_help_dialog()

    # ------------------------------------------------------------------
    # Close guard
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Operation in Progress",
                "An operation is still running.\n\nAre you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.worker.terminate()
            self.worker.wait(2000)   # give it up to 2 s to stop cleanly
        event.accept()


# Made with Bob
