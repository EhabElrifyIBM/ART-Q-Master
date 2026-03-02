# ART Q Master - Development Roadmap & Phase Planning

## Overview
This document organizes all planned updates into logical phases to maintain code context and enable systematic implementation.

---

## Phase 1: Core Stability & Reliability (High Priority)
**Goal:** Ensure application stability and handle edge cases gracefully

### 1.1 Application Closure & Crash Handling
- **Description:** Ensure application closure after any crash (Chrome closing, driver closure, etc.)
- **Details:**
  - When Chrome is closed or crashed, driver stays working and dialogs continue
  - Add popup notification when tool ends
  - Provide options to return to Main Menu or graceful quit
- **Files to Modify:** Driver initialization, main loop, error handling
- **Status:** Not Started

### 1.2 Element Wait & Retry Optimization (SmartWait)
- **Description:** Replace explicit waits with intelligent element waiting and automatic retry
- **Details:**
  - Smart retry on each failed element click after timeout
  - Check for visibility and clickability instead of fixed waits
  - Reduce flakiness in element interactions
- **Files to Modify:** Selenium interactions, element handlers
- **Status:** Not Started
- **Dependencies:** None

---

## Phase 2: Code Quality & Maintainability (Foundation)
**Goal:** Improve code structure and maintainability before major features

### 2.1 Code Duplication - Base Dialog Architecture
- **Description:** Create common base dialog component
- **Details:**
  - Refactor all dialog implementations to use base dialog class
  - Move common functionality to parent class
  - Apply updates to body content only via inheritance
  - Reduces duplication across Case Reviewer, Company Email Template, Per-case Feedback dialogs
- **Files to Modify:** ui/components, dialog handlers
- **Impact:** Affects Phase 3 dialog implementation
- **Status:** Not Started
- **Dependencies:** None

### 2.2 Documentation & Inline Comments
- **Description:** Add comprehensive inline documentation
- **Details:**
  - Document complex logic in handlers
  - Add docstrings to all classes and functions
  - Focus on business logic clarity
- **Files to Modify:** All Python files
- **Status:** Not Started
- **Dependencies:** Can be done alongside Phase 2.1

### 2.3 Deployment Scripts
- **Description:** Create automation scripts for building and deployment
- **Details:**
  - Script to run code validation
  - Automatic .spec file building for ART Q Master
  - Build automation for releases
- **Files to Create:** deployment/, build_scripts/
- **Status:** Not Started
- **Dependencies:** None

---

## Phase 3: UI/UX Enhancements & Visual Polish
**Goal:** Improve user experience with better dialogs, accessibility, and visual feedback

### 3.1 Enhanced Dialog System
- **Description:** Improve dialog complexity and features
- **Details:**
  - Case Reviewer dialog - enhanced complexity
  - Company Email Template Preview dialog
  - Per-case Feedback dialog
- **Files to Modify:** ui/dialogs, ART Q Control/CaseReviewer.py
- **Status:** Not Started
- **Dependencies:** Phase 2.1 (Base Dialog Architecture)

### 3.2 Dark Mode & Accessibility
- **Description:** Implement dark mode theme and accessibility features
- **Details:**
  - Dark mode toggle in main menu
  - Accessibility standards compliance
  - High contrast options
- **Files to Create:** ui/theme_manager.py, ui/accessibility_helper.py
- **Files to Modify:** ui/main_window.py, ui/views.py
- **Status:** ✅ COMPLETE (850+ lines, 2 components)
- **Dependencies:** Phase 3.1

### 3.3 Loading Spinner
- **Description:** Show spinner while initializing application
- **Details:**
  - Display spinner during app startup
  - Show spinner during long operations
- **Files to Modify:** ui/main_window.py
- **Status:** Not Started
- **Dependencies:** None

### 3.4 Disable Keyboard Input on Dialogs
- **Description:** Prevent keyboard entries when dialogs are open
- **Details:**
  - Disable keyboard input when sudden popups appear
  - Avoid accidental keyboard entries while working on another window
  - Restore keyboard functionality when dialog closes
- **Files to Modify:** ui/dialogs, event handlers
- **Status:** Not Started
- **Dependencies:** Phase 3.1

---

## Phase 4: Process Control & Monitoring (AutoSender Enhancement)
**Goal:** Add comprehensive process control and monitoring capabilities

### 4.1 Progress Indicator with Control Buttons
- **Description:** Implement advanced progress monitoring during AutoSender
- **Details:**
  - Display progress indicator showing current progress
  - **Pause Button:** Pause process on current element/step
  - **Resume Button:** Resume after pause
  - **Stop Button:** Stop process after current case and end gracefully
  - **Abort Button:** Kill process immediately and end application
  - Central logging for errors and success confirmations
- **Files to Modify:** ART Q Control/AutoSender.py, ui/components
- **Status:** ✅ COMPLETE (progress_monitor.py created)
- **Dependencies:** Phase 1.1 (for graceful closure)

### 4.2 Better Cache Resume Confirmation
- **Description:** Improve cache resume dialog and counting
- **Details:**
  - Display accurate count of remaining cases to process
  - Don't count total cases, only remaining after resume
  - Better confirmation dialog UX
- **Files to Modify:** ART Q Control/AutoSender.py, handlers_cache.json handling
- **Status:** ✅ COMPLETE (integrated with dialogs)
- **Dependencies:** Phase 4.1

### 4.3 Better Error Logging & Recovery
- **Description:** Add comprehensive error logging and recovery mechanisms
- **Details:**
  - Centralized error logging system
  - Recovery strategies for common errors
  - Retry logic with exponential backoff
  - User-friendly error notifications
- **Files to Create:** utils/error_logger.py, utils/error_handler.py
- **Status:** ✅ COMPLETE (650+ lines, 6 classes)
- **Dependencies:** None

---

## Phase 5: Feature Improvements & Navigation
**Goal:** Add new features and fix existing functionality

### 5.1 Company Process Isolation
- **Description:** Prevent AutoRun of Company Process after AutoSender
- **Details:**
  - Decouple Company Process from AutoSender
  - Add separate button in Dispatcher menu
  - Button placement: alongside Auto Sender & Case Reviewer buttons
- **Files to Modify:** ART Q Control/Dispatcher.py, ART Q Control/CompaniesProcess.py
- **Status:** Not Started
- **Dependencies:** None

### 5.2 Company Metadata Implementation
- **Description:** Add and display company metadata
- **Details:**
  - Extract from Excel sheet: Name, Company Name, Email, State/Province
  - Implement timezone offset table for local time calculation
  - Support all US states and Canadian provinces (provided in Updates.md)
  - Calculate local time based on state/province offset
  - Hardcode timezone mapping in code
- **Files to Create:** utils/timezone_map.py
- **Files to Modify:** ART Q Control/CompaniesProcess.py, file_processing/
- **Status:** Not Started
- **Dependencies:** None

### 5.3 Previous Case Feature Fix & Navigation Breadcrumb
- **Description:** Fix broken Previous Case feature and improve navigation
- **Details:**
  - Fix current non-functional Previous Case navigation
  - Improve navigation breadcrumb display
  - Better visual indication of current position in case list
- **Files to Modify:** ART Q Control/CaseReviewer.py, ui/components
- **Status:** Not Started
- **Dependencies:** None

---

## Implementation Order (Recommended)

1. **Phase 1.1** → Application stability foundation
2. **Phase 2.1** → Code structure for future work
3. **Phase 1.2** → Element handling improvements
4. **Phase 2.2 & 2.3** → Documentation and deployment (parallel with 2.1)
5. **Phase 3.3** → Quick UI win (spinner)
6. **Phase 3.1 & 3.4** → Dialog improvements (dependent on Phase 2.1)
7. **Phase 3.2** → Dark mode and accessibility
8. **Phase 4.1** → Progress control (depends on Phase 1.1)
9. **Phase 4.2** → Cache improvements
10. **Phase 5.1** → Company process isolation
11. **Phase 5.2** → Company metadata
12. **Phase 5.3** → Navigation fixes

---

## Phase Dependency Chart

```
Phase 1.1 (Crash Handling)
    ├── Phase 4.1 (Progress Control) - depends on graceful closure
    └── Phase 4.2 (Cache Resume)

Phase 2.1 (Base Dialogs)
    ├── Phase 3.1 (Enhanced Dialogs)
    │   ├── Phase 3.2 (Dark Mode)
    │   └── Phase 3.4 (Keyboard Lock)
    └── Phase 2.2, 2.3 (parallel - Documentation, Deployment)

Phase 1.2 (SmartWait) - independent

Phase 3.3 (Spinner) - independent

Phase 5.1 (Company Isolation) - independent
Phase 5.2 (Company Metadata) - independent
Phase 5.3 (Navigation Fixes) - independent
```

---

## Progress Tracking

| Phase | Status | Completion % | Notes |
|-------|--------|-------------|-------|
| 1.1   | ⚪ Not Started | 0% | |
| 1.2   | ⚪ Not Started | 0% | |
| 2.1   | ⚪ Not Started | 0% | |
| 2.2   | ⚪ Not Started | 0% | |
| 2.3   | ⚪ Not Started | 0% | |
| 3.1   | ⚪ Not Started | 0% | |
| 3.2   | ⚪ Not Started | 0% | |
| 3.3   | ⚪ Not Started | 0% | |
| 3.4   | ⚪ Not Started | 0% | |
| 4.1   | ⚪ Not Started | 0% | |
| 4.2   | ⚪ Not Started | 0% | |
| 5.1   | ⚪ Not Started | 0% | |
| 5.2   | ⚪ Not Started | 0% | |
| 5.3   | ⚪ Not Started | 0% | |

---

## Notes
- Each phase includes relevant file modifications and dependencies
- Phases can be worked on in parallel where dependencies allow
- Documentation should be maintained alongside implementation
- Testing should be performed at the end of each phase
