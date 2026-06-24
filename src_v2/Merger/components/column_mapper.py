"""Column mapping component for Merger tool."""
from typing import Dict, List

from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QComboBox,
    QInputDialog,
    QFrame,
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography_mixin import V2TypographyMixin
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from utils.merge_templates import get_merge_templates_manager


class ColumnMapperWidget(QWidget, V2TypographyMixin):
    """Visual column mapping interface."""

    mapping_changed = pyqtSignal(dict)  # {target_col: [source_cols]}

    def __init__(self, parent=None):
        super().__init__(parent)
        V2TypographyMixin.__init__(self)

        self._theme_mode = "light"
        self.template_manager = get_merge_templates_manager()
        self.all_columns: List[str] = []
        self.mappings: Dict[str, List[str]] = {}

        self._setup_ui()
        self._load_templates()
        self._apply_styles()
        self.apply_typography()

    def _setup_ui(self):
        """Setup UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        self.title_label = QLabel("Column Mapping")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(
            "Select one or more source columns and add them to the output mapping."
        )
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)

        self.header_card = QFrame()
        header_layout = QHBoxLayout(self.header_card)
        header_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        header_layout.setSpacing(Spacing.MD)

        self.template_label = QLabel("Template:")
        header_layout.addWidget(self.template_label)

        self.template_combo = QComboBox()
        self.template_combo.addItem("No Template")
        self.template_combo.currentTextChanged.connect(self._on_template_selected)
        header_layout.addWidget(self.template_combo)

        header_layout.addStretch()

        self.save_template_btn = SecondaryButton("Save as Template")
        self.save_template_btn.clicked.connect(self._save_template)
        header_layout.addWidget(self.save_template_btn)

        layout.addWidget(self.header_card)

        self.content_card = QFrame()
        mapping_layout = QHBoxLayout(self.content_card)
        mapping_layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        mapping_layout.setSpacing(Spacing.MD)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(Spacing.SM)
        self.available_label = QLabel("Available Columns")
        left_panel.addWidget(self.available_label)

        self.available_list = QListWidget()
        self.available_list.setSelectionMode(QListWidget.MultiSelection)
        left_panel.addWidget(self.available_list)
        mapping_layout.addLayout(left_panel, 1)

        controls = QVBoxLayout()
        controls.setSpacing(Spacing.SM)
        controls.addStretch()

        self.add_mapping_btn = PrimaryButton("→ Add Mapping")
        self.add_mapping_btn.clicked.connect(self._add_mapping)
        controls.addWidget(self.add_mapping_btn)

        self.remove_mapping_btn = SecondaryButton("← Remove")
        self.remove_mapping_btn.clicked.connect(self._remove_mapping)
        controls.addWidget(self.remove_mapping_btn)

        controls.addStretch()
        mapping_layout.addLayout(controls)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(Spacing.SM)
        self.mapped_label = QLabel("Target Columns")
        right_panel.addWidget(self.mapped_label)

        self.mapped_list = QListWidget()
        right_panel.addWidget(self.mapped_list)
        mapping_layout.addLayout(right_panel, 1)

        layout.addWidget(self.content_card)

    def _apply_styles(self):
        """Apply theme-aware styling."""
        colors = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
        card_style = f"""
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
        """
        list_style = f"""
            QListWidget {{
                background-color: {colors['background']};
                color: {colors['text_primary']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px;
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px;
                border-radius: {BorderRadius.SM}px;
            }}
            QListWidget::item:selected {{
                background-color: {colors['primary']};
                color: {colors['text_inverse']};
            }}
            QListWidget::item:hover {{
                background-color: {colors['surface_hover']};
            }}
        """
        combo_style = f"""
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

        self.header_card.setStyleSheet(card_style)
        self.content_card.setStyleSheet(card_style)
        self.available_list.setStyleSheet(list_style)
        self.mapped_list.setStyleSheet(list_style)
        self.template_combo.setStyleSheet(combo_style)

        for label in [
            self.title_label,
            self.subtitle_label,
            self.template_label,
            self.available_label,
            self.mapped_label,
        ]:
            label.setStyleSheet(
                f"color: {colors['text_primary']}; background: transparent; border: none;"
            )

        self.subtitle_label.setStyleSheet(
            f"color: {colors['text_secondary']}; background: transparent; border: none;"
        )

    def apply_typography(self):
        """Apply typography to widgets."""
        self.title_label.setFont(self.get_font("h3", QFont.Bold))
        self.subtitle_label.setFont(self.get_font("body"))
        self.template_label.setFont(self.get_font("label"))
        self.available_label.setFont(self.get_font("label", QFont.Bold))
        self.mapped_label.setFont(self.get_font("label", QFont.Bold))
        self.template_combo.setFont(self.get_font("input"))
        self.available_list.setFont(self.get_font("body"))
        self.mapped_list.setFont(self.get_font("body"))

    def set_columns(self, columns: List[str]):
        """Set available columns."""
        self.all_columns = list(columns)
        self.available_list.clear()
        self.available_list.addItems(self.all_columns)

    def _load_templates(self):
        """Load saved templates."""
        existing_names = {self.template_combo.itemText(i) for i in range(self.template_combo.count())}
        for template in self.template_manager.get_templates():
            name = template.get("name", "")
            if name and name not in existing_names:
                self.template_combo.addItem(name)

    def _on_template_selected(self, template_name: str):
        """Handle template selection."""
        if template_name == "No Template":
            return

        template = self.template_manager.get_template(template_name)
        if not template:
            return

        template_mappings = template.get("column_mappings", [])
        converted: Dict[str, List[str]] = {}
        for mapping in template_mappings:
            output_name = mapping.get("output_name")
            source_columns = mapping.get("source_columns", [])
            if output_name and isinstance(source_columns, list):
                converted[output_name] = [str(col) for col in source_columns]

        self.mappings = converted
        self._update_mapped_list()
        self.mapping_changed.emit(self.get_mappings())

    def _add_mapping(self):
        """Add selected columns to mapping."""
        selected = self.available_list.selectedItems()
        if not selected:
            return

        source_cols = [item.text() for item in selected]
        default_name = source_cols[0] if len(source_cols) == 1 else "_".join(source_cols[:2])

        target_col, ok = QInputDialog.getText(
            self,
            "Target Column Name",
            "Enter output column name:",
            text=default_name,
        )
        if not ok or not target_col.strip():
            return

        self.mappings[target_col.strip()] = source_cols
        self._update_mapped_list()
        self.mapping_changed.emit(self.get_mappings())

    def _remove_mapping(self):
        """Remove selected mapping."""
        current = self.mapped_list.currentItem()
        if not current:
            return

        target_col = current.data(0)
        if not target_col:
            text = current.text()
            target_col = text.split(" ← ")[0] if " ← " in text else text

        if target_col in self.mappings:
            del self.mappings[target_col]
            self._update_mapped_list()
            self.mapping_changed.emit(self.get_mappings())

    def _update_mapped_list(self):
        """Update mapped columns display."""
        self.mapped_list.clear()
        for target, sources in self.mappings.items():
            display = f"{target} ← {', '.join(sources)}"
            self.mapped_list.addItem(display)

    def _save_template(self):
        """Save current mapping as template."""
        if not self.mappings:
            return

        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if not ok or not name.strip():
            return

        template_payload = [
            {
                "output_name": target,
                "source_columns": sources,
            }
            for target, sources in self.mappings.items()
        ]

        saved = self.template_manager.save_template(name.strip(), template_payload)
        if saved and self.template_combo.findText(name.strip()) < 0:
            self.template_combo.addItem(name.strip())

    def set_mappings(self, mappings: Dict[str, List[str]]):
        """Set mappings programmatically."""
        self.mappings = {str(k): [str(v) for v in values] for k, values in mappings.items()}
        self._update_mapped_list()
        self.mapping_changed.emit(self.get_mappings())

    def clear_mappings(self):
        """Clear all mappings."""
        self.mappings.clear()
        self._update_mapped_list()
        self.mapping_changed.emit(self.get_mappings())

    def get_mappings(self) -> Dict[str, List[str]]:
        """Get current mappings."""
        return {target: list(sources) for target, sources in self.mappings.items()}

    def set_theme_mode(self, mode: str):
        """Update theme mode."""
        self._theme_mode = mode
        self._apply_styles()


__all__ = ["ColumnMapperWidget"]

# Made with Bob