# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — ART Q Master v2
====================================

Modules bundled
---------------
- ART Q Control  (AutoSender, CaseReviewer, CompaniesProcess, Dispatcher …)
- Archiver
- Merger  / DailyMerger  / MonthlyMerger
- Assigner
- Reach Rate Calculator
- Shared utils, config, UI design-system

Build
-----
    pyinstaller art_q_master_v2.spec

Output
------
    dist/ART Q Master v2/ART Q Master v2.exe  (one-folder bundle)
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

block_cipher  = None
project_root  = os.getcwd()
src_v2_path   = os.path.join(project_root, "src_v2")
assets_path   = os.path.join(project_root, "assets")
icon_path     = os.path.join(assets_path, "ibm_logo.png")

# ---------------------------------------------------------------------------
# Data files
# ---------------------------------------------------------------------------

datas = [
    # Application config files
    (os.path.join(src_v2_path, "config.json"),                          "."             ),
    (os.path.join(src_v2_path, "ART Q Control", "config.json"),         "ART Q Control" ),

    # Assets (icons, images)
    (assets_path, "assets"),
]

# Third-party runtime data
datas += collect_data_files("webdriver_manager")
datas += collect_data_files("selenium")

# ---------------------------------------------------------------------------
# Hidden imports
# ---------------------------------------------------------------------------

hiddenimports = [

    # ------------------------------------------------------------------
    # Standard-library modules that PyInstaller sometimes misses
    # ------------------------------------------------------------------
    "encodings",
    "multiprocessing",
    "threading",
    "subprocess",
    "platform",
    "ctypes",
    "json",
    "pathlib",
    "collections",
    "dataclasses",
    "enum",
    "traceback",
    "logging",
    "re",
    "shutil",
    "copy",
    "datetime",
    "time",
    "zoneinfo",

    # ------------------------------------------------------------------
    # PyQt5 — top-level modules only (PyInstaller resolves sub-symbols)
    # ------------------------------------------------------------------
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "PyQt5.sip",

    # ------------------------------------------------------------------
    # Selenium & WebDriver
    # ------------------------------------------------------------------
    "selenium",
    "selenium.webdriver",
    "selenium.webdriver.chrome",
    "selenium.webdriver.chrome.service",
    "selenium.webdriver.chrome.options",
    "selenium.webdriver.common.by",
    "selenium.webdriver.common.keys",
    "selenium.webdriver.common.action_chains",
    "selenium.webdriver.support",
    "selenium.webdriver.support.ui",
    "selenium.webdriver.support.expected_conditions",
    "selenium.common.exceptions",
    "webdriver_manager",
    "webdriver_manager.chrome",

    # ------------------------------------------------------------------
    # Excel / data processing
    # ------------------------------------------------------------------
    "pandas",
    "pandas.core",
    "pandas.core.frame",
    "pandas.core.series",
    "pandas.io",
    "pandas.io.excel",
    "openpyxl",
    "openpyxl.utils",
    "openpyxl.reader",
    "openpyxl.reader.excel",
    "openpyxl.writer",
    "openpyxl.writer.excel",
    "openpyxl.styles",
    "openpyxl.worksheet",
    "openpyxl.workbook",
    "xlsxwriter",

    # ------------------------------------------------------------------
    # Timezone
    # ------------------------------------------------------------------
    "pytz",

    # ------------------------------------------------------------------
    # GUI automation
    # ------------------------------------------------------------------
    "pyautogui",

    # ------------------------------------------------------------------
    # Tkinter (legacy modules)
    # ------------------------------------------------------------------
    "tkinter",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.ttk",
    "tkinter.scrolledtext",
    "tkinter.font",

    # ------------------------------------------------------------------
    # Charts (Reach Rate Calculator)
    # ------------------------------------------------------------------
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.backends.backend_qt5agg",

    # ------------------------------------------------------------------
    # Application — entry point + version
    # ------------------------------------------------------------------
    "main",
    "version",

    # ------------------------------------------------------------------
    # UI modules
    # ------------------------------------------------------------------
    "ui",
    "ui.main_menu",
    "ui.main_window",
    "ui.shell",
    "ui.theme_manager",
    "ui.theme",
    "ui.typography",
    "ui.typography_mixin",
    "ui.services",
    "ui.settings",
    "ui.settings_dialog",
    "ui.settings_dialog_v2",
    "ui.design_system",
    "ui.responsive",
    "ui.keyboard_shortcuts",
    "ui.keyboard_locker",
    "ui.accessibility_helper",
    "ui.company_metadata_display",
    "ui.feedback_guide",
    "ui.views",

    # UI Components
    "ui.components",
    "ui.components.base_dialog",
    "ui.components.dialog_components",
    "ui.components.loading_spinner",
    "ui.components.progress_monitor",
    "ui.components.case_review_dialog",
    "ui.components.company_email_dialog",
    "ui.components.feedback_dialog",

    # UI Components V2
    "ui.components_v2",
    "ui.components_v2.buttons",
    "ui.components_v2.cards",
    "ui.components_v2.dialogs",
    "ui.components_v2.inputs",
    "ui.components_v2.tables",
    "ui.components_v2.navigation",
    "ui.components_v2.feedback",

    # ------------------------------------------------------------------
    # ART Q Control
    # ------------------------------------------------------------------
    "ART Q Control",
    "ART Q Control.config_loader",
    "ART Q Control.config_manager",
    "ART Q Control.SharedFunctions",
    "ART Q Control.AutoSender",
    "ART Q Control.AutoSender_v2",
    "ART Q Control.CaseReviewer",
    "ART Q Control.CaseReviewer_v2",
    "ART Q Control.CompaniesProcess",
    "ART Q Control.CompaniesProcess_v2",
    "ART Q Control.Dispatcher",
    "ART Q Control.Dispatcher_v2",
    "ART Q Control.Functions",
    "ART Q Control.Main",
    "ART Q Control.logger",
    "ART Q Control.ibm_theme",
    "ART Q Control.runtime",

    # ------------------------------------------------------------------
    # Archiver
    # ------------------------------------------------------------------
    "Archiver",
    "Archiver.Archiver",
    "Archiver.archiver_window",
    "Archiver.archiver_service",
    "Archiver.run_archiver",
    "Archiver.components",
    "Archiver.components.file_selector",
    "Archiver.components.analysis_view",
    "Archiver.components.export_dialog",

    # ------------------------------------------------------------------
    # Merger
    # ------------------------------------------------------------------
    "Merger",
    "Merger.Merger",
    "Merger.merger_window",
    "Merger.merger_service",
    "Merger.components",
    "Merger.components.file_list",
    "Merger.components.sheet_selector",
    "Merger.components.column_mapper",
    "Merger.components.preview_dialog",

    # ------------------------------------------------------------------
    # DailyMerger
    # ------------------------------------------------------------------
    "DailyMerger",
    "DailyMerger.daily_merger_window",
    "DailyMerger.daily_merger_service",
    "DailyMerger.run_daily_merger",
    "DailyMerger.components",
    "DailyMerger.components.daily_calendar",
    "DailyMerger.components.daily_file_list",
    "DailyMerger.components.daily_summary",

    # ------------------------------------------------------------------
    # MonthlyMerger
    # ------------------------------------------------------------------
    "MonthlyMerger",
    "MonthlyMerger.monthly_merger_window",
    "MonthlyMerger.run_monthly_merger",

    # ------------------------------------------------------------------
    # Assigner
    # ------------------------------------------------------------------
    "Assigner",
    "Assigner.main_window_assigner",
    "Assigner.assigner_processor",

    # ------------------------------------------------------------------
    # Reach Rate Calculator
    # ------------------------------------------------------------------
    "Reach Rate Calculator",
    "Reach Rate Calculator.ReachRateCalculator",
    "Reach Rate Calculator.ReachRateCalculatorUI",
    "Reach Rate Calculator.ReachRateCalculatorUI_v2",
    "Reach Rate Calculator.chart_generator",

    # ------------------------------------------------------------------
    # File processing
    # ------------------------------------------------------------------
    "file_processing",
    "file_processing.processor",
    "file_processing.final_processor",

    # ------------------------------------------------------------------
    # Config subsystem
    # ------------------------------------------------------------------
    "config",
    "config.manager",
    "config.schema",
    "config.validator",
    "config.migrator",
    "config.backup",
    "config.security",

    # ------------------------------------------------------------------
    # Utils
    # ------------------------------------------------------------------
    "utils",
    "utils.config",
    "utils.helpers",
    "utils.crash_handler",
    "utils.error_handler",
    "utils.error_logger",
    "utils.timezone_map",
    "utils.runtime",
    "utils.tool_launcher",
    "utils.tool_registry",
    "utils.recent_tools",
    "utils.recent_archiver_files",
    "utils.recent_merger_files",
    "utils.recent_daily_merger_files",
    "utils.merge_templates",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

a = Analysis(
    [os.path.join(src_v2_path, "main.py")],
    pathex=[src_v2_path],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test frameworks
        "pytest",
        "unittest",
        "_pytest",
        # Unused Qt back-ends
        "PyQt6",
        "PyQt5.QtSvg",
        "PyQt5.QtPrintSupport",
        "PyQt5.QtSql",
        "PyQt5.QtNetwork",
        "PyQt5.QtWebKit",
        # Unused scientific stack
        "numpy.testing",
        "PIL.ImageQt",
        "scipy",
        "sklearn",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ---------------------------------------------------------------------------
# PYZ
# ---------------------------------------------------------------------------

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ---------------------------------------------------------------------------
# EXE  (one-folder mode: binaries kept separate for faster cold-start)
# ---------------------------------------------------------------------------

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ART Q Master v2",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,                    # windowed GUI — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

# ---------------------------------------------------------------------------
# COLLECT  (one-folder bundle)
# ---------------------------------------------------------------------------

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=["vcruntime140.dll", "pythonw.exe"],
    name="ART Q Master v2",
)
