# Feedback Components API Documentation

## Overview

Feedback components provide user feedback mechanisms including notifications, progress indicators, loading states, and status badges. All components follow IBM Carbon Design principles and support theming.

## Components

- **Toast** - Temporary notification messages
- **ModernProgressBar** - Progress indicators with ETA
- **LoadingSpinner** (ModernSpinner) - Loading animations
- **Badge** - Status and counter badges

---

## Toast

Temporary notification messages that appear and auto-dismiss.

### Current Features (Phase 5.4)

```python
from ui.components_v2 import Toast

# Show notifications
Toast.info(parent, "Information message", duration=4000)
Toast.success(parent, "Operation successful!", duration=3000)
Toast.warning(parent, "Warning message", duration=5000)
Toast.error(parent, "Error occurred")  # Shows dialog instead

# Custom toast
toast = Toast("Custom message", "info", parent, duration=5000)
toast.show()
```

### Enhanced API (Phase 5.5 Specification)

```python
from ui.components_v2 import Toast, ToastPosition

# Position options
Toast.success(parent, "Saved!", position=ToastPosition.TOP_RIGHT)
Toast.info(parent, "Loading...", position=ToastPosition.BOTTOM_CENTER)

# With action button
def retry_action():
    print("Retrying...")

Toast.error(parent, "Failed to save", 
           action=("Retry", retry_action),
           position=ToastPosition.TOP_RIGHT)

# Dismissible toast
Toast.warning(parent, "Check this out", 
             dismissible=True,
             position=ToastPosition.TOP_CENTER)

# With sound notification
Toast.success(parent, "Complete!", sound=True)

# Multiple toasts stack automatically
Toast.info(parent, "First message")
Toast.info(parent, "Second message")  # Stacks below first
Toast.success(parent, "Third message")  # Stacks below second
```

### Toast Positions

- `ToastPosition.TOP_LEFT` - Top left corner
- `ToastPosition.TOP_CENTER` - Top center
- `ToastPosition.TOP_RIGHT` - Top right corner (default)
- `ToastPosition.BOTTOM_LEFT` - Bottom left corner
- `ToastPosition.BOTTOM_CENTER` - Bottom center
- `ToastPosition.BOTTOM_RIGHT` - Bottom right corner

### Toast Features

✅ **Implemented:**
- 4 variants (info, success, warning, error)
- Auto-dismiss with configurable duration
- Theme support (light/dark)
- Font preset support
- Semantic colors

📋 **Phase 5.5 Enhancements:**
- Position options (6 positions)
- Toast stacking
- Manual dismiss button
- Action button support
- Slide-in/slide-out animations
- Progress bar for auto-dismiss
- Pause on hover
- Sound notifications
- Icon display

### Toast Duration Standards

- **Success**: 3000ms (3 seconds) - Quick confirmation
- **Info**: 4000ms (4 seconds) - Standard information
- **Warning**: 5000ms (5 seconds) - Important warnings
- **Error**: Shows dialog (requires acknowledgment)

---

## ModernProgressBar

Progress indicator with percentage display and ETA calculation.

### Current Features (Phase 5.4)

```python
from ui.components_v2 import ModernProgressBar

# Create progress bar
progress = ModernProgressBar()
progress.setValue(50)  # Set to 50%

# Theme support
progress.set_theme("dark")
```

### Enhanced API (Phase 5.5 Specification)

```python
from ui.components_v2 import ModernProgressBar

# Determinate mode (0-100%)
progress = ModernProgressBar(variant="primary", size="medium")
progress.set_value(75)

# Indeterminate mode (loading animation)
progress = ModernProgressBar()
progress.set_indeterminate(True)

# With label
progress.set_label("Processing files...")
progress.set_value(50)  # Shows "Processing files... 50%"

# With ETA calculation
import time
start_time = time.time()
for i in range(100):
    elapsed = time.time() - start_time
    progress.set_value(i)
    eta = progress.calculate_eta(i, 100, elapsed)
    # Shows "ETA: 2m 30s"

# Color variants
progress = ModernProgressBar(variant="success")  # Green
progress = ModernProgressBar(variant="warning")  # Yellow
progress = ModernProgressBar(variant="error")    # Red

# Size variants
progress = ModernProgressBar(size="small")   # 16px height
progress = ModernProgressBar(size="medium")  # 24px height
progress = ModernProgressBar(size="large")   # 32px height

# Striped animation
progress = ModernProgressBar(striped=True)

# Pause/resume
progress.pause()
progress.resume()

# Buffer mode (for streaming)
progress.set_buffer_value(50, 75)  # 50% played, 75% buffered
```

### Progress Bar Variants

- `VARIANT_PRIMARY` - Blue (default)
- `VARIANT_SUCCESS` - Green
- `VARIANT_WARNING` - Yellow
- `VARIANT_ERROR` - Red
- `VARIANT_INFO` - Blue

### Progress Bar Sizes

- `SIZE_SMALL` - 16px height
- `SIZE_MEDIUM` - 24px height (default)
- `SIZE_LARGE` - 32px height

### Progress Bar Features

✅ **Implemented:**
- Determinate mode (0-100%)
- Percentage display
- Theme support
- Font preset support

📋 **Phase 5.5 Enhancements:**
- Indeterminate mode
- Buffer mode
- Label support (inside/outside)
- Color variants (5 variants)
- Size variants (3 sizes)
- Striped animation
- ETA calculation
- Pause/resume support

---

## LoadingSpinner (ModernSpinner)

Animated loading indicator with multiple styles.

### Current Features (Phase 5.4)

```python
from ui.components_v2 import LoadingSpinner

# Create and start spinner
spinner = LoadingSpinner()
spinner.start()

# Stop spinner
spinner.stop()

# Theme support
spinner.set_theme("dark")
```

### Enhanced API (Phase 5.5 Specification)

```python
from ui.components_v2 import LoadingSpinner

# Size variants
spinner = LoadingSpinner(size="small")   # 24px
spinner = LoadingSpinner(size="medium")  # 32px (default)
spinner = LoadingSpinner(size="large")   # 48px
spinner = LoadingSpinner(size="xlarge")  # 64px

# Color variants
spinner = LoadingSpinner(color="primary")    # Blue
spinner = LoadingSpinner(color="success")    # Green
spinner = LoadingSpinner(color="warning")    # Yellow
spinner = LoadingSpinner(color="error")      # Red

# With text label
spinner = LoadingSpinner(text="Loading data...")
spinner.set_text("Processing...")

# Overlay mode (full-screen with backdrop)
spinner = LoadingSpinner(overlay=True)
spinner.show()  # Covers entire parent with semi-transparent backdrop

# With cancel button
def on_cancel():
    print("Cancelled")

spinner = LoadingSpinner(cancelable=True)
spinner.set_cancelable(True, on_cancel)

# Animation styles
spinner = LoadingSpinner(animation_style="spinner")  # Rotating arc (default)
spinner = LoadingSpinner(animation_style="dots")     # Three dots
spinner = LoadingSpinner(animation_style="bars")     # Bouncing bars
spinner = LoadingSpinner(animation_style="pulse")    # Pulsing circle

# Change animation style dynamically
spinner.set_animation_style("dots")
```

### Spinner Sizes

- `SIZE_SMALL` - 24px
- `SIZE_MEDIUM` - 32px (default)
- `SIZE_LARGE` - 48px
- `SIZE_XLARGE` - 64px

### Spinner Colors

- `COLOR_PRIMARY` - Blue (default)
- `COLOR_SECONDARY` - Gray
- `COLOR_SUCCESS` - Green
- `COLOR_WARNING` - Yellow
- `COLOR_ERROR` - Red

### Animation Styles

- `STYLE_SPINNER` - Rotating arc (default)
- `STYLE_DOTS` - Three animated dots
- `STYLE_BARS` - Bouncing bars
- `STYLE_PULSE` - Pulsing circle

### Spinner Features

✅ **Implemented:**
- Rotating arc animation
- Theme support
- Font preset support
- Start/stop control

📋 **Phase 5.5 Enhancements:**
- Size variants (4 sizes)
- Color variants (5 colors)
- Overlay mode with backdrop
- Text label support
- Cancel button support
- Multiple animation styles (4 styles)
- Smooth transitions

---

## Badge

Status badge for labels and counters.

### Current Features (Phase 5.4)

```python
from ui.components_v2 import Badge

# Create badge
badge = Badge("New", "success")
badge = Badge("5", "error")

# Update badge type
badge.set_type("warning")

# Theme support
badge.set_theme("dark")
```

### Enhanced API (Phase 5.5 Specification)

```python
from ui.components_v2 import Badge

# Variants
badge = Badge("Active", variant="success")   # Green
badge = Badge("Pending", variant="warning")  # Yellow
badge = Badge("Error", variant="error")      # Red
badge = Badge("Info", variant="info")        # Blue
badge = Badge("New", variant="primary")      # Primary blue
badge = Badge("Default", variant="default")  # Gray

# Sizes
badge = Badge("S", size="small")    # Small badge
badge = Badge("M", size="medium")   # Medium badge (default)
badge = Badge("L", size="large")    # Large badge

# Shapes
badge = Badge("Round", shape="rounded")  # Rounded corners (default)
badge = Badge("Pill", shape="pill")      # Pill shape (fully rounded)
badge = Badge("Square", shape="square")  # Square corners

# Counter mode with 99+ display
badge = Badge("5", variant="error")    # Shows "5"
badge = Badge("99", variant="error")   # Shows "99"
badge = Badge("150", variant="error")  # Shows "99+"

# Dot indicator mode (no text)
badge = Badge("", variant="success", dot_mode=True)  # Just a colored dot

# Pulse animation
badge = Badge("Live", variant="error", pulse=True)  # Pulsing animation

# Dismissible badge
def on_dismiss():
    print("Badge dismissed")

badge = Badge("Removable", dismissible=True)
badge.dismissed.connect(on_dismiss)

# With icon
badge = Badge("✓ Done", variant="success")
badge = Badge("⚠ Warning", variant="warning")
```

### Badge Variants

- `VARIANT_DEFAULT` - Gray (default)
- `VARIANT_PRIMARY` - Primary blue
- `VARIANT_SUCCESS` - Green
- `VARIANT_WARNING` - Yellow
- `VARIANT_ERROR` - Red
- `VARIANT_INFO` - Blue

### Badge Sizes

- `SIZE_SMALL` - Small badge
- `SIZE_MEDIUM` - Medium badge (default)
- `SIZE_LARGE` - Large badge

### Badge Shapes

- `SHAPE_ROUNDED` - Rounded corners (default)
- `SHAPE_PILL` - Pill shape (fully rounded)
- `SHAPE_SQUARE` - Square corners

### Badge Features

✅ **Implemented:**
- 5 variants (default, success, warning, error, info)
- Theme support
- Font preset support
- Type updates

📋 **Phase 5.5 Enhancements:**
- 6 variants (added primary)
- 3 sizes (small, medium, large)
- 3 shapes (rounded, pill, square)
- Icon support
- Dismissible badges
- Dot indicator mode
- Pulse animation
- Counter mode with 99+ display

---

## Theme Support

All feedback components support theme changes:

```python
# Components automatically respond to theme changes via V2SettingsBus
from ui.services import get_v2_settings_bus

settings_bus = get_v2_settings_bus()
settings_bus.theme_changed.emit("dark")  # All components update

# Manual theme update
component.set_theme("dark")
```

## Font Preset Support

All feedback components support font preset changes:

```python
# Components automatically respond to font preset changes
settings_bus.font_preset_changed.emit("large")  # All components update
```

## Accessibility

All feedback components follow WCAG 2.1 AA guidelines:

- **Color Contrast**: All text meets 4.5:1 contrast ratio
- **Focus Indicators**: 3px visible focus indicators
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels and roles
- **Touch Targets**: Minimum 44x44px for interactive elements

## Performance

- **Smooth Animations**: 60 FPS target
- **Efficient Rendering**: Minimal repaints
- **Memory Management**: Proper cleanup on dismiss
- **CPU Usage**: Optimized animation loops

## Best Practices

### Toast Notifications

1. **Use appropriate variants**: Match severity to variant
2. **Keep messages concise**: 1-2 sentences maximum
3. **Use action buttons sparingly**: Only for critical actions
4. **Position consistently**: Use same position throughout app
5. **Don't stack too many**: Limit to 3-4 visible toasts

### Progress Bars

1. **Show ETA when possible**: Helps user understand wait time
2. **Use indeterminate for unknown duration**: Don't fake progress
3. **Update frequently**: At least every 100ms for smooth animation
4. **Use appropriate variant**: Match color to operation type
5. **Add labels**: Explain what's being processed

### Loading Spinners

1. **Use overlay for blocking operations**: Prevents user interaction
2. **Add text labels**: Explain what's loading
3. **Provide cancel option**: For long operations
4. **Choose appropriate size**: Match context (small for inline, large for full-screen)
5. **Use appropriate animation**: Match app style

### Badges

1. **Keep text short**: 1-3 characters for counters, 1-2 words for labels
2. **Use 99+ for large numbers**: Prevents layout issues
3. **Use dot mode for indicators**: When text isn't needed
4. **Match variant to meaning**: Success=green, Error=red, etc.
5. **Use pulse sparingly**: Only for urgent/live updates

---

## Migration Guide

### From Phase 5.4 to Phase 5.5

Most existing code will continue to work. New features are opt-in:

```python
# Old code (still works)
Toast.success(parent, "Done!")

# New code (with enhancements)
Toast.success(parent, "Done!", position="top-right", dismissible=True)

# Old code (still works)
progress = ModernProgressBar()
progress.setValue(50)

# New code (with enhancements)
progress = ModernProgressBar(variant="success", size="large")
progress.set_label("Processing...")
progress.set_value(50)
```

---

## Examples

### Complete Toast Example

```python
from ui.components_v2 import Toast, ToastPosition

def save_file():
    try:
        # Save operation
        Toast.success(parent, "File saved successfully!", 
                     position=ToastPosition.TOP_RIGHT,
                     duration=3000)
    except Exception as e:
        def retry():
            save_file()
        
        Toast.error(parent, f"Failed to save: {str(e)}", 
                   action=("Retry", retry),
                   position=ToastPosition.TOP_RIGHT,
                   duration=6000)
```

### Complete Progress Bar Example

```python
from ui.components_v2 import ModernProgressBar
import time

# Create progress bar
progress = ModernProgressBar(variant="primary", size="large")
progress.set_label("Processing files...")
layout.addWidget(progress)

# Process with ETA
start_time = time.time()
total_files = 100

for i in range(total_files):
    # Process file
    time.sleep(0.1)
    
    # Update progress
    elapsed = time.time() - start_time
    progress.set_value(i + 1)
    eta = progress.calculate_eta(i + 1, total_files, elapsed)
    
    # Shows: "Processing files... 50% | ETA: 5s"

# Change to success variant when done
progress.set_variant("success")
progress.set_label("Complete!")
```

### Complete Loading Spinner Example

```python
from ui.components_v2 import LoadingSpinner

# Create overlay spinner
spinner = LoadingSpinner(
    size="large",
    color="primary",
    overlay=True,
    text="Loading data...",
    cancelable=True,
    animation_style="spinner"
)

def on_cancel():
    # Cancel operation
    spinner.stop()

spinner.set_cancelable(True, on_cancel)
spinner.start()

# Update text during operation
spinner.set_text("Processing...")

# Stop when done
spinner.stop()
```

### Complete Badge Example

```python
from ui.components_v2 import Badge

# Notification counter
notification_badge = Badge("5", variant="error", shape="pill")

# Update counter
def update_notifications(count):
    notification_badge.setText(str(count) if count <= 99 else "99+")

# Status indicator
status_badge = Badge("", variant="success", dot_mode=True, pulse=True)

# Dismissible tag
tag_badge = Badge("Python", variant="primary", shape="pill", dismissible=True)
tag_badge.dismissed.connect(lambda: print("Tag removed"))
```

---

## API Reference Summary

### Toast
- `Toast.info(parent, message, duration, position, **kwargs)`
- `Toast.success(parent, message, duration, position, **kwargs)`
- `Toast.warning(parent, message, duration, position, **kwargs)`
- `Toast.error(parent, message, duration, position, **kwargs)`

### ModernProgressBar
- `__init__(parent, variant, size, striped, show_percentage)`
- `set_value(value)`
- `set_indeterminate(indeterminate)`
- `set_label(text)`
- `set_variant(variant)`
- `set_size(size)`
- `calculate_eta(current, total, elapsed_seconds)`
- `pause()` / `resume()`

### LoadingSpinner
- `__init__(parent, size, color, overlay, text, cancelable, animation_style)`
- `start()` / `stop()`
- `set_text(text)`
- `set_overlay(overlay)`
- `set_cancelable(cancelable, callback)`
- `set_animation_style(style)`

### Badge
- `__init__(text, variant, parent, size, shape, dot_mode, pulse, dismissible)`
- `set_type(variant)`
- `setText(text)` - Inherited from QLabel

---

**Document Version**: 1.0  
**Phase**: 5.5 - Feedback Enhancement  
**Status**: ✅ Complete  
**Last Updated**: 2026-04-29

Made with Bob