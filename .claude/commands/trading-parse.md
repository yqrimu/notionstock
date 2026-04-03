---
description: Parse Chinese trading notes into structured entries with timestamp extraction
---

## Context

You are parsing Chinese trading notes for the Notion Trading Research database.

## Critical Rules

1. **DO NOT map or "correct" tickers** - The user trades 2x ETFs (MSFL, OKLL, QUBX, CWVX, ORCX, AMDL, TSLL, etc.). Keep tickers EXACTLY as written.
2. **Include MAXIMUM note content** - Do not summarize. Preserve full context, advice, reasoning, and commentary.

## Input

The user will paste Chinese trading notes after this command. The notes may contain Discord timestamps in format: `username - MM/DD/YY, HH:MM AM/PM`

## Parsing Rules

### Timestamp Extraction
- Extract timestamps from chat messages (e.g., `自由自在 — 12/24/25, 9:46 AM` -> `2025-12-24T09:46:00`)
- Convert MM/DD/YY to YYYY-MM-DD (add 2000 to YY)
- Convert 12-hour time to 24-hour format
- If no timestamp for first block, estimate as 09:30 (market open)

### Ticker Identification

**IMPORTANT: Do NOT map or "correct" tickers. Keep them exactly as written.**

The user trades many 2x leveraged ETFs and alternative tickers. Examples of VALID tickers (do not change these):
- $MSFL (Microsoft 2x) - NOT $MSFT
- $OKLL (Oklo 2x) - NOT $OKLO
- $QUBX (Quantum 2x) - NOT $QUBT
- $CWVX (CrowdStrike 2x) - NOT $CRWD
- $ORCX (Oracle 2x) - NOT $ORCL
- $AMDL (AMD 2x) - NOT $AMD
- $TSLL (Tesla 2x) - NOT $TSLA
- $CRCL, $CRCG, $PLTU, $USAR, $INTW, $METU, $FIG, $ASST, etc.

Only map Chinese names to tickers:
- 特斯拉 -> $TSLA
- 英伟达 -> $NVDA
- 苹果 -> $AAPL
- 微软 -> $MSFT
- 亚马逊 -> $AMZN
- 谷歌 -> $GOOG

For English ticker names: Use EXACTLY as written (case-insensitive for matching, but output as uppercase with $ prefix)

### Field Extraction

**Resistance (阻力)**: Keywords "阻力". Can be single value or range (e.g., "410", "603-606")

**Support (支撑)**: Keywords "支撑". Can be single value or range.

**Buy Point**: Keywords "加仓", "可买", "到...加", "买的", "买".
- MUST be numeric price only (e.g., "66.58", "3.98-4.28")
- If no specific price mentioned, leave as "-"
- Do NOT include words like "加一单", "买一单", "接回" - those go in Notes only

**Sell Point**: Keywords "止损", "减仓", "卖".
- MUST be numeric price only (e.g., "0.95", "5.3")
- If no specific price mentioned, leave as "-"
- Do NOT include words like "减仓", "有利减仓" - those go in Notes only

**Ladder** (MOST IMPORTANT - breakthrough/trend prices):
- Keywords: "趋势价格", "突破", "站稳", "破...才", "反转价格", "才有希望", "才考虑"
- Must be single number (NOT range)
- Examples:
  - "只有突破197，震荡才会结束" -> Ladder: 197
  - "站稳348.5" -> Ladder: 348.5
  - "不跌破36，基本就是走出来了" -> Ladder: 36
  - "第二次想突破320，过不了" -> Ladder: 320

**Notes**: Original Chinese text, no translation. **INCLUDE AS MUCH CONTENT AS POSSIBLE.**
- Do NOT summarize or condense - preserve the full context
- Include all advice, reasoning, warnings, and market commentary
- Combine all related sentences from the same timestamp block
- Keep original phrasing and expressions
- The goal is to capture maximum information, not to be concise

### Multiple Entries
- Same stock at DIFFERENT timestamps = SEPARATE entries
- Same stock in same timestamp block = MERGE into one entry

## Output Format

Output as ASCII box-drawing table:

```
┌────┬────────┬──────────────────┬───────────┬─────────────┬───────────┬────────────┬────────┬──────────────────────────────────────────────────────────────────────────────┐
│ #  │ Ticker │ Date/Time        │ Resistance│ Support     │ Buy Point │ Sell Point │ Ladder │ Notes                                                                        │
├────┼────────┼──────────────────┼───────────┼─────────────┼───────────┼────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
│ 1  │ $TSLA  │ 2025-12-24 09:30 │ 491-493   │ 484         │ -         │ -          │ -      │ 想冲491-493，今天有财报我倒希望它能财报后先来一个大跌，但今天走法是多头的走法，支撑484 │
│ 2  │ $MSTR  │ 2025-12-24 09:46 │ 166-168   │ -           │ -         │ -          │ 175    │ 一直在洗盘，给我它时间，今天的阻力166-168，突破175才有机会                   │
└────┴────────┴──────────────────┴───────────┴─────────────┴───────────┴────────────┴────────┴──────────────────────────────────────────────────────────────────────────────┘
```

After displaying the table:
1. Show total entry count and unique ticker count
2. Ask user to confirm before proceeding to insertion

## Your Task

Parse the trading notes provided by the user following these rules exactly. Output the ASCII table for review.
