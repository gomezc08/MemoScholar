"""
Centralized logging configuration for MemoScholar backend.
This module provides a consistent logging setup across all backend modules.
"""

import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", log_format: Optional[str] = None) -> None:
    """
    Configure logging for the entire backend application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string. If None, uses default format.
    """
    if log_format is None:
        log_format = '[%(asctime)s] %(levelname)s in %(name)s: %(message)s'
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create a stream handler with UTF-8 encoding to handle Unicode characters
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(numeric_level)
    stream_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger with UTF-8 encoding
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[stream_handler],
        force=True  # Override any existing configuration
    )
    
    # Set encoding for stdout to handle Unicode characters
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Usually __name__ from the calling module
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

# Initialize logging when this module is imported
setup_logging()
