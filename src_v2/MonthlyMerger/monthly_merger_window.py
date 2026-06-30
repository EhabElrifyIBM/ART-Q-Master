"""
Monthly Case Merger - Main Window
==================================

Merges monthly output workbooks (produced by the Daily Case Merger) into a
single deduplicated result.  Accepts any .xlsx file regardless of naming.

Deduplication rule: latest month always overwrites earlier month,
keyed on column A (All Cases / Companies) or column L (Chat Agent Cases).

Keyboard shortcuts:
  Ctrl+O       Browse files
  Ctrl+M       Start merge
  Ctrl+W       Close window
  Ctrl+L       Toggle activity log
  F1           About
"""

from __future__ import annotations

import os
# subprocess intentionally removed — use QDesktopServices instead (avoids AV heuristics)
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QPainter, QPen, QColor
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QFrame, QLabel,
    QScrollArea, QSizePolicy, QTextEdit,
    QPushButton, QLineEdit, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from ui.typography_mixin import V2TypographyMixin
from ui.theme_manager import ThemeManager
from ui.services import get_v2_settings_bus
from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem
from ui.components_v2.dialogs import ProgressDialog
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory

from DailyMerger.daily_merger_service import (
    DailyMergerService, MergeConfig, ValidationResult,
    _parse_month_label_from_filename,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _esc(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


_MONTH_NAMES = {
    "01": "January",  "02": "February", "03": "March",    "04": "April",
    "05": "May",      "06": "June",     "07": "July",      "08": "August",
    "09": "September","10": "October",  "11": "November",  "12": "December",
}

_LOG_COLORS = {
    "INFO": None, "WARN": "#E6A817", "ERROR": "#D94040",
    "DETAIL": "#888888", "BANNER": "#4A90D9",
}


def _ro_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
    item.setTextAlignment(Qt.AlignCenter)
    return item


# ---------------------------------------------------------------------------
# Merge worker
# ---------------------------------------------------------------------------

class MonthlyMergeWorker(QThread):
    progress  = pyqtSignal(int, str)
    log_entry = pyqtSignal(str, str)   # (level, message)
    finished  = pyqtSignal(bool, str, dict)

    def __init__(self, service: DailyMergerService, config: MergeConfig, parent=None):
        super().__init__(parent)
        self._service = service
        self._config  = config

    def run(self) -> None:
        import re
        _TAG = re.compile(r"^\[(?P<lvl>INFO|WARN|ERROR|DETAIL)\]\s*")

        def cb(pct: int, raw: str) -> None:
            m = _TAG.match(raw)
            lvl = m.group("lvl") if m else "INFO"
            msg = raw[m.end():] if m else raw
            if msg.startswith("──"):
                lvl = "BANNER"
            self.progress.emit(pct, msg)
            self.log_entry.emit(lvl, msg)

        try:
            result = self._service.merge(self._config, progress_callback=cb)
            stats = result.stats
            # Replace "daily" with "monthly" in the success message
            msg = result.message.replace("daily files", "monthly files")
            self.finished.emit(result.success, msg, {
                "files_processed": stats.files_processed,
                "all_cases":       stats.all_cases_count,
                "chat_cases":      stats.chat_cases_count,
                "companies":       stats.companies_count,
                "skipped":         stats.skipped_empty_keys,
                "output_path":     str(result.output_path) if result.output_path else "",
            })
        except Exception as exc:
            self.log_entry.emit("ERROR", f"Unhandled: {exc}")
            self.finished.emit(False, str(exc), {})


# ---------------------------------------------------------------------------
# Scan overlay
# ---------------------------------------------------------------------------

class ScanOverlay(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(40)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        self._canvas = QWidget(self)
        self._canvas.setFixedSize(56, 56)
        self._canvas.paintEvent = self._paint_spinner  # type: ignore[method-assign]
        layout.addWidget(self._canvas, alignment=Qt.AlignCenter)

        self._lbl = QLabel("Scanning…", self)
        self._lbl.setAlignment(Qt.AlignCenter)
        self._lbl.setFont(TypographySystem().create_font("body"))
        self._lbl.setWordWrap(True)
        self._lbl.setStyleSheet("QLabel { color: #f4f4f4; font-weight: bold; }")
        layout.addWidget(self._lbl)
        self.hide()

    def start(self, msg: str = "Scanning…") -> None:
        self._lbl.setText(msg)
        if self.parent():
            self.setGeometry(self.parent().rect())  # type: ignore[union-attr]
        self.raise_()
        self.show()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self.hide()

    def _tick(self) -> None:
        self._angle = (self._angle + 12) % 360
        self._canvas.update()

    def _paint_spinner(self, _event) -> None:
        p = QPainter(self._canvas)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#e0e0e0"), 5)
        pen.setCapStyle(Qt.RoundCap)
        p.setPen(pen)
        p.drawEllipse(6, 6, 44, 44)
        pen.setColor(QColor("#0f62fe"))
        p.setPen(pen)
        p.drawArc(6, 6, 44, 44, -self._angle * 16, 100 * 16)
        p.end()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))
        p.end()


# ---------------------------------------------------------------------------
# Validation worker
# ---------------------------------------------------------------------------

class ValidationWorker(QThread):
    finished = pyqtSignal(object)
    error    = pyqtSignal(str)

    def __init__(self, service: DailyMergerService, paths: List[Path], parent=None):
        super().__init__(parent)
        self._service = service
        self._paths   = paths

    def run(self) -> None:
        try:
            result = self._service.validate_files(
                self._paths, accept_zip=False, relaxed_filename=True
            )
            self.finished.emit(result)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MonthlyMergerWindow(QMainWindow, V2TypographyMixin):
    """Monthly Case Merger main window."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self.theme_manager = ThemeManager()
        self.settings_bus = get_v2_settings_bus()
        self.service       = DailyMergerService()
        self.worker:       Optional[MonthlyMergeWorker] = None
        self._val_worker:  Optional[ValidationWorker]   = None
        self._theme_mode   = "light"
        self._last_output  = ""
        self._files:       List[Path] = []

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
        self._apply_styles()
        self.log("Monthly Case Merger ready — drop monthly workbooks to begin")

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        self.setWindowTitle("Monthly Case Merger")
        self.setMinimumSize(1200, 860)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        root.setSpacing(Spacing.MD)

        # Header
        hdr = QHBoxLayout()
        t = TypographySystem()
        title = QLabel("📆  Monthly Case Merger", self)
        title.setFont(t.create_font("h2"))
        hdr.addWidget(title)
        hdr.addStretch()
        sub = QLabel("Merge monthly output files — latest month overwrites earlier", self)
        sub.setFont(t.create_font("body_sm"))
        hdr.addWidget(sub)
        root.addLayout(hdr)

        # Splitter
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setHandleWidth(2)
        splitter.setChildrenCollapsible(False)

        # ── Left: drop zone with overlay ──────────────────────────────
        left_container = QWidget()
        left_container.setMinimumWidth(280)
        left_vbox = QVBoxLayout(left_container)
        left_vbox.setContentsMargins(0, 0, 0, 0)
        left_vbox.setSpacing(0)

        self._drop_frame = self._build_drop_zone(left_container)
        left_vbox.addWidget(self._drop_frame, stretch=1)
        self._overlay = ScanOverlay(left_container)

        # ── Right: table + output + merge ─────────────────────────────
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_widget = QWidget()
        right_vbox = QVBoxLayout(right_widget)
        right_vbox.setContentsMargins(Spacing.MD, 0, 0, 0)
        right_vbox.setSpacing(Spacing.MD)

        sec_title = QLabel("📋  Loaded Monthly Files", right_widget)
        sec_title.setFont(t.create_font("h3"))
        right_vbox.addWidget(sec_title)

        self._month_lbl = QLabel("", right_widget)
        self._month_lbl.setFont(t.create_font("body"))
        self._month_lbl.setWordWrap(True)
        right_vbox.addWidget(self._month_lbl)

        # File table — 5 columns (added "Order" to show which file wins in deduplication)
        self._table = QTableWidget(0, 5, right_widget)
        self._table.setHorizontalHeaderLabels(
            ["Order", "Filename", "Month Range", "Sheets Found", "Status"]
        )
        hdr2 = self._table.horizontalHeader()
        hdr2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr2.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr2.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(240)
        self._table.setFont(t.create_font("body_sm"))
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        right_vbox.addWidget(self._table)

        # Output path row
        out_label = QLabel("Output File:", right_widget)
        out_label.setFont(t.create_font("label"))
        right_vbox.addWidget(out_label)

        out_row = QHBoxLayout()
        out_row.setSpacing(Spacing.SM)
        self._output_edit = QLineEdit(right_widget)
        self._output_edit.setMinimumHeight(44)
        self._output_edit.setPlaceholderText("Choose output file path…")
        self._output_edit.setFont(t.create_font("body_sm"))
        out_row.addWidget(self._output_edit)
        browse_out = SecondaryButton("Browse…", right_widget)
        browse_out.setMinimumHeight(44)
        browse_out.clicked.connect(self._browse_output)
        out_row.addWidget(browse_out)
        right_vbox.addLayout(out_row)

        # Merge button
        self._merge_btn = PrimaryButton("🔀  Merge Monthly Files", right_widget)
        self._merge_btn.setMinimumHeight(52)
        self._merge_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._merge_btn.setEnabled(False)
        self._merge_btn.clicked.connect(self._start_merge)
        right_vbox.addWidget(self._merge_btn)
        right_vbox.addStretch()

        right_scroll.setWidget(right_widget)

        splitter.addWidget(left_container)
        splitter.addWidget(right_scroll)
        splitter.setSizes([320, 860])
        root.addWidget(splitter, stretch=1)

        # ── Activity log ──────────────────────────────────────────────
        self._log_panel = QFrame(self)
        self._log_panel.setFrameShape(QFrame.NoFrame)
        log_outer = QVBoxLayout(self._log_panel)
        log_outer.setContentsMargins(0, 0, 0, 0)
        log_outer.setSpacing(0)

        log_header = QFrame(self._log_panel)
        log_hl = QHBoxLayout(log_header)
        log_hl.setContentsMargins(Spacing.SM, Spacing.XS, Spacing.SM, Spacing.XS)
        log_hl.setSpacing(Spacing.SM)
        log_title_lbl = QLabel("📋  Activity Log", log_header)
        log_title_lbl.setFont(t.create_font("label"))
        log_hl.addWidget(log_title_lbl)
        log_hl.addStretch()
        clr_btn = QPushButton("Clear", log_header)
        clr_btn.setFixedSize(54, 26)
        clr_btn.setFont(t.create_font("caption"))
        clr_btn.clicked.connect(lambda: self._log_view.clear())
        log_hl.addWidget(clr_btn)
        self._log_toggle_btn = QPushButton("▲ Hide", log_header)
        self._log_toggle_btn.setFixedSize(64, 26)
        self._log_toggle_btn.setFont(t.create_font("caption"))
        self._log_toggle_btn.clicked.connect(self._toggle_log)
        log_hl.addWidget(self._log_toggle_btn)
        log_outer.addWidget(log_header)

        self._log_view = QTextEdit(self._log_panel)
        self._log_view.setReadOnly(True)
        self._log_view.setMaximumHeight(200)
        self._log_view.setMinimumHeight(120)
        lf = QFont("Consolas", 9)
        lf.setStyleHint(QFont.Monospace)
        self._log_view.setFont(lf)
        self._log_view.setPlaceholderText("Activity will appear here…")
        log_outer.addWidget(self._log_view)
        root.addWidget(self._log_panel)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready — drop monthly merged workbooks to begin")

    def _build_drop_zone(self, parent: QWidget) -> QFrame:
        frame = QFrame(parent)
        frame.setAcceptDrops(True)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        frame.dragEnterEvent = self._dz_drag_enter
        frame.dragLeaveEvent = lambda e: self._set_dz_active(False)
        frame.dropEvent      = self._dz_drop

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)
        layout.setAlignment(Qt.AlignCenter)

        icon = QLabel("📆", frame)
        icon.setAlignment(Qt.AlignCenter)
        icon.setFont(QFont("Segoe UI Emoji", 36))
        layout.addWidget(icon)

        self._dz_title = QLabel("Drop Monthly Merged Files Here", frame)
        self._dz_title.setAlignment(Qt.AlignCenter)
        self._dz_title.setFont(TypographySystem().create_font("h3"))
        layout.addWidget(self._dz_title)

        self._dz_sub = QLabel(
            "Accepts any .xlsx workbook with\nAll Cases, Chat Agent, and Companies sheets",
            frame,
        )
        self._dz_sub.setAlignment(Qt.AlignCenter)
        self._dz_sub.setFont(TypographySystem().create_font("body_sm"))
        self._dz_sub.setWordWrap(True)
        layout.addWidget(self._dz_sub)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(Spacing.SM)

        browse_btn = PrimaryButton("Browse Files…", frame)
        browse_btn.setMinimumHeight(44)
        browse_btn.setMinimumWidth(130)
        browse_btn.clicked.connect(self._browse_files)
        btn_row.addWidget(browse_btn)

        self._clear_btn = SecondaryButton("Clear All", frame)
        self._clear_btn.setMinimumHeight(44)
        self._clear_btn.setMinimumWidth(100)
        self._clear_btn.setEnabled(False)
        self._clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(self._clear_btn)
        layout.addLayout(btn_row)

        self._summary_lbl = QLabel("No files loaded", frame)
        self._summary_lbl.setAlignment(Qt.AlignCenter)
        self._summary_lbl.setFont(TypographySystem().create_font("body_sm"))
        layout.addWidget(self._summary_lbl)

        return frame

    # ------------------------------------------------------------------
    # Drag-drop
    # ------------------------------------------------------------------

    def _dz_drag_enter(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith((".xlsx", ".xls")):
                    event.acceptProposedAction()
                    self._set_dz_active(True)
                    return

    def _dz_drop(self, event) -> None:
        self._set_dz_active(False)
        if event.mimeData().hasUrls():
            paths = [
                Path(url.toLocalFile())
                for url in event.mimeData().urls()
                if url.toLocalFile().lower().endswith((".xlsx", ".xls"))
                and Path(url.toLocalFile()).exists()
            ]
            if paths:
                self._add_files(paths)
                event.acceptProposedAction()

    # ------------------------------------------------------------------
    # File management
    # ------------------------------------------------------------------

    def _browse_files(self) -> None:
        last = str(self._files[-1].parent) if self._files else ""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Monthly Merged Files", last,
            "Excel Files (*.xlsx *.xls);;All Files (*.*)",
        )
        if paths:
            self._add_files([Path(p) for p in paths])

    def _add_files(self, new_paths: List[Path]) -> None:
        existing = {p.resolve() for p in self._files}
        added = 0
        for p in new_paths:
            rp = p.resolve()
            if rp not in existing and p.exists():
                self._files.append(p)
                existing.add(rp)
                added += 1
        if added:
            self._files.sort(key=lambda f: f.name)
            self._update_dz_summary()
            self._clear_btn.setEnabled(True)
            self._trigger_validation()

    def _clear_files(self) -> None:
        self._files.clear()
        self._table.setRowCount(0)
        self._month_lbl.setText("")
        self._output_edit.clear()
        self._merge_btn.setEnabled(False)
        self._merge_btn.setText("🔀  Merge Monthly Files")
        self._clear_btn.setEnabled(False)
        self._dz_title.setText("Drop Monthly Merged Files Here")
        self._summary_lbl.setText("No files loaded")
        self.log("WARN", "Files cleared")
        self.status_bar.showMessage("No files loaded")

    def _update_dz_summary(self) -> None:
        n = len(self._files)
        self._dz_title.setText(f"✅  {n} file{'s' if n != 1 else ''} loaded")
        preview = "  •  ".join(f.name for f in self._files[:3])
        if n > 3:
            preview += f"  … +{n - 3} more"
        self._summary_lbl.setText(preview)

    # ------------------------------------------------------------------
    # Async validation
    # ------------------------------------------------------------------

    def _trigger_validation(self) -> None:
        if self._val_worker and self._val_worker.isRunning():
            self._val_worker.quit()
            self._val_worker.wait(300)

        n = len(self._files)
        self.log(f"Scanning {n} file{'s' if n != 1 else ''}…")
        self.status_bar.showMessage(f"Scanning {n} file(s)…")
        self._merge_btn.setEnabled(False)
        self._overlay.start(f"Scanning {n} file{'s' if n != 1 else ''}…")

        self._val_worker = ValidationWorker(self.service, list(self._files), parent=self)
        self._val_worker.finished.connect(self._on_validation_done)
        self._val_worker.error.connect(self._on_validation_error)
        self._val_worker.start()

    def _on_validation_done(self, result: ValidationResult) -> None:
        self._overlay.stop()
        self._populate_table(result)
        self._update_month_label(result)
        self._auto_suggest_output(result)

        if result.is_valid:
            n = len(result.daily_files)
            self._merge_btn.setEnabled(True)
            self._merge_btn.setText(f"🔀  Merge {n} Monthly File{'s' if n != 1 else ''}")
            self.log(f"Validation OK — {n} file(s) loaded, ordered oldest→newest (latest wins)")
            if result.warnings:
                for w in result.warnings:
                    self.log("WARN", w)
            self.status_bar.showMessage(f"✅  {n} file(s) ready — choose output path and merge")
        else:
            self.log("ERROR", f"Validation failed: {result.error}")
            self.status_bar.showMessage(f"❌  {result.error}")

    def _on_validation_error(self, err: str) -> None:
        self._overlay.stop()
        self.log("ERROR", f"Validation error: {err}")
        self.status_bar.showMessage(f"❌  {err}")

    def _populate_table(self, result: ValidationResult) -> None:
        self._table.setRowCount(0)
        total = len(result.daily_files)
        for idx, df in enumerate(result.daily_files):
            r = self._table.rowCount()
            self._table.insertRow(r)

            # Order column — show which file is processed first/last (latest wins)
            order_text = f"{idx + 1}/{total}"
            if idx == total - 1:
                order_text += " (wins)"
            self._table.setItem(r, 0, _ro_item(order_text))

            name = df.source_zip.name if df.source_zip else df.path.name
            self._table.setItem(r, 1, _ro_item("📄 " + name))

            # Month range label
            monthly = _parse_month_label_from_filename(name)
            if monthly:
                _, _, label = monthly
                # Resolve month names
                parts = label.replace("→", "to").split()
                if len(parts) >= 3:
                    m1 = parts[0].split("-")[0].zfill(2)
                    m2 = parts[2].split("-")[0].zfill(2)
                    label = f"{_MONTH_NAMES.get(m1, m1)} → {_MONTH_NAMES.get(m2, m2)}"
            else:
                label = _MONTH_NAMES.get(df.month, df.month)
            self._table.setItem(r, 2, _ro_item(label))

            # Sheets found
            parts2 = []
            if df.handler_sheets:
                parts2.append(f"{len(df.handler_sheets)} case sheet{'s' if len(df.handler_sheets) != 1 else ''}")
            if df.has_chat:
                parts2.append("Chat ✅")
            if df.has_companies:
                parts2.append("Companies ✅")
            self._table.setItem(r, 3, _ro_item("  ·  ".join(parts2) or "?"))

            # Status
            ok = bool(df.handler_sheets) and df.has_chat and df.has_companies
            self._table.setItem(r, 4, _ro_item("✅  OK" if ok else "⚠  Incomplete"))

    def _update_month_label(self, result: ValidationResult) -> None:
        if not result.daily_files:
            self._month_lbl.setText("")
            return
        months = sorted(result.months_found.keys())
        parts = [
            f"{_MONTH_NAMES.get(m, m)}: {result.months_found[m]} file{'s' if result.months_found[m] != 1 else ''}"
            for m in months
        ]
        # Also show "latest overwrites earlier" tip when multiple months present
        label_str = "📅  " + "  |  ".join(parts)
        if len(months) > 1:
            label_str += "  •  Latest month overwrites earlier"
        self._month_lbl.setText(label_str)

    def _auto_suggest_output(self, result: ValidationResult) -> None:
        """Suggest an output name using the outer date range across all monthly files."""
        if not result.daily_files:
            return
        first = result.daily_files[0]
        last = result.daily_files[-1]
        folder = (first.source_zip or first.path).parent
        
        # Extract start date from first file and end date from last file
        # For monthly files like "Merged Cases 01-05 to 01-30.xlsx":
        #   - first file: use start date "01-05"
        #   - last file: extract end date "01-30" if available
        start_date = first.date_str
        
        # Try to extract end date from last file's name
        last_name = (last.source_zip or last.path).name
        monthly = _parse_month_label_from_filename(last_name)
        if monthly:
            # monthly = (month, start_date, label_str like "01-05 → 01-30")
            label = monthly[2]
            parts = label.replace("→", "to").split()
            if len(parts) >= 3:
                end_date = parts[2]  # "01-30"
            else:
                end_date = last.date_str
        else:
            end_date = last.date_str
        
        suggestion = folder / f"Merged All Months {start_date} to {end_date}.xlsx"
        self._output_edit.setText(str(suggestion))

    # ------------------------------------------------------------------
    # Output browse
    # ------------------------------------------------------------------

    def _browse_output(self) -> None:
        current = self._output_edit.text().strip()
        start = str(Path(current).parent) if current else str(Path.home())
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Merged Output As", start,
            "Excel Files (*.xlsx);;All Files (*.*)",
        )
        if path:
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self._output_edit.setText(path)

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    def _start_merge(self) -> None:
        output = self._output_edit.text().strip()
        if not output:
            QMessageBox.warning(self, "No Output Path", "Please choose an output file path.")
            return
        if not self._files:
            QMessageBox.warning(self, "No Files", "No monthly files are loaded.")
            return

        config = MergeConfig(
            file_paths=list(self._files),
            output_path=Path(output),
            accept_zip=False,
            relaxed_filename=True,
        )
        self._last_output = output
        self.log("BANNER", f"── Monthly merge started ── {len(self._files)} file(s) → {Path(output).name}")

        progress = ProgressDialog(
            self, f"Merging {len(self._files)} monthly workbooks…", "Monthly Merge"
        )
        progress.show()

        self.worker = MonthlyMergeWorker(self.service, config, parent=self)
        self.worker.progress.connect(
            lambda pct, msg: (progress.set_progress(pct), progress.set_message(msg))
        )
        self.worker.log_entry.connect(self.log)
        self.worker.finished.connect(
            lambda ok, msg, stats: self._on_merge_done(ok, msg, stats, progress)
        )
        self._merge_btn.setEnabled(False)
        self._spinner_ticks = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick_spinner)
        self._spin_timer.start(200)
        self.worker.start()

    def _tick_spinner(self) -> None:
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self._spinner_ticks += 1
        self.status_bar.showMessage(
            f"{frames[self._spinner_ticks % len(frames)]}  Merging in progress…"
        )

    def _on_merge_done(
        self, success: bool, message: str, stats: dict, progress: ProgressDialog
    ) -> None:
        progress.close()
        self._merge_btn.setEnabled(True)
        if hasattr(self, "_spin_timer"):
            self._spin_timer.stop()

        if success:
            output = stats.get("output_path", self._last_output)
            self.log("BANNER", "── Monthly merge complete ──")
            self.log("DETAIL", f"   Files processed : {stats.get('files_processed', '?')}")
            self.log("DETAIL", f"   All Cases rows  : {stats.get('all_cases', '?')}")
            self.log("DETAIL", f"   Chat Agent rows : {stats.get('chat_cases', '?')}")
            self.log("DETAIL", f"   Companies rows  : {stats.get('companies', '?')}")
            if stats.get("skipped", 0):
                self.log("WARN", f"   Skipped (empty key): {stats.get('skipped')}")
            self.log("INFO", f"✔ Output → {output}")
            detail = (
                f"{message}\n\n"
                f"All Cases rows    : {stats.get('all_cases', '?')}\n"
                f"Chat Agent rows   : {stats.get('chat_cases', '?')}\n"
                f"Companies rows    : {stats.get('companies', '?')}\n\n"
                f"Deduplication: latest month overwrites earlier.\n\n"
                f"Output: {output}"
            )
            reply = QMessageBox.information(
                self, "Monthly Merge Complete", detail,
                QMessageBox.Open | QMessageBox.Ok, QMessageBox.Ok,
            )
            if reply == QMessageBox.Open and output:
                _open_explorer(output)
            self.status_bar.showMessage("✅  Monthly merge complete — " + message)
        else:
            self.log("ERROR", f"Merge failed: {message}")
            QMessageBox.critical(self, "Monthly Merge Error", message)
            self.status_bar.showMessage("❌  Monthly merge failed")

    # ------------------------------------------------------------------
    # Log
    # ------------------------------------------------------------------

    def log(self, level_or_msg: str, message: str = "") -> None:
        if message:
            level, msg = level_or_msg.upper(), message
        else:
            level, msg = "INFO", level_or_msg

        ts    = datetime.now().strftime("%H:%M:%S")
        color = _LOG_COLORS.get(level)
        prefixes = {"WARN": "⚠ ", "ERROR": "✖ ", "BANNER": "", "DETAIL": "  "}
        prefix   = prefixes.get(level, "")
        ts_html  = f'<span style="color:#888888;">[{ts}]</span>'

        if color:
            bold = "<b>" if level == "BANNER" else ""
            endb = "</b>" if level == "BANNER" else ""
            line = (
                f'{ts_html} <span style="color:{color};">'
                f'{bold}{prefix}{_esc(msg)}{endb}</span>'
            )
        else:
            info_c = getattr(self, "_log_default_text_color", "#222222")
            line = f'{ts_html} <span style="color:{info_c};">{_esc(msg)}</span>'

        self._log_view.append(line)
        sb = self._log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _toggle_log(self) -> None:
        vis = self._log_view.isVisible()
        self._log_view.setVisible(not vis)
        self._log_toggle_btn.setText("▲ Hide" if not vis else "▼ Show")

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        colors   = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        bg       = colors["background"]
        border   = colors["border"]
        text     = colors["text_primary"]
        text_s   = colors["text_secondary"]
        surface  = colors["surface"]
        primary  = colors["primary"]
        hover_bg = colors["surface_hover"]

        self._log_default_text_color = text
        self._log_view.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 4px;
                padding: 4px;
            }}
        """)
        header_w = self._log_panel.layout().itemAt(0).widget()
        if header_w:
            header_w.setStyleSheet(f"""
                QFrame {{ background-color: {surface}; border: 1px solid {border};
                          border-bottom: none; border-radius: 4px 4px 0 0; }}
                QLabel {{ color: {text}; }}
                QPushButton {{ background-color: {surface}; color: {text_s};
                               border: 1px solid {border}; border-radius: 3px; padding: 2px 6px; }}
                QPushButton:hover {{ background-color: {hover_bg}; color: {text}; }}
            """)

        self._drop_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {surface};
                border: 2px dashed {border};
                border-radius: {BorderRadius.LG}px;
            }}
            QFrame:hover {{
                border-color: {primary};
                background-color: {hover_bg};
            }}
        """)
        self._dz_title.setStyleSheet(f"QLabel {{ color: {text}; border: none; }}")
        self._dz_sub.setStyleSheet(f"QLabel {{ color: {text_s}; border: none; }}")
        self._summary_lbl.setStyleSheet(f"QLabel {{ color: {text_s}; }}")

        self._table.setStyleSheet(f"""
            QTableWidget {{ background-color: {bg}; alternate-background-color: {surface};
                            border: 1px solid {border}; border-radius: {BorderRadius.MD}px;
                            color: {text}; gridline-color: {border}; }}
            QHeaderView::section {{ background-color: {surface}; color: {text}; border: none;
                                     border-bottom: 1px solid {border}; padding: 4px 8px;
                                     font-weight: bold; }}
            QTableWidget::item {{ padding: 4px 8px; }}
            QTableWidget::item:selected {{ background-color: {primary}; color: white; }}
        """)
        self._output_edit.setStyleSheet(f"""
            QLineEdit {{ background-color: {bg}; border: 1px solid {border};
                         border-radius: {BorderRadius.MD}px; padding: 4px 8px; color: {text}; }}
            QLineEdit:focus {{ border-color: {primary}; }}
        """)
        self._month_lbl.setStyleSheet(f"QLabel {{ color: {text}; font-weight: bold; }}")

    def _set_dz_active(self, active: bool) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        if active:
            self._drop_frame.setStyleSheet(f"""
                QFrame {{ background-color: {colors['info_bg']};
                          border: 2px solid {colors['primary']};
                          border-radius: {BorderRadius.LG}px; }}
            """)
        else:
            self._apply_styles()

    def _on_theme_changed(self, mode: str) -> None:
        self._theme_mode = mode
        self._apply_styles()

    # ------------------------------------------------------------------
    # Shortcuts / signals / close
    # ------------------------------------------------------------------

    def _setup_shortcuts(self) -> None:
        self.shortcut_manager = ShortcutManager(self)
        defs = [
            ("monthly_open",  "Ctrl+O", "Browse files",        ShortcutCategory.FILE,          self._browse_files),
            ("monthly_merge", "Ctrl+M", "Start merge",         ShortcutCategory.TOOL_SPECIFIC, self._start_merge),
            ("monthly_close", "Ctrl+W", "Close window",        ShortcutCategory.GLOBAL,        self.close),
            ("monthly_help",  "F1",     "About",               ShortcutCategory.GLOBAL,        self._show_about),
            ("monthly_log",   "Ctrl+L", "Toggle activity log", ShortcutCategory.GLOBAL,        self._toggle_log),
        ]
        for key, seq, desc, cat, action in defs:
            self.shortcut_manager.register_shortcut(
                key,
                ShortcutDefinition(
                    key_sequence=seq, description=desc, category=cat, action=action
                ),
            )

    def _connect_signals(self) -> None:
        self.settings_bus.theme_changed.connect(self._on_theme_changed)

    def _show_about(self) -> None:
        QMessageBox.about(
            self, "About Monthly Case Merger",
            "Monthly Case Merger v1.0\n\n"
            "Merges monthly output workbooks produced by the Daily Case Merger.\n"
            "Latest month always wins (deduplication by case number).\n\n"
            "Keyboard shortcuts:\n"
            "  Ctrl+O  Browse files\n"
            "  Ctrl+M  Start merge\n"
            "  Ctrl+L  Toggle log\n"
            "  Ctrl+W  Close",
        )

    def closeEvent(self, event) -> None:
        if self._val_worker and self._val_worker.isRunning():
            self._val_worker.quit()
            self._val_worker.wait(500)
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Merge in Progress",
                "A merge is still running. Close anyway?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.worker.terminate()
            self.worker.wait(2000)
        event.accept()

    def apply_typography(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _open_explorer(path: str) -> None:
    """Open the output file's parent folder in the OS file explorer."""
    try:
        folder = str(Path(path).parent)
        # QDesktopServices handles all platforms cleanly without subprocess
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))
    except Exception:
        pass


__all__ = ["MonthlyMergerWindow"]

# Made with Bob
