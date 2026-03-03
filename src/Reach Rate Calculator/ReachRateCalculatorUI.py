"""
Reach Rate Calculator - UI
==========================
IBM Carbon Design PyQt5 window for the Reach Rate Calculator tool.
Runs the calculation engine in a background QThread.
"""

import os
import sys
import subprocess
import threading
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QGroupBox,
    QCheckBox, QDateEdit, QFrame, QSizePolicy, QMessageBox,
    QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QObject
from PyQt5.QtGui import QFont, QIcon


# ── IBM Carbon Tokens ──────────────────────────────────────────────────────────
IBM = {
    "bg":           "#f4f4f4",
    "layer_01":     "#ffffff",
    "layer_02":     "#f4f4f4",
    "text_primary":  "#161616",
    "text_secondary":"#525252",
    "interactive":   "#0f62fe",
    "interactive_hover": "#0353e9",
    "danger":        "#da1e28",
    "danger_hover":  "#b81922",
    "success":       "#198038",
    "warning":       "#f1c21b",
    "border_subtle": "#e0e0e0",
    "disabled_bg":   "#c6c6c6",
    "text_disabled": "#a8a8a8",
    "purple":        "#6929c4",
    "teal":          "#005d5d",
}
FF = "'IBM Plex Sans','Segoe UI',Arial,sans-serif"


# ── Worker Thread ──────────────────────────────────────────────────────────────

class WorkerSignals(QObject):
    log   = pyqtSignal(str, str)   # message, level
    done  = pyqtSignal(str)        # output_path
    error = pyqtSignal(str)        # error message


class CalculatorWorker(QThread):
    def __init__(self, pa_path, sms_path, email_path, phone_path,
                 output_path, start_date=None, end_date=None):
        super().__init__()
        self.pa_path    = pa_path
        self.sms_path   = sms_path
        self.email_path = email_path
        self.phone_path = phone_path
        self.output_path = output_path
        self.start_date  = start_date
        self.end_date    = end_date
        self.signals     = WorkerSignals()

    def run(self):
        try:
            # Import engine (same directory)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from ReachRateCalculator import ReachRateCalculator

            def log_fn(msg, level="INFO"):
                self.signals.log.emit(msg, level)

            calc = ReachRateCalculator(log_fn=log_fn)
            calc.load_files(
                pa_path   = self.pa_path,
                sms_path  = self.sms_path,
                email_path= self.email_path,
                phone_path= self.phone_path,
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


# ── Shared Styles ──────────────────────────────────────────────────────────────

def _btn_primary():
    return f"""
        QPushButton {{
            background-color: {IBM['interactive']};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 10px 24px;
            font-family: {FF};
            font-size: 13px;
            font-weight: 700;
            min-height: 40px;
        }}
        QPushButton:hover {{ background-color: {IBM['interactive_hover']}; }}
        QPushButton:disabled {{ background-color: {IBM['disabled_bg']}; color: {IBM['text_disabled']}; }}
    """

def _btn_ghost():
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {IBM['interactive']};
            border: 2px solid {IBM['interactive']};
            border-radius: 4px;
            padding: 10px 24px;
            font-family: {FF};
            font-size: 13px;
            font-weight: 700;
            min-height: 40px;
        }}
        QPushButton:hover {{ background-color: {IBM['interactive']}; color: #ffffff; }}
        QPushButton:disabled {{ border-color: {IBM['disabled_bg']}; color: {IBM['text_disabled']}; }}
    """

def _btn_success():
    return f"""
        QPushButton {{
            background-color: {IBM['success']};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 10px 24px;
            font-family: {FF};
            font-size: 13px;
            font-weight: 700;
            min-height: 40px;
        }}
        QPushButton:hover {{ background-color: #0e6027; }}
    """


# ── File Row Widget ────────────────────────────────────────────────────────────

class FileRow(QWidget):
    """A labelled file-picker row: [Label] [Path display] [Browse]"""

    def __init__(self, label: str, placeholder: str = "No file selected", parent=None):
        super().__init__(parent)
        self._path = ""

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        lbl = QLabel(label)
        lbl.setFixedWidth(230)
        lbl.setStyleSheet(f"font-family: {FF}; font-size: 13px; font-weight: 600; color: {IBM['text_primary']};")
        row.addWidget(lbl)

        self._path_lbl = QLabel(placeholder)
        self._path_lbl.setStyleSheet(
            f"font-family: {FF}; font-size: 12px; color: {IBM['text_secondary']};"
            f"background: {IBM['layer_01']}; border: 1px solid {IBM['border_subtle']};"
            "border-radius: 4px; padding: 6px 10px;"
        )
        self._path_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._path_lbl.setMinimumHeight(36)
        row.addWidget(self._path_lbl)

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(100)
        browse_btn.setStyleSheet(_btn_ghost())
        browse_btn.clicked.connect(self._browse)
        row.addWidget(browse_btn)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Excel File", "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        if path:
            self._path = path
            self._path_lbl.setText(os.path.basename(path))
            self._path_lbl.setStyleSheet(
                f"font-family: {FF}; font-size: 12px; color: {IBM['text_primary']};"
                f"background: {IBM['layer_01']}; border: 1px solid {IBM['interactive']};"
                "border-radius: 4px; padding: 6px 10px;"
            )

    def get_path(self) -> str:
        return self._path

    def is_set(self) -> bool:
        return bool(self._path)


# ── Main Window ────────────────────────────────────────────────────────────────

class ReachRateCalculatorWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Reach Rate Calculator — ART Q Master")
        self.setMinimumSize(860, 780)
        self.resize(920, 850)

        # Icon
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            root = os.path.dirname(os.path.dirname(current_dir))
            icon_path = os.path.join(root, "assets", "ibm_logo.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self._worker: CalculatorWorker = None
        self._output_path = ""

        self._build_ui()
        self._apply_stylesheet()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(32, 24, 32, 20)
        main.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────────────
        header = QLabel("Reach Rate Calculator")
        header.setStyleSheet(
            f"font-family: {FF}; font-size: 22px; font-weight: 700;"
            f"color: {IBM['interactive']};"
        )
        main.addWidget(header)

        subtitle = QLabel(
            "Upload the 4 required sheets, optionally select a time frame, then click Process."
        )
        subtitle.setStyleSheet(
            f"font-family: {FF}; font-size: 13px; color: {IBM['text_secondary']};"
        )
        main.addWidget(subtitle)

        self._add_divider(main)

        # ── File Upload Section ────────────────────────────────────────────────
        upload_box = QGroupBox("Input Files")
        upload_box.setStyleSheet(self._group_box_style())
        upload_layout = QVBoxLayout(upload_box)
        upload_layout.setSpacing(12)
        upload_layout.setContentsMargins(16, 20, 16, 16)

        self._row_pa    = FileRow("PA Cases (Active Cases Workbook)")
        self._row_sms   = FileRow("SMS View")
        self._row_email = FileRow("Email View")
        self._row_phone = FileRow("Phone Call View")

        for row in (self._row_pa, self._row_sms, self._row_email, self._row_phone):
            upload_layout.addWidget(row)

        main.addWidget(upload_box)

        # ── Time Frame Section ─────────────────────────────────────────────────
        time_box = QGroupBox("Time Frame (Optional)")
        time_box.setStyleSheet(self._group_box_style())
        time_layout = QVBoxLayout(time_box)
        time_layout.setContentsMargins(16, 20, 16, 16)
        time_layout.setSpacing(10)

        self._use_dates = QCheckBox("Filter by date range")
        self._use_dates.setStyleSheet(
            f"font-family: {FF}; font-size: 13px; color: {IBM['text_primary']};"
        )
        self._use_dates.stateChanged.connect(self._toggle_date_range)
        time_layout.addWidget(self._use_dates)

        date_row = QWidget()
        date_hl  = QHBoxLayout(date_row)
        date_hl.setContentsMargins(0, 0, 0, 0)
        date_hl.setSpacing(16)

        lbl_from = QLabel("From:")
        lbl_from.setStyleSheet(f"font-family: {FF}; font-size: 13px; color: {IBM['text_primary']};")
        date_hl.addWidget(lbl_from)

        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDate(QDate.currentDate().addMonths(-1))
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        self._date_from.setStyleSheet(self._date_edit_style())
        self._date_from.setFixedWidth(160)
        self._date_from.setEnabled(False)
        date_hl.addWidget(self._date_from)

        lbl_to = QLabel("To:")
        lbl_to.setStyleSheet(f"font-family: {FF}; font-size: 13px; color: {IBM['text_primary']};")
        date_hl.addWidget(lbl_to)

        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDate(QDate.currentDate())
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        self._date_to.setStyleSheet(self._date_edit_style())
        self._date_to.setFixedWidth(160)
        self._date_to.setEnabled(False)
        date_hl.addWidget(self._date_to)

        date_hl.addStretch()
        time_layout.addWidget(date_row)
        main.addWidget(time_box)

        # ── Action Row ─────────────────────────────────────────────────────────
        act_row = QHBoxLayout()
        act_row.setSpacing(12)

        self._process_btn = QPushButton("⚙  Process")
        self._process_btn.setStyleSheet(_btn_primary())
        self._process_btn.clicked.connect(self._on_process)
        act_row.addWidget(self._process_btn)

        self._open_btn = QPushButton("📂  Open Output")
        self._open_btn.setStyleSheet(_btn_success())
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_output)
        act_row.addWidget(self._open_btn)

        act_row.addStretch()

        self._menu_btn = QPushButton("← Back to Menu")
        self._menu_btn.setStyleSheet(_btn_ghost())
        self._menu_btn.clicked.connect(self._back_to_menu)
        act_row.addWidget(self._menu_btn)

        main.addLayout(act_row)

        # ── Log Section ────────────────────────────────────────────────────────
        log_hdr = QLabel("ACTIVITY LOG")
        log_hdr.setStyleSheet(
            f"font-family: {FF}; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;"
            f"color: {IBM['text_secondary']};"
            f"border-bottom: 2px solid {IBM['border_subtle']}; padding-bottom: 4px;"
        )
        main.addWidget(log_hdr)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {IBM['layer_01']};"
            f"  border: 1px solid {IBM['border_subtle']};"
            f"  border-radius: 4px;"
            f"  font-family: 'IBM Plex Mono','Courier New',monospace;"
            f"  font-size: 12px;"
            f"  color: {IBM['text_primary']};"
            f"  padding: 8px;"
            f"}}"
        )
        self._log_text.setMinimumHeight(220)
        main.addWidget(self._log_text, 1)

        # ── Footer ─────────────────────────────────────────────────────────────
        footer = QLabel(
            '<span style="font-size:12px; color:#525252;">'
            'Developed by: Ehab Elrify | Adam Maged &nbsp;·&nbsp; '
            '<a href="mailto:ehab.elrify@ibm.com" style="color:#0f62fe;">ehab.elrify@ibm.com</a> | '
            '<a href="mailto:abdelrahman.maged@ibm.com" style="color:#0f62fe;">abdelrahman.maged@ibm.com</a>'
            '&nbsp;·&nbsp; Assurance Resolution Team</span>'
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setOpenExternalLinks(True)
        footer.setStyleSheet("padding-top: 6px;")
        main.addWidget(footer)

    # ── Styling Helpers ────────────────────────────────────────────────────────

    def _group_box_style(self):
        return f"""
            QGroupBox {{
                font-family: {FF};
                font-size: 13px;
                font-weight: 700;
                color: {IBM['text_primary']};
                border: 1px solid {IBM['border_subtle']};
                border-radius: 6px;
                margin-top: 14px;
                background: {IBM['layer_01']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 6px;
                color: {IBM['interactive']};
            }}
        """

    def _date_edit_style(self):
        return f"""
            QDateEdit {{
                font-family: {FF}; font-size: 13px;
                border: 1px solid {IBM['border_subtle']};
                border-radius: 4px; padding: 6px 10px;
                background: {IBM['layer_01']};
                color: {IBM['text_primary']};
            }}
            QDateEdit:disabled {{
                background: {IBM['layer_02']};
                color: {IBM['text_disabled']};
            }}
        """

    def _apply_stylesheet(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {IBM['bg']};
                color: {IBM['text_primary']};
                font-family: {FF};
            }}
        """)

    def _add_divider(self, layout: QVBoxLayout):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color: {IBM['border_subtle']};")
        layout.addWidget(line)

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def _toggle_date_range(self, state):
        enabled = (state == Qt.Checked)
        self._date_from.setEnabled(enabled)
        self._date_to.setEnabled(enabled)

    def _on_process(self):
        # Validate inputs
        missing = []
        if not self._row_pa.is_set():    missing.append("PA Cases")
        if not self._row_sms.is_set():   missing.append("SMS View")
        if not self._row_email.is_set(): missing.append("Email View")
        if not self._row_phone.is_set(): missing.append("Phone Call View")

        if missing:
            QMessageBox.warning(self, "Missing Files",
                                f"Please select the following files:\n• " + "\n• ".join(missing))
            return

        # Date range
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

        # Ask for output path
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

        # Launch worker thread
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
        """Return to Main Menu."""
        try:
            if getattr(sys, "frozen", False):
                try:
                    os.startfile(sys.executable)
                except Exception:
                    subprocess.Popen([sys.executable])
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_dir     = os.path.dirname(current_dir)
                main_script = os.path.join(src_dir, "main.py")
                if os.path.exists(main_script):
                    subprocess.Popen([sys.executable, main_script])
                else:
                    QMessageBox.warning(self, "Error", f"main.py not found: {main_script}")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to return to menu: {e}")

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "INFO"):
        from datetime import datetime as _dt
        ts = _dt.now().strftime("%H:%M:%S")

        _colors = {
            "INFO":    IBM["interactive"],
            "SUCCESS": IBM["success"],
            "WARNING": IBM["warning"],
            "ERROR":   IBM["danger"],
            "DEBUG":   "#8d8d8d",
        }
        _syms = {
            "INFO": "›", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗",
        }
        color  = _colors.get(level, IBM["text_primary"])
        sym    = _syms.get(level, "·")
        bold   = level in ("WARNING", "ERROR")
        weight = "font-weight:700;" if bold else ""

        entry = (
            f'<span style="color:#8d8d8d;">{ts}</span>'
            f'&nbsp;<span style="color:{color};{weight}">{sym}&nbsp;{msg}</span>'
        )
        self._log_text.append(entry)
        sb = self._log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
        QApplication.processEvents()


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    win = ReachRateCalculatorWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
