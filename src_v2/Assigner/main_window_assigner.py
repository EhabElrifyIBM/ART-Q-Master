from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QCheckBox, QGroupBox, QComboBox, QGridLayout, QLineEdit, QScrollArea,
    QPushButton, QProgressBar, QTextEdit, QHBoxLayout, QFileDialog, QMessageBox, QMainWindow, QFrame,
    QDesktopWidget, QSizePolicy, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog,
    QApplication, QScrollBar, QLayoutItem
)
from datetime import datetime
from PyQt5.QtCore import (
    Qt, QThread, pyqtSignal, QSize, QObject, QModelIndex
)
from PyQt5.QtGui import QFont, QPixmap, QIcon, QResizeEvent
import sys
import os
import json
from typing import Optional

# Modern UI systems
from ui.typography_mixin import V2TypographyMixin
from ui.theme_manager import ThemeManager
from ui.services import get_v2_settings_bus

# Handle both package and standalone imports
try:
    from .assigner_processor import FileProcessor
except ImportError:
    from assigner_processor import FileProcessor

# Qt constants for alignment and item flags
class Alignment:
    def __init__(self):
        # Standard Qt alignment values
        self.Left = 0x0001     # Qt::AlignLeft
        self.Right = 0x0002    # Qt::AlignRight
        self.HCenter = 0x0004  # Qt::AlignHCenter
        self.VCenter = 0x0080  # Qt::AlignVCenter
        self.Center = self.HCenter | self.VCenter

class ItemFlags:
    def __init__(self):
        # Standard Qt item flag values
        self.NoItemFlags = 0x0000
        self.ItemIsSelectable = 0x0001
        self.ItemIsEditable = 0x0002
        self.ItemIsEnabled = 0x0004
        self.Standard = self.ItemIsSelectable | self.ItemIsEnabled

class HeaderSectionResizeMode:
    def __init__(self):
        # Standard Qt header resize modes
        self.Interactive = 0
        self.Fixed = 2
        self.Stretch = 1
        self.ResizeToContents = 3

# Initialize Qt constants
ALIGN = Alignment()
FLAGS = ItemFlags()
HEADER = HeaderSectionResizeMode()

class ScrollAreaWithDelete(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        
    def clearLayout(self, layout):
        if not layout:
            return
        while layout.count():
            item = layout.takeAt(0)
            if not item:
                continue
            widget = item.widget()
            if widget:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout:
                self.clearLayout(child_layout)

class FileProcessingWorker(QObject):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, raw_file, prev_file, sms_file, email_file, output_file, selected_handlers, chat_agent_info=None, protect_companies=False):
        super().__init__()
        self.raw_file = raw_file
        self.prev_file = prev_file
        self.sms_file = sms_file
        self.email_file = email_file
        self.output_file = output_file
        self.selected_handlers = selected_handlers
        self.chat_agent_info = chat_agent_info
        self.protect_companies = protect_companies

    def run(self):
        try:
            from .assigner_processor import FileProcessor
        except ImportError:
            from assigner_processor import FileProcessor
        processor = FileProcessor()
        processor.setup_logging(log_callback=self.emit_log)
        try:
            self.emit_log("\n=== Starting File Processing ===")
            self.emit_log(f"Raw file: {self.raw_file}")
            if self.prev_file:
                self.emit_log(f"Previous file: {self.prev_file}")
            if self.sms_file:
                self.emit_log(f"SMS file: {self.sms_file}")
            self.emit_log(f"Selected handlers: {', '.join(self.selected_handlers)}")
            
            # Log Chat Agent info if enabled
            if self.chat_agent_info:
                names = self.chat_agent_info.get('supporter_names', [self.chat_agent_info.get('supporter_name', '')])
                if self.chat_agent_info.get('dev_mode') and len(names) > 1:
                    self.emit_log(
                        f"Chat Agent [DEV MODE]: {', '.join(names)} "
                        f"({len(names)} agents, 15% capacity bonus each)"
                    )
                else:
                    self.emit_log(f"Chat Agent: {names[0]} (with 15% capacity bonus)")

            is_valid, message = processor.validate_files(
                self.raw_file,
                self.prev_file if self.prev_file else None,
                self.sms_file if self.sms_file else None
            )
            if not is_valid:
                self.emit_log(f"Validation failed: {message}")
                self.finished.emit(False, message)
                return
            self.emit_log("File validation successful")
            self.progress_signal.emit(10)
            success, message = processor.process_files(
                self.raw_file,
                self.prev_file if self.prev_file else None,
                self.sms_file if self.sms_file else None,
                self.email_file if self.email_file else None,
                self.output_file,
                self.selected_handlers,
                chat_agent_info=self.chat_agent_info,
                protect_companies=self.protect_companies
            )
            if success:
                self.progress_signal.emit(100)
                self.emit_log("\nProcessing completed successfully!")
                self.emit_log(f"Output saved to: {self.output_file}")
                self.finished.emit(True, message)
            else:
                self.emit_log("\nProcessing failed")
                self.finished.emit(False, message)
        except Exception as e:
            error_msg = str(e)
            self.emit_log(f"\nError during processing: {error_msg}")
            self.finished.emit(False, error_msg)

    def emit_log(self, message):
        self.log_signal.emit(message)

class MainWindow(QMainWindow, V2TypographyMixin):
    def __init__(self):
        super().__init__()
        V2TypographyMixin.__init__(self)  # Initialize typography mixin
        
        self.setWindowTitle("ART Q Master V2 - Assigner")
        self.setGeometry(100, 100, 1220, 760)
        
        # Initialize modern UI systems
        self.theme_manager = ThemeManager()
        self.settings_bus = get_v2_settings_bus()
        
        # Track dynamic widgets for typography updates
        self._dynamic_labels = []
        self._dynamic_buttons = []
        self._dynamic_groupboxes = []
        self._dynamic_lineedits = []

        # Initialize handler dictionaries
        self.handler_vars = {}
        
        # Initialize Chat Agent variables
        self.chat_agent_checkbox = None
        self.chat_agent_input = None         # single-name mode (QLineEdit)
        self.chat_agent_input_multi = None   # DEV MODE multi-name (QTextEdit)
        self.chat_agent_label = None
        self._chat_agent_single_row = None   # sub-widget for normal mode
        self._chat_agent_dev_row = None      # sub-widget for DEV MODE

        # Initialize protect companies checkbox
        self.protect_companies_checkbox = None

        # Load saved handlers or use defaults
        self.load_handlers()

        # Initialize file paths
        self.raw_file = None
        self.previous_file = None
        self.sms_file = None
        self.email_file = None # Added for email replies
        self.file_labels = {}

        # Create log area first
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)

        # Initialize stats labels
        self.wo_stats_label = QLabel("No file loaded.")
        self.handler_dist_label = QLabel("Select handlers to see distribution.")

        # Create main window
        self.main_frame = self.create_main_window()
        self.setCentralWidget(self.main_frame)
        
        # Hide progress bars and related UI elements (progress feature removed)
        if hasattr(self, 'progress_bar'):
            try:
                self.progress_bar.setVisible(False)
            except Exception:
                pass

        # Load handlers from file
        self.load_handlers()

        # Create file processor
        self.processor = FileProcessor()
        self.processor.setup_logging(log_callback=self.add_log)

        # Connect to theme changes
        self.settings_bus.theme_changed.connect(self._on_theme_changed)

        # Connect to font size changes
        self.settings_bus.font_size_changed.connect(self._on_font_changed)

        # Connect to DEV MODE changes — swap Chat Agent input widget live
        self.settings_bus.dev_mode_changed.connect(self._on_dev_mode_changed)

        # Sync initial DEV MODE state from config
        try:
            from config.manager import config_manager as _cm
            self.settings_bus.set_dev_mode(_cm.get('advanced.dev_mode', False))
        except Exception:
            pass
        
        # Apply initial styling and typography
        self.setStyleSheet(self.ibm_stylesheet())
        self.apply_typography()
        
        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Initial log message
        self.add_log("Application started successfully.")
        
    def ibm_stylesheet(self) -> str:
        """Generate IBM-themed stylesheet using modern theme manager."""
        # Get base font size from typography system
        base_size = self.get_size('body')  # Returns pixel size as int
        section_size = self.get_size('h3')
        button_size = self.get_size('button')
        
        # Get colors from theme manager
        bg = self.theme_manager.get_color('background')
        text = self.theme_manager.get_color('text_primary')
        primary = self.theme_manager.get_color('primary')
        border = self.theme_manager.get_color('border')
        field_bg = self.theme_manager.get_color('surface')
        hover = self.theme_manager.get_color('primary_hover')
        
        return f"""
            QWidget {{
                background-color: {bg};
                color: {text};
                font-family: 'IBM Plex Sans', Arial, sans-serif;
                font-size: {base_size}px;
            }}
            QMainWindow {{
                background-color: {bg};
            }}
            QGroupBox {{
                border: 1px solid {border};
                border-radius: 12px;
                margin-top: 12px;
                background-color: {field_bg};
                font-weight: bold;
                font-size: {section_size}px;
            }}
            QGroupBox:title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 2px 8px 2px 8px;
                color: {primary};
            }}
            QLabel {{
                font-size: {base_size}px;
                color: {text};
            }}
            QLineEdit {{
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
                background: {field_bg};
                color: {text};
                font-size: {base_size}px;
            }}
            QPushButton {{
                background-color: {primary};
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 18px;
                font-weight: bold;
                font-size: {button_size}px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
            QCheckBox {{
                spacing: 8px;
                font-size: {base_size}px;
                color: {text};
            }}
            QComboBox {{
                background-color: {field_bg};
                color: {text};
                border: 1px solid {border};
                padding: 8px;
                border-radius: 8px;
                font-size: {base_size}px;
            }}
            QProgressBar {{
                border: 1px solid {border};
                border-radius: 8px;
                text-align: center;
                height: 24px;
                background: {field_bg};
            }}
            QProgressBar::chunk {{
                background-color: {primary};
                border-radius: 8px;
            }}
            QTableWidget {{
                background: {field_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.theme_manager.get_color('surface')};
                width: 10px;
                margin: 2px 0 2px 0;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.theme_manager.get_color('border')};
                min-height: 36px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {primary};
            }}
            QTextEdit {{
                background-color: {field_bg};
                color: {text};
                border: 1px solid {border};
                border-radius: 8px;
                padding: 8px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: {base_size}px;
            }}
        """

    def create_main_window(self):
        # Create the main widget that will hold everything
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QFrame()
        # Use theme colors instead of hardcoded black
        header_bg = self.theme_manager.get_color('surface')  # Use 'surface' instead of 'layer_01'
        header.setStyleSheet(f"background-color: {header_bg};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 14, 24, 14)
        
        # Left side of header with ART Q Master
        header_left = QWidget()
        header_left_layout = QHBoxLayout(header_left)
        header_left_layout.setContentsMargins(0, 0, 0, 0)
        header_left_layout.setSpacing(10)
        
        ibm_title = QLabel("ART Q Master")
        self._dynamic_labels.append((ibm_title, "title_blue"))
        
        # Version label
        version_label = QLabel("v0.2.0")
        self._dynamic_labels.append((version_label, "version_light"))
        
        header_left_layout.addWidget(ibm_title)
        header_left_layout.addWidget(version_label)
        
        # Right side of header with Main Menu and Progress View buttons
        main_menu_btn = QPushButton("Main Menu")
        self._dynamic_buttons.append((main_menu_btn, "header"))
        main_menu_btn.clicked.connect(self.open_main_menu)

        progress_btn = QPushButton("Progress View")
        self._dynamic_buttons.append((progress_btn, "header"))
        progress_btn.clicked.connect(self.show_progress)
        # Disable and hide the Progress View button for release
        progress_btn.setEnabled(False)
        progress_btn.setVisible(False)
        header_layout.addWidget(header_left)
        header_layout.addStretch()
        header_layout.addWidget(main_menu_btn)
        header_layout.addWidget(progress_btn)

        # Main content
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(14)
        content_layout.setContentsMargins(24, 18, 24, 18)

        # --- Handlers Frame (left panel) ---
        self.handlers_frame = QGroupBox("Handlers")
        self._dynamic_groupboxes.append(self.handlers_frame)
        handlers_layout = QVBoxLayout(self.handlers_frame)
        handlers_layout.setSpacing(5)

        # Add search bar
        self.search_bar = QLineEdit()
        self._dynamic_lineedits.append(self.search_bar)
        self.search_bar.setPlaceholderText("Search handlers...")
        self.search_bar.textChanged.connect(self.filter_handlers)
        handlers_layout.addWidget(self.search_bar)

        # Add select all button
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setCheckable(True)
        self.select_all_btn.clicked.connect(self.toggle_all_handlers)
        handlers_layout.addWidget(self.select_all_btn)

        # Create scroll area for handlers
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(4)
        self.scroll_area.setWidget(self.scroll_content)
        handlers_layout.addWidget(self.scroll_area)

        # Initial population of handlers
        self.handler_vars = {}
        self.repopulate_handlers(self.current_handlers)

        # Add and Remove handler buttons layout
        buttons_layout = QHBoxLayout()
        
        add_handler_btn = QPushButton("Add Handler")
        add_handler_btn.clicked.connect(self._add_new_handler)
        buttons_layout.addWidget(add_handler_btn)
        
        remove_handler_btn = QPushButton("Remove Handler")
        remove_handler_btn.clicked.connect(self._remove_handler)
        buttons_layout.addWidget(remove_handler_btn)
        
        handlers_layout.addLayout(buttons_layout)

        # --- Create right panel with file inputs ---
        right_panel_widget = QWidget()
        right_panel = QVBoxLayout(right_panel_widget)
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(10)

        # Raw File Input
        raw_file_box = QGroupBox("Raw File")
        self._dynamic_groupboxes.append(raw_file_box)
        raw_file_layout = QHBoxLayout()
        self.raw_file_path = QLineEdit()
        self._dynamic_lineedits.append(self.raw_file_path)
        raw_browse_btn = QPushButton("Browse")
        raw_browse_btn.clicked.connect(lambda: self.browse_file("raw"))
        raw_file_layout.addWidget(self.raw_file_path)
        raw_file_layout.addWidget(raw_browse_btn)
        raw_file_box.setLayout(raw_file_layout)
        right_panel.addWidget(raw_file_box)

        # Previous File Input
        prev_file_box = QGroupBox("Previous File")
        self._dynamic_groupboxes.append(prev_file_box)
        prev_file_layout = QHBoxLayout()
        self.prev_file_path = QLineEdit()
        self._dynamic_lineedits.append(self.prev_file_path)
        prev_browse_btn = QPushButton("Browse")
        prev_browse_btn.clicked.connect(lambda: self.browse_file("previous"))
        prev_file_layout.addWidget(self.prev_file_path)
        prev_file_layout.addWidget(prev_browse_btn)
        prev_file_box.setLayout(prev_file_layout)
        right_panel.addWidget(prev_file_box)

        # SMS Replies Input
        sms_file_box = QGroupBox("SMS Replies")
        self._dynamic_groupboxes.append(sms_file_box)
        sms_file_layout = QHBoxLayout()
        self.sms_file_path = QLineEdit()
        self._dynamic_lineedits.append(self.sms_file_path)
        sms_browse_btn = QPushButton("Browse")
        sms_browse_btn.clicked.connect(lambda: self.browse_file("sms"))
        sms_file_layout.addWidget(self.sms_file_path)
        sms_file_layout.addWidget(sms_browse_btn)
        sms_file_box.setLayout(sms_file_layout)
        right_panel.addWidget(sms_file_box)

        # Email Replies Input
        # TODO: Email Replies widget is currently hidden - under development
        email_file_box = QGroupBox("Email Replies")
        self._dynamic_groupboxes.append(email_file_box)
        email_file_layout = QHBoxLayout()
        self.email_file_path = QLineEdit()
        self._dynamic_lineedits.append(self.email_file_path)
        email_browse_btn = QPushButton("Browse")
        email_browse_btn.clicked.connect(lambda: self.browse_file("email"))
        email_file_layout.addWidget(self.email_file_path)
        email_file_layout.addWidget(email_browse_btn)
        email_file_box.setLayout(email_file_layout)
        right_panel.addWidget(email_file_box)
        
        # Show the Email Replies widget (re-activated)
        email_file_box.setVisible(True)

        right_panel.addStretch()

        # --- Top layout: handlers left, right panel right ---
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(14)
        top_layout.addWidget(self.handlers_frame, 1)
        top_layout.addWidget(right_panel_widget, 1)
        content_layout.addWidget(top_widget)

        # Output file path
        output_layout = QHBoxLayout()
        output_layout.setSpacing(10)

        self.output_file_edit = QLineEdit()
        self._dynamic_lineedits.append(self.output_file_edit)
        browse_output_button = QPushButton("Browse")
        browse_output_button.clicked.connect(self.browse_output)
        output_layout.addWidget(QLabel("Output File Path:"))
        output_layout.addWidget(self.output_file_edit)
        output_layout.addWidget(browse_output_button)
        content_layout.addLayout(output_layout)

        # Protect Companies sheet checkbox (default: unchecked)
        self.protect_companies_checkbox = QCheckBox("Protect Companies sheet with password")
        self.protect_companies_checkbox.setChecked(False)
        self.protect_companies_checkbox.setToolTip(
            "When checked, the 'Companies' sheet in the output file will be\n"
            "password-protected (password: artadmin) to prevent accidental edits."
        )
        content_layout.addWidget(self.protect_companies_checkbox)

        # Process section
        process_layout = QHBoxLayout()
        process_layout.setContentsMargins(0, 0, 0, 0)
        
        # Process button with fixed width
        process_button = QPushButton("Process")
        process_button.setObjectName("Process")
        process_button.setFixedWidth(112)
        process_button.clicked.connect(self.process)
        process_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        
        # Progress bar with expanding policy and minimum width
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setMinimumWidth(300)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Add widgets to layout
        process_layout.addWidget(process_button)
        process_layout.addWidget(self.progress_bar)
        
        content_layout.addLayout(process_layout)

        # Log section
        log_label = QLabel("Log:")
        self._dynamic_labels.append((log_label, "section_dark"))
        content_layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(110)
        self.log_area.setMaximumHeight(180)
        self.log_area.setStyleSheet("")
        content_layout.addWidget(self.log_area)

        # Reset button
        self.reset_btn = QPushButton("Reset")
        self._dynamic_buttons.append((self.reset_btn, "secondary"))
        self.reset_btn.clicked.connect(self.reset_all)
        content_layout.addWidget(self.reset_btn)

        # Create scrollable content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content_widget)

        # Footer
        footer = QFrame()
        # Use theme colors instead of hardcoded light blue
        footer_bg = self.theme_manager.get_color('surface_hover')  # Use 'surface_hover' for subtle accent
        footer.setStyleSheet(f"background-color: {footer_bg}; border-radius: 12px;")
        footer_layout = QGridLayout(footer)
        footer_layout.setContentsMargins(16, 8, 16, 8)
        footer_layout.setColumnStretch(0, 0)
        footer_layout.setColumnStretch(1, 2)
        footer_layout.setColumnStretch(2, 1)

        # Left side of footer
        # Use theme colors for footer text
        footer_text_color = self.theme_manager.get_color('text_primary')
        link_color = self.theme_manager.get_color('link')
        left_label = QLabel(
            f'<span style="color:{footer_text_color};">Developed by: Ehab Elrify | Adam Maged <br>'
            f'Email: <a href="mailto:ehab.elrify@ibm.com" style="color:{link_color};">ehab.elrify@ibm.com</a> | '
            f'<a href="mailto:abdelrahman.maged@ibm.com" style="color:{link_color};">abdelrahman.maged@ibm.com</a><br>'
            'Assurance Resolution Team</span>'
        )
        left_label.setOpenExternalLinks(True)
        self._dynamic_labels.append((left_label, "footer"))

        # Center IBM logo
        ibm_logo_footer = QLabel("IBM")
        self._dynamic_labels.append((ibm_logo_footer, "ibm_footer"))
        ibm_logo_footer.setAlignment(Qt.AlignmentFlag(ALIGN.Center))
        #)
        #right_label.setOpenExternalLinks(True)
        #right_layout.addWidget(right_label)

        # Add all footer elements
        footer_layout.addWidget(left_label, 0, 0)
        footer_layout.addWidget(ibm_logo_footer, 0, 1)

        # Add all main sections to the main layout
        main_layout.addWidget(header)
        main_layout.addWidget(content_widget)
        main_layout.addWidget(footer)

        # Typography is applied in __init__ after UI creation
        return main_widget
    def create_top_bar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(50)
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Add Progress View button to the right
        progress_btn = QPushButton("Progress View")
        progress_btn.clicked.connect(self.show_progress)
        progress_btn.setFixedWidth(120)
        
        layout.addStretch()
        layout.addWidget(progress_btn)
        
        return top_bar

    def create_right_panel(self):
        right_panel = QWidget()
        layout = QVBoxLayout(right_panel)
        layout.setSpacing(12)

        # Files group box
        files_group = QGroupBox("Files")
        files_layout = QVBoxLayout()
        files_layout.setSpacing(15)

        # Create table for files
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(3)
        self.files_table.setRowCount(3)
        self.files_table.setHorizontalHeaderLabels(["File Type", "Selected File", "Action"])
        
        # Style the table
        self.files_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dde1e6;
                gridline-color: #f2f4f8;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f2f4f8;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        
        # Set up the table rows
        file_types = ["Raw File", "Previous File", "SMS Replies"]
        self.file_labels = {}
        
        for row, file_type in enumerate(file_types):
            # File type label with icon or color indicator
            type_item = QTableWidgetItem(file_type)
            type_item.setFlags(Qt.ItemFlag(FLAGS.Standard))
            self.files_table.setItem(row, 0, type_item)
            
            # File name label
            file_label = QLabel("No file selected")
            file_label.setStyleSheet("color: #525252;")
            self.file_labels[file_type] = file_label
            
            label_widget = QWidget()
            label_layout = QHBoxLayout(label_widget)
            label_layout.setContentsMargins(8, 0, 8, 0)
            label_layout.addWidget(file_label)
            label_layout.addStretch()
            self.files_table.setCellWidget(row, 1, label_widget)
            
            # Browse button with modern style
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(8, 0, 8, 0)
            
            browse_btn = QPushButton("Browse")
            browse_btn.setProperty("file_type", file_type.lower().replace(" ", "_"))
            browse_btn.clicked.connect(self.browse_file)
            browse_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0f62fe;
                    border-radius: 4px;
                    padding: 5px 15px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #0353e9;
                }
            """)
            
            action_layout.addWidget(browse_btn)
            action_layout.addStretch()
            self.files_table.setCellWidget(row, 2, action_widget)
        
        # Set column widths
        self.files_table.setColumnWidth(0, 120)  # File Type
        self.files_table.setColumnWidth(2, 100)  # Action
        header = self.files_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode(HEADER.Stretch))
        
        vert_header = self.files_table.verticalHeader()
        if vert_header:
            vert_header.setVisible(False)
        self.files_table.setSelectionMode(QTableWidget.NoSelection)
        self.files_table.setShowGrid(False)
        self.files_table.setAlternatingRowColors(True)
        
        files_layout.addWidget(self.files_table)
        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

        layout.addStretch()
        return right_panel

    def create_file_section(self):
        group = QGroupBox("Output")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Output file selection
        output_widget = QWidget()
        output_layout = QHBoxLayout(output_widget)
        output_layout.setContentsMargins(0, 0, 0, 0)

        self.output_path = QLineEdit()
        output_layout.addWidget(QLabel("Output Path:"))
        output_layout.addWidget(self.output_path)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_output)
        output_layout.addWidget(browse_btn)
        
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_all)
        output_layout.addWidget(reset_btn)
        
        layout.addWidget(output_widget)

        # Progress and Log section
        # Process button and progress bar in one row
        process_row = QWidget()
        process_layout = QHBoxLayout(process_row)
        process_layout.setContentsMargins(0, 0, 0, 0)
        
        process_btn = QPushButton("Process")
        process_btn.clicked.connect(self.process_files)
        process_btn.setMinimumWidth(120)
        process_btn.setStyleSheet("""
            QPushButton {
                background-color: #24a148;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1c8a3c;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumWidth(400)
        
        process_layout.addWidget(process_btn)
        process_layout.addWidget(self.progress_bar)
        process_layout.addStretch()
        
        layout.addWidget(process_row)

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(100)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #e0e0e0 !important;
                border: none;
                border-radius: 4px;
                padding: 8px;
                color: #161616;
            }
            QTextEdit:focus {
                background-color: #e0e0e0 !important;
            }
        """)
        layout.addWidget(self.log_area)

        group.setLayout(layout)
        return group

    def _create_processing_view(self):
        view = QWidget()
        layout = QVBoxLayout(view)
        
        # Handlers selection
        handlers_group = QWidget()
        handlers_layout = QVBoxLayout(handlers_group)
        handlers_layout.setSpacing(10)
        
        # Title for handlers
        handlers_title = QLabel("Select Handlers")
        handlers_title.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px;")
        handlers_layout.addWidget(handlers_title)
        
        # Checkbox container for handlers
        self.handler_widgets = {}
        checkbox_widget = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_widget)
        
        for handler in self.handlers:
            handler_row = QWidget()
            handler_layout = QHBoxLayout(handler_row)
            handler_layout.setContentsMargins(0, 0, 0, 0)
            
            checkbox = QCheckBox(handler)

            handler_layout.addWidget(checkbox)
            handler_layout.addStretch()

            self.handler_widgets[handler] = {'checkbox': checkbox}
            checkbox_layout.addWidget(handler_row)
        
        # Add new handler button
        add_handler_btn = QPushButton("Add Handler")
        add_handler_btn.clicked.connect(self._add_new_handler)
        checkbox_layout.addWidget(add_handler_btn)
        
        handlers_layout.addWidget(checkbox_widget)
        layout.addWidget(handlers_group)
        
        # File selection options
        files_group = QWidget()
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(10)
        
        # Title for files section
        files_title = QLabel("File Options")
        files_title.setStyleSheet("font-weight: bold; font-size: 16px; padding: 5px;")
        files_layout.addWidget(files_title)
        
        # Raw file selection
        raw_file_widget = QWidget()
        raw_file_layout = QHBoxLayout(raw_file_widget)
        
        self.raw_file_btn = QPushButton("Select Raw File")
        self.raw_file_btn.clicked.connect(lambda: self._select_files("raw"))
        self.raw_file_label = QLabel("No raw file selected")
        
        raw_file_layout.addWidget(self.raw_file_btn)
        raw_file_layout.addWidget(self.raw_file_label)
        raw_file_layout.addStretch()
        files_layout.addWidget(raw_file_widget)
        
        # Previous file selection
        prev_file_widget = QWidget()
        prev_file_layout = QHBoxLayout(prev_file_widget)
        
        self.prev_file_btn = QPushButton("Add Previous File")
        self.prev_file_btn.clicked.connect(lambda: self._select_files("previous"))
        self.prev_file_label = QLabel("No previous file selected")
        
        prev_file_layout.addWidget(self.prev_file_btn)
        prev_file_layout.addWidget(self.prev_file_label)
        prev_file_layout.addStretch()
        files_layout.addWidget(prev_file_widget)
        
        # SMS replies selection
        sms_file_widget = QWidget()
        sms_file_layout = QHBoxLayout(sms_file_widget)
        
        self.sms_file_btn = QPushButton("Add SMS Replies")
        self.sms_file_btn.clicked.connect(lambda: self._select_files("sms"))
        self.sms_file_label = QLabel("No SMS file selected")
        
        sms_file_layout.addWidget(self.sms_file_btn)
        sms_file_layout.addWidget(self.sms_file_label)
        sms_file_layout.addStretch()
        files_layout.addWidget(sms_file_widget)
        
        layout.addWidget(files_group)

        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["File Name", "Status", "Processing Time", "Actions"])
        layout.addWidget(self.results_table)

        return view



    def _select_files(self, file_type):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            f"Select {file_type.capitalize()} File",
            "",
            "All Files (*.*)"
        )
        if files:
            if file_type == "raw":
                self.raw_file_label.setText(files[0].split('/')[-1])
            elif file_type == "previous":
                self.prev_file_label.setText(files[0].split('/')[-1])
            elif file_type == "sms":
                self.sms_file_label.setText(files[0].split('/')[-1])
            elif file_type == "email":
                self.email_file = files[0]
            # TODO: Implement file processing logic

    def _add_new_handler(self):
        handler_name, ok = QInputDialog.getText(self, 'Add Handler', 'Enter handler name:')
        if ok and handler_name:
            # Add to handlers list
            self.handlers.append(handler_name)
            self.current_handlers.append(handler_name)
            
            # Create row widget
            handler_row = QWidget()
            row_layout = QHBoxLayout(handler_row)
            row_layout.setContentsMargins(5, 2, 5, 2)

            # Create checkbox for handler selection
            checkbox = QCheckBox()
            self.handler_vars[handler_name] = checkbox
            row_layout.addWidget(checkbox)

            # Add handler name label
            name_label = QLabel(handler_name)
            row_layout.addWidget(name_label)
            row_layout.addStretch()

            # (Half-day option removed)

            # Insert the row before the stretch item
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, handler_row)
            
            # Save the updated handlers list
            self.save_handlers()
            self.add_log(f"Handler '{handler_name}' added and saved.")

    def _remove_handler(self):
        # Find selected handlers to remove
        handlers_to_remove = [name for name, cb in self.handler_vars.items() if cb.isChecked()]
        
        if not handlers_to_remove:
            QMessageBox.warning(self, "Warning", "Please select at least one handler to remove.")
            return
        
        for name in handlers_to_remove:
            # Remove from lists and dictionaries
            if name in self.handlers:
                self.handlers.remove(name)
            if name in self.current_handlers:
                self.current_handlers.remove(name)
            
            # Clean up UI elements
            for i in range(self.scroll_layout.count()):
                item = self.scroll_layout.itemAt(i)
                if not item:
                    continue
                widget = item.widget()
                if not widget:
                    continue
                label = widget.findChild(QLabel)
                if label and label.text() == name:
                    item_widget = self.scroll_layout.takeAt(i)
                    if item_widget:
                        widget = item_widget.widget()
                        if widget:
                            widget.deleteLater()
                    break
            
            # Clean up handler dictionaries
            if name in self.handler_vars:
                del self.handler_vars[name]
            
            self.add_log(f"Handler '{name}' removed.")
        
        # Save the updated handlers list
        self.save_handlers()
        self.add_log("Handler changes saved.")

    def repopulate_handlers(self, handler_list):
        # Clear existing items
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

        # Clear dictionaries
        self.handler_vars.clear()

        # Add new handlers
        for handler in handler_list:
            # Create row widget
            handler_row = QWidget()
            row_layout = QHBoxLayout(handler_row)
            row_layout.setContentsMargins(5, 2, 5, 2)

            # Create checkbox for handler selection
            checkbox = QCheckBox()
            self.handler_vars[handler] = checkbox
            row_layout.addWidget(checkbox)

            # Add handler name label
            name_label = QLabel(handler)
            row_layout.addWidget(name_label)
            row_layout.addStretch()

            # (Half-day option removed)

            # Add the row to the scroll area
            self.scroll_layout.addWidget(handler_row)

        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #d0d0d0;")
        self.scroll_layout.addWidget(separator)

        # Add Chat Agent section
        # Chat Agent checkbox
        chat_agent_row = QWidget()
        chat_agent_layout = QHBoxLayout(chat_agent_row)
        chat_agent_layout.setContentsMargins(5, 2, 5, 2)
        
        self.chat_agent_checkbox = QCheckBox()
        self.chat_agent_checkbox.stateChanged.connect(self._on_chat_agent_toggled)
        self.handler_vars["Chat Agent"] = self.chat_agent_checkbox
        chat_agent_layout.addWidget(self.chat_agent_checkbox)
        
        chat_agent_label = QLabel("Chat Agent")
        chat_agent_label.setStyleSheet("font-weight: bold;")
        chat_agent_layout.addWidget(chat_agent_label)
        chat_agent_layout.addStretch()
        
        self.scroll_layout.addWidget(chat_agent_row)
        
        # ── Chat Agent name input container (hidden until checkbox is checked) ──
        supporter_container = QWidget()
        container_layout = QVBoxLayout(supporter_container)
        container_layout.setContentsMargins(25, 2, 5, 2)
        container_layout.setSpacing(4)

        # Normal mode: single QLineEdit
        self._chat_agent_single_row = QWidget()
        single_layout = QHBoxLayout(self._chat_agent_single_row)
        single_layout.setContentsMargins(0, 0, 0, 0)
        supporter_label = QLabel("Supporter Name:")
        supporter_label.setStyleSheet("font-size: 12px; color: #525252;")
        single_layout.addWidget(supporter_label)
        self.chat_agent_input = QLineEdit()
        self.chat_agent_input.setPlaceholderText("Enter supporter name…")
        self.chat_agent_input.setMaximumWidth(160)
        single_layout.addWidget(self.chat_agent_input)
        single_layout.addStretch()
        container_layout.addWidget(self._chat_agent_single_row)

        # DEV MODE: multi-name QTextEdit
        self._chat_agent_dev_row = QWidget()
        dev_layout = QVBoxLayout(self._chat_agent_dev_row)
        dev_layout.setContentsMargins(0, 0, 0, 0)
        dev_layout.setSpacing(3)
        dev_header = QLabel("🛠 DEV MODE — Agent Sheet Names (one per line):")
        dev_header.setStyleSheet("font-size: 12px; font-weight: bold; color: #da1e28;")
        dev_layout.addWidget(dev_header)
        self.chat_agent_input_multi = QTextEdit()
        self.chat_agent_input_multi.setPlaceholderText(
            "Enter one agent/sheet name per line, e.g.:\nAdam\nEhab\nTeama"
        )
        self.chat_agent_input_multi.setFixedHeight(76)
        self.chat_agent_input_multi.setMaximumWidth(220)
        dev_layout.addWidget(self.chat_agent_input_multi)
        dev_hint = QLabel("Each name → its own output sheet.")
        dev_hint.setStyleSheet("font-size: 11px; color: #6f6f6f;")
        dev_layout.addWidget(dev_hint)
        container_layout.addWidget(self._chat_agent_dev_row)

        # Start both sub-rows hidden; _on_chat_agent_toggled shows the right one
        self._chat_agent_single_row.setVisible(False)
        self._chat_agent_dev_row.setVisible(False)
        supporter_container.setVisible(False)
        self._chat_agent_container = supporter_container

        self.scroll_layout.addWidget(supporter_container)

        # Add a stretch at the end to keep items at the top
        self.scroll_layout.addStretch()

    def toggle_all_handlers(self):
        checked = self.select_all_btn.isChecked()
        for checkbox in self.handler_vars.values():
            checkbox.setChecked(checked)

    def filter_handlers(self, text):
        if not self.scroll_layout:
            return
        text = text.lower()
        for i in range(self.scroll_layout.count() - 1):  # -1 to skip the stretch item
            layout_item = self.scroll_layout.itemAt(i)
            if not layout_item:
                continue
            widget = layout_item.widget()
            if not widget:
                continue
            label = widget.findChild(QLabel)
            if not label:
                continue
            handler_name = label.text()
            widget.setVisible(text in handler_name.lower())

    def _on_dev_mode_changed(self, enabled: bool):
        """React live when DEV MODE is toggled from Settings.
        Swaps the visible Chat Agent input between the single QLineEdit (normal)
        and the multi-line QTextEdit (DEV MODE).  Only affects visibility — the
        container itself stays shown/hidden based on the checkbox state.
        """
        is_checked = (self.chat_agent_checkbox is not None and
                      self.chat_agent_checkbox.isChecked())
        if self._chat_agent_single_row:
            self._chat_agent_single_row.setVisible(is_checked and not enabled)
        if self._chat_agent_dev_row:
            self._chat_agent_dev_row.setVisible(is_checked and enabled)
        # Clear stale input on mode switch
        if self.chat_agent_input:
            self.chat_agent_input.clear()
        if self.chat_agent_input_multi:
            self.chat_agent_input_multi.clear()

    def _on_chat_agent_toggled(self, state):
        """Handle Chat Agent checkbox toggle.
        Shows the appropriate input sub-widget depending on current DEV MODE.
        """
        is_checked = bool(state)
        is_dev = self.settings_bus.dev_mode

        if hasattr(self, '_chat_agent_container') and self._chat_agent_container:
            self._chat_agent_container.setVisible(is_checked)
        if self._chat_agent_single_row:
            self._chat_agent_single_row.setVisible(is_checked and not is_dev)
        if self._chat_agent_dev_row:
            self._chat_agent_dev_row.setVisible(is_checked and is_dev)

        if not is_checked:
            if self.chat_agent_input:
                self.chat_agent_input.clear()
            if self.chat_agent_input_multi:
                self.chat_agent_input_multi.clear()

    def get_selected_handlers(self):
        """Get list of selected handlers (excluding Chat Agent)
        Returns:
            list: List of selected handler names (without half-day status)
        """
        selected = []
        for name, cb in self.handler_vars.items():
            if name != "Chat Agent" and cb.isChecked():
                selected.append(name)
        return selected

    def get_chat_agent_info(self):
        """Get Chat Agent info if selected.

        Normal mode → {'enabled': True, 'supporter_name': str,
                        'supporter_names': [str], 'dev_mode': False}
        DEV MODE    → {'enabled': True, 'supporter_name': str (first),
                        'supporter_names': [str, …], 'dev_mode': True}

        Returns None when checkbox is unchecked or no name(s) entered.
        """
        if not self.chat_agent_checkbox or not self.chat_agent_checkbox.isChecked():
            return None

        is_dev = self.settings_bus.dev_mode

        if is_dev:
            raw = self.chat_agent_input_multi.toPlainText() if self.chat_agent_input_multi else ""
            names = [n.strip() for n in raw.splitlines() if n.strip()]
            if not names:
                return None
            return {
                'enabled': True,
                'supporter_name': names[0],   # first name for backward-compat
                'supporter_names': names,
                'dev_mode': True,
            }
        else:
            name = self.chat_agent_input.text().strip() if self.chat_agent_input else ""
            if not name:
                return None
            return {
                'enabled': True,
                'supporter_name': name,
                'supporter_names': [name],
                'dev_mode': False,
            }

    def browse_input(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select Input File",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        if file_name:
            self.input_file_path.setText(file_name)

    def browse_output(self):
        # Get current date in MM-DD format
        current_date = datetime.now().strftime("%m-%d")
        suggested_name = f"Active Cases PA {current_date}.xlsx"
        
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Select Output File",
            suggested_name,
            "Excel Files (*.xlsx);;All Files (*.*)"
        )
        if file_name:
            self.output_file_edit.setText(file_name)
    
    def browse_file(self, file_type):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {file_type.title()} File",
            "",
            "Excel Files (*.xlsx *.xls);;All Files (*.*)"
        )
        
        if file_name:
            if file_type == "raw":
                self.raw_file_path.setText(file_name)
                self.raw_file = file_name
            elif file_type == "previous":
                self.prev_file_path.setText(file_name)
                self.previous_file = file_name
            elif file_type == "sms":
                self.sms_file_path.setText(file_name)
                self.sms_file = file_name
            elif file_type == "email":
                self.email_file_path.setText(file_name)
                self.email_file = file_name

    def reset_all(self):
        # Reset file selections
        for label in self.file_labels.values():
            label.setText("No file selected")
        
        self.raw_file = None
        self.previous_file = None
        self.sms_file = None
        self.email_file = None # Reset email file
        
        # Reset output path
        self.output_file_edit.clear()
        
        # Reset file paths
        self.raw_file_path.clear()
        self.prev_file_path.clear()
        self.sms_file_path.clear()
        self.email_file_path.clear() # Clear email path
        
        # Reset handlers
        for checkbox in self.handler_vars.values():
            checkbox.setChecked(False)
        # (Half-day options removed)
        
        # Clear log
        self.log_area.clear()
        
        # Reset progress bar to 0% but keep it visible
        self.progress_bar.setValue(0)

    def add_log(self, message):
        """Add a message to the log window with smart filtering - only show important steps and errors"""
        if hasattr(self, 'log_area') and self.log_area is not None:
            # Filter messages for the main window - only show important ones
            if self._should_show_in_main_window(message):
                self.log_area.append(message)
                # Ensure the new text is visible by scrolling to bottom
                scroll_bar = self.log_area.verticalScrollBar()
                if scroll_bar:
                    scroll_bar.setValue(scroll_bar.maximum())
    
    def _should_show_in_main_window(self, message):
        """Determine if a message should be shown in the main window based on importance"""
        message_lower = message.lower()
        
        # Always show these important messages
        important_keywords = [
            '=== starting file processing ===',
            '=== starting final processing ===',
            'processing completed successfully',
            'processing failed',
            'error',
            'warning',
            'critical',
            'failed',
            'exception',
            'validation failed',
            'file validation successful',
            'final processing completed successfully',
            'error during final processing',
            'error adding validation dropdowns',
            'error creating',
            'error in final processing',
            'error during processing',
            'error opening progress view',
            'error updating database',
            'error saving handlers',
            'error loading handlers'
        ]
        
        # Check if message contains important keywords
        for keyword in important_keywords:
            if keyword in message_lower:
                return True
        
        # Show step progress messages (but not too verbose)
        step_keywords = [
            'step',
            'phase',
            'stage',
            'progress',
            'processing',
            'creating',
            'adding',
            'validating',
            'filtering',
            'merging',
            'saving',
            'loading'
        ]
        
        # Only show step messages if they're not too verbose
        step_count = sum(1 for keyword in step_keywords if keyword in message_lower)
        if step_count > 0 and len(message) < 100:  # Short step messages
            return True
        
        # Show summary statistics
        if any(keyword in message_lower for keyword in ['count:', 'total:', 'found', 'processed', 'created']):
            return True
        
        # Don't show verbose debug messages, detailed processing info, or repetitive status updates
        verbose_keywords = [
            'debug',
            'traceback',
            'sample',
            'checking',
            'verifying',
            'reading',
            'writing',
            'formatting',
            'adjusting',
            'auto-adjusting'
        ]
        
        for keyword in verbose_keywords:
            if keyword in message_lower:
                return False
        
        # Don't show very long messages (likely detailed logs)
        if len(message) > 150:
            return False
        
        return False

    def update_log(self, message):
        """Update log from external sources (like file processor)"""
        self.add_log(message)

    def process_files(self):
        # TODO: Implement file processing logic
        pass

    def show_progress(self):
        # Show the progress dashboard (ProgressView)
        # Progress view has been removed from this build. Keep the method for API compatibility
        # but do not attempt to import or display a separate progress window.
        self.add_log("Progress View feature has been removed in this build.")

    def apply_typography(self):
        """Apply typography to all widgets using modern typography system."""
        # Reapply stylesheet with current font sizes
        self.setStyleSheet(self.ibm_stylesheet())
        
        # Update dynamic labels with appropriate fonts
        for widget, role in self._dynamic_labels:
            if role == "title_blue":
                widget.setFont(self.get_font('h2', QFont.DemiBold))
                text_color = self.theme_manager.get_color('primary')
                widget.setStyleSheet(f"color: {text_color}; font-weight: 600;")
            elif role == "version_light":
                widget.setFont(self.get_font('caption'))
                widget.setStyleSheet("color: white; margin-left: 10px;")
            elif role == "section_dark":
                widget.setFont(self.get_font('label', QFont.DemiBold))
                text_color = self.theme_manager.get_color('text_primary')
                widget.setStyleSheet(f"font-weight: 600; color: {text_color};")
            elif role == "footer":
                widget.setFont(self.get_font('caption'))
                text_color = self.theme_manager.get_color('text_primary')
                widget.setStyleSheet(f"color: {text_color};")
            elif role == "ibm_footer":
                widget.setFont(self.get_font('h3', QFont.Bold))
                widget.setStyleSheet("color: #000000; font-weight: bold;")
        
        # Update dynamic buttons
        primary = self.theme_manager.get_color('primary')
        hover = self.theme_manager.get_color('primary_hover')
        for widget, role in self._dynamic_buttons:
            widget.setFont(self.get_font('button', QFont.DemiBold))
            if role == "header":
                widget.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {primary};
                        color: white;
                        border-radius: 8px;
                        padding: 8px 16px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: {hover};
                    }}
                """)
            elif role == "secondary":
                layer = self.theme_manager.get_color('surface')
                layer_hover = self.theme_manager.get_color('surface_hover')
                text = self.theme_manager.get_color('text_primary')
                widget.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {layer};
                        color: {text};
                        font-weight: 600;
                        border: none;
                        border-radius: 8px;
                        padding: 8px 16px;
                    }}
                    QPushButton:hover {{
                        background-color: {layer_hover};
                    }}
                """)
        
        # Update groupboxes
        border = self.theme_manager.get_color('border')
        field_bg = self.theme_manager.get_color('surface')
        for widget in self._dynamic_groupboxes:
            widget.setFont(self.get_font('label', QFont.DemiBold))
            widget.setStyleSheet(f"""
                QGroupBox {{
                    border: 1px solid {border};
                    border-radius: 12px;
                    margin-top: 10px;
                    background-color: {field_bg};
                    font-weight: 600;
                    color: {primary};
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 2px 8px 2px 8px;
                    color: {primary};
                }}
            """)
        
        # Update line edits
        for widget in self._dynamic_lineedits:
            widget.setFont(self.get_font('input'))
        
        # Update log area
        self.log_area.setFont(self.get_font('body'))
    
    def _on_theme_changed(self, theme_mode: str):
        """Handle theme changes from settings."""
        # Reapply stylesheet with new theme colors
        self.setStyleSheet(self.ibm_stylesheet())
        
        # Reapply typography to update all widget styles
        self.apply_typography()
        
        # Update status message
        self.add_log(f"Theme changed to {theme_mode} mode")
    
    def _on_font_changed(self, font_size: int):
        """Handle font size changes from settings."""
        # Reapply stylesheet with new font sizes
        self.setStyleSheet(self.ibm_stylesheet())
        
        # Reapply typography to update all widget fonts
        self.apply_typography()
        
        # Update status message
        self.add_log(f"Font size changed to {font_size}px")

    def resizeEvent(self, a0: Optional[QResizeEvent]) -> None:
        """Handle window resize events."""
        # Font scaling is now handled by typography system via settings
        # No need for dynamic resize-based font scaling
        super().resizeEvent(a0)
    
    def _setup_shortcuts(self):
        """Setup keyboard shortcuts using ShortcutManager."""
        from ui.keyboard_shortcuts import ShortcutManager, ShortcutDefinition, ShortcutCategory
        
        self.shortcut_manager = ShortcutManager(self)
        
        # Register tool-specific shortcuts
        self.shortcut_manager.register_shortcut(
            "assigner_open_file",
            ShortcutDefinition(
                key_sequence="Ctrl+O",
                description="Open file",
                category=ShortcutCategory.FILE,
                action=self.browse_file
            )
        )
        
        self.shortcut_manager.register_shortcut(
            "assigner_assign_cases",
            ShortcutDefinition(
                key_sequence="Ctrl+A",
                description="Assign cases",
                category=ShortcutCategory.TOOL_SPECIFIC,
                action=self.process
            )
        )
        
        self.shortcut_manager.register_shortcut(
            "assigner_reset",
            ShortcutDefinition(
                key_sequence="Ctrl+R",
                description="Reset all",
                category=ShortcutCategory.EDIT,
                action=self.reset_all
            )
        )
        
        self.shortcut_manager.register_shortcut(
            "assigner_close",
            ShortcutDefinition(
                key_sequence="Ctrl+W",
                description="Close window",
                category=ShortcutCategory.GLOBAL,
                action=self.close
            )
        )
        
        self.shortcut_manager.register_shortcut(
            "assigner_settings",
            ShortcutDefinition(
                key_sequence="Ctrl+,",
                description="Open settings",
                category=ShortcutCategory.GLOBAL,
                action=self._open_settings
            )
        )
        
        self.shortcut_manager.register_shortcut(
            "assigner_help",
            ShortcutDefinition(
                key_sequence="F1",
                description="Show keyboard shortcuts",
                category=ShortcutCategory.GLOBAL,
                action=self._show_help
            )
        )
        
        self.shortcut_manager.register_shortcut(
            "assigner_main_menu",
            ShortcutDefinition(
                key_sequence="Ctrl+M",
                description="Return to main menu",
                category=ShortcutCategory.NAVIGATION,
                action=self.open_main_menu
            )
        )
    
    def _open_settings(self):
        """Open settings dialog."""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec_()
    
    def _show_help(self):
        """Show help dialog with keyboard shortcuts."""
        self.shortcut_manager.show_help_dialog()

    def open_main_menu(self):
        """Open the unified v2 main menu. Uses a local import to avoid circular imports."""
        try:
            from ui.main_menu import V2MainMenu
            self.menu_window = V2MainMenu()
            self.menu_window.show()
            # Close this window to mimic the menu->assigner flow
            self.close()
        except Exception as e:
            # Log and show a warning but do not change any backend logic
            self.add_log(f"Error opening Main Menu: {e}")
            try:
                QMessageBox.warning(self, "Error", f"Failed to open Main Menu: {e}")
            except Exception:
                pass

    def output_path_changed(self):
        # This method gets called when the output file path changes
        pass

    def _validate_inputs(self) -> bool:
        """Validate inputs with Toast feedback."""
        from ui.components_v2.feedback import Toast

        # Check if handlers are selected
        selected_handlers = self.get_selected_handlers()
        if not selected_handlers:
            Toast.error(self, "Please select at least one handler")
            return False

        # If Chat Agent is checked, require at least one name
        if self.chat_agent_checkbox and self.chat_agent_checkbox.isChecked():
            is_dev = self.settings_bus.dev_mode
            if is_dev:
                raw = self.chat_agent_input_multi.toPlainText() if self.chat_agent_input_multi else ""
                names = [n.strip() for n in raw.splitlines() if n.strip()]
                if not names:
                    Toast.error(
                        self,
                        "DEV MODE: enter at least one agent/sheet name in the Chat Agent box"
                    )
                    return False
            else:
                name = self.chat_agent_input.text().strip() if self.chat_agent_input else ""
                if not name:
                    Toast.error(self, "Chat Agent: please enter the supporter name")
                    return False

        # Check if raw file is selected
        if not self.raw_file_path.text():
            Toast.error(self, "Please select a raw file")
            return False

        # Check if raw file exists
        from pathlib import Path
        raw_file = Path(self.raw_file_path.text())
        if not raw_file.exists():
            Toast.error(self, "Selected raw file does not exist")
            return False

        # Check if output path is specified
        if not self.output_file_edit.text():
            Toast.error(self, "Please specify an output file path")
            return False

        # All validations passed
        Toast.success(self, "Inputs validated successfully")
        return True

    def process(self):
        """Process the files with the selected handlers (now threaded)"""
        # Validate inputs with Toast feedback
        if not self._validate_inputs():
            return
        
        # Get selected handlers after validation
        selected_handlers = self.get_selected_handlers()
        
        # Disable process button to prevent re-entry
        self.findChild(QPushButton, "Process").setEnabled(False)
        self.progress_bar.setValue(0)
        self.log_area.clear()
        # Set up worker and thread
        self.worker_thread = QThread()
        
        # Get Chat Agent info if selected
        chat_agent_info = self.get_chat_agent_info()
        
        protect_companies = (
            self.protect_companies_checkbox.isChecked()
            if self.protect_companies_checkbox else False
        )

        self.worker = FileProcessingWorker(
            self.raw_file_path.text(),
            self.prev_file_path.text() if self.prev_file_path.text() else None,
            self.sms_file_path.text() if self.sms_file_path.text() else None,
            self.email_file_path.text() if self.email_file_path.text() else None,
            self.output_file_edit.text(),
            selected_handlers,
            chat_agent_info,
            protect_companies=protect_companies
        )
        self.worker.moveToThread(self.worker_thread)
        self.worker.log_signal.connect(self.add_log)
    # Progress-related UI updates removed per build requirements.
    # Worker will continue to emit progress signals, but the main UI will not display them.
        self.worker.finished.connect(self.on_processing_finished)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_processing_finished(self, success, message):
        self.findChild(QPushButton, "Process").setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.add_log("\nProcessing completed successfully!")
            self.add_log(f"Output saved to: {self.output_file_edit.text()}")
            # Database update feature removed: skipping previous-file/database update step.
            self.add_log("Database update skipped (feature removed in this build).")
            # --- Enhanced popup with Open Sheet option ---
            try:
                from PyQt5.QtCore import QUrl
                from PyQt5.QtGui import QDesktopServices
                
                output_path = self.output_file_edit.text()
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Success")
                msg_box.setText("Files processed successfully!")
                ok_btn = msg_box.addButton(QMessageBox.Ok)
                open_btn = msg_box.addButton("Open Sheet", QMessageBox.ActionRole)
                msg_box.exec_()
                if msg_box.clickedButton() == open_btn:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
            except ImportError as e:
                self.add_log(f"Error importing QDesktopServices: {str(e)}")
                # Fallback to simple message box
                QMessageBox.information(self, "Success", "Files processed successfully!")
        else:
            self.add_log("\nProcessing failed")
            QMessageBox.warning(self, "Error", f"File processing failed: {message}")
    
    def save_handlers(self):
        """Save handlers to a JSON file"""
        handlers_data = {
            "handlers": self.handlers,
            "current_handlers": self.current_handlers
        }
        try:
            with open('handlers_cache.json', 'w') as f:
                json.dump(handlers_data, f)
        except Exception as e:
            self.add_log(f"Error saving handlers: {str(e)}")

    def load_handlers(self):
        """Load handlers from JSON file"""
        try:
            with open('handlers_cache.json', 'r') as f:
                handlers_data = json.load(f)
                # Load handlers from saved file
                self.handlers = handlers_data.get('handlers', ["Adam", "Ehab", "Teama", "Ibrahim", "Moamen"])
                self.current_handlers = handlers_data.get('current_handlers', self.handlers.copy())
        except FileNotFoundError:
            # If file doesn't exist, use default handlers
            self.handlers = ["Adam", "Ehab", "Teama", "Ibrahim", "Moamen"]
            self.current_handlers = self.handlers.copy()
            self.save_handlers()
        except Exception as e:
            self.add_log(f"Error loading handlers: {str(e)}")
            # Use default handlers if there's an error
            self.handlers = ["Adam", "Ehab", "Teama", "Ibrahim", "Moamen"]
            self.current_handlers = self.handlers.copy()
            self.save_handlers()

def main():
    import os
    from utils.crash_handler import install_crash_handler, enable_qt_sigint_heartbeat
    install_crash_handler()

    app = QApplication(sys.argv)
    enable_qt_sigint_heartbeat(app)

    window = MainWindow()
    window.show()
    app.exec_()

    # Window closed — exit immediately so worker threads don't keep the
    # process alive in the background / terminal.
    os._exit(0)

if __name__ == "__main__":
    main()
