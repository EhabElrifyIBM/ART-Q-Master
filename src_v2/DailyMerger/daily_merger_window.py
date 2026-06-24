"""
Daily Case Merger — Main Window
================================

PyQt5 main window for the Daily Case Merger tool.

Workflow:
  1. User loads up to 30 daily Excel files (drag-drop or browse)
  2. Files are automatically validated on the main thread (sheet-name scan only — fast)
  3. ValidationResult is shown in the summary panel + coverage calendar updates
  4. User picks output file path and clicks Merge
  5. Background QThread worker runs the merge, reporting progress
  6. On completion: success dialog with option to open output folder

Keyboard shortcuts:
  Ctrl+O       Open files (browse)
  Ctrl+Return  Validate (re-scan loaded files)
  Ctrl+M       Start merge
  Ctrl+W       Close window
  F1           About
  Ctrl+L       Toggle activity log panel
  Ctrl+K       Toggle coverage calendar
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize
from PyQt5.QtGui import QKeySequence, QFont, QTextCharFormat, QColor, QTextCursor, QPainter, QPen, QBrush
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QFrame, QLabel,
    QMenuBar, QScrollArea, QSizePolicy, QPlainTextEdit, QTextEdit,
    QPushButton, QCheckBox, QGraphicsOpacityEffect,
)

from ui.typography_mixin import V2TypographyMixin
from ui.theme_manager import ThemeManager
from ui.services import V2SettingsBus
from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem
from ui.components_v2.dialogs import ProgressDialog
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory

from DailyMerger.daily_merger_service import (
    DailyMergerService, MergeConfig, MergeResult, ValidationResult,
)
from DailyMerger.components.daily_file_list import DailyFileListWidget
from DailyMerger.components.daily_summary import DailySummaryWidget
from DailyMerger.components.daily_calendar import DailyCalendarWidget
from utils.recent_daily_merger_files import get_recent_daily_merger_manager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    """HTML-escape a string for safe insertion into QTextEdit.append()."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ---------------------------------------------------------------------------
# Log level constants
# ---------------------------------------------------------------------------
_LOG_LEVEL_COLORS = {
    "INFO":   None,          # theme default text — set at paint time
    "WARN":   "#E6A817",     # amber
    "ERROR":  "#D94040",     # red
    "DETAIL": "#888888",     # muted grey
    "BANNER": "#4A90D9",     # blue — for ── lines
}

_LEVEL_TAG_RE = __import__("re").compile(r"^\[(?P<lvl>INFO|WARN|ERROR|DETAIL)\]\s*")


class DailyMergeWorker(QThread):
    """
    Worker thread for the merge operation.

    Signals:
        progress(int, str):        percent (0-100) and stripped status message (no [LEVEL] prefix)
        log_entry(str, str):       (level, plain message) — window adds timestamp + color
        finished(bool, str, dict): success, message, stats dict
    """

    progress  = pyqtSignal(int, str)
    log_entry = pyqtSignal(str, str)   # (level, message)
    finished  = pyqtSignal(bool, str, dict)

    def __init__(self, service: DailyMergerService, config: MergeConfig) -> None:
        super().__init__()
        self._service = service
        self._config  = config

    def run(self) -> None:
        def cb(percent: int, raw: str) -> None:
            m = _LEVEL_TAG_RE.match(raw)
            if m:
                level = m.group("lvl")
                msg   = raw[m.end():]
            else:
                level = "INFO"
                msg   = raw
            # Determine banner level for ── lines
            if msg.startswith("──"):
                level = "BANNER"
            # Progress bar gets the clean message (no prefix)
            self.progress.emit(percent, msg)
            self.log_entry.emit(level, msg)

        try:
            result: MergeResult = self._service.merge(self._config, progress_callback=cb)
            stats_dict = {
                "files_processed":  result.stats.files_processed,
                "all_cases":        result.stats.all_cases_count,
                "chat_cases":       result.stats.chat_cases_count,
                "companies":        result.stats.companies_count,
                "skipped":          result.stats.skipped_empty_keys,
                "zip_files_expanded": result.stats.zip_files_expanded,
                "output_path":      str(result.output_path) if result.output_path else "",
            }
            self.finished.emit(result.success, result.message, stats_dict)
        except Exception as exc:
            self.log_entry.emit("ERROR", f"Unhandled exception: {exc}")
            self.finished.emit(False, str(exc), {})


# ---------------------------------------------------------------------------
# Validation worker — runs service.validate_files() off the main thread
# ---------------------------------------------------------------------------

class ValidationWorker(QThread):
    """
    Runs DailyMergerService.validate_files() in a background thread so the
    UI stays responsive while ZIP files are extracted and sheet names scanned.

    Signals:
        finished(ValidationResult): emitted with the result when done.
        error(str):                 emitted if an unexpected exception occurs.
    """

    finished = pyqtSignal(object)   # ValidationResult
    error    = pyqtSignal(str)

    def __init__(
        self,
        service: DailyMergerService,
        paths: List[Path],
        accept_zip: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._service    = service
        self._paths      = paths
        self._accept_zip = accept_zip

    def run(self) -> None:
        try:
            result = self._service.validate_files(self._paths, accept_zip=self._accept_zip)
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Scan overlay — shown over the left pane while validation runs
# ---------------------------------------------------------------------------

class ScanOverlay(QWidget):
    """
    Semi-transparent overlay with an animated spinner and a status label.
    Parent it to the widget you want to cover, then call show()/hide().

    The spinner is drawn with QPainter — no image files needed.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # Spinner state
        self._angle   = 0
        self._timer   = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(40)   # 25 fps

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        # Canvas for the arc spinner
        self._canvas = QWidget(self)
        self._canvas.setFixedSize(56, 56)
        self._canvas.paintEvent = self._paint_spinner  # type: ignore[method-assign]
        layout.addWidget(self._canvas, alignment=Qt.AlignCenter)

        self._label = QLabel("Scanning files…", self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setFont(TypographySystem().create_font("body"))
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self.hide()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, message: str = "Scanning files…") -> None:
        """Show the overlay and start spinning."""
        self._label.setText(message)
        self._resize_to_parent()
        self.raise_()
        self.show()
        self._timer.start()

    def stop(self) -> None:
        """Hide the overlay and stop the timer."""
        self._timer.stop()
        self.hide()

    def set_message(self, message: str) -> None:
        self._label.setText(message)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _tick(self) -> None:
        self._angle = (self._angle + 12) % 360
        self._canvas.update()

    def _resize_to_parent(self) -> None:
        if self.parent():
            self.setGeometry(self.parent().rect())  # type: ignore[union-attr]

    def resizeEvent(self, event) -> None:
        self._resize_to_parent()
        super().resizeEvent(event)

    def _paint_spinner(self, event) -> None:  # noqa: ARG002
        painter = QPainter(self._canvas)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background circle
        pen = QPen(QColor("#e0e0e0"), 5)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawEllipse(6, 6, 44, 44)

        # Spinning arc
        pen.setColor(QColor("#0f62fe"))   # IBM Blue
        painter.setPen(pen)
        painter.drawArc(6, 6, 44, 44, -self._angle * 16, 100 * 16)

        painter.end()

    def paintEvent(self, event) -> None:
        """Semi-transparent dark scrim."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 110))
        painter.end()

    def apply_theme(self, theme_mode: str) -> None:
        text_color = "#f4f4f4" if theme_mode == "dark" else "#f4f4f4"
        self._label.setStyleSheet(f"QLabel {{ color: {text_color}; font-weight: bold; }}")


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class DailyMergerWindow(QMainWindow, V2TypographyMixin):
    """Daily Case Merger main window."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self.theme_manager     = ThemeManager()
        self.settings_bus      = V2SettingsBus()
        self.service           = DailyMergerService()
        self.worker: Optional[DailyMergeWorker]       = None
        self._val_worker: Optional[ValidationWorker]   = None
        self._theme_mode       = "light"
        self._last_output_path = ""
        self._recent_manager   = get_recent_daily_merger_manager()

        self._setup_ui()
        self._setup_menu()
        self._setup_shortcuts()
        self._connect_signals()
        self._apply_log_styles()
        self.apply_typography()
        self.log("Daily Case Merger ready — drag & drop files to begin")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setWindowTitle("Daily Case Merger")
        self.setMinimumSize(1200, 900)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        root.setSpacing(Spacing.MD)

        # ── Header ───────────────────────────────────────────────────
        header_row = QHBoxLayout()
        title_lbl = QLabel("📅  Daily Case Merger", self)
        title_lbl.setFont(TypographySystem().create_font("h2"))
        header_row.addWidget(title_lbl)
        header_row.addStretch()

        self._cal_toggle_btn = QPushButton("▲ Hide Calendar", self)
        self._cal_toggle_btn.setFixedHeight(28)
        self._cal_toggle_btn.setFont(TypographySystem().create_font("caption"))
        self._cal_toggle_btn.clicked.connect(self._toggle_calendar)
        header_row.addWidget(self._cal_toggle_btn)

        root.addLayout(header_row)

        # ── Coverage Calendar ─────────────────────────────────────────
        self.calendar = DailyCalendarWidget(self)
        root.addWidget(self.calendar)

        # ── Horizontal splitter: file list (left) | summary (right) ──
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(2)
        splitter.setChildrenCollapsible(False)

        # Left pane — file list
        # Left pane — drop zone inside a container so we can stack the overlay
        left_container = QWidget()
        left_container.setMinimumWidth(280)
        left_stack = QVBoxLayout(left_container)
        left_stack.setContentsMargins(0, 0, 0, 0)
        left_stack.setSpacing(0)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setFrameShape(QFrame.NoFrame)
        self.file_list = DailyFileListWidget()
        left_scroll.setWidget(self.file_list)
        left_stack.addWidget(left_scroll)

        # Overlay — parented to left_container so it covers the whole left pane
        self._scan_overlay = ScanOverlay(left_container)

        # Right pane — summary + merge
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        self.summary = DailySummaryWidget()
        right_scroll.setWidget(self.summary)

        splitter.addWidget(left_container)
        splitter.addWidget(right_scroll)
        # Left = compact drop zone (~320px), right = wide summary + table
        splitter.setSizes([320, 860])
        root.addWidget(splitter, stretch=1)

        # ── Activity Log panel ───────────────────────────────────────
        self._log_panel = QFrame(self)
        self._log_panel.setFrameShape(QFrame.NoFrame)
        log_outer = QVBoxLayout(self._log_panel)
        log_outer.setContentsMargins(0, 0, 0, 0)
        log_outer.setSpacing(0)

        # Header row: title + clear + toggle
        log_header = QFrame(self._log_panel)
        log_header_layout = QHBoxLayout(log_header)
        log_header_layout.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        log_header_layout.setSpacing(Spacing.SM)

        log_title = QLabel("📋  Activity Log", log_header)
        log_title.setFont(TypographySystem().create_font("label"))
        log_header_layout.addWidget(log_title)
        log_header_layout.addStretch()

        self._log_clear_btn = QPushButton("Clear", log_header)
        self._log_clear_btn.setFixedHeight(26)
        self._log_clear_btn.setFixedWidth(54)
        self._log_clear_btn.setFont(TypographySystem().create_font("caption"))
        self._log_clear_btn.clicked.connect(self._clear_log)
        log_header_layout.addWidget(self._log_clear_btn)

        self._log_toggle_btn = QPushButton("▲ Hide", log_header)
        self._log_toggle_btn.setFixedHeight(26)
        self._log_toggle_btn.setFixedWidth(64)
        self._log_toggle_btn.setFont(TypographySystem().create_font("caption"))
        self._log_toggle_btn.clicked.connect(self._toggle_log)
        log_header_layout.addWidget(self._log_toggle_btn)

        log_outer.addWidget(log_header)

        # Text area — QTextEdit so .append(html) works for color-coded lines
        self._log_view = QTextEdit(self._log_panel)
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(200)
        self._log_view.setMinimumHeight(120)
        log_font = QFont("Consolas", 9)
        log_font.setStyleHint(QFont.Monospace)
        self._log_view.setFont(log_font)
        self._log_view.setPlaceholderText("Activity will appear here…")
        log_outer.addWidget(self._log_view)

        root.addWidget(self._log_panel)

        # ── Status bar ───────────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            "Ready — drag & drop up to 30 daily Active Cases files to begin"
        )

    # ------------------------------------------------------------------
    # Menu
    # ------------------------------------------------------------------

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction("&Open Files…", self.file_list.browse_files, QKeySequence.Open)
        file_menu.addAction("&Clear Files", self.file_list.clear_files)
        file_menu.addSeparator()
        file_menu.addAction("E&xit", self.close, QKeySequence.Quit)

        merge_menu = menubar.addMenu("&Merge")
        self._merge_action = merge_menu.addAction("&Start Merge", self._start_merge)
        self._merge_action.setEnabled(False)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&About", self._show_about)
        help_menu.addAction("Keyboard &Shortcuts", self._show_shortcuts)

    # ------------------------------------------------------------------
    # Keyboard shortcuts
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        self.shortcut_manager = ShortcutManager(self)

        self.shortcut_manager.register_shortcut(
            "daily_merger_open",
            ShortcutDefinition(
                key_sequence="Ctrl+O",
                description="Open files",
                category=ShortcutCategory.FILE,
                action=self.file_list.browse_files,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "daily_merger_validate",
            ShortcutDefinition(
                key_sequence="Ctrl+Return",
                description="Re-validate loaded files",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=self._validate_files,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "daily_merger_merge",
            ShortcutDefinition(
                key_sequence="Ctrl+M",
                description="Start merge",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=self._start_merge,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "daily_merger_close",
            ShortcutDefinition(
                key_sequence="Ctrl+W",
                description="Close window",
                category=ShortcutCategory.GLOBAL,
                action=self.close,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "daily_merger_help",
            ShortcutDefinition(
                key_sequence="F1",
                description="Show About",
                category=ShortcutCategory.GLOBAL,
                action=self._show_about,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "daily_merger_log",
            ShortcutDefinition(
                key_sequence="Ctrl+L",
                description="Toggle activity log",
                category=ShortcutCategory.GLOBAL,
                action=self._toggle_log,
            ),
        )
        self.shortcut_manager.register_shortcut(
            "daily_merger_calendar",
            ShortcutDefinition(
                key_sequence="Ctrl+K",
                description="Toggle coverage calendar",
                category=ShortcutCategory.GLOBAL,
                action=self._toggle_calendar,
            ),
        )

    # ------------------------------------------------------------------
    # Signal wiring
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self.file_list.files_changed.connect(self._on_files_changed)
        self.file_list.clear_requested.connect(self.summary.clear_output_path)
        self.summary.merge_requested.connect(self._on_merge_requested)
        self.settings_bus.font_preset_changed.connect(self.apply_typography)
        self.settings_bus.theme_changed.connect(self._on_theme_changed)

    # ------------------------------------------------------------------
    # Slot: files changed → auto-validate
    # ------------------------------------------------------------------

    def _on_files_changed(self, paths: List[Path]) -> None:
        if not paths:
            self.summary.show_idle()
            self.calendar.clear()
            self._merge_action.setEnabled(False)
            self.status_bar.showMessage("No files loaded")
            self.log("WARN", "All files cleared — output path reset")
            return

        zip_count  = sum(1 for p in paths if p.suffix.lower() == ".zip")
        xlsx_count = len(paths) - zip_count
        parts = []
        if xlsx_count:
            parts.append(f"{xlsx_count} Excel")
        if zip_count:
            parts.append(f"{zip_count} ZIP")
        self.log(f"Loaded {len(paths)} file(s): {', '.join(parts)}")
        self.status_bar.showMessage(f"Scanning {len(paths)} file(s)…")
        self._validate_files(paths)

    def _validate_files(self, paths: Optional[List[Path]] = None) -> None:
        """Kick off async validation — shows overlay, never blocks the UI."""
        if paths is None:
            paths = self.file_list.get_files()
        if not paths:
            self.status_bar.showMessage("No files to validate")
            return

        # Abort any previous in-flight validation
        if self._val_worker and self._val_worker.isRunning():
            self._val_worker.quit()
            self._val_worker.wait(300)

        n = len(paths)
        self.log(f"Scanning {n} file{'s' if n != 1 else ''}…")
        self.status_bar.showMessage(f"Scanning {n} file(s)…")
        self._merge_action.setEnabled(False)

        # Show spinner overlay over the left pane
        self._scan_overlay.start(
            f"Scanning {n} file{'s' if n != 1 else ''}…\nReading sheet names"
        )

        self._val_worker = ValidationWorker(
            self.service, paths, self.file_list.zip_enabled(), parent=self
        )
        self._val_worker.finished.connect(self._on_validation_done)
        self._val_worker.error.connect(self._on_validation_error)
        self._val_worker.start()

    def _on_validation_done(self, result: ValidationResult) -> None:
        """Called on the main thread when ValidationWorker finishes."""
        self._scan_overlay.stop()
        self.summary.show_validation(result)

        # Update calendar
        date_strs = [df.date_str for df in result.daily_files]
        self.calendar.set_dates(date_strs)

        if result.is_valid:
            n = len(result.daily_files)
            months = result.months_found
            month_summary = ", ".join(
                f"{m}: {c} file{'s' if c != 1 else ''}"
                for m, c in sorted(months.items())
            )
            warn_count = len(result.warnings)
            skipped    = getattr(result, "skipped_months", [])
            self.log(f"Validation OK — {n} file(s) | Months: {month_summary}")
            if result.handler_names:
                self.log(f"Handlers: {', '.join(result.handler_names)}")
            for w in result.warnings:
                self.log("WARN", w)
            if skipped:
                self.log("WARN", f"Skipped month(s): {', '.join(skipped)}")
            warn_note = f"  ⚠ {warn_count} warning(s)" if warn_count else ""
            skip_note = f"  🚨 Skipped: {', '.join(skipped)}" if skipped else ""
            self.status_bar.showMessage(
                f"✅  {n} daily file(s) validated — {month_summary}{warn_note}{skip_note}"
            )
            self._merge_action.setEnabled(True)
        else:
            self.log("ERROR", f"Validation failed: {result.error}")
            self.status_bar.showMessage(f"❌  Validation failed: {result.error}")
            self._merge_action.setEnabled(False)

    def _on_validation_error(self, error_msg: str) -> None:
        """Called if ValidationWorker raises an unexpected exception."""
        self._scan_overlay.stop()
        self.log("ERROR", f"Validation error: {error_msg}")
        self.status_bar.showMessage(f"❌  Validation error — {error_msg}")
        self._merge_action.setEnabled(False)

    # ------------------------------------------------------------------
    # Slot: merge requested (from summary widget button)
    # ------------------------------------------------------------------

    def _on_merge_requested(self, options: dict) -> None:
        output_path = options.get("output_path", "").strip()
        if not output_path:
            QMessageBox.warning(self, "No Output Path", "Please choose an output file path.")
            return
        self._run_merge(output_path)

    def _start_merge(self) -> None:
        """Triggered by menu / shortcut — reads output path from summary widget."""
        output_path = self.summary.get_output_path()
        if not output_path:
            QMessageBox.warning(self, "No Output Path", "Please choose an output file path.")
            return
        self._run_merge(output_path)

    def _run_merge(self, output_path: str) -> None:
        files = self.file_list.get_files()
        if not files:
            QMessageBox.warning(self, "No Files", "No daily files are loaded.")
            return

        config = MergeConfig(
            file_paths=files,
            output_path=Path(output_path),
            accept_zip=self.file_list.zip_enabled(),
        )
        self._last_output_path = output_path

        self.log("BANNER", f"── Merge started ── {len(files)} file(s) → {Path(output_path).name}")

        progress = ProgressDialog(
            self,
            f"Merging {len(files)} daily workbooks…",
            "Daily Case Merge",
        )
        progress.show()

        self.worker = DailyMergeWorker(self.service, config)
        self.worker.progress.connect(
            lambda pct, msg: (progress.set_progress(pct), progress.set_message(msg))
        )
        self.worker.log_entry.connect(self.log)   # log(level, message)
        self.worker.finished.connect(
            lambda ok, msg, stats: self._on_merge_complete(ok, msg, stats, progress)
        )
        self._merge_action.setEnabled(False)
        # Start status-bar spinner
        self._spinner_ticks = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)
        self._spinner_timer.start(200)
        self.worker.start()

    def _on_merge_complete(
        self,
        success: bool,
        message: str,
        stats: dict,
        progress: ProgressDialog,
    ) -> None:
        progress.close()
        self._merge_action.setEnabled(True)
        # Stop spinner
        if hasattr(self, "_spinner_timer"):
            self._spinner_timer.stop()

        if success:
            output = stats.get("output_path", self._last_output_path)
            # Persist the output folder for next session
            if output:
                self._recent_manager.add_output_folder(str(Path(output).parent))
            self.log("BANNER", "── Merge complete ──")
            self.log("DETAIL", f"   Files processed     : {stats.get('files_processed', '?')}")
            if stats.get("zip_files_expanded", 0):
                self.log("DETAIL", f"   ZIP files expanded  : {stats.get('zip_files_expanded')}")
            self.log("DETAIL", f"   All Cases rows      : {stats.get('all_cases', '?')}")
            self.log("DETAIL", f"   Chat Agent rows     : {stats.get('chat_cases', '?')}")
            self.log("DETAIL", f"   Companies rows      : {stats.get('companies', '?')}")
            if stats.get("skipped", 0):
                self.log("WARN",   f"   Skipped (empty key) : {stats.get('skipped')}")
            self.log("INFO",   f"✔ Output → {output}")
            zip_line = (
                f"ZIP files expanded: {stats.get('zip_files_expanded', 0)}\n"
                if stats.get("zip_files_expanded", 0) else ""
            )
            detail = (
                f"{message}\n\n"
                f"Files processed    : {stats.get('files_processed', '?')}\n"
                f"{zip_line}"
                f"All Cases rows     : {stats.get('all_cases', '?')}\n"
                f"Chat Agent rows    : {stats.get('chat_cases', '?')}\n"
                f"Companies rows     : {stats.get('companies', '?')}\n"
                f"Skipped (empty key): {stats.get('skipped', 0)}\n\n"
                f"Output: {output}"
            )
            reply = QMessageBox.information(
                self,
                "Merge Complete",
                detail,
                QMessageBox.Open | QMessageBox.Ok,
                QMessageBox.Ok,
            )
            if reply == QMessageBox.Open and output:
                _open_in_explorer(output)
            self.status_bar.showMessage("✅  Merge complete — " + message)
        else:
            self.log("ERROR", f"Merge failed: {message}")
            QMessageBox.critical(self, "Merge Error", message)
            self.status_bar.showMessage("❌  Merge failed — see error dialog for details")

    # ------------------------------------------------------------------
    # Theme & typography
    # ------------------------------------------------------------------

    def _toggle_calendar(self) -> None:
        """Show/hide the coverage calendar panel."""
        visible = self.calendar.isVisible()
        self.calendar.setVisible(not visible)
        self._cal_toggle_btn.setText(
            "▲ Hide Calendar" if not visible else "▼ Show Calendar"
        )

    def _on_theme_changed(self, theme_mode: str) -> None:
        self._theme_mode = theme_mode
        self.file_list.set_theme_mode(theme_mode)
        self.summary.set_theme_mode(theme_mode)
        self.calendar.set_theme_mode(theme_mode)
        self._scan_overlay.apply_theme(theme_mode)
        self._apply_log_styles()
        self.status_bar.showMessage(f"Theme changed to {theme_mode}")

    def apply_typography(self) -> None:
        """Reactive typography update — child components manage their own fonts."""
        pass

    # ------------------------------------------------------------------
    # Activity log
    # ------------------------------------------------------------------

    def log(self, level_or_msg: str, message: str = "") -> None:
        """Append a color-coded timestamped line to the activity log.

        Can be called as:
          log("WARN", "some text")   — from worker signal (two args)
          log("some text")           — convenience one-arg call (level = INFO)
        """
        if message:
            level = level_or_msg.upper()
            msg   = message
        else:
            level = "INFO"
            msg   = level_or_msg

        ts = datetime.now().strftime("%H:%M:%S")

        # --- Build the colored HTML fragment ---
        color = _LOG_LEVEL_COLORS.get(level)

        # Prefix decoration per level
        prefixes = {
            "WARN":   "⚠ ",
            "ERROR":  "✖ ",
            "BANNER": "",
            "DETAIL": "  ",   # indent detail lines
        }
        prefix = prefixes.get(level, "")

        timestamp_html = f'<span style="color:#888888;">[{ts}]</span>'

        if color:
            bold_start = "<b>" if level == "BANNER" else ""
            bold_end   = "</b>" if level == "BANNER" else ""
            line_html = (
                f'{timestamp_html} '
                f'<span style="color:{color};">{bold_start}{prefix}{_esc(msg)}{bold_end}</span>'
            )
        else:
            # INFO: use the current theme text colour so it adapts to dark/light
            info_color = getattr(self, "_log_default_text_color", "#222222")
            line_html = (
                f'{timestamp_html} '
                f'<span style="color:{info_color};">{_esc(msg)}</span>'
            )

        # QTextEdit.append() accepts HTML and appends as a new paragraph
        self._log_view.append(line_html)

        # Auto-scroll to bottom
        sb = self._log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _tick_spinner(self) -> None:
        """Animate status bar while merge is running."""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_ticks += 1
        frame = frames[self._spinner_ticks % len(frames)]
        self.status_bar.showMessage(f"{frame}  Merging in progress…")

    def _clear_log(self) -> None:
        self._log_view.clear()
        self.log("Log cleared")

    def _toggle_log(self) -> None:
        visible = self._log_view.isVisible()
        self._log_view.setVisible(not visible)
        self._log_toggle_btn.setText("▲ Hide" if not visible else "▼ Show")

    def _apply_log_styles(self) -> None:
        from ui.design_system import Colors
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        bg     = colors["background"]
        border = colors["border"]
        text   = colors["text_primary"]
        surface = colors["surface"]

        self._log_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px;
                selection-background-color: {colors['primary']};
            }}
        """)
        # Keep INFO-level (unstyled) text matching the theme
        self._log_default_text_color = text
        log_header_style = f"""
            QFrame {{
                background-color: {surface};
                border: 1px solid {border};
                border-bottom: none;
                border-radius: 4px 4px 0 0;
            }}
            QLabel {{ color: {text}; }}
            QPushButton {{
                background-color: {surface};
                color: {colors['text_secondary']};
                border: 1px solid {border};
                border-radius: 3px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: {colors['surface_hover']};
                color: {text};
            }}
        """
        # Apply to the log panel's first child (the header frame)
        header = self._log_panel.layout().itemAt(0).widget()
        if header:
            header.setStyleSheet(log_header_style)

    # ------------------------------------------------------------------
    # About / shortcuts
    # ------------------------------------------------------------------

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            "About Daily Case Merger",
            "Daily Case Merger v1.0\n\n"
            "Merges up to 30 daily 'Active Cases PA MM-DD.xlsx' workbooks\n"
            "into a single deduplicated output with three sheets:\n"
            "  • All Cases (all handler sheets combined)\n"
            "  • Chat Agent's Cases\n"
            "  • Companies\n\n"
            "Deduplication: latest day always wins (per case number).\n\n"
            "Keyboard shortcuts:\n"
            "  Ctrl+O    Open files\n"
            "  Ctrl+↵    Re-validate\n"
            "  Ctrl+M    Start merge\n"
            "  Ctrl+W    Close window\n"
            "  F1        Show this dialog",
        )

    def _show_shortcuts(self) -> None:
        self.shortcut_manager.show_help_dialog()

    # ------------------------------------------------------------------
    # Close guard
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        # Stop background validation silently
        if self._val_worker and self._val_worker.isRunning():
            self._val_worker.quit()
            self._val_worker.wait(500)
        # Guard against closing mid-merge
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Merge in Progress",
                "A merge is still running.\n\nAre you sure you want to close?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.worker.terminate()
            self.worker.wait(2000)
        event.accept()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _open_in_explorer(path: str) -> None:
    """Open the output file's parent folder in the OS file explorer."""
    try:
        folder = str(Path(path).parent)
        if sys.platform == "win32":
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", folder])
        else:
            subprocess.Popen(["xdg-open", folder])
    except Exception:
        pass


__all__ = ["DailyMergerWindow"]

# Made with Bob
