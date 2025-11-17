"""
Logging utility for the University Merch Bot.

Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import config


def setup_logger(
        name: str,
        log_file: Optional[Path] = None,
        level: str = config.LOG_LEVEL
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__ from calling module)
        log_file: Optional file path to write logs
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(config.LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_statistics(logger: logging.Logger, stats: dict) -> None:
    """
    Log statistics in a formatted way.
    
    Args:
        logger: Logger instance
        stats: Dictionary of statistics to log
    """
    logger.info("=" * 60)
    logger.info("STATISTICS SUMMARY")
    logger.info("=" * 60)
    for key, value in stats.items():
        logger.info(f"{key}: {value}")
    logger.info("=" * 60)
