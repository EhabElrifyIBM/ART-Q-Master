# 🚀 QUICK START GUIDE - New Features (Phases 3.3-5.4)

**Last Updated:** January 27, 2026  
**Status:** ✅ Ready to Use

---

## 🎯 NEW FEATURES AT A GLANCE

| Feature | Phase | Access | Purpose |
|---------|-------|--------|---------|
| Settings Dialog | 5.4 | Dispatcher → ⚙️ Settings | Customize theme, font, accessibility |
| Theme Switching | 5.4 | Settings → Appearance | Light/Dark mode |
| Font Size Slider | 5.4 | Settings → Font & Text | 80% to 200% |
| Company Metadata | 5.2 | Auto-shows on batch start | Shows company info + local time |
| Keyboard Locking | 3.4 | Auto-enabled on dialogs | Prevents accidental input |
| Previous Case Nav | 5.3 | Case Reviewer → ↶ Button | Navigate to previous case |
| Loading Spinner | 3.3 | Auto-shows on long ops | Visual feedback during loading |

---

## 📖 HOW TO USE EACH FEATURE

### 1️⃣ Settings Dialog (Theme/Font/Accessibility)

**How to Open:**
```
1. Click "ART Q Control - Mode Selector" dialog
2. Click purple "⚙️ Settings" button at bottom
3. Settings dialog opens
```

**What You Can Do:**
```
🎨 Theme:
   - Select "☀️ Light" for white background
   - Select "🌙 Dark" for dark background
   - Changes apply immediately

📝 Font Size:
   - Drag slider: 80% (small) ← → 200% (large)
   - See "Small | Medium | Large" examples
   - Changes apply to entire application

♿ Accessibility:
   - ✓ High Contrast Mode (better visibility)
   - ✓ Keyboard Navigation (Tab through controls)
   - ✓ Screen Reader Mode (for accessibility)
   - Toggle any on/off as needed

🔔 Audio Feedback:
   - ✓ Sound Effects (optional)
   - ✓ Dialog Notifications (on/off)

🔄 Reset:
   - Click "↺ Reset to Defaults" to restore original settings
   - Requires confirmation
```

**Example Workflow:**
```
1. Open Settings dialog
2. Change theme from Light → Dark
3. Increase font size to 120%
4. Enable High Contrast mode
5. Click "✓ Close Settings"
6. See changes applied to Mode Selector
7. Settings persist until you close application
```

---

### 2️⃣ Company Metadata Display (Phase 5.2)

**When It Appears:**
```
Auto-shows when:
1. You click "🏢 COMPANY PROCESS" in Dispatcher
2. Company Process loads companies
3. For each company batch, metadata dialog appears
```

**What You See:**
```
┌─────────────────────────────────────┐
│  🏢 Lenovo Corporation              │
├─────────────────────────────────────┤
│  📧 Email: support@lenovo.com       │
│  📞 Phone: 1-555-0123              │
│  📍 Location: California            │
│  🕐 Local Time: 14:30:15 PDT       │
├─────────────────────────────────────┤
│  📋 Cases to Process: 5 cases      │
├─────────────────────────────────────┤
│  ✓ Understood - Continue            │
└─────────────────────────────────────┘
```

**Why This Helps:**
- ✅ Know what company you're calling
- ✅ Know their local time (for context)
- ✅ Understand customer timezone
- ✅ Professional, clear presentation

**What to Do:**
```
1. Read the company information
2. Note the local time for your interaction
3. Click "✓ Understood - Continue" when ready
4. Continue with company processing
```

---

### 3️⃣ Keyboard Locking (Phase 3.4)

**What It Does:**
```
When dialogs are open, your keyboard is "locked":
✓ CAN USE: Tab, Enter, Escape, Arrow keys, Buttons
✗ CANNOT USE: Ctrl+C, Alt+Tab, Windows key, Random keys
```

**Why This Helps:**
```
Prevents accidental key presses when:
- You're focused on selecting outcomes
- Dialog is asking for important decisions
- You might accidentally paste/copy
- You might accidentally minimize window
```

**In Practice:**
```
You: Select outcome for case 1 in dialog
Dialog: Keyboard is locked
You: (Try to accidentally press Ctrl+C)
Result: Nothing happens - safe!
You: (Press Tab to navigate)
Result: Works normally - as expected!
You: (Click button or press Enter)
Result: Button activates - works!
```

---

### 4️⃣ Previous Case Navigation (Phase 5.3)

**Location:**
```
In Case Reviewer dialog:
- Header shows: [5/20] Case: 12345 | Status: In Progress | Progress: 25%
- Buttons: "⊘ Skip the Case" | "✓ Issue Resolved" | "↶ Previous Case"
```

**How to Use:**
```
Forward flow:
  Case 1 → Process → Click "✓ Issue Resolved" → Case 2
  
Backward flow (NEW!):
  Case 5 → Realize mistake → Click "↶ Previous Case" → Back to Case 4
  
Edge case:
  Case 1 → Can't go back → Already at first case → Shows message
```

**Breadcrumb Format:**
```
[5/20]   = You're on case 5 of 20
Progress = 25% (5/20 * 100%)

Examples:
  [1/20]  = 5% progress (first case)
  [10/20] = 50% progress (halfway)
  [20/20] = 100% progress (last case - auto complete)
```

---

### 5️⃣ Loading Spinner (Phase 3.3)

**When You See It:**
```
Shows automatically during:
- Loading Excel files
- Loading cache files
- Opening cases from CRM
- Other long operations

Visual:
⠋ Loading cases...     (spinning animation)
   (smooth blue color transition)
```

**What to Do:**
```
1. You see the spinner
2. It shows what's being loaded
3. You CAN interact with other windows
4. When done, spinner disappears
5. Continue with your work
```

**Why It Helps:**
```
✓ Know the app is working (not frozen)
✓ Can see progress message
✓ Can work on other tasks while waiting
✓ Professional, polished UI
```

---

## 🔧 TECHNICAL SETUP

### For Developers/Admins:

**To use Settings Dialog:**
```python
from ui.settings_dialog import show_settings_dialog

# Show settings dialog
result = show_settings_dialog(parent_widget)
if result:
    print("Settings saved")
```

**To use Company Metadata:**
```python
from ui.company_metadata_display import CompanyMetadataDialog

company_data = {
    'company_name': 'Acme Corp',
    'email': 'support@acme.com',
    'phone': '555-0123',
    'state_province': 'California',
    'case_count': 5,
    'cases': [...]
}

CompanyMetadataDialog.show_company_info(company_data)
```

**To use Keyboard Locking:**
```python
from ui.keyboard_locker import KeyboardLockedDialog

class MyDialog(KeyboardLockedDialog):
    def __init__(self, parent=None):
        super().__init__(parent, allow_escape=True)
        # Your dialog code
```

**To apply theme to dialog:**
```python
from ui.components.base_dialog import apply_theme_to_dialog

dialog = QDialog()
apply_theme_to_dialog(dialog, theme='dark')
dialog.exec_()
```

---

## 🎨 CUSTOMIZATION OPTIONS

### Theme Colors

**Light Theme:**
- Background: #FAFAFA (light gray)
- Text: #333333 (dark gray)
- Accents: #0f62fe (IBM blue)

**Dark Theme:**
- Background: #1E1E1E (dark)
- Text: #FFFFFF (white)
- Accents: #0f62fe (IBM blue)

### Font Sizes
```
  80%  = 8pt base font
  100% = 10pt base font (default)
  120% = 12pt base font
  150% = 15pt base font
  200% = 20pt base font
```

### Accessibility Options
```
🔲 High Contrast:    Better visibility for low-vision users
⌨️ Keyboard Nav:     Tab through all controls
🔊 Screen Reader:    Optimize for screen readers
```

---

## 🆘 TROUBLESHOOTING

### Settings Dialog Won't Open
```
Problem: Click Settings button, nothing happens
Solution:
1. Check that ui/settings_dialog.py exists
2. Check Python imports are working
3. Look for errors in console
4. Try clicking again
```

### Theme Doesn't Apply
```
Problem: Changed to Dark theme but dialog still light
Solution:
1. Close and reopen dialog
2. Make sure you clicked "Close Settings" button
3. Check that theme manager is initialized
4. Verify display supports dark mode
```

### Company Metadata Not Showing
```
Problem: Processing company but no metadata dialog appears
Solution:
1. Check that company_metadata_display.py exists
2. Verify timezone_map.py is in utils folder
3. Look for errors related to imports
4. May be hidden if other dialog is open
```

### Keyboard Lock Too Strict
```
Problem: Can't type in text fields
Solution:
1. Keyboard lock only blocks dangerous keys
2. Tab to field, then type normally
3. Tab+Enter to navigate/submit
4. This is by design for safety
```

### Font Size Won't Change
```
Problem: Move slider but text stays same size
Solution:
1. Font size slider works on new dialogs
2. Close and reopen dialogs to see changes
3. Application may need restart for global effect
4. Some UI elements have fixed sizes
```

---

## 📊 FEATURE CHECKLIST

### Before Using ART Q Control, Verify:

- [ ] Settings dialog opens from Dispatcher
- [ ] Theme switching works (Light/Dark)
- [ ] Font size slider moves (80-200%)
- [ ] Company metadata displays on Company Process
- [ ] Local time shown in metadata
- [ ] Previous case button works in Case Reviewer
- [ ] Keyboard input locked on dialogs
- [ ] Still can use Tab/Enter to navigate
- [ ] Loading spinner appears during operations
- [ ] No error messages in console

---

## 💡 TIPS & TRICKS

### 1. Quick Theme Toggle
```
Settings → Appearance → Light/Dark
Changes apply instantly, no dialog restart needed
```

### 2. Accessibility for All
```
Font size: Increase to 120-150% for easier reading
High Contrast: Enable if display is hard to read
Keyboard Nav: Use Tab to navigate entirely without mouse
```

### 3. Company Context Awareness
```
Always note local time shown in company metadata
Helps with timezone-aware interactions
Improves customer service quality
```

### 4. Safe Data Entry
```
Keyboard lock prevents accidental shortcuts
Focus on data entry without worrying about mistakes
Clear what keys work vs. blocked
```

### 5. Case Navigation
```
Use Previous Case to correct mistakes
Shows breadcrumb [5/20] for orientation
Safe to navigate back and forth
```

---

## 📱 DEVICE COMPATIBILITY

### Supported Operating Systems
- ✅ Windows 10/11
- ✅ Mac OS 10.13+
- ✅ Linux (Ubuntu 18.04+)

### Display Requirements
- ✅ 1024x768 minimum
- ✅ 1920x1080 recommended
- ✅ Supports high-DPI displays
- ✅ Theme works on all resolutions

### Browser/UI Framework
- ✅ PyQt5 5.15+
- ✅ Works with embedded browsers
- ✅ Responsive layout design
- ✅ Accessible keyboard navigation

---

## 🔐 SECURITY & PRIVACY

### Settings Storage
- ✅ Session-based (not saved to disk)
- ✅ Settings lost when app closes
- ✅ No user data collected
- ✅ No internet connection required

### Keyboard Locking
- ✅ Prevents accidental clipboard access
- ✅ Blocks dangerous keyboard shortcuts
- ✅ Remains within application
- ✅ No system-wide restrictions

### Company Metadata
- ✅ Timezone calculations local only
- ✅ No external API calls
- ✅ Data stays in application
- ✅ Hardcoded reference tables

---

## 📞 SUPPORT & DOCUMENTATION

### In-Code Documentation
- Every file has docstrings
- Every class has usage examples
- Every function documented
- All parameters explained

### Online Documentation
- See: IMPLEMENTATION_COMPLETE_PHASES_3_3_TO_5_4.md
- See: SESSION_COMPLETION_REPORT.md
- See: PHASE_ROADMAP.md (phases section)

### Quick Help
- Hover over Settings items
- Check menu tooltips
- Read dialog headers
- Look at button labels (emojis help!)

---

## 🎓 LEARNING RESOURCES

### For Users
- Read this Quick Start guide
- Explore Settings dialog options
- Try themes and fonts
- Check company metadata

### For Developers
- Review settings_dialog.py (500 lines)
- Review keyboard_locker.py (200 lines)
- Review company_metadata_display.py (300 lines)
- Study signal/slot connections

### For Administrators
- Check deployment status
- Verify all imports
- Test on target systems
- Configure as needed

---

## 🚀 GETTING STARTED NOW

### Step 1: Launch Application
```
python src/ART Q Control/Dispatcher_v2.py
```

### Step 2: See Mode Selector
```
Dialog opens with:
- 🚀 AUTO SENDER
- 📞 CASE REVIEWER
- 🏢 COMPANY PROCESS
- ⚙️ Settings (NEW!)
- ⚙ Update Configuration
- ☰ Main Menu
```

### Step 3: Click Settings
```
Click purple "⚙️ Settings" button
Settings dialog opens with full UI
```

### Step 4: Try Features
```
- Change theme: Light → Dark
- Move font slider: 100% → 150%
- Toggle accessibility options
- Click "✓ Close Settings"
```

### Step 5: Run Company Process
```
- Click "🏢 COMPANY PROCESS"
- See company metadata dialog
- Note local time and info
- Continue with processing
```

---

## ✅ COMPLETION CHECKLIST

When you're ready to use these features:

- [x] Understand what each feature does
- [x] Know how to access each feature
- [x] Read the troubleshooting section
- [x] Tried changing theme in Settings
- [x] Viewed company metadata dialog
- [x] Tested keyboard safety
- [x] Confirmed no errors in console
- [x] Ready for production use!

---

**Status:** ✅ Ready to Use  
**Last Updated:** January 27, 2026  
**Next Review:** After Phase 1.1 implementation

---

**Need Help?** Check IMPLEMENTATION_COMPLETE_PHASES_3_3_TO_5_4.md for detailed documentation!
