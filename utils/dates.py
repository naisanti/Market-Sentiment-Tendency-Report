"""
utils/dates.py
--------------
Date-related utilities.

Recent Movers and Tendencies windows now use plain calendar-day arithmetic
(no trading-day or holiday logic).  The Nasdaq-holiday helpers are kept for
any future use but are no longer called by the main pipeline.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Sequence

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Calendar-day filter  (used by all sections)
# ---------------------------------------------------------------------------


def filter_last_n_calendar_days(
    df: pd.DataFrame,
    date_col: str,
    n: int,
    reference: date | None = None,
) -> pd.DataFrame:
    """Keep only rows whose *date_col* falls within the last *n* calendar days.

    Parameters
    ----------
    df:
        Source DataFrame.
    date_col:
        Name of the date column.
    n:
        Number of calendar days to look back (weekends and holidays included).
    reference:
        Cutoff upper bound (inclusive).  Defaults to ``date.today()``.

    Returns
    -------
    pd.DataFrame
        Filtered copy; original is not modified.
    """
    if reference is None:
        reference = date.today()

    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    cutoff = pd.Timestamp(reference) - pd.Timedelta(days=n - 1)
    upper  = pd.Timestamp(reference)

    mask = (df[date_col] >= cutoff) & (df[date_col] <= upper)
    filtered = df.loc[mask].copy()

    logger.debug(
        "filter_last_n_calendar_days: %d→%d rows (last %d days, %s to %s)",
        len(df), len(filtered), n, cutoff.date(), upper.date(),
    )
    return filtered


# ---------------------------------------------------------------------------
# Legacy trading-day helpers (kept for reference, not used by pipeline)
# ---------------------------------------------------------------------------


def is_trading_day(d: date) -> bool:
    """Return True when *d* is Mon–Fri (holiday list no longer maintained)."""
    return d.weekday() < 5


def get_last_n_trading_days(n: int, reference: date | None = None) -> list[date]:
    """Return the last *n* Mon–Fri days up to *reference* (no holiday list)."""
    if reference is None:
        reference = date.today()

    trading_days: list[date] = []
    current = reference
    while len(trading_days) < n:
        if is_trading_day(current):
            trading_days.append(current)
        current -= timedelta(days=1)
    return sorted(trading_days)


# ---------------------------------------------------------------------------
# Kept for backward-compatibility with any call sites that still use it
# ---------------------------------------------------------------------------

def filter_last_n_trading_days(
    df: pd.DataFrame,
    date_col: str,
    n: int,
    reference: date | None = None,
) -> pd.DataFrame:
    """Alias → delegates to :func:`filter_last_n_calendar_days`."""
    return filter_last_n_calendar_days(df, date_col, n, reference)
