"""Sheet selector component for Merger tool."""
from pathlib import Path
from typing import Dict, List

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QScrollArea,
    QFrame,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography_mixin import V2TypographyMixin


class SheetSelectorRow(QWidget, V2TypographyMixin):
    """Single file sheet selector row."""

    sheet_changed = pyqtSignal(Path, str)  # file_path, sheet_name

    def __init__(self, file_path: Path, sheets: List[str], parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self.file_path = file_path
        self.sheets = sheets
        self._theme_mode = "light"

        self._setup_ui()
        self._apply_styles()
        self.apply_typography()

    def _setup_ui(self):
        """Setup row UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.SM, Spacing.MD, Spacing.SM)
        layout.setSpacing(Spacing.MD)

        self.file_label = QLabel(self.file_path.name)
        self.file_label.setMinimumWidth(240)
        self.file_label.setToolTip(str(self.file_path))
        layout.addWidget(self.file_label)

        self.sheet_combo = QComboBox()
        self.sheet_combo.setMinimumWidth(180)
        self.sheet_combo.addItems(self.sheets)
        self.sheet_combo.currentTextChanged.connect(self._on_sheet_changed)
        layout.addWidget(self.sheet_combo)

        layout.addStretch()

    def _apply_styles(self):
        """Apply theme-aware styling."""
        colors = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
        self.setStyleSheet(
            f"""
            SheetSelectorRow {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.MD}px;
            }}
            QLabel {{
                color: {colors['text_primary']};
                background: transparent;
            }}
            QComboBox {{
                background-color: {colors['input_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['input_border']};
                border-radius: {BorderRadius.SM}px;
                padding: {Spacing.SM}px;
                min-height: 36px;
            }}
            QComboBox:hover {{
                border-color: {colors['primary']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                selection-background-color: {colors['primary']};
                selection-color: {colors['text_inverse']};
            }}
            """
        )

    def apply_typography(self):
        """Apply typography to widgets."""
        self.file_label.setFont(self.get_font("body"))
        self.sheet_combo.setFont(self.get_font("input"))

    def _on_sheet_changed(self, sheet_name: str):
        """Handle sheet selection change."""
        self.sheet_changed.emit(self.file_path, sheet_name)

    def get_selected_sheet(self) -> str:
        """Get selected sheet name."""
        return self.sheet_combo.currentText()

    def set_selected_sheet(self, sheet_name: str):
        """Set selected sheet if it exists."""
        index = self.sheet_combo.findText(sheet_name)
        if index >= 0:
            self.sheet_combo.setCurrentIndex(index)

    def set_theme_mode(self, mode: str):
        """Update theme mode."""
        self._theme_mode = mode
        self._apply_styles()


class SheetSelectorWidget(QWidget, V2TypographyMixin):
    """Sheet selector for multiple files."""

    sheets_changed = pyqtSignal(dict)  # {file_path: sheet_name}

    def __init__(self, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self._theme_mode = "light"
        self.sheet_rows: Dict[Path, SheetSelectorRow] = {}

        self._setup_ui()
        self._apply_styles()
        self.apply_typography()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        self.title_label = QLabel("Select Sheets")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("Choose which worksheet to use from each loaded file.")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.card = QFrame()
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        card_layout.setSpacing(Spacing.SM)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(Spacing.SM)
        self.container_layout.addStretch()

        self.scroll.setWidget(self.container)
        card_layout.addWidget(self.scroll)
        layout.addWidget(self.card)

    def _apply_styles(self):
        """Apply theme-aware styling."""
        colors = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
        self.card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {colors['background']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
            """
        )
        self.title_label.setStyleSheet(
            f"color: {colors['text_primary']}; background: transparent; border: none;"
        )
        self.subtitle_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent; border: none;"
        )
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

    def apply_typography(self):
        """Apply typography to widgets."""
        self.title_label.setFont(self.get_font("h3"))
        self.subtitle_label.setFont(self.get_font("body"))
        for row in self.sheet_rows.values():
            row.apply_typography()

    def set_files(self, file_sheets: Dict[Path, List[str]]):
        """Set files and their available sheets."""
        for row in self.sheet_rows.values():
            row.deleteLater()
        self.sheet_rows.clear()

        for file_path, sheets in file_sheets.items():
            if not sheets:
                continue
            row = SheetSelectorRow(file_path, sheets)
            row.set_theme_mode(self._theme_mode)
            row.sheet_changed.connect(self._on_sheet_changed)
            self.container_layout.insertWidget(self.container_layout.count() - 1, row)
            self.sheet_rows[file_path] = row

        self.sheets_changed.emit(self.get_selections())

    def clear(self):
        """Clear all selector rows."""
        self.set_files({})

    def _on_sheet_changed(self, file_path: Path, sheet_name: str):
        """Handle sheet change."""
        self.sheets_changed.emit(self.get_selections())

    def get_selections(self) -> Dict[Path, str]:
        """Get all sheet selections."""
        return {
            file_path: row.get_selected_sheet()
            for file_path, row in self.sheet_rows.items()
        }

    def set_selections(self, selections: Dict[Path, str]):
        """Apply sheet selections programmatically."""
        for file_path, sheet_name in selections.items():
            row = self.sheet_rows.get(file_path)
            if row:
                row.set_selected_sheet(sheet_name)

    def set_theme_mode(self, mode: str):
        """Update theme mode."""
        self._theme_mode = mode
        self._apply_styles()
        for row in self.sheet_rows.values():
            row.set_theme_mode(mode)


__all__ = ["SheetSelectorRow", "SheetSelectorWidget"]

# Made with Bob