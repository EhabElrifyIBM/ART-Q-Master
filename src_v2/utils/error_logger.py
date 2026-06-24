# ============================================================================
# error_logger.py - Comprehensive Error Logging & Recovery System
# ============================================================================
# Phase 4.3: Better Error Logging & Recovery
# 
# Provides centralized error logging, recovery mechanisms, and retry functionality.
# ============================================================================

import os
import sys
import json
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from enum import Enum


class ErrorLevel(Enum):
    """Error severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    RECOVERED = "RECOVERED"


class ErrorLogger:
    """
    Comprehensive error logging and tracking system.
    
    Features:
    - Centralized error logging
    - Error history with timestamps
    - Recovery tracking
    - Automatic log file rotation
    - JSON error export
    - Statistics tracking
    
    Usage:
        logger = ErrorLogger("AutoSender")
        logger.log_error("Operation failed", exc, error_level=ErrorLevel.ERROR)
        stats = logger.get_statistics()
    """
    
    def __init__(self, module_name: str, log_dir: Optional[str] = None):
        """
        Initialize error logger.
        
        Args:
            module_name (str): Name of module using this logger (e.g., "AutoSender")
            log_dir (str): Directory for log files. Default: project_root/logs
        """
        self.module_name = module_name
        self.log_dir = log_dir or self._get_log_directory()
        self.session_start = datetime.now()
        self.errors = []
        self.recovered_errors = []
        self.statistics = {
            'total_errors': 0,
            'total_recovered': 0,
            'total_warnings': 0,
            'critical_errors': 0,
            'by_type': {}
        }
        
        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Setup Python logging
        self._setup_logging()
    
    def _get_log_directory(self) -> str:
        """Get default log directory."""
        # Try to find project root
        current = os.path.dirname(os.path.abspath(__file__))
        
        # Navigate up to find logs directory
        while current != os.path.dirname(current):  # Stop at root
            potential_logs = os.path.join(current, 'logs')
            if os.path.exists(potential_logs):
                return potential_logs
            
            potential_logs = os.path.join(current, 'errors')
            if os.path.exists(potential_logs):
                return potential_logs
            
            current = os.path.dirname(current)
        
        # Default: create logs in home directory
        logs_dir = os.path.expanduser('~/ART_Q_Master/logs')
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    
    def _setup_logging(self):
        """Setup Python logging handler."""
        log_file = os.path.join(
            self.log_dir,
            f"{self.module_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.logger = logging.getLogger(self.module_name)
    
    def log_error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        error_level: ErrorLevel = ErrorLevel.ERROR,
        context: Optional[Dict[str, Any]] = None,
        recovery_action: Optional[str] = None
    ):
        """
        Log an error with full context.
        
        Args:
            message (str): Error message
            exception (Exception): Exception object if available
            error_level (ErrorLevel): Severity level
            context (dict): Additional context (case_id, step, etc.)
            recovery_action (str): Description of recovery action taken
        """
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'module': self.module_name,
            'level': error_level.value,
            'message': message,
            'traceback': None,
            'context': context or {},
            'recovery_action': recovery_action
        }
        
        if exception:
            error_record['exception_type'] = type(exception).__name__
            error_record['exception_message'] = str(exception)
            error_record['traceback'] = traceback.format_exc()
        
        # Store error
        self.errors.append(error_record)
        
        # Update statistics
        self.statistics['total_errors'] += 1
        if error_level == ErrorLevel.CRITICAL:
            self.statistics['critical_errors'] += 1
        elif error_level == ErrorLevel.WARNING:
            self.statistics['total_warnings'] += 1
        
        # Track by type
        error_type = error_record.get('exception_type', message)
        self.statistics['by_type'][error_type] = self.statistics['by_type'].get(error_type, 0) + 1
        
        # Log to file
        self.logger.error(
            f"[{error_level.value}] {message}",
            exc_info=exception
        )
        
        # Print to console
        print(f"[{error_level.value}] {self.module_name}: {message}")
        if recovery_action:
            print(f"[RECOVERY] {recovery_action}")
    
    def log_recovery(self, original_error: str, recovery_action: str, success: bool):
        """
        Log error recovery attempt.
        
        Args:
            original_error (str): Description of original error
            recovery_action (str): Recovery action attempted
            success (bool): Whether recovery was successful
        """
        recovery_record = {
            'timestamp': datetime.now().isoformat(),
            'original_error': original_error,
            'recovery_action': recovery_action,
            'success': success
        }
        
        self.recovered_errors.append(recovery_record)
        if success:
            self.statistics['total_recovered'] += 1
        
        level = ErrorLevel.RECOVERED if success else ErrorLevel.WARNING
        status = "SUCCESS" if success else "FAILED"
        
        self.logger.info(f"Recovery attempt [{status}]: {recovery_action}")
        print(f"[RECOVERY {status}] {recovery_action}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        return {
            **self.statistics,
            'session_duration': str(datetime.now() - self.session_start),
            'total_logged_errors': len(self.errors),
            'total_recoveries': len(self.recovered_errors),
            'recovery_rate': (
                f"{(len(self.recovered_errors) / len(self.errors) * 100):.1f}%" 
                if self.errors else "N/A"
            )
        }
    
    def export_to_json(self, filename: Optional[str] = None) -> str:
        """
        Export error log to JSON file.
        
        Args:
            filename (str): Output filename. Default: <module>_errors_<timestamp>.json
        
        Returns:
            str: Path to exported file
        """
        if not filename:
            filename = f"{self.module_name}_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.log_dir, filename)
        
        export_data = {
            'module': self.module_name,
            'session_start': self.session_start.isoformat(),
            'export_time': datetime.now().isoformat(),
            'statistics': self.get_statistics(),
            'errors': self.errors,
            'recoveries': self.recovered_errors
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"[LOG EXPORT] Errors exported to: {filepath}")
        return filepath
    
    def print_summary(self):
        """Print error summary to console."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print(f"ERROR LOG SUMMARY - {self.module_name}")
        print("="*60)
        print(f"Total Errors: {stats['total_logged_errors']}")
        print(f"Critical Errors: {stats['critical_errors']}")
        print(f"Warnings: {stats['total_warnings']}")
        print(f"Recovered: {stats['total_recovered']}")
        print(f"Recovery Rate: {stats['recovery_rate']}")
        print(f"Session Duration: {stats['session_duration']}")
        
        if stats['by_type']:
            print("\nError Types:")
            for error_type, count in sorted(stats['by_type'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {error_type}: {count}")
        
        print("="*60 + "\n")


class RetryHandler:
    """
    Intelligent retry mechanism with exponential backoff.
    
    Usage:
        retry = RetryHandler(max_attempts=3, backoff_factor=2)
        result = retry.execute(operation, arg1, arg2)
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        logger: Optional[ErrorLogger] = None
    ):
        """
        Initialize retry handler.
        
        Args:
            max_attempts (int): Maximum retry attempts
            backoff_factor (float): Multiplier for exponential backoff
            initial_delay (float): Initial delay in seconds
            max_delay (float): Maximum delay in seconds
            logger (ErrorLogger): Logger instance for tracking
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.logger = logger
        self.attempt_count = 0
    
    def execute(
        self,
        operation: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute operation with retry logic.
        
        Args:
            operation (callable): Function to execute
            *args: Arguments for operation
            **kwargs: Keyword arguments for operation
        
        Returns:
            Result from successful operation execution
        
        Raises:
            Exception: If all retry attempts fail
        """
        import time
        
        self.attempt_count = 0
        last_exception = None
        
        while self.attempt_count < self.max_attempts:
            try:
                self.attempt_count += 1
                
                if self.attempt_count > 1:
                    print(f"[RETRY] Attempt {self.attempt_count}/{self.max_attempts}")
                
                result = operation(*args, **kwargs)
                
                if self.attempt_count > 1:
                    recovery_msg = f"Recovered after {self.attempt_count} attempts"
                    print(f"[RECOVERY SUCCESS] {recovery_msg}")
                    if self.logger:
                        self.logger.log_recovery(
                            str(last_exception),
                            recovery_msg,
                            success=True
                        )
                
                return result
            
            except Exception as e:
                last_exception = e
                
                if self.attempt_count >= self.max_attempts:
                    # All retries exhausted
                    if self.logger:
                        self.logger.log_error(
                            f"Operation failed after {self.max_attempts} attempts",
                            e,
                            error_level=ErrorLevel.CRITICAL
                        )
                    raise
                
                # Calculate backoff delay
                delay = min(
                    self.initial_delay * (self.backoff_factor ** (self.attempt_count - 1)),
                    self.max_delay
                )
                
                if self.logger:
                    self.logger.log_recovery(
                        str(e),
                        f"Retrying in {delay:.1f}s (attempt {self.attempt_count}/{self.max_attempts})",
                        success=False
                    )
                
                print(f"[RETRY] Waiting {delay:.1f} seconds before retry...")
                time.sleep(delay)
    
    def get_attempt_count(self) -> int:
        """Get current attempt count."""
        return self.attempt_count


class ErrorRecoveryManager:
    """
    Centralized error recovery manager for common errors.
    
    Provides recovery strategies for common operational errors.
    """
    
    def __init__(self, logger: ErrorLogger):
        """
        Initialize recovery manager.
        
        Args:
            logger (ErrorLogger): Logger instance
        """
        self.logger = logger
        self.recovery_strategies = {}
    
    def register_strategy(
        self,
        error_type: type,
        strategy: Callable[[Exception], bool]
    ):
        """
        Register error recovery strategy.
        
        Args:
            error_type (type): Exception type to handle
            strategy (callable): Function to execute for recovery
        """
        self.recovery_strategies[error_type] = strategy
    
    def attempt_recovery(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """
        Attempt to recover from error using registered strategy.
        
        Args:
            exception (Exception): Exception that occurred
            context (dict): Additional context
        
        Returns:
            bool: True if recovery successful, False otherwise
        """
        error_type = type(exception)
        
        if error_type in self.recovery_strategies:
            try:
                strategy = self.recovery_strategies[error_type]
                success = strategy(exception)
                
                self.logger.log_recovery(
                    str(exception),
                    f"Applied {error_type.__name__} recovery strategy",
                    success=success
                )
                
                return success
            except Exception as e:
                self.logger.log_error(
                    f"Recovery strategy failed: {e}",
                    e,
                    error_level=ErrorLevel.WARNING
                )
                return False
        
        return False


# ============================================================================
# Example Usage
# ============================================================================
if __name__ == "__main__":
    # Create logger
    logger = ErrorLogger("ExampleModule")
    
    # Log an error
    try:
        x = 1 / 0
    except Exception as e:
        logger.log_error(
            "Division by zero",
            e,
            error_level=ErrorLevel.ERROR,
            context={'operation': 'calculate', 'values': [1, 0]},
            recovery_action="Using fallback value of 0"
        )
    
    # Retry handler
    retry = RetryHandler(max_attempts=3, logger=logger)
    
    def flaky_operation():
        import random
        if random.random() < 0.7:
            raise RuntimeError("Random failure")
        return "Success!"
    
    try:
        result = retry.execute(flaky_operation)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Operation failed: {e}")
    
    # Print summary
    logger.print_summary()
    
    # Export to JSON
    logger.export_to_json()


# ============================================================================
# Singleton Management
# ============================================================================

_error_logger = None

def get_error_logger(module_name: str = "Application") -> ErrorLogger:
    """
    Get or create the global error logger singleton.
    
    Args:
        module_name: Name of the module for logging
        
    Returns:
        ErrorLogger: The global error logger instance
    """
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger(module_name)
    return _error_logger
