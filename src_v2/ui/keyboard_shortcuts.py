"""
Keyboard Shortcuts System - Centralized Shortcut Management
============================================================

This module provides a centralized keyboard shortcuts system for the application.
Manages global and tool-specific shortcuts with conflict detection and help dialog.

Features:
- ShortcutManager: Central manager for all shortcuts
- ShortcutRegistry: Organizes shortcuts by category
- ShortcutHelpDialog: Shows available shortcuts to users
- Conflict detection to prevent duplicate shortcuts
- Enable/disable shortcuts dynamically
- Integration with design system and typography

Global Shortcuts:
- Ctrl+Q: Quit application
- Ctrl+W: Close current window
- Ctrl+,: Open settings
- Ctrl+H: Open help
- Ctrl+M: Return to main menu
- F1: Context-sensitive help

Usage:
    from ui.keyboard_shortcuts import ShortcutManager
    
    # Initialize in your window
    self._shortcut_manager = ShortcutManager(self)
    
    # Register global shortcuts
    self._shortcut_manager.register_global_shortcuts()
    
    # Show help dialog
    self._shortcut_manager.show_help_dialog()
"""

from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtGui import QKeySequence, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QWidget, QScrollArea, QFrame,
    QShortcut, QApplication
)

from ui.design_system import Colors, Spacing, BorderRadius, Shadows
from ui.typography import TypographySystem, FontSizePreset
from ui.services import get_v2_settings_bus


class ShortcutCategory(Enum):
    """Categories for organizing shortcuts."""
    GLOBAL = "Global"
    NAVIGATION = "Navigation"
    FILE = "File Operations"
    EDIT = "Editing"
    VIEW = "View"
    TOOL_SPECIFIC = "Tool Specific"


@dataclass
class ShortcutDefinition:
    """Definition of a keyboard shortcut."""
    key_sequence: str  # e.g., "Ctrl+Q"
    description: str
    category: ShortcutCategory
    action: Optional[Callable] = None
    enabled: bool = True
    tool_id: Optional[str] = None  # For tool-specific shortcuts


class ShortcutRegistry:
    """
    Registry for organizing and managing shortcuts.
    
    Provides methods to register, retrieve, and validate shortcuts.
    Detects conflicts and organizes shortcuts by category.
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._shortcuts: Dict[str, ShortcutDefinition] = {}
        self._conflicts: List[Tuple[str, str]] = []
    
    def register(self, shortcut_id: str, definition: ShortcutDefinition) -> bool:
        """
        Register a shortcut.
        
        Args:
            shortcut_id: Unique identifier for the shortcut
            definition: Shortcut definition
            
        Returns:
            True if registered successfully, False if conflict detected
        """
        # Check for conflicts
        for existing_id, existing_def in self._shortcuts.items():
            if existing_def.key_sequence == definition.key_sequence:
                if existing_def.enabled and definition.enabled:
                    self._conflicts.append((shortcut_id, existing_id))
                    return False
        
        self._shortcuts[shortcut_id] = definition
        return True
    
    def unregister(self, shortcut_id: str) -> bool:
        """
        Unregister a shortcut.
        
        Args:
            shortcut_id: Shortcut identifier
            
        Returns:
            True if unregistered, False if not found
        """
        if shortcut_id in self._shortcuts:
            del self._shortcuts[shortcut_id]
            return True
        return False
    
    def get(self, shortcut_id: str) -> Optional[ShortcutDefinition]:
        """Get shortcut definition by ID."""
        return self._shortcuts.get(shortcut_id)
    
    def get_by_category(self, category: ShortcutCategory) -> Dict[str, ShortcutDefinition]:
        """Get all shortcuts in a category."""
        return {
            sid: sdef for sid, sdef in self._shortcuts.items()
            if sdef.category == category
        }
    
    def get_all(self) -> Dict[str, ShortcutDefinition]:
        """Get all registered shortcuts."""
        return self._shortcuts.copy()
    
    def has_conflicts(self) -> bool:
        """Check if there are any conflicts."""
        return len(self._conflicts) > 0
    
    def get_conflicts(self) -> List[Tuple[str, str]]:
        """Get list of conflicting shortcut pairs."""
        return self._conflicts.copy()
    
    def enable(self, shortcut_id: str) -> bool:
        """Enable a shortcut."""
        if shortcut_id in self._shortcuts:
            self._shortcuts[shortcut_id].enabled = True
            return True
        return False
    
    def disable(self, shortcut_id: str) -> bool:
        """Disable a shortcut."""
        if shortcut_id in self._shortcuts:
            self._shortcuts[shortcut_id].enabled = False
            return True
        return False


class ShortcutHelpDialog(QDialog):
    """
    Dialog showing all available keyboard shortcuts.
    
    Displays shortcuts organized by category with modern styling.
    Integrates with design system and typography.
    """
    
    def __init__(self, registry: ShortcutRegistry, parent: Optional[QWidget] = None):
        """
        Initialize help dialog.
        
        Args:
            registry: Shortcut registry to display
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._registry = registry
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        
        # Connect to settings bus
        try:
            self._settings_bus = get_v2_settings_bus()
            self._theme_mode = self._settings_bus.theme
            self._settings_bus.theme_changed.connect(self._on_theme_changed)
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in ShortcutHelpDialog: {e}")
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up dialog UI."""
        self.setWindowTitle("Keyboard Shortcuts - ART Q Master V2")
        self.resize(800, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        main_layout.setSpacing(Spacing.MD)
        
        # Header
        header = QLabel("Keyboard Shortcuts")
        header.setObjectName("dialogTitle")
        self._typography.apply_to_widget(header, 'h2')
        main_layout.addWidget(header)
        
        subtitle = QLabel("Use these shortcuts to navigate and control the application efficiently")
        subtitle.setObjectName("dialogSubtitle")
        self._typography.apply_to_widget(subtitle, 'body')
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)
        
        # Scroll area for shortcuts
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(Spacing.LG)
        
        # Group shortcuts by category
        categories = [
            ShortcutCategory.GLOBAL,
            ShortcutCategory.NAVIGATION,
            ShortcutCategory.FILE,
            ShortcutCategory.EDIT,
            ShortcutCategory.VIEW,
            ShortcutCategory.TOOL_SPECIFIC,
        ]
        
        for category in categories:
            shortcuts = self._registry.get_by_category(category)
            if shortcuts:
                category_widget = self._build_category_section(category, shortcuts)
                scroll_layout.addWidget(category_widget)
        
        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.setSpacing(Spacing.SM)
        button_layout.addStretch(1)
        
        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(120)
        self._typography.apply_to_widget(close_btn, 'button')
        button_layout.addWidget(close_btn)
        
        main_layout.addLayout(button_layout)
    
    def _build_category_section(
        self, 
        category: ShortcutCategory, 
        shortcuts: Dict[str, ShortcutDefinition]
    ) -> QFrame:
        """Build a section for a shortcut category."""
        frame = QFrame()
        frame.setObjectName("shortcutCategory")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)
        
        # Category title
        title = QLabel(category.value)
        title.setObjectName("categoryTitle")
        self._typography.apply_to_widget(title, 'h3')
        layout.addWidget(title)
        
        # Shortcuts in this category
        for shortcut_id, shortcut_def in shortcuts.items():
            if shortcut_def.enabled:
                shortcut_row = self._build_shortcut_row(
                    shortcut_def.key_sequence,
                    shortcut_def.description
                )
                layout.addWidget(shortcut_row)
        
        return frame
    
    def _build_shortcut_row(self, key_sequence: str, description: str) -> QWidget:
        """Build a row showing a single shortcut."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, Spacing.XS, 0, Spacing.XS)
        layout.setSpacing(Spacing.MD)
        
        # Key sequence (styled as badge)
        key_label = QLabel(key_sequence)
        key_label.setObjectName("shortcutKey")
        key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_label.setMinimumWidth(120)
        self._typography.apply_to_widget(key_label, 'button')
        layout.addWidget(key_label)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("shortcutDescription")
        self._typography.apply_to_widget(desc_label, 'body')
        layout.addWidget(desc_label, 1)
        
        return widget
    
    def _apply_style(self) -> None:
        """Apply theme-aware styling."""
        colors = Colors.DARK if self._theme_mode == "dark" else Colors.LIGHT
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background']};
            }}
            
            QLabel#dialogTitle {{
                color: {colors['text_primary']};
                font-weight: 600;
            }}
            
            QLabel#dialogSubtitle {{
                color: {colors['text_secondary']};
            }}
            
            QFrame#shortcutCategory {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
            
            QLabel#categoryTitle {{
                color: {colors['text_primary']};
                font-weight: 600;
                padding-bottom: {Spacing.XS}px;
            }}
            
            QLabel#shortcutKey {{
                background-color: {colors['primary']};
                color: {colors['text_inverse']};
                border-radius: {BorderRadius.SM}px;
                padding: {Spacing.XS}px {Spacing.SM}px;
                font-weight: 600;
            }}
            
            QLabel#shortcutDescription {{
                color: {colors['text_primary']};
            }}
            
            QPushButton#primaryButton {{
                background-color: {colors['primary']};
                color: {colors['text_inverse']};
                border: none;
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px {Spacing.LG}px;
                font-weight: 600;
            }}
            
            QPushButton#primaryButton:hover {{
                background-color: {colors['primary_hover']};
            }}
            
            QPushButton#primaryButton:pressed {{
                background-color: {colors['primary_active']};
            }}
            
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
    
    def _on_theme_changed(self, theme: str) -> None:
        """Handle theme change."""
        self._theme_mode = theme
        self._apply_style()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            # Reapply typography to all widgets
            for label in self.findChildren(QLabel):
                obj_name = label.objectName()
                if obj_name == "dialogTitle":
                    self._typography.apply_to_widget(label, 'h2')
                elif obj_name == "dialogSubtitle":
                    self._typography.apply_to_widget(label, 'body')
                elif obj_name == "categoryTitle":
                    self._typography.apply_to_widget(label, 'h3')
                elif obj_name in ("shortcutKey", "shortcutDescription"):
                    self._typography.apply_to_widget(label, 'body')
            
            for button in self.findChildren(QPushButton):
                self._typography.apply_to_widget(button, 'button')
        except Exception as e:
            print(f"Warning: Could not update font preset in help dialog: {e}")


class ShortcutManager:
    """
    Central manager for keyboard shortcuts.
    
    Manages registration, activation, and help display for all shortcuts.
    Provides methods to register global and tool-specific shortcuts.
    """
    
    def __init__(self, parent: QWidget):
        """
        Initialize shortcut manager.
        
        Args:
            parent: Parent widget (usually main window)
        """
        self._parent = parent
        self._registry = ShortcutRegistry()
        self._qshortcuts: Dict[str, QShortcut] = {}
    
    def register_global_shortcuts(self) -> None:
        """Register all global application shortcuts."""
        # Ctrl+Q: Quit application
        self.register_shortcut(
            "global_quit",
            ShortcutDefinition(
                key_sequence="Ctrl+Q",
                description="Quit application",
                category=ShortcutCategory.GLOBAL,
                action=self._quit_application
            )
        )
        
        # Ctrl+W: Close current window
        self.register_shortcut(
            "global_close_window",
            ShortcutDefinition(
                key_sequence="Ctrl+W",
                description="Close current window",
                category=ShortcutCategory.GLOBAL,
                action=self._close_window
            )
        )
        
        # Ctrl+,: Open settings
        self.register_shortcut(
            "global_settings",
            ShortcutDefinition(
                key_sequence="Ctrl+,",
                description="Open settings",
                category=ShortcutCategory.GLOBAL,
                action=self._open_settings
            )
        )
        
        # Ctrl+H: Open help
        self.register_shortcut(
            "global_help",
            ShortcutDefinition(
                key_sequence="Ctrl+H",
                description="Open help documentation",
                category=ShortcutCategory.GLOBAL,
                action=self._open_help
            )
        )
        
        # Ctrl+M: Return to main menu
        self.register_shortcut(
            "global_main_menu",
            ShortcutDefinition(
                key_sequence="Ctrl+M",
                description="Return to main menu",
                category=ShortcutCategory.GLOBAL,
                action=self._return_to_main_menu
            )
        )
        
        # F1: Context-sensitive help
        self.register_shortcut(
            "global_context_help",
            ShortcutDefinition(
                key_sequence="F1",
                description="Show keyboard shortcuts",
                category=ShortcutCategory.GLOBAL,
                action=self.show_help_dialog
            )
        )
    
    def register_shortcut(self, shortcut_id: str, definition: ShortcutDefinition) -> bool:
        """
        Register a shortcut and activate it.
        
        Args:
            shortcut_id: Unique identifier
            definition: Shortcut definition
            
        Returns:
            True if registered successfully
        """
        # Register in registry
        if not self._registry.register(shortcut_id, definition):
            print(f"Warning: Shortcut conflict detected for {shortcut_id}")
            return False
        
        # Create QShortcut if action is provided
        if definition.action and definition.enabled:
            qshortcut = QShortcut(QKeySequence(definition.key_sequence), self._parent)
            qshortcut.activated.connect(definition.action)
            self._qshortcuts[shortcut_id] = qshortcut
        
        return True
    
    def unregister_shortcut(self, shortcut_id: str) -> bool:
        """
        Unregister a shortcut.
        
        Args:
            shortcut_id: Shortcut identifier
            
        Returns:
            True if unregistered successfully
        """
        # Remove QShortcut
        if shortcut_id in self._qshortcuts:
            self._qshortcuts[shortcut_id].setEnabled(False)
            del self._qshortcuts[shortcut_id]
        
        # Remove from registry
        return self._registry.unregister(shortcut_id)
    
    def enable_shortcut(self, shortcut_id: str) -> bool:
        """Enable a shortcut."""
        if self._registry.enable(shortcut_id):
            if shortcut_id in self._qshortcuts:
                self._qshortcuts[shortcut_id].setEnabled(True)
            return True
        return False
    
    def disable_shortcut(self, shortcut_id: str) -> bool:
        """Disable a shortcut."""
        if self._registry.disable(shortcut_id):
            if shortcut_id in self._qshortcuts:
                self._qshortcuts[shortcut_id].setEnabled(False)
            return True
        return False
    
    def show_help_dialog(self) -> None:
        """Show keyboard shortcuts help dialog."""
        dialog = ShortcutHelpDialog(self._registry, self._parent)
        dialog.exec_()
    
    def get_registry(self) -> ShortcutRegistry:
        """Get the shortcut registry."""
        return self._registry
    
    # Action handlers for global shortcuts
    
    def _quit_application(self) -> None:
        """Quit the application."""
        app = QApplication.instance()
        if app:
            app.quit()
    
    def _close_window(self) -> None:
        """Close the current window."""
        if self._parent:
            self._parent.close()
    
    def _open_settings(self) -> None:
        """Open settings dialog."""
        try:
            from ui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self._parent)
            dialog.exec_()
        except Exception as e:
            print(f"Error opening settings: {e}")
    
    def _open_help(self) -> None:
        """Open help documentation."""
        # For now, show the shortcuts dialog
        # In the future, this could open external documentation
        self.show_help_dialog()
    
    def _return_to_main_menu(self) -> None:
        """Return to main menu."""
        # Close current window and show main menu
        if self._parent:
            # Check if this is already the main menu
            if hasattr(self._parent, '__class__') and 'MainMenu' in self._parent.__class__.__name__:
                return  # Already at main menu
            
            # Close current window
            self._parent.close()
            
            # Show main menu if it exists
            app = QApplication.instance()
            if app and hasattr(app, '_art_q_v2_main_menu'):
                main_menu = getattr(app, '_art_q_v2_main_menu')
                if main_menu:
                    main_menu.show()
                    main_menu.raise_()
                    main_menu.activateWindow()


# Made with Bob