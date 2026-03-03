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


import sys
import os

# ---------------------------------------------------------------------------
# IBM theme import (best-effort — works when run from ART Q Control dir)
# ---------------------------------------------------------------------------
def _get_qss_safe():
    try:
        _art_q_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ART Q Control')
        if _art_q_dir not in sys.path:
            sys.path.insert(0, _art_q_dir)
        from ibm_theme import get_qss, _read_font_size
        return get_qss('light', _read_font_size())
    except Exception:
        return ""  # Fallback: no custom theme


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
    progress_updated = pyqtSignal(int, str, int, int, int, int)  # current, case_num, completed, skipped, failed, total
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
        self.setWindowTitle("ART Q Master - AutoSender")
        self.setMinimumWidth(700)
        self.resize(860, 820)
        self.setModal(True)

        # Apply IBM Carbon QSS (best-effort, falls back to empty string)
        _qss = _get_qss_safe()
        if _qss:
            self.setStyleSheet(_qss)
        else:
            # Minimal fallback stylesheet
            self.setStyleSheet("""
                QDialog { background-color: #f4f4f4; font-family: 'Segoe UI', Arial; font-size: 13pt; }
                QLabel { color: #161616; }
                QPushButton { background-color: #0f62fe; color: #fff;
                    border: none; border-radius: 4px;
                    padding: 10px 20px; font-weight: 600; min-height: 40px; }
                QPushButton:hover { background-color: #0353e9; }
                QProgressBar { border: none; border-radius: 4px;
                    background: #e0e0e0; height: 8px; }
                QProgressBar::chunk { background: #0f62fe; border-radius: 4px; }
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
        """IBM Carbon Design progress monitor layout."""
        # Pull IBM tokens if available
        try:
            from ibm_theme import IBM, _read_font_size
            _c = IBM.LIGHT
            _fs = _read_font_size()
        except Exception:
            _c = {
                'bg': '#f4f4f4', 'layer_01': '#ffffff', 'layer_02': '#f4f4f4',
                'layer_03': '#e8e8e8', 'text_primary': '#161616',
                'text_secondary': '#525252', 'text_on_color': '#ffffff',
                'interactive': '#0f62fe', 'interactive_hover': '#0353e9',
                'interactive_active': '#002d9c', 'danger': '#da1e28',
                'danger_hover': '#b81922', 'success': '#198038',
                'border_subtle': '#e0e0e0', 'progress_track': '#e0e0e0',
                'progress_fill': '#0f62fe', 'disabled_bg': '#c6c6c6',
                'text_disabled': '#a8a8a8',
            }
            _fs = 13

        ff = "'IBM Plex Sans','Segoe UI',Arial,sans-serif"

        main = QVBoxLayout()
        main.setContentsMargins(24, 20, 24, 16)
        main.setSpacing(0)

        # ── HEADER ────────────────────────────────────────────────────────────
        title = QLabel("AutoSender  ·  Progress Monitor")
        title.setFont(QFont('IBM Plex Sans', _fs + 4, QFont.Bold))
        title.setStyleSheet(
            f"font-weight: 800; color: {_c['interactive']};"
            f" background: transparent; letter-spacing: 0.5px;"
        )
        main.addWidget(title)

        self.status_label = QLabel("Status: Initializing…")
        self.status_label.setFont(QFont('IBM Plex Sans', _fs - 1))
        self.status_label.setStyleSheet(
            f"color: {_c['text_secondary']}; background: transparent;"
        )
        main.addWidget(self.status_label)
        main.addSpacing(16)

        # ── CURRENT CASE INFO ─────────────────────────────────────────────────
        self.case_info_label = QLabel("Waiting for first case…")
        self.case_info_label.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self.case_info_label.setStyleSheet(
            f"font-weight: 700; color: {_c['text_primary']}; background: transparent;"
        )
        main.addWidget(self.case_info_label)
        main.addSpacing(8)

        # ── PROGRESS BAR ──────────────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%  (%v / %m)")
        self.progress_bar.setFont(QFont('IBM Plex Sans', _fs - 2, QFont.Bold))
        self.progress_bar.setMinimumHeight(28)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ border: none; border-radius: 8px;"
            f" background: {_c['progress_track']};"
            f" color: #ffffff; text-align: center;"
            f" font-weight: 700; }}"
            f"QProgressBar::chunk {{ background: {_c['interactive']};"
            f" border-radius: 8px; }}"
        )
        main.addWidget(self.progress_bar)
        main.addSpacing(12)

        # ── STAT CARDS ROW ────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        def _stat_card(label, color):
            frame = QFrame()
            frame.setStyleSheet(
                f"QFrame {{ background: {_c['layer_01']};"
                f" border-left: 4px solid {color};"
                f" border-top: 1px solid {_c['border_subtle']};"
                f" border-right: 1px solid {_c['border_subtle']};"
                f" border-bottom: 1px solid {_c['border_subtle']}; }}"
            )
            col = QVBoxLayout(frame)
            col.setContentsMargins(12, 8, 12, 8)
            col.setSpacing(2)
            lbl = QLabel(label.upper())
            lbl.setFont(QFont('IBM Plex Sans', _fs - 5, QFont.Bold))
            lbl.setStyleSheet(
                f"color: {_c['text_secondary']}; letter-spacing: 1px;"
                f" background: transparent; border: none;"
            )
            val = QLabel("0")
            val.setFont(QFont('IBM Plex Sans', _fs + 4, QFont.Bold))
            val.setStyleSheet(
                f"font-weight: 800; color: {color};"
                f" background: transparent; border: none;"
            )
            col.addWidget(lbl)
            col.addWidget(val)
            return frame, val

        card_completed, self._val_completed = _stat_card("Completed", _c['interactive'])
        card_skipped,   self._val_skipped   = _stat_card("Skipped",   _c.get('warning', '#f1c21b'))
        card_failed,    self._val_failed     = _stat_card("Failed",    _c['danger'])
        card_avg_time,  self._val_avg_time   = _stat_card("AVG Time",   _c['text_secondary'])

        stats_row.addWidget(card_completed)
        stats_row.addWidget(card_skipped)
        stats_row.addWidget(card_failed)
        stats_row.addWidget(card_avg_time)
        main.addLayout(stats_row)
        main.addSpacing(16)

        # ── CONTROL BUTTONS ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        _btn_base = (
            f"QPushButton {{ font-family: {ff}; font-size: {_fs}pt;"
            f" font-weight: 700; border: none; border-radius: 4px;"
            f" padding: 10px 20px; min-height: 44px; }}"
        )

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self.pause_btn.setMinimumHeight(44)
        self.pause_btn.setMinimumWidth(110)
        self.pause_btn.setStyleSheet(
            _btn_base +
            f"QPushButton {{ background-color: transparent;"
            f" color: {_c['interactive']};"
            f" border: 2px solid {_c['interactive']};"
            f" border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: {_c['interactive']};"
            f" color: #ffffff; }}"
            f"QPushButton:disabled {{ border-color: {_c['disabled_bg']};"
            f" color: {_c['text_disabled']}; }}"
        )
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        btn_row.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self.resume_btn.setMinimumHeight(44)
        self.resume_btn.setMinimumWidth(110)
        self.resume_btn.setEnabled(False)
        self.resume_btn.setStyleSheet(
            _btn_base +
            f"QPushButton {{ background-color: {_c['interactive']};"
            f" color: #ffffff; border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: {_c['interactive_hover']}; }}"
            f"QPushButton:disabled {{ background-color: {_c['disabled_bg']};"
            f" color: {_c['text_disabled']}; }}"
        )
        self.resume_btn.clicked.connect(self._on_resume_clicked)
        btn_row.addWidget(self.resume_btn)

        self.stop_btn = QPushButton("Stop (Graceful)")
        self.stop_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setMinimumWidth(150)
        self.stop_btn.setStyleSheet(
            _btn_base +
            f"QPushButton {{ background-color: transparent;"
            f" color: {_c['text_secondary']};"
            f" border: 2px solid {_c['border_subtle']};"
            f" border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: {_c['layer_02']};"
            f" color: {_c['text_primary']};"
            f" border-color: {_c['text_secondary']}; }}"
            f"QPushButton:disabled {{ border-color: {_c['disabled_bg']};"
            f" color: {_c['text_disabled']}; }}"
        )
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        btn_row.addWidget(self.stop_btn)

        self.abort_btn = QPushButton("Abort")
        self.abort_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self.abort_btn.setMinimumHeight(44)
        self.abort_btn.setMinimumWidth(110)
        self.abort_btn.setStyleSheet(
            _btn_base +
            f"QPushButton {{ background-color: {_c['danger']};"
            f" color: #ffffff; border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: {_c['danger_hover']}; }}"
            f"QPushButton:disabled {{ background-color: {_c['disabled_bg']};"
            f" color: {_c['text_disabled']}; }}"
        )
        self.abort_btn.clicked.connect(self._on_abort_clicked)
        btn_row.addWidget(self.abort_btn)

        btn_row.addStretch()

        self.finish_btn = QPushButton("Close")
        self.finish_btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self.finish_btn.setMinimumHeight(44)
        self.finish_btn.setMinimumWidth(110)
        self.finish_btn.setEnabled(False)
        self.finish_btn.setStyleSheet(
            _btn_base +
            f"QPushButton {{ background-color: {_c['interactive']};"
            f" color: #ffffff; border-radius: 8px; }}"
            f"QPushButton:hover {{ background-color: {_c['interactive_hover']}; }}"
            f"QPushButton:disabled {{ background-color: {_c['disabled_bg']};"
            f" color: {_c['text_disabled']}; }}"
        )
        self.finish_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.finish_btn)

        main.addLayout(btn_row)
        main.addSpacing(14)

        # ── LOG SECTION ───────────────────────────────────────────────────────
        log_header = QLabel("ACTIVITY LOG")
        log_header.setFont(QFont('IBM Plex Sans', _fs - 4, QFont.Bold))
        log_header.setStyleSheet(
            f"color: {_c['text_secondary']}; letter-spacing: 1.2px;"
            f" font-weight: 700; background: transparent;"
            f" border-bottom: 2px solid {_c['border_subtle']};"
            f" padding-bottom: 4px;"
        )
        main.addWidget(log_header)
        main.addSpacing(6)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(260)
        self.log_text.setFont(QFont('IBM Plex Mono', _fs - 2))
        self.log_text.setStyleSheet(
            f"QTextEdit {{ background-color: {_c['layer_01']};"
            f" border: 1px solid {_c['border_subtle']};"
            f" border-radius: 4px;"
            f" font-family: 'IBM Plex Mono','Courier New',monospace;"
            f" font-size: {_fs - 2}pt;"
            f" color: {_c['text_primary']};"
            f" padding: 6px; }}"
        )
        main.addWidget(self.log_text)

        self.setLayout(main)

    # ── helper: update stat card values ──────────────────────────────────────
    def _refresh_stat_cards(self):
        """Keep stat cards in sync after update_progress calls."""
        try:
            self._val_completed.setText(str(self.cases_completed))
            self._val_skipped.setText(str(self.cases_skipped))
            self._val_failed.setText(str(self.cases_failed))
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if self.cases_completed > 0:
                avg = elapsed / self.cases_completed
                m, s = int(avg // 60), int(avg % 60)
                self._val_avg_time.setText(f"{m:02}:{s:02}")
            else:
                self._val_avg_time.setText("--:--")
        except Exception:
            pass
    
    # ========== SIGNAL HANDLER METHODS (for thread-safe updates) ==========
    
    def _on_progress_updated(self, current_case_num, case_number, completed, skipped, failed, total):
        """Handle progress update signal from worker thread — relay all 6 args."""
        self.update_progress(current_case_num, case_number, completed, skipped, failed, total)
    
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
        
        # Update case info
        self.case_info_label.setText(
            f"Case {current_case_num} of {total}  ·  {case_number}"
        )

        # Update progress bar
        if total > 0:
            percentage = int((current_case_num / total) * 100)
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current_case_num)
            self.progress_bar.setFormat(f"{current_case_num} / {total}  ({percentage}%)")

        # Refresh stat cards
        self._refresh_stat_cards()

        QApplication.processEvents()
    
    def log_message(self, message, level="INFO"):
        """
        Add message to central log.
        
        Args:
            message: Message to log
            level: Log level (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # IBM Carbon color tokens per level
        _colors = {
            "INFO":    "#0f62fe",   # IBM Blue
            "SUCCESS": "#198038",   # IBM Green
            "WARNING": "#f1c21b",   # IBM Yellow
            "ERROR":   "#da1e28",   # IBM Red
            "ETICKET": "#6929c4",   # IBM Purple
            "STEP":    "#005d5d",   # IBM Teal
            "DEBUG":   "#8d8d8d",   # IBM Grey — muted
        }
        color  = _colors.get(level, "#161616")
        bold   = level in ("WARNING", "ERROR", "ETICKET")
        weight = "font-weight:700;" if bold else ""
        sym    = {"INFO": "›", "SUCCESS": "✓", "WARNING": "⚠",
                  "ERROR": "✗", "ETICKET": "⚡", "STEP": "→"}.get(level, "·")

        log_entry = (
            f'<span style="color:#8d8d8d;">{timestamp}</span>'
            f'&nbsp;<span style="color:{color};{weight}">{sym}&nbsp;{message}</span>'
        )
        self.log_text.append(log_entry)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
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
        try:
            from ibm_theme import IBM
            _c = IBM.LIGHT
            danger_color = _c['danger']
            sec_color    = _c['text_secondary']
        except Exception:
            danger_color = '#da1e28'
            sec_color    = '#525252'
        color = danger_color if is_error else sec_color
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(
            f"color: {color}; background: transparent;"
        )
    
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
            self._pause_flag = True
            self.state = ProcessState.PAUSED
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)
            self.set_status("Paused — waiting to resume", is_error=False)
            self.log_warning("Process paused by user")
            self.pause_requested.emit()
    
    def _on_resume_clicked(self):
        """Handle resume button click"""
        if self._pause_flag:
            self._pause_flag = False
            self.state = ProcessState.RUNNING
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)
            self.set_status("Processing (resumed)")
            self.log_message("Process resumed", "INFO")
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
