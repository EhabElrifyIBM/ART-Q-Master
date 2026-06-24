# ============================================================================
# error_handler.py - Error Handler Integration for v2 Components
# ============================================================================
# Phase 4.3: Better Error Logging & Recovery
#
# Integrates error logging and recovery with AutoSender_v2 and CaseReviewer_v2.
# ============================================================================

from typing import Optional, Callable, Any, Dict
from utils.error_logger import ErrorLogger, ErrorLevel, RetryHandler, ErrorRecoveryManager


class OperationErrorHandler:
    """
    Error handler for AutoSender and CaseReviewer operations.
    
    Features:
    - Automatic error logging
    - Recovery strategies
    - User notifications
    - Graceful error degradation
    
    Usage:
        handler = OperationErrorHandler("AutoSender")
        handler.handle_excel_load_error(e, filename)
        handler.print_report()
    """
    
    def __init__(self, module_name: str):
        """Initialize operation error handler."""
        self.logger = ErrorLogger(module_name)
        self.recovery_manager = ErrorRecoveryManager(self.logger)
        self.module_name = module_name
        
        # Register common recovery strategies
        self._register_recovery_strategies()
    
    def _register_recovery_strategies(self):
        """Register default error recovery strategies."""
        
        # File not found - offer alternative paths
        def handle_file_not_found(e):
            self.logger.log_error(
                f"File not found: {e}",
                e,
                error_level=ErrorLevel.WARNING,
                recovery_action="User should select alternate file"
            )
            return False  # Requires user intervention
        
        self.recovery_manager.register_strategy(FileNotFoundError, handle_file_not_found)
        
        # Permission error - explain permissions issue
        def handle_permission_error(e):
            self.logger.log_error(
                f"Permission denied: {e}",
                e,
                error_level=ErrorLevel.WARNING,
                recovery_action="Close file if open in Excel, try again"
            )
            return False  # Requires user intervention
        
        self.recovery_manager.register_strategy(PermissionError, handle_permission_error)
    
    def handle_file_operation_error(
        self,
        error: Exception,
        operation: str,
        filepath: str,
        user_notification: bool = True,
        **context
    ):
        """
        Handle file operation errors (read, write, access).
        
        Args:
            error (Exception): Exception that occurred
            operation (str): Operation that failed (load, save, process)
            filepath (str): File path involved
            user_notification (bool): Show user notification
            **context: Additional context (case_id, step, etc.)
        """
        error_context = {
            'operation': operation,
            'filepath': filepath,
            'error_type': type(error).__name__,
            **context
        }
        
        # Determine error level
        if isinstance(error, PermissionError):
            error_level = ErrorLevel.WARNING
            message = f"Cannot access {operation}: File may be open in another application"
        elif isinstance(error, FileNotFoundError):
            error_level = ErrorLevel.WARNING
            message = f"Cannot find file: {filepath}"
        else:
            error_level = ErrorLevel.ERROR
            message = f"File {operation} failed: {str(error)}"
        
        # Log error
        self.logger.log_error(
            message,
            error,
            error_level=error_level,
            context=error_context
        )
        
        # Attempt recovery
        self.recovery_manager.attempt_recovery(error, error_context)
        
        # Notify user
        if user_notification:
            self._notify_user(message, error_level)
    
    def handle_data_processing_error(
        self,
        error: Exception,
        operation: str,
        case_id: Optional[str] = None,
        user_notification: bool = True,
        **context
    ):
        """
        Handle data processing errors (parsing, validation, transformation).
        
        Args:
            error (Exception): Exception that occurred
            operation (str): Processing operation that failed
            case_id (str): Case ID being processed
            user_notification (bool): Show user notification
            **context: Additional context
        """
        error_context = {
            'operation': operation,
            'case_id': case_id,
            'error_type': type(error).__name__,
            **context
        }
        
        error_level = ErrorLevel.ERROR
        message = f"Data processing error in {operation}: {str(error)}"
        
        # Log error
        self.logger.log_error(
            message,
            error,
            error_level=error_level,
            context=error_context
        )
        
        # Notify user
        if user_notification:
            self._notify_user(f"Processing failed for case {case_id}: {str(error)}", error_level)
    
    def handle_selenium_error(
        self,
        error: Exception,
        operation: str,
        case_id: Optional[str] = None,
        user_notification: bool = True,
        **context
    ):
        """
        Handle Selenium/browser errors (element not found, timeout, connection).
        
        Args:
            error (Exception): Exception that occurred
            operation (str): Selenium operation that failed
            case_id (str): Case ID being processed
            user_notification (bool): Show user notification
            **context: Additional context
        """
        error_context = {
            'operation': operation,
            'case_id': case_id,
            'error_type': type(error).__name__,
            **context
        }
        
        error_level = ErrorLevel.WARNING
        
        # Determine specific error type
        error_str = str(error).lower()
        if 'timeout' in error_str:
            message = f"Operation timeout: {operation}"
            recovery = "Page may be slow to load. Retrying..."
        elif 'element' in error_str or 'not found' in error_str:
            message = f"UI element not found: {operation}"
            recovery = "Page structure may have changed. Retrying..."
        elif 'connection' in error_str or 'refused' in error_str:
            message = f"Connection error: {operation}"
            recovery = "Network issue detected. Retrying..."
        else:
            message = f"Browser error in {operation}: {str(error)}"
            recovery = "Retrying operation..."
        
        # Log error with recovery action
        self.logger.log_error(
            message,
            error,
            error_level=error_level,
            context=error_context,
            recovery_action=recovery
        )
        
        # Notify user
        if user_notification:
            self._notify_user(f"{message} - {recovery}", error_level)
    
    def handle_network_error(
        self,
        error: Exception,
        operation: str,
        user_notification: bool = True,
        **context
    ):
        """
        Handle network-related errors (API calls, CRM connection).
        
        Args:
            error (Exception): Exception that occurred
            operation (str): Network operation that failed
            user_notification (bool): Show user notification
            **context: Additional context
        """
        error_context = {
            'operation': operation,
            'error_type': type(error).__name__,
            **context
        }
        
        error_level = ErrorLevel.WARNING
        message = f"Network error in {operation}: {str(error)}"
        recovery = "Retrying with exponential backoff..."
        
        # Log error
        self.logger.log_error(
            message,
            error,
            error_level=error_level,
            context=error_context,
            recovery_action=recovery
        )
        
        # Notify user
        if user_notification:
            self._notify_user(f"{message} - {recovery}", error_level)
    
    def handle_critical_error(
        self,
        error: Exception,
        operation: str,
        user_notification: bool = True,
        **context
    ):
        """
        Handle critical errors that cannot be recovered.
        
        Args:
            error (Exception): Exception that occurred
            operation (str): Operation that failed
            user_notification (bool): Show user notification
            **context: Additional context
        """
        error_context = {
            'operation': operation,
            'error_type': type(error).__name__,
            **context
        }
        
        message = f"Critical error in {operation}: {str(error)}"
        
        # Log critical error
        self.logger.log_error(
            message,
            error,
            error_level=ErrorLevel.CRITICAL,
            context=error_context,
            recovery_action="Operation halted. Manual intervention required."
        )
        
        # Notify user
        if user_notification:
            self._notify_user(
                f"CRITICAL ERROR: {message}\nPlease check the logs for details.",
                ErrorLevel.CRITICAL
            )
    
    def _notify_user(self, message: str, error_level: ErrorLevel):
        """
        Notify user of error through UI.
        
        Args:
            message (str): Error message to display
            error_level (ErrorLevel): Severity level for styling
        """
        try:
            # Lazy import UI functions (after QApplication created)
            try:
                from ART_Q_Control.SharedFunctions import show_popup
                
                # Determine icon based on level
                if error_level == ErrorLevel.CRITICAL:
                    title = "⚠️ Critical Error"
                    icon_type = "critical"
                elif error_level == ErrorLevel.ERROR:
                    title = "❌ Error"
                    icon_type = "error"
                elif error_level == ErrorLevel.WARNING:
                    title = "⚠️ Warning"
                    icon_type = "warning"
                else:
                    title = "ℹ️ Information"
                    icon_type = "info"
                
                # Show popup
                show_popup(title, message, icon=icon_type)
            except (ImportError, AttributeError):
                # Fallback if SharedFunctions not available
                print(f"[{error_level.value}] {message}")
        except Exception as e:
            # Final fallback: log to console
            print(f"[{error_level.value}] {message}")
    
    def create_retry_handler(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0
    ) -> RetryHandler:
        """
        Create a retry handler for retryable operations.
        
        Args:
            max_attempts (int): Maximum retry attempts
            backoff_factor (float): Backoff multiplier
            initial_delay (float): Initial delay in seconds
        
        Returns:
            RetryHandler: Configured retry handler
        """
        return RetryHandler(
            max_attempts=max_attempts,
            backoff_factor=backoff_factor,
            initial_delay=initial_delay,
            logger=self.logger
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return self.logger.get_statistics()
    
    def print_report(self):
        """Print error report to console."""
        print("\n" + "="*70)
        print(f"ERROR REPORT - {self.module_name}")
        print("="*70)
        self.logger.print_summary()
    
    def export_errors(self, filename: Optional[str] = None) -> str:
        """
        Export errors to JSON file.
        
        Args:
            filename (str): Output filename
        
        Returns:
            str: Path to exported file
        """
        return self.logger.export_to_json(filename)


# ============================================================================
# Context Manager for Error Handling
# ============================================================================

class ErrorHandlingContext:
    """
    Context manager for automatic error handling.
    
    Usage:
        handler = OperationErrorHandler("AutoSender")
        with ErrorHandlingContext(
            handler,
            operation="load_excel",
            case_id="CASE_001"
        ):
            # Your operation here
            df = pd.read_excel("file.xlsx")
    """
    
    def __init__(
        self,
        error_handler: OperationErrorHandler,
        operation: str,
        case_id: Optional[str] = None,
        error_level: str = "warning",
        **context
    ):
        """
        Initialize error handling context.
        
        Args:
            error_handler (OperationErrorHandler): Error handler instance
            operation (str): Operation being performed
            case_id (str): Case ID if applicable
            error_level (str): Default error level for this context
            **context: Additional context
        """
        self.error_handler = error_handler
        self.operation = operation
        self.case_id = case_id
        self.error_level = error_level
        self.context = context
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and handle any exception."""
        if exc_type is None:
            return False  # No exception, continue normally
        
        # Handle different exception types
        if exc_type.__name__.startswith('FileNotFoundError') or exc_type.__name__.startswith('PermissionError'):
            self.error_handler.handle_file_operation_error(
                exc_val,
                self.operation,
                self.context.get('filepath', 'unknown'),
                **self.context
            )
        elif exc_type.__name__.startswith('Selenium'):
            self.error_handler.handle_selenium_error(
                exc_val,
                self.operation,
                self.case_id,
                **self.context
            )
        elif 'Connection' in exc_type.__name__ or 'Request' in exc_type.__name__:
            self.error_handler.handle_network_error(
                exc_val,
                self.operation,
                **self.context
            )
        else:
            self.error_handler.handle_data_processing_error(
                exc_val,
                self.operation,
                self.case_id,
                **self.context
            )
        
        return True  # Suppress exception (it was handled)


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    # Create error handler
    handler = OperationErrorHandler("ExampleModule")
    
    # Example 1: Direct error handling
    try:
        with open("nonexistent.txt", "r") as f:
            pass
    except Exception as e:
        handler.handle_file_operation_error(
            e,
            operation="load",
            filepath="nonexistent.txt",
            case_id="CASE_001"
        )
    
    # Example 2: Using context manager
    try:
        with ErrorHandlingContext(
            handler,
            operation="process_data",
            case_id="CASE_001",
            filepath="data.txt"
        ):
            x = 1 / 0
    except Exception as e:
        print(f"Caught: {e}")
    
    # Example 3: Retry with error handling
    retry = handler.create_retry_handler(max_attempts=3)
    
    def flaky_operation():
        import random
        if random.random() < 0.7:
            raise RuntimeError("Flaky!")
        return "Success!"
    
    try:
        result = retry.execute(flaky_operation)
        print(f"Result: {result}")
    except Exception as e:
        handler.handle_critical_error(e, "flaky_operation")
    
    # Print report
    handler.print_report()
    
    # Export errors
    handler.export_errors()
