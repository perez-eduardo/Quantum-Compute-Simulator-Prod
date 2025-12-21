"""
Course: CS340 Fall 2025
App name: Quantum Computing Simulation
Description: Logging configuration for the application.
"""

import logging
import sys


def setup_logger():
    """
    Func: Configure and return the application logger.
    
    Creates a logger with DEBUG level that outputs to stdout
    with timestamp, level, and message formatting.
    
    Return:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)  # log level = debug

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    if not logger.handlers:  # prevent duplicate handlers on reimport
        logger.addHandler(handler)
    
    return logger


# Module-level logger instance for import by other modules
logger = setup_logger()