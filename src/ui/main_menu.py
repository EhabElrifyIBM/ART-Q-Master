from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QHBoxLayout, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
import os
import sys
import subprocess

# Import the new MainWindow (Assigner) from main_window_assigner
from Assigner.main_window_assigner import MainWindow


class MainMenu(QMainWindow):
    """Main application menu with 4 buttons:
    1) ART Q Assigner -> opens the existing MainWindow
    2) PowerBi Dashboard -> placeholder (TODO)
    3) Email Merger -> placeholder (TODO)
    4) Archiver -> placeholder (TODO)
    5) ART Q Control -> placeholder (TODO)

    This file only provides the UI and wiring for the menu. It does not change
    any backend logic or behavior of the existing app.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ART Q Master - Main Menu")
        # Resolve icon path
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            icon_path = os.path.join(project_root, 'assets', 'ibm_logo.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
            
        self.setGeometry(200, 200, 600, 500) # Increased height for footer

        # Use a central widget with vertical layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(18)

        # Title label
        title = QLabel("ART Q Master")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: 600; color: #0f62fe;")
        layout.addWidget(title)

        subtitle = QLabel("Select an action below")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 15px; color: #161616;")
        layout.addWidget(subtitle)

        # Buttons area
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setSpacing(12)

        # Shared button style to match existing app
        btn_style = """
        QPushButton {
            background-color: #0f62fe;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 14px;
            font-weight: bold;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #0353e9;
        }
        """

        self.assigner_btn = QPushButton("ART Q Assigner")
        self.assigner_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.assigner_btn.setStyleSheet(btn_style)
        self.assigner_btn.clicked.connect(self.open_assigner)
        btn_layout.addWidget(self.assigner_btn)

        self.powerbi_btn = QPushButton("PowerBi Dashboard")
        self.powerbi_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.powerbi_btn.setStyleSheet(btn_style)
        self.powerbi_btn.clicked.connect(self.powerbi_placeholder)
        btn_layout.addWidget(self.powerbi_btn)

        self.email_merge_btn = QPushButton("Email Merger")
        self.email_merge_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.email_merge_btn.setStyleSheet(btn_style)
        self.email_merge_btn.clicked.connect(self.emailmerge_placeholder)
        btn_layout.addWidget(self.email_merge_btn)

        self.archiver_btn = QPushButton("Archiver")
        self.archiver_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.archiver_btn.setStyleSheet(btn_style)
        self.archiver_btn.clicked.connect(self.archiver_placeholder)
        btn_layout.addWidget(self.archiver_btn)
       
        self.q_control_btn = QPushButton("ART Q Control")
        self.q_control_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.q_control_btn.setStyleSheet(btn_style)
        self.q_control_btn.clicked.connect(self.q_control_placeholder)
        btn_layout.addWidget(self.q_control_btn)

        self.reach_rate_btn = QPushButton("Reach Rate Calculator")
        self.reach_rate_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.reach_rate_btn.setStyleSheet(btn_style)
        self.reach_rate_btn.clicked.connect(self.open_reach_rate_calculator)
        btn_layout.addWidget(self.reach_rate_btn)
        layout.addWidget(btn_container)

        # Footer
        footer_label = QLabel(
            '<span style="color:#161616; font-size: 15px;">Developed by: Ehab Elrify | Adam Maged <br>'
            'Email: <a href="mailto:ehab.elrify@ibm.com" style="color:#0f62fe;">ehab.elrify@ibm.com</a> | '
            '<a href="mailto:abdelrahman.maged@ibm.com" style="color:#0f62fe;">abdelrahman.maged@ibm.com</a><br>'
            'Assurance Resolution Team</span>'
        )
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setOpenExternalLinks(True)
        footer_label.setStyleSheet("padding-top: 20px;")
        layout.addWidget(footer_label)

        # Keep appearance consistent with the main app; lightweight stylesheet
        self.setStyleSheet(self.ibm_stylesheet())

    def ibm_stylesheet(self):
        # Small subset of styles copied from MainWindow to keep consistent look
        return """
            QWidget {
                background-color: #f4f4f4;
                color: #161616;
                font-family: 'IBM Plex Sans', Arial, sans-serif;
                font-size: 15px;
            }
            QPushButton {
                font-family: 'IBM Plex Sans', Arial, sans-serif;
            }
        """

    def open_assigner(self):
        # Open the existing MainWindow (Assigner). Do not change any backend logic.
        try:
            self.assigner_window = MainWindow()
            self.assigner_window.show()
            # Close the menu window to keep behavior consistent with launching main app
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Assigner: {e}")

    def powerbi_placeholder(self):
        # TODO: Implement later
        QMessageBox.information(self, "TODO", "PowerBi Dashboard is not implemented yet. # TODO: Implement later")

    def emailmerge_placeholder(self):
        try:
            if getattr(sys, 'frozen', False):
                # Running as frozen exe
                subprocess.Popen([sys.executable, 'merger'])
                self.close()
            else:
                # Running from source
                current_dir = os.path.dirname(os.path.abspath(__file__))
                # src/ui -> src
                src_dir = os.path.dirname(current_dir)
                main_script = os.path.join(src_dir, 'main.py')
                
                if os.path.exists(main_script):
                    subprocess.Popen([sys.executable, main_script, 'merger'])
                    self.close()
                else:
                    QMessageBox.critical(self, "Error", f"Dispatcher script not found: {main_script}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch Email Merger: {e}")

    def archiver_placeholder(self):
        try:
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable, 'archiver'])
                self.close()
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_dir = os.path.dirname(current_dir)
                main_script = os.path.join(src_dir, 'main.py')
                
                if os.path.exists(main_script):
                    subprocess.Popen([sys.executable, main_script, 'archiver'])
                    self.close()
                else:
                    QMessageBox.critical(self, "Error", f"Dispatcher script not found: {main_script}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch Archiver: {e}")

    def q_control_placeholder(self):
        try:
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable, 'qcontrol'])
                self.close()
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_dir = os.path.dirname(current_dir)
                main_script = os.path.join(src_dir, 'main.py')
                
                if os.path.exists(main_script):
                    subprocess.Popen([sys.executable, main_script, 'qcontrol'])
                    self.close()
                else:
                    QMessageBox.critical(self, "Error", f"Dispatcher script not found: {main_script}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch ART Q Control: {e}")

    def open_reach_rate_calculator(self):
        try:
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable, 'reachrate'])
                self.close()
            else:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_dir = os.path.dirname(current_dir)
                main_script = os.path.join(src_dir, 'main.py')

                if os.path.exists(main_script):
                    subprocess.Popen([sys.executable, main_script, 'reachrate'])
                    self.close()
                else:
                    QMessageBox.critical(self, "Error", f"Dispatcher script not found: {main_script}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch Reach Rate Calculator: {e}")


def main_menu_entry():
    # Small helper to start the menu when invoked directly
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    w = MainMenu()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main_menu_entry()
