# Card Components Documentation

## Overview

Card components are versatile containers for grouping related content. They follow IBM Carbon Design principles and integrate seamlessly with the design system.

**Phase 5.2 Enhancements:**
- ✅ 3 card variants (Card, ElevatedCard, OutlinedCard)
- ✅ Collapsible/expandable functionality
- ✅ Action buttons in header (close, minimize, settings)
- ✅ Loading state with skeleton animation
- ✅ Hover effects (subtle elevation change)
- ✅ Proper spacing (8px grid)
- ✅ Footer section support

## Card Variants

### 1. Card (Default)
Standard card with subtle background and border.

**Use Cases:**
- Grouping related form fields
- Displaying user information
- Content sections

**Visual Style:**
- Surface background color
- 1px border
- 12px border radius

### 2. ElevatedCard
Card with visual elevation using frame shadow.

**Use Cases:**
- Important notices
- Featured content
- Interactive cards that need emphasis

**Visual Style:**
- Surface background color
- Subtle border
- Raised frame shadow
- Hover effect (increased elevation)

### 3. OutlinedCard
Card with prominent border and transparent background.

**Use Cases:**
- Settings panels
- Clear visual separation
- Lightweight containers

**Visual Style:**
- Transparent background
- 2px border
- Hover effect (border color change to primary)

## API Reference

### BaseCard

Base class for all card variants. Provides common functionality.

#### Constructor

```python
BaseCard(
    parent: Optional[QWidget] = None,
    collapsible: bool = False,
    hoverable: bool = False
)
```

**Parameters:**
- `parent`: Parent widget
- `collapsible`: Whether card can be collapsed/expanded
- `hoverable`: Whether card has hover effects

#### Methods

##### set_title(title: str)
Set the card title displayed in the header.

```python
card.set_title("User Profile")
```

##### set_content(widget: QWidget)
Set the main content widget.

```python
content = QLabel("Card content goes here")
card.set_content(content)
```

##### set_footer(widget: QWidget)
Add a footer section to the card.

```python
footer = QHBoxLayout()
footer.addWidget(PrimaryButton("Save"))
footer.addWidget(SecondaryButton("Cancel"))
footer_widget = QWidget()
footer_widget.setLayout(footer)
card.set_footer(footer_widget)
```

##### remove_footer()
Remove the footer section.

```python
card.remove_footer()
```

##### add_header_action(action_type: str, callback: Callable, tooltip: str = "")
Add action button to card header.

**Action Types:**
- `"close"`: Close/dismiss button (✕)
- `"minimize"`: Minimize button (−)
- `"settings"`: Settings button (⚙)
- `"custom"`: Custom action (•)

```python
card.add_header_action("close", lambda: card.hide(), "Close card")
card.add_header_action("settings", on_settings_clicked, "Card settings")
```

##### remove_header_action(action_type: str)
Remove action button from header.

```python
card.remove_header_action("close")
```

##### set_collapsed(collapsed: bool)
Set card collapsed state (only works if `collapsible=True`).

```python
card.set_collapsed(True)  # Collapse
card.set_collapsed(False)  # Expand
```

##### toggle_collapsed()
Toggle between collapsed and expanded states.

```python
card.toggle_collapsed()
```

##### is_collapsed() -> bool
Check if card is currently collapsed.

```python
if card.is_collapsed():
    print("Card is collapsed")
```

##### set_loading(loading: bool)
Show/hide loading skeleton animation.

```python
card.set_loading(True)  # Show loading
# ... load data ...
card.set_loading(False)  # Hide loading
```

##### is_loading() -> bool
Check if card is in loading state.

```python
if card.is_loading():
    print("Card is loading")
```

##### set_theme(theme_mode: str)
Update card theme ('light' or 'dark').

```python
card.set_theme("dark")
```

##### set_font_preset(preset: FontSizePreset)
Update font size preset.

```python
from ui.typography import FontSizePreset
card.set_font_preset(FontSizePreset.LARGE)
```

## Usage Examples

### Example 1: Basic Card

```python
from ui.components_v2 import Card
from PyQt5.QtWidgets import QLabel

# Create card
card = Card()
card.set_title("User Information")

# Add content
content = QLabel("Name: John Doe\nEmail: john@example.com")
card.set_content(content)

# Add to layout
layout.addWidget(card)
```

### Example 2: Collapsible Card

```python
from ui.components_v2 import Card
from PyQt5.QtWidgets import QVBoxLayout, QLabel

# Create collapsible card
card = Card(collapsible=True)
card.set_title("Advanced Settings")

# Add content
content_layout = QVBoxLayout()
content_layout.addWidget(QLabel("Setting 1"))
content_layout.addWidget(QLabel("Setting 2"))
content_widget = QWidget()
content_widget.setLayout(content_layout)
card.set_content(content_widget)

# Start collapsed
card.set_collapsed(True)

layout.addWidget(card)
```

### Example 3: Card with Actions

```python
from ui.components_v2 import ElevatedCard
from PyQt5.QtWidgets import QLabel

# Create elevated card with actions
card = ElevatedCard(hoverable=True)
card.set_title("Notification")

# Add action buttons
card.add_header_action("close", lambda: card.hide(), "Dismiss")
card.add_header_action("settings", on_settings, "Settings")

# Add content
content = QLabel("You have 3 new messages")
card.set_content(content)

layout.addWidget(card)
```

### Example 4: Card with Footer

```python
from ui.components_v2 import Card
from ui.components_v2.buttons import PrimaryButton, SecondaryButton
from PyQt5.QtWidgets import QLabel, QHBoxLayout, QWidget

# Create card
card = Card()
card.set_title("Confirm Action")

# Add content
content = QLabel("Are you sure you want to proceed?")
card.set_content(content)

# Add footer with buttons
footer_layout = QHBoxLayout()
footer_layout.addStretch()
footer_layout.addWidget(SecondaryButton("Cancel"))
footer_layout.addWidget(PrimaryButton("Confirm"))

footer_widget = QWidget()
footer_widget.setLayout(footer_layout)
card.set_footer(footer_widget)

layout.addWidget(card)
```

### Example 5: Loading State

```python
from ui.components_v2 import Card
from PyQt5.QtWidgets import QLabel
import asyncio

# Create card
card = Card()
card.set_title("Data Loading")

# Show loading state
card.set_loading(True)

# Simulate async data loading
async def load_data():
    await asyncio.sleep(2)  # Simulate network delay
    
    # Update content
    content = QLabel("Data loaded successfully!")
    card.set_content(content)
    
    # Hide loading
    card.set_loading(False)

asyncio.create_task(load_data())

layout.addWidget(card)
```

### Example 6: Outlined Card with Hover

```python
from ui.components_v2 import OutlinedCard
from PyQt5.QtWidgets import QLabel

# Create outlined card with hover effect
card = OutlinedCard(hoverable=True)
card.set_title("Settings Panel")

# Add content
content = QLabel("Configure your preferences here")
card.set_content(content)

# Hover effect will change border color to primary
layout.addWidget(card)
```

### Example 7: Complex Card Layout

```python
from ui.components_v2 import ElevatedCard
from ui.components_v2.buttons import PrimaryButton, SecondaryButton, GhostButton
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QHBoxLayout, QWidget

# Create card
card = ElevatedCard(collapsible=True, hoverable=True)
card.set_title("Project Details")

# Add header actions
card.add_header_action("settings", on_edit_project, "Edit project")
card.add_header_action("close", lambda: card.hide(), "Close")

# Add content
content_layout = QVBoxLayout()
content_layout.addWidget(QLabel("Project Name: My Project"))
content_layout.addWidget(QLabel("Status: Active"))
content_layout.addWidget(QLabel("Team Members: 5"))

content_widget = QWidget()
content_widget.setLayout(content_layout)
card.set_content(content_widget)

# Add footer with actions
footer_layout = QHBoxLayout()
footer_layout.addWidget(GhostButton("View Details"))
footer_layout.addStretch()
footer_layout.addWidget(SecondaryButton("Archive"))
footer_layout.addWidget(PrimaryButton("Open"))

footer_widget = QWidget()
footer_widget.setLayout(footer_layout)
card.set_footer(footer_widget)

layout.addWidget(card)
```

## Best Practices

### 1. Choose the Right Variant

- **Card**: Default choice for most content grouping
- **ElevatedCard**: Use for important or interactive content
- **OutlinedCard**: Use when you need clear separation without shadows

### 2. Use Collapsible Cards Wisely

- Good for: Advanced settings, optional information, long content
- Avoid for: Critical information that should always be visible

### 3. Action Buttons

- Limit to 2-3 action buttons per card
- Use clear, recognizable icons
- Provide tooltips for clarity

### 4. Loading States

- Always show loading state for async operations
- Keep loading time reasonable (< 3 seconds ideal)
- Provide feedback when loading completes

### 5. Footer Usage

- Use for card-specific actions
- Keep footer actions relevant to card content
- Align buttons consistently (right-aligned is standard)

### 6. Spacing

- Card padding is automatically set to 16px (Spacing.CARD_PADDING)
- Content spacing uses 8px (Spacing.COMPONENT_GAP)
- Follow the 8px grid system

### 7. Accessibility

- Cards automatically respond to theme changes
- Font sizes scale with preset changes
- Collapsible cards use clear visual indicators (▼/▶)

## Theme Integration

Cards automatically integrate with the theme system:

```python
# Cards respond to theme changes automatically
from ui.services import get_v2_settings_bus

settings_bus = get_v2_settings_bus()
settings_bus.theme_changed.connect(lambda mode: card.set_theme(mode))
```

## Typography Integration

Cards automatically respond to font preset changes:

```python
# Font sizes update automatically when preset changes
from ui.services import get_v2_settings_bus

settings_bus = get_v2_settings_bus()
# Card title will automatically resize when preset changes
```

## Design Tokens Used

Cards use the following design system tokens:

- **Spacing**: `CARD_PADDING` (16px), `COMPONENT_GAP` (8px), `SM` (8px)
- **BorderRadius**: `LG` (12px), `SM` (4px)
- **Colors**: `surface`, `border`, `border_subtle`, `text_primary`, `primary`
- **Shadows**: Frame shadow for ElevatedCard

## Migration from Old Cards

If migrating from older card implementations:

```python
# Old way
old_card = QFrame()
old_card.setStyleSheet("background: white; border: 1px solid gray;")

# New way
new_card = Card()
new_card.set_title("My Card")
new_card.set_content(content_widget)
```

Benefits of new cards:
- Automatic theme support
- Built-in collapsible functionality
- Loading states
- Action buttons
- Footer support
- Consistent styling

## Related Components

- **Buttons**: Use for card actions and footer buttons
- **Inputs**: Use in card content for forms
- **Dialogs**: Cards can contain dialog triggers
- **Typography**: Card titles use typography system

## Troubleshooting

### Card not showing content
```python
# Make sure to call set_content()
card.set_content(my_widget)
```

### Collapsible not working
```python
# Make sure collapsible=True in constructor
card = Card(collapsible=True)
```

### Loading animation not showing
```python
# Make sure to call set_loading(True)
card.set_loading(True)
# And set_loading(False) when done
```

### Footer not visible
```python
# Make sure to call set_footer()
card.set_footer(footer_widget)
```

## Performance Considerations

- Cards are lightweight and efficient
- Loading animation runs at 20 FPS (50ms interval)
- Hover effects use CSS transitions (no JavaScript)
- Collapsible animation is instant (no performance impact)

## Accessibility

- Cards support keyboard navigation
- Collapsible cards use clear visual indicators
- Action buttons have tooltips
- Theme changes are automatic
- Font scaling is automatic

---

**Last Updated**: Phase 5.2 Implementation
**Component Version**: 2.0
**Design System**: IBM Carbon Design