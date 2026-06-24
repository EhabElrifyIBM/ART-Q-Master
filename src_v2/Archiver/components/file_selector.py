"""
File Selector Component (Phase 6.2 — Fixed & Upgraded)
=======================================================

Modern file selector widget with drag-drop support and recent files.

Fixes applied:
- file_selected signal now emits Path (was str — caused AttributeError in window)
- browse_file() is now public (was _browse_file — menu/shortcut crashed)
- Theme updates propagate to all sub-widgets correctly

Upgrades:
- Shows file size and last-modified timestamp on selection
- Recent files show date last opened
- Keyboard-navigable recent files list
"""

from typing import Optional
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QListWidget, QListWidgetItem, QFrame
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem, FontSizePreset
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from utils.recent_archiver_files import get_recent_archiver_files_manager


class FileSelectorWidget(QWidget):
    """
    File selector with drag-drop, file metadata display, and recent files.

    Signals:
        file_selected(Path): Emitted with the resolved Path when a valid
            Excel file is chosen via browse, drag-drop, or recent files list.
    """

    # FIX #1 & #2: signal emits Path not str; window's _on_file_selected(path: Path) works correctly
    file_selected = pyqtSignal(Path)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self._theme_mode = "light"
        self._typography = TypographySystem()
        self._recent_manager = get_recent_archiver_files_manager()
        self._selected_file: Optional[Path] = None

        self._setup_ui()
        self._apply_styles()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)

        # ── Drop zone ────────────────────────────────────────────────
        self._drop_zone = QFrame(self)
        self._drop_zone.setAcceptDrops(True)
        self._drop_zone.setMinimumHeight(160)
        self._drop_zone.dragEnterEvent = self._on_drag_enter
        self._drop_zone.dragLeaveEvent = self._on_drag_leave
        self._drop_zone.dropEvent = self._on_drop

        drop_layout = QVBoxLayout(self._drop_zone)
        drop_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        drop_layout.setSpacing(Spacing.SM)
        drop_layout.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("📁", self._drop_zone)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Segoe UI Emoji", 40))
        drop_layout.addWidget(icon_label)

        drop_text = QLabel("Drag & Drop Excel File Here", self._drop_zone)
        drop_text.setAlignment(Qt.AlignCenter)
        drop_text.setFont(self._typography.create_font("h3"))
        drop_layout.addWidget(drop_text)

        or_label = QLabel("or", self._drop_zone)
        or_label.setAlignment(Qt.AlignCenter)
        or_label.setFont(self._typography.create_font("body_sm"))
        drop_layout.addWidget(or_label)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        # FIX #16: method is public browse_file(), not _browse_file()
        self._browse_btn = PrimaryButton("Browse Files", self._drop_zone)
        self._browse_btn.setMinimumHeight(44)
        self._browse_btn.clicked.connect(self.browse_file)
        btn_row.addWidget(self._browse_btn)
        drop_layout.addLayout(btn_row)

        layout.addWidget(self._drop_zone)

        # ── Selected file info ────────────────────────────────────────
        self._file_info_frame = QFrame(self)
        file_info_layout = QVBoxLayout(self._file_info_frame)
        file_info_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        file_info_layout.setSpacing(2)

        self._file_label = QLabel("No file selected", self._file_info_frame)
        self._file_label.setFont(self._typography.create_font("body"))
        self._file_label.setWordWrap(True)
        file_info_layout.addWidget(self._file_label)

        self._file_meta_label = QLabel("", self._file_info_frame)
        self._file_meta_label.setFont(self._typography.create_font("caption"))
        self._file_meta_label.setVisible(False)
        file_info_layout.addWidget(self._file_meta_label)

        layout.addWidget(self._file_info_frame)

        # ── Recent files ──────────────────────────────────────────────
        recent_label = QLabel("Recent Files:", self)
        recent_label.setFont(self._typography.create_font("label"))
        layout.addWidget(recent_label)

        self._recent_list = QListWidget(self)
        self._recent_list.setMaximumHeight(130)
        self._recent_list.setFont(self._typography.create_font("body_sm"))
        self._recent_list.setAlternatingRowColors(True)
        self._recent_list.itemClicked.connect(self._on_recent_file_clicked)
        self._recent_list.itemActivated.connect(self._on_recent_file_clicked)  # keyboard Enter
        layout.addWidget(self._recent_list)

        self._load_recent_files()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_styles(self) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        bg = colors["background"]
        border = colors["border"]
        text = colors["text_primary"]
        text_sec = colors["text_secondary"]
        hover_bg = colors["surface_hover"]
        primary = colors["primary"]
        surface = colors["surface"]

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

        self._file_info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {BorderRadius.MD}px;
            }}
        """)
        self._file_label.setStyleSheet(f"QLabel {{ color: {text}; }}")
        self._file_meta_label.setStyleSheet(f"QLabel {{ color: {text_sec}; }}")

        self._recent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {bg};
                alternate-background-color: {surface};
                border: 1px solid {border};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.XS}px;
                color: {text};
                outline: none;
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px {Spacing.MD}px;
                border-radius: {BorderRadius.SM}px;
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
            QListWidget::item:selected {{
                background-color: {primary};
                color: white;
            }}
        """)

    def _apply_drag_active_style(self) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        self._drop_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['info_bg']};
                border: 2px solid {colors['primary']};
                border-radius: {BorderRadius.LG}px;
            }}
        """)

    # ------------------------------------------------------------------
    # Public API  (FIX #16: browse_file is public)
    # ------------------------------------------------------------------

    def browse_file(self) -> None:
        """Open a file-picker dialog and select an Excel file."""
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            str(self._selected_file.parent) if self._selected_file else "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)",
        )
        if path_str:
            self._select_file(Path(path_str))

    def get_selected_file(self) -> Optional[Path]:
        """Return the currently selected file Path, or None."""
        return self._selected_file

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self._selected_file = None
        self._file_label.setText("No file selected")
        self._file_label.setStyleSheet(
            f"QLabel {{ color: {Colors.LIGHT['text_primary'] if self._theme_mode == 'light' else Colors.DARK['text_primary']}; }}"
        )
        self._file_meta_label.setVisible(False)
        self._apply_styles()

    def set_theme_mode(self, mode: str) -> None:
        """Update the theme ('light' or 'dark')."""
        self._theme_mode = mode
        self._apply_styles()

    # ------------------------------------------------------------------
    # Drag-drop handlers
    # ------------------------------------------------------------------

    def _on_drag_enter(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if self._is_valid_excel_file(url.toLocalFile()):
                    event.acceptProposedAction()
                    self._apply_drag_active_style()
                    return

    def _on_drag_leave(self, event) -> None:
        self._apply_styles()

    def _on_drop(self, event: QDropEvent) -> None:
        self._apply_styles()
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self._is_valid_excel_file(file_path):
                    self._select_file(Path(file_path))
                    event.acceptProposedAction()
                    return

    # ------------------------------------------------------------------
    # Recent files list
    # ------------------------------------------------------------------

    def _load_recent_files(self) -> None:
        self._recent_list.clear()
        recent = self._recent_manager.get_recent_files(limit=5)

        if not recent:
            placeholder = QListWidgetItem("No recent files")
            placeholder.setFlags(Qt.NoItemFlags)
            self._recent_list.addItem(placeholder)
            return

        for info in recent:
            path_str = info.get("path", "")
            name = info.get("name", Path(path_str).name)
            ts = info.get("timestamp", "")

            # Format timestamp
            date_text = ""
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    date_text = f"  —  {dt.strftime('%b %d, %Y')}"
                except Exception:
                    pass

            item = QListWidgetItem(f"📄 {name}{date_text}")
            item.setData(Qt.UserRole, path_str)
            item.setToolTip(path_str)
            self._recent_list.addItem(item)

    def _on_recent_file_clicked(self, item: QListWidgetItem) -> None:
        path_str = item.data(Qt.UserRole)
        if path_str:
            self._select_file(Path(path_str))

    # ------------------------------------------------------------------
    # Core selection logic
    # ------------------------------------------------------------------

    def _is_valid_excel_file(self, file_path: str) -> bool:
        p = Path(file_path)
        return p.exists() and p.suffix.lower() in (".xlsx", ".xls")

    def _select_file(self, file_path: Path) -> None:
        """Validate, store, and announce a newly selected file."""
        if not file_path.exists():
            self._set_error(f"File not found: {file_path.name}")
            return

        if file_path.suffix.lower() not in (".xlsx", ".xls"):
            self._set_error("Invalid file type. Please select an Excel file (.xlsx or .xls)")
            return

        self._selected_file = file_path

        # Update label
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        self._file_label.setText(f"✅  {file_path.name}")
        self._file_label.setStyleSheet(f"QLabel {{ color: {colors['success']}; font-weight: bold; }}")

        # Show file metadata
        try:
            size_kb = file_path.stat().st_size / 1024
            modified = datetime.fromtimestamp(file_path.stat().st_mtime)
            self._file_meta_label.setText(
                f"{size_kb:.1f} KB  •  Modified {modified.strftime('%b %d, %Y %H:%M')}"
            )
            self._file_meta_label.setVisible(True)
        except Exception:
            self._file_meta_label.setVisible(False)

        # Persist to recent files and refresh list
        self._recent_manager.add_file(str(file_path))
        self._load_recent_files()

        # Emit Path signal (FIX #1)
        self.file_selected.emit(file_path)

    def _set_error(self, message: str) -> None:
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        self._file_label.setText(f"❌  {message}")
        self._file_label.setStyleSheet(f"QLabel {{ color: {colors['danger']}; }}")
        self._file_meta_label.setVisible(False)


__all__ = ["FileSelectorWidget"]

# Made with Bob
