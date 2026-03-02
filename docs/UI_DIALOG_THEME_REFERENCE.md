# UI Dialog and Theme Reference Extracted from Functions.py

This document summarizes all dialog, popup, and UI widget settings, styles, and themes found in the ART Q Master Functions.py codebase. Use this as a reference for consistent UI design in other projects.

---

## General Dialog/Popup Patterns
- All dialogs inherit from `QDialog` (PyQt6)
- Layouts used: `QVBoxLayout`, `QHBoxLayout`, `QGridLayout`
- Widgets: `QLabel`, `QPushButton`, `QProgressBar`, `QGroupBox`, `QCheckBox`, `QInputDialog`
- Dialogs are typically sized with `.resize(width, height)` or `.setFixedSize(width, height)`
- Dialogs set window titles with `.setWindowTitle()`

---

## Font, Color, and StyleSheet Usage

### Fonts & Text Size
- Main action labels: `font-family: Arial; font-size: 14px; font-weight: bold;`
- Time labels: `font-size: 12px; color: White; font-weight: bold;`
- Unknown time: `font-size: 12px; color: White; font-style: italic;`
- Resume dialog message: `font-size: 15px; color: #161616;`

### Button Styles
- Default button height: 35-40px
- Resume button:
  ```css
  QPushButton {
      background-color: #0f62fe;
      color: white;
      font-weight: bold;
      padding: 12px 24px;
      border-radius: 5px;
      font-size: 15px;
  }
  QPushButton:hover { background-color: #0353e9; }
  ```
- Start Fresh button:
  ```css
  QPushButton {
      background-color: #e0e0e0;
      color: #161616;
      font-weight: bold;
      padding: 12px 24px;
      border-radius: 5px;
      font-size: 15px;
  }
  QPushButton:hover { background-color: #cacaca; }
  ```
- Play Voicemail button: `background-color: #d1e7dd; color: #0f5132; font-weight: bold;`

---

## Dialog Layouts & Windows
- Progress dialogs use `QProgressBar` with custom format: `Case {current_index}/{total_count} (%p%)`
- Navigation buttons (Next/Previous) in a horizontal layout
- Button groups for actions and resolutions are grouped in `QGroupBox` with `QGridLayout`
- Checkbox for "Add Case Note" at the bottom
- Dialogs for confirming actions (e.g., Resume) use emoji in button text and message

---

## Example Dialog Construction
```python
class Popup(QDialog):
    def __init__(self, ...):
        super().__init__()
        self.setWindowTitle("Case Reviewer")
        self.resize(400, 450)
        main_layout = QVBoxLayout(self)
        label = QLabel("Select Action for Case: ...")
        label.setStyleSheet("font-family: Arial; font-size: 14px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(label)
        # ... add more widgets ...
```

---

## Color Palette
- Primary blue: `#0f62fe` (Resume button)
- Hover blue: `#0353e9`
- Light gray: `#e0e0e0` (Start Fresh button)
- Hover gray: `#cacaca`
- Text black: `#161616`
- Light green: `#d1e7dd` (Play Voicemail)
- Green text: `#0f5132`
- White text for labels and buttons

---

## Other Notable UI Practices
- Use of emoji in button and label text for clarity (e.g., ✅, 🔄, 📋)
- All dialogs ensure a `QApplication` instance exists before showing
- Dialogs use `.exec()` or `.exec_()` for modal display
- Word wrap enabled for long messages

---

## Reference: Example Dialogs
- **Case Reviewer**: Large dialog with progress bar, navigation, grouped action buttons, and styled labels
- **Call Closing Code**: Compact dialog with grid of buttons, styled label, and special action buttons
- **Resume Dialog**: Fixed size, bold color-coded buttons, and clear message

---

**Use this as a style and layout reference for consistent dialog UI in PyQt6 projects.**
