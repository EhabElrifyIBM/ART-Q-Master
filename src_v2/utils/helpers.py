"""
Common utility functions used across the application
"""

from datetime import datetime
import os
import json
import logging

def setup_logging(name, log_file):
    """Set up logging configuration for a module"""
    # Reset basicConfig if it was already configured
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create file handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Set formatter for both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO
    )
    
    # Configure named logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers and add new ones
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_config(config_path):
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")
        return {}

def format_date(date_obj, format_str="%Y-%m-%d"):
    """Format date object to string"""
    return date_obj.strftime(format_str)

def parse_date(date_str, format_str="%Y-%m-%d"):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, format_str)
    except ValueError as e:
        logging.error(f"Error parsing date: {str(e)}")
        return None

def ensure_dir(directory):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        
def validate_file(file_path, required_columns):
    """Validate that file exists and has required columns"""
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            return False, f"Missing required columns: {', '.join(missing_cols)}"
        return True, "File is valid"
    except Exception as e:
        return False, f"Error validating file: {str(e)}"
