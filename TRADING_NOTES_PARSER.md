# Trading Notes Parser Guide

## Overview
This document contains the knowledge and rules for parsing raw Chinese trading notes into structured Trading Research database entries.

## Database Schema

### Trading Research Table Columns
- **Date**: Reference datetime (format: YYYY-MM-DDTHH:MM:SS for timestamp precision, or YYYY-MM-DD for date only)
- **Stock 1**: Relation field linking to Stocks database (ticker format: `$TSLA`)
- **Resistance**: Rich text field (numeric values or ranges like "410" or "603-606")
- **Support**: Rich text field (numeric values or ranges)
- **Buy Point**: Rich text field (numeric values or ranges)
- **Sell Point**: Rich text field (numeric values or ranges)
- **Ladder**: Number field (single numeric value only - for trend/breakout prices)
- **Notes**: Title field (raw Chinese notes, no translation needed)
- **Prev. Close/High/Low/Volume**: Previous day OHLCV data (populated by separate script)

## Parsing Rules

### 1. Ticker Format
- All tickers must be in `$SYMBOL` format (e.g., `$TSLA`, `$NVDA`, `$META`)
- Remove any Chinese characters, keep only the ticker symbol with `$` prefix

### 2. Resistance (阻力)
- Keywords: "阻力"
- Extract numeric values following the keyword
- Can be single value (e.g., "410") or range (e.g., "603-606", "180.5-181.88")
- Store as string in Resistance column
- Example: "阻力410" → Resistance: "410"
- Example: "阻力603-606" → Resistance: "603-606"

### 3. Support (支撑)
- Keywords: "支撑"
- Extract numeric values following the keyword
- Can be single value or range
- Store as string in Support column
- Example: "支撑594-596" → Support: "594-596"
- Example: "支撑69" → Support: "69"

### 4. Buy Point (加仓点位)
- Keywords: "加仓", "可买", "到...加"
- Extract the price level mentioned for adding positions
- Can be single value or range
- Store as string in Buy Point column
- Example: "如果到168.88加一仓" → Buy Point: "168.88"
- Example: "到193-195加仓" → Buy Point: "193-195"
- Example: "到166-167可买" → Buy Point: "166-167"

### 5. Sell Point (止损/减仓点位)
- Keywords: "止损", "减仓", "设止损"
- Extract the price level for stop loss or reducing position
- Usually a single value
- Store as string in Sell Point column
- Example: "设止损165.4" → Sell Point: "165.4"
- Note: "减仓" without specific price doesn't go in Sell Point

### 6. Ladder (趋势价格/突破价格)
- **Most important rule**: This is for TREND or BREAKTHROUGH prices only
- Keywords: "趋势价格", "突破", "站稳", "破", "才考虑", "才有希望"
- Must be a single numeric value (NOT a range)
- Store as number in Ladder column
- Examples:
  - "趋势价格422" → Ladder: 422
  - "不突破414是反弹" → Ladder: 414 (breakthrough threshold)
  - "突破184才有希望" → Ladder: 184
  - "突破294会涨" → Ladder: 294
  - "破450才考虑" → Ladder: 450
  - "反转价格30.6" → Ladder: 30.6
  - "看能不能站稳17.3" → Ladder: 17.3
  - "8.28-8.38突破就有希望8.6" → Ladder: 8.6 (the target after breakthrough)
  - "如果不突破1.12，减仓" → Ladder: 1.12 AND Resistance: 1.12

### 7. Notes Field
- Always include the ORIGINAL Chinese text
- NO translation needed
- Keep all context and details
- This is the title field of the entry

### 8. Timestamp Extraction from Chat Messages
- **Key Rule**: Use timestamps from chat messages to create time-specific entries
- Discord/chat timestamps appear in format: `username — MM/DD/YY, HH:MM AM/PM`
- Example: `自由自在 — 12/24/25, 9:46 AM` → `2025-12-24T09:46:00`
- Convert to ISO format: `YYYY-MM-DDTHH:MM:SS`
- If no timestamp visible for first block, estimate based on market context (e.g., 09:30 for market open)
- **Important**: When the same stock is mentioned at DIFFERENT timestamps, create SEPARATE entries
- This allows tracking how advice evolves throughout the trading day

### 9. Multiple Updates for Same Stock
- **Key Rule**: If a stock is mentioned in DIFFERENT blocks/paragraphs with different timestamps, create SEPARATE entries
- Each mention represents a different update or timepoint
- Example:
  ```
  自由自在 — 12/24/25, 9:30 AM
  特斯拉支撑484

  自由自在 — 12/24/25, 9:46 AM
  特斯拉484破了
  下一个支撑479
  ```
  This creates TWO separate entries for $TSLA:
  - Entry 1: 2025-12-24T09:30:00, Support: 484
  - Entry 2: 2025-12-24T09:46:00, Support: 479

### 10. Edge Cases

#### Case 1: Stocks to ignore
- If note says "不动它" (don't touch it), still create an entry with just the note
- Example: "Amzu 不动它" → Create entry with Notes only

#### Case 2: General observations without specific levels
- If no specific price levels mentioned, just put in Notes
- Example: "无论怎么走，大概率要再测试83-84" → Notes only (no columns filled)

#### Case 3: Price mentioned as already bought
- "25.88买的" → Buy Point: "25.88"
- This indicates an executed buy, still record in Buy Point

#### Case 4: Ranges in numeric fields
- Resistance, Support, Buy Point, Sell Point can all accept ranges like "603-606"
- Ladder must be single number - if range given for breakthrough, pick the higher end

#### Case 5: Multiple resistance or support levels
- If multiple levels mentioned in same note, use range format
- "阻力180.5-181.88" → Resistance: "180.5-181.88"

## Complete Prompt for Parsing

Use this prompt when you need to parse trading notes:

---

**PROMPT START**

You are parsing Chinese trading notes into structured Trading Research database entries. Follow these rules exactly:

**INPUT FORMAT**: Raw Chinese text with stock tickers and trading information

**OUTPUT FORMAT**: Structured entries with these fields:
- Date/Time: YYYY-MM-DDTHH:MM:SS (extracted from chat timestamps) or YYYY-MM-DD if no time available
- Ticker: $SYMBOL format
- Resistance: String (numeric values or ranges like "410" or "603-606")
- Support: String (numeric values or ranges)
- Buy Point: String (numeric values or ranges)
- Sell Point: String (numeric values or ranges)
- Ladder: Single number only (for trend/breakthrough prices)
- Notes: Original Chinese text (NO translation)

**PARSING RULES**:

1. **Ticker Identification**:
   - CRITICAL: Only create ONE entry per stock ticker per logical note block
   - If the same stock is mentioned multiple times in close proximity (within 3-5 lines), COMBINE into ONE entry
   - Only create separate entries if the stock is mentioned in clearly different contexts or time references
   - Common ticker names to recognize (case-insensitive):
     * Tesla/特斯拉 → $TSLA
     * Nvidia/英伟达 → $NVDA
     * Meta → $META
     * Amazon/Amzu → $AMZN
     * Google/Goog → $GOOG
     * Microsoft/Mstr → $MSTR (be careful: MSTR is MicroStrategy, not Microsoft)
     * Oracle/Orcl → $ORCL
     * CrowdStrike/Crwv → $CRWD
     * Circle/Crcl → $CRCL
     * SoundHound/Soun → $SOUN (NOT $SONY)
     * Opad → $OPAD (NOT $OSRD)
     * VST → $VST
     * OSCR → $OSCR

2. **Resistance (阻力)**: Extract values after "阻力". Can be single or range.

3. **Support (支撑)**: Extract values after "支撑". Can be single or range.

4. **Buy Point**: Keywords "加仓", "可买", "到...加", "买的". Can be single or range.

5. **Sell Point**: Keywords "止损", "减仓" (with specific price). Can be single or range.

6. **Ladder (MOST IMPORTANT)**:
   - For TREND prices: "趋势价格"
   - For BREAKTHROUGH prices: "突破", "站稳", "破...才", "反转价格"
   - Target prices after breakthrough: "突破...就有希望[X]" → Ladder is X
   - Must be single number (NOT range)
   - Examples:
     * "趋势价格422" → Ladder: 422
     * "不突破414" → Ladder: 414
     * "突破294会涨" → Ladder: 294
     * "破450才考虑" → Ladder: 450
     * "站稳17.3" → Ladder: 17.3
     * "不突破1.12，减仓" → Ladder: 1.12 (also Resistance: 1.12)

7. **CRITICAL - Avoid Duplicates**:
   - Before creating an entry, check if you already created one for this ticker
   - If multiple pieces of information for same stock appear together, MERGE into ONE entry
   - Only create separate entries if clearly different time contexts (e.g., "昨天" vs "今天")

8. **Notes Field**: Always include original Chinese text, no translation. Combine related notes if merging entries.

9. **Numeric Fields**: Only include raw numeric values or ranges (e.g., "410", "603-606"). No words or descriptions.

10. **Empty Fields**: Use `-` or leave empty if no data for that field.

**OUTPUT FORMAT**:
**IMPORTANT**: Always present the final output as an **ASCII box-drawing table** for easy visualization. Include Date/Time column with timestamps extracted from chat messages.

Present as an ASCII table with these columns:

```
┌────┬────────┬──────────────────┬───────────┬─────────┬───────────┬────────────┬────────┬─────────────────────────────────────────┐
│ #  │ Ticker │ Date/Time        │ Resistance│ Support │ Buy Point │ Sell Point │ Ladder │ Notes                                   │
├────┼────────┼──────────────────┼───────────┼─────────┼───────────┼────────────┼────────┼─────────────────────────────────────────┤
│ 1  │ $TSLA  │ 2025-12-24 09:30 │ 491-493   │ 484     │ -         │ -          │ -      │ 想冲491-493。今天的支撑是484            │
│ 2  │ $TSLA  │ 2025-12-24 09:46 │ -         │ 479     │ -         │ -          │ -      │ 484破了，下一个支撑479                  │
│ 3  │ $NVDA  │ 2025-12-24 09:30 │ 197       │ -       │ -         │ -          │ 197    │ 只有突破197，震荡才会结束               │
└────┴────────┴──────────────────┴───────────┴─────────┴───────────┴────────────┴────────┴─────────────────────────────────────────┘
```

**Key formatting rules**:
- Use box-drawing characters: `┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ │ ─`
- Date/Time column shows timestamp extracted from chat (format: YYYY-MM-DD HH:MM)
- Same stock can have multiple rows if mentioned at different timestamps
- Notes column truncated for display but full text used in insertion
- Use `-` for empty fields

**Note on comprehensive notes**: Always include ALL context mentioned about a stock for that specific timestamp.

Now parse the provided trading notes following these rules exactly.

**PROMPT END**

---

## Common Mistakes to Avoid

1. ❌ **Don't translate Notes field** - Keep original Chinese
2. ❌ **Don't put ranges in Ladder** - Ladder must be single number
3. ❌ **Don't combine multiple stock mentions** - Create separate entries
4. ❌ **Don't put words in numeric fields** - Only numbers or ranges like "410", "603-606"
5. ❌ **Don't miss breakthrough prices** - "突破X" means X goes in Ladder
6. ❌ **Don't ignore "才" keywords** - "破450才考虑" means Ladder is 450
7. ❌ **Don't forget trend prices** - "趋势价格" always goes to Ladder
8. ❌ **Don't put target prices in wrong column** - "突破X希望Y" → Ladder is Y (the target)

## Example Parsing

### Input:
```
特斯拉阻力410
不突破414，是反弹
Nvda 阻力180.5-181.88
如果到168.88，加一仓
Mstr 突破184，才有希望
它的支撑，以166为参考
到了166-167都可以买，设止损165.4
```

### Output:
```
1. $TSLA - Entry 1
   - Resistance: 410
   - Support: -
   - Buy Point: -
   - Sell Point: -
   - Ladder: 414
   - Notes: "阻力410。不突破414是反弹"

2. $NVDA
   - Resistance: 180.5-181.88
   - Support: -
   - Buy Point: 168.88
   - Sell Point: -
   - Ladder: -
   - Notes: "阻力180.5-181.88。如果到168.88加一仓"

3. $MSTR
   - Resistance: 184
   - Support: 166
   - Buy Point: 166-167
   - Sell Point: 165.4
   - Ladder: -
   - Notes: "突破184，才有希望。它的支撑，以166为参考。到了166-167都可以买，设止损165.4"
```

### Why these choices?
- **TSLA Entry 1**: "不突破414" indicates 414 is the breakthrough threshold → Ladder
- **NVDA**: "阻力180.5-181.88" is range → Resistance, "168.88加一仓" → Buy Point
- **MSTR**: "突破184" is resistance level (not breakthrough target, no "才有希望" after it), "166为参考" is support, "166-167可买" is buy point, "止损165.4" is sell point

## Script Usage

After parsing the notes, use the `insert_trading_notes.py` script template:

```python
entries = [
    # Format: (datetime, ticker, resistance, support, buy_point, sell_point, ladder, notes)
    ("2025-12-24T09:30:00", "$TSLA", "491-493", "484", None, None, None, "想冲491-493。今天的支撑是484"),
    ("2025-12-24T09:46:00", "$TSLA", None, "479", None, None, None, "484破了，下一个支撑479"),
    ("2025-12-24T09:30:00", "$NVDA", "197", None, None, None, 197, "只有突破197，震荡才会结束"),
    # ... more entries
]
```

**Date/Time format**: Use ISO format `YYYY-MM-DDTHH:MM:SS` for timestamp precision.

Then run:
```bash
python3 insert_trading_notes.py
```

## Keywords Reference

### Chinese Keywords and Their Meanings

| Chinese | English | Column Mapping |
|---------|---------|----------------|
| 阻力 | Resistance | → Resistance |
| 支撑 | Support | → Support |
| 加仓 | Add position | → Buy Point |
| 可买 | Can buy | → Buy Point |
| 止损 | Stop loss | → Sell Point |
| 减仓 | Reduce position | → Sell Point |
| 趋势价格 | Trend price | → Ladder |
| 突破 | Break through | → Ladder (if target) |
| 站稳 | Stabilize | → Ladder |
| 破 | Break | → Ladder |
| 反转价格 | Reversal price | → Ladder |
| 才有希望 | Then have hope | → Indicates Ladder target |
| 才考虑 | Then consider | → Indicates Ladder |
| 不动 | Don't touch | → Notes only |
| 震荡 | Oscillate | → Notes only |
| 财报 | Earnings | → Notes only |
| 长拿 | Long hold | → Notes only |

---

*Last Updated: 2025-01-08*
*This guide is based on actual parsing experience and tested patterns.*
*Updates: Added timestamp extraction from chat messages, ASCII box-drawing table output format.*
