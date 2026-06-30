"""
Unified Phase 6 UI shell for src_v2.

This module defines the first shared application shell that all v2 tools can
use. It is intentionally lightweight and safe to evolve while the current
production implementation remains untouched in `src/`.
"""

from typing import Iterable, List, Optional, Tuple

from version import version_label, footer_label, version_tag, __version__
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QResizeEvent, QFont
from PyQt5.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.services import V2ThemeService, get_v2_settings_bus
from ui.typography import TypographySystem, FontSizePreset
from ui.keyboard_shortcuts import ShortcutManager
from ui.accessibility_helper import get_accessibility_manager
from ui.components_v2 import SearchBar, CompactToolCard, EnhancedToolCard, ProfileButton
from utils.tool_launcher import can_launch_tool, launch_tool
from utils.tool_registry import get_tool_definition, get_tool_status_map
from utils.recent_tools import get_recent_tools_manager
from utils.error_logger import log


ToolCard = Tuple[str, str, str]


class ToolPlaceholderDialog(QDialog):
    """Shared placeholder dialog for v2 tools until full migrations are wired."""

    def __init__(self, tool_id: str, parent=None):
        super().__init__(parent)
        self._tool_id = tool_id
        self._settings_bus = get_v2_settings_bus()
        self._theme_service = V2ThemeService()
        self._tool_status_map = get_tool_status_map()
        self._current_theme = self._settings_bus.theme
        self._current_font_size = self._settings_bus.font_size
        
        # Initialize typography system
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        
        # Initialize accessibility manager
        self._accessibility = get_accessibility_manager()

        self._settings_bus.theme_changed.connect(self._on_theme_changed)
        self._settings_bus.font_size_changed.connect(self._on_font_size_changed)
        self._settings_bus.font_preset_changed.connect(self._on_preset_changed)

        self._build_ui()
        self._apply_current_style()
        self._setup_accessibility()
    
    def _setup_accessibility(self):
        """Setup accessibility features for dialog."""
        # Apply accessibility to dialog
        self._accessibility.apply_to_widget(self)
        
        # Set ARIA labels
        definition = get_tool_definition(self._tool_id)
        self._accessibility.set_aria_label(
            self,
            f"{definition.display_name} Tool Dialog",
            f"Dialog for {definition.display_name} tool with status {definition.status}"
        )

    def _build_ui(self) -> None:
        definition = get_tool_definition(self._tool_id)
        self.setWindowTitle(f"{definition.display_name} — {version_label}")
        self.resize(920, 620)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(18)

        card = QFrame()
        card.setObjectName("dialogCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(18)

        title = QLabel(definition.display_name)
        title.setObjectName("dialogTitle")

        subtitle = QLabel(f"Status: {definition.status}  •  Area: {definition.area}")
        subtitle.setObjectName("dialogSubtitle")

        launch_state = (
            "This tool has a confirmed production launcher and can be opened from the v2 shell."
            if can_launch_tool(self._tool_id)
            else "This tool remains pending until its exact production startup path is confirmed."
        )
        body = QLabel(
            f"{definition.description}\n\n"
            f"{launch_state}\n"
            "The v2 workspace keeps current production logic intact while migration continues."
        )
        body.setObjectName("dialogBody")
        body.setWordWrap(True)

        launch_legacy = QPushButton("Open current production tool")
        launch_legacy.setObjectName("primaryButton")
        launch_legacy.clicked.connect(self._launch_tool)
        launch_legacy.setEnabled(can_launch_tool(self._tool_id))

        close_button = QPushButton("Close")
        close_button.setObjectName("secondaryButton")
        close_button.clicked.connect(self.accept)

        actions = QHBoxLayout()
        actions.setSpacing(12)
        actions.addWidget(launch_legacy)
        actions.addWidget(close_button)
        actions.addStretch(1)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(body)
        card_layout.addLayout(actions)

        root.addWidget(card)

    def resizeEvent(self, a0: Optional[QResizeEvent]) -> None:
        # Keep responsive sizing for backward compatibility
        responsive_size = self._settings_bus.calculate_responsive_font_size(self.width(), self.height())
        if responsive_size != self._current_font_size:
            self._current_font_size = responsive_size
            self._apply_current_style()
        super().resizeEvent(a0)
    
    def _on_preset_changed(self, preset: str):
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            self._apply_typography()
        except Exception as e:
            print(f"Warning: Could not update font preset in dialog: {e}")
    
    def _apply_typography(self):
        """Apply typography to dialog elements."""
        try:
            # Apply to title
            if hasattr(self, 'findChildren'):
                for label in self.findChildren(QLabel):
                    obj_name = label.objectName()
                    if obj_name == "dialogTitle":
                        self._typography.apply_to_widget(label, 'h2')
                    elif obj_name == "dialogSubtitle":
                        self._typography.apply_to_widget(label, 'body')
                    elif obj_name == "dialogBody":
                        self._typography.apply_to_widget(label, 'body')
                
                # Apply to buttons
                for button in self.findChildren(QPushButton):
                    self._typography.apply_to_widget(button, 'button')
        except Exception as e:
            print(f"Warning: Could not apply typography to dialog: {e}")

    def _apply_current_style(self) -> None:
        self.setStyleSheet(
            self._theme_service.build_tool_dialog_stylesheet(
                self._current_theme,
                self._current_font_size,
            )
        )

    def _on_theme_changed(self, theme: str) -> None:
        self._current_theme = theme
        self._apply_current_style()

    def _on_font_size_changed(self, font_size: int) -> None:
        self._current_font_size = font_size
        self._apply_current_style()

    def _launch_tool(self) -> None:
        definition = get_tool_definition(self._tool_id)
        try:
            result = launch_tool(self._tool_id)
        except Exception as exc:
            QMessageBox.critical(
                self,
                definition.display_name,
                f"Failed to launch the current production tool.\n\n{exc}",
            )
            return

        if result.launched:
            self.accept()
            return

        QMessageBox.information(
            self,
            definition.display_name,
            result.message,
        )


class UnifiedToolShell(QMainWindow):
    """Common Phase 6 shell for all v2 tools."""

    def __init__(
        self,
        title: str = "ART Q Master V2",
        subtitle: str = "Unified tool experience",
        tools: Optional[Iterable[ToolCard]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._title_text = title
        self._subtitle_text = subtitle
        self._tools: List[ToolCard] = list(tools or [])
        self._tool_buttons: List[QPushButton] = []
        self._tool_cards: dict = {}  # Store cards for filtering
        self._settings_bus = get_v2_settings_bus()
        self._theme_service = V2ThemeService()
        self._tool_status_map = get_tool_status_map()
        self._current_theme = self._settings_bus.theme
        self._current_font_size = self._settings_bus.font_size
        
        # Initialize typography system with saved preset
        saved_preset = self._load_saved_preset()
        self._typography = TypographySystem(saved_preset)
        
        # Initialize keyboard shortcuts manager
        self._shortcut_manager = ShortcutManager(self)
        self._shortcut_manager.register_global_shortcuts()
        
        # Initialize accessibility manager
        self._accessibility = get_accessibility_manager()
        
        # Initialize recent tools manager
        self._recent_tools_manager = get_recent_tools_manager()
        
        self._settings_bus.theme_changed.connect(self._on_theme_changed)
        self._settings_bus.font_size_changed.connect(self._on_font_size_changed)
        self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        self._build_ui()
        
        # Apply saved preset after UI is built
        self._apply_typography()
        
        # Setup accessibility after UI is built
        self._setup_accessibility()
    
    def _setup_accessibility(self):
        """Setup WCAG 2.1 AA compliant accessibility features."""
        # Apply accessibility to entire shell
        self._accessibility.apply_to_widget(self)
        
        # Set ARIA labels for main window
        self._accessibility.set_aria_label(
            self,
            self._title_text,
            f"{self._subtitle_text}. Use Tab to navigate between tools."
        )
        
        # Setup keyboard navigation
        self._accessibility.setup_keyboard_navigation(self)
        
        # Apply ARIA labels to tool buttons
        for button in self._tool_buttons:
            tool_name = button.text()
            self._accessibility.set_aria_label(
                button,
                f"{tool_name} Tool",
                f"Launch {tool_name} tool"
            )

    def _build_ui(self) -> None:
        self.setWindowTitle(f"{self._title_text}  —  {version_tag}")
        self.resize(1380, 900)

        central = QWidget(self)
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        header = self._build_header()
        root.addWidget(header)

        content = self._build_content()
        root.addWidget(content, 1)

        footer = self._build_footer()
        root.addWidget(footer)

        self._update_responsive_typography()
        self._apply_current_style()

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(26, 26, 26, 26)
        layout.setSpacing(10)

        # Top row: Welcome message + profile + settings + help
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Welcome message with agent name from config
        agent_name = self._load_agent_name()
        welcome = QLabel(f"Welcome back, {agent_name}!")
        welcome.setObjectName("welcomeLabel")
        top_row.addWidget(welcome)

        top_row.addStretch()

        # Profile button
        profile_btn = ProfileButton()
        profile_btn.profileClicked.connect(self._view_profile)
        profile_btn.settingsClicked.connect(self._open_settings)
        profile_btn.signOutClicked.connect(self._sign_out)
        top_row.addWidget(profile_btn)

        # Settings button
        settings_btn = QPushButton("⚙️")
        settings_btn.setObjectName("settingsButton")
        settings_btn.setToolTip("Open application settings\nShortcut: Ctrl+,")
        settings_btn.clicked.connect(self._open_settings)
        settings_btn.setFixedHeight(44)
        settings_btn.setFixedWidth(44)
        settings_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_row.addWidget(settings_btn)
        
        # Help button (F1)
        help_btn = QPushButton("❓")
        help_btn.setObjectName("helpButton")
        help_btn.setToolTip("Show keyboard shortcuts\nShortcut: F1")
        help_btn.clicked.connect(self._shortcut_manager.show_help_dialog)
        help_btn.setFixedHeight(44)
        help_btn.setFixedWidth(44)
        help_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        top_row.addWidget(help_btn)

        layout.addLayout(top_row)

        # Search bar
        self._search_bar = SearchBar()
        self._search_bar.textChanged.connect(self._filter_tools)
        layout.addWidget(self._search_bar)

        # Subtitle (if provided)
        if self._subtitle_text:
            subtitle = QLabel(self._subtitle_text)
            subtitle.setObjectName("subtitleLabel")
            subtitle.setWordWrap(True)
            layout.addWidget(subtitle)

        return frame

    def _build_content(self) -> QWidget:
        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.setSpacing(24)

        # Recent tools section (if any)
        recent_tools = self._get_recent_tools()
        if recent_tools:
            recent_section = self._build_recent_tools_section(recent_tools)
            wrapper_layout.addWidget(recent_section)

        # All Tools section - using same simple approach as Recent Tools
        if not self._tools:
            wrapper_layout.addWidget(
                self._build_empty_state(
                    "No v2 tools are registered yet.",
                    "Tool adapters will appear here as migration progresses.",
                )
            )
        else:
            all_tools_section = self._build_all_tools_section()
            wrapper_layout.addWidget(all_tools_section)

        wrapper_layout.addStretch(1)
        return wrapper

    def _load_agent_name(self) -> str:
        """Load agent name from unified config via ConfigManager."""
        try:
            from config.manager import get_config_manager
            name = get_config_manager().get("agent_settings.agent_name", "User")
            return name if name and name.strip() else "User"
        except Exception as e:
            print(f"Warning: Could not load agent name: {e}")
            return "User"

    def _get_recent_tools(self) -> List[str]:
        """Get recent tools from manager."""
        # Validate against current tools
        valid_ids = [tool_id for tool_id, _, _ in self._tools]
        self._recent_tools_manager.validate_tools(valid_ids)
        
        return self._recent_tools_manager.get_recent_tools(limit=3)

    def _build_recent_tools_section(self, recent_tool_ids: List[str]) -> QWidget:
        """Build recent tools section with compact cards."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        title = QLabel("Recent Tools")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Horizontal layout for compact cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)
        
        for tool_id in recent_tool_ids:
            # Find tool definition
            tool_def = get_tool_definition(tool_id)
            
            # Create compact card
            card = CompactToolCard(
                tool_id=tool_id,
                tool_name=tool_def.display_name,
                icon=tool_def.icon
            )
            card.clicked.connect(self._on_tool_launched)
            cards_layout.addWidget(card)
        
        cards_layout.addStretch(1)
        layout.addLayout(cards_layout)
        
        return section
    
    def _build_all_tools_section(self) -> QWidget:
        """Build all tools section with enhanced cards in a grid (2x3 or 3x2)."""
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        title = QLabel("All Tools")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Grid layout for enhanced cards (2 columns)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(16)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        row = 0
        col = 0
        
        for tool_id, name, description in self._tools:
            tool_def = get_tool_definition(tool_id)
            
            # Create enhanced card
            card = EnhancedToolCard(
                tool_id=tool_id,
                tool_name=tool_def.display_name,
                description=tool_def.description,
                icon=tool_def.icon
            )
            card.clicked.connect(self._on_tool_launched)
            
            # Store card for filtering
            self._tool_cards[tool_id] = card
            
            # Add to grid
            grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 2:  # 2 columns
                col = 0
                row += 1
        
        layout.addLayout(grid_layout)
        
        return section


    def _filter_tools(self, search_text: str):
        """Filter tools based on search text."""
        search_lower = search_text.lower().strip()
        
        # If search is empty, show all cards
        if not search_lower:
            for card in self._tool_cards.values():
                card.setVisible(True)
            return
        
        # Hide/show cards based on search
        for tool_id, card in self._tool_cards.items():
            tool_def = get_tool_definition(tool_id)
            tool_name = tool_def.display_name.lower()
            tool_desc = tool_def.description.lower()
            
            matches = search_lower in tool_name or search_lower in tool_desc
            card.setVisible(matches)

    def _on_tool_launched(self, tool_id: str):
        """Handle tool launch and track in recent tools."""
        # Track in recent tools
        self._recent_tools_manager.add_tool(tool_id)
        
        # Launch tool
        self.open_tool(tool_id)

    def _view_profile(self):
        """Handle view profile action."""
        from ui.components_v2 import Toast
        Toast.show_info(
            self,
            f"Profile: {self._load_agent_name()}",
            "Profile management coming soon"
        )

    def _sign_out(self):
        """Handle sign out action."""
        reply = QMessageBox.question(
            self,
            "Sign Out",
            "Are you sure you want to sign out?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.close()

    def _build_empty_state(self, title: str, description: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("emptyState")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("emptyTitle")

        description_label = QLabel(description)
        description_label.setObjectName("emptyDescription")
        description_label.setWordWrap(True)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        return frame

    def _build_footer(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("footerFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)

        left_label = QLabel(footer_label)
        left_label.setObjectName("footerLabel")
        layout.addWidget(left_label)

        layout.addStretch(1)

        version_badge = QLabel(__version__)
        version_badge.setObjectName("versionBadge")
        version_badge.setToolTip(f"Application version {__version__}")
        layout.addWidget(version_badge)

        return frame

    def set_tools(self, tools: Iterable[ToolCard]) -> None:
        """Replace the registered tools list."""
        self._tools = list(tools)
        self._tool_buttons.clear()

        old_central = self.centralWidget()
        if old_central is not None:
            old_central.deleteLater()

        self._build_ui()

    def resizeEvent(self, a0: Optional[QResizeEvent]) -> None:
        """Handle window resize for responsive grid."""
        self._update_responsive_typography()
        self._apply_current_style()
        
        # Adjust grid columns based on width
        if hasattr(self, '_tools_grid'):
            if self.width() < 800:
                # Switch to 1 column
                self._set_grid_columns(1)
            else:
                # Use 2 columns
                self._set_grid_columns(2)
        
        super().resizeEvent(a0)

    def _set_grid_columns(self, columns: int):
        """Reorganize grid to use specified number of columns."""
        if not hasattr(self, '_tools_grid') or not hasattr(self, '_tool_cards'):
            return
        
        # Collect all cards
        cards = []
        for tool_id in self._tool_cards:
            card = self._tool_cards[tool_id]
            if card.isVisible():  # Only reorganize visible cards
                cards.append(card)
        
        # Clear grid
        while self._tools_grid.count():
            item = self._tools_grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        # Re-add cards in new layout
        row = 0
        col = 0
        for card in cards:
            self._tools_grid.addWidget(card, row, col)
            col += 1
            if col >= columns:
                col = 0
                row += 1

    def _update_responsive_typography(self) -> None:
        self._current_font_size = self._settings_bus.calculate_responsive_font_size(
            self.width(),
            self.height(),
        )

    def open_tool(self, tool_id: str) -> None:
        """Open a tool using a confirmed launcher or the pending-state dialog."""
        if can_launch_tool(tool_id):
            try:
                result = launch_tool(tool_id)
            except Exception as exc:
                definition = get_tool_definition(tool_id)
                QMessageBox.critical(
                    self,
                    definition.display_name,
                    f"Failed to launch the current production tool.\n\n{exc}",
                )
                return

            if not result.launched:
                definition = get_tool_definition(tool_id)
                QMessageBox.information(self, definition.display_name, result.message)
            return

        dialog = ToolPlaceholderDialog(tool_id, self)
        dialog.exec_()

    def _open_settings(self) -> None:
        """Open settings dialog."""
        try:
            from ui.settings_dialog import SettingsDialog
            dialog = SettingsDialog(self)
            dialog.exec_()
        except Exception as e:
            print(f"Error opening settings: {e}")
            QMessageBox.warning(
                self,
                "Settings Error",
                f"Could not open settings dialog:\n{str(e)}"
            )

    def _apply_current_style(self) -> None:
        # Get current preset name
        preset_name = self._typography.preset.value
        self.setStyleSheet(
            self._theme_service.build_shell_stylesheet(
                self._current_theme,
                self._current_font_size,
                preset_name,
            )
        )

    def _on_theme_changed(self, theme: str) -> None:
        self._current_theme = theme
        self._apply_current_style()

    def _on_font_size_changed(self, font_size: int) -> None:
        self._current_font_size = max(20, font_size)
        self._apply_current_style()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            self._apply_typography()
            # Force update
            self.update()
        except Exception as e:
            print(f"Warning: Could not update font preset in shell: {e}")
    
    def _apply_typography(self):
        """Apply typography to shell UI elements."""
        try:
            # Apply to labels
            for label in self.findChildren(QLabel):
                obj_name = label.objectName()
                if obj_name == "welcomeLabel":
                    self._typography.apply_to_widget(label, 'h2')
                elif obj_name == "subtitleLabel":
                    self._typography.apply_to_widget(label, 'body')
                elif obj_name == "sectionTitle":
                    self._typography.apply_to_widget(label, 'h3')
                elif obj_name == "footerLabel":
                    self._typography.apply_to_widget(label, 'caption')
                elif obj_name == "emptyTitle":
                    self._typography.apply_to_widget(label, 'h3')
                elif obj_name == "emptyDescription":
                    self._typography.apply_to_widget(label, 'body')
            
            # Apply to buttons
            for button in self.findChildren(QPushButton):
                self._typography.apply_to_widget(button, 'button')
        except Exception as e:
            print(f"Warning: Could not apply typography to shell: {e}")
    
    def _load_saved_preset(self) -> FontSizePreset:
        """Load saved font preset from config file."""
        try:
            import json
            from pathlib import Path
            
            config_path = Path(__file__).parent.parent / "config.json"
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                saved_preset = config.get('ui_settings', {}).get('font_preset', 'normal')
                preset_enum = FontSizePreset.from_string(saved_preset)
                log("info", f"Shell loaded font preset from config: {saved_preset}", "Shell")
                return preset_enum
        except Exception as e:
            log("warn", f"Could not load preset from config: {e}", "Shell")
        
        return FontSizePreset.NORMAL
    
    def get_shortcut_manager(self) -> ShortcutManager:
        """
        Get the shortcut manager instance.

        Returns:
            ShortcutManager instance for this shell
        """
        return self._shortcut_manager

# Made with Bob
