"""
Card Components - Modern Card Containers (Phase 5.2 Enhanced)
==============================================================

This module provides modern card components following IBM Carbon Design principles.
Cards are versatile containers for grouping related content.

Card Variants:
- BaseCard: Foundation card class with common functionality
- Card: Default card with subtle background
- ElevatedCard: Card with shadow for depth
- OutlinedCard: Card with border emphasis

Phase 5.2 Enhancements:
- ✅ 3 card variants (Card, ElevatedCard, OutlinedCard)
- ✅ Collapsible/expandable functionality
- ✅ Action buttons in header (close, minimize, settings)
- ✅ Loading state with skeleton animation
- ✅ Hover effects (subtle elevation change)
- ✅ Proper spacing (8px grid)
- ✅ Footer section support

Features:
- Uses design_system.py for colors, spacing, shadows, borders
- Integrates with typography.py for font sizing
- Supports theme changes via V2SettingsBus
- Flexible content layout
- Optional title and actions
- Hover states for interactive cards
- Collapsible content with smooth animation
- Loading skeleton for async content

Usage:
    from ui.components_v2 import Card, ElevatedCard
    
    # Create basic card
    card = Card()
    card.set_title("My Card")
    card.set_content(my_widget)
    
    # Create collapsible card
    card = Card(collapsible=True)
    card.set_title("Collapsible Card")
    card.set_content(content_widget)
    card.set_collapsed(True)
    
    # Create card with actions
    card = ElevatedCard()
    card.set_title("Card with Actions")
    card.add_header_action("close", lambda: card.close())
    card.set_content(content_widget)
    card.set_footer(footer_widget)
"""

from typing import Optional, Callable
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt5.QtGui import QFont, QPainter, QColor, QLinearGradient, QPaintEvent
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QPushButton
)

from ui.design_system import Colors, Spacing, BorderRadius, Shadows, Animation
from ui.typography import TypographySystem, FontSizePreset
from .buttons import GhostButton


class BaseCard(QFrame):
    """
    Base card component with common functionality (Phase 5.2 Enhanced).
    
    Provides foundation for all card variants with:
    - Design system integration
    - Typography support
    - Theme awareness
    - Flexible layout
    - Collapsible functionality
    - Action buttons in header
    - Loading state with skeleton
    - Footer section support
    
    Attributes:
        _theme_mode: Current theme mode
        _typography: Typography system
        _layout: Main vertical layout
        _header_layout: Header layout with title and actions
        _title_label: Optional title label
        _content_widget: Content widget
        _footer_widget: Optional footer widget
        _is_collapsible: Whether card can be collapsed
        _is_collapsed: Whether card is currently collapsed
        _is_loading: Whether card is in loading state
        _action_buttons: Dictionary of action buttons
    """
    
    def __init__(
        self, 
        parent: Optional[QWidget] = None,
        collapsible: bool = False,
        hoverable: bool = False
    ):
        """
        Initialize base card.
        
        Args:
            parent: Parent widget
            collapsible: Whether card can be collapsed
            hoverable: Whether card has hover effects
        """
        super().__init__(parent)
        
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        
        self._title_label: Optional[QLabel] = None
        self._content_widget: Optional[QWidget] = None
        self._footer_widget: Optional[QWidget] = None
        self._content_container: Optional[QWidget] = None
        
        self._is_collapsible = collapsible
        self._is_collapsed = False
        self._is_loading = False
        self._hoverable = hoverable
        self._action_buttons = {}
        
        # Loading animation
        self._loading_timer: Optional[QTimer] = None
        self._loading_offset = 0
        
        # Connect to preset changes
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in BaseCard: {e}")
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up card UI structure."""
        # Main layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        
        # Header container (for title and actions)
        self._header_container = QWidget()
        self._header_layout = QHBoxLayout(self._header_container)
        self._header_layout.setContentsMargins(
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.SM
        )
        self._header_layout.setSpacing(Spacing.SM)
        
        # Content container (for collapsible animation)
        self._content_container = QWidget()
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(
            Spacing.CARD_PADDING,
            Spacing.SM,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING
        )
        self._content_layout.setSpacing(Spacing.COMPONENT_GAP)
        
        # Footer container (optional)
        self._footer_container = QWidget()
        self._footer_layout = QVBoxLayout(self._footer_container)
        self._footer_layout.setContentsMargins(
            Spacing.CARD_PADDING,
            0,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING
        )
        self._footer_layout.setSpacing(0)
        self._footer_container.hide()
        
        # Add containers to main layout
        self._layout.addWidget(self._header_container)
        self._layout.addWidget(self._content_container)
        self._layout.addWidget(self._footer_container)
        
        # Set up hover effects if enabled
        if self._hoverable:
            self.setMouseTracking(True)
    
    def _apply_style(self) -> None:
        """
        Apply card stylesheet.
        
        Override in subclasses to customize appearance.
        """
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
        """)
        
        # Apply header style
        self._header_container.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
            }}
        """)
        
        # Apply content container style
        if self._content_container:
            self._content_container.setStyleSheet(f"""
                QWidget {{
                    background-color: transparent;
                }}
            """)
        
        # Apply footer style
        self._footer_container.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border-top: 1px solid {colors['border']};
            }}
        """)
    
    def set_title(self, title: str) -> None:
        """
        Set card title.
        
        Args:
            title: Title text
        """
        if self._title_label is None:
            self._title_label = QLabel(title)
            self._typography.apply_to_widget(self._title_label, 'h3', QFont.Bold)
            self._header_layout.insertWidget(0, self._title_label, 1)
            
            # Add collapse button if collapsible
            if self._is_collapsible:
                self._collapse_button = GhostButton("▼")
                self._collapse_button.setMaximumWidth(32)
                self._collapse_button.setMaximumHeight(32)
                self._collapse_button.clicked.connect(self.toggle_collapsed)
                self._header_layout.insertWidget(0, self._collapse_button)
        else:
            self._title_label.setText(title)
        
        self._update_title_style()
    
    def _update_title_style(self) -> None:
        """Update title label style."""
        if self._title_label:
            colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
            self._title_label.setStyleSheet(f"""
                QLabel {{
                    color: {colors['text_primary']};
                    background-color: transparent;
                }}
            """)
    
    def add_header_action(
        self, 
        action_type: str, 
        callback: Callable[[], None],
        tooltip: str = ""
    ) -> None:
        """
        Add action button to card header.
        
        Args:
            action_type: Type of action ('close', 'minimize', 'settings', 'custom')
            callback: Function to call when button is clicked
            tooltip: Optional tooltip text
        """
        # Create action button
        button = GhostButton()
        button.setMaximumWidth(32)
        button.setMaximumHeight(32)
        
        # Set button icon/text based on type
        if action_type == "close":
            button.setText("✕")
        elif action_type == "minimize":
            button.setText("−")
        elif action_type == "settings":
            button.setText("⚙")
        else:
            button.setText("•")
        
        if tooltip:
            button.setToolTip(tooltip)
        
        button.clicked.connect(callback)
        
        # Add to header layout
        self._header_layout.addWidget(button)
        self._action_buttons[action_type] = button
    
    def remove_header_action(self, action_type: str) -> None:
        """
        Remove action button from header.
        
        Args:
            action_type: Type of action to remove
        """
        if action_type in self._action_buttons:
            button = self._action_buttons[action_type]
            self._header_layout.removeWidget(button)
            button.deleteLater()
            del self._action_buttons[action_type]
    
    def set_content(self, widget: QWidget) -> None:
        """
        Set card content widget.
        
        Args:
            widget: Content widget to display
        """
        # Remove old content if exists
        if self._content_widget is not None:
            self._content_layout.removeWidget(self._content_widget)
            self._content_widget.deleteLater()
        
        self._content_widget = widget
        self._content_layout.addWidget(widget)
    
    def set_footer(self, widget: QWidget) -> None:
        """
        Set card footer widget.
        
        Args:
            widget: Footer widget to display
        """
        # Remove old footer if exists
        if self._footer_widget is not None:
            self._footer_layout.removeWidget(self._footer_widget)
            self._footer_widget.deleteLater()
        
        self._footer_widget = widget
        self._footer_layout.addWidget(widget)
        self._footer_container.show()
    
    def remove_footer(self) -> None:
        """Remove footer widget."""
        if self._footer_widget is not None:
            self._footer_layout.removeWidget(self._footer_widget)
            self._footer_widget.deleteLater()
            self._footer_widget = None
            self._footer_container.hide()
    
    def set_collapsed(self, collapsed: bool) -> None:
        """
        Set card collapsed state.
        
        Args:
            collapsed: Whether card should be collapsed
        """
        if not self._is_collapsible:
            return
        
        self._is_collapsed = collapsed
        
        # Update collapse button icon
        if hasattr(self, '_collapse_button'):
            self._collapse_button.setText("▶" if collapsed else "▼")
        
        # Animate content visibility
        if collapsed:
            if self._content_container:
                self._content_container.hide()
            self._footer_container.hide()
        else:
            if self._content_container:
                self._content_container.show()
            if self._footer_widget:
                self._footer_container.show()
    
    def toggle_collapsed(self) -> None:
        """Toggle card collapsed state."""
        self.set_collapsed(not self._is_collapsed)
    
    def is_collapsed(self) -> bool:
        """
        Check if card is collapsed.
        
        Returns:
            bool: True if collapsed, False otherwise
        """
        return self._is_collapsed
    
    def set_loading(self, loading: bool) -> None:
        """
        Set card loading state.
        
        When loading, shows animated skeleton instead of content.
        
        Args:
            loading: Whether card should show loading state
        """
        self._is_loading = loading
        
        if loading:
            # Start loading animation
            if not self._loading_timer:
                self._loading_timer = QTimer(self)
                self._loading_timer.timeout.connect(self._update_loading_animation)
            self._loading_timer.start(50)  # 20 FPS
            
            # Hide content, show skeleton
            if self._content_widget:
                self._content_widget.hide()
        else:
            # Stop loading animation
            if self._loading_timer:
                self._loading_timer.stop()
            self._loading_offset = 0
            
            # Show content
            if self._content_widget:
                self._content_widget.show()
        
        self.update()
    
    def is_loading(self) -> bool:
        """
        Check if card is in loading state.
        
        Returns:
            bool: True if loading, False otherwise
        """
        return self._is_loading
    
    def _update_loading_animation(self) -> None:
        """Update loading skeleton animation."""
        self._loading_offset = (self._loading_offset + 5) % 200
        self.update()
    
    def paintEvent(self, a0: Optional[QPaintEvent]) -> None:
        """
        Custom paint event to draw loading skeleton.
        
        Args:
            a0: Paint event
        """
        super().paintEvent(a0)
        
        if self._is_loading:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            
            colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
            
            # Draw skeleton bars in content area
            if not self._content_container:
                return
            content_rect = self._content_container.geometry()
            x = content_rect.x() + Spacing.CARD_PADDING
            y = content_rect.y() + Spacing.SM
            width = content_rect.width() - (Spacing.CARD_PADDING * 2)
            
            # Create gradient for shimmer effect
            gradient = QLinearGradient(x + self._loading_offset - 100, 0, x + self._loading_offset, 0)
            base_color = QColor(colors['surface_hover'])
            shimmer_color = QColor(colors['surface_active'])
            gradient.setColorAt(0, base_color)
            gradient.setColorAt(0.5, shimmer_color)
            gradient.setColorAt(1, base_color)
            
            painter.setBrush(gradient)
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Draw 3 skeleton bars
            for i in range(3):
                bar_y = y + (i * 32)
                bar_width = width if i < 2 else width * 0.6
                painter.drawRoundedRect(
                    int(x), int(bar_y), int(bar_width), 20,
                    BorderRadius.SM, BorderRadius.SM
                )
    
    def enterEvent(self, a0) -> None:
        """Handle mouse enter event for hover effects."""
        if self._hoverable:
            self._apply_hover_style(True)
        super().enterEvent(a0)
    
    def leaveEvent(self, a0) -> None:
        """Handle mouse leave event for hover effects."""
        if self._hoverable:
            self._apply_hover_style(False)
        super().leaveEvent(a0)
    
    def _apply_hover_style(self, hovered: bool) -> None:
        """
        Apply hover style changes.
        
        Args:
            hovered: Whether mouse is hovering over card
        """
        # Override in subclasses for specific hover effects
        pass
    
    def set_theme(self, theme_mode: str) -> None:
        """
        Update card theme.
        
        Args:
            theme_mode: Theme mode ('light' or 'dark')
        """
        self._theme_mode = theme_mode
        self._apply_style()
        self._update_title_style()
    
    def set_font_preset(self, preset: FontSizePreset) -> None:
        """
        Update font size preset.
        
        Args:
            preset: Font size preset
        """
        self._typography.set_preset(preset)
        if self._title_label:
            self._typography.apply_to_widget(self._title_label, 'h3', QFont.Bold)
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            if self._title_label:
                self._typography.apply_to_widget(self._title_label, 'h3', QFont.Bold)
        except Exception as e:
            print(f"Warning: Could not update font preset in BaseCard: {e}")


class Card(BaseCard):
    """
    Default card with subtle background.
    
    Standard card for grouping related content.
    Uses surface color with subtle border.
    
    Example:
        card = Card()
        card.set_title("User Information")
        card.set_content(user_form)
        
        # With collapsible
        card = Card(collapsible=True)
        card.set_title("Collapsible Section")
        card.set_collapsed(True)
    """
    
    def _apply_style(self) -> None:
        """Apply default card style."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
        """)
        
        # Apply container styles
        super()._apply_style()


class ElevatedCard(BaseCard):
    """
    Card with shadow for depth and emphasis.
    
    Use for important content that needs to stand out.
    Includes shadow for visual elevation.
    Supports hover effects for interactive cards.
    
    Example:
        card = ElevatedCard(hoverable=True)
        card.set_title("Important Notice")
        card.set_content(notice_widget)
        card.add_header_action("close", lambda: card.hide())
    """
    
    def _apply_style(self) -> None:
        """Apply elevated card style with shadow."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        # Note: QSS doesn't support box-shadow, so we use border styling
        # For true shadows, would need to use QPainter or platform-specific code
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {colors['surface']};
                border: 1px solid {colors['border_subtle']};
                border-radius: {BorderRadius.LG}px;
            }}
        """)
        
        # Set frame shadow for visual depth
        self.setFrameShadow(QFrame.Raised)
        self.setLineWidth(2)
        
        # Apply container styles
        super()._apply_style()
    
    def _apply_hover_style(self, hovered: bool) -> None:
        """Apply hover elevation change."""
        if hovered:
            self.setLineWidth(3)
        else:
            self.setLineWidth(2)


class OutlinedCard(BaseCard):
    """
    Card with prominent border emphasis.
    
    Use when you want clear visual separation without shadows.
    Transparent background with visible border.
    
    Example:
        card = OutlinedCard()
        card.set_title("Settings")
        card.set_content(settings_form)
        card.set_footer(action_buttons)
    """
    
    def _apply_style(self) -> None:
        """Apply outlined card style with prominent border."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
            }}
        """)
        
        # Apply container styles
        super()._apply_style()
    
    def _apply_hover_style(self, hovered: bool) -> None:
        """Apply hover border color change."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        if hovered:
            border_color = colors['primary']
        else:
            border_color = colors['border']
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: transparent;
                border: 2px solid {border_color};
                border-radius: {BorderRadius.LG}px;
            }}
        """)


class CompactToolCard(QFrame):
    """
    Compact tool card for recent tools section (Phase 6.1).
    
    Small card (150x80px) showing only icon and tool name.
    Used in the "Recent Tools" section of the main menu.
    
    Features:
    - Icon + name only (no description)
    - Hover effect
    - Click to launch tool
    - 44x44px minimum touch target (WCAG 2.1 AA)
    
    Signals:
        clicked: Emitted when card is clicked
    
    Attributes:
        _theme_mode: Current theme mode
        _typography: Typography system
        _tool_id: Tool identifier
        _tool_name: Tool display name
        _icon: Tool icon (emoji)
    """
    
    clicked = pyqtSignal(str)  # Emits tool_id
    
    def __init__(
        self,
        tool_id: str,
        tool_name: str,
        icon: str = "📦",
        parent: Optional[QWidget] = None
    ):
        """
        Initialize compact tool card.
        
        Args:
            tool_id: Tool identifier
            tool_name: Tool display name
            icon: Tool icon (emoji)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        self._tool_id = tool_id
        self._tool_name = tool_name
        self._icon = icon
        
        # Connect to preset changes
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in CompactToolCard: {e}")
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up compact card UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        layout.setSpacing(Spacing.XS)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Icon label
        self._icon_label = QLabel(self._icon)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._typography.apply_to_widget(self._icon_label, 'h2')
        
        # Name label
        self._name_label = QLabel(self._tool_name)
        self._name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_label.setWordWrap(True)
        self._typography.apply_to_widget(self._name_label, 'caption', QFont.Weight.DemiBold)
        
        layout.addWidget(self._icon_label)
        layout.addWidget(self._name_label)
        
        # Set fixed size
        self.setFixedSize(150, 80)
        
        # Enable mouse tracking for hover
        self.setMouseTracking(True)
    
    def _apply_style(self) -> None:
        """Apply compact card stylesheet."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        # Use white/dark background for maximum contrast with parent surface
        card_bg = colors['background']  # White in light mode, dark in dark mode
        
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {card_bg};
                border: 1px solid {colors['border']};
                border-radius: {BorderRadius.MD}px;
            }}
            
            QFrame:hover {{
                background-color: {colors['surface_hover']};
                border-color: {colors['primary']};
            }}
        """)
        
        # Update label styles
        self._icon_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
                border: none;
            }}
        """)
        
        self._name_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_secondary']};
                background-color: transparent;
                border: none;
            }}
        """)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._tool_id)
        super().mousePressEvent(event)
    
    def set_theme(self, theme_mode: str) -> None:
        """Update card theme."""
        self._theme_mode = theme_mode
        self._apply_style()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            self._typography.apply_to_widget(self._icon_label, 'h2')
            self._typography.apply_to_widget(self._name_label, 'caption', QFont.Weight.DemiBold)
        except Exception as e:
            print(f"Warning: Could not update font preset in CompactToolCard: {e}")


class EnhancedToolCard(QFrame):
    """
    Enhanced tool card for main tool grid (Phase 6.1).
    
    Full-featured card with icon, name, description, and launch button.
    Used in the main tools grid of the main menu.
    
    Features:
    - Icon + name + description + button
    - Hover effects
    - Click anywhere to launch
    - WCAG 2.1 AA compliant
    
    Signals:
        clicked: Emitted when card is clicked
    
    Attributes:
        _theme_mode: Current theme mode
        _typography: Typography system
        _tool_id: Tool identifier
        _tool_name: Tool display name
        _description: Tool description
        _icon: Tool icon (emoji)
    """
    
    clicked = pyqtSignal(str)  # Emits tool_id
    
    def __init__(
        self,
        tool_id: str,
        tool_name: str,
        description: str,
        icon: str = "📦",
        parent: Optional[QWidget] = None
    ):
        """
        Initialize enhanced tool card.
        
        Args:
            tool_id: Tool identifier
            tool_name: Tool display name
            description: Tool description
            icon: Tool icon (emoji)
            parent: Parent widget
        """
        super().__init__(parent)
        
        self._theme_mode = "light"
        self._typography = TypographySystem(FontSizePreset.NORMAL)
        self._tool_id = tool_id
        self._tool_name = tool_name
        self._description = description
        self._icon = icon
        
        # Connect to preset changes
        try:
            from ui.services import get_v2_settings_bus
            self._settings_bus = get_v2_settings_bus()
            self._settings_bus.font_preset_changed.connect(self._on_preset_changed)
        except Exception as e:
            print(f"Warning: Could not connect to settings bus in EnhancedToolCard: {e}")
        
        self._setup_ui()
        self._apply_style()
    
    def _setup_ui(self) -> None:
        """Set up enhanced card UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING
        )
        layout.setSpacing(Spacing.SM)
        
        # Header (icon + name)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(Spacing.SM)
        
        # Icon label
        self._icon_label = QLabel(self._icon)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setFixedSize(32, 32)
        self._typography.apply_to_widget(self._icon_label, 'h3')
        
        # Name label
        self._name_label = QLabel(self._tool_name)
        self._typography.apply_to_widget(self._name_label, 'h3', QFont.Weight.Bold)
        
        header_layout.addWidget(self._icon_label)
        header_layout.addWidget(self._name_label, 1)
        
        # Description label
        self._description_label = QLabel(self._description)
        self._description_label.setWordWrap(True)
        self._description_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._typography.apply_to_widget(self._description_label, 'body')

        # Launch button
        self._launch_button = GhostButton("Launch →")
        self._launch_button.clicked.connect(lambda: self.clicked.emit(self._tool_id))

        # Add to main layout (no stretch — the card is fixed-height, sized to its content)
        layout.addLayout(header_layout)
        layout.addWidget(self._description_label)
        layout.addWidget(self._launch_button)

        # Size the card to fit its actual description text — no more, no less —
        # so short descriptions don't leave a block of dead space below them.
        self._reserve_description_height()

        # Set minimum width and size policy. Vertical is Fixed: the card's height comes
        # entirely from _reserve_description_height(), not from the grid stretching it.
        self.setMinimumWidth(300)
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Enable mouse tracking for hover
        self.setMouseTracking(True)

    def _reserve_description_height(self) -> None:
        """Fix the card's height to fit the actual description text (clamped to 1-3 lines)."""
        metrics = self._description_label.fontMetrics()
        available_width = max(self.minimumWidth() - (Spacing.CARD_PADDING * 2), 100)
        bounds = metrics.boundingRect(
            QRect(0, 0, available_width, 0),
            Qt.TextFlag.TextWordWrap,
            self._description,
        )
        line_height = metrics.height()
        text_height = max(line_height, min(bounds.height(), line_height * 3))
        self._description_label.setFixedHeight(text_height)

        header_height = 32  # icon size
        button_height = self._launch_button.sizeHint().height()
        spacing_total = Spacing.SM * 2
        padding_total = Spacing.CARD_PADDING * 2
        self.setFixedHeight(
            header_height + text_height + button_height + spacing_total + padding_total
        )

    def hasHeightForWidth(self) -> bool:
        """Tell layouts this widget's height depends on its width (wrapped description)."""
        return True

    def heightForWidth(self, width: int) -> int:
        """Delegate to the internal layout so QGridLayout sizes rows correctly."""
        if self.layout() is not None:
            return self.layout().totalHeightForWidth(width)
        return super().heightForWidth(width)
    
    def _apply_style(self) -> None:
        """Apply enhanced card stylesheet."""
        colors = Colors.LIGHT if self._theme_mode == "light" else Colors.DARK
        
        # Use white/dark background for maximum contrast with parent surface
        card_bg = colors['background']  # White in light mode, dark in dark mode
        
        # Use more specific selector to avoid being overridden
        self.setStyleSheet(f"""
            EnhancedToolCard {{
                background-color: {card_bg};
                border: 2px solid {colors['border']};
                border-radius: {BorderRadius.LG}px;
                min-width: 300px;
            }}
            
            EnhancedToolCard:hover {{
                background-color: {colors['surface_hover']};
                border-color: {colors['primary']};
            }}
        """)
        
        # Update label styles
        self._icon_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
                border: none;
            }}
        """)
        
        self._name_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_primary']};
                background-color: transparent;
                border: none;
            }}
        """)
        
        self._description_label.setStyleSheet(f"""
            QLabel {{
                color: {colors['text_secondary']};
                background-color: transparent;
                border: none;
            }}
        """)
    
    def mousePressEvent(self, event) -> None:
        """Handle mouse press to emit clicked signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._tool_id)
        super().mousePressEvent(event)
    
    def set_theme(self, theme_mode: str) -> None:
        """Update card theme."""
        self._theme_mode = theme_mode
        self._launch_button.set_theme(theme_mode)
        self._apply_style()
    
    def _on_preset_changed(self, preset: str) -> None:
        """Handle font preset change from settings."""
        try:
            preset_enum = FontSizePreset.from_string(preset)
            self._typography.set_preset(preset_enum)
            self._typography.apply_to_widget(self._icon_label, 'h3')
            self._typography.apply_to_widget(self._name_label, 'h3', QFont.Weight.Bold)
            self._typography.apply_to_widget(self._description_label, 'body')
            self._reserve_description_height()
        except Exception as e:
            print(f"Warning: Could not update font preset in EnhancedToolCard: {e}")


# Export all card classes
__all__ = [
    'BaseCard',
    'Card',
    'ElevatedCard',
    'OutlinedCard',
    'CompactToolCard',
    'EnhancedToolCard',
]

# Made with Bob