"""
Daily File List Widget
======================

Drop-zone panel for the Daily Case Merger.
Accepts .xlsx files and (when the ZIP toggle is enabled) .zip archives.

Signals:
    files_changed(list):   Emitted with the current list of Path objects
                           whenever the file list changes.
    clear_requested():     Emitted when the user clicks "Clear All" so the
                           window can also reset the output path.

The table that previously lived here has been removed — all per-file detail
is shown in the Validation Summary table on the right-side panel, which is
populated by the service after every file change.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QFrame, QSizePolicy,
    QCheckBox,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem
from ui.components_v2.buttons import PrimaryButton, SecondaryButton


class DailyFileListWidget(QWidget):
    """
    Drop-zone + file-count summary for loading daily workbooks.

    Signals:
        files_changed(list[Path]):  Current file list after any add/remove.
        clear_requested():          Fired on "Clear All" so the window resets
                                    the output path.
    """

    files_changed   = pyqtSignal(list)
    clear_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme_mode = "light"
        self._typography = TypographySystem()
        self._files: List[Path] = []
        self._last_browse_dir: str = ""

        self._setup_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Spacing.MD)

        # ── Section title ─────────────────────────────────────────────
        title = QLabel("📅  Load Daily Workbooks", self)
        title.setFont(self._typography.create_font("h3"))
        root.addWidget(title)

        # ── ZIP toggle ────────────────────────────────────────────────
        zip_row = QHBoxLayout()
        zip_row.setSpacing(Spacing.SM)
        self._zip_toggle = QCheckBox(
            "📦  Accept ZIP files (containing a daily .xlsx workbook)", self
        )
        self._zip_toggle.setChecked(True)
        self._zip_toggle.setFont(self._typography.create_font("body_sm"))
        self._zip_toggle.setToolTip(
            "When enabled, .zip archives that contain a single\n"
            "'Active Cases PA MM-DD.xlsx' workbook are accepted\n"
            "and processed with the same rules as direct .xlsx files."
        )
        self._zip_toggle.stateChanged.connect(self._on_zip_toggle_changed)
        zip_row.addWidget(self._zip_toggle)
        zip_row.addStretch()
        root.addLayout(zip_row)

        # ── Drop zone ─────────────────────────────────────────────────
        self._drop_zone = QFrame(self)
        self._drop_zone.setAcceptDrops(True)
        self._drop_zone.setMinimumHeight(200)
        self._drop_zone.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._drop_zone.dragEnterEvent = self._on_drag_enter
        self._drop_zone.dragLeaveEvent = self._on_drag_leave
        self._drop_zone.dropEvent      = self._on_drop

        dz_layout = QVBoxLayout(self._drop_zone)
        dz_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        dz_layout.setSpacing(Spacing.MD)
        dz_layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel("📂", self._drop_zone)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFont(QFont("Segoe UI Emoji", 36))
        dz_layout.addWidget(icon_lbl)

        self._dz_title = QLabel(
            "Drag & Drop Daily Files Here", self._drop_zone
        )
        self._dz_title.setAlignment(Qt.AlignCenter)
        self._dz_title.setFont(self._typography.create_font("h3"))
        dz_layout.addWidget(self._dz_title)

        self._dz_sub = QLabel(
            "Accepts .xlsx files (or .zip when toggle is on)\n"
            "Up to 30 daily Active Cases PA MM-DD workbooks",
            self._drop_zone,
        )
        self._dz_sub.setAlignment(Qt.AlignCenter)
        self._dz_sub.setFont(self._typography.create_font("body_sm"))
        self._dz_sub.setWordWrap(True)
        dz_layout.addWidget(self._dz_sub)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(Spacing.SM)

        self._browse_btn = PrimaryButton("Browse Files…", self._drop_zone)
        self._browse_btn.setMinimumHeight(44)
        self._browse_btn.setMinimumWidth(130)
        self._browse_btn.clicked.connect(self.browse_files)
        btn_row.addWidget(self._browse_btn)

        self._clear_btn = SecondaryButton("Clear All", self._drop_zone)
        self._clear_btn.setMinimumHeight(44)
        self._clear_btn.setMinimumWidth(100)
        self._clear_btn.clicked.connect(self.clear_files)
        self._clear_btn.setEnabled(False)   # disabled until files are loaded
        btn_row.addWidget(self._clear_btn)

        dz_layout.addLayout(btn_row)
        root.addWidget(self._drop_zone, stretch=1)

        # ── File count / summary chip ──────────────────────────────────
        self._summary_label = QLabel("No files loaded — drop files above to begin", self)
        self._summary_label.setFont(self._typography.create_font("body_sm"))
        self._summary_label.setAlignment(Qt.AlignCenter)
        self._summary_label.setWordWrap(True)
        root.addWidget(self._summary_label)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def browse_files(self) -> None:
        """Open a multi-select file dialog."""
        accept_zip = self.zip_enabled()
        if accept_zip:
            file_filter = (
                "Daily Files (*.xlsx *.xls *.zip);;"
                "Excel Files (*.xlsx *.xls);;"
                "ZIP Archives (*.zip);;"
                "All Files (*.*)"
            )
        else:
            file_filter = "Excel Files (*.xlsx *.xls);;All Files (*.*)"

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Daily Active Cases Files",
            self._last_browse_dir,
            file_filter,
        )
        if paths:
            self._last_browse_dir = str(Path(paths[0]).parent)
            self._add_files([Path(p) for p in paths])

    def clear_files(self) -> None:
        """Remove all loaded files and notify the window to clear the output path."""
        self._files.clear()
        self._update_summary()
        self._clear_btn.setEnabled(False)
        self.files_changed.emit([])
        self.clear_requested.emit()

    def get_files(self) -> List[Path]:
        """Return current file list (sorted chronologically by name)."""
        return list(self._files)

    def get_last_dir(self) -> str:
        """Return the directory of the most recently added file."""
        return self._last_browse_dir

    def zip_enabled(self) -> bool:
        """Return True when the ZIP toggle is checked."""
        return self._zip_toggle.isChecked()

    def set_theme_mode(self, mode: str) -> None:
        self._theme_mode = mode
        self._apply_styles()

    # ------------------------------------------------------------------
    # Drag-drop
    # ------------------------------------------------------------------

    def _on_drag_enter(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if self._is_accepted(url.toLocalFile()):
                    event.acceptProposedAction()
                    self._apply_drop_active_style()
                    return

    def _on_drag_leave(self, event) -> None:
        self._apply_styles()

    def _on_drop(self, event: QDropEvent) -> None:
        self._apply_styles()
        if event.mimeData().hasUrls():
            new_files = [
                Path(url.toLocalFile())
                for url in event.mimeData().urls()
                if self._is_accepted(url.toLocalFile())
            ]
            if new_files:
                self._add_files(new_files)
                event.acceptProposedAction()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_zip_toggle_changed(self) -> None:
        if self.zip_enabled():
            self._dz_sub.setText(
                "Accepts .xlsx and .zip files\n"
                "Up to 30 daily Active Cases PA MM-DD workbooks"
            )
        else:
            self._dz_sub.setText(
                "Accepts .xlsx files only\n"
                "Up to 30 daily Active Cases PA MM-DD workbooks"
            )

    def _is_accepted(self, file_path: str) -> bool:
        p = Path(file_path)
        if not p.exists():
            return False
        suffix = p.suffix.lower()
        if suffix in (".xlsx", ".xls"):
            return True
        if suffix == ".zip" and self.zip_enabled():
            return True
        return False

    def _add_files(self, new_paths: List[Path]) -> None:
        """Add files, deduplicating by resolved path. Cap at 30."""
        existing = {p.resolve() for p in self._files}
        added = 0
        for p in new_paths:
            if len(self._files) >= 30:
                break
            rp = p.resolve()
            suffix = p.suffix.lower()
            is_valid = (
                suffix in (".xlsx", ".xls")
                or (suffix == ".zip" and self.zip_enabled())
            )
            if rp not in existing and p.exists() and is_valid:
                self._files.append(p)
                existing.add(rp)
                added += 1
                # Track last known directory from actual files
                self._last_browse_dir = str(p.parent)

        if added:
            self._files.sort(key=lambda f: f.name)
            self._update_summary()
            self._clear_btn.setEnabled(True)
            self.files_changed.emit(list(self._files))

    def _update_summary(self) -> None:
        """Refresh the summary chip below the drop zone."""
        n = len(self._files)
        if n == 0:
            self._summary_label.setText("No files loaded — drop files above to begin")
            self._dz_title.setText("Drag & Drop Daily Files Here")
            return

        from DailyMerger.daily_merger_service import _parse_date_from_filename
        zip_count  = sum(1 for p in self._files if p.suffix.lower() == ".zip")
        xlsx_count = n - zip_count
        dates = []
        for p in self._files:
            parsed = _parse_date_from_filename(p.name)
            if parsed:
                dates.append(parsed[1])

        date_range = f"{min(dates)} → {max(dates)}" if dates else "unknown range"

        type_parts = []
        if xlsx_count:
            type_parts.append(f"{xlsx_count} Excel")
        if zip_count:
            type_parts.append(f"{zip_count} ZIP")

        self._dz_title.setText(f"✅  {n} file{'s' if n != 1 else ''} loaded")
        self._summary_label.setText(
            f"{', '.join(type_parts)}  •  Date range: {date_range}"
        )

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        colors   = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        surface  = colors["surface"]
        border   = colors["border"]
        primary  = colors["primary"]
        hover_bg = colors["surface_hover"]
        text     = colors["text_primary"]
        text_sec = colors["text_secondary"]

        self._drop_zone.setStyleSheet(f"""
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
        self._dz_sub.setStyleSheet(f"QLabel {{ color: {text_sec}; border: none; }}")
        self._summary_label.setStyleSheet(f"QLabel {{ color: {text_sec}; }}")

    def _apply_drop_active_style(self) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        self._drop_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['info_bg']};
                border: 2px solid {colors['primary']};
                border-radius: {BorderRadius.LG}px;
            }}
        """)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_excel(path: str) -> bool:
    p = Path(path)
    return p.exists() and p.suffix.lower() in (".xlsx", ".xls")


__all__ = ["DailyFileListWidget"]

# Made with Bob
