"""
File List Component (Phase 6.3)
================================

Modern multi-file selector widget with drag-drop support and file management.

Features:
- Multi-file drag-drop selection
- Browse button for file picker
- File reordering (drag to reorder)
- Remove individual files
- Recent operations quick load
- File validation (Excel files only)
- Visual feedback for drag-over state
- WCAG 2.1 AA compliant
"""

from typing import Optional, List, Callable
from pathlib import Path

from PyQt5.QtCore import Qt, pyqtSignal, QMimeData
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QListWidget, QListWidgetItem, QFrame, QPushButton
)

from ui.design_system import Colors, Spacing, BorderRadius
from ui.typography import TypographySystem, FontSizePreset
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from utils.recent_merger_files import get_recent_merger_files_manager


class FileListWidget(QWidget):
    """
    Multi-file selector with drag-drop and file management.
    
    Signals:
        files_changed: Emitted when file list changes (file_paths: List[str])
        file_loaded: Emitted when a file is successfully loaded (file_path: str)
    """
    
    files_changed = pyqtSignal(list)  # List[str] of file paths
    file_loaded = pyqtSignal(str)  # file_path
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize file list widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._theme_mode = 'light'
        self._typography = TypographySystem()
        self._recent_manager = get_recent_merger_files_manager()
        self._file_paths: List[str] = []
        
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.MD)
        
        # Title
        title_label = QLabel("Excel Files to Merge", self)
        title_label.setFont(self._typography.create_font('h3'))
        layout.addWidget(title_label)
        
        # Drop zone
        self._drop_zone = QFrame(self)
        self._drop_zone.setAcceptDrops(True)
        self._drop_zone.setMinimumHeight(120)
        self._drop_zone.dragEnterEvent = self._on_drag_enter
        self._drop_zone.dragLeaveEvent = self._on_drag_leave
        self._drop_zone.dropEvent = self._on_drop
        
        drop_layout = QVBoxLayout(self._drop_zone)
        drop_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        drop_layout.setSpacing(Spacing.SM)
        
        # Drop zone icon/text
        icon_label = QLabel("📁", self._drop_zone)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setFont(QFont("Segoe UI", 36))
        drop_layout.addWidget(icon_label)
        
        drop_text = QLabel("Drag & Drop Excel Files Here", self._drop_zone)
        drop_text.setAlignment(Qt.AlignCenter)
        drop_text.setFont(self._typography.create_font('body'))
        drop_layout.addWidget(drop_text)
        
        drop_hint = QLabel("(Multiple files supported)", self._drop_zone)
        drop_hint.setAlignment(Qt.AlignCenter)
        drop_hint.setFont(self._typography.create_font('body_sm'))
        drop_layout.addWidget(drop_hint)
        
        layout.addWidget(self._drop_zone)
        
        # Buttons row
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SM)
        
        browse_btn = PrimaryButton("Browse Files", self)
        browse_btn.setMinimumHeight(44)  # WCAG 2.1 AA
        browse_btn.clicked.connect(self._browse_files)
        button_layout.addWidget(browse_btn)
        
        clear_btn = SecondaryButton("Clear All", self)
        clear_btn.setMinimumHeight(44)
        clear_btn.clicked.connect(self.clear_files)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # File list
        list_label = QLabel("Selected Files:", self)
        list_label.setFont(self._typography.create_font('body'))
        layout.addWidget(list_label)
        
        self._file_list = QListWidget(self)
        self._file_list.setMinimumHeight(150)
        self._file_list.setFont(self._typography.create_font('body_sm'))
        self._file_list.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(self._file_list)
        
        # File list buttons
        file_btn_layout = QHBoxLayout()
        file_btn_layout.setSpacing(Spacing.SM)
        
        remove_btn = SecondaryButton("Remove Selected", self)
        remove_btn.setMinimumHeight(44)
        remove_btn.clicked.connect(self._remove_selected)
        file_btn_layout.addWidget(remove_btn)
        
        file_btn_layout.addStretch()
        layout.addLayout(file_btn_layout)
        
        # Recent operations section
        recent_label = QLabel("Recent Merge Operations:", self)
        recent_label.setFont(self._typography.create_font('body'))
        layout.addWidget(recent_label)
        
        self._recent_list = QListWidget(self)
        self._recent_list.setMaximumHeight(100)
        self._recent_list.setFont(self._typography.create_font('body_sm'))
        self._recent_list.itemDoubleClicked.connect(self._on_recent_operation_clicked)
        layout.addWidget(self._recent_list)
        
        # Load recent operations
        self._load_recent_operations()
    
    def _apply_styles(self):
        """Apply theme-aware styles."""
        colors = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
        bg_color = colors['background']
        border_color = colors['border']
        text_color = colors['text_primary']
        hover_bg = colors['surface_hover']
        primary = colors['primary']

        # Drop zone styles
        self._drop_zone.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px dashed {border_color};
                border-radius: {BorderRadius.MD}px;
            }}
            QFrame:hover {{
                border-color: {primary};
            }}
        """)

        # File list styles
        self._file_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {BorderRadius.SM}px;
                padding: {Spacing.SM}px;
                color: {text_color};
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px;
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

        # Recent list styles
        self._recent_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: {BorderRadius.SM}px;
                padding: {Spacing.SM}px;
                color: {text_color};
            }}
            QListWidget::item {{
                padding: {Spacing.SM}px;
                border-radius: {BorderRadius.SM}px;
            }}
            QListWidget::item:hover {{
                background-color: {hover_bg};
            }}
        """)
    
    def _browse_files(self):
        """Open file browser dialog for multiple file selection."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Excel Files",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        
        if file_paths:
            for file_path in file_paths:
                self._add_file(file_path)
    
    def _on_drag_enter(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            # Check if any URL is an Excel file
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self._is_valid_excel_file(file_path):
                    event.acceptProposedAction()
                    # Visual feedback
                    _c = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
                    self._drop_zone.setStyleSheet(f"""
                        QFrame {{
                            background-color: {_c['surface_hover']};
                            border: 2px solid {_c['primary']};
                            border-radius: {BorderRadius.MD}px;
                        }}
                    """)
                    return
    
    def _on_drag_leave(self, event):
        """Handle drag leave event."""
        self._apply_styles()
    
    def _on_drop(self, event: QDropEvent):
        """Handle drop event."""
        self._apply_styles()
        
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self._is_valid_excel_file(file_path):
                    self._add_file(file_path)
            event.acceptProposedAction()
    
    def _is_valid_excel_file(self, file_path: str) -> bool:
        """
        Check if file is a valid Excel file.
        
        Args:
            file_path: Path to file
        
        Returns:
            bool: True if valid Excel file
        """
        path = Path(file_path)
        return path.exists() and path.suffix.lower() in ['.xlsx', '.xls']
    
    def _add_file(self, file_path: str):
        """
        Add a file to the list.
        
        Args:
            file_path: Path to file
        """
        if not self._is_valid_excel_file(file_path):
            return
        
        # Normalize path
        file_path = str(Path(file_path).resolve())
        
        # Check if already added
        if file_path in self._file_paths:
            return
        
        # Add to list
        self._file_paths.append(file_path)
        
        # Update display
        file_name = Path(file_path).name
        item = QListWidgetItem(f"📄 {file_name}")
        item.setData(Qt.UserRole, file_path)
        item.setToolTip(file_path)
        self._file_list.addItem(item)
        
        # Emit signals
        self.files_changed.emit(self._file_paths)
        self.file_loaded.emit(file_path)
    
    def _remove_selected(self):
        """Remove selected file from list."""
        current_item = self._file_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.UserRole)
            if file_path in self._file_paths:
                self._file_paths.remove(file_path)
            
            row = self._file_list.row(current_item)
            self._file_list.takeItem(row)
            
            self.files_changed.emit(self._file_paths)
    
    def _load_recent_operations(self):
        """Load and display recent merge operations."""
        self._recent_list.clear()
        
        recent_ops = self._recent_manager.get_recent_operations(limit=5)
        
        if not recent_ops:
            item = QListWidgetItem("No recent operations")
            item.setFlags(Qt.NoItemFlags)  # Make it non-selectable
            self._recent_list.addItem(item)
            return
        
        for op in recent_ops:
            file_names = op.get('file_names', [])
            output_name = op.get('output_name', 'Unknown')
            
            # Create display text
            files_text = ", ".join(file_names[:2])
            if len(file_names) > 2:
                files_text += f" +{len(file_names) - 2} more"
            
            display_text = f"🔄 {files_text} → {output_name}"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, op)
            item.setToolTip(f"Double-click to load these files\nOutput: {op.get('output_path', '')}")
            self._recent_list.addItem(item)
    
    def _on_recent_operation_clicked(self, item: QListWidgetItem):
        """Handle recent operation double-click."""
        op = item.data(Qt.UserRole)
        if op:
            file_paths = op.get('file_paths', [])
            # Clear current files
            self.clear_files()
            # Load files from operation
            for file_path in file_paths:
                if Path(file_path).exists():
                    self._add_file(file_path)
    
    def get_file_paths(self) -> List[str]:
        """
        Get list of selected file paths.
        
        Returns:
            List[str]: File paths
        """
        return self._file_paths.copy()
    
    def clear_files(self):
        """Clear all files from list."""
        self._file_paths.clear()
        self._file_list.clear()
        self.files_changed.emit(self._file_paths)
    
    def set_files(self, file_paths: List[str]):
        """
        Set file list programmatically.
        
        Args:
            file_paths: List of file paths to set
        """
        self.clear_files()
        for file_path in file_paths:
            self._add_file(file_path)
    
    def set_theme_mode(self, mode: str):
        """
        Update theme mode.
        
        Args:
            mode: Theme mode ('light' or 'dark')
        """
        self._theme_mode = mode
        self._apply_styles()


# Export
__all__ = ['FileListWidget']

# Made with Bob