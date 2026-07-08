# Market Sentiment Tendency Report


Automated report generator that analyzes trading data from Excel workbooks 
and generates a structured Microsoft Word (.docx) and PDF report summarizing 
market sentiment, recent movers, sector activity, and trading tendencies.

---

## Project Structure

```
Market_Sentiment_Tendency_Report/
│
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
├── Daily_Report_Template.docx
│
├── data_processing/
├── reporting/
├── utils/
│
├── Input_Example/
│   ├── Market_Sentiment_DB.xlsx
│   └── Strategy_Playbook_DB.xlsx
│
└── Output_Example/
    ├── Daily_Report_YYYY-MM-DD.docx
    ├── Daily_Report_YYYY-MM-DD.pdf
    └── run_YYYY-MM-DD.log
```

---

## Input Files

| Variable                   | Description            |
|----------------------------|------------------------|
| `Market_Sentiment_DB.xlsx` | `Tendences Data Base`  |
| `Strategy_Playbook_DB.xlsx` | `Strategies Data Base` |

## Configuration

Create a `.env` file in the project root.

Example:

```env
STRATEGY_PLAYBOOK_PATH=C:\...\Strategy_Playbook_DB.xlsx
MARKET_SENTIMENT_PATH=C:\...\Market_Sentiment_DB.xlsx
OUTPUT_DIR=C:\...\Reports
WORD_TEMPLATE_PATH=C:\...\Daily_Report_Template.docx
```

---

## Output Files

| File | Description |
|---|---|
| `Daily_Report_YYYY-MM-DD.docx` | Word report |
| `Daily_Report_YYYY-MM-DD.pdf` | PDF version (requires Microsoft Word or LibreOffice) |
| `run_YYYY-MM-DD.log` | Execution log |

---

## Setup

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt
```

> If Activate.ps1 is blocked by execution policy, run once:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## Usage

```powershell
python main.py
```

---

## Word Template

The file `Daily Report Template.docx` must remain in the project root.
It defines these paragraph styles used throughout the report:

| Style Name | Used for |
|---|---|
| `Title Rock` | Main report title |
| `Subtitle Rock` | Section headings |
| `Normal Trading Inform` | Body text |

---

## Report Sections

### 1 · Recent Movers
- Source: `Strategy_Playbook_DB.xlsx` — all sheets
- Window: **last 8 calendar days** from today (weekends and holidays included)
- Columns: `Date`, `Ticker`, all `T_` columns, all `CT_` columns, `RR` (1 decimal)
- Sheets with no rows in the window are silently omitted from the report

### 2 · Recent Sectors
- Source: `Trading_Analytics_DB.xlsx` — sheet `Companies`
- Join key: `Ticker`
- Columns: `Date`, `Ticker`, `Category/Industry`, `Subcategory`, `RR` (1 decimal)
- Sorted by `Date DESC`, duplicates removed

### 3 · Tendencies
- Source: `Trading_Analytics_DB.xlsx` — sheet `Tendencies`
- Window: **last 6 calendar days**
- Column selection window: **last 5 calendar days**
- **B_ columns** kept if at least one value == 1 in the selection window
- **C_ columns** kept if at least one value > 1 in the selection window
- Output: Ranking table (`Indicator`, `Count`) — green highlight when the
  indicator's value on the **most-recent date** is > 0

### 4 · Tendencies Detail
- C_ columns table: `Date` + selected `C_` columns
- Sorted by `Date DESC`
- No green highlighting

---

## PDF Conversion

The script attempts conversion in this order:

1. **LibreOffice** (`soffice`) — works on Windows, macOS, Linux
2. **Microsoft Word COM** (`comtypes`) — Windows only, fallback when LibreOffice is absent

If neither is available the `.docx` is still saved and a warning is logged.
Install LibreOffice: https://www.libreoffice.org

---

## Configuration Reference (`config.py`)

| Constant | Value | Description |
|---|---|---|
| `RECENT_MOVERS_DAYS` | 8 | Calendar-day window for Section 1 |
| `TENDENCIES_DAYS` | 6 | Calendar-day window for Tendencies sheet |
| `TENDENCIES_FILTER_DAYS` | 5 | Calendar-day window for B_/C_ column selection |
| `GREEN_FILL` | `C6EFCE` | Hex colour for green cell highlight |

---

## Dependencies (`requirements.txt`)

```
pandas
openpyxl
python-docx
comtypes
```

No version pins — install with `pip install -r requirements.txt`.

---

## Logging

Each run appends a timestamped log to `output/run_YYYY-MM-DD.log`.
Console shows INFO and above; the file captures DEBUG and above.
