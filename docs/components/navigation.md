# Navigation Components API Documentation

**Phase 5.4 Enhanced** - Modern navigation components with advanced features

## Overview

The navigation components provide a complete navigation system for modern applications, including toolbars, sidebars, and breadcrumbs. All components follow IBM Carbon Design principles and integrate seamlessly with the design system.

## Components

### 1. ModernToolBar

Enhanced toolbar with action groups, overflow menu, and customization.

#### Features
- ✅ Action groups (left, center, right alignment)
- ✅ Separator support
- ✅ Overflow menu (when toolbar too narrow)
- ✅ Icon-only mode
- ✅ Tooltips for all actions
- ✅ Keyboard shortcuts display
- ✅ Search/filter in toolbar
- ✅ Customization (show/hide actions)
- ✅ Theme support (light/dark)
- ✅ Font preset integration

#### API Reference

**Constructor**
```python
ModernToolBar(parent: Optional[QWidget] = None)
```

**Methods**

```python
# Add single action
add_action(
    text: str,
    callback: Callable,
    icon: Optional[str] = None,
    shortcut: Optional[str] = None,
    tooltip: Optional[str] = None,
    alignment: str = "left"
) -> ToolBarAction

# Add action group
add_action_group(
    actions: List[Tuple[str, Callable, Optional[str]]],
    alignment: str = "left"
) -> List[ToolBarAction]

# Add separator
add_separator(alignment: str = "left") -> None

# Enable search
enable_search(enabled: bool = True, placeholder: str = "Search...") -> None

# Enable overflow menu
enable_overflow(enabled: bool = True) -> None

# Set icon-only mode
set_icon_only(icon_only: bool) -> None

# Set theme
set_theme(theme_mode: str) -> None
```

**Signals**
```python
action_triggered = pyqtSignal(str)  # Emitted when action is triggered
search_changed = pyqtSignal(str)    # Emitted when search text changes
```

#### Usage Examples

**Basic Toolbar**
```python
from ui.components_v2 import ModernToolBar

# Create toolbar
toolbar = ModernToolBar()

# Add actions
toolbar.add_action("New", on_new, icon="📄", shortcut="Ctrl+N")
toolbar.add_action("Open", on_open, icon="📂", shortcut="Ctrl+O")
toolbar.add_action("Save", on_save, icon="💾", shortcut="Ctrl+S")

# Add separator
toolbar.add_separator()

# Add more actions
toolbar.add_action("Cut", on_cut, icon="✂️", shortcut="Ctrl+X")
toolbar.add_action("Copy", on_copy, icon="📋", shortcut="Ctrl+C")
toolbar.add_action("Paste", on_paste, icon="📌", shortcut="Ctrl+V")
```

**Action Groups with Alignment**
```python
# Left-aligned actions
toolbar.add_action_group([
    ("New", on_new, "📄"),
    ("Open", on_open, "📂"),
    ("Save", on_save, "💾")
], alignment="left")

# Center-aligned actions
toolbar.add_action_group([
    ("Bold", on_bold, "B"),
    ("Italic", on_italic, "I"),
    ("Underline", on_underline, "U")
], alignment="center")

# Right-aligned actions
toolbar.add_action_group([
    ("Settings", on_settings, "⚙️"),
    ("Help", on_help, "❓")
], alignment="right")
```

**With Search and Overflow**
```python
# Enable search
toolbar.enable_search(True, placeholder="Search files...")

# Enable overflow menu
toolbar.enable_overflow(True)

# Connect to search signal
toolbar.search_changed.connect(on_search)

# Connect to action signal
toolbar.action_triggered.connect(on_action)
```

**Icon-Only Mode**
```python
# Toggle icon-only mode
toolbar.set_icon_only(True)  # Show icons only
toolbar.set_icon_only(False)  # Show icons + text
```

---

### 2. Sidebar

Collapsible sidebar navigation with nested items and sections.

#### Features
- ✅ Collapsible functionality
- ✅ Navigation items with icons
- ✅ Nested navigation (expandable sections)
- ✅ Active item highlighting
- ✅ Hover effects
- ✅ Keyboard navigation
- ✅ Resize handle (drag to resize)
- ✅ Mini mode (icons only)
- ✅ Footer section
- ✅ Smooth animations (250ms)
- ✅ Theme support

#### API Reference

**Constructor**
```python
Sidebar(parent: Optional[QWidget] = None)
```

**Methods**

```python
# Add navigation item
add_item(
    text: str,
    icon: Optional[str] = None,
    callback: Optional[Callable] = None
) -> SidebarItem

# Add collapsible section with items
add_section(
    title: str,
    items: List[Tuple[str, Optional[str], Optional[Callable]]]
) -> SidebarSection

# Add footer item
add_footer_item(
    text: str,
    icon: Optional[str] = None,
    callback: Optional[Callable] = None
) -> SidebarItem

# Toggle collapsed state
toggle_collapsed() -> None

# Set collapsible
set_collapsible(collapsible: bool) -> None

# Set mini mode
set_mini_mode(mini_mode: bool) -> None

# Set theme
set_theme(theme_mode: str) -> None
```

**Signals**
```python
item_clicked = pyqtSignal(str)        # Emitted when item is clicked
collapsed_changed = pyqtSignal(bool)  # Emitted when collapsed state changes
```

#### Usage Examples

**Basic Sidebar**
```python
from ui.components_v2 import Sidebar

# Create sidebar
sidebar = Sidebar()

# Add navigation items
sidebar.add_item("Dashboard", icon="📊", callback=on_dashboard)
sidebar.add_item("Projects", icon="📁", callback=on_projects)
sidebar.add_item("Tasks", icon="✓", callback=on_tasks)
sidebar.add_item("Calendar", icon="📅", callback=on_calendar)

# Connect to item clicked signal
sidebar.item_clicked.connect(on_nav_item_clicked)
```

**With Sections**
```python
# Add main items
sidebar.add_item("Dashboard", icon="📊", callback=on_dashboard)

# Add Reports section with nested items
sidebar.add_section("Reports", [
    ("Sales Report", "💰", on_sales_report),
    ("Analytics", "📈", on_analytics),
    ("Performance", "⚡", on_performance)
])

# Add Settings section
sidebar.add_section("Settings", [
    ("Profile", "👤", on_profile),
    ("Preferences", "⚙️", on_preferences),
    ("Security", "🔒", on_security)
])
```

**With Footer**
```python
# Add footer items
sidebar.add_footer_item("Help", icon="❓", callback=on_help)
sidebar.add_footer_item("Settings", icon="⚙️", callback=on_settings)
sidebar.add_footer_item("Logout", icon="🚪", callback=on_logout)
```

**Collapsible Sidebar**
```python
# Enable collapsible
sidebar.set_collapsible(True)

# Toggle programmatically
sidebar.toggle_collapsed()

# Listen to collapsed state changes
sidebar.collapsed_changed.connect(on_collapsed_changed)

def on_collapsed_changed(collapsed: bool):
    if collapsed:
        print("Sidebar collapsed")
    else:
        print("Sidebar expanded")
```

**Mini Mode**
```python
# Enable mini mode (icons only)
sidebar.set_mini_mode(True)

# Disable mini mode
sidebar.set_mini_mode(False)
```

---

### 3. Breadcrumbs

Enhanced breadcrumb navigation with dropdowns and overflow handling.

#### Features
- ✅ Home icon
- ✅ Dropdown menus for long paths
- ✅ Ellipsis for overflow
- ✅ Keyboard navigation (Arrow keys, Home, End)
- ✅ Custom separators
- ✅ Click handlers
- ✅ Hover effects
- ✅ Max width handling
- ✅ Theme support

#### API Reference

**Constructor**
```python
Breadcrumbs(parent: Optional[QWidget] = None)
```

**Methods**

```python
# Set breadcrumb path
set_path(path: List[str]) -> None

# Set maximum items before ellipsis
set_max_items(max_items: int) -> None

# Set custom separator
set_separator(separator: str) -> None

# Enable/disable home icon
enable_home_icon(enabled: bool = True) -> None

# Enable/disable dropdown menus
enable_dropdowns(enabled: bool = True) -> None

# Set theme
set_theme(theme_mode: str) -> None
```

**Signals**
```python
crumb_clicked = pyqtSignal(int, str)  # Emitted when breadcrumb is clicked (index, text)
item_clicked = pyqtSignal(str)        # Emitted when breadcrumb item is clicked (text)
```

#### Usage Examples

**Basic Breadcrumbs**
```python
from ui.components_v2 import Breadcrumbs

# Create breadcrumbs
breadcrumbs = Breadcrumbs()

# Set path
breadcrumbs.set_path(["Home", "Projects", "ART Q Master", "src_v2"])

# Connect to click signal
breadcrumbs.crumb_clicked.connect(on_breadcrumb_clicked)

def on_breadcrumb_clicked(index: int, text: str):
    print(f"Clicked: {text} at index {index}")
    # Navigate to that level
    navigate_to_level(index)
```

**With Home Icon**
```python
# Enable home icon (default: True)
breadcrumbs.enable_home_icon(True)

# Disable home icon
breadcrumbs.enable_home_icon(False)
```

**With Overflow Handling**
```python
# Set maximum items to show
breadcrumbs.set_max_items(4)

# Long path will show: Home / ... / item3 / item4
breadcrumbs.set_path([
    "Home", "Projects", "ART Q Master", 
    "src_v2", "ui", "components_v2"
])
```

**With Dropdown Menus**
```python
# Enable dropdown menus for hidden items
breadcrumbs.enable_dropdowns(True)

# Now clicking "..." will show a menu with hidden items
breadcrumbs.set_max_items(4)
breadcrumbs.set_path(["Home", "A", "B", "C", "D", "E", "F"])
```

**Custom Separator**
```python
# Use custom separator
breadcrumbs.set_separator("›")  # Right arrow
breadcrumbs.set_separator("→")  # Arrow
breadcrumbs.set_separator(">")  # Greater than
breadcrumbs.set_separator("/")  # Slash (default)
```

**Keyboard Navigation**
```python
# Breadcrumbs support keyboard navigation:
# - Left Arrow: Navigate to previous breadcrumb
# - Right Arrow: Navigate to next breadcrumb
# - Home: Navigate to first breadcrumb
# - End: Navigate to last breadcrumb

# Set focus to enable keyboard navigation
breadcrumbs.setFocusPolicy(Qt.StrongFocus)
breadcrumbs.setFocus()
```

---

## Integration Examples

### Complete Navigation Layout

```python
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from ui.components_v2 import ModernToolBar, Sidebar, Breadcrumbs

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar at top
        self.toolbar = ModernToolBar()
        self.toolbar.add_action("New", self.on_new, icon="📄", shortcut="Ctrl+N")
        self.toolbar.add_action("Open", self.on_open, icon="📂", shortcut="Ctrl+O")
        self.toolbar.add_separator()
        self.toolbar.add_action("Save", self.on_save, icon="💾", shortcut="Ctrl+S")
        self.toolbar.enable_search(True)
        main_layout.addWidget(self.toolbar)
        
        # Content area with sidebar
        content_layout = QHBoxLayout()
        content_layout.setSpacing(0)
        
        # Sidebar on left
        self.sidebar = Sidebar()
        self.sidebar.add_item("Dashboard", icon="📊", callback=self.on_dashboard)
        self.sidebar.add_section("Projects", [
            ("Active", "✓", self.on_active_projects),
            ("Archived", "📦", self.on_archived_projects)
        ])
        self.sidebar.add_footer_item("Settings", icon="⚙️", callback=self.on_settings)
        content_layout.addWidget(self.sidebar)
        
        # Main content area
        content_widget = QWidget()
        content_widget_layout = QVBoxLayout(content_widget)
        
        # Breadcrumbs
        self.breadcrumbs = Breadcrumbs()
        self.breadcrumbs.set_path(["Home", "Projects", "Current Project"])
        self.breadcrumbs.crumb_clicked.connect(self.on_breadcrumb_clicked)
        content_widget_layout.addWidget(self.breadcrumbs)
        
        # Your main content here
        # content_widget_layout.addWidget(your_content)
        
        content_layout.addWidget(content_widget, 1)
        main_layout.addLayout(content_layout, 1)
    
    def on_new(self):
        print("New file")
    
    def on_open(self):
        print("Open file")
    
    def on_save(self):
        print("Save file")
    
    def on_dashboard(self):
        self.breadcrumbs.set_path(["Home", "Dashboard"])
    
    def on_active_projects(self):
        self.breadcrumbs.set_path(["Home", "Projects", "Active"])
    
    def on_archived_projects(self):
        self.breadcrumbs.set_path(["Home", "Projects", "Archived"])
    
    def on_settings(self):
        self.breadcrumbs.set_path(["Home", "Settings"])
    
    def on_breadcrumb_clicked(self, index: int, text: str):
        print(f"Navigate to: {text}")
```

### Responsive Navigation

```python
from PyQt5.QtCore import QSize

class ResponsiveMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        # Setup navigation components
        self.toolbar = ModernToolBar()
        self.sidebar = Sidebar()
        
        # ... add items ...
    
    def resizeEvent(self, event):
        """Handle window resize for responsive behavior."""
        super().resizeEvent(event)
        
        width = event.size().width()
        
        # Collapse sidebar on narrow screens
        if width < 768:
            self.sidebar.set_mini_mode(True)
            self.toolbar.set_icon_only(True)
        else:
            self.sidebar.set_mini_mode(False)
            self.toolbar.set_icon_only(False)
```

---

## Styling and Theming

All navigation components automatically respond to theme changes through the V2SettingsBus.

```python
from ui.services import get_v2_settings_bus

# Get settings bus
settings_bus = get_v2_settings_bus()

# Change theme (components update automatically)
settings_bus.theme_changed.emit("dark")
settings_bus.theme_changed.emit("light")

# Change font preset (components update automatically)
settings_bus.font_preset_changed.emit("large")
```

---

## Accessibility

All navigation components are keyboard accessible:

### ModernToolBar
- **Tab**: Navigate between actions
- **Enter/Space**: Activate focused action
- **Shortcuts**: Use defined keyboard shortcuts

### Sidebar
- **Tab**: Navigate between items
- **Enter/Space**: Activate focused item
- **Up/Down**: Navigate items (when focused)

### Breadcrumbs
- **Tab**: Navigate between breadcrumbs
- **Enter/Space**: Activate focused breadcrumb
- **Left/Right**: Navigate between breadcrumbs
- **Home**: Jump to first breadcrumb
- **End**: Jump to last breadcrumb

---

## Performance

All components are optimized for 60 FPS performance:

- **Smooth animations**: 250ms duration with cubic easing
- **Efficient rendering**: Only re-render when necessary
- **Lazy loading**: Items created on-demand
- **Event throttling**: Search events debounced
- **Memory efficient**: Proper cleanup on deletion

---

## Best Practices

### ModernToolBar
1. Group related actions together
2. Use separators to create visual groups
3. Place primary actions on the left
4. Place secondary actions on the right
5. Use tooltips with keyboard shortcuts
6. Enable overflow for many actions
7. Use icon-only mode for compact layouts

### Sidebar
1. Keep navigation hierarchy shallow (max 2 levels)
2. Use clear, concise labels
3. Use meaningful icons
4. Group related items in sections
5. Place important items at the top
6. Use footer for settings/help
7. Enable collapsible for flexible layouts

### Breadcrumbs
1. Keep paths reasonably short
2. Use max_items to handle long paths
3. Enable dropdowns for better UX
4. Use clear, descriptive labels
5. Make all items clickable (except last)
6. Use home icon for quick navigation
7. Choose appropriate separator

---

## Migration Guide

### From Old ModernToolBar

**Before:**
```python
toolbar = ModernToolBar()
toolbar.add_action("Save", on_save)
```

**After (Phase 5.4):**
```python
toolbar = ModernToolBar()
toolbar.add_action("Save", on_save, icon="💾", shortcut="Ctrl+S", alignment="left")
toolbar.enable_search(True)
toolbar.enable_overflow(True)
```

### From Old ModernSideBar

**Before:**
```python
sidebar = ModernSideBar()
sidebar.add_item("Dashboard")
```

**After (Phase 5.4):**
```python
sidebar = Sidebar()  # Note: Renamed from ModernSideBar
sidebar.add_item("Dashboard", icon="📊", callback=on_dashboard)
sidebar.add_section("Reports", [
    ("Sales", "💰", on_sales),
    ("Analytics", "📈", on_analytics)
])
sidebar.set_collapsible(True)
```

### From Old Breadcrumbs

**Before:**
```python
breadcrumbs = Breadcrumbs()
breadcrumbs.set_path(["Home", "Projects"])
```

**After (Phase 5.4):**
```python
breadcrumbs = Breadcrumbs()
breadcrumbs.set_path(["Home", "Projects", "Current"])
breadcrumbs.set_max_items(4)
breadcrumbs.enable_dropdowns(True)
breadcrumbs.enable_home_icon(True)
```

---

## Troubleshooting

### Toolbar actions not showing
- Check alignment parameter
- Verify callback is callable
- Check if overflow is hiding actions

### Sidebar not collapsing
- Ensure `set_collapsible(True)` is called
- Check if animations are enabled
- Verify parent layout allows resizing

### Breadcrumbs not clickable
- Last item is intentionally not clickable
- Check if callback is connected
- Verify path is set correctly

### Theme not updating
- Ensure V2SettingsBus is available
- Check if `set_theme()` is called
- Verify theme mode is valid ("light" or "dark")

---

## Version History

- **Phase 5.4** (Current): Enhanced navigation with advanced features
  - ModernToolBar: Action groups, overflow, search, customization
  - Sidebar: Collapsible, nested navigation, mini mode, footer
  - Breadcrumbs: Dropdowns, ellipsis, keyboard navigation
  - Smooth animations and performance optimization

- **Phase 1**: Initial implementation
  - Basic ModernToolBar
  - Basic ModernSideBar
  - Basic Breadcrumbs

---

**Made with Bob** - Phase 5.4 Navigation Enhancement Complete ✅