# Alpha Vantage to Notion Trading System Integration

This integration automatically populates your Notion trading databases with real-time market data from Alpha Vantage, filling gaps in your current system with comprehensive fundamental and technical data.

## 🎯 What This Solves

Based on your current Notion setup, this integration addresses these gaps:

### Current Empty Fields in Your Stocks Database:
- ✅ **Stock Name** → Populated from company overview
- ✅ **Market Cap** → Formatted market capitalization 
- ✅ **P/E Ratio** → Current price-to-earnings ratio
- ✅ **Sector** → Industry sector classification

### Enhanced Trading Research Database:
- ✅ **Previous OHLC Data** → Daily open, high, low, close prices
- ✅ **Volume Data** → Trading volume information
- ✅ **Last API Fetch** → Automatic timestamp tracking
- ✅ **Automated Entries** → Daily market data entries

## 🚀 Features

### Efficient Batching System
- **Parallel Processing**: Simultaneous API calls for multiple stocks
- **Rate Limiting**: Respects Alpha Vantage (75/min) and Notion (3/sec) limits
- **Smart Scheduling**: Uses "Last API Fetch" field to avoid redundant calls

### Data Quality
- **No Overwriting**: Only fills empty fields, preserves your manual data
- **Error Handling**: Comprehensive logging and error recovery
- **Data Validation**: Ensures data integrity before Notion updates

### Comprehensive Market Data
- **Fundamental Data**: Company overview, financials, ratios
- **Price Data**: Daily OHLCV with 20+ years of history  
- **Technical Indicators**: Support/resistance level calculations
- **Market Intelligence**: News, sentiment, insider transactions

## 📋 Prerequisites

### 1. Alpha Vantage API Key
- Get your free API key: https://www.alphavantage.co/support/#api-key
- Free tier: 75 requests/minute, 500 requests/day
- Premium tiers available for higher limits

### 2. Notion Integration Token
- Create a Notion integration: https://www.notion.so/my-integrations
- Grant access to your trading workspace
- Copy the integration token

### 3. Python Environment
- Python 3.8+ required
- Virtual environment recommended

## ⚙️ Installation

### 1. Clone/Download Files
```bash
# Download the integration files to your workspace
# Files needed:
# - alpha_vantage_notion_integration.py
# - test_integration.py  
# - requirements.txt
# - README.md
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv alpha_vantage_env

# Activate environment
# On macOS/Linux:
source alpha_vantage_env/bin/activate
# On Windows:
alpha_vantage_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Test Your Setup
```bash
# Run comprehensive test suite
python test_integration.py
```

The test will guide you through:
- ✅ Alpha Vantage API connection
- ✅ Notion API access  
- ✅ Database permissions
- ✅ Sample data fetch

## 🔧 Configuration

### Update API Keys
Edit `alpha_vantage_notion_integration.py` and replace:

```python
# Configuration
ALPHA_VANTAGE_KEY = "your_actual_api_key_here"
NOTION_TOKEN = "your_notion_integration_token_here"
```

### Your Database IDs (Pre-configured)
- **Stocks Database**: `20be24d8-7d14-818a-9586-e5478b4e6c18`
- **Trading Research Database**: `20be24d8-7d14-8129-975e-e2624faaaad9`

## 🏃‍♂️ Usage

### Full System Update
```bash
# Run complete integration
python alpha_vantage_notion_integration.py
```

This will:
1. **Fetch all 55+ stocks** from your Notion database
2. **Batch fetch company overviews** (fills Stock Name, Market Cap, P/E, Sector)
3. **Update empty fields only** (preserves your existing data)
4. **Fetch daily price data** for all stocks
5. **Create trading research entries** with OHLCV data
6. **Log all activities** with success/failure tracking

### Selective Updates
```python
# Modify in main() function for custom runs:

# Only update fundamental data (no daily prices)
await integrator.run_full_update(
    update_fundamentals=True,
    update_daily_data=False
)

# Only fetch daily data (no fundamental updates)  
await integrator.run_full_update(
    update_fundamentals=False,
    update_daily_data=True
)
```

## 📊 Expected Results

### Stocks Database Updates
For each stock with empty fields:
```
$AAPL → Apple Inc. | Technology | $3.5T | 29.8
$NVDA → NVIDIA Corporation | Technology | $3.2T | 65.4
$TSLA → Tesla, Inc. | Consumer Cyclical | $800.1B | 85.2
```

### Trading Research Entries
Daily entries created with:
- **Date**: Latest trading day
- **Previous Close**: $182.31
- **Previous High**: $184.95
- **Previous Low**: $181.23  
- **Previous Volume**: 45,234,567
- **Last API Fetch**: 2025-01-07T10:30:00.000Z

## ⚡ Performance Specs

### Batch Processing Efficiency
- **55 stocks** (your current count)
- **11 batches** of 5 stocks each
- **Company overviews**: ~15 minutes (with rate limiting)
- **Daily data**: ~15 minutes (with rate limiting)  
- **Total runtime**: ~30-35 minutes

### Rate Limiting Strategy
```
Alpha Vantage: 75 requests/minute
├── Batch size: 5 stocks
├── Delay between batches: 4 seconds
└── Parallel within batch: Yes

Notion: 3 requests/second  
├── Update delay: 0.33 seconds
└── Sequential updates: Yes
```

## 🔍 Monitoring & Logs

### Log Output Example
```
2025-01-07 10:30:15 - INFO - Fetching all stocks from Notion...
2025-01-07 10:30:16 - INFO - Retrieved 55 stocks from Notion
2025-01-07 10:30:16 - INFO - Fetching company overview for 55 stocks...
2025-01-07 10:30:16 - INFO - Processing batch 1 (5 stocks)
2025-01-07 10:30:18 - INFO - ✓ Fetched overview for AAPL
2025-01-07 10:30:18 - INFO - ✓ Fetched overview for NVDA
...
2025-01-07 10:30:25 - INFO - ✓ Updated fundamentals for $AAPL
2025-01-07 10:30:26 - INFO - ⚬ No updates needed for $NVDA
```

### Error Handling
- **API Failures**: Logged but don't stop the process
- **Rate Limiting**: Automatic retry with exponential backoff
- **Invalid Tickers**: Skipped with warning logs
- **Notion Errors**: Individual stock failures logged

## 🛠️ Troubleshooting

### Common Issues

#### "API Error: Thank you for using Alpha Vantage!"
- **Cause**: Rate limit exceeded
- **Solution**: Wait 1 minute or get premium key

#### "Notion API Error: 400"
- **Cause**: Database permissions or invalid data
- **Solution**: Check integration has database access

#### "Failed to fetch overview for XYZ"
- **Cause**: Invalid ticker symbol or delisted stock
- **Solution**: Check ticker format, remove invalid stocks

### Debug Mode
Add this to enable verbose logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

### Phase 2 Features (Available)
- **Technical Indicators**: RSI, MACD, Bollinger Bands
- **News Integration**: Sentiment analysis and market news
- **Earnings Data**: EPS estimates and actual results
- **Options Data**: Put/call ratios and options flow

### Advanced Analytics
```python
# Add to your integration:
# - Insider trading notifications
# - Unusual volume alerts  
# - Sector rotation analysis
# - Portfolio correlation matrix
```

## 📈 Alpha Vantage API Reference

### Core APIs Used
- **Company Overview**: `/query?function=OVERVIEW`
- **Daily Adjusted**: `/query?function=TIME_SERIES_DAILY_ADJUSTED` 
- **Global Quote**: `/query?function=GLOBAL_QUOTE` (for testing)

### Available Extensions
- **Intraday Data**: 1min, 5min, 15min, 30min, 60min intervals
- **Technical Indicators**: 30+ indicators available
- **Fundamental Data**: Income statements, balance sheets, cash flow
- **Market Intelligence**: News, earnings, insider transactions

## 🤝 Support

### Getting Help
1. **Test First**: Always run `test_integration.py`
2. **Check Logs**: Review console output for specific errors
3. **API Limits**: Monitor your Alpha Vantage usage
4. **Backup Data**: Notion automatically backs up, but consider exports

### Contributing
This integration can be extended for:
- Additional data sources (Yahoo Finance, IEX Cloud)
- Custom technical indicators
- Portfolio analysis features
- Automated trading signals

---

## 🎉 Ready to Run?

1. **Get your API keys** (Alpha Vantage + Notion)
2. **Run the test**: `python test_integration.py`
3. **Update the config** in `alpha_vantage_notion_integration.py`
4. **Execute full update**: `python alpha_vantage_notion_integration.py`
5. **Monitor your Notion** as data populates!

Your sophisticated trading system is about to get a major upgrade with real-time market intelligence! 🚀📊 

## 🪜 The Ladder Column

### What is the Ladder Column?
The Ladder column is a numeric field with Dollar as the unit, added to the Trading Research database. It can be used for:
- Position sizing calculations
- Risk management levels
- Price targets
- Capital allocation amounts

### Adding the Ladder Column

To add the Ladder column to your Trading Research database:

```bash
# Set your Notion token as an environment variable
export NOTION_TOKEN="your_notion_integration_token"

# Run the script to add the column
python add_ladder_column.py
```

### Testing the Ladder Column

To verify the column was added correctly and test setting values:

```bash
# Make sure your Notion token is set
export NOTION_TOKEN="your_notion_integration_token"

# Run the test script
python test_add_ladder_column.py
```

The test script will:
1. Verify the column exists with the correct configuration
2. Update a few recent entries with test values
3. Create a new test entry with a Ladder value

### Using the Ladder Column in Your Workflow

The Ladder column is designed to be set manually in most cases, but you can also:

- Set it programmatically using the Notion API
- Include it in your trading strategy scripts
- Use it for position sizing calculations based on risk parameters

Example for position sizing calculation:
```python
# Position sizing based on risk percentage
account_size = 10000
risk_percentage = 0.01  # 1% risk
stop_price = 95
entry_price = 100

# Calculate position size
risk_amount = account_size * risk_percentage
shares = risk_amount / (entry_price - stop_price)
ladder_value = shares * entry_price

# This is what you would set in the Ladder column
print(f"Ladder value: ${ladder_value:.2f}")
``` 