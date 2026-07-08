"""
data_processing/filters.py
----------------------------
Business-logic filters applied to the raw DataFrames before they are
passed to the reporting layer.

Windows are now calendar-day based (no trading-day / holiday logic).
"""

from __future__ import annotations

import pandas as pd

from config import (
    B_PREFIX,
    C_PREFIX,
    DATE_COL,
    TENDENCIES_DAYS,
    TENDENCIES_FILTER_DAYS,
)
from utils.dates import filter_last_n_calendar_days
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Section 3 helpers
# ---------------------------------------------------------------------------


def select_binary_columns(df: pd.DataFrame) -> list[str]:
    """Return B_ column names that have at least one value == 1
    within the last ``TENDENCIES_FILTER_DAYS`` calendar days.

    Parameters
    ----------
    df:
        DataFrame already filtered to ``TENDENCIES_DAYS`` calendar days.

    Returns
    -------
    list[str]
    """
    b_cols = [c for c in df.columns if c.startswith(B_PREFIX)]
    if not b_cols:
        logger.warning("No B_ columns found in Tendencies sheet.")
        return []

    recent = _get_last_n_rows(df, TENDENCIES_FILTER_DAYS)
    selected = [c for c in b_cols if (recent[c] == 1).any()]
    logger.debug(
        "B_ columns: %d total, %d pass filter (≥1 activation in last %d calendar days)",
        len(b_cols), len(selected), TENDENCIES_FILTER_DAYS,
    )
    return selected


def select_count_columns(df: pd.DataFrame) -> list[str]:
    """Return C_ column names that have at least one value > 1
    within the last ``TENDENCIES_FILTER_DAYS`` calendar days.

    Parameters
    ----------
    df:
        DataFrame already filtered to ``TENDENCIES_DAYS`` calendar days.

    Returns
    -------
    list[str]
    """
    c_cols = [c for c in df.columns if c.startswith(C_PREFIX)]
    if not c_cols:
        logger.warning("No C_ columns found in Tendencies sheet.")
        return []

    recent = _get_last_n_rows(df, TENDENCIES_FILTER_DAYS)
    selected = [c for c in c_cols if (recent[c] > 1).any()]
    logger.debug(
        "C_ columns: %d total, %d pass filter (≥1 value > 1 in last %d calendar days)",
        len(c_cols), len(selected), TENDENCIES_FILTER_DAYS,
    )
    return selected


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_last_n_rows(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """Return the *n* rows with the most-recent dates (sorted DESC)."""
    if DATE_COL not in df.columns:
        logger.warning("'%s' column missing; falling back to tail(%d).", DATE_COL, n)
        return df.tail(n)
    return df.sort_values(DATE_COL, ascending=False).head(n)


def build_tendencies_base(tendencies_raw: pd.DataFrame) -> pd.DataFrame:
    """Filter the raw Tendencies sheet to the last ``TENDENCIES_DAYS`` calendar days.

    Parameters
    ----------
    tendencies_raw:
        Full DataFrame from the Tendencies sheet.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame sorted by date descending.
    """
    df = filter_last_n_calendar_days(tendencies_raw, DATE_COL, TENDENCIES_DAYS)
    df = df.sort_values(DATE_COL, ascending=False).reset_index(drop=True)
    return df
