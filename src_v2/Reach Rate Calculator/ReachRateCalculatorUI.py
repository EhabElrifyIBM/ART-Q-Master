"""
Reach Rate Calculator - UI
==========================
IBM Carbon Design PyQt5 window for the Reach Rate Calculator tool.
Runs the calculation engine in a background QThread.
"""

import os
import sys
import subprocess
from datetime import date
from typing import Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_V2_DIR = os.path.dirname(CURRENT_DIR)
if SRC_V2_DIR not in sys.path:
    sys.path.insert(0, SRC_V2_DIR)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QGroupBox,
    QCheckBox, QDateEdit, QFrame, QSizePolicy, QMessageBox,
    QSpacerItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QObject
from PyQt5.QtGui import QFont, QIcon, QFontDatabase, QResizeEvent
from ui.responsive import build_scale_tokens, calculate_responsive_font_size


# ── IBM Carbon Design Tokens ───────────────────────────────────────────────────
IBM = {
    "bg":                "#f4f4f4",
    "layer_01":          "#ffffff",
    "layer_02":          "#e8e8e8",
    "text_primary":      "#161616",
    "text_secondary":    "#525252",
    "interactive":       "#0f62fe",
    "interactive_hover": "#0353e9",
    "danger":            "#da1e28",
    "danger_hover":      "#b81922",
    "success":           "#198038",
    "success_hover":     "#0e6027",
    "warning":           "#f1c21b",
    "border_subtle":     "#c6c6c6",
    "border_strong":     "#8d8d8d",
    "disabled_bg":       "#c6c6c6",
    "text_disabled":     "#8d8d8d",
}
FF = "'IBM Plex Sans','Segoe UI',Arial,sans-serif"
FM = "'IBM Plex Mono','Consolas','Courier New',monospace"

# Base font size defaults — retained for fallbacks, but window styling is driven
# by responsive scale tokens in ReachRateCalculatorWindow.
BASE  = 18
LARGE = 20
TITLE = 24
SMALL = 16


# ── Worker Thread ──────────────────────────────────────────────────────────────

class WorkerSignals(QObject):
    log   = pyqtSignal(str, str)   # message, level
    done  = pyqtSignal(str)        # output_path
    error = pyqtSignal(str)        # error message


class CalculatorWorker(QThread):
    def __init__(self, pa_path, sms_path, email_path, phone_path,
                 output_path, start_date=None, end_date=None):
        super().__init__()
        self.pa_path     = pa_path
        self.sms_path    = sms_path
        self.email_path  = email_path
        self.phone_path  = phone_path
        self.output_path = output_path
        self.start_date  = start_date
        self.end_date    = end_date
        self.signals     = WorkerSignals()

    def run(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from ReachRateCalculator import ReachRateCalculator

            def log_fn(msg, level="INFO"):
                self.signals.log.emit(msg, level)

            calc = ReachRateCalculator(log_fn=log_fn)
            calc.load_files(
                pa_path    = self.pa_path,
                sms_path   = self.sms_path,
                email_path = self.email_path,
                phone_path = self.phone_path,
            )
            calc.run(
                output_path = self.output_path,
                start_date  = self.start_date,
                end_date    = self.end_date,
            )
            self.signals.done.emit(self.output_path)
        except Exception as exc:
            import traceback
            self.signals.error.emit(f"{exc}\n{traceback.format_exc()}")


# ── Shared Button Styles ───────────────────────────────────────────────────────

def _s_primary(scale: Optional[dict] = None):
    scale = scale or build_scale_tokens(BASE)
    return f"""
        QPushButton {{
            background-color: {IBM['interactive']};
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 0 {scale['padding_x']}px;
            font-family: {FF};
            font-size: {scale['button']}px;
            font-weight: 700;
            min-height: {scale['control_height']}px;
            min-width: {scale['button_min_width']}px;
        }}
        QPushButton:hover   {{ background-color: {IBM['interactive_hover']}; }}
        QPushButton:pressed {{ background-color: #002d9c; }}
        QPushButton:disabled {{
            background-color: {IBM['disabled_bg']};
            color: {IBM['text_disabled']};
        }}
    """

def _s_success(scale: Optional[dict] = None):
    scale = scale or build_scale_tokens(BASE)
    return f"""
        QPushButton {{
            background-color: {IBM['success']};
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 0 {scale['padding_x']}px;
            font-family: {FF};
            font-size: {scale['button']}px;
            font-weight: 700;
            min-height: {scale['control_height']}px;
            min-width: {scale['button_min_width'] + 20}px;
        }}
        QPushButton:hover   {{ background-color: {IBM['success_hover']}; }}
        QPushButton:disabled {{
            background-color: {IBM['disabled_bg']};
            color: {IBM['text_disabled']};
        }}
    """

def _s_ghost(scale: Optional[dict] = None):
    scale = scale or build_scale_tokens(BASE)
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {IBM['interactive']};
            border: 2px solid {IBM['interactive']};
            border-radius: 10px;
            padding: 0 {max(18, scale['padding_x'] - 4)}px;
            font-family: {FF};
            font-size: {scale['button']}px;
            font-weight: 700;
            min-height: {scale['control_height']}px;
            min-width: {scale['button_min_width']}px;
        }}
        QPushButton:hover {{
            background-color: {IBM['interactive']};
            color: #ffffff;
        }}
        QPushButton:disabled {{
            border-color: {IBM['disabled_bg']};
            color: {IBM['text_disabled']};
        }}
    """

def _s_browse(scale: Optional[dict] = None):
    """Compact ghost button for file rows."""
    scale = scale or build_scale_tokens(BASE)
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {IBM['interactive']};
            border: 1px solid {IBM['interactive']};
            border-radius: 8px;
            padding: 0 {max(8, scale['padding_x'] - 6)}px;
            font-family: {FF};
            font-size: {max(12, scale['small'])}px;
            font-weight: 600;
            min-height: {max(30, scale['control_height'] - 6)}px;
            min-width: {max(78, scale['button_min_width'] - 24)}px;
        }}
        QPushButton:hover {{
            background-color: {IBM['interactive']};
            color: #ffffff;
        }}
    """


# ── File Row Widget ────────────────────────────────────────────────────────────

class FileRow(QWidget):
    """A labelled file-picker row: [Label] [Path display] [Browse]"""

    def __init__(self, label: str, placeholder: str = "No file selected", parent=None):
        super().__init__(parent)
        self._path = ""
        self._label_text = label
        self._placeholder = placeholder
        self._scale = build_scale_tokens(BASE)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(10)

        # Label — fixed, wide enough for longest label
        self._label = QLabel(label)
        self._label.setMinimumWidth(150)
        self._label.setMaximumWidth(210)
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        row.addWidget(self._label)

        # Path display
        self._path_lbl = QLabel(placeholder)
        self._path_lbl.setStyleSheet(
            f"font-family: {FF}; font-size: {BASE}px; color: {IBM['text_secondary']};"
            f"background: {IBM['layer_01']}; border: 1px solid {IBM['border_subtle']};"
            f"border-radius: 4px; padding: 5px 10px;"
        )
        self._path_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._path_lbl.setMinimumHeight(32)
        self._path_lbl.setWordWrap(True)
        row.addWidget(self._path_lbl)

        # Browse button
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.setStyleSheet(_s_browse())
        self._browse_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self._browse_btn.setMinimumHeight(32)
        self._browse_btn.setMinimumWidth(78)
        self._browse_btn.clicked.connect(self._browse)
        row.addWidget(self._browse_btn)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        if path:
            self._path = path
            self._path_lbl.setText(os.path.basename(path))
            self.apply_scale(self._scale)

    def get_path(self) -> str:
        return self._path

    def is_set(self) -> bool:
        return bool(self._path)

    def apply_scale(self, scale: dict) -> None:
        self._scale = scale
        self._label.setStyleSheet(
            f"font-family: {FF}; font-size: {max(12, scale['label'] - 1)}px; font-weight: 600;"
            f"color: {IBM['text_primary']};"
        )
        path_color = IBM['text_primary'] if self._path else IBM['text_secondary']
        path_border = IBM['interactive'] if self._path else IBM['border_subtle']
        self._path_lbl.setStyleSheet(
            f"font-family: {FF}; font-size: {max(11, scale['small'] - 1)}px; color: {path_color};"
            f"background: {IBM['layer_01']}; border: 1px solid {path_border};"
            f"border-radius: 8px; padding: 4px 8px;"
        )
        self._browse_btn.setStyleSheet(_s_browse(scale))
        self._browse_btn.setMinimumHeight(max(28, scale['control_height'] - 8))
        self._browse_btn.setMinimumWidth(max(74, scale['button_min_width'] - 26))
        self._path_lbl.setMinimumHeight(max(28, scale['control_height'] - 8))


# ── Main Window ────────────────────────────────────────────────────────────────

class ReachRateCalculatorWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ART Q Master V2 - Reach Rate Calculator")
        self.setMinimumSize(900, 640)
        self.resize(1020, 700)

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root = os.path.dirname(os.path.dirname(current_dir))
            icon_path = os.path.join(root, "assets", "ibm_logo.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self._worker = None
        self._output_path = ""

        self._font_size = 18
        self._scale = build_scale_tokens(self._font_size)
        self._apply_global_stylesheet()
        self._build_ui()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self._root_layout = QVBoxLayout(central)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        self._accent = QWidget()
        self._accent.setFixedHeight(4)
        self._accent.setStyleSheet(f"background: {IBM['interactive']};")
        self._root_layout.addWidget(self._accent)

        self._content = QWidget()
        self._main_layout = QVBoxLayout(self._content)
        self._main_layout.setContentsMargins(18, 16, 18, 16)
        self._main_layout.setSpacing(10)

        self._header = QLabel("Reach Rate Calculator")
        self._main_layout.addWidget(self._header)

        self._subtitle = QLabel(
            "Upload the 4 required files, optionally select a time frame, then click Process."
        )
        self._subtitle.setWordWrap(True)
        self._main_layout.addWidget(self._subtitle)

        self._header_divider = self._make_divider()
        self._main_layout.addWidget(self._header_divider)

        self._upload_box = self._make_group("  Input Files")
        upload_layout = QVBoxLayout(self._upload_box)
        upload_layout.setSpacing(6)
        upload_layout.setContentsMargins(12, 12, 12, 10)

        self._row_pa = FileRow("PA Cases")
        self._row_sms = FileRow("SMS View")
        self._row_email = FileRow("Email View")
        self._row_phone = FileRow("Phone Call View")

        self._file_rows = (self._row_pa, self._row_sms, self._row_email, self._row_phone)
        for row in self._file_rows:
            upload_layout.addWidget(row)

        self._main_layout.addWidget(self._upload_box)

        self._time_box = self._make_group("  Time Frame  (Optional)")
        time_layout = QVBoxLayout(self._time_box)
        time_layout.setContentsMargins(12, 12, 12, 10)
        time_layout.setSpacing(8)

        self._use_dates = QCheckBox("Filter by date range")
        self._use_dates.stateChanged.connect(self._toggle_date_range)
        time_layout.addWidget(self._use_dates)

        self._date_row = QWidget()
        self._date_layout = QHBoxLayout(self._date_row)
        self._date_layout.setContentsMargins(0, 0, 0, 0)
        self._date_layout.setSpacing(12)

        self._from_group = self._make_group("From")
        from_layout = QVBoxLayout(self._from_group)
        from_layout.setContentsMargins(10, 12, 10, 8)

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setMinimumWidth(140)
        self._date_from.setEnabled(False)
        from_layout.addWidget(self._date_from)

        self._to_group = self._make_group("To")
        to_layout = QVBoxLayout(self._to_group)
        to_layout.setContentsMargins(10, 12, 10, 8)

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setMinimumWidth(140)
        self._date_to.setEnabled(False)
        to_layout.addWidget(self._date_to)

        self._date_layout.addWidget(self._from_group, 1)
        self._date_layout.addWidget(self._to_group, 1)
        time_layout.addWidget(self._date_row)
        self._main_layout.addWidget(self._time_box)

        self._action_divider = self._make_divider()
        self._main_layout.addWidget(self._action_divider)

        self._act_row = QHBoxLayout()
        self._act_row.setSpacing(10)

        self._process_btn = QPushButton("Process")
        self._process_btn.clicked.connect(self._on_process)
        self._act_row.addWidget(self._process_btn)

        self._open_btn = QPushButton("Open Output")
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_output)
        self._act_row.addWidget(self._open_btn)

        self._act_row.addStretch()

        self._menu_btn = QPushButton("Back to Menu")
        self._menu_btn.clicked.connect(self._back_to_menu)
        self._act_row.addWidget(self._menu_btn)

        self._main_layout.addLayout(self._act_row)

        self._log_hdr = QLabel("ACTIVITY LOG")
        self._main_layout.addWidget(self._log_hdr)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._main_layout.addWidget(self._log_text, 1)

        self._footer = QLabel(
            'Developed by: Ehab Elrify | Adam Maged · '
            '<a href="mailto:ehab.elrify@ibm.com">ehab.elrify@ibm.com</a> | '
            '<a href="mailto:abdelrahman.maged@ibm.com">abdelrahman.maged@ibm.com</a> · '
            'Assurance Resolution Team'
        )
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer.setOpenExternalLinks(True)
        self._footer.setWordWrap(True)
        self._main_layout.addWidget(self._footer)

        self._root_layout.addWidget(self._content, 1)
        self._apply_layout_scale()

    # ── Styling Helpers ────────────────────────────────────────────────────────

    def _make_group(self, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        gb.setStyleSheet(f"""
            QGroupBox {{
                font-family: {FF};
                font-size: {self._scale['section']}px;
                font-weight: 600;
                color: {IBM['interactive']};
                border: 1.5px solid #c6d6f5;
                border-radius: 10px;
                margin-top: 14px;
                background: {IBM['layer_01']};
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                top: -2px;
                padding: 2px 10px 2px 10px;
                background: {IBM['layer_01']};
                color: {IBM['interactive']};
                border-radius: 6px;
            }}
        """)
        return gb

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background: {IBM['border_subtle']}; border: none;")
        return line

    def _date_edit_style(self) -> str:
        return f"""
            QDateEdit {{
                font-family: {FF};
                font-size: {self._scale['base']}px;
                color: {IBM['text_primary']};
                background: {IBM['layer_01']};
                border: 1px solid #c6d6f5;
                border-radius: 8px;
                padding: 6px 10px;
                min-height: {max(34, self._scale['control_height'])}px;
            }}
            QDateEdit:focus {{
                border-color: {IBM['interactive']};
            }}
            QDateEdit:disabled {{
                background: {IBM['layer_02']};
                color: {IBM['text_disabled']};
                border-color: {IBM['disabled_bg']};
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid {IBM['border_subtle']};
            }}
        """

    def _apply_global_stylesheet(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: #eef4ff;
                color: {IBM['text_primary']};
                font-family: {FF};
                font-size: {self._scale['base']}px;
            }}
            QScrollBar:vertical {{
                background: #dbeafe;
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: #93c5fd;
                border-radius: 5px;
                min-height: 36px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {IBM['interactive']};
            }}
        """)

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def _toggle_date_range(self, state):
        enabled = bool(state)
        self._date_from.setEnabled(enabled)
        self._date_to.setEnabled(enabled)

    def _on_process(self):
        missing = []
        if not self._row_pa.is_set():    missing.append("PA Cases")
        if not self._row_sms.is_set():   missing.append("SMS View")
        if not self._row_email.is_set(): missing.append("Email View")
        if not self._row_phone.is_set(): missing.append("Phone Call View")

        if missing:
            QMessageBox.warning(self, "Missing Files",
                                "Please select the following files:\n• " + "\n• ".join(missing))
            return

        start_date = None
        end_date   = None
        if self._use_dates.isChecked():
            qd_from = self._date_from.date()
            qd_to   = self._date_to.date()
            start_date = date(qd_from.year(), qd_from.month(), qd_from.day())
            end_date   = date(qd_to.year(),   qd_to.month(),   qd_to.day())
            if start_date > end_date:
                QMessageBox.warning(self, "Invalid Date Range",
                                    "Start date must be before or equal to end date.")
                return

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

        self._worker = CalculatorWorker(
            pa_path    = self._row_pa.get_path(),
            sms_path   = self._row_sms.get_path(),
            email_path = self._row_email.get_path(),
            phone_path = self._row_phone.get_path(),
            output_path= out_path,
            start_date = start_date,
            end_date   = end_date,
        )
        self._worker.signals.log.connect(self._log)
        self._worker.signals.done.connect(self._on_done)
        self._worker.signals.error.connect(self._on_error)
        self._worker.start()

    def _on_done(self, output_path: str):
        self._log("✓ Process completed successfully!", "SUCCESS")
        self._log(f"Output file: {output_path}", "INFO")
        self._process_btn.setEnabled(True)
        self._open_btn.setEnabled(True)
        QMessageBox.information(self, "Done",
                                f"Reach Rate report generated successfully!\n\n{output_path}")

    def _on_error(self, err_msg: str):
        self._log(f"✗ Error: {err_msg}", "ERROR")
        self._process_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Processing failed:\n\n{err_msg}")

    def _open_output(self):
        if self._output_path and os.path.exists(self._output_path):
            try:
                os.startfile(self._output_path)
            except Exception as e:
                QMessageBox.warning(self, "Cannot Open", str(e))
        else:
            QMessageBox.warning(self, "File Not Found", "Output file not found.")

    def _back_to_menu(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            src_v2_dir = os.path.dirname(current_dir)
            main_script = os.path.join(src_v2_dir, "main.py")
            if os.path.exists(main_script):
                subprocess.Popen([sys.executable, main_script], cwd=src_v2_dir)
                self.close()
            else:
                QMessageBox.warning(self, "Error", f"v2 main.py not found: {main_script}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to return to menu: {e}")

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "INFO"):
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H:%M:%S")

        _colors = {
            "INFO":    IBM["interactive"],
            "SUCCESS": IBM["success"],
            "WARNING": "#b45309",   # amber, readable on white
            "ERROR":   IBM["danger"],
        }
        _syms = {
            "INFO": "›", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗",
        }
        color  = _colors.get(level, IBM["text_primary"])
        sym    = _syms.get(level, "·")
        bold   = "font-weight:700;" if level in ("WARNING", "ERROR", "SUCCESS") else ""

        entry = (
            f'<span style="color:#8d8d8d;font-size:{self._scale["label"]}px;">[{ts}]</span>'
            f'&nbsp;<span style="color:{color};{bold}font-size:{self._scale["base"]}px;">'
            f'{sym}&nbsp;{msg}</span>'
        )
        self._log_text.append(entry)
        sb = self._log_text.verticalScrollBar()
        if sb is not None:
            sb.setValue(sb.maximum())
        QApplication.processEvents()


# ── Entry Point ────────────────────────────────────────────────────────────────

    def _apply_layout_scale(self) -> None:
        self._apply_global_stylesheet()
        margins = max(14, min(24, self._scale['padding_x']))
        spacing = max(8, min(14, self._scale.get('spacing', 10)))
        self._main_layout.setContentsMargins(margins, max(12, margins - 2), margins, max(12, margins - 2))
        self._main_layout.setSpacing(spacing)

        self._header.setStyleSheet(
            f"font-family: {FF}; font-size: {self._scale['title']}px; font-weight: 700;"
            f"color: {IBM['interactive']}; margin-bottom: 2px;"
        )
        self._subtitle.setStyleSheet(
            f"font-family: {FF}; font-size: {self._scale['label']}px; color: {IBM['text_secondary']};"
        )
        self._use_dates.setStyleSheet(
            f"QCheckBox {{ font-family: {FF}; font-size: {self._scale['label']}px;"
            f"color: {IBM['text_primary']}; spacing: 8px; }}"
            f"QCheckBox::indicator {{ width: 18px; height: 18px; }}"
            f"QCheckBox::indicator:unchecked {{"
            f"  border: 2px solid {IBM['border_strong']};"
            f"  border-radius: 2px; background: {IBM['layer_01']}; }}"
            f"QCheckBox::indicator:checked {{"
            f"  border: 2px solid {IBM['interactive']};"
            f"  border-radius: 2px; background: {IBM['interactive']}; }}"
        )

        for row in getattr(self, "_file_rows", ()):
            row.apply_scale(self._scale)

        self._date_layout.setSpacing(max(10, spacing))
        self._date_from.setStyleSheet(self._date_edit_style())
        self._date_to.setStyleSheet(self._date_edit_style())
        self._date_from.setMinimumHeight(max(34, self._scale["control_height"] - 4))
        self._date_to.setMinimumHeight(max(34, self._scale["control_height"] - 4))

        button_height = max(36, self._scale["control_height"] - 4)
        self._process_btn.setStyleSheet(_s_primary(self._scale))
        self._process_btn.setMinimumHeight(button_height)
        self._process_btn.setMinimumWidth(max(124, self._scale["button_min_width"]))
        self._process_btn.setFont(QFont("IBM Plex Sans", self._scale["button"], QFont.Bold))

        self._open_btn.setStyleSheet(_s_success(self._scale))
        self._open_btn.setMinimumHeight(button_height)
        self._open_btn.setMinimumWidth(max(138, self._scale["button_min_width"] + 8))
        self._open_btn.setFont(QFont("IBM Plex Sans", self._scale["button"], QFont.Bold))

        self._menu_btn.setStyleSheet(_s_ghost(self._scale))
        self._menu_btn.setMinimumHeight(button_height)
        self._menu_btn.setMinimumWidth(max(144, self._scale["button_min_width"] + 12))
        self._menu_btn.setFont(QFont("IBM Plex Sans", self._scale["button"], QFont.Bold))

        self._log_hdr.setStyleSheet(
            f"font-family: {FF}; font-size: {self._scale['label']}px; font-weight: 700;"
            f"letter-spacing: 1px; color: {IBM['text_secondary']};"
            f"border-bottom: 1px solid {IBM['border_subtle']}; padding-bottom: 4px;"
        )
        self._log_text.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {IBM['layer_01']};"
            f"  border: 1px solid {IBM['border_subtle']};"
            f"  border-radius: 6px;"
            f"  font-family: {FM};"
            f"  font-size: {self._scale['small']}px;"
            f"  color: {IBM['text_primary']};"
            f"  padding: 8px;"
            f"}}"
        )
        self._log_text.setMinimumHeight(max(170, 140 + (self._scale['base'] - 18) * 14))

        self._footer.setStyleSheet(
            f"padding-top: 6px; font-size: {self._scale['small']}px; color: {IBM['text_secondary']};"
        )

    def resizeEvent(self, a0: Optional[QResizeEvent]) -> None:
        width = max(900, self.width())
        height = max(640, self.height())
        width_growth = min(4, max(0, (width - 1020) // 150))
        height_growth = min(3, max(0, (height - 700) // 140))
        new_font_size = min(22, max(18, 18 + max(width_growth, height_growth)))
        if new_font_size != self._font_size:
            self._font_size = new_font_size
            self._scale = build_scale_tokens(self._font_size)
            self._apply_layout_scale()
        super().resizeEvent(a0)


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    app = QApplication.instance() or QApplication(sys.argv)
    win = ReachRateCalculatorWindow()
    win.show()

    if QApplication.instance() is app:
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
