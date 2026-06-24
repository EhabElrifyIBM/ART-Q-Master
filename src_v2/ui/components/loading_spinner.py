# ============================================================================
# loading_spinner.py - Loading Spinner Component
# ============================================================================
# Phase 3.3: UI/UX Enhancement
# 
# A reusable loading spinner component that displays during long operations
# - Animated spinner with message
# - Non-blocking (can be used in threads/tasks)
# - Professional styling
# - Context manager support for automatic cleanup
# ============================================================================

import sys
import time
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap, QFont


class LoadingSpinner(QDialog):
    """
    Non-modal loading spinner dialog for displaying during long operations.
    
    Phase 3.3: Provides visual feedback to users during:
    - Cache loading
    - CRM navigation
    - Excel file reading
    - API calls
    
    Usage:
        spinner = LoadingSpinner(message="Loading cases...")
        spinner.show()
        # Do long operation
        spinner.close()
    
    Or with context manager:
        with LoadingSpinner(message="Processing...") as spinner:
            # Long operation here
            time.sleep(2)
    """
    
    def __init__(self, message="Loading...", title="Processing", parent=None):
        """
        Initialize the loading spinner.
        
        Args:
            message (str): Message to display below spinner
            title (str): Window title
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 200)
        self.setModal(False)  # Non-modal so user can interact
        self.setStyleSheet("QDialog { background-color: white; }")
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spinner animation
        self.spinner_label = QLabel()
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setFixedSize(60, 60)
        layout.addStretch()
        layout.addWidget(self.spinner_label, alignment=Qt.AlignCenter)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        message_font = QFont()
        message_font.setPointSize(12)
        self.message_label.setFont(message_font)
        self.message_label.setStyleSheet("color: #333333; font-weight: bold;")
        layout.addWidget(self.message_label)
        
        layout.addStretch()
        
        # Animation state
        self.spinner_frame = 0
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_colors = [
            "#0f62fe", "#0353e9", "#0242d3", "#0333bd",
            "#0242a7", "#015291", "#00427b", "#003265"
        ]
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate_spinner)
        self.timer.start(80)  # ~80ms per frame = smooth animation
    
    def _animate_spinner(self):
        """Update spinner animation frame."""
        frame = self.spinner_frames[self.spinner_frame % len(self.spinner_frames)]
        color = self.spinner_colors[self.spinner_frame % len(self.spinner_colors)]
        
        # Create animated text with color
        self.spinner_label.setText(frame)
        self.spinner_label.setStyleSheet(f"color: {color}; font-size: 48px; font-weight: bold;")
        
        self.spinner_frame += 1
    
    def set_message(self, message):
        """Update the message during loading."""
        self.message_label.setText(message)
    
    def closeEvent(self, event):
        """Stop animation when closing."""
        self.timer.stop()
        super().closeEvent(event)
    
    def __enter__(self):
        """Context manager entry."""
        self.show()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class AsyncSpinner(QDialog):
    """
    Async-aware loading spinner that runs code in background thread.
    
    Phase 3.3: For use when you need to run long-running operations
    without blocking the UI.
    
    Usage:
        def long_operation():
            # Do work here
            time.sleep(2)
            return "done"
        
        spinner = AsyncSpinner(long_operation, message="Processing...")
        result = spinner.show_and_wait()
    """
    
    # Signal for when task completes
    task_complete = pyqtSignal(object)
    task_error = pyqtSignal(Exception)
    
    def __init__(self, task_func, message="Processing...", title="Working", parent=None):
        """
        Initialize async spinner.
        
        Args:
            task_func (callable): Function to run in background
            message (str): Display message
            title (str): Window title
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(300, 200)
        self.setModal(True)
        self.setStyleSheet("QDialog { background-color: white; }")
        
        self.task_func = task_func
        self.result = None
        self.error = None
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spinner animation
        self.spinner_label = QLabel()
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setFixedSize(60, 60)
        layout.addStretch()
        layout.addWidget(self.spinner_label, alignment=Qt.AlignCenter)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        message_font = QFont()
        message_font.setPointSize(12)
        self.message_label.setFont(message_font)
        self.message_label.setStyleSheet("color: #333333; font-weight: bold;")
        layout.addWidget(self.message_label)
        
        layout.addStretch()
        
        # Animation state
        self.spinner_frame = 0
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_colors = [
            "#0f62fe", "#0353e9", "#0242d3", "#0333bd",
            "#0242a7", "#015291", "#00427b", "#003265"
        ]
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate_spinner)
        
        # Background thread
        self.worker_thread = None
        
        # Connect signals
        self.task_complete.connect(self._on_task_complete)
        self.task_error.connect(self._on_task_error)
    
    def _animate_spinner(self):
        """Update spinner animation frame."""
        frame = self.spinner_frames[self.spinner_frame % len(self.spinner_frames)]
        color = self.spinner_colors[self.spinner_frame % len(self.spinner_colors)]
        
        self.spinner_label.setText(frame)
        self.spinner_label.setStyleSheet(f"color: {color}; font-size: 48px; font-weight: bold;")
        
        self.spinner_frame += 1
    
    def _run_task(self):
        """Run the task in background (called from worker thread)."""
        try:
            result = self.task_func()
            self.task_complete.emit(result)
        except Exception as e:
            self.task_error.emit(e)
    
    def _on_task_complete(self, result):
        """Handle task completion."""
        self.result = result
        self.timer.stop()
        self.accept()
    
    def _on_task_error(self, error):
        """Handle task error."""
        self.error = error
        self.timer.stop()
        self.reject()
    
    def set_message(self, message):
        """Update message during loading."""
        self.message_label.setText(message)
    
    def show_and_wait(self):
        """Show spinner and wait for task to complete. Returns result or raises error."""
        self.timer.start(80)
        
        # Start task in background thread
        self.worker_thread = QThread()
        self.worker_thread.run = self._run_task
        self.worker_thread.start()
        
        # Show modal dialog and wait
        self.exec_()
        
        # Clean up
        self.worker_thread.quit()
        self.worker_thread.wait()
        
        if self.error:
            raise self.error
        
        return self.result
    
    def closeEvent(self, event):
        """Stop animation when closing."""
        self.timer.stop()
        super().closeEvent(event)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def show_spinner(message="Loading...", title="Processing"):
    """
    Create and show a loading spinner.
    
    Returns the spinner object so you can call .close() when done.
    
    Usage:
        spinner = show_spinner("Loading cases...")
        # Do work
        spinner.close()
    """
    spinner = LoadingSpinner(message=message, title=title)
    spinner.show()
    return spinner


def run_with_spinner(func, message="Processing...", title="Working"):
    """
    Run a function with a loading spinner displayed.
    
    Returns the result of the function.
    
    Usage:
        result = run_with_spinner(my_long_function, message="Loading...")
    """
    spinner = AsyncSpinner(func, message=message, title=title)
    return spinner.show_and_wait()
