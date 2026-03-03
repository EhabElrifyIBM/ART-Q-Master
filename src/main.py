import os
import sys
import runpy
import encodings  # Fix for fatal bootloader issue
import multiprocessing
from PyQt5.QtWidgets import QApplication, QMessageBox
import importlib.util

def _pyinstaller_meta_imports():
    """
    Exhaustive imports for PyInstaller static analysis.
    This function is never called but ensures all dependencies are bundled.
    """
    import pandas
    import openpyxl
    import openpyxl.utils
    import openpyxl.reader.excel
    import selenium
    import selenium.webdriver
    import selenium.webdriver.chrome.service
    import selenium.webdriver.chrome.options
    import selenium.webdriver.common.by
    import selenium.webdriver.common.keys
    import selenium.webdriver.common.action_chains
    import selenium.webdriver.support.ui
    import selenium.webdriver.support.expected_conditions
    import webdriver_manager
    import webdriver_manager.chrome
    import PIL
    import PIL.Image
    import PIL.ImageTk
    import tkinter
    import tkinter.filedialog
    import tkinter.messagebox
    import tkinter.ttk
    import tkinter.scrolledtext
    import json
    import threading
    import subprocess
    import platform
    import time
    import datetime
    import traceback
    import ctypes
    import pyautogui
    import collections
    import pathlib
    import shutil
    import copy
    import re
    import xlsxwriter
    import PyQt5.QtCore
    import PyQt5.QtGui
    import PyQt5.QtWidgets

# Add the project root directory to Python path
if getattr(sys, 'frozen', False):
    # Running as a frozen executable (PyInstaller)
    project_root = sys._MEIPASS
else:
    # Running from source
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

if project_root not in sys.path:
    sys.path.append(project_root)

def run_merger():
    try:
        # Use runpy for robust execution
        merger_path = os.path.join(project_root, 'src', 'Merger', 'Merger.py')
        if os.path.exists(merger_path):
            runpy.run_path(merger_path, run_name="__main__")
        else:
            # Fallback for source run if structure differs
            from src.Merger.Merger import main
            main()
    except Exception as e:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"Failed to launch Merger: {e}")

def run_archiver():
    try:
        archiver_path = os.path.join(project_root, 'src', 'Archiver', 'Archiver.py')
        if os.path.exists(archiver_path):
            runpy.run_path(archiver_path, run_name="__main__")
        else:
            from src.Archiver.Archiver import main
            main()
    except Exception as e:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"Failed to launch Archiver: {e}")

def run_q_control():
    # Handle path with spaces 'ART Q Control'
    q_control_dir = os.path.join(project_root, 'src', 'ART Q Control')
    if q_control_dir not in sys.path:
        sys.path.insert(0, q_control_dir)

    # Also ensure src is in path
    src_dir = os.path.join(project_root, 'src')
    if src_dir not in sys.path:
        sys.path.append(src_dir)

    try:
        # ── v2 Dispatcher (IBM Carbon UI) — preferred entry point ──────────────
        dispatcher_v2 = os.path.join(q_control_dir, 'Dispatcher_v2.py')
        dispatcher_v1 = os.path.join(q_control_dir, 'Dispatcher.py')
        main_script   = os.path.join(q_control_dir, 'Main.py')

        if os.path.exists(dispatcher_v2):
            runpy.run_path(dispatcher_v2, run_name="__main__")
        elif os.path.exists(dispatcher_v1):
            # Fallback: legacy Dispatcher
            runpy.run_path(dispatcher_v1, run_name="__main__")
        elif os.path.exists(main_script):
            # Last resort: monolithic Main.py
            runpy.run_path(main_script, run_name="__main__")
        else:
            raise FileNotFoundError("No ART Q Control entry point found.")
    except Exception as e:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"Failed to launch ART Q Control: {e}")

def run_reach_rate_calculator():
    reach_rate_dir = os.path.join(project_root, 'src', 'Reach Rate Calculator')
    if reach_rate_dir not in sys.path:
        sys.path.insert(0, reach_rate_dir)
    try:
        ui_script = os.path.join(reach_rate_dir, 'ReachRateCalculatorUI.py')
        if os.path.exists(ui_script):
            runpy.run_path(ui_script, run_name="__main__")
        else:
            from ReachRateCalculatorUI import main
            main()
    except Exception as e:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"Failed to launch Reach Rate Calculator: {e}")

def run_main_menu():
    try:
        from src.ui.main_menu import MainMenu
        app = QApplication.instance() or QApplication(sys.argv)
        window = MainMenu()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Error", f"Failed to launch Main Menu: {e}")

def main():
    # Recommended for frozen executables
    multiprocessing.freeze_support()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == 'merger':
            run_merger()
        elif cmd == 'archiver':
            run_archiver()
        elif cmd == 'qcontrol':
            run_q_control()
        elif cmd == 'reachrate':
            run_reach_rate_calculator()
        else:
            run_main_menu()
    else:
        run_main_menu()

if __name__ == "__main__":
    main()
