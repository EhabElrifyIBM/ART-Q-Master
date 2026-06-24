"""
Daily Calendar Widget
=====================

Shows a compact month-grid for every month detected in the loaded daily files.
Each day cell is either:

  • Marked  (●) — a file was loaded for that date  →  primary/success colour
  • Empty        — no file for that date             →  surface colour

Supports dark/light themes and multi-month date ranges.

Public API
----------
  set_dates(date_strs)   — receive a list of "MM-DD" strings; rebuilds grids
  clear()                — reset to empty / hidden state
  set_theme_mode(mode)   — "light" | "dark"
"""

from __future__ import annotations

import calendar
from typing import Dict, List, Optional, Set, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem

# Day-of-week header labels (Mon first)
_DOW_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

_MONTH_NAMES = {
    1: "January",  2: "February", 3: "March",    4: "April",
    5: "May",      6: "June",     7: "July",      8: "August",
    9: "September",10: "October", 11: "November", 12: "December",
}


class _MonthGrid(QFrame):
    """
    A single month calendar grid.

    Draws 7 columns (Mon–Sun) and up to 6 rows of day cells.
    Marked days are highlighted; empty days have no number shown.
    """

    def __init__(
        self,
        year: int,
        month: int,
        marked_days: Set[int],
        theme_mode: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._year       = year
        self._month      = month
        self._marked     = marked_days
        self._theme_mode = theme_mode
        self._typography = TypographySystem()
        self._day_cells: List[QLabel] = []

        self._build()
        self._apply_styles()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        outer.setSpacing(4)

        # Month title
        title = QLabel(
            f"{_MONTH_NAMES[self._month]} {self._year}", self
        )
        title.setFont(self._typography.create_font("label"))
        title.setAlignment(Qt.AlignCenter)
        outer.addWidget(title)
        self._title_label = title

        # Day-of-week header row
        grid = QGridLayout()
        grid.setSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)

        for col, dow in enumerate(_DOW_LABELS):
            lbl = QLabel(dow, self)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFont(self._typography.create_font("caption"))
            lbl.setFixedSize(34, 22)
            grid.addWidget(lbl, 0, col)
            self._style_dow_header(lbl)

        # Day cells
        # calendar.monthcalendar returns rows of [Mon…Sun], 0 = not this month
        cal_rows = calendar.monthcalendar(self._year, self._month)
        self._day_cells.clear()

        for row_idx, week in enumerate(cal_rows):
            for col_idx, day_num in enumerate(week):
                cell = QLabel(self)
                cell.setFixedSize(34, 32)
                cell.setAlignment(Qt.AlignCenter)

                if day_num == 0:
                    # Outside this month — blank filler
                    cell.setText("")
                    cell._is_marked  = False  # type: ignore[attr-defined]
                    cell._day_num    = 0       # type: ignore[attr-defined]
                else:
                    cell.setText(str(day_num))
                    cell._is_marked = day_num in self._marked  # type: ignore[attr-defined]
                    cell._day_num   = day_num                  # type: ignore[attr-defined]

                grid.addWidget(cell, row_idx + 1, col_idx)
                self._day_cells.append(cell)

        outer.addLayout(grid)

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _style_dow_header(self, lbl: QLabel) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        lbl.setStyleSheet(
            f"QLabel {{ color: {colors['text_secondary']}; font-weight: bold; }}"
        )

    def _apply_styles(self) -> None:
        colors  = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        surface = colors["surface"]
        border  = colors["border"]
        text    = colors["text_primary"]
        text_s  = colors["text_secondary"]
        primary = colors["primary"]
        success = colors["success"]
        success_bg = colors["success_bg"]

        # Frame border
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {surface};
                border: 1px solid {border};
                border-radius: {BorderRadius.MD}px;
            }}
        """)

        # Title
        self._title_label.setStyleSheet(
            f"QLabel {{ color: {text}; font-weight: bold; border: none; }}"
        )

        for cell in self._day_cells:
            day_num  = getattr(cell, "_day_num",  0)
            is_marked = getattr(cell, "_is_marked", False)

            if day_num == 0:
                cell.setStyleSheet(
                    "QLabel { background: transparent; border: none; }"
                )
                continue

            if is_marked:
                # Filled pill — success green
                cell.setStyleSheet(f"""
                    QLabel {{
                        background-color: {success_bg};
                        color: {success};
                        border: 2px solid {success};
                        border-radius: 6px;
                        font-weight: bold;
                    }}
                """)
            else:
                # Empty day — subtle outline
                cell.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: {text_s};
                        border: 1px solid {border};
                        border-radius: 6px;
                    }}
                """)

    def set_theme_mode(self, mode: str) -> None:
        self._theme_mode = mode
        self._apply_styles()
        # Re-style DOW headers
        dow_row_labels = []
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if item and item.layout():
                grid = item.layout()
                for j in range(7):
                    w = grid.itemAtPosition(0, j)
                    if w and w.widget():
                        self._style_dow_header(w.widget())


class DailyCalendarWidget(QWidget):
    """
    Container that holds one _MonthGrid per detected month, arranged
    horizontally in a scroll area.

    Usage::

        cal = DailyCalendarWidget()
        cal.set_dates(["01-03", "01-07", "01-15", "02-01"])
        # → renders January and February grids side-by-side
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme_mode = "light"
        self._typography = TypographySystem()
        self._grids: List[_MonthGrid] = []
        self._current_year = _current_year()

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(Spacing.XS)

        # ── Section header ────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(Spacing.SM)

        self._title_lbl = QLabel("📆  File Coverage Calendar", self)
        self._title_lbl.setFont(self._typography.create_font("label"))
        hdr.addWidget(self._title_lbl)

        self._legend_loaded = QLabel("", self)
        self._legend_loaded.setFont(self._typography.create_font("caption"))
        hdr.addWidget(self._legend_loaded)
        hdr.addStretch()

        # Legend
        self._legend_lbl = QLabel(
            "  ●  = file loaded    □  = no file", self
        )
        self._legend_lbl.setFont(self._typography.create_font("caption"))
        hdr.addWidget(self._legend_lbl)

        root.addLayout(hdr)

        # ── Scroll area containing month grids side by side ───────────
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setFixedHeight(230)

        self._inner = QWidget()
        self._inner_layout = QHBoxLayout(self._inner)
        self._inner_layout.setContentsMargins(0, 0, 0, 0)
        self._inner_layout.setSpacing(Spacing.MD)
        self._inner_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self._placeholder = QLabel(
            "Load daily files to see coverage calendar…", self._inner
        )
        self._placeholder.setAlignment(Qt.AlignCenter)
        self._placeholder.setFont(self._typography.create_font("body_sm"))
        self._inner_layout.addWidget(self._placeholder)

        self._scroll.setWidget(self._inner)
        root.addWidget(self._scroll)

        self._apply_styles()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_dates(self, date_strs: List[str]) -> None:
        """
        Rebuild calendar grids from a list of "MM-DD" strings.

        Dates are assumed to be in the current year unless you provide a
        dict via the internal _set_year_dates API.
        """
        self._rebuild(date_strs)

    def clear(self) -> None:
        """Remove all grids and show the placeholder."""
        self._clear_grids()
        self._placeholder.setVisible(True)
        self._legend_loaded.setText("")

    def set_theme_mode(self, mode: str) -> None:
        self._theme_mode = mode
        for g in self._grids:
            g.set_theme_mode(mode)
        self._apply_styles()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _rebuild(self, date_strs: List[str]) -> None:
        self._clear_grids()

        # Parse "MM-DD" → month→{days} mapping
        month_days: Dict[int, Set[int]] = {}
        for ds in date_strs:
            parts = ds.split("-")
            if len(parts) != 2:
                continue
            try:
                m, d = int(parts[0]), int(parts[1])
                month_days.setdefault(m, set()).add(d)
            except ValueError:
                continue

        if not month_days:
            self._placeholder.setVisible(True)
            self._legend_loaded.setText("")
            return

        self._placeholder.setVisible(False)

        year = self._current_year
        total_marked = sum(len(v) for v in month_days.values())
        total_days   = sum(
            calendar.monthrange(year, m)[1] for m in month_days
        )

        self._legend_loaded.setText(
            f"  {total_marked} day{'s' if total_marked != 1 else ''} loaded"
            f" / {total_days} working days in range"
        )

        for month in sorted(month_days.keys()):
            grid = _MonthGrid(
                year=year,
                month=month,
                marked_days=month_days[month],
                theme_mode=self._theme_mode,
                parent=self._inner,
            )
            grid.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            self._inner_layout.addWidget(grid)
            self._grids.append(grid)

        # Push grids left
        self._inner_layout.addStretch()

    def _clear_grids(self) -> None:
        for g in self._grids:
            self._inner_layout.removeWidget(g)
            g.deleteLater()
        self._grids.clear()

    def _apply_styles(self) -> None:
        colors  = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        text    = colors["text_primary"]
        text_s  = colors["text_secondary"]
        success = colors["success"]
        bg      = colors["background"]

        self._scroll.setStyleSheet(
            f"QScrollArea {{ background-color: {bg}; border: none; }}"
        )
        self._inner.setStyleSheet(
            f"QWidget {{ background-color: {bg}; }}"
        )
        self._title_lbl.setStyleSheet(
            f"QLabel {{ color: {text}; font-weight: bold; }}"
        )
        self._legend_lbl.setStyleSheet(
            f"QLabel {{ color: {text_s}; }}"
        )
        self._legend_loaded.setStyleSheet(
            f"QLabel {{ color: {success}; font-weight: bold; }}"
        )
        self._placeholder.setStyleSheet(
            f"QLabel {{ color: {text_s}; }}"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _current_year() -> int:
    from datetime import date
    return date.today().year


__all__ = ["DailyCalendarWidget"]

# Made with Bob
