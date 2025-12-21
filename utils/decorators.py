"""
App name: Quantum Computing Simulation
Description: Decorator utilities for error handling in database operations.
"""

from functools import wraps
import logging

from utils.constants import Constants

code = Constants.ResponseCode
logger = logging.getLogger(__name__)


def db_error_handler(func):
    """
    Decorator: Wraps database operations with exception handling.
    
    If the wrapped function raises an exception, logs the error
    and returns a standardized 500 Internal Server Error response.
    
    Args:
        func: The function to wrap.
    
    Return:
        Wrapped function with error handling.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}", exc_info=True)
            return {
                "status_code": code.CODE_500,
                "context": {
                    "message": "Internal server error",
                    "error": str(e)
                }
            }
    return wrapper
