"""
data_processing/excel_reader.py
---------------------------------
Low-level helpers for reading Excel workbooks with openpyxl / pandas.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
logger = get_logger(__name__)


def read_all_sheets(path: Path) -> dict[str, pd.DataFrame]:
    """Read every sheet from an Excel workbook.

    Parameters
    ----------
    path:
        Absolute or relative path to the ``.xlsx`` file.

    Returns
    -------
    dict[str, pd.DataFrame]
        Mapping of sheet name → DataFrame.

    Raises
    ------
    FileNotFoundError
        When *path* does not point to an existing file.
    ValueError
        When the workbook contains no sheets.
    """
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    logger.info("Reading all sheets from '%s'", path.name)
    sheets: dict[str, pd.DataFrame] = pd.read_excel(
        path, sheet_name=None, engine="openpyxl"
    )

    if not sheets:
        raise ValueError(f"Workbook '{path.name}' contains no sheets.")

    logger.debug("Found sheets: %s", list(sheets.keys()))
    return sheets


def read_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    """Read a single sheet from an Excel workbook.

    Parameters
    ----------
    path:
        Absolute or relative path to the ``.xlsx`` file.
    sheet_name:
        Exact name of the target sheet.

    Returns
    -------
    pd.DataFrame

    Raises
    ------
    FileNotFoundError
        When *path* does not exist.
    KeyError
        When *sheet_name* is not present in the workbook.
    """
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")

    try:
        logger.info("Reading sheet '%s' from '%s'", sheet_name, path.name)
        df: pd.DataFrame = pd.read_excel(
            path, sheet_name=sheet_name, engine="openpyxl"
        )
        logger.debug("Shape: %s", df.shape)
        return df
    except Exception as exc:
        raise KeyError(
            f"Sheet '{sheet_name}' not found in '{path.name}'. Original error: {exc}"
        ) from exc


def select_prefixed_columns(
    df: pd.DataFrame,
    prefixes: list[str],
    always_include: list[str] | None = None,
) -> pd.DataFrame:
    """Return a DataFrame keeping only columns that start with any of *prefixes*,
    plus any column listed in *always_include*.

    Parameters
    ----------
    df:
        Source DataFrame.
    prefixes:
        List of column-name prefixes to match (case-sensitive).
    always_include:
        Extra column names to always include (e.g. ``["Date", "Ticker"]``).

    Returns
    -------
    pd.DataFrame
        Subset of *df* with columns in their original order.
    """
    always_include = always_include or []
    prefixed = [c for c in df.columns if any(c.startswith(p) for p in prefixes)]
    keep = [c for c in always_include if c in df.columns] + prefixed

    missing_always = [c for c in always_include if c not in df.columns]
    if missing_always:
        logger.warning("Columns not found and skipped: %s", missing_always)

    # Preserve original column order while deduplicating
    seen: set[str] = set()
    ordered: list[str] = []
    for col in df.columns:
        if col in keep and col not in seen:
            ordered.append(col)
            seen.add(col)

    return df[ordered].copy()
