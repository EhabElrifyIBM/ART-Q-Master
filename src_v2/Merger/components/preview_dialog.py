"""Merge preview dialog for Merger tool."""
import pandas as pd

from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QTableWidgetItem,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography_mixin import V2TypographyMixin
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from ui.components_v2.tables import ModernTableWidget


class PreviewDialog(QDialog, V2TypographyMixin):
    """Preview merged data before execution."""

    def __init__(self, preview_df: pd.DataFrame, stats: dict, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self.preview_df = preview_df
        self.stats = stats
        self._theme_mode = "light"

        self._setup_ui()
        self._apply_styles()
        self.apply_typography()

    def _setup_ui(self):
        """Setup UI."""
        self.setWindowTitle("Merge Preview")
        self.setMinimumSize(900, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self.title_label = QLabel("Merge Preview")
        layout.addWidget(self.title_label)

        self.stats_label = QLabel(
            f"Previewing {self.stats.get('total_rows', 0)} rows, "
            f"{self.stats.get('total_columns', 0)} columns from "
            f"{self.stats.get('file_count', 0)} files"
        )
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)

        self.card = QFrame()
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        card_layout.setSpacing(Spacing.MD)

        self.notice_label = QLabel("Showing the first 100 rows of the merged result.")
        card_layout.addWidget(self.notice_label)

        self.table = ModernTableWidget()
        card_layout.addWidget(self.table)
        layout.addWidget(self.card)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = SecondaryButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.confirm_btn = PrimaryButton("Confirm Merge")
        self.confirm_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.confirm_btn)

        layout.addLayout(button_layout)

        self._populate_table()

    def _apply_styles(self):
        """Apply theme-aware styling."""
        colors = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {colors['background']};
            }}
            """
        )
        self.card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
            """
        )
        self.title_label.setStyleSheet(
            f"color: {colors['text_primary']}; background: transparent; border: none;"
        )
        self.stats_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent; border: none;"
        )
        self.notice_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent; border: none;"
        )

    def apply_typography(self):
        """Apply typography to widgets."""
        self.title_label.setFont(self.get_font("h2", QFont.Bold))
        self.stats_label.setFont(self.get_font("body"))
        self.notice_label.setFont(self.get_font("body_sm"))

    def _populate_table(self):
        """Populate table with preview data."""
        preview = self.preview_df.head(100).copy()

        self.table._table.clear()
        self.table.set_columns([str(col) for col in preview.columns])

        rows = []
        for _, row in preview.iterrows():
            rows.append([("" if pd.isna(value) else str(value)) for value in row.tolist()])

        self.table.set_data(rows)
        self.table.resize_columns_to_contents()

    def set_theme_mode(self, mode: str):
        """Update theme mode."""
        self._theme_mode = mode
        self._apply_styles()
        self.table.set_theme(mode)


__all__ = ["PreviewDialog"]

# Made with Bob