---
description: Full trading notes workflow - parse, insert, and populate OHLCV
allowed-tools: Read, Edit, Bash(python3 insert_trading_notes.py:*), Bash(python3 populate_trading_research.py:*)
---

## Context

This is the complete trading notes workflow that combines:
1. `/trading-parse` - Parse Chinese trading notes
2. `/trading-insert` - Insert to Notion + Obsidian
3. `/trading-ohlcv` - Populate OHLCV data

## Input

The user will paste Chinese trading notes after this command.

## Workflow

### Step 1: Parse Notes

Extract timestamps from chat messages and parse following these rules:

**Timestamp Format**: `自由自在 — 12/24/25, 9:46 AM` -> `2025-12-24T09:46:00`

**Field Extraction**:
- **Resistance**: "阻力" + value/range
- **Support**: "支撑" + value/range
- **Buy Point**: "加仓", "可买", "到...加", "买"
- **Sell Point**: "止损", "减仓", "卖"
- **Ladder**: "突破", "站稳", "破...才", "趋势价格", "才有希望" (single number only)

**Ticker Mappings**: Tesla/特斯拉->$TSLA, Nvidia/英伟达->$NVDA, Meta->$META, MSTR->$MSTR (MicroStrategy), Crwv->$CRWD, etc.

### Step 2: Display for Confirmation

Output parsed data as ASCII box-drawing table:

```
┌────┬────────┬──────────────────┬───────────┬─────────┬───────────┬────────────┬────────┬───────────────────┐
│ #  │ Ticker │ Date/Time        │ Resistance│ Support │ Buy Point │ Sell Point │ Ladder │ Notes             │
├────┼────────┼──────────────────┼───────────┼─────────┼───────────┼────────────┼────────┼───────────────────┤
│ 1  │ $TSLA  │ 2025-12-24 09:30 │ 491-493   │ 484     │ -         │ -          │ -      │ 想冲491-493       │
└────┴────────┴──────────────────┴───────────┴─────────┴───────────┴────────────┴────────┴───────────────────┘
```

**STOP HERE** and ask user to confirm before proceeding.

### Step 3: Insert to Notion + Obsidian (after confirmation)

1. Read `/Users/yueqiu/rimu/notion/insert_trading_notes.py`
2. Update the entries list with parsed data:
```python
entries = [
    ("2025-12-24T09:30:00", "$TSLA", "491-493", "484", None, None, None, "Notes"),
    # ...
]
```
3. Run: `python3 insert_trading_notes.py`

### Step 4: Populate OHLCV Data

Run: `python3 populate_trading_research.py`

Report success/failure counts.

## Final Summary

After all steps complete, show:
```
┌─────────────────────────────────────────────────────────────┐
│                    SYNC COMPLETE                            │
├─────────────────────────────────────────────────────────────┤
│  Parsed:   X entries from Y unique tickers                  │
│  Inserted: X/X to Notion + Obsidian                         │
│  OHLCV:    X entries populated, Y skipped                   │
└─────────────────────────────────────────────────────────────┘
```
