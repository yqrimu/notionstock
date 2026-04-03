---
description: Insert parsed trading notes into Notion and Obsidian
allowed-tools: Read, Edit, Bash(python3 insert_trading_notes.py:*)
---

## Context

- Current entries in script: !`grep -c "^\s*(" /Users/yueqiu/rimu/notion/insert_trading_notes.py 2>/dev/null || echo "0"`
- Script location: `/Users/yueqiu/rimu/notion/insert_trading_notes.py`

## Prerequisites

This command should be run AFTER `/trading-parse` has been used to parse notes and the user has confirmed the parsed data.

The parsed data should be available from the previous conversation context as an ASCII table.

## Your Task

1. **Read** the current `insert_trading_notes.py` to understand the format
2. **Update** the entries list in `insert_trading_notes.py` with the parsed data from the previous `/trading-parse` output
3. **Run** the script: `python3 insert_trading_notes.py`
4. **Report** results showing:
   - Number of entries inserted
   - Any failures
   - Suggestion to run `/trading-ohlcv` to populate OHLCV data

## Entry Format

```python
entries = [
    # Format: (datetime, ticker, resistance, support, buy_point, sell_point, ladder, notes)
    ("2025-12-24T09:30:00", "$TSLA", "491-493", "484", None, None, None, "Notes here"),
    # ...
]
```

## Important Notes

- Use `None` for empty fields (not "-" or empty string)
- Ladder must be a number (int or float), not string
- Date format: `YYYY-MM-DDTHH:MM:SS`
- Ticker format: `$SYMBOL` (with dollar sign)

## Handling "Stock not found" Failures

When the script reports `✗ Stock $XYZ not found in Stocks database`, the ticker is missing from the Stocks database. Fix it inline without re-running the full script:

```python
import os, requests
from dotenv import load_dotenv
from obsidian_sync import ObsidianWriter
load_dotenv()

headers = {
    "Authorization": f"Bearer {os.getenv('NOTION_TOKEN')}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

obsidian_writer = ObsidianWriter(
    stocks_path=os.getenv('OBSIDIAN_STOCKS_PATH'),
    trading_research_path=os.getenv('OBSIDIAN_TRADING_RESEARCH_PATH')
)

# 1. Create the missing stock entry in Notion
ticker = "$XYZ"
resp = requests.post(
    "https://api.notion.com/v1/pages",
    headers=headers,
    json={
        "parent": {"database_id": "20be24d8-7d14-818a-9586-e5478b4e6c18"},
        "properties": {
            "Ticker": {"title": [{"text": {"content": ticker}}]},
            "Stock Name": {"rich_text": [{"text": {"content": ticker.replace("$", "")}}]}
        }
    }
)
stock_id = resp.json()["id"]

# 2. Create the corresponding Obsidian file in Stocks List/Entries (NOT Inbox)
obsidian_writer.write_stock_entry(
    ticker=ticker,
    notion_id=stock_id,
    properties={"stock_name": ticker.replace("$", "")}
)

# 3. Then insert the trading research entry using create_trading_research_entry() from the script
```

After creating the stock, call `create_trading_research_entry()` with the original entry data to insert it into both Notion and Obsidian.

**Rule**: For each `✗ Stock $XYZ not found` line in the output, create the stock first (including the Obsidian file), then re-insert that specific entry. Do not re-run the entire script.
