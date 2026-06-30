"""
Reach Rate Calculator - Modernized UI (Phase 6.9)
==================================================
IBM Carbon Design PyQt5 window for the Reach Rate Calculator tool.
Runs the calculation engine in a background QThread.

Phase 6.9 Modernization:
- Integrated V2 foundation systems (ThemeManager, TypographyMixin, SettingsBus)
- Modern card-based layout with V2 components
- Enhanced file selection with drag-drop support
- Keyboard shortcuts support
- Modern progress indicators
- Theme-aware styling throughout
- Improved accessibility (WCAG 2.1 AA)

Core functionality:
- Load 4 required Excel files (PA Cases, SMS View, Email View, Phone Call View)
- Optional date range filtering
- Calculate reach rates by channel (SMS, Email, Phone)
- Generate comprehensive Excel report with metrics
"""

import os
import sys
from datetime import date
from typing import Optional

# Path setup
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_V2_DIR = os.path.dirname(CURRENT_DIR)
if SRC_V2_DIR not in sys.path:
    sys.path.insert(0, SRC_V2_DIR)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QGroupBox,
    QCheckBox, QDateEdit, QFrame, QSizePolicy, QMessageBox,
    QSpacerItem, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QObject, QEvent
from PyQt5.QtGui import QFont, QIcon, QDragEnterEvent, QDropEvent

# Import V2 foundation systems (Phase 6.9)
from ui.theme_manager import get_theme_manager
from ui.typography_mixin import V2TypographyMixin
from ui.services import get_v2_settings_bus, V2ThemeService
from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory
from ui.design_system import Colors, Spacing, BorderRadius, Shadows
from ui.components_v2.buttons import PrimaryButton, SecondaryButton, GhostButton
from ui.components_v2.cards import Card, ElevatedCard
from ui.components_v2.inputs import ModernLineEdit
from ui.components_v2.dialogs import ProgressDialog
from utils.recent_tools import get_recent_tools_manager


# ── Worker Thread ──────────────────────────────────────────────────────────────

class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    log = pyqtSignal(str, str)   # message, level
    done = pyqtSignal(str)        # output_path
    error = pyqtSignal(str)       # error message


class CalculatorWorker(QThread):
    """
    Worker thread for running calculations in background.
    Keeps UI responsive during long operations.
    """
    
    def __init__(self, pa_path, sms_path, email_path, phone_path,
                 output_path, start_date=None, end_date=None):
        super().__init__()
        self.pa_path = pa_path
        self.sms_path = sms_path
        self.email_path = email_path
        self.phone_path = phone_path
        self.output_path = output_path
        self.start_date = start_date
        self.end_date = end_date
        self.signals = WorkerSignals()

    def run(self):
        """Execute calculation in background thread."""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from ReachRateCalculator import ReachRateCalculator

            def log_fn(msg, level="INFO"):
                self.signals.log.emit(msg, level)

            calc = ReachRateCalculator(log_fn=log_fn)
            calc.load_files(
                pa_path=self.pa_path,
                sms_path=self.sms_path,
                email_path=self.email_path,
                phone_path=self.phone_path,
            )
            calc.run(
                output_path=self.output_path,
                start_date=self.start_date,
                end_date=self.end_date,
            )
            self.signals.done.emit(self.output_path)
        except Exception as exc:
            import traceback
            self.signals.error.emit(f"{exc}\n{traceback.format_exc()}")


# ── File Selection Card ────────────────────────────────────────────────────────

class FileSelectionCard(Card):
    """
    Modern file selection card with drag-drop support.
    Displays file path and provides browse button.
    """
    
    file_selected = pyqtSignal(str)  # file_path
    
    def __init__(self, label: str, parent=None):
        super().__init__(parent, hoverable=False)
        self._label_text = label
        self._file_path = ""
        
        # Enable drag-drop
        self.setAcceptDrops(True)
        
        self._setup_content()
        self.set_title(label)
        
        # Override card title font to be smaller
        if self._title_label:
            from ui.typography import TypographySystem, FontSizePreset
            typography = TypographySystem(FontSizePreset.NORMAL)
            typography.apply_to_widget(self._title_label, 'body', QFont.DemiBold)
    
    def _setup_content(self):
        """Set up card content."""
        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(Spacing.XS, Spacing.XS, Spacing.XS, Spacing.XS)
        layout.setSpacing(Spacing.XS)
        
        # File path display
        self._path_label = QLabel("No file selected")
        self._path_label.setWordWrap(True)
        from ui.typography import TypographySystem, FontSizePreset
        typography = TypographySystem(FontSizePreset.NORMAL)
        typography.apply_to_widget(self._path_label, 'caption')
        self._path_label.setStyleSheet(f"""
            QLabel {{
                color: #6b7280;
                padding: {Spacing.XS}px;
                background: #f9fafb;
                border: 1px dashed #d1d5db;
                border-radius: {BorderRadius.SM}px;
            }}
        """)
        layout.addWidget(self._path_label, 1)
        
        # Browse button
        self._browse_btn = SecondaryButton("Browse...")
        self._browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(self._browse_btn)
        
        self.set_content(content)
    
    def _browse_file(self):
        """Open file dialog to select Excel file."""
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select {self._label_text}", "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        if path:
            self.set_file_path(path)
    
    def set_file_path(self, path: str):
        """Set the file path and update display."""
        self._file_path = path
        if path:
            self._path_label.setText(os.path.basename(path))
            self._path_label.setStyleSheet(f"""
                QLabel {{
                    color: #0f62fe;
                    padding: {Spacing.XS}px;
                    background: #edf5ff;
                    border: 1px solid #0f62fe;
                    border-radius: {BorderRadius.SM}px;
                    font-weight: 600;
                }}
            """)
            self.file_selected.emit(path)
        else:
            self._path_label.setText("No file selected")
            self._path_label.setStyleSheet(f"""
                QLabel {{
                    color: #6b7280;
                    padding: {Spacing.XS}px;
                    background: #f9fafb;
                    border: 1px dashed #d1d5db;
                    border-radius: {BorderRadius.SM}px;
                }}
            """)
    
    def get_file_path(self) -> str:
        """Get the selected file path."""
        return self._file_path
    
    def is_set(self) -> bool:
        """Check if file is selected."""
        return bool(self._file_path)
    
    def dragEnterEvent(self, a0):
        """Handle drag enter event."""
        if a0.mimeData() and a0.mimeData().hasUrls():
            a0.acceptProposedAction()
    
    def dropEvent(self, a0):
        """Handle drop event."""
        if a0.mimeData():
            urls = a0.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if path.endswith(('.xlsx', '.xls')):
                    self.set_file_path(path)
                    a0.acceptProposedAction()


# ── Main Window ────────────────────────────────────────────────────────────────

class ReachRateCalculatorWindow(QMainWindow, V2TypographyMixin):
    """
    Modernized Reach Rate Calculator main window (Phase 6.9).
    
    Features:
    - V2 foundation systems integration
    - Modern card-based layout
    - Enhanced file selection with drag-drop
    - Keyboard shortcuts
    - Theme-aware styling
    - Improved accessibility
    """

    def __init__(self):
        super().__init__()
        V2TypographyMixin.__init__(self)
        
        self.setWindowTitle("ART Q Master V2 - Reach Rate Calculator")
        self.setMinimumSize(750, 550)
        self.resize(850, 600)
        
        # Set window icon
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root = os.path.dirname(os.path.dirname(current_dir))
            icon_path = os.path.join(root, "assets", "ibm_logo.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        
        # Initialize state
        self._worker = None
        self._output_path = ""
        self._progress_dialog = None
        
        # Get theme manager and settings bus
        self._theme_manager = get_theme_manager()
        self._settings_bus = get_v2_settings_bus()
        self._theme_mode = self._theme_manager.current_theme.value
        
        # Connect to theme changes
        self._settings_bus.theme_changed.connect(self._on_theme_changed)
        
        # Connect to font preset changes (from V2TypographyMixin)
        self._settings_bus.font_preset_changed.connect(self._on_font_preset_changed)
        
        # Build UI
        self._build_ui()
        self._setup_keyboard_shortcuts()
        self._apply_theme()
        
        # Apply initial typography
        self.apply_typography()
        
        # Register with recent tools
        try:
            recent_tools = get_recent_tools_manager()
            recent_tools.add_tool("reachrate")
        except Exception:
            pass

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the main UI."""
        # Central widget with scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.setCentralWidget(scroll)
        
        central = QWidget()
        scroll.setWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)
        main_layout.setSpacing(Spacing.XS)
        
        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(Spacing.XS)
        
        self._title_label = QLabel("Reach Rate Calculator")
        self._title_label.setFont(self.get_font('h3', QFont.Bold))
        header_layout.addWidget(self._title_label)
        
        self._subtitle_label = QLabel(
            "Upload the 4 required files, optionally select a time frame, then click Process."
        )
        self._subtitle_label.setFont(self.get_font('caption'))
        self._subtitle_label.setWordWrap(True)
        header_layout.addWidget(self._subtitle_label)
        
        main_layout.addLayout(header_layout)
        
        # File selection card
        self._files_card = ElevatedCard()
        self._files_card.set_title("📁 Input Files")
        
        files_content = QWidget()
        files_layout = QVBoxLayout(files_content)
        files_layout.setSpacing(Spacing.XS)
        files_layout.setContentsMargins(0, 0, 0, 0)
        
        self._file_pa = FileSelectionCard("PA Cases")
        self._file_sms = FileSelectionCard("SMS View")
        self._file_email = FileSelectionCard("Email View")
        self._file_phone = FileSelectionCard("Phone Call View")
        
        self._file_cards = [self._file_pa, self._file_sms, self._file_email, self._file_phone]
        
        for card in self._file_cards:
            files_layout.addWidget(card)
        
        self._files_card.set_content(files_content)
        main_layout.addWidget(self._files_card)
        
        # Override card title font to be smaller
        if self._files_card._title_label:
            self._files_card._title_label.setFont(self.get_font('body', QFont.DemiBold))
        
        # Time frame card
        self._time_card = Card()
        self._time_card.set_title("📅 Time Frame (Optional)")
        
        # Override card title font to be smaller
        if self._time_card._title_label:
            self._time_card._title_label.setFont(self.get_font('body', QFont.DemiBold))
        
        time_content = QWidget()
        time_layout = QVBoxLayout(time_content)
        time_layout.setSpacing(Spacing.XS)
        time_layout.setContentsMargins(0, 0, 0, 0)
        
        self._use_dates = QCheckBox("Filter by date range")
        self._use_dates.setFont(self.get_font('body_sm'))
        self._use_dates.stateChanged.connect(self._toggle_date_range)
        time_layout.addWidget(self._use_dates)
        
        # Date range row
        date_row = QWidget()
        date_layout = QHBoxLayout(date_row)
        date_layout.setSpacing(Spacing.SM)
        date_layout.setContentsMargins(0, 0, 0, 0)
        
        # From date
        from_container = QWidget()
        from_layout = QVBoxLayout(from_container)
        from_layout.setSpacing(Spacing.XS)
        from_layout.setContentsMargins(0, 0, 0, 0)
        
        self._from_label = QLabel("From")
        self._from_label.setFont(self.get_font('label', QFont.DemiBold))
        from_layout.addWidget(self._from_label)
        
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setMinimumWidth(140)
        self._date_from.setMinimumHeight(32)
        self._date_from.setEnabled(False)
        self._date_from.setFont(self.get_font('body_sm'))
        from_layout.addWidget(self._date_from)
        
        date_layout.addWidget(from_container, 1)
        
        # To date
        to_container = QWidget()
        to_layout = QVBoxLayout(to_container)
        to_layout.setSpacing(Spacing.XS)
        to_layout.setContentsMargins(0, 0, 0, 0)
        
        self._to_label = QLabel("To")
        self._to_label.setFont(self.get_font('label', QFont.DemiBold))
        to_layout.addWidget(self._to_label)
        
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setMinimumWidth(140)
        self._date_to.setMinimumHeight(32)
        self._date_to.setEnabled(False)
        self._date_to.setFont(self.get_font('body_sm'))
        to_layout.addWidget(self._date_to)
        
        date_layout.addWidget(to_container, 1)
        
        time_layout.addWidget(date_row)
        self._time_card.set_content(time_content)
        main_layout.addWidget(self._time_card)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(Spacing.XS)
        
        self._process_btn = PrimaryButton("Process")
        self._process_btn.clicked.connect(self._on_process)
        action_layout.addWidget(self._process_btn)
        
        self._open_btn = SecondaryButton("Open Output")
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_output)
        action_layout.addWidget(self._open_btn)
        
        action_layout.addStretch()
        
        self._menu_btn = GhostButton("Back to Menu")
        self._menu_btn.clicked.connect(self._back_to_menu)
        action_layout.addWidget(self._menu_btn)
        
        main_layout.addLayout(action_layout)
        
        # Activity log card
        log_card = Card()
        log_card.set_title("📋 Activity Log")
        
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setMinimumHeight(150)
        self._log_text.setFont(self.get_font('caption'))
        
        log_card.set_content(self._log_text)
        main_layout.addWidget(log_card, 1)
        
        # Footer
        self._footer = QLabel(
            'Developed by: Ehab Elrify | Adam Maged · '
            '<a href="mailto:ehab.elrify@ibm.com">ehab.elrify@ibm.com</a> | '
            '<a href="mailto:abdelrahman.maged@ibm.com">abdelrahman.maged@ibm.com</a> · '
            'Assurance Resolution Team'
        )
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer.setOpenExternalLinks(True)
        self._footer.setWordWrap(True)
        self._footer.setFont(self.get_font('caption'))
        main_layout.addWidget(self._footer)

    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts."""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence
        
        # Process shortcut (Ctrl+R)
        process_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        process_shortcut.activated.connect(self._on_process)
        
        # Open output shortcut (Ctrl+E)
        open_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        open_shortcut.activated.connect(self._open_output)
        
        # Back to menu shortcut (Ctrl+M)
        menu_shortcut = QShortcut(QKeySequence("Ctrl+M"), self)
        menu_shortcut.activated.connect(self._back_to_menu)

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def _toggle_date_range(self, state):
        """Toggle date range inputs."""
        enabled = bool(state)
        self._date_from.setEnabled(enabled)
        self._date_to.setEnabled(enabled)

    def _on_process(self):
        """Start processing files."""
        # Validate file selection
        missing = []
        if not self._file_pa.is_set():
            missing.append("PA Cases")
        if not self._file_sms.is_set():
            missing.append("SMS View")
        if not self._file_email.is_set():
            missing.append("Email View")
        if not self._file_phone.is_set():
            missing.append("Phone Call View")
        
        if missing:
            QMessageBox.warning(
                self, "Missing Files",
                "Please select the following files:\n• " + "\n• ".join(missing)
            )
            return
        
        # Validate date range if enabled
        start_date = None
        end_date = None
        if self._use_dates.isChecked():
            qd_from = self._date_from.date()
            qd_to = self._date_to.date()
            start_date = date(qd_from.year(), qd_from.month(), qd_from.day())
            end_date = date(qd_to.year(), qd_to.month(), qd_to.day())
            if start_date > end_date:
                QMessageBox.warning(
                    self, "Invalid Date Range",
                    "Start date must be before or equal to end date."
                )
                return
        
        # Get output path
        out_path, _ = QFileDialog.getSaveFileName(
            self, "Save Output As", "Reach_Rate_Report.xlsx",
            "Excel Files (*.xlsx);;All Files (*.*)"
        )
        if not out_path:
            return
        
        self._output_path = out_path
        self._log_text.clear()
        self._process_btn.setEnabled(False)
        self._open_btn.setEnabled(False)
        self._log("Starting Reach Rate Calculator…", "INFO")
        
        # Show progress message
        self._log("Processing files...", "INFO")
        
        # Start worker thread
        self._worker = CalculatorWorker(
            pa_path=self._file_pa.get_file_path(),
            sms_path=self._file_sms.get_file_path(),
            email_path=self._file_email.get_file_path(),
            phone_path=self._file_phone.get_file_path(),
            output_path=out_path,
            start_date=start_date,
            end_date=end_date,
        )
        self._worker.signals.log.connect(self._log)
        self._worker.signals.done.connect(self._on_done)
        self._worker.signals.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, output_path: str):
        """Handle successful completion."""
        self._log("✓ Process completed successfully!", "SUCCESS")
        self._log(f"Output file: {output_path}", "INFO")
        self._process_btn.setEnabled(True)
        self._open_btn.setEnabled(True)
        
        QMessageBox.information(
            self, "Done",
            f"Reach Rate report generated successfully!\n\n{output_path}"
        )

    def _on_error(self, err_msg: str):
        """Handle error."""
        self._log(f"✗ Error: {err_msg}", "ERROR")
        self._process_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Processing failed:\n\n{err_msg}")

    def _open_output(self):
        """Open the output file."""
        if self._output_path and os.path.exists(self._output_path):
            try:
                os.startfile(self._output_path)
            except Exception as e:
                QMessageBox.warning(self, "Cannot Open", str(e))
        else:
            QMessageBox.warning(self, "File Not Found", "Output file not found.")

    def _back_to_menu(self):
        """Return to main menu.

        When running as a frozen .exe the main menu is already open in the same
        process — just close this window.  In development, re-launch main.py in
        a subprocess as before.
        """
        if getattr(sys, "frozen", False):
            # In-process: main menu is the parent window — just close here
            self.close()
            return
        try:
            import subprocess as _sp
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_v2_dir = os.path.dirname(current_dir)
            main_script = os.path.join(src_v2_dir, "main.py")
            if os.path.exists(main_script):
                _sp.Popen([sys.executable, main_script], cwd=src_v2_dir)
                self.close()
            else:
                QMessageBox.warning(self, "Error", f"v2 main.py not found: {main_script}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to return to menu: {e}")

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "INFO"):
        """Add log message to activity log."""
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H:%M:%S")
        
        colors = V2ThemeService.LIGHT if self._theme_mode == "light" else V2ThemeService.DARK
        
        _colors = {
            "INFO": colors["accent"],
            "SUCCESS": colors["success"],
            "WARNING": colors["warning"],
            "ERROR": "#da1e28",
        }
        _syms = {
            "INFO": "›", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗",
        }
        color = _colors.get(level, colors["text_primary"])
        sym = _syms.get(level, "·")
        bold = "font-weight:700;" if level in ("WARNING", "ERROR", "SUCCESS") else ""
        
        entry = (
            f'<span style="color:#8d8d8d;font-size:{self.get_size("caption")}px;">[{ts}]</span>'
            f'&nbsp;<span style="color:{color};{bold}font-size:{self.get_size("body_sm")}px;">'
            f'{sym}&nbsp;{msg}</span>'
        )
        self._log_text.append(entry)
        sb = self._log_text.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())
        QApplication.processEvents()

    # ── Theme Support ──────────────────────────────────────────────────────────

    def _on_theme_changed(self, theme: str):
        """Handle theme change."""
        self._theme_mode = theme
        self._apply_theme()

    def _apply_theme(self):
        """Apply current theme to window."""
        colors = V2ThemeService.LIGHT if self._theme_mode == "light" else V2ThemeService.DARK
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {colors['window_bg']};
            }}
            QScrollArea {{
                background-color: {colors['window_bg']};
                border: none;
            }}
            QLabel {{
                color: {colors['text_primary']};
            }}
            QCheckBox {{
                color: {colors['text_primary']};
                spacing: {Spacing.SM}px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {colors['surface_border']};
                border-radius: {BorderRadius.SM}px;
                background: {colors['surface']};
            }}
            QCheckBox::indicator:checked {{
                background: {colors['accent']};
                border-color: {colors['accent']};
            }}
            QDateEdit {{
                background: {colors['surface']};
                color: {colors['text_primary']};
                border: 2px solid {colors['surface_border']};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px;
            }}
            QDateEdit:focus {{
                border-color: {colors['accent']};
            }}
            QDateEdit:disabled {{
                background: {colors['surface_alt']};
                color: {colors['text_secondary']};
            }}
            QTextEdit {{
                background: {colors['surface']};
                color: {colors['text_primary']};
                border: 1px solid {colors['surface_border']};
                border-radius: {BorderRadius.MD}px;
                padding: {Spacing.SM}px;
            }}
        """)

    def apply_typography(self):
        """Apply typography to all widgets (V2TypographyMixin)."""
        self._title_label.setFont(self.get_font('h3', QFont.Bold))
        self._subtitle_label.setFont(self.get_font('caption'))
        self._use_dates.setFont(self.get_font('body_sm'))
        self._from_label.setFont(self.get_font('caption', QFont.DemiBold))
        self._to_label.setFont(self.get_font('caption', QFont.DemiBold))
        self._date_from.setFont(self.get_font('body_sm'))
        self._date_to.setFont(self.get_font('body_sm'))
        self._log_text.setFont(self.get_font('caption'))
        self._footer.setFont(self.get_font('caption'))
        
        # Update card titles
        if self._files_card._title_label:
            self._files_card._title_label.setFont(self.get_font('body', QFont.DemiBold))
        if self._time_card._title_label:
            self._time_card._title_label.setFont(self.get_font('body', QFont.DemiBold))


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    import os
    from utils.crash_handler import install_crash_handler, enable_qt_sigint_heartbeat
    install_crash_handler()

    # No explicit High-DPI attributes here — every other tool window in this
    # suite (Merger, Archiver, DailyMerger, MonthlyMerger, the main shell)
    # runs without opting into AA_EnableHighDpiScaling, so enabling it only
    # here made this window render visibly larger/"zoomed in" relative to
    # all the others when the OS has a display scale factor configured.

    app = QApplication.instance() or QApplication(sys.argv)
    enable_qt_sigint_heartbeat(app)

    win = ReachRateCalculatorWindow()
    win.show()
    app.exec_()

    # Window closed — exit immediately so worker threads don't keep the
    # process alive in the background / terminal.
    os._exit(0)


if __name__ == "__main__":
    main()

# Made with Bob
