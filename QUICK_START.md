# Notion Trading System - Quick Start

## Three Essential Scripts

### 1. `populate_trading_research.py`
**Purpose**: Fill empty Trading Research entries with previous day OHLCV data

**Usage**:
```bash
python3 populate_trading_research.py
```

**What it does**:
- Finds Trading Research entries with empty Prev. Close/High/Low/Volume fields
- Uses Date field to calculate previous trading day
- Fetches OHLCV data from Alpha Vantage + EODHD (with multi-key rotation)
- Fills in the data automatically

**When to use**: After manually creating new Trading Research entries

---

### 2. `insert_trading_notes.py`
**Purpose**: Insert manually parsed trading notes into Trading Research database

**Usage**:
1. Parse your Chinese notes manually or with Claude assistance
2. Edit the script to add your entries:
   ```python
   entries = [
       (date, ticker, resistance, support, buy_point, sell_point, ladder, notes),
       # ... more entries
   ]
   ```
3. Run:
   ```bash
   python3 insert_trading_notes.py
   ```

**When to use**: After parsing Chinese trading notes (see workflow below)

---

### 3. Trading Notes Parsing Workflow

**File**: `TRADING_NOTES_PARSER.md` (reference guide)

**Recommended Approach**: Manual parsing with Claude assistance

**Workflow**:
1. Share your Chinese trading notes with Claude in conversation
2. Claude parses following the rules in `TRADING_NOTES_PARSER.md`
3. Review Claude's parsed output
4. Manually insert to Notion OR use `insert_trading_notes.py`

**Why manual?** Testing showed Ollama automation has:
- 3+ minute processing time
- 85% accuracy (vs 95-100% manual)
- Merges entries incorrectly
- Not worth the tradeoff

---

## Typical Workflows

### Daily Trading Notes Entry
1. Get Chinese notes from your source
2. Share with Claude: "Please parse these trading notes"
3. Claude shows structured output
4. Manually create entries in Notion Trading Research
   - OR edit `insert_trading_notes.py` and run it
5. Run `python3 populate_trading_research.py` to fill OHLCV data

### Weekly Backfill
1. Run `python3 populate_trading_research.py`
2. Script finds all empty Trading Research entries
3. Fills previous day data automatically
4. Check success rate in output

---

## Files Structure

### Active Files (main directory)
- `populate_trading_research.py` - OHLCV data population
- `insert_trading_notes.py` - Manual insertion template
- `TRADING_NOTES_PARSER.md` - Parsing rules reference
- `CLAUDE.md` - Production system documentation
- `README.md` - Original comprehensive docs
- `.env` - API keys (NOTION_TOKEN, ALPHA_VANTAGE_KEY, EODHD_API_KEYS)

### Archive (testing/reference)
- `archive/` - Experimental scripts and comparison docs
  - Ollama automation attempt
  - Various parsing helpers
  - Analysis documents

---

## Quick Reference

### Database IDs
- Stocks: `20be24d8-7d14-818a-9586-e5478b4e6c18`
- Trading Research: `20be24d8-7d14-8129-975e-e2624faaaad9`

### API Keys Required
```bash
# .env file
NOTION_TOKEN=secret_xxx
ALPHA_VANTAGE_KEY=xxx
EODHD_API_KEYS=key1,key2,key3  # Comma-separated for rotation
```

### Common Issues
- "Entries needing data: 0" → Make sure Date and Stock 1 fields are filled
- ".SPX warnings" → Expected, these index entries can't be filled
- "402 error" → EODHD key exhausted, automatic rotation to next key

---

*Last Updated: 2025-11-26*
*System Status: Production Ready*
