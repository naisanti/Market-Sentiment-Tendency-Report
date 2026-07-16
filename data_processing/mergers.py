"""
data_processing/mergers.py
---------------------------
Functions that merge / join DataFrames from different sources.
"""

from __future__ import annotations

import pandas as pd

from config import (
    CATEGORY_COL,
    DATE_COL,
    SUBCATEGORY_COL,
    TICKER_COL,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def build_recent_sectors(
    movers_frames: dict[str, pd.DataFrame],
    movers_raw_sheets: dict[str, pd.DataFrame],
    companies_df: pd.DataFrame,
) -> pd.DataFrame:
    """Join Recent-Movers tickers with the Companies sheet to obtain sector info,
    and append the ``RR`` column sourced from the Strategy Playbook sheets.

    Parameters
    ----------
    movers_frames:
        List of DataFrames produced by Section 1, each containing at least
        ``Date`` and ``Ticker`` columns.
    movers_raw_sheets:
        Mapping of sheet name → raw (unfiltered) DataFrame from Camino 1.
        Used to look up the ``RR`` column per ticker.
    companies_df:
        Full Companies sheet; must contain ``Ticker``, ``Category/Industry``
        and ``Subcategory``.

    Returns
    -------
    pd.DataFrame
        Deduplicated table with columns
        ``[Date, Ticker, Category/Industry, Subcategory, RR]``
        sorted by ``Date`` descending.

    Raises
    ------
    KeyError
        When required columns are absent from *companies_df*.
    """
    _validate_companies_columns(companies_df)

    # Collect all (Date, Ticker) pairs from every strategy sheet
    combined = _combine_date_ticker(movers_frames)

    if combined.empty:
        logger.warning("No tickers found in Recent Movers; Recent Sectors will be empty.")
        return pd.DataFrame(columns=[DATE_COL, TICKER_COL, CATEGORY_COL, SUBCATEGORY_COL, "RR"])

    # Keep only the columns we need from Companies
    companies_slim = companies_df[[TICKER_COL, CATEGORY_COL, SUBCATEGORY_COL]].copy()
    companies_slim = companies_slim.drop_duplicates(subset=[TICKER_COL])

    merged = combined.merge(companies_slim, on=TICKER_COL, how="left")

    missing_sector = merged[CATEGORY_COL].isna().sum()
    if missing_sector:
        logger.warning(
            "%d ticker(s) not found in Companies sheet; sector info will be NaN.",
            missing_sector,
        )

    # Build a Ticker → RR lookup from all Strategy Playbook sheets.
    # If a ticker appears in multiple sheets, the most-recent RR value wins.
    rr_lookup = _build_rr_lookup(movers_raw_sheets)
    merged["RR"] = merged[TICKER_COL].map(rr_lookup)

    if merged["RR"].isna().all():
        logger.warning("RR column not found in any Strategy Playbook sheet.")

    # Deduplicate and sort
    result = (
        merged[
            [
                DATE_COL,
                TICKER_COL,
                CATEGORY_COL,
                SUBCATEGORY_COL,
                "Pattern",
                "RR",
            ]
        ]
        .drop_duplicates()
        .sort_values(DATE_COL, ascending=False)
        .reset_index(drop=True)
    )

    logger.info("Recent Sectors: %d unique rows.", len(result))
    return result


# ---------------------------------------------------------------------------
# Section 4 helpers
# ---------------------------------------------------------------------------


def build_tendencies_ranking(
    tendencies_df: pd.DataFrame,
    b_cols: list[str],
) -> pd.DataFrame:
    """Calculate total activations for each selected B_ indicator.

    Parameters
    ----------
    tendencies_df:
        Date-filtered Tendencies DataFrame.
    b_cols:
        List of B_ column names to include.

    Returns
    -------
    pd.DataFrame
        Columns ``[Indicator, Count]`` sorted by ``Count`` descending.
    """
    if not b_cols or tendencies_df.empty:
        return pd.DataFrame(columns=["Indicator", "Count"])

    counts = tendencies_df[b_cols].apply(lambda col: (col == 1).sum())
    ranking = (
        counts.reset_index()
        .rename(columns={"index": "Indicator", 0: "Count"})
        .sort_values("Count", ascending=False)
        .reset_index(drop=True)
    )
    ranking.columns = ["Indicator", "Count"]
    logger.debug("Tendencies Ranking: %d rows.", len(ranking))
    return ranking


def build_tendencies_c_table(
    tendencies_df: pd.DataFrame,
    c_cols: list[str],
) -> pd.DataFrame:
    """Build the historical C_ table for the report.

    Parameters
    ----------
    tendencies_df:
        Date-filtered Tendencies DataFrame (already sorted Date DESC).
    c_cols:
        Filtered C_ column names to include.

    Returns
    -------
    pd.DataFrame
        Columns ``[Date] + c_cols`` sorted by ``Date`` descending.
    """
    if not c_cols or tendencies_df.empty:
        return pd.DataFrame(columns=[DATE_COL])

    cols = [DATE_COL] + c_cols
    result = tendencies_df[cols].sort_values(DATE_COL, ascending=False).reset_index(drop=True)
    logger.debug("Tendencies C_ table: %d rows × %d cols.", *result.shape)
    return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _combine_date_ticker(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Stack Date + Ticker columns from multiple DataFrames."""
    parts: list[pd.DataFrame] = []

    for pattern, df in frames.items():
        if DATE_COL in df.columns and TICKER_COL in df.columns:
            part = df[[DATE_COL, TICKER_COL]].copy()
            part["Pattern"] = pattern
            parts.append(part)
        else:
            logger.warning(
                "Skipping a movers DataFrame that is missing '%s' or '%s'.",
                DATE_COL,
                TICKER_COL,
            )

    if not parts:
        return pd.DataFrame(columns=[DATE_COL, TICKER_COL])

    return pd.concat(parts, ignore_index=True).drop_duplicates()


def _build_rr_lookup(raw_sheets: dict[str, pd.DataFrame]) -> dict[str, object]:
    """Build a ``{Ticker: RR}`` mapping from all Strategy Playbook sheets.

    For each sheet that contains both ``Ticker`` and ``RR`` columns, extract
    the most-recent row per ticker (by ``Date`` when available, otherwise the
    last row).  Later sheets in iteration order overwrite earlier ones only
    if the date is more recent.

    Parameters
    ----------
    raw_sheets:
        Mapping of sheet name → full (unfiltered) DataFrame.

    Returns
    -------
    dict[str, object]
        Ticker string → RR value.
    """
    rr_map: dict[str, object] = {}

    for sheet_name, df in raw_sheets.items():
        if TICKER_COL not in df.columns or "RR" not in df.columns:
            logger.debug("Sheet '%s' has no RR column; skipping for RR lookup.", sheet_name)
            continue

        work = df[[TICKER_COL, "RR"]].copy()

        # Use the most-recent row per ticker when Date is available
        if DATE_COL in df.columns:
            work[DATE_COL] = pd.to_datetime(df[DATE_COL])
            work = (
                work.assign(**{DATE_COL: df[DATE_COL]})
                .sort_values(DATE_COL, ascending=False)
                .drop_duplicates(subset=[TICKER_COL])
            )

        for _, row in work.iterrows():
            ticker = row[TICKER_COL]
            if pd.notna(ticker) and ticker not in rr_map:
                rr_map[str(ticker)] = row["RR"]

    logger.debug("RR lookup built: %d tickers.", len(rr_map))
    return rr_map


def _validate_companies_columns(df: pd.DataFrame) -> None:
    required = {TICKER_COL, CATEGORY_COL, SUBCATEGORY_COL}
    missing = required - set(df.columns)
    if missing:
        raise KeyError(
            f"Companies sheet is missing required columns: {missing}"
        )
