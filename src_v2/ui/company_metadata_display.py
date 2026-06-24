# ============================================================================
# company_metadata_display.py - Company Information Display
# ============================================================================
# Phase 5.2: Company Metadata Integration
#
# Displays company information including:
# - Company name
# - Contact email/phone
# - State/Province
# - Local time calculation
# ============================================================================

import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Lazy imports
timezone_map = None


def _init_timezone_map():
    """Initialize timezone map."""
    global timezone_map
    try:
        from utils.timezone_map import get_timezone_offset, calculate_local_time
        timezone_map = {
            'get_offset': get_timezone_offset,
            'calc_local': calculate_local_time
        }
        return True
    except Exception as e:
        print(f"[WARNING] Could not load timezone_map: {e}")
        return False


class CompanyMetadataDialog(QDialog):
    """
    Dialog displaying company information and metadata.
    
    Shows:
    - Company name
    - Contact information (email, phone)
    - State/Province
    - Local time for the company location
    - Number of cases to process
    """
    
    def __init__(self, company_data, parent=None):
        super().__init__(parent)
        self.company_data = company_data
        self.font_settings = company_data.get('font_settings', None)
        self.setWindowTitle("Company Information")
        self.setMinimumWidth(520)
        self.setModal(True)

        # ── IBM tokens ─────────────────────────────────────────────────────────
        try:
            from ART_Q_Control.ibm_theme import IBM, get_qss, _read_font_size
        except Exception:
            try:
                import sys, os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ART Q Control'))
                from ibm_theme import IBM, get_qss, _read_font_size
            except Exception:
                IBM = None
                get_qss = None
                _read_font_size = None

        if IBM and get_qss and _read_font_size:
            _c = IBM.LIGHT
            _fs = _read_font_size()
            self.setStyleSheet(get_qss('light', _fs))
        else:
            _c = {
                'bg': '#f4f4f4', 'layer_01': '#ffffff', 'layer_02': '#f4f4f4',
                'text_primary': '#161616', 'text_secondary': '#525252',
                'text_on_color': '#ffffff', 'interactive': '#0f62fe',
                'interactive_hover': '#0353e9', 'border_subtle': '#e0e0e0',
                'teal': '#005d5d', 'teal_hover': '#004144',
                'purple': '#6929c4', 'success': '#198038',
                'disabled_bg': '#c6c6c6',
            }
            _fs = 13
            self.setStyleSheet(
                f"QDialog {{ background-color: {_c['bg']}; font-family: 'IBM Plex Sans','Segoe UI',Arial; }}"
            )

        self.setFont(QFont('IBM Plex Sans', _fs))
        _init_timezone_map()
        self._c = _c
        self._fs = _fs
        self._setup_ui()

    def _setup_ui(self):
        """IBM Carbon layout — company metadata."""
        _c = self._c
        _fs = self._fs

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        def _label(text, bold=False, size_delta=0, color=None):
            lbl = QLabel(text)
            w = _fs + size_delta
            lbl.setFont(QFont('IBM Plex Sans', w, QFont.Bold if bold else QFont.Normal))
            style = f"background: transparent; border: none; color: {color or _c['text_primary']};"
            lbl.setStyleSheet(style)
            lbl.setWordWrap(True)
            return lbl

        def _accent_card(border_color):
            frame = QFrame()
            frame.setStyleSheet(
                f"QFrame {{ background: {_c['layer_01']};"
                f" border-left: 4px solid {border_color};"
                f" border-top: 1px solid {_c['border_subtle']};"
                f" border-right: 1px solid {_c['border_subtle']};"
                f" border-bottom: 1px solid {_c['border_subtle']}; }}"
            )
            return frame

        # ── COMPANY NAME HEADER ────────────────────────────────────────────────
        company_name = self.company_data.get('company_name', 'Unknown Company')

        hdr = _label(company_name, bold=True, size_delta=4, color=_c['interactive'])
        hdr.setAlignment(Qt.AlignLeft)
        layout.addWidget(hdr)

        sub = _label("Review company information before proceeding", size_delta=-2, color=_c['text_secondary'])
        layout.addWidget(sub)

        # ── BATCH PROGRESS CARD ────────────────────────────────────────────────
        batch_index   = self.company_data.get('batch_index', None)
        total_groups  = self.company_data.get('total_groups', None)
        cases_left    = self.company_data.get('cases_left', None)
        groups_left   = self.company_data.get('groups_left', None)

        if batch_index is not None and total_groups is not None:
            from PyQt5.QtWidgets import QProgressBar

            prog_card = _accent_card(_c['teal'])
            pc_lyt = QVBoxLayout(prog_card)
            pc_lyt.setContentsMargins(14, 10, 14, 10)
            pc_lyt.setSpacing(6)

            # Stat row
            stat_row_w = QWidget()
            stat_row_w.setStyleSheet("background: transparent; border: none;")
            stat_row = QHBoxLayout(stat_row_w)
            stat_row.setContentsMargins(0, 0, 0, 0)
            stat_row.setSpacing(24)

            def _stat(lbl_text, val_text, color):
                col = QVBoxLayout()
                col.setSpacing(1)
                l = _label(lbl_text.upper(), bold=True, size_delta=-4, color=_c['text_secondary'])
                l.setAlignment(Qt.AlignLeft)
                v = _label(str(val_text), bold=True, size_delta=3, color=color)
                v.setAlignment(Qt.AlignLeft)
                col.addWidget(l)
                col.addWidget(v)
                return col

            stat_row.addLayout(_stat("Batch", f"{batch_index} / {total_groups}", _c['teal']))
            if cases_left is not None:
                stat_row.addLayout(_stat("Cases Left", cases_left, _c['interactive']))
            if groups_left is not None:
                stat_row.addLayout(_stat("Groups After This", groups_left, _c['text_secondary']))
            stat_row.addStretch()
            pc_lyt.addWidget(stat_row_w)

            # Slim progress bar
            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(total_groups)
            bar.setValue(batch_index)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(
                f"QProgressBar {{ border: none; border-radius: 3px;"
                f" background: {_c['progress_track']}; }}"
                f"QProgressBar::chunk {{ background: {_c['teal']}; border-radius: 3px; }}"
            )
            pc_lyt.addWidget(bar)
            layout.addWidget(prog_card)

        layout.addSpacing(4)

        # ── CONTACT CARD ───────────────────────────────────────────────────────
        contact_card = _accent_card(_c['interactive'])
        cl = QGridLayout(contact_card)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.setSpacing(8)
        cl.setColumnStretch(1, 1)

        def _row(grid, r, key, val, val_color=None):
            k = _label(key, bold=True, size_delta=-1, color=_c['text_secondary'])
            v = _label(str(val), size_delta=-1, color=val_color or _c['text_primary'])
            grid.addWidget(k, r, 0)
            grid.addWidget(v, r, 1)

        email_val = self.company_data.get('email', 'N/A')
        _row(cl, 0, "Email", email_val, _c['interactive'])

        phone = self.company_data.get('phone', None)
        if phone:
            _row(cl, 1, "Phone", phone, _c['interactive'])

        layout.addWidget(contact_card)

        # ── LOCATION CARD ──────────────────────────────────────────────────────
        state = self.company_data.get('state_province', None)
        if state:
            loc_card = _accent_card(_c['teal'])
            ll = QGridLayout(loc_card)
            ll.setContentsMargins(14, 12, 14, 12)
            ll.setSpacing(8)
            ll.setColumnStretch(1, 1)
            _row(ll, 0, "Location", state, _c['teal'])

            if timezone_map:
                try:
                    local_time = timezone_map['calc_local'](state)
                    if local_time:
                        _row(ll, 1, "Local Time", local_time.strftime("%H:%M  %Z"), _c['teal'])
                except Exception:
                    pass

            layout.addWidget(loc_card)

        # ── CASE COUNT CARD ────────────────────────────────────────────────────
        case_count = self.company_data.get('case_count', 0)
        case_card = _accent_card(_c['text_secondary'])
        ccl = QHBoxLayout(case_card)
        ccl.setContentsMargins(14, 10, 14, 10)
        ccl.setSpacing(16)

        lbl_key = _label("Cases to Process", bold=True, size_delta=-2, color=_c['text_secondary'])
        lbl_val = _label(
            f"{case_count} case{'s' if case_count != 1 else ''}",
            bold=True, size_delta=2, color=_c['interactive']
        )
        ccl.addWidget(lbl_key)
        ccl.addWidget(lbl_val)
        ccl.addStretch()
        layout.addWidget(case_card)

        layout.addSpacing(8)

        # ── CONTINUE BUTTON with 30-second auto-proceed countdown ─────────────
        COUNTDOWN = 30
        self._countdown_secs = COUNTDOWN

        self._btn = QPushButton(f"Understood  —  Continue  ({COUNTDOWN})")
        self._btn.setFont(QFont('IBM Plex Sans', _fs, QFont.Bold))
        self._btn.setMinimumHeight(46)
        self._btn_base_style = (
            f"QPushButton {{ background-color: {_c['interactive']};"
            f" color: #ffffff; border: none; border-radius: 8px;"
            f" font-weight: 700; font-size: {_fs}pt;"
            f" padding: 10px 28px; letter-spacing: 0.3px; }}"
            f"QPushButton:hover {{ background-color: {_c['interactive_hover']}; }}"
            f"QPushButton:pressed {{ background-color: #002d9c; }}"
        )
        self._btn.setStyleSheet(self._btn_base_style)
        self._btn.clicked.connect(self._on_continue)
        layout.addWidget(self._btn)

        # Start the countdown timer — fires every 1 000 ms
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

        self.setLayout(layout)
        self.adjustSize()

    def _tick(self):
        """Decrement countdown; auto-accept when it reaches 0."""
        self._countdown_secs -= 1
        if self._countdown_secs <= 0:
            self._timer.stop()
            self.accept()
        else:
            self._btn.setText(f"Understood  —  Continue  ({self._countdown_secs})")

    def _on_continue(self):
        """User clicked manually — stop timer and accept."""
        self._timer.stop()
        self.accept()

    
    @staticmethod
    def show_company_info(company_data, parent=None):
        """
        Show company metadata dialog.
        
        Args:
            company_data (dict): Company information
            parent: Parent widget
        
        Returns:
            bool: True if user accepted, False if cancelled
        """
        dialog = CompanyMetadataDialog(company_data, parent)
        result = dialog.exec_()
        return result == QDialog.Accepted


def extract_company_metadata(row, excel_df=None):
    """
    Extract company metadata from a row.
    
    Args:
        row: DataFrame row with company data
        excel_df: Full DataFrame (optional, for lookup)
    
    Returns:
        dict: Company metadata
    """
    try:
        metadata = {
            'company_name': row.get('Company Name', 'Unknown'),
            'email': row.get('Email', '') or row.get('Primary Email (Contact) (Contact)', ''),
            'phone': row.get('Phone Number', '') or row.get('Contact Mobile Phone', ''),
            'state_province': row.get('State/Province', '') or row.get('State/Province (Case) (Case)', ''),
            'contact_name': row.get('Customer Name', '') or row.get('Contact Name', ''),
        }
        return metadata
    except Exception as e:
        print(f"[WARNING] Error extracting company metadata: {e}")
        return {}


def format_company_metadata_display(row, excel_df=None):
    """
    Format company metadata for display.
    
    Args:
        row: DataFrame row
        excel_df: Full DataFrame (optional)
    
    Returns:
        str: Formatted display string
    """
    metadata = extract_company_metadata(row, excel_df)
    
    display_parts = [
        f"🏢 {metadata.get('company_name', 'Company')}",
        f"📧 {metadata.get('email', 'No email')}",
    ]
    
    if metadata.get('phone'):
        display_parts.append(f"📞 {metadata['phone']}")
    
    if metadata.get('state_province'):
        display_parts.append(f"📍 {metadata['state_province']}")
    
    return " | ".join(display_parts)
