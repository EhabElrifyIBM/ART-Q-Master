"""
Export Dialog Component
=======================

Clean QDialog for configuring month-based or age-based export operations.

All controls are always visible (no hover-to-reveal).  Output filename is
auto-generated as  "Archive (Mon - YYYY).xlsx"  and defaults to the same
folder as the source workbook.
"""

from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QLineEdit, QCheckBox, QPlainTextEdit,
    QFileDialog, QSpinBox, QGroupBox, QFrame, QListWidget,
    QPushButton, QDialogButtonBox, QScrollArea, QSizePolicy,
    QAbstractItemView,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem
from Archiver.archiver_service import ArchiverService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label(text: str, typo: TypographySystem, bold: bool = False) -> QLabel:
    lbl = QLabel(text)
    weight = QFont.Bold if bold else QFont.Normal
    lbl.setFont(typo.create_font("body", weight))
    return lbl


def _hline() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Sunken)
    return f


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class ExportDialog(QDialog):
    """
    Dialog for configuring month-based or age-based export operations.

    Always shows all controls without requiring hover.
    Auto-generates an 'Archive (Mon - YYYY).xlsx' filename that defaults
    to the same folder as the loaded workbook.
    """

    def __init__(
        self,
        parent: Optional[QWidget],
        service: ArchiverService,
        export_type: str = "month",   # "month" or "age"
    ) -> None:
        super().__init__(parent)

        self._service = service
        self._export_type = export_type
        self._typo = TypographySystem()

        title = "Export by Month" if export_type == "month" else "Export by Age"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(560)
        self.setMinimumHeight(520)
        self.resize(600, 600)

        self._build_ui()
        self._connect_signals()
        self._refresh_default_filename()
        self._update_preview()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.MD)
        root.setSpacing(Spacing.MD)

        # Title row
        title_lbl = QLabel(
            "📅  Export by Month" if self._export_type == "month" else "⏳  Export by Age"
        )
        title_lbl.setFont(self._typo.create_font("h2", QFont.Bold))
        root.addWidget(title_lbl)
        root.addWidget(_hline())

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body_widget = QWidget()
        body = QVBoxLayout(body_widget)
        body.setContentsMargins(0, 0, Spacing.SM, 0)
        body.setSpacing(Spacing.MD)
        scroll.setWidget(body_widget)
        root.addWidget(scroll, 1)

        # ── Handler ────────────────────────────────────────────────────
        handler_box = QGroupBox("Handler")
        handler_box.setFont(self._typo.create_font("label", QFont.Bold))
        hl = QVBoxLayout(handler_box)
        hl.setSpacing(Spacing.SM)
        hl.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

        self._handler_combo = QComboBox()
        self._handler_combo.setMinimumHeight(40)
        self._handler_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._handler_combo.addItem("All Handlers")
        self._handler_combo.addItems(self._service.get_handlers())
        hl.addWidget(self._handler_combo)
        body.addWidget(handler_box)

        # ── Month / Age specific ──────────────────────────────────────
        if self._export_type == "month":
            month_box = QGroupBox("Months to Export  (hold Ctrl / ⌘ for multi-select)")
            month_box.setFont(self._typo.create_font("label", QFont.Bold))
            ml = QVBoxLayout(month_box)
            ml.setSpacing(Spacing.SM)
            ml.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

            self._month_list = QListWidget()
            self._month_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
            self._month_list.setMinimumHeight(120)
            self._month_list.setMaximumHeight(160)
            self._month_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            self._month_list.addItems(self._service.get_available_months())
            # Pre-select the first item
            if self._month_list.count():
                self._month_list.setCurrentRow(0)
            ml.addWidget(self._month_list)

            # Helper buttons row
            sel_row = QHBoxLayout()
            sel_all_btn = QPushButton("Select All")
            sel_all_btn.setFixedHeight(30)
            sel_all_btn.clicked.connect(self._month_list.selectAll)
            sel_row.addWidget(sel_all_btn)
            sel_none_btn = QPushButton("Clear")
            sel_none_btn.setFixedHeight(30)
            sel_none_btn.clicked.connect(self._month_list.clearSelection)
            sel_row.addWidget(sel_none_btn)
            sel_row.addStretch()
            ml.addLayout(sel_row)

            body.addWidget(month_box)
        else:
            age_box = QGroupBox("Age Threshold")
            age_box.setFont(self._typo.create_font("label", QFont.Bold))
            al = QVBoxLayout(age_box)
            al.setSpacing(Spacing.SM)
            al.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

            age_row = QHBoxLayout()
            age_lbl = _label("Export cases older than:", self._typo)
            age_row.addWidget(age_lbl)
            age_row.addStretch()

            self._days_spin = QSpinBox()
            self._days_spin.setMinimumHeight(40)
            self._days_spin.setMinimum(1)
            self._days_spin.setMaximum(3650)
            self._days_spin.setValue(30)
            self._days_spin.setSuffix("  days")
            self._days_spin.setFixedWidth(130)
            age_row.addWidget(self._days_spin)
            al.addLayout(age_row)
            body.addWidget(age_box)

        # ── Output file ────────────────────────────────────────────────
        out_box = QGroupBox("Save Archive To")
        out_box.setFont(self._typo.create_font("label", QFont.Bold))
        ol = QVBoxLayout(out_box)
        ol.setSpacing(Spacing.SM)
        ol.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

        out_row = QHBoxLayout()
        self._output_edit = QLineEdit()
        self._output_edit.setMinimumHeight(40)
        self._output_edit.setPlaceholderText("Click Browse… or edit path directly")
        self._output_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        out_row.addWidget(self._output_edit)

        browse_btn = QPushButton("Browse…")
        browse_btn.setMinimumHeight(40)
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_output)
        out_row.addWidget(browse_btn)
        ol.addLayout(out_row)
        body.addWidget(out_box)

        # ── Options ────────────────────────────────────────────────────
        opts_box = QGroupBox("Options")
        opts_box.setFont(self._typo.create_font("label", QFont.Bold))
        opts_l = QVBoxLayout(opts_box)
        opts_l.setSpacing(Spacing.SM)
        opts_l.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

        self._cleanup_check = QCheckBox(
            "Remove exported rows from original file  (a timestamped backup is created automatically)"
        )
        self._cleanup_check.setFont(self._typo.create_font("body"))
        opts_l.addWidget(self._cleanup_check)

        # Merged sheet option is available for BOTH export types
        self._merged_check = QCheckBox(
            "Create a merged sheet combining all handlers"
        )
        self._merged_check.setFont(self._typo.create_font("body"))
        opts_l.addWidget(self._merged_check)

        body.addWidget(opts_box)

        # ── Preview ────────────────────────────────────────────────────
        prev_box = QGroupBox("Preview")
        prev_box.setFont(self._typo.create_font("label", QFont.Bold))
        prev_l = QVBoxLayout(prev_box)
        prev_l.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)

        self._preview_text = QPlainTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setMinimumHeight(100)
        self._preview_text.setMaximumHeight(130)
        self._preview_text.setFont(self._typo.create_font("body_sm"))
        prev_l.addWidget(self._preview_text)
        body.addWidget(prev_box)

        body.addStretch()

        # ── Button row ─────────────────────────────────────────────────
        root.addWidget(_hline())
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setMinimumHeight(40)
        self._cancel_btn.setFixedWidth(100)
        self._cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._cancel_btn)

        self._export_btn = QPushButton("📦  Export")
        self._export_btn.setMinimumHeight(40)
        self._export_btn.setFixedWidth(130)
        self._export_btn.setDefault(True)
        self._export_btn.clicked.connect(self._on_export_clicked)
        btn_row.addWidget(self._export_btn)

        root.addLayout(btn_row)

        self._apply_styles()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        colors = Colors.LIGHT
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
            }}
            QGroupBox {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.MD}px;
                margin-top: 6px;
                padding-top: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {colors['text_primary']};
            }}
            QComboBox, QLineEdit, QSpinBox {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.SM}px;
                padding: 4px 10px;
                color: {colors['text_primary']};
                selection-background-color: {colors['primary']};
            }}
            QComboBox:focus, QLineEdit:focus, QSpinBox:focus {{
                border: 2px solid {colors['primary']};
            }}
            QListWidget {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.SM}px;
                color: {colors['text_primary']};
                padding: 2px;
                outline: none;
            }}
            QListWidget:focus {{
                border: 2px solid {colors['primary']};
            }}
            QListWidget::item {{
                padding: 4px 10px;
                border-radius: 3px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background-color: {colors['surface_hover']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QCheckBox {{
                color: {colors['text_primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {colors['border']};
                border-radius: 3px;
                background: {colors['background']};
            }}
            QCheckBox::indicator:checked {{
                background: {colors['primary']};
                border-color: {colors['primary']};
            }}
            QPlainTextEdit {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.SM}px;
                color: {colors['text_secondary']};
                padding: 4px;
            }}
            QPushButton {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.SM}px;
                color: {colors['text_primary']};
                padding: 6px 16px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {colors['surface_hover']};
                border-color: {colors['primary']};
            }}
            QPushButton#export_btn {{
                background-color: {colors['primary']};
                color: white;
                border: none;
            }}
            QPushButton#export_btn:hover {{
                background-color: {colors['primary_hover']};
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QScrollArea {{
                background: transparent;
            }}
        """)
        self._export_btn.setObjectName("export_btn")
        self._export_btn.setStyleSheet(
            f"QPushButton {{ background-color: {colors['primary']}; color: white; "
            f"border: none; border-radius: {BorderRadius.SM}px; "
            f"padding: 6px 16px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: {colors.get('primary_hover', '#0050a0')}; }}"
        )

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    def _connect_signals(self) -> None:
        self._handler_combo.currentTextChanged.connect(self._on_handler_changed)
        self._cleanup_check.stateChanged.connect(self._update_preview)
        self._merged_check.stateChanged.connect(self._update_preview)

        if self._export_type == "month":
            self._month_list.itemSelectionChanged.connect(self._on_month_selection_changed)
        else:
            self._days_spin.valueChanged.connect(self._update_preview)

    def _on_handler_changed(self, handler: str) -> None:
        if self._export_type == "month":
            months = self._service.get_available_months(
                None if handler == "All Handlers" else handler
            )
            self._month_list.blockSignals(True)
            self._month_list.clear()
            self._month_list.addItems(months)
            if self._month_list.count():
                self._month_list.setCurrentRow(0)
            self._month_list.blockSignals(False)
        self._refresh_default_filename()
        self._update_preview()

    def _on_month_selection_changed(self) -> None:
        self._refresh_default_filename()
        self._update_preview()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _selected_months(self) -> List[str]:
        """Return sorted list of selected 'YYYY-MM' month strings."""
        return sorted(
            item.text() for item in self._month_list.selectedItems()
        )

    # ------------------------------------------------------------------
    # Default filename
    # ------------------------------------------------------------------

    def _refresh_default_filename(self) -> None:
        """Auto-generate 'Archive (Mon - YYYY).xlsx' based on current selection."""
        # Use workbook folder as default save location
        base_dir = ""
        if self._service.workbook_path:
            base_dir = str(Path(self._service.workbook_path).parent)

        if self._export_type == "month":
            months = self._selected_months()
            fname = self._service.make_archive_filename(months)
        else:
            # For age export, use all months available for the selected handler
            handler = self._handler_combo.currentText()
            months = self._service.get_available_months(
                None if handler == "All Handlers" else handler
            )
            fname = self._service.make_archive_filename(months)

        if base_dir:
            full_path = str(Path(base_dir) / fname)
        else:
            full_path = fname

        # Only update if user hasn't typed something custom yet
        current = self._output_edit.text().strip()
        is_default = (not current) or Path(current).name.startswith("Archive")
        if is_default:
            self._output_edit.setText(full_path)

    # ------------------------------------------------------------------
    # Preview
    # ------------------------------------------------------------------

    def _update_preview(self) -> None:
        handler = self._handler_combo.currentText()
        cleanup = self._cleanup_check.isChecked()

        try:
            if self._export_type == "month":
                months = self._selected_months()
                if not months:
                    self._preview_text.setPlainText("⚠  No months selected.")
                    return
                data = self._service.preview_month_export(handler, months, cleanup)
            else:
                days = self._days_spin.value()
                data = self._service.preview_age_export(handler, days, cleanup)

            lines = []
            if self._export_type == "age":
                cutoff = data.get("cutoff_date")
                if cutoff:
                    lines.append(f"Cutoff date:   {cutoff.strftime('%Y-%m-%d')}")

            total = data.get("total", 0)
            lines.append(f"Cases to export:   {total:,}")

            details = data.get("details", [])
            if details:
                lines.append("")
                lines.append("Breakdown by handler:")
                for d in details:
                    lines.append(f"  • {d['handler']}:  {d['count']:,} case(s)")

            if cleanup and "cleanup" in data:
                c = data["cleanup"]
                lines.append("")
                lines.append("After cleanup:")
                lines.append(f"  Rows removed from original:  {c['to_delete']:,}")
                lines.append(f"  Rows remaining in original:  {c['remaining']:,}")

            if total == 0:
                lines.append("")
                lines.append("⚠  No cases match the selected criteria.")

            self._preview_text.setPlainText("\n".join(lines))

        except Exception as exc:
            self._preview_text.setPlainText(f"Preview error: {exc}")

    # ------------------------------------------------------------------
    # Browse
    # ------------------------------------------------------------------

    def _browse_output(self) -> None:
        current = self._output_edit.text().strip()
        start_dir = str(Path(current).parent) if current else ""
        suggested = Path(current).name if current else "Archive.xlsx"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Archive File",
            str(Path(start_dir) / suggested) if start_dir else suggested,
            "Excel Files (*.xlsx);;All Files (*.*)",
        )
        if path:
            # Ensure .xlsx extension
            if not path.lower().endswith(".xlsx"):
                path += ".xlsx"
            self._output_edit.setText(path)

    # ------------------------------------------------------------------
    # Export action
    # ------------------------------------------------------------------

    def _on_export_clicked(self) -> None:
        output_file = self._output_edit.text().strip()
        if not output_file:
            self._preview_text.setPlainText("⚠  Please specify an output file path.")
            return

        if self._export_type == "month":
            if not self._selected_months():
                self._preview_text.setPlainText("⚠  Please select at least one month.")
                return

        self.accept()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_export_options(self) -> Dict[str, Any]:
        """Return export parameters collected from the dialog."""
        output_file = self._output_edit.text().strip()
        if not output_file.lower().endswith(".xlsx"):
            output_file += ".xlsx"

        options: Dict[str, Any] = {
            "export_type": self._export_type,
            "handler": self._handler_combo.currentText(),
            "output_file": output_file,
            "cleanup": self._cleanup_check.isChecked(),
            "merged": self._merged_check.isChecked(),
        }

        if self._export_type == "month":
            options["months"] = self._selected_months()
        else:
            options["days"] = self._days_spin.value()

        return options


__all__ = ["ExportDialog"]

# Made with Bob
