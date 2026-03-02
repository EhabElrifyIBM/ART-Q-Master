# ============================================================================
# ibm_theme.py — Centralized IBM Carbon Design System QSS Stylesheet
# ============================================================================
# All ART Q Control dialogs import get_qss() from this module.
# IBM Carbon color tokens: https://carbondesignsystem.com/elements/color/tokens/
#
# Usage:
#   from ibm_theme import get_qss, FONT_FAMILY, IBM
#   self.setStyleSheet(get_qss())          # light (default)
#   self.setStyleSheet(get_qss('dark'))    # dark
#   self.setStyleSheet(get_qss('light', font_size=16))   # custom size
# ============================================================================

import json
import os

# ---------------------------------------------------------------------------
# Font
# ---------------------------------------------------------------------------
FONT_FAMILY = "'IBM Plex Sans', 'Segoe UI', Arial, sans-serif"

def _read_font_size() -> int:
    """Read font_size from config.json; fallback to 14."""
    try:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config.json'
        )
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                cfg = json.load(f)
            size = cfg.get('ui_settings', {}).get('font_size', 14)
            return max(10, min(40, int(size)))
    except Exception:
        pass
    return 14


# ---------------------------------------------------------------------------
# IBM Carbon color palettes
# ---------------------------------------------------------------------------
class IBM:
    """IBM Carbon Design System color tokens — both themes."""

    # ---- Light theme -------------------------------------------------------
    LIGHT = {
        # Backgrounds
        'bg':               '#f4f4f4',
        'layer_01':         '#ffffff',
        'layer_02':         '#f4f4f4',
        'layer_03':         '#e8e8e8',

        # Text
        'text_primary':     '#161616',
        'text_secondary':   '#525252',
        'text_placeholder': '#a8a8a8',
        'text_on_color':    '#ffffff',
        'text_disabled':    '#c6c6c6',

        # Interactive (primary blue)
        'interactive':      '#0f62fe',
        'interactive_hover':'#0353e9',
        'interactive_active':'#002d9c',

        # Accent variants for mode cards
        'purple':           '#6929c4',
        'purple_hover':     '#491d8b',
        'teal':             '#005d5d',
        'teal_hover':       '#004144',

        # Status
        'success':          '#198038',
        'success_bg':       '#defbe6',
        'warning':          '#f1c21b',
        'warning_bg':       '#fdf6dd',
        'danger':           '#da1e28',
        'danger_hover':     '#b81922',
        'danger_bg':        '#fff1f1',
        'info_bg':          '#edf5ff',

        # Progress bar
        'progress_track':   '#e0e0e0',
        'progress_fill':    '#0f62fe',
        'progress_success': '#198038',

        # Borders
        'border_subtle':    '#e0e0e0',
        'border_strong':    '#8d8d8d',
        'border_interactive':'#0f62fe',

        # Misc
        'focus':            '#0f62fe',
        'disabled_bg':      '#c6c6c6',
        'overlay':          'rgba(22,22,22,0.5)',
    }

    # ---- Dark theme --------------------------------------------------------
    DARK = {
        # Backgrounds
        'bg':               '#161616',
        'layer_01':         '#262626',
        'layer_02':         '#393939',
        'layer_03':         '#525252',

        # Text
        'text_primary':     '#f4f4f4',
        'text_secondary':   '#c6c6c6',
        'text_placeholder': '#6f6f6f',
        'text_on_color':    '#ffffff',
        'text_disabled':    '#525252',

        # Interactive
        'interactive':      '#4589ff',
        'interactive_hover':'#5596ff',
        'interactive_active':'#0353e9',

        # Accent variants
        'purple':           '#8a3ffc',
        'purple_hover':     '#7822fb',
        'teal':             '#009d9a',
        'teal_hover':       '#007d79',

        # Status
        'success':          '#42be65',
        'success_bg':       '#071908',
        'warning':          '#f1c21b',
        'warning_bg':       '#302400',
        'danger':           '#ff8389',
        'danger_hover':     '#ff99a0',
        'danger_bg':        '#2d0709',
        'info_bg':          '#001141',

        # Progress bar
        'progress_track':   '#393939',
        'progress_fill':    '#4589ff',
        'progress_success': '#42be65',

        # Borders
        'border_subtle':    '#393939',
        'border_strong':    '#6f6f6f',
        'border_interactive':'#4589ff',

        # Misc
        'focus':            '#4589ff',
        'disabled_bg':      '#525252',
        'overlay':          'rgba(22,22,22,0.7)',
    }


def _tokens(theme: str) -> dict:
    return IBM.DARK if theme == 'dark' else IBM.LIGHT


# ---------------------------------------------------------------------------
# Main QSS generator
# ---------------------------------------------------------------------------
def get_qss(theme: str = 'light', font_size: int = None) -> str:
    """
    Return a complete QSS stylesheet string for the given theme.

    Args:
        theme:      'light' (default) or 'dark'
        font_size:  Override font size in pt. If None, reads from config.json.

    Returns:
        str: Qt stylesheet (QSS)
    """
    if font_size is None:
        font_size = _read_font_size()

    c = _tokens(theme)
    fs = font_size
    fs_sm = max(9, fs - 2)
    fs_lg = fs + 2
    ff = FONT_FAMILY

    return f"""
/* ================================================================
   IBM Carbon Design System — ART Q Control
   Theme: {theme} | Font: {fs}pt
   ================================================================ */

/* ---- Base dialog / window ---------------------------------------- */
QDialog, QMainWindow, QWidget {{
    background-color: {c['bg']};
    color: {c['text_primary']};
    font-family: {ff};
    font-size: {fs}pt;
}}

/* ---- Labels ------------------------------------------------------- */
QLabel {{
    color: {c['text_primary']};
    font-family: {ff};
    font-size: {fs}pt;
    background: transparent;
}}
QLabel[role="title"] {{
    font-size: {fs_lg}pt;
    font-weight: 700;
    color: {c['text_primary']};
    letter-spacing: 0.3px;
}}
QLabel[role="subtitle"] {{
    font-size: {fs_sm}pt;
    color: {c['text_secondary']};
}}
QLabel[role="caption"] {{
    font-size: {fs_sm}pt;
    color: {c['text_secondary']};
}}
QLabel[role="code"] {{
    font-family: 'IBM Plex Mono', 'Consolas', monospace;
    font-size: {fs_sm}pt;
    background-color: {c['layer_02']};
    color: {c['text_primary']};
    padding: 4px 8px;
    border-radius: 2px;
}}

/* ---- QFrame cards ------------------------------------------------- */
QFrame {{
    background-color: {c['layer_01']};
    border: 1px solid {c['border_subtle']};
    border-radius: 4px;
}}
QFrame[role="info"] {{
    background-color: {c['info_bg']};
    border-left: 4px solid {c['interactive']};
    border-top: 1px solid {c['border_subtle']};
    border-right: 1px solid {c['border_subtle']};
    border-bottom: 1px solid {c['border_subtle']};
    border-radius: 0px;
}}
QFrame[role="success"] {{
    background-color: {c['success_bg']};
    border-left: 4px solid {c['success']};
    border-top: 1px solid {c['border_subtle']};
    border-right: 1px solid {c['border_subtle']};
    border-bottom: 1px solid {c['border_subtle']};
    border-radius: 0px;
}}
QFrame[role="danger"] {{
    background-color: {c['danger_bg']};
    border-left: 4px solid {c['danger']};
    border-top: 1px solid {c['border_subtle']};
    border-right: 1px solid {c['border_subtle']};
    border-bottom: 1px solid {c['border_subtle']};
    border-radius: 0px;
}}
QFrame[role="card-blue"] {{
    background-color: {c['layer_01']};
    border-left: 4px solid {c['interactive']};
    border-top: 1px solid {c['border_subtle']};
    border-right: 1px solid {c['border_subtle']};
    border-bottom: 1px solid {c['border_subtle']};
    border-radius: 0px;
}}
QFrame[role="card-purple"] {{
    background-color: {c['layer_01']};
    border-left: 4px solid {c['purple']};
    border-top: 1px solid {c['border_subtle']};
    border-right: 1px solid {c['border_subtle']};
    border-bottom: 1px solid {c['border_subtle']};
    border-radius: 0px;
}}
QFrame[role="card-teal"] {{
    background-color: {c['layer_01']};
    border-left: 4px solid {c['teal']};
    border-top: 1px solid {c['border_subtle']};
    border-right: 1px solid {c['border_subtle']};
    border-bottom: 1px solid {c['border_subtle']};
    border-radius: 0px;
}}
QFrame[role="flat"] {{
    background: transparent;
    border: none;
    border-radius: 0px;
}}

/* ---- Primary button (IBM Blue) ------------------------------------ */
QPushButton {{
    background-color: {c['interactive']};
    color: {c['text_on_color']};
    font-family: {ff};
    font-size: {fs}pt;
    font-weight: 600;
    padding: 12px 28px;
    border: none;
    border-radius: 8px;
    min-height: 44px;
    outline: none;
    letter-spacing: 0.2px;
}}
QPushButton:hover {{
    background-color: {c['interactive_hover']};
}}
QPushButton:pressed {{
    background-color: {c['interactive_active']};
}}
QPushButton:disabled {{
    background-color: {c['disabled_bg']};
    color: {c['text_disabled']};
}}

/* ---- Secondary button (outlined) ---------------------------------- */
QPushButton[role="secondary"] {{
    background-color: transparent;
    color: {c['interactive']};
    border: 2px solid {c['interactive']};
    font-weight: 600;
    border-radius: 8px;
}}
QPushButton[role="secondary"]:hover {{
    background-color: {c['layer_02']};
}}
QPushButton[role="secondary"]:pressed {{
    background-color: {c['layer_03']};
}}

/* ---- Ghost button (text only) ------------------------------------- */
QPushButton[role="ghost"] {{
    background-color: transparent;
    color: {c['text_secondary']};
    border: 1px solid {c['border_subtle']};
    font-weight: 500;
    border-radius: 8px;
}}
QPushButton[role="ghost"]:hover {{
    background-color: {c['layer_02']};
    color: {c['text_primary']};
}}

/* ---- Danger button (red / abort) ---------------------------------- */
QPushButton[role="danger"] {{
    background-color: {c['danger']};
    color: {c['text_on_color']};
    border: none;
    font-weight: 600;
}}
QPushButton[role="danger"]:hover {{
    background-color: {c['danger_hover']};
}}

/* ---- Purple button (Case Reviewer accent) ------------------------- */
QPushButton[role="purple"] {{
    background-color: {c['purple']};
    color: {c['text_on_color']};
    border: none;
    font-weight: 600;
}}
QPushButton[role="purple"]:hover {{
    background-color: {c['purple_hover']};
}}

/* ---- Teal button (Company Process accent) ------------------------- */
QPushButton[role="teal"] {{
    background-color: {c['teal']};
    color: {c['text_on_color']};
    border: none;
    font-weight: 600;
}}
QPushButton[role="teal"]:hover {{
    background-color: {c['teal_hover']};
}}

/* ---- Progress bar ------------------------------------------------- */
QProgressBar {{
    border: none;
    border-radius: 6px;
    background-color: {c['progress_track']};
    height: 8px;
    text-align: center;
    font-size: {fs_sm}pt;
    font-weight: 700;
    color: #ffffff;
}}
QProgressBar::chunk {{
    background-color: {c['progress_fill']};
    border-radius: 6px;
}}
QProgressBar[state="success"]::chunk {{
    background-color: {c['progress_success']};
}}

/* ---- QLineEdit / QTextEdit ---------------------------------------- */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['layer_01']};
    color: {c['text_primary']};
    border: 1px solid {c['border_strong']};
    border-bottom: 2px solid {c['border_strong']};
    border-radius: 4px;
    padding: 8px 12px;
    font-size: {fs}pt;
    font-family: {ff};
    selection-background-color: {c['interactive']};
    selection-color: {c['text_on_color']};
}}
QLineEdit:focus, QTextEdit:focus {{
    border-bottom: 2px solid {c['focus']};
    outline: none;
}}
QLineEdit:disabled {{
    background-color: {c['layer_02']};
    color: {c['text_disabled']};
}}

/* ---- QComboBox ---------------------------------------------------- */
QComboBox {{
    background-color: {c['layer_01']};
    color: {c['text_primary']};
    border: 1px solid {c['border_strong']};
    border-radius: 4px;
    padding: 8px 12px;
    font-size: {fs}pt;
    font-family: {ff};
    min-height: 40px;
    selection-background-color: {c['interactive']};
}}
QComboBox:hover {{
    border-color: {c['focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 32px;
}}
QComboBox::down-arrow {{
    width: 12px;
    height: 12px;
}}
QComboBox QAbstractItemView {{
    background-color: {c['layer_01']};
    color: {c['text_primary']};
    border: 1px solid {c['border_subtle']};
    selection-background-color: {c['interactive']};
    selection-color: {c['text_on_color']};
    padding: 4px;
}}

/* ---- QCheckBox ---------------------------------------------------- */
QCheckBox {{
    color: {c['text_primary']};
    font-size: {fs}pt;
    font-family: {ff};
    spacing: 10px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {c['border_strong']};
    border-radius: 2px;
    background-color: {c['layer_01']};
}}
QCheckBox::indicator:checked {{
    background-color: {c['interactive']};
    border-color: {c['interactive']};
}}
QCheckBox::indicator:hover {{
    border-color: {c['focus']};
}}

/* ---- QRadioButton ------------------------------------------------- */
QRadioButton {{
    color: {c['text_primary']};
    font-size: {fs}pt;
    font-family: {ff};
    spacing: 10px;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {c['border_strong']};
    border-radius: 9px;
    background-color: {c['layer_01']};
}}
QRadioButton::indicator:checked {{
    background-color: {c['interactive']};
    border-color: {c['interactive']};
    width: 18px;
    height: 18px;
}}
QRadioButton::indicator:hover {{
    border-color: {c['focus']};
}}

/* ---- QScrollArea / Scrollbar -------------------------------------- */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: {c['layer_02']};
    width: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {c['border_strong']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c['text_secondary']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {c['layer_02']};
    height: 8px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {c['border_strong']};
    border-radius: 4px;
    min-width: 30px;
}}

/* ---- QGroupBox ---------------------------------------------------- */
QGroupBox {{
    color: {c['text_secondary']};
    font-size: {fs_sm}pt;
    font-weight: 600;
    font-family: {ff};
    border: 1px solid {c['border_subtle']};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {c['text_secondary']};
    font-size: {fs_sm}pt;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

/* ---- Divider line ------------------------------------------------- */
QFrame[frameShape="4"], QFrame[frameShape="HLine"] {{
    background: transparent;
    border: none;
    border-top: 1px solid {c['border_subtle']};
    max-height: 1px;
}}

/* ---- QMessageBox -------------------------------------------------- */
QMessageBox {{
    background-color: {c['bg']};
}}
QMessageBox QLabel {{
    color: {c['text_primary']};
    font-size: {fs}pt;
}}
""".strip()


def get_mode_card_style(accent_color: str, hover_color: str, theme: str = 'light') -> str:
    """
    Returns inline QSS for a mode-selector card button.
    Accent bar is on the left; hover lightens the background.
    """
    c = _tokens(theme)
    return f"""
        QPushButton {{
            background-color: {c['layer_01']};
            color: {c['text_primary']};
            font-family: {FONT_FAMILY};
            font-weight: 600;
            padding: 18px 20px;
            border: 1px solid {c['border_subtle']};
            border-left: 5px solid {accent_color};
            border-radius: 4px;
            min-height: 60px;
            text-align: left;
        }}
        QPushButton:hover {{
            background-color: {c['layer_02']};
            border-left-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {c['layer_03']};
        }}
    """.strip()
