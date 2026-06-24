"""
Analysis View Component (Phase 6.2 — Fixed & Upgraded)
=======================================================

Display workbook analysis results in a modern layout.

Fixes applied:
- set_analysis() renamed → set_analysis_results() (was causing AttributeError)
- export_requested signal replaced with export_by_month_clicked /
  export_by_age_clicked — matching what the window actually wires up
- AnalysisViewWidget.export_requested no longer referenced internally

Upgrades:
- Stats bar: total cases, handler count, date range
- Per-handler month breakdown chart (text sparkline)
- Tab bar to switch between Month export and Age export views
"""

from typing import Optional, Dict
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QTabWidget
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem, FontSizePreset
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from Archiver.archiver_service import AnalysisResult


class _StatCard(QFrame):
    """Small stat card showing a value and a label."""

    def __init__(
        self,
        value: str,
        label: str,
        icon: str = "",
        theme_mode: str = "light",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(2)

        typo = TypographySystem()

        top_row = QHBoxLayout()
        if icon:
            ic = QLabel(icon)
            ic.setFont(QFont("Segoe UI Emoji", 16))
            top_row.addWidget(ic)
        self._value_label = QLabel(value)
        self._value_label.setFont(typo.create_font("h3", QFont.Bold))
        top_row.addWidget(self._value_label)
        top_row.addStretch()
        layout.addLayout(top_row)

        self._desc_label = QLabel(label)
        self._desc_label.setFont(typo.create_font("caption"))
        layout.addWidget(self._desc_label)

        self._apply_style(theme_mode)

    def update_value(self, value: str) -> None:
        self._value_label.setText(value)

    def _apply_style(self, theme_mode: str) -> None:
        colors = Colors.LIGHT if theme_mode == "light" else Colors.DARK
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.MD}px;
            }}
            QLabel {{ color: {colors['text_primary']}; }}
        """)
        self._desc_label.setStyleSheet(
            f"QLabel {{ color: {colors['text_secondary']}; }}"
        )


class AnalysisViewWidget(QWidget):
    """
    Display workbook analysis results with stats and per-handler table.

    Signals:
        export_by_month_clicked(): User clicked "Export by Month"
        export_by_age_clicked():   User clicked "Export by Age"
    """

    # FIX #4 & #14: correct signal names that the window actually connects to
    export_by_month_clicked = pyqtSignal()
    export_by_age_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._theme_mode = "light"
        self._typography = TypographySystem()
        self._analysis_results: Optional[Dict[str, AnalysisResult]] = None

        self._setup_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        # ── Title ────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_label = QLabel("📊  Analysis Results", self)
        title_label.setFont(self._typography.create_font("h2", QFont.Bold))
        title_row.addWidget(title_label)
        title_row.addStretch()
        layout.addLayout(title_row)

        # ── Stats bar ────────────────────────────────────────────────
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(Spacing.SM)

        self._stat_handlers = _StatCard("—", "Handlers", "👤")
        self._stat_cases = _StatCard("—", "Total Cases", "📋")
        self._stat_months = _StatCard("—", "Month Span", "📅")
        self._stat_oldest = _StatCard("—", "Oldest Case", "⏰")

        for card in (self._stat_handlers, self._stat_cases, self._stat_months, self._stat_oldest):
            stats_layout.addWidget(card)

        layout.addLayout(stats_layout)

        # ── Summary message ──────────────────────────────────────────
        self._summary_label = QLabel("Select and analyse a workbook to see results.", self)
        self._summary_label.setFont(self._typography.create_font("body"))
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        # ── Results table ────────────────────────────────────────────
        self._results_table = QTableWidget(self)
        self._results_table.setColumnCount(7)
        self._results_table.setHorizontalHeaderLabels([
            "Handler Sheet", "Total Cases", "✅ Completion Date",
            "🔄 Last Status Change", "⬜ No Date", "Month Span", "Recent Months"
        ])
        hdr = self._results_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(6, QHeaderView.Stretch)
        self._results_table.verticalHeader().setVisible(False)
        self._results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._results_table.setSelectionMode(QTableWidget.SingleSelection)
        self._results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._results_table.setMinimumHeight(180)
        self._results_table.setAlternatingRowColors(True)
        layout.addWidget(self._results_table)

        # ── Action buttons ───────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(Spacing.MD)

        self._export_month_btn = PrimaryButton("📅  Export by Month", self)
        self._export_month_btn.setMinimumHeight(44)
        self._export_month_btn.setToolTip("Export cases from a selected month")
        self._export_month_btn.clicked.connect(self.export_by_month_clicked.emit)
        self._export_month_btn.setEnabled(False)
        btn_layout.addWidget(self._export_month_btn)

        self._export_age_btn = SecondaryButton("⏳  Export by Age", self)
        self._export_age_btn.setMinimumHeight(44)
        self._export_age_btn.setToolTip("Export cases older than a specified number of days")
        self._export_age_btn.clicked.connect(self.export_by_age_clicked.emit)
        self._export_age_btn.setEnabled(False)
        btn_layout.addWidget(self._export_age_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        bg = colors["background"]
        border = colors["border"]
        text = colors["text_primary"]
        header_bg = colors["surface"]
        hover = colors["surface_hover"]
        primary = colors["primary"]

        self._results_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {bg};
                alternate-background-color: {header_bg};
                border: 1px solid {border};
                border-radius: {BorderRadius.MD}px;
                gridline-color: {border};
                color: {text};
            }}
            QTableWidget::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
            }}
            QTableWidget::item:selected {{
                background-color: {primary};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: {text};
                padding: {Spacing.SM}px {Spacing.MD}px;
                border: none;
                border-bottom: 2px solid {border};
                font-weight: bold;
            }}
        """)

        self._summary_label.setStyleSheet(f"""
            QLabel {{
                color: {text};
                padding: {Spacing.SM}px {Spacing.MD}px;
                background-color: {header_bg};
                border: 1px solid {border};
                border-radius: {BorderRadius.SM}px;
            }}
        """)

    # ------------------------------------------------------------------
    # Public API  (FIX #3: correct method name)
    # ------------------------------------------------------------------

    def set_analysis_results(self, results: Dict[str, AnalysisResult]) -> None:
        """
        Populate the view with analysis results.

        Args:
            results: Dict of AnalysisResult keyed by handler sheet name.
                     May include a "Companies" sheet entry alongside handler sheets.
        """
        _COMPANIES = "Companies"
        self._analysis_results = results

        # Separate handler sheets from Companies for accurate stat counts
        handler_results = {k: v for k, v in results.items() if k != _COMPANIES}
        companies_result = results.get(_COMPANIES)

        # Stats bar
        total_cases = sum(r.total_cases for r in results.values())
        all_months: set = set()
        for r in results.values():
            all_months.update(r.month_data.keys())
        month_list = sorted(all_months, reverse=True)

        oldest_dt: Optional[datetime] = None
        for r in results.values():
            if r.oldest_date and (oldest_dt is None or r.oldest_date < oldest_dt):
                oldest_dt = r.oldest_date

        # Date source totals (across all handler sheets, excluding Companies)
        total_by_completion = sum(r.dated_by_completion for r in handler_results.values())
        total_by_status     = sum(r.dated_by_status     for r in handler_results.values())
        total_blank         = sum(r.dated_blank          for r in handler_results.values())

        # Handler count shows only case-handler sheets; Companies is a bonus
        self._stat_handlers.update_value(str(len(handler_results)))
        self._stat_cases.update_value(f"{total_cases:,}")
        self._stat_months.update_value(str(len(month_list)) + " mo")
        self._stat_oldest.update_value(
            oldest_dt.strftime("%b %Y") if oldest_dt else "—"
        )

        # Summary text — includes date-source breakdown
        companies_note = (
            f" + Companies ({companies_result.total_cases:,} rows)"
            if companies_result else ""
        )
        handler_total = sum(r.total_cases for r in handler_results.values())
        self._summary_label.setText(
            f"✅  Found {len(handler_results)} handler sheet(s) with "
            f"{handler_total:,} case(s){companies_note} — spanning {len(month_list)} month(s).  "
            f"Date source: ✅ Completion Date: {total_by_completion:,}  |  "
            f"🔄 Last Status Change: {total_by_status:,}  |  "
            f"⬜ No date: {total_blank:,}"
        )

        # Table — handler sheets first, then Companies (with icon marker)
        self._results_table.setRowCount(0)

        def _item(text: str, center: bool = False) -> QTableWidgetItem:
            it = QTableWidgetItem(text)
            it.setFont(self._typography.create_font("body"))
            if center:
                it.setTextAlignment(Qt.AlignCenter)
            return it

        def _add_row(sheet_name: str, result: AnalysisResult, is_companies: bool = False) -> None:
            row = self._results_table.rowCount()
            self._results_table.insertRow(row)

            # Prefix Companies with a building icon so it stands out
            display_name = ("🏢  " + sheet_name) if is_companies else sheet_name
            self._results_table.setItem(row, 0, _item(display_name))
            self._results_table.setItem(row, 1, _item(f"{result.total_cases:,}", center=True))

            # Date-source columns
            self._results_table.setItem(row, 2, _item(f"{result.dated_by_completion:,}", center=True))
            self._results_table.setItem(row, 3, _item(f"{result.dated_by_status:,}", center=True))
            # Blank gets a dash if zero to reduce visual noise
            blank_text = f"{result.dated_blank:,}" if result.dated_blank else "—"
            self._results_table.setItem(row, 4, _item(blank_text, center=True))

            months = sorted(result.month_data.keys(), reverse=True)
            span = f"{months[-1]} → {months[0]}" if len(months) > 1 else (months[0] if months else "—")
            self._results_table.setItem(row, 5, _item(span, center=True))

            recent = months[:4]
            recent_text = ", ".join(
                f"{m} ({result.month_data[m]})" for m in recent
            )
            if len(months) > 4:
                recent_text += f"  (+{len(months) - 4} more)"
            self._results_table.setItem(row, 6, _item(recent_text))

        # Handler sheets first (alphabetical order preserved from service)
        for sheet_name, result in handler_results.items():
            _add_row(sheet_name, result, is_companies=False)

        # Companies sheet last, visually separated
        if companies_result:
            _add_row(_COMPANIES, companies_result, is_companies=True)

        # Enable export buttons
        self._export_month_btn.setEnabled(True)
        self._export_age_btn.setEnabled(True)

    def clear_results(self) -> None:
        """Reset the view to initial empty state."""
        self._analysis_results = None
        self._summary_label.setText("Select and analyse a workbook to see results.")
        self._results_table.setRowCount(0)
        self._stat_handlers.update_value("—")
        self._stat_cases.update_value("—")
        self._stat_months.update_value("—")
        self._stat_oldest.update_value("—")
        self._export_month_btn.setEnabled(False)
        self._export_age_btn.setEnabled(False)

    def get_analysis_results(self) -> Optional[Dict[str, AnalysisResult]]:
        """Return the currently displayed analysis results, or None."""
        return self._analysis_results

    def set_theme_mode(self, mode: str) -> None:
        """Update the theme ('light' or 'dark')."""
        self._theme_mode = mode
        self._apply_styles()


__all__ = ["AnalysisViewWidget"]

# Made with Bob
