"""
deckAIn - Logging Utilities
Centralized logging configuration
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from config.settings import LOG_LEVEL, PROJECT_ROOT

# Create logs directory
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str) -> logging.Logger:
    """
    Create a logger with both file and console handlers.
    
    Args:
        name: Logger name (usually __name__ of the module)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger
    
    # Console handler (UTF-8 encoding for emoji support)
    # Reconfigure stdout/stderr to use UTF-8 on Windows
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except AttributeError:
             # Fallback for older Python versions
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # File handler (detailed logs)
    log_file = LOGS_DIR / f"deckain_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_stage(logger: logging.Logger, stage_num: int, stage_name: str, status: str = "START"):
    """
    Log a pipeline stage with consistent formatting.
    
    Args:
        logger: Logger instance
        stage_num: Stage number (1-7)
        stage_name: Name of the stage
        status: "START", "DONE", "FAIL", "SKIP"
    """
    symbols = {
        "START": "[>]",
        "DONE": "[OK]",
        "FAIL": "[X]",
        "SKIP": "[SKIP]"
    }
    symbol = symbols.get(status, "*")
    logger.info(f"{symbol} [{stage_num}/7] {stage_name} - {status}")

def log_api_call(logger, model: str, tokens_in: int, tokens_out: int):
    """Log API call with token usage (no cost assumptions)."""
    total = tokens_in + tokens_out
    logger.info(f"API Call: {model} | In: {tokens_in:,} | Out: {tokens_out:,} | Total: {total:,} tokens")

def log_compliance_check(logger: logging.Logger, check_name: str, passed: bool, details: str = ""):
    """
    Log compliance validation results.
    
    Args:
        logger: Logger instance
        check_name: Name of check
        passed: Whether check passed
        details: Additional details
    """
    status = "PASS" if passed else "FAIL"
    logger.info(f"Compliance: {check_name} - {status} {details}")
