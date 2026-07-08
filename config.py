"""
config.py
---------
Central configuration for the Market Sentiment Tendency Report.
All paths, constants, and settings are defined here.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

# Load .env
load_dotenv()

# ---------------------------------------------------------------------------
# Input file paths
# ---------------------------------------------------------------------------

STRATEGY_PLAYBOOK_PATH = Path(os.getenv("STRATEGY_PLAYBOOK_PATH"))

MARKET_SENTIMENT_PATH = Path(os.getenv("MARKET_SENTIMENT_PATH"))

# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR"))

# ---------------------------------------------------------------------------
# Word template path
# ---------------------------------------------------------------------------

WORD_TEMPLATE_PATH = Path(os.getenv("WORD_TEMPLATE_PATH"))

# ---------------------------------------------------------------------------
# Section 1 – Recent Movers
# ---------------------------------------------------------------------------

RECENT_MOVERS_DAYS: int = 8
TICKER_COL: str = "Ticker"
DATE_COL: str = "Date"
T_PREFIX: str = "T_"
CT_PREFIX: str = "CT_"

# ---------------------------------------------------------------------------
# Section 2 – Recent Sectors
# ---------------------------------------------------------------------------

COMPANIES_SHEET: str = "Companies"
CATEGORY_COL: str = "Category/Industry"
SUBCATEGORY_COL: str = "Subcategory"

# ---------------------------------------------------------------------------
# Section 3 & 4 – Tendencies
# ---------------------------------------------------------------------------

TENDENCIES_SHEET: str = "Tendencies"
TENDENCIES_DAYS: int = 6
TENDENCIES_FILTER_DAYS: int = 5

# ---------------------------------------------------------------------------
# Column prefixes
# ---------------------------------------------------------------------------

B_PREFIX: str = "B_"
C_PREFIX: str = "C_"

# ---------------------------------------------------------------------------
# Word style names
# ---------------------------------------------------------------------------

STYLE_TITLE: str = "Title Rock"
STYLE_SUBTITLE: str = "Subtitle Rock"
STYLE_NORMAL: str = "Normal Trading Inform"

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

GREEN_FILL: str = "C6EFCE"