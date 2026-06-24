"""
Configuration module for the application
"""

import os
import sys
from pathlib import Path

# Use the directory of the executable or script as the base directory
BASE_DIR = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.argv[0]))))
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure directories exist
for directory in [DATA_DIR, LOG_DIR, REPORTS_DIR]:
    directory.mkdir(exist_ok=True)

# Database configuration
DATABASE = {
    "path": str(DATA_DIR / "cases.db"),
    "backup_dir": str(DATA_DIR / "backups")
}

# File processing configuration
FILE_PROCESSING = {
    "input_dir": str(DATA_DIR / "input"),
    "output_dir": str(DATA_DIR / "output"),
    "archive_dir": str(DATA_DIR / "archive")
}

# Reports configuration
REPORTS = {
    "output_dir": str(REPORTS_DIR),
    "templates_dir": str(SRC_DIR / "reports" / "templates")
}

# Logging configuration
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "dir": str(LOG_DIR)
}

# Required columns for different file types
REQUIRED_COLUMNS = {
    "raw_file": [
        'Case Number',
        'Case',
        'Work Order Status',
        'Case Reason (Case) (Case)',
        'Closing Code',
        'Do Not Disturb (Contact) (Contact)',
        'Primary Email (Contact) (Contact)',
        'Contact Mobile Phone',
        'Work Order Type'
    ],
    "sms_replies": [
        "case_id",
        "reply_text",
        "reply_date"
    ]
}
