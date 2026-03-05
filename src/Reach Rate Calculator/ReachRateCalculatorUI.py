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
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFileDialog, QGroupBox,
    QCheckBox, QDateEdit, QFrame, QSizePolicy, QMessageBox,
    QSpacerItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QObject
from PyQt5.QtGui import QFont, QIcon, QFontDatabase


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

# Base font size — all sizes derived from this so DPI scaling is consistent
BASE  = 14   # px  (was 12-13, felt tiny on high-DPI)
LARGE = 16
TITLE = 22
SMALL = 12


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

def _s_primary():
    return f"""
        QPushButton {{
            background-color: {IBM['interactive']};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 0 28px;
            font-family: {FF};
            font-size: {BASE}px;
            font-weight: 700;
            min-height: 44px;
            min-width: 120px;
        }}
        QPushButton:hover   {{ background-color: {IBM['interactive_hover']}; }}
        QPushButton:pressed {{ background-color: #002d9c; }}
        QPushButton:disabled {{
            background-color: {IBM['disabled_bg']};
            color: {IBM['text_disabled']};
        }}
    """

def _s_success():
    return f"""
        QPushButton {{
            background-color: {IBM['success']};
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 0 28px;
            font-family: {FF};
            font-size: {BASE}px;
            font-weight: 700;
            min-height: 44px;
            min-width: 140px;
        }}
        QPushButton:hover   {{ background-color: {IBM['success_hover']}; }}
        QPushButton:disabled {{
            background-color: {IBM['disabled_bg']};
            color: {IBM['text_disabled']};
        }}
    """

def _s_ghost():
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {IBM['interactive']};
            border: 2px solid {IBM['interactive']};
            border-radius: 4px;
            padding: 0 22px;
            font-family: {FF};
            font-size: {BASE}px;
            font-weight: 700;
            min-height: 44px;
            min-width: 100px;
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

def _s_browse():
    """Compact ghost button for file rows."""
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {IBM['interactive']};
            border: 2px solid {IBM['interactive']};
            border-radius: 4px;
            padding: 0 16px;
            font-family: {FF};
            font-size: {BASE}px;
            font-weight: 600;
            min-height: 40px;
            min-width: 90px;
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

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 6, 0, 6)  # Moderate vertical padding
        row.setSpacing(12)  # Moderate horizontal spacing

        # Label — fixed, wide enough for longest label
        lbl = QLabel(label)
        lbl.setFixedWidth(320)  # Increased width for full label visibility
        lbl.setWordWrap(False)
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        lbl.setStyleSheet(
            f"font-family: {FF}; font-size: {BASE}px; font-weight: 600;"
            f"color: {IBM['text_primary']};"
        )
        row.addWidget(lbl)

        # Path display
        self._path_lbl = QLabel(placeholder)
        self._path_lbl.setStyleSheet(
            f"font-family: {FF}; font-size: {BASE}px; color: {IBM['text_secondary']};"
            f"background: {IBM['layer_01']}; border: 1px solid {IBM['border_subtle']};"
            f"border-radius: 4px; padding: 6px 12px;"
        )
        self._path_lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._path_lbl.setMinimumHeight(36)
        row.addWidget(self._path_lbl)

        # Browse button
        browse_btn = QPushButton("Browse…")
        browse_btn.setStyleSheet(_s_browse())
        browse_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        browse_btn.setMinimumHeight(36)
        browse_btn.setMinimumWidth(90)
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
                f"font-family: {FF}; font-size: {BASE}px; color: {IBM['text_primary']};"
                f"background: {IBM['layer_01']}; border: 1px solid {IBM['interactive']};"
                f"border-radius: 4px; padding: 6px 12px;"
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
        self.setMinimumSize(1250, 900)
        self.resize(1400, 1000)

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

        self._apply_global_stylesheet()
        self._build_ui()

    # ── UI Construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Top blue accent bar ────────────────────────────────────────────────
        accent = QWidget()
        accent.setFixedHeight(4)
        accent.setStyleSheet(f"background: {IBM['interactive']};")
        root_layout.addWidget(accent)

        # ── Scrollable content ─────────────────────────────────────────────────
        content = QWidget()
        main = QVBoxLayout(content)
        main.setContentsMargins(36, 28, 36, 24)
        main.setSpacing(20)

        # Header
        header = QLabel("Reach Rate Calculator")
        header.setStyleSheet(
            f"font-family: {FF}; font-size: {TITLE}px; font-weight: 700;"
            f"color: {IBM['interactive']}; margin-bottom: 2px;"
        )
        main.addWidget(header)

        subtitle = QLabel(
            "Upload the 4 required files, optionally select a time frame, then click Process."
        )
        subtitle.setStyleSheet(
            f"font-family: {FF}; font-size: {BASE}px; color: {IBM['text_secondary']};"
        )
        main.addWidget(subtitle)

        # Divider
        main.addWidget(self._make_divider())

        # ── File Upload Section ────────────────────────────────────────────────
        upload_box = self._make_group("  Input Files")
        upload_layout = QVBoxLayout(upload_box)
        upload_layout.setSpacing(18)  # Increased vertical spacing between rows
        upload_layout.setContentsMargins(20, 24, 20, 20)  # Default padding inside group

        self._row_pa    = FileRow("PA Cases  (Active Cases Workbook)")
        self._row_sms   = FileRow("SMS View")
        self._row_email = FileRow("Email View")
        self._row_phone = FileRow("Phone Call View")

        for row in (self._row_pa, self._row_sms, self._row_email, self._row_phone):
            upload_layout.addWidget(row)

        main.addWidget(upload_box)

        # ── Time Frame Section ─────────────────────────────────────────────────
        time_box = self._make_group("  Time Frame  (Optional)")
        time_layout = QVBoxLayout(time_box)
        time_layout.setContentsMargins(20, 24, 20, 20)
        time_layout.setSpacing(12)

        self._use_dates = QCheckBox("Filter by date range")
        self._use_dates.setStyleSheet(
            f"QCheckBox {{ font-family: {FF}; font-size: {BASE}px;"
            f"color: {IBM['text_primary']}; spacing: 8px; }}"
            f"QCheckBox::indicator {{ width: 18px; height: 18px; }}"
            f"QCheckBox::indicator:unchecked {{"
            f"  border: 2px solid {IBM['border_strong']};"
            f"  border-radius: 2px; background: {IBM['layer_01']}; }}"
            f"QCheckBox::indicator:checked {{"
            f"  border: 2px solid {IBM['interactive']};"
            f"  border-radius: 2px; background: {IBM['interactive']}; }}"
        )
        self._use_dates.stateChanged.connect(self._toggle_date_range)
        time_layout.addWidget(self._use_dates)

        date_row = QWidget()
        date_hl  = QHBoxLayout(date_row)
        date_hl.setContentsMargins(0, 0, 0, 0)
        date_hl.setSpacing(16)

        for lbl_text, attr in (("From:", "_date_from"), ("To:", "_date_to")):
            lbl = QLabel(lbl_text)
            lbl.setStyleSheet(
                f"font-family: {FF}; font-size: {BASE}px; font-weight: 600;"
                f"color: {IBM['text_primary']};"
            )
            lbl.setMinimumWidth(40)
            date_hl.addWidget(lbl)

            de = QDateEdit()
            de.setCalendarPopup(True)
            if attr == "_date_from":
                de.setDate(QDate.currentDate().addMonths(-1))
            else:
                de.setDate(QDate.currentDate())
            de.setDisplayFormat("yyyy-MM-dd")
            de.setStyleSheet(self._date_edit_style())
            de.setMinimumWidth(120)
            de.setMinimumHeight(36)
            de.setEnabled(False)
            setattr(self, attr, de)
            date_hl.addWidget(de)

        date_hl.addStretch()
        time_layout.addWidget(date_row)
        main.addWidget(time_box)

        # ── Action Row ─────────────────────────────────────────────────────────
        main.addWidget(self._make_divider())

        act_row = QHBoxLayout()
        act_row.setSpacing(12)

        self._process_btn = QPushButton("⚙   Process")
        self._process_btn.setStyleSheet(_s_primary())
        self._process_btn.setMinimumHeight(40)
        self._process_btn.setMinimumWidth(120)
        self._process_btn.setFont(QFont("IBM Plex Sans", 13, QFont.Bold))
        self._process_btn.clicked.connect(self._on_process)
        act_row.addWidget(self._process_btn)

        self._open_btn = QPushButton("📂   Open Output")
        self._open_btn.setStyleSheet(_s_success())
        self._open_btn.setMinimumHeight(40)
        self._open_btn.setMinimumWidth(120)
        self._open_btn.setFont(QFont("IBM Plex Sans", 13, QFont.Bold))
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_output)
        act_row.addWidget(self._open_btn)

        act_row.addStretch()

        self._menu_btn = QPushButton("← Back to Menu")
        self._menu_btn.setStyleSheet(_s_ghost())
        self._menu_btn.setMinimumHeight(40)
        self._menu_btn.setMinimumWidth(120)
        self._menu_btn.setFont(QFont("IBM Plex Sans", 13, QFont.Bold))
        self._menu_btn.clicked.connect(self._back_to_menu)
        act_row.addWidget(self._menu_btn)

        main.addLayout(act_row)

        # ── Log Section ────────────────────────────────────────────────────────
        log_hdr = QLabel("ACTIVITY LOG")
        log_hdr.setStyleSheet(
            f"font-family: {FF}; font-size: {SMALL}px; font-weight: 700;"
            f"letter-spacing: 2px; color: {IBM['text_secondary']};"
            f"border-bottom: 2px solid {IBM['border_subtle']}; padding-bottom: 6px;"
        )
        main.addWidget(log_hdr)

        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        self._log_text.setStyleSheet(
            f"QTextEdit {{"
            f"  background-color: {IBM['layer_01']};"
            f"  border: 1px solid {IBM['border_subtle']};"
            f"  border-radius: 4px;"
            f"  font-family: {FM};"
            f"  font-size: {BASE}px;"
            f"  color: {IBM['text_primary']};"
            f"  padding: 10px;"
            f"  line-height: 1.5;"
            f"}}"
        )
        self._log_text.setMinimumHeight(200)
        main.addWidget(self._log_text, 1)

        # Footer
        footer = QLabel(
            f'<span style="font-size:{SMALL}px; color:{IBM["text_secondary"]};">'
            'Developed by: Ehab Elrify | Adam Maged &nbsp;·&nbsp; '
            f'<a href="mailto:ehab.elrify@ibm.com" style="color:{IBM["interactive"]};">ehab.elrify@ibm.com</a> | '
            f'<a href="mailto:abdelrahman.maged@ibm.com" style="color:{IBM["interactive"]};">abdelrahman.maged@ibm.com</a>'
            ' &nbsp;·&nbsp; Assurance Resolution Team</span>'
        )
        footer.setAlignment(Qt.AlignCenter)
        footer.setOpenExternalLinks(True)
        footer.setStyleSheet("padding-top: 8px;")
        main.addWidget(footer)

        root_layout.addWidget(content, 1)

    # ── Styling Helpers ────────────────────────────────────────────────────────

    def _make_group(self, title: str) -> QGroupBox:
        gb = QGroupBox(title)
        gb.setStyleSheet(f"""
            QGroupBox {{
                font-family: {FF};
                font-size: {BASE}px;
                font-weight: 700;
                color: {IBM['interactive']};
                border: 1.5px solid {IBM['border_subtle']};
                border-radius: 6px;
                margin-top: 18px;
                background: {IBM['layer_01']};
                padding-top: 6px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 16px;
                top: -2px;
                padding: 2px 8px 2px 8px;
                background: {IBM['layer_01']};
                color: {IBM['interactive']};
                border-radius: 3px;
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
                font-size: {BASE}px;
                color: {IBM['text_primary']};
                background: {IBM['layer_01']};
                border: 1px solid {IBM['border_subtle']};
                border-radius: 4px;
                padding: 6px 12px;
                min-height: 40px;
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
                background-color: {IBM['bg']};
                color: {IBM['text_primary']};
                font-family: {FF};
                font-size: {BASE}px;
            }}
            QScrollBar:vertical {{
                background: {IBM['layer_02']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {IBM['border_strong']};
                border-radius: 4px;
                min-height: 30px;
            }}
        """)

    # ── Event Handlers ─────────────────────────────────────────────────────────

    def _toggle_date_range(self, state):
        enabled = (state == Qt.Checked)
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
            f'<span style="color:#8d8d8d;font-size:{SMALL}px;">[{ts}]</span>'
            f'&nbsp;<span style="color:{color};{bold}font-size:{BASE}px;">'
            f'{sym}&nbsp;{msg}</span>'
        )
        self._log_text.append(entry)
        sb = self._log_text.verticalScrollBar()
        sb.setValue(sb.maximum())
        QApplication.processEvents()


# ── Entry Point ────────────────────────────────────────────────────────────────

def main():
    app = QApplication.instance() or QApplication(sys.argv)
    # Enable high-DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    win = ReachRateCalculatorWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
