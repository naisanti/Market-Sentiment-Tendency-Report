"""
utils/logger.py
---------------
Centralised logging configuration for the project.

Call ``setup_logger(log_dir=OUTPUT_DIR)`` once from ``main.py``.
All other modules should import and use ``get_logger(__name__)``
to obtain a child logger.
"""

import logging
import sys
from datetime import date
from pathlib import Path


def setup_logger(log_dir: Path, level: int = logging.DEBUG) -> logging.Logger:
    """Configure and return the project's root logger.

    Parameters
    ----------
    log_dir : Path
        Directory where the log file will be written.
    level : int, optional
        Minimum severity level captured by the root logger.

    Returns
    -------
    logging.Logger
        The configured root logger (name ``"trading_report"``).
    """
    root_logger = logging.getLogger("trading_report")
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers on repeated calls.
    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ------------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ------------------------------------------------------------------
    # File handler
    # ------------------------------------------------------------------
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"run_{date.today():%Y-%m-%d}.log"

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the ``trading_report`` namespace."""
    return logging.getLogger(f"trading_report.{name}")