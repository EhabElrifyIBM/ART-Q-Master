"""
Progress Monitor Component for AutoSender Phase 4.1 - V2 MODERNIZED
====================================================================

Advanced progress monitoring with control buttons and modern shell styling:
- Pause: Pause process on current element/step
- Resume: Resume after pause
- Stop: Stop process after current case and end gracefully
- Abort: Kill process immediately and end application
- Central Logging: Errors and success confirmations
- THREADING: Long operations run in separate thread, UI stays responsive
- SIGNALS: Qt signals for thread-safe communication
- V2 SHELL STYLING: Modern card-based design matching main menu/Dispatcher

Author: ART Q Master Development
Version: 3.0 (V2 Shell Modernization)
Phase: 6.11 - Progress Monitor Modernization
"""

import time
from datetime import datetime
from enum import Enum
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QColor, QResizeEvent
from typing import Optional, Callable

# V2 Design System Imports
from ui.services import get_v2_settings_bus, V2ThemeService
from ui.typography_mixin import V2TypographyMixin
from ui.design_system import Spacing, BorderRadius


import sys
import os


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


class ProgressMonitor(QDialog, V2TypographyMixin):
    """
    Advanced progress monitoring dialog with control buttons and V2 shell styling.
    Provides real-time progress updates, logging, and process control.
    
    THREADING: This dialog can work with worker threads using signals for thread-safe updates.
    Use signals for all UI updates from worker threads.
    
    V2 FEATURES:
    - Shell palette integration (window_bg, surface, borders)
    - Typography system for consistent fonts
    - Theme-aware styling (light/dark/auto)
    - Reactive updates via settings bus
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
        V2TypographyMixin.__init__(self)
        
        self.setWindowTitle("ART Q Master - AutoSender")
        self.setMinimumWidth(700)
        self.resize(860, 820)
        self.setModal(True)

        # Initialize V2 systems
        self.theme_service = V2ThemeService()
        
        # Subscribe to theme changes
        self.settings_bus.theme_changed.connect(self._apply_theme)
        self.settings_bus.font_preset_changed.connect(self.apply_typography)

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
        self._apply_theme()
        self.apply_typography()

    def _init_ui(self):
        """V2 Shell-styled progress monitor layout."""
        colors = self.theme_service.colors_for(self.settings_bus.theme)

        main = QVBoxLayout()
        main.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        main.setSpacing(Spacing.MD)

        # ── HEADER CARD ───────────────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        header_layout.setSpacing(Spacing.SM)
        
        title = QLabel("AutoSender  ·  Progress Monitor")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)

        self.status_label = QLabel("Status: Initializing…")
        self.status_label.setObjectName("statusLabel")
        header_layout.addWidget(self.status_label)
        
        main.addWidget(header_frame)
        main.addSpacing(Spacing.MD)

        # ── PROGRESS CARD ─────────────────────────────────────────────────────
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        progress_layout.setSpacing(Spacing.MD)
        
        self.case_info_label = QLabel("Waiting for first case…")
        self.case_info_label.setObjectName("caseInfoLabel")
        progress_layout.addWidget(self.case_info_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%  (%v / %m)")
        self.progress_bar.setMinimumHeight(32)
        progress_layout.addWidget(self.progress_bar)
        
        main.addWidget(progress_frame)
        main.addSpacing(Spacing.MD)

        # ── STAT CARDS ROW ────────────────────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(Spacing.MD)

        def _stat_card(label, color_key):
            frame = QFrame()
            frame.setObjectName("statCard")
            col = QVBoxLayout(frame)
            col.setContentsMargins(Spacing.LG, Spacing.MD, Spacing.LG, Spacing.MD)
            col.setSpacing(Spacing.XS)
            
            lbl = QLabel(label.upper())
            lbl.setObjectName("statLabel")
            lbl.setStyleSheet(f"color: {colors['text_secondary']}; letter-spacing: 1px;")
            
            val = QLabel("0")
            val.setObjectName("statValue")
            val.setProperty("colorKey", color_key)  # Store for theme updates
            
            col.addWidget(lbl)
            col.addWidget(val)
            return frame, val

        card_completed, self._val_completed = _stat_card("Completed", "accent")
        card_skipped,   self._val_skipped   = _stat_card("Skipped",   "warning")
        card_failed,    self._val_failed     = _stat_card("Failed",    "danger")
        card_avg_time,  self._val_avg_time   = _stat_card("AVG Time",  "text_secondary")
        
        # Store color keys for theme updates
        self._val_completed.setProperty("colorKey", "accent")
        self._val_skipped.setProperty("colorKey", "warning")
        self._val_failed.setProperty("colorKey", "danger")
        self._val_avg_time.setProperty("colorKey", "text_secondary")

        stats_row.addWidget(card_completed)
        stats_row.addWidget(card_skipped)
        stats_row.addWidget(card_failed)
        stats_row.addWidget(card_avg_time)
        main.addLayout(stats_row)
        main.addSpacing(Spacing.MD)

        # ── CONTROL BUTTONS ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(Spacing.MD)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("pauseButton")
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        btn_row.addWidget(self.pause_btn)

        self.resume_btn = QPushButton("Resume")
        self.resume_btn.setObjectName("resumeButton")
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self._on_resume_clicked)
        btn_row.addWidget(self.resume_btn)

        self.stop_btn = QPushButton("Stop (Graceful)")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        btn_row.addWidget(self.stop_btn)

        self.abort_btn = QPushButton("Abort")
        self.abort_btn.setObjectName("abortButton")
        self.abort_btn.clicked.connect(self._on_abort_clicked)
        btn_row.addWidget(self.abort_btn)

        btn_row.addStretch()

        self.finish_btn = QPushButton("Close")
        self.finish_btn.setObjectName("finishButton")
        self.finish_btn.setEnabled(False)
        self.finish_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.finish_btn)

        main.addLayout(btn_row)
        main.addSpacing(Spacing.MD)

        # ── LOG SECTION ───────────────────────────────────────────────────────
        log_frame = QFrame()
        log_frame.setObjectName("logFrame")
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(Spacing.XL, Spacing.LG, Spacing.XL, Spacing.LG)
        log_layout.setSpacing(Spacing.MD)
        
        log_header = QLabel("ACTIVITY LOG")
        log_header.setObjectName("logHeader")
        log_layout.addWidget(log_header)

        self.log_text = QTextEdit()
        self.log_text.setObjectName("logText")
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(280)
        log_layout.addWidget(self.log_text)
        
        main.addWidget(log_frame)

        self.setLayout(main)

    def _apply_theme(self):
        """Apply V2 shell theme styling to all components."""
        colors = self.theme_service.colors_for(self.settings_bus.theme)
        
        # Generate complete stylesheet
        stylesheet = f"""
            QDialog {{
                background-color: {colors['window_bg']};
                color: {colors['text_primary']};
                font-family: 'IBM Plex Sans', Arial, sans-serif;
            }}
            
            QLabel {{
                color: {colors['text_primary']};
                background: transparent;
            }}
            
            QFrame#headerFrame, QFrame#progressFrame, QFrame#logFrame {{
                background: {colors['surface']};
                border: 1px solid {colors['surface_border']};
                border-radius: {BorderRadius.LG}px;
            }}
            
            QLabel#titleLabel {{
                font-size: {self.get_size('h2')}px;
                font-weight: 700;
                color: {colors['accent']};
                letter-spacing: 0.5px;
            }}
            
            QLabel#statusLabel {{
                font-size: {self.get_size('body')}px;
                color: {colors['text_secondary']};
            }}
            
            QLabel#caseInfoLabel {{
                font-size: {self.get_size('h3')}px;
                font-weight: 600;
                color: {colors['text_primary']};
            }}
            
            QProgressBar {{
                border: none;
                border-radius: {BorderRadius.MD}px;
                background: {colors['surface_alt']};
                color: #ffffff;
                text-align: center;
                font-weight: 700;
                font-size: {self.get_size('body_sm')}px;
            }}
            
            QProgressBar::chunk {{
                background: {colors['accent']};
                border-radius: {BorderRadius.MD}px;
            }}
            
            QFrame#statCard {{
                background: {colors['surface']};
                border: 1px solid {colors['surface_border']};
                border-radius: {BorderRadius.LG}px;
            }}
            
            QLabel#statLabel {{
                font-size: {self.get_size('caption')}px;
                font-weight: 600;
                color: {colors['text_secondary']};
                letter-spacing: 1px;
            }}
            
            QLabel#statValue {{
                font-size: {self.get_size('h2')}px;
                font-weight: 700;
            }}
            
            QPushButton#pauseButton {{
                background: transparent;
                color: {colors['accent']};
                border: 2px solid {colors['accent']};
                border-radius: {BorderRadius.MD}px;
                font-size: {self.get_size('body')}px;
                font-weight: 700;
                padding: {Spacing.MD}px {Spacing.LG}px;
                min-height: {int(self.get_size('body') * 2.5)}px;
                min-width: {int(self.get_size('body') * 5.5)}px;
            }}
            
            QPushButton#pauseButton:hover {{
                background: {colors['accent']};
                color: #ffffff;
            }}
            
            QPushButton#pauseButton:disabled {{
                border-color: {colors['surface_border']};
                color: {colors['text_secondary']};
                opacity: 0.5;
            }}
            
            QPushButton#resumeButton, QPushButton#finishButton {{
                background: {colors['accent']};
                color: #ffffff;
                border: none;
                border-radius: {BorderRadius.MD}px;
                font-size: {self.get_size('body')}px;
                font-weight: 700;
                padding: {Spacing.MD}px {Spacing.LG}px;
                min-height: {int(self.get_size('body') * 2.5)}px;
                min-width: {int(self.get_size('body') * 5.5)}px;
            }}
            
            QPushButton#resumeButton:hover, QPushButton#finishButton:hover {{
                background: {colors['accent_hover']};
            }}
            
            QPushButton#resumeButton:disabled, QPushButton#finishButton:disabled {{
                background: {colors['surface_border']};
                color: {colors['text_secondary']};
                opacity: 0.5;
            }}
            
            QPushButton#stopButton {{
                background: transparent;
                color: {colors['text_secondary']};
                border: 2px solid {colors['surface_border']};
                border-radius: {BorderRadius.MD}px;
                font-size: {self.get_size('body')}px;
                font-weight: 700;
                padding: {Spacing.MD}px {Spacing.LG}px;
                min-height: {int(self.get_size('body') * 2.5)}px;
                min-width: {int(self.get_size('body') * 7.5)}px;
            }}
            
            QPushButton#stopButton:hover {{
                background: {colors['surface_alt']};
                color: {colors['text_primary']};
                border-color: {colors['text_secondary']};
            }}
            
            QPushButton#stopButton:disabled {{
                border-color: {colors['surface_border']};
                color: {colors['text_secondary']};
                opacity: 0.5;
            }}
            
            QPushButton#abortButton {{
                background: {colors.get('danger', '#da1e28')};
                color: #ffffff;
                border: none;
                border-radius: {BorderRadius.MD}px;
                font-size: {self.get_size('body')}px;
                font-weight: 700;
                padding: {Spacing.MD}px {Spacing.LG}px;
                min-height: {int(self.get_size('body') * 2.5)}px;
                min-width: {int(self.get_size('body') * 5.5)}px;
            }}
            
            QPushButton#abortButton:hover {{
                background: #b81922;
            }}
            
            QPushButton#abortButton:disabled {{
                background: {colors['surface_border']};
                color: {colors['text_secondary']};
                opacity: 0.5;
            }}
            
            QLabel#logHeader {{
                font-size: {self.get_size('h4')}px;
                font-weight: 600;
                color: {colors['text_secondary']};
                letter-spacing: 1.2px;
                text-transform: uppercase;
            }}
            
            QTextEdit#logText {{
                background: {colors['surface_alt']};
                border: 1px solid {colors['surface_border']};
                border-radius: {BorderRadius.MD}px;
                font-family: 'IBM Plex Mono', 'Courier New', monospace;
                font-size: {self.get_size('h3')}px;
                color: {colors['text_primary']};
                padding: {Spacing.LG}px;
                line-height: 1.8;
            }}
        """
        
        self.setStyleSheet(stylesheet)
        
        # Update stat value colors dynamically
        stat_colors = {
            'accent': colors['accent'],
            'warning': colors.get('warning', '#f1c21b'),
            'danger': colors.get('danger', '#da1e28'),
            'text_secondary': colors['text_secondary']
        }
        
        for val_widget in [self._val_completed, self._val_skipped, self._val_failed, self._val_avg_time]:
            color_key = val_widget.property("colorKey")
            if color_key and color_key in stat_colors:
                val_widget.setStyleSheet(f"color: {stat_colors[color_key]}; font-weight: 700;")
    
    def apply_typography(self):
        """Apply V2 typography system to all text elements."""
        # This is called automatically when font preset changes
        # Regenerate stylesheet to pick up new font sizes
        self._apply_theme()

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
        Add message to central log with V2 theme colors.
        
        Args:
            message: Message to log
            level: Log level (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = self.theme_service.colors_for(self.settings_bus.theme)

        # V2 theme color tokens per level
        _colors = {
            "INFO":    colors['accent'],           # Accent blue
            "SUCCESS": colors.get('success', '#198038'),  # Success green
            "WARNING": colors.get('warning', '#f1c21b'),  # Warning yellow
            "ERROR":   colors.get('danger', '#da1e28'),   # Danger red
            "ETICKET": "#6929c4",                  # Purple (kept for consistency)
            "STEP":    "#005d5d",                  # Teal (kept for consistency)
            "DEBUG":   colors['text_secondary'],   # Muted text
        }
        color  = _colors.get(level, colors['text_primary'])
        bold   = level in ("WARNING", "ERROR", "ETICKET")
        weight = "font-weight:700;" if bold else ""
        sym    = {"INFO": "›", "SUCCESS": "✓", "WARNING": "⚠",
                  "ERROR": "✗", "ETICKET": "⚡", "STEP": "→"}.get(level, "·")

        log_entry = (
            f'<span style="color:{colors["text_secondary"]};">{timestamp}</span>'
            f'&nbsp;<span style="color:{color};{weight}">{sym}&nbsp;{message}</span>'
        )
        self.log_text.append(log_entry)

        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        if scrollbar is not None:
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
        Update status label with V2 theme colors.
        
        Args:
            status_text: Status text to display
            is_error: If True, display in red (error status)
        """
        colors = self.theme_service.colors_for(self.settings_bus.theme)
        danger_color = colors.get('danger', '#da1e28')
        sec_color = colors['text_secondary']
        
        color = danger_color if is_error else sec_color
        self.status_label.setText(f"Status: {status_text}")
        self.status_label.setStyleSheet(
            f"color: {color}; background: transparent; font-size: {self.get_size('body')}px;"
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
