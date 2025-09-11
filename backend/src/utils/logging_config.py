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
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)  # Send logs to console
        ],
        force=True  # Override any existing configuration
    )

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
