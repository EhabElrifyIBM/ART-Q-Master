"""
Modern UI Components V2 - Base Component Library
=================================================

This module provides modern, reusable UI components built on the new foundation:
- design_system.py for colors, spacing, shadows
- typography.py for font scaling
- theme.py for stylesheet generation
- V2SettingsBus for reactive updates

Components follow IBM Carbon Design principles and are designed to be:
- Extensible and composable
- Accessible (keyboard navigation, ARIA support)
- Themeable (light/dark mode)
- Responsive to settings changes

Component Categories:
- Buttons: Primary, Secondary, Ghost, Danger buttons
- Inputs: LineEdit, TextEdit, ComboBox, CheckBox, RadioButton
- Cards: Base, Elevated, Outlined cards
- Dialogs: Modern, Confirm, Input, Progress, Message dialogs
- Tables: Enhanced table with sorting and filtering
- Navigation: ToolBar, SideBar, Breadcrumbs
- Feedback: Toast, Spinner, ProgressBar, Badge

Usage:
    from ui.components_v2 import PrimaryButton, ModernDialog, Card
    
    # Create a primary button
    button = PrimaryButton("Click Me")
    button.clicked.connect(on_click)
    
    # Create a card
    card = Card()
    card.set_title("My Card")
    card.set_content(my_widget)
    
    # Create a dialog
    dialog = ModernDialog(parent)
    dialog.set_title("Confirm Action")
    dialog.exec_()

Version: 1.0.0 (Phase 1 - Base Implementation)
"""

# Button components
from .buttons import (
    ModernButton,
    PrimaryButton,
    SecondaryButton,
    GhostButton,
    DangerButton,
    ProfileButton,  # Phase 6.1
)

# Input components
from .inputs import (
    ModernLineEdit,
    ModernTextEdit,
    ModernComboBox,
    ModernCheckBox,
    ModernRadioButton,
    SearchBar,  # Phase 6.1
)

# Card components
from .cards import (
    BaseCard,
    Card,
    ElevatedCard,
    OutlinedCard,
    CompactToolCard,  # Phase 6.1
    EnhancedToolCard,  # Phase 6.1
)

# Dialog components
from .dialogs import (
    ModernDialog,
    ConfirmDialog,
    InputDialog,
    ProgressDialog,
    MessageDialog,
)

# Table components (Phase 5.3 Enhanced)
from .tables import (
    ModernTableWidget,
    TableFilterWidget,
    TablePaginationWidget,
    SortOrder,
    SelectionMode,
)

# Navigation components (Phase 5.4 Enhanced)
from .navigation import (
    ModernToolBar,
    Sidebar,
    Breadcrumbs,
)

# Feedback components
from .feedback import (
    Toast,
    ModernSpinner,
    ModernProgressBar,
    Badge,
)

# Version info
__version__ = "1.0.0"
__phase__ = "Phase 1 - Base Implementation"

# Export all components
__all__ = [
    # Buttons
    'ModernButton',
    'PrimaryButton',
    'SecondaryButton',
    'GhostButton',
    'DangerButton',
    'ProfileButton',  # Phase 6.1
    
    # Inputs
    'ModernLineEdit',
    'ModernTextEdit',
    'ModernComboBox',
    'ModernCheckBox',
    'ModernRadioButton',
    'SearchBar',  # Phase 6.1
    
    # Cards
    'BaseCard',
    'Card',
    'ElevatedCard',
    'OutlinedCard',
    'CompactToolCard',  # Phase 6.1
    'EnhancedToolCard',  # Phase 6.1
    
    # Dialogs
    'ModernDialog',
    'ConfirmDialog',
    'InputDialog',
    'ProgressDialog',
    'MessageDialog',
    
    # Tables (Phase 5.3 Enhanced)
    'ModernTableWidget',
    'TableFilterWidget',
    'TablePaginationWidget',
    'SortOrder',
    'SelectionMode',
    
    # Navigation (Phase 5.4 Enhanced)
    'ModernToolBar',
    'Sidebar',
    'Breadcrumbs',
    
    # Feedback
    'Toast',
    'ModernSpinner',
    'ModernProgressBar',
    'Badge',
    
    # Metadata
    '__version__',
    '__phase__',
]

# Made with Bob