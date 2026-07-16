"""
main.py
-------
Entry-point for the Market Sentiment Tendency Report pipeline.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

from config import (
    COMPANIES_SHEET,
    CT_PREFIX,
    DATE_COL,
    OUTPUT_DIR,
    RECENT_MOVERS_DAYS,
    STRATEGY_PLAYBOOK_PATH,
    T_PREFIX,
    TENDENCIES_SHEET,
    TICKER_COL,
    MARKET_SENTIMENT_PATH,
)
from data_processing.excel_reader import (
    read_all_sheets,
    read_sheet,
    select_prefixed_columns,
)
from data_processing.filters import (
    build_tendencies_base,
    select_binary_columns,
    select_count_columns,
)
from data_processing.mergers import (
    build_recent_sectors,
    build_tendencies_c_table,
    build_tendencies_ranking,
)
from reporting.report_generator import ReportData, generate_report
from utils.dates import filter_last_n_calendar_days
from utils.logger import get_logger, setup_logger


def main() -> None:
    """Orchestrate the full report-generation pipeline."""
    setup_logger(log_dir=OUTPUT_DIR)
    logger = get_logger(__name__)
    logger.info("=== Market Sentiment Tendency Report – pipeline started ===")

    # ------------------------------------------------------------------
    # Section 1 – Recent Movers
    # Window: last RECENT_MOVERS_DAYS calendar days from today.
    # Sheets with no matching rows are silently skipped.
    # Includes RR column (1 decimal) when present.
    # ------------------------------------------------------------------
    movers: dict[str, pd.DataFrame] = {}

    try:
        all_sheets = read_all_sheets(STRATEGY_PLAYBOOK_PATH)
    except FileNotFoundError as exc:
        logger.error("Cannot read Strategy Playbook: %s", exc)
        all_sheets = {}

    for sheet_name, raw_df in all_sheets.items():
        try:
            # Calendar-day filter anchored to today
            filtered = filter_last_n_calendar_days(
                raw_df, DATE_COL, RECENT_MOVERS_DAYS, reference=date.today()
            )

            # Skip entirely if no rows matched
            if filtered.empty:
                logger.info("Section 1 – '%s': no data in window, skipped.", sheet_name)
                continue

            # Keep Date, Ticker, T_, CT_, and RR (if present)
            always = [DATE_COL, TICKER_COL]
            subset = select_prefixed_columns(
                filtered,
                prefixes=[T_PREFIX, CT_PREFIX],
                always_include=always,
            )

            # Append RR column (1 decimal) when available
            if "RR" in filtered.columns:
                subset = subset.copy()
                subset["RR"] = filtered["RR"].map(
                    lambda v: f"{float(v):.1f}" if pd.notna(v) else ""
                )

            # Sort descending by date
            if DATE_COL in subset.columns:
                subset = subset.sort_values(DATE_COL, ascending=False).reset_index(drop=True)

            movers[sheet_name] = subset
            logger.info("Section 1 – '%s': %d rows.", sheet_name, len(subset))

        except Exception as exc:
            logger.error("Section 1 – error processing sheet '%s': %s", sheet_name, exc)

    # ------------------------------------------------------------------
    # Section 2 – Recent Sectors  (RR formatted to 1 decimal)
    # ------------------------------------------------------------------
    recent_sectors = pd.DataFrame()

    try:
        companies_df = read_sheet(MARKET_SENTIMENT_PATH, COMPANIES_SHEET)
        recent_sectors = build_recent_sectors(
            movers_frames=movers,
            movers_raw_sheets=all_sheets,
            companies_df=companies_df,
        )
        # Format RR to 1 decimal if the column exists
        if "RR" in recent_sectors.columns:
            recent_sectors["RR"] = recent_sectors["RR"].map(
                lambda v: f"{float(v):.1f}" if pd.notna(v) else ""
            )
        logger.info("Section 2 – Recent Sectors: %d rows.", len(recent_sectors))
    except FileNotFoundError as exc:
        logger.error("Cannot read Trading Analytics: %s", exc)
    except KeyError as exc:
        logger.error("Section 2 – %s", exc)
    except Exception as exc:
        logger.error("Section 2 – unexpected error: %s", exc)

    # ------------------------------------------------------------------
    # Section 3 & 4 – Tendencies
    # ------------------------------------------------------------------
    tendencies_c = pd.DataFrame()
    tendencies_ranking = pd.DataFrame()
    tendencies_df_full: pd.DataFrame = pd.DataFrame()   # kept for green-highlight logic

    try:
        tendencies_raw = read_sheet(MARKET_SENTIMENT_PATH, TENDENCIES_SHEET)
        tendencies_df_full = build_tendencies_base(tendencies_raw)

        # B_ columns → Ranking only (no date table)
        b_cols = select_binary_columns(tendencies_df_full)
        if b_cols:
            tendencies_ranking = build_tendencies_ranking(
                tendencies_df_full, b_cols
            )
        else:
            logger.warning("Section 3 – no B_ columns passed the filter.")

        # C_ columns → detail table (no green highlight)
        c_cols = select_count_columns(tendencies_df_full)
        if c_cols:
            tendencies_c = build_tendencies_c_table(tendencies_df_full, c_cols)
        else:
            logger.warning("Section 3 – no C_ columns passed the filter.")

        logger.info(
            "Section 3 – B_ cols: %d, C_ cols: %d.", len(b_cols), len(c_cols)
        )

    except FileNotFoundError as exc:
        logger.error("Cannot read Trading Analytics (Tendencies): %s", exc)
    except KeyError as exc:
        logger.error("Section 3 – %s", exc)
    except Exception as exc:
        logger.error("Section 3 – unexpected error: %s", exc)

    # ------------------------------------------------------------------
    # Generate Report
    # ------------------------------------------------------------------
    try:
        report_data = ReportData(
            movers=movers,
            recent_sectors=recent_sectors,
            tendencies_ranking=tendencies_ranking,
            tendencies_ranking_source=tendencies_df_full,  # for latest-day green logic
            tendencies_c=tendencies_c,
        )
        output_path = generate_report(report_data)
        logger.info("=== Report generated successfully: %s ===", output_path)
    except Exception as exc:
        logger.error("Report generation failed: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
