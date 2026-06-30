"""
Daily Summary Widget
====================

Displays the ValidationResult after files are loaded:
  - Per-day sheet-count table with warnings
  - Output file path picker (with recent-folder memory)
  - Month confirmation label
  - "Merge N Files" primary action button

Signals:
    merge_requested(dict):  Emitted with {'output_path': str} when the user
                            clicks the Merge button after validation passes.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QFileDialog, QLineEdit, QSizePolicy,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem
from ui.components_v2.buttons import PrimaryButton, SecondaryButton

from DailyMerger.daily_merger_service import ValidationResult
from utils.recent_daily_merger_files import get_recent_daily_merger_manager


class DailySummaryWidget(QWidget):
    """
    Validation summary + output path picker + merge trigger.

    Signals:
        merge_requested(dict):  {'output_path': str}
    """

    merge_requested = pyqtSignal(dict)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme_mode = "light"
        self._typography = TypographySystem()
        self._validation: Optional[ValidationResult] = None
        self._recent_manager = get_recent_daily_merger_manager()

        self._setup_ui()
        self._apply_styles()
        self._set_idle_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Spacing.MD)

        # ── Section title ─────────────────────────────────────────────
        title = QLabel("📋  Validation Summary", self)
        title.setFont(self._typography.create_font("h3"))
        root.addWidget(title)

        # ── Month confirmation label ───────────────────────────────────
        self._month_label = QLabel("", self)
        self._month_label.setFont(self._typography.create_font("body"))
        self._month_label.setWordWrap(True)
        root.addWidget(self._month_label)

        # ── Skipped-month alert (danger, always shown prominently) ────
        self._skip_frame = QFrame(self)
        self._skip_frame.setObjectName("skipFrame")
        skip_layout = QVBoxLayout(self._skip_frame)
        skip_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        self._skip_label = QLabel("", self._skip_frame)
        self._skip_label.setFont(self._typography.create_font("body_sm"))
        self._skip_label.setWordWrap(True)
        skip_layout.addWidget(self._skip_label)
        self._skip_frame.setVisible(False)
        root.addWidget(self._skip_frame)

        # ── Warning banner (missing sheets) ──────────────────────────
        self._warning_frame = QFrame(self)
        self._warning_frame.setObjectName("warningFrame")
        warn_layout = QVBoxLayout(self._warning_frame)
        warn_layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        self._warning_label = QLabel("", self._warning_frame)
        self._warning_label.setFont(self._typography.create_font("body_sm"))
        self._warning_label.setWordWrap(True)
        warn_layout.addWidget(self._warning_label)
        self._warning_frame.setVisible(False)
        root.addWidget(self._warning_frame)

        # ── Per-day table ─────────────────────────────────────────────
        # 7 columns: Filename · Source · Date · Handlers · Chat · Companies · Status
        self._table = QTableWidget(0, 7, self)
        self._table.setHorizontalHeaderLabels([
            "Filename", "Source", "Date",
            "Handlers", "Chat", "Companies", "Status",
        ])
        hdr = self._table.horizontalHeader()
        # Filename stretches to fill remaining space; the rest size to fit
        # their (now-shortened) header text via ResizeToContents. The previous
        # full-length headers ("Handler Sheets", "Chat Agent", ...) summed to
        # more width than the panel had, forcing a horizontal scrollbar that
        # clipped every column; shorter labels remove that overflow.
        hdr.setSectionResizeMode(0, QHeaderView.Stretch)           # Filename
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Source
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Date
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Handlers
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Chat
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Companies
        hdr.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Status
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(220)
        self._table.setFont(self._typography.create_font("body_sm"))
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        root.addWidget(self._table)

        # ── Handler names found ───────────────────────────────────────
        self._handlers_label = QLabel("", self)
        self._handlers_label.setFont(self._typography.create_font("body_sm"))
        self._handlers_label.setWordWrap(True)
        root.addWidget(self._handlers_label)

        # ── Output path picker ────────────────────────────────────────
        out_label = QLabel("Output File:", self)
        out_label.setFont(self._typography.create_font("label"))
        root.addWidget(out_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(Spacing.SM)
        self._output_edit = QLineEdit(self)
        self._output_edit.setMinimumHeight(44)
        self._output_edit.setPlaceholderText("Choose output file path…")
        self._output_edit.setFont(self._typography.create_font("body_sm"))
        path_row.addWidget(self._output_edit)

        self._browse_out_btn = SecondaryButton("Browse…", self)
        self._browse_out_btn.setMinimumHeight(44)
        self._browse_out_btn.clicked.connect(self._browse_output)
        path_row.addWidget(self._browse_out_btn)
        root.addLayout(path_row)

        # ── Merge button ──────────────────────────────────────────────
        self._merge_btn = PrimaryButton("🔀  Merge Files", self)
        self._merge_btn.setMinimumHeight(48)
        self._merge_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._merge_btn.setEnabled(False)
        self._merge_btn.clicked.connect(self._on_merge_clicked)
        root.addWidget(self._merge_btn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_validation(self, result: ValidationResult) -> None:
        """Populate the widget from a ValidationResult."""
        self._validation = result

        if not result.is_valid:
            self._month_label.setText(f"❌  {result.error}")
            self._month_label.setStyleSheet(
                f"color: {_c(self._theme_mode, 'danger')}; font-weight: bold;"
            )
            self._table.setRowCount(0)
            self._skip_frame.setVisible(False)
            self._warning_frame.setVisible(False)
            self._handlers_label.setText("")
            self._merge_btn.setEnabled(False)
            return

        # Month confirmation
        month_parts = []
        month_names = {
            "01": "January", "02": "February", "03": "March", "04": "April",
            "05": "May",      "06": "June",     "07": "July",  "08": "August",
            "09": "September","10": "October",  "11": "November","12": "December",
        }
        for m, count in sorted(result.months_found.items()):
            month_parts.append(f"{month_names.get(m, m)}: {count} daily file{'s' if count != 1 else ''}")
        self._month_label.setText("📅  " + " | ".join(month_parts))
        self._month_label.setStyleSheet(
            f"color: {_c(self._theme_mode, 'success')}; font-weight: bold;"
        )

        # Handlers
        if result.handler_names:
            self._handlers_label.setText(
                "👥  Handlers detected: " + ", ".join(result.handler_names)
            )
        else:
            self._handlers_label.setText("⚠  No handler sheets detected")

        # Skipped-month alert (shown above the warnings banner)
        skipped = getattr(result, "skipped_months", [])
        if skipped:
            month_names = {
                "01": "January", "02": "February", "03": "March", "04": "April",
                "05": "May",      "06": "June",     "07": "July",  "08": "August",
                "09": "September","10": "October",  "11": "November","12": "December",
            }
            skipped_names = [month_names.get(m, m) for m in skipped]
            self._skip_label.setText(
                "🚨  Skipped month(s) detected — no files loaded for: "
                + ", ".join(skipped_names)
                + "\n\nThe merge will still run with the months you have loaded. "
                "If this is intentional you can proceed, otherwise add the missing "
                "monthly files before merging."
            )
            self._skip_frame.setVisible(True)
        else:
            self._skip_frame.setVisible(False)

        # Warnings banner (missing sheets within a day)
        if result.warnings:
            self._warning_label.setText(
                "⚠  Warnings:\n" + "\n".join(f"  • {w}" for w in result.warnings)
            )
            self._warning_frame.setVisible(True)
        else:
            self._warning_frame.setVisible(False)

        # Per-day table  (7 cols: Filename, Source, Date, Handlers, Chat, Companies, Status)
        self._table.setRowCount(0)
        for df in result.daily_files:
            r = self._table.rowCount()
            self._table.insertRow(r)

            # col 0 — Filename (source ZIP name if applicable, else xlsx name)
            display_name = (
                ("📦 " + df.source_zip.name) if df.source_zip
                else ("📄 " + df.path.name)
            )
            self._table.setItem(r, 0, _ro_item(display_name))

            # col 1 — Source type
            source_str = "📦 ZIP" if df.source_zip else "📄 Excel"
            self._table.setItem(r, 1, _ro_item(source_str))

            # col 2 — Date
            self._table.setItem(r, 2, _ro_item(df.date_str))

            # col 3 — Handler sheets
            h_count = len(df.handler_sheets)
            handler_label = (
                f"{h_count} sheet{'s' if h_count != 1 else ''}"
                + (f"  ({', '.join(df.handler_sheets)})" if df.handler_sheets else "")
            )
            self._table.setItem(r, 3, _ro_item(handler_label))

            # col 4 — Chat Agent
            self._table.setItem(r, 4, _ro_item("✅" if df.has_chat else "⚠  Missing"))

            # col 5 — Companies
            self._table.setItem(r, 5, _ro_item("✅" if df.has_companies else "⚠  Missing"))

            # col 6 — Status
            missing = (not df.has_chat) or (not df.has_companies)
            status_text = "⚠  Incomplete" if missing else "✅  OK"
            self._table.setItem(r, 6, _ro_item(status_text))

        # Auto-detect output path: always update to match the current file set
        # so it stays correct when more files are added or the date range changes.
        if result.daily_files:
            days = [df.date_str for df in result.daily_files]
            # Prefer the folder of the first loaded file
            first = result.daily_files[0]
            folder = (first.source_zip or first.path).parent
            suggestion = folder / f"Merged Cases {min(days)} to {max(days)}.xlsx"
            self._output_edit.setText(str(suggestion))

        self._merge_btn.setEnabled(True)
        n = len(result.daily_files)
        self._merge_btn.setText(f"🔀  Merge {n} File{'s' if n != 1 else ''}")
        self._apply_styles()

    def show_idle(self) -> None:
        """Reset to idle (no validation yet)."""
        self._set_idle_state()

    def set_theme_mode(self, mode: str) -> None:
        self._theme_mode = mode
        self._apply_styles()

    def clear_output_path(self) -> None:
        """Clear the output path field (called when files are cleared)."""
        self._output_edit.clear()

    def get_output_path(self) -> str:
        return self._output_edit.text().strip()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _set_idle_state(self) -> None:
        self._month_label.setText("Load files to begin…")
        self._month_label.setStyleSheet(f"color: {_c(self._theme_mode, 'text_secondary')};")
        self._table.setRowCount(0)
        self._skip_frame.setVisible(False)
        self._warning_frame.setVisible(False)
        self._handlers_label.setText("")
        self._merge_btn.setEnabled(False)
        self._merge_btn.setText("🔀  Merge Files")

    def _browse_output(self) -> None:
        current = self._output_edit.text().strip()
        # Prefer current path's parent → recent folder → home
        if current:
            start_dir = str(Path(current).parent)
        else:
            recent = self._recent_manager.get_recent_folder_paths(limit=1)
            start_dir = recent[0] if recent else str(Path.home())

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Merged Output As",
            start_dir,
            "Excel Files (*.xlsx);;All Files (*.*)",
        )
        if path:
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self._output_edit.setText(path)
            # Persist the chosen folder
            self._recent_manager.add_output_folder(str(Path(path).parent))

    def _on_merge_clicked(self) -> None:
        output = self._output_edit.text().strip()
        if not output:
            self._output_edit.setPlaceholderText("⚠  Please choose an output file path first")
            return
        self.merge_requested.emit({"output_path": output})

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        surface  = colors["surface"]
        border   = colors["border"]
        primary  = colors["primary"]
        text     = colors["text_primary"]
        text_sec = colors["text_secondary"]
        warn_bg  = colors.get("warning_bg", "#fdf3c8")
        danger   = colors.get("danger", "#da1e28")

        # Skipped-month danger frame (selectors scoped to #skipFrame/#warningFrame
        # — QLabel is a QFrame subclass, so an unscoped "QFrame {...}" selector
        # would also paint a border/background on the labels nested inside)
        self._skip_frame.setStyleSheet(f"""
            QFrame#skipFrame {{
                background-color: {colors.get('danger_bg', '#fff1f1')};
                border: 2px solid {danger};
                border-radius: {BorderRadius.MD}px;
            }}
        """)
        self._skip_label.setStyleSheet(
            f"color: {danger}; font-weight: bold;"
        )

        self._warning_frame.setStyleSheet(f"""
            QFrame#warningFrame {{
                background-color: {warn_bg};
                border: 1px solid {colors.get('warning', '#f1c21b')};
                border-radius: {BorderRadius.MD}px;
            }}
        """)
        self._warning_label.setStyleSheet(
            f"color: {colors.get('warning_text', '#533f04')};"
        )
        self._output_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {colors['background']};
                border: 1px solid {border};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.MD}px;
                color: {text};
            }}
            QLineEdit:focus {{ border-color: {primary}; }}
        """)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {colors['background']};
                alternate-background-color: {surface};
                border: 1px solid {border};
                border-radius: {BorderRadius.MD}px;
                color: {text};
                gridline-color: {border};
            }}
            QHeaderView::section {{
                background-color: {surface};
                color: {text};
                border: none;
                border-bottom: 1px solid {border};
                padding: {Spacing.SM}px {Spacing.MD}px;
                font-weight: bold;
            }}
            QTableWidget::item {{ padding: {Spacing.SM}px {Spacing.MD}px; }}
            QTableWidget::item:selected {{
                background-color: {primary};
                color: white;
            }}
        """)
        self._handlers_label.setStyleSheet(f"color: {text_sec};")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _c(mode: str, key: str) -> str:
    colors = Colors.LIGHT if mode == "light" else Colors.DARK
    return colors.get(key, "#000000")


def _ro_item(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
    item.setTextAlignment(Qt.AlignCenter)
    return item


__all__ = ["DailySummaryWidget"]

# Made with Bob
