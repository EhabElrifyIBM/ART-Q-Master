# Assigner V2 - Standalone Processor & UI

## Overview
Assigner V2 is a standalone implementation combining `FileProcessor` and `FinalProcessor` into a single module, with a self-contained PyQt5 UI for independent testing and usage.

## Files

### 1. `assigner_processor.py` (457 KB)
Combined processor module containing:
- **FileProcessor**: Main file processing engine
  - Handles raw file validation and transformation
  - Manages SMS/Email reply processing
  - Applies DND (Do Not Disturb) rules
  - Implements Bank/Sutherland case balancing
  - Assigns cases to handlers
  
- **FinalProcessor**: Final output generation
  - Creates Excel workbooks with formatted sheets
  - Manages Handler sheets with preservation logic
  - Creates Companies sheet with duplicate detection
  - Generates Summary and Counter sheets
  - Applies validation dropdowns

### 2. `main_window_assigner.py` (51 KB)
Standalone PyQt5 UI for Assigner V2 that includes:
- **MainWindow**: Primary application interface with:
  - File selection (raw files, previous assignments, SMS/Email replies)
  - Handler management and filtering
  - Progress tracking and real-time logging
  - IBM-themed styling
  
- **FileProcessingWorker**: QThread-based worker for non-blocking execution
  - Runs FileProcessor.validate_files() and FileProcessor.process_files()
  - Emits real-time log signals to UI
  - Handles success/error reporting

### 3. `__init__.py`
Package initialization file for module imports.

## Key Modifications from Original

### Import Changes
The main modification from the original files is the import path:

**Original** (in main_window.py):
```python
from ..file_processing.processor import FileProcessor
```

**Assigner V2** (in main_window_assigner.py):
```python
from .assigner_processor import FileProcessor
```

This allows the UI to import the combined processor from the same folder level, enabling standalone execution.

## Usage

### Integrated with Main Application
The Assigner V2 module can be embedded in the main application:

```python
from src.Assigner.main_window_assigner import MainWindow
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
```

### Standalone Execution
Run the Assigner V2 UI directly without the main application:

```bash
cd src/Assigner
python -c "from main_window_assigner import MainWindow; from PyQt5.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); w = MainWindow(); w.show(); sys.exit(app.exec_())"
```

Or create a simple launcher script:

```python
#!/usr/bin/env python
import sys
from PyQt5.QtWidgets import QApplication
from main_window_assigner import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
```

## Architecture

### Execution Flow
1. **User starts UI** → MainWindow initializes FileProcessor instance
2. **User selects files and handlers** → UI prepares parameters
3. **User clicks Process** → FileProcessingWorker thread spawned
4. **Worker runs**:
   - Calls `processor.validate_files()` for input validation
   - Calls `processor.process_files()` for main processing
   - FinalProcessor internally called for output generation
   - Emits `log_signal` for real-time UI updates
5. **Results generated** → Excel output file created

### Class Integration
```
MainWindow (PyQt5 UI)
    ↓
FileProcessingWorker (QThread)
    ↓
FileProcessor (from assigner_processor.py)
    ↓
FinalProcessor (from assigner_processor.py)
    ↓
Excel Output
```

## Processor Classes

### FileProcessor Methods
- `__init__()`: Initialize with canonical field mappings
- `setup_logging()`: Configure logging
- `validate_files()`: Validate input file structure
- `process_files()`: Main processing pipeline
- `load_previous_file()`: Load previous assignments
- `process_sms_replies()`: Handle SMS responses
- `process_email_replies()`: Handle email responses
- `assign_handlers()`: Assign cases to handlers
- `_apply_bank_sutherland_rule()`: Apply business rules
- `_apply_dnd_actions_and_status()`: Apply DND rules
- `format_output_data()`: Prepare output columns

### FinalProcessor Methods
- `process_final_output()`: Orchestrate final processing
- `create_handler_sheets_from_processed_data()`: Generate per-handler sheets
- `create_companies_sheet_with_preservation()`: Email duplicate detection
- `create_counters_sheet()`: Generate statistics
- `create_summary_sheet()`: Generate processing report
- `add_validation_dropdowns()`: Add Excel data validation lists

## Dependencies

**Python Packages**:
- PyQt5 (UI framework)
- pandas (data processing)
- openpyxl (Excel manipulation, with fallback)
- pytz (timezone handling)

**Standard Library**:
- datetime, os, json, logging, re, math, itertools, collections

## Testing

### Basic Import Test
```python
from src.Assigner.assigner_processor import FileProcessor, FinalProcessor

processor = FileProcessor()
print("FileProcessor initialized successfully")

final_processor = FinalProcessor()
print("FinalProcessor initialized successfully")
```

### UI Test
```bash
python -m PyQt5.QtWidgets.qpy -c "
from src.Assigner.main_window_assigner import MainWindow
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())
"
```

## Notes

- Both FileProcessor and FinalProcessor maintain all original logic and functionality
- The combined file is an exact concatenation of both processors with deduplicated imports
- UI functionality is identical to the main application version
- openpyxl is optional; a fallback mechanism is included if unavailable
- The module is fully independent and can be deployed separately from the main application

## File Locations

```
src/
├── Assigner/
│   ├── __init__.py                    (package marker)
│   ├── assigner_processor.py          (447 KB - combined processors)
│   ├── main_window_assigner.py        (51 KB - standalone UI)
│   └── README.md                      (this file)
└── file_processing/
    ├── processor.py                   (original)
    └── final_processor.py             (original)
```

## Status

✅ Assigner V2 fully implemented
✅ Both FileProcessor and FinalProcessor combined
✅ UI wired to combined processor
✅ Import paths adjusted for standalone execution
✅ All dependencies preserved
✅ Ready for testing and deployment
