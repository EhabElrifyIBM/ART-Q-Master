"""
Progress Monitor Component for AutoSender Phase 4.1 - ENHANCED WITH THREADING
===============================================================================

Advanced progress monitoring with control buttons:
- Pause: Pause process on current element/step
- Resume: Resume after pause
- Stop: Stop process after current case and end gracefully
- Abort: Kill process immediately and end application
- Central Logging: Errors and success confirmations
- THREADING: Long operations run in separate thread, UI stays responsive
- SIGNALS: Qt signals for thread-safe communication

Author: ART Q Master Development
Version: 2.0 (Threading Support)
Phase: 4.1 - Progress Control & Monitoring
"""

import time
from datetime import datetime
from enum import Enum
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QColor
from typing import Optional, Callable


class ProcessState(Enum):
    """State machine for process control"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ABORTED = "aborted"
    COMPLETED = "completed"
    ERROR = "error"


class ProgressSignals(QObject):
    """
    Signals for thread-safe communication between worker and UI thread.
    Prevents "non-responding" window issues.
    """
    # Progress updates
    progress_updated = pyqtSignal(int, str, int, int, int)  # current, case_num, completed, failed, total
    log_message_signal = pyqtSignal(str, str)  # message, level
    status_changed = pyqtSignal(str, bool)  # status_text, is_error
    finished = pyqtSignal(str)  # reason
    
    # Worker control
    pause_signal = pyqtSignal()
    resume_signal = pyqtSignal()
    stop_signal = pyqtSignal()
    abort_signal = pyqtSignal()


class ProgressMonitor(QDialog):
    """
    Advanced progress monitoring dialog with control buttons.
    Provides real-time progress updates, logging, and process control.
    
    THREADING: This dialog can work with worker threads using signals for thread-safe updates.
    Use signals for all UI updates from worker threads.
    """
    
    # Signals for process control
    pause_requested = pyqtSignal()
    resume_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    abort_requested = pyqtSignal()
    
    # Signals that the worker thread can emit (for thread-safe updates)
    progress_signals = ProgressSignals()
    
    def __init__(self, title="Processing Cases", total_cases=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(900, 600)
        self.resize(900, 650)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: #f7f9fa;
                border-radius: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 21px;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 21px;
                font-weight: 600;
                color: #222;
            }
            QPushButton {
                background-color: #1976D2;
                color: #fff;
                font-weight: 600;
                padding: 12px 28px;
                border-radius: 8px;
                font-size: 21px;
                border: none;
                transition: background 0.2s;
            }
            QPushButton:hover {
                background-color: #1565C0;
                color: #fff;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QProgressBar {
                border: 1px solid #b0bec5;
                border-radius: 6px;
                text-align: center;
                height: 14px;
                font-size: 18px;
                background: #eceff1;
            }
            QProgressBar::chunk {
                background-color: #43A047;
                border-radius: 6px;
            }
            QFrame {
                background: #fff;
                border-radius: 10px;
            }
            QCheckBox {
                font-size: 21px;
            }
        """)
        
        # State tracking
        self.state = ProcessState.RUNNING
        self.total_cases = total_cases
        self.current_case_num = 0
        self.cases_completed = 0
        self.cases_skipped = 0  # Track skipped cases
        self.cases_failed = 0
        self.start_time = datetime.now()
        self.paused_time = None
        self.total_pause_duration = 0
        
        # Control flags
        self._pause_flag = False
        self._stop_flag = False
        self._abort_flag = False
        
        # Connect signals (for thread safety)
        self.progress_signals.progress_updated.connect(self._on_progress_updated)
        self.progress_signals.log_message_signal.connect(self._on_log_message)
        self.progress_signals.status_changed.connect(self._on_status_changed)
        self.progress_signals.finished.connect(self.finish_process)
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize UI components with LARGER FONTS"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== TOP SECTION: Title & Status ==========
        top_layout = QVBoxLayout()
        
        self.title_label = QLabel("ART Q Master - AutoSender Progress")
        title_font = QFont()
        title_font.setPointSize(18)  # INCREASED from 16
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #1976D2;")
        top_layout.addWidget(self.title_label)
        
        self.status_label = QLabel("Status: Processing...")
        status_font = QFont()
        status_font.setPointSize(14)  # INCREASED from 12
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet("color: #333333;")
        top_layout.addWidget(self.status_label)
        
        main_layout.addLayout(top_layout)
        
        # ========== PROGRESS SECTION ==========
        progress_layout = QVBoxLayout()
        
        # Current case info
        self.case_info_label = QLabel()
        case_font = QFont()
        case_font.setPointSize(14)  # INCREASED from 13
        case_font.setBold(True)
        self.case_info_label.setFont(case_font)
        progress_layout.addWidget(self.case_info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(True)
        progress_bar_font = QFont()
        progress_bar_font.setPointSize(13)  # INCREASED from 11
        progress_bar_font.setBold(True)
        self.progress_bar.setFont(progress_bar_font)
        self.progress_bar.setMinimumHeight(14)
        self.progress_bar.setStyleSheet("")
        progress_layout.addWidget(self.progress_bar)
        
        # Statistics (now below progress bar)
        self.stats_label = QLabel()
        stats_font = QFont()
        stats_font.setPointSize(13)
        self.stats_label.setFont(stats_font)
        self.stats_label.setStyleSheet("color: #666666;")
        progress_layout.addWidget(self.stats_label)
        
        main_layout.addLayout(progress_layout)
        
        # ========== CONTROL BUTTONS SECTION ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.pause_btn = QPushButton("⏸ Pause")
        button_font = QFont()
        button_font.setPointSize(12)  # INCREASED from 10
        button_font.setBold(True)
        self.pause_btn.setFont(button_font)
        self.pause_btn.setMinimumHeight(45)  # INCREASED height
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFA726;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        buttons_layout.addWidget(self.pause_btn)
        
        self.resume_btn = QPushButton("▶ Resume")
        self.resume_btn.setFont(button_font)
        self.resume_btn.setMinimumHeight(45)
        self.resume_btn.clicked.connect(self._on_resume_clicked)
        self.resume_btn.setEnabled(False)
        self.resume_btn.setStyleSheet("""
            QPushButton {
                background-color: #66BB6A;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #999999;
            }
        """)
        buttons_layout.addWidget(self.resume_btn)
        
        self.stop_btn = QPushButton("⏹ Stop (Graceful)")
        self.stop_btn.setFont(button_font)
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FDD835;
                color: #333333;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #F9A825;
            }
        """)
        buttons_layout.addWidget(self.stop_btn)
        
        self.abort_btn = QPushButton("🛑 Abort")
        self.abort_btn.setFont(button_font)
        self.abort_btn.setMinimumHeight(45)
        self.abort_btn.clicked.connect(self._on_abort_clicked)
        self.abort_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF5350;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        buttons_layout.addWidget(self.abort_btn)
        
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
        
        # ========== LOGGING SECTION ==========
        logging_label = QLabel("📋 Central Log:")
        logging_font = QFont()
        logging_font.setPointSize(13)  # INCREASED from 12
        logging_font.setBold(True)
        logging_label.setFont(logging_font)
        main_layout.addWidget(logging_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(250)
        log_font = QFont("Courier New", 11)  # INCREASED from 10
        self.log_text.setFont(log_font)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
            }
        """)
        main_layout.addWidget(self.log_text)
        
        # ========== FINISH BUTTON ==========
        self.finish_btn = QPushButton("✓ Close")
        finish_font = QFont()
        finish_font.setPointSize(13)  # INCREASED from 12
        finish_font.setBold(True)
        self.finish_btn.setFont(finish_font)
        self.finish_btn.setMinimumHeight(45)  # INCREASED height
        self.finish_btn.clicked.connect(self.accept)
        self.finish_btn.setEnabled(False)
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #CCCCCC;
            }
        """)
        main_layout.addWidget(self.finish_btn)
        
        self.setLayout(main_layout)
    
    # ========== SIGNAL HANDLER METHODS (for thread-safe updates) ==========
    
    def _on_progress_updated(self, current_case_num, case_number, completed, failed, total):
        """Handle progress update signal from worker thread"""
        self.update_progress(current_case_num, case_number, completed, failed, total)
    
    def _on_log_message(self, message, level):
        """Handle log message signal from worker thread"""
        self.log_message(message, level)
    
    def _on_status_changed(self, status_text, is_error):
        """Handle status change signal from worker thread"""
        self.set_status(status_text, is_error)
    
    def update_progress(self, current_case_num, case_number, completed, skipped, failed, total):
        """
        Update progress display.
        
        Args:
            current_case_num: Current position (1-indexed)
            case_number: Case ID being processed
            skipped: Number of skipped cases
            failed: Number of failed cases
            total: Total cases to process
        """
        self.current_case_num = current_case_num
        self.cases_completed = completed
        self.cases_skipped = skipped
        self.cases_failed = failed
        self.total_cases = total
        
        # Update case info (current case)
        self.case_info_label.setText(f"Processing Case {current_case_num}/{total}: {case_number}")
        
        # Update progress bar
        if total > 0:
            percentage = int((current_case_num / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{current_case_num}/{total} ({percentage}%)")
        
        # Calculate average case time
        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_time = elapsed / max(1, (completed + skipped + failed))
        avg_min = int(avg_time // 60)
        avg_sec = int(avg_time % 60)
        avg_str = f"{avg_min:02}:{avg_sec:02}"
        
        # Update statistics (below bar)
        self.stats_label.setText(
            f"✓ Completed: {completed} | ⏭ Skipped: {skipped} | ❌ Failed: {failed} | Avg Case Time: {avg_str}"
        )
        
        QApplication.processEvents()
    
    def log_message(self, message, level="INFO"):
        """
        Add message to central log.
        
        Args:
            message: Message to log
            level: Log level (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        level_colors = {
            "INFO": "#0066CC",
            "SUCCESS": "#00AA00",
            "WARNING": "#FF8800",
            "ERROR": "#CC0000",
            "ETICKET": "#8E24AA"
        }
        
        color = level_colors.get(level, "#000000")
        # Special formatting for eticket
        if level == "ETICKET":
            log_entry = f'<span style="color: {color}; font-weight:bold;">[{timestamp}] [ETICKET] {message}</span>'
        elif level == "WARNING":
            log_entry = f'<span style="color: {color}; font-weight:bold;">[{timestamp}] [WARNING] {message}</span>'
        elif level == "ERROR":
            log_entry = f'<span style="color: {color}; font-weight:bold; text-decoration:underline;">[{timestamp}] [ERROR] {message}</span>'
        else:
            log_entry = f'<span style="color: {color};">[{timestamp}] [{level}] {message}</span>'
        self.log_text.append(log_entry)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Process pending events FREQUENTLY to keep UI responsive
        QApplication.processEvents()
    
    def log_success(self, message):
        self.log_message(message, "SUCCESS")
    def log_warning(self, message):
        self.log_message(message, "WARNING")
    def log_error(self, message):
        self.log_message(message, "ERROR")
    def log_eticket(self, message):
        self.log_message(message, "ETICKET")
    
    def set_status(self, status_text, is_error=False):
        """
        Update status label.
        
        Args:
            status_text: Status text to display
            is_error: If True, display in red (error status)
        """
        color = "#CC0000" if is_error else "#333333"
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"font-size: 12px; color: {color};")
    
    # ========== CONTROL METHODS ==========
    
    def is_pause_requested(self) -> bool:
        """Check if pause was requested"""
        return self._pause_flag
    
    def is_stop_requested(self) -> bool:
        """Check if stop was requested"""
        return self._stop_flag
    
    def is_abort_requested(self) -> bool:
        """Check if abort was requested"""
        return self._abort_flag
    
    def wait_if_paused(self, timeout=0.1):
        """
        Called during processing to check for pause/stop/abort.
        Blocks while paused.
        
        Args:
            timeout: Check interval in seconds
        """
        while self._pause_flag:
            time.sleep(timeout)
            # Allow abort even while paused
            if self._abort_flag:
                break
    
    def _on_pause_clicked(self):
        """Handle pause button click"""
        if not self._pause_flag:
            print("[DEBUG] Pause button clicked - emitting pause_requested signal")
            self._pause_flag = True
            self.state = ProcessState.PAUSED
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.set_status("Status: ⏸ PAUSED - Process paused, waiting to resume...")
            self.log_warning("Process PAUSED by user")
            # EMIT SIGNAL to notify worker thread
            self.pause_requested.emit()
    
    def _on_resume_clicked(self):
        """Handle resume button click"""
        if self._pause_flag:
            print("[DEBUG] Resume button clicked - emitting resume_requested signal")
            self._pause_flag = False
            self.state = ProcessState.RUNNING
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.set_status("Status: Processing... (resumed)")
            self.log_message("Process RESUMED by user")
            # EMIT SIGNAL to notify worker thread
            self.resume_requested.emit()
    
    def _on_stop_clicked(self):
        """Handle stop button click"""
        reply = QMessageBox.question(
            self,
            "Stop Process?",
            "Stop process after current case?\n\nThe tool will complete the current case and then terminate gracefully.",
            QMessageBox.Yes | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            print("[DEBUG] Stop button confirmed - emitting stop_requested signal")
            self._stop_flag = True
            self.state = ProcessState.STOPPED
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.set_status("Status: ⏹ STOPPING - Will stop after current case...")
            self.log_warning("Process STOP requested - will complete current case and terminate")
            # EMIT SIGNAL to notify worker thread
            self.stop_requested.emit()
    
    def _on_abort_clicked(self):
        """Handle abort button click"""
        reply = QMessageBox.warning(
            self,
            "Abort Process?",
            "Abort process immediately?\n\nThis will KILL the process and close the application immediately.\nAny unsaved progress will be lost!",
            QMessageBox.Yes | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            print("[DEBUG] Abort button confirmed - emitting abort_requested signal")
            self._abort_flag = True
            self.state = ProcessState.ABORTED
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.abort_btn.setEnabled(False)
            self.set_status("Status: 🛑 ABORTING - Process will terminate immediately!", is_error=True)
            self.log_error("Process ABORTED by user - terminating immediately!")
            # EMIT SIGNAL to notify worker thread
            self.abort_requested.emit()
            # Close immediately after logging
            time.sleep(0.5)
            self.accept()
    
    def finish_process(self, reason="Completed"):
        """
        Mark process as finished.
        
        Args:
            reason: Reason for finishing (Completed, Stopped, Error, etc.)
        """
        self.state = ProcessState.COMPLETED if reason == "Completed" else ProcessState.ERROR
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.abort_btn.setEnabled(False)
        self.finish_btn.setEnabled(True)
        
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]
        
        if reason == "Completed":
            self.set_status(f"Status: ✓ COMPLETED - All {self.cases_completed} cases processed in {elapsed_str}")
            self.log_success(f"Process completed successfully in {elapsed_str}")
        else:
            self.set_status(f"Status: ⚠ {reason.upper()} - {self.cases_completed} cases completed in {elapsed_str}")
            self.log_warning(f"Process {reason} after {elapsed_str}")
        
        self.progress_bar.setFormat(f"Done: {self.cases_completed}/{self.total_cases}")
    
    def get_statistics(self) -> dict:
        """
        Get final statistics from process.
        
        Returns:
            dict with keys: cases_completed, cases_failed, total_cases, duration
        """
        elapsed = datetime.now() - self.start_time
        return {
            "cases_completed": self.cases_completed,
            "cases_failed": self.cases_failed,
            "total_cases": self.total_cases,
            "duration": str(elapsed).split('.')[0],
            "state": self.state.value,
        }
