#!/usr/bin/env python3
"""
Populate empty fields in Stocks database using Alpha Vantage and EODHD APIs.

Prioritizes entries with absolutely zero data (all fields empty).
Uses dual API support: Alpha Vantage (primary) + EODHD (backup) with multi-key rotation.

Usage: python3 populate_empty_stocks.py

Features:
- Prioritizes entries with zero data (all optional fields empty)
- Dual API support with automatic fallback
- Multi-key EODHD rotation when daily limits hit
- Smart sector mapping to Notion select options
- Formatted market cap and P/E ratio values
"""

import requests
import os
import time
import logging
from dotenv import load_dotenv
from obsidian_sync import ObsidianWriter

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')

# Load multiple EODHD API keys for rotation
eodhd_keys_str = os.getenv('EODHD_API_KEYS', os.getenv('EODHD_API_KEY', ''))
EODHD_API_KEYS = [key.strip() for key in eodhd_keys_str.split(',') if key.strip()]
current_eodhd_key_index = 0
exhausted_eodhd_keys = set()

STOCKS_DB_ID = '20be24d8-7d14-818a-9586-e5478b4e6c18'

# Notion headers
headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

# Initialize Obsidian writer
obsidian_writer = ObsidianWriter(
    stocks_path=os.getenv('OBSIDIAN_STOCKS_PATH'),
    trading_research_path=os.getenv('OBSIDIAN_TRADING_RESEARCH_PATH')
)

# API usage tracking
alpha_vantage_calls = 0
eodhd_calls = 0
ALPHA_VANTAGE_LIMIT = 25

def get_current_eodhd_key():
    """Get the current active EODHD API key"""
    if not EODHD_API_KEYS:
        return None

    # Find next non-exhausted key
    for _ in range(len(EODHD_API_KEYS)):
        key_index = current_eodhd_key_index % len(EODHD_API_KEYS)
        key = EODHD_API_KEYS[key_index]

        if key not in exhausted_eodhd_keys:
            return key

    # All keys exhausted
    return None

def rotate_eodhd_key():
    """Rotate to the next EODHD API key"""
    global current_eodhd_key_index

    if not EODHD_API_KEYS:
        return

    current_key = EODHD_API_KEYS[current_eodhd_key_index % len(EODHD_API_KEYS)]
    exhausted_eodhd_keys.add(current_key)
    current_eodhd_key_index += 1

    next_key = get_current_eodhd_key()
    if next_key:
        logging.info(f"Rotating EODHD API key (exhausted {len(exhausted_eodhd_keys)}/{len(EODHD_API_KEYS)} keys)")
    else:
        logging.warning("All EODHD API keys have been exhausted for today")

def clean_ticker(ticker):
    """Remove $ prefix from ticker for API calls."""
    return ticker.replace('$', '').strip()

def get_alpha_vantage_overview(symbol):
    """Get stock overview from Alpha Vantage."""
    global alpha_vantage_calls

    if alpha_vantage_calls >= ALPHA_VANTAGE_LIMIT:
        return None

    url = f'https://www.alphavantage.co/query'
    params = {
        'function': 'OVERVIEW',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        alpha_vantage_calls += 1

        if response.status_code == 200:
            data = response.json()
            if 'Symbol' in data:  # Valid response
                return data
            else:
                logging.warning(f"Alpha Vantage - No overview data for {symbol}")
        else:
            logging.error(f"Alpha Vantage API error for {symbol}: {response.status_code}")
    except Exception as e:
        logging.error(f"Alpha Vantage request failed for {symbol}: {str(e)}")

    return None

def get_eodhd_fundamentals(symbol):
    """Get stock fundamentals from EODHD with multi-key rotation."""
    global eodhd_calls

    api_key = get_current_eodhd_key()
    if not api_key:
        logging.warning("No EODHD API keys available")
        return None

    url = f'https://eodhd.com/api/fundamentals/{symbol}.US'
    params = {
        'api_token': api_key,
        'fmt': 'json'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        eodhd_calls += 1

        if response.status_code == 200:
            data = response.json()
            if 'General' in data or 'Highlights' in data:  # Valid response
                return data
            else:
                logging.warning(f"EODHD - No fundamentals data for {symbol}")
        elif response.status_code == 402:
            # Daily limit hit for this key, rotate to next
            logging.warning(f"EODHD API daily limit hit for current key")
            rotate_eodhd_key()

            # Try with next key if available
            next_key = get_current_eodhd_key()
            if next_key:
                params['api_token'] = next_key
                response = requests.get(url, params=params, timeout=10)
                eodhd_calls += 1

                if response.status_code == 200:
                    data = response.json()
                    if 'General' in data or 'Highlights' in data:
                        return data
        else:
            logging.error(f"EODHD API error for {symbol}: {response.status_code}")
    except Exception as e:
        logging.error(f"EODHD request failed for {symbol}: {str(e)}")

    return None

def format_market_cap(market_cap_value):
    """Format market cap value to standard representation."""
    if not market_cap_value or market_cap_value == 'None':
        return None

    try:
        # Handle string numbers
        if isinstance(market_cap_value, str):
            market_cap_value = market_cap_value.replace(',', '')

        value = float(market_cap_value)

        if value >= 1_000_000_000_000:  # Trillion
            return f"${value/1_000_000_000_000:.1f}T"
        elif value >= 1_000_000_000:  # Billion
            return f"${value/1_000_000_000:.1f}B"
        elif value >= 1_000_000:  # Million
            return f"${value/1_000_000:.1f}M"
        else:
            return f"${value:.0f}"
    except (ValueError, TypeError):
        return None

def format_pe_ratio(pe_value):
    """Format P/E ratio to standard representation."""
    if not pe_value or pe_value == 'None' or pe_value == '-':
        return "N/A"

    try:
        value = float(pe_value)
        return f"{value:.2f}"
    except (ValueError, TypeError):
        return "N/A"

def map_sector(sector_input):
    """Map API sector to Notion database select options."""
    if not sector_input:
        return None

    # Common sector mappings - adjust based on your Notion select options
    sector_map = {
        'TECHNOLOGY': 'Technology',
        'TECH': 'Technology',
        'FINANCIAL': 'Finance',
        'FINANCE': 'Finance',
        'HEALTHCARE': 'Healthcare',
        'CONSUMER': 'Consumer',
        'ENERGY': 'Energy',
        'INDUSTRIALS': 'Industrial',
        'MATERIALS': 'Materials',
        'UTILITIES': 'Utilities',
        'REAL ESTATE': 'Real Estate',
        'COMMUNICATION': 'Communication'
    }

    sector_upper = sector_input.upper()
    for key, value in sector_map.items():
        if key in sector_upper:
            return value

    return sector_input.title()  # Fallback to title case

def get_stock_data(ticker):
    """Get comprehensive stock data from available APIs."""
    symbol = clean_ticker(ticker)
    stock_data = {}

    # Try Alpha Vantage first for comprehensive overview
    logging.info(f"Fetching data for {symbol}...")
    av_data = get_alpha_vantage_overview(symbol)

    if av_data:
        logging.info(f"✓ Alpha Vantage data for {symbol}")
        stock_data.update({
            'name': av_data.get('Name'),
            'sector': av_data.get('Sector'),
            'market_cap': av_data.get('MarketCapitalization'),
            'pe_ratio': av_data.get('PERatio')
        })
    else:
        # Fallback to EODHD
        logging.info(f"Trying EODHD for {symbol}...")
        eodhd_data = get_eodhd_fundamentals(symbol)

        if eodhd_data:
            logging.info(f"✓ EODHD data for {symbol}")
            general = eodhd_data.get('General', {})
            highlights = eodhd_data.get('Highlights', {})

            stock_data.update({
                'name': general.get('Name'),
                'sector': general.get('Sector'),
                'market_cap': highlights.get('MarketCapitalization'),
                'pe_ratio': highlights.get('PERatio')
            })

    if not stock_data:
        logging.warning(f"✗ No data available for {symbol}")

    return stock_data

def update_stock_entry(page_id, ticker, updates):
    """Update stock entry in Notion AND Obsidian."""
    properties = {}

    if updates.get('market_cap'):
        properties['Market Cap'] = {
            'rich_text': [{'text': {'content': updates['market_cap']}}]
        }

    if updates.get('pe_ratio'):
        properties['P/E ratio'] = {
            'rich_text': [{'text': {'content': updates['pe_ratio']}}]
        }

    if updates.get('stock_name'):
        properties['Stock Name'] = {
            'rich_text': [{'text': {'content': updates['stock_name']}}]
        }

    if updates.get('sector'):
        properties['Sector'] = {
            'select': {'name': updates['sector']}
        }

    if not properties:
        return False

    # Update Notion first (primary operation)
    try:
        response = requests.patch(
            f'https://api.notion.com/v1/pages/{page_id}',
            headers=headers,
            json={'properties': properties}
        )

        if response.status_code != 200:
            return False
    except Exception as e:
        logging.error(f"Failed to update Notion entry: {str(e)}")
        return False

    # Update Obsidian (non-blocking)
    try:
        obsidian_writer.write_stock_entry(
            ticker=ticker,
            notion_id=page_id,
            properties={
                'market_cap': updates.get('market_cap'),
                'pe_ratio': updates.get('pe_ratio'),
                'stock_name': updates.get('stock_name'),
                'sector': updates.get('sector')
            }
        )
    except Exception as e:
        logging.warning(f"Obsidian update failed (non-blocking): {str(e)}")

    return True

def has_any_data(props):
    """Check if entry has any data in optional fields."""
    # Check Market Cap
    market_cap = ''.join([t.get('plain_text', '') for t in props.get('Market Cap', {}).get('rich_text', [])])
    if market_cap.strip():
        return True

    # Check P/E ratio
    pe_ratio = ''.join([t.get('plain_text', '') for t in props.get('P/E ratio', {}).get('rich_text', [])])
    if pe_ratio.strip():
        return True

    # Check Stock Name
    stock_name = ''.join([t.get('plain_text', '') for t in props.get('Stock Name', {}).get('rich_text', [])])
    if stock_name.strip():
        return True

    # Check Sector
    sector = props.get('Sector', {}).get('select', {}).get('name', '') if props.get('Sector', {}).get('select') else ''
    if sector.strip():
        return True

    return False

def get_empty_entries():
    """Get entries with empty fields, prioritizing entries with absolutely zero data."""
    all_entries = []

    # Get all entries from database
    has_more = True
    next_cursor = None

    while has_more:
        query_data = {
            'page_size': 100
        }
        if next_cursor:
            query_data['start_cursor'] = next_cursor

        response = requests.post(
            f'https://api.notion.com/v1/databases/{STOCKS_DB_ID}/query',
            headers=headers,
            json=query_data
        )
        data = response.json()
        all_entries.extend(data.get('results', []))
        has_more = data.get('has_more', False)
        next_cursor = data.get('next_cursor')

    # Separate entries into zero-data and partial-data
    zero_data_entries = []
    partial_data_entries = []

    for entry in all_entries:
        props = entry.get('properties', {})

        # Skip if ticker is missing
        ticker = ''
        if props.get('Ticker', {}).get('title'):
            ticker = ''.join([t.get('plain_text', '') for t in props['Ticker']['title']])
        if not ticker:
            continue

        if has_any_data(props):
            # Has some data - check if any fields are still empty
            market_cap = ''.join([t.get('plain_text', '') for t in props.get('Market Cap', {}).get('rich_text', [])])
            pe_ratio = ''.join([t.get('plain_text', '') for t in props.get('P/E ratio', {}).get('rich_text', [])])
            stock_name = ''.join([t.get('plain_text', '') for t in props.get('Stock Name', {}).get('rich_text', [])])
            sector = props.get('Sector', {}).get('select', {}).get('name', '') if props.get('Sector', {}).get('select') else ''

            if not (market_cap.strip() and pe_ratio.strip() and stock_name.strip() and sector.strip()):
                partial_data_entries.append(entry)
        else:
            # Absolutely no data
            zero_data_entries.append(entry)

    # Prioritize zero-data entries first
    logging.info(f"Found {len(zero_data_entries)} entries with ZERO data")
    logging.info(f"Found {len(partial_data_entries)} entries with partial data")

    return zero_data_entries + partial_data_entries

def main():
    logging.info(f"Initialized with {len(EODHD_API_KEYS)} EODHD API key(s)")
    logging.info("Starting Stocks database empty fields population...")
    logging.info("PRIORITY: Entries with absolutely zero data will be processed first")

    # Get entries with empty fields
    logging.info("Fetching entries with empty fields...")
    empty_entries = get_empty_entries()
    logging.info(f"Found {len(empty_entries)} total entries needing data")

    if not empty_entries:
        logging.info("No empty entries found")
        return

    updated_count = 0

    for i, entry in enumerate(empty_entries, 1):
        props = entry.get('properties', {})
        page_id = entry['id']

        # Get ticker
        ticker = ''
        if props.get('Ticker', {}).get('title'):
            ticker = ''.join([t.get('plain_text', '') for t in props['Ticker']['title']])

        # Mark zero-data entries
        has_data = has_any_data(props)
        priority_marker = "[ZERO DATA]" if not has_data else "[PARTIAL]"

        logging.info(f"Processing entry {i}/{len(empty_entries)} {priority_marker}: {ticker}")

        # Get stock data
        stock_data = get_stock_data(ticker)

        if not stock_data:
            continue

        # Prepare updates for empty fields only
        updates = {}

        # Check what fields are empty
        market_cap = ''.join([t.get('plain_text', '') for t in props.get('Market Cap', {}).get('rich_text', [])])
        if not market_cap.strip() and stock_data.get('market_cap'):
            formatted_mc = format_market_cap(stock_data['market_cap'])
            if formatted_mc:
                updates['market_cap'] = formatted_mc

        pe_ratio = ''.join([t.get('plain_text', '') for t in props.get('P/E ratio', {}).get('rich_text', [])])
        if not pe_ratio.strip() and stock_data.get('pe_ratio'):
            formatted_pe = format_pe_ratio(stock_data['pe_ratio'])
            if formatted_pe:
                updates['pe_ratio'] = formatted_pe

        stock_name = ''.join([t.get('plain_text', '') for t in props.get('Stock Name', {}).get('rich_text', [])])
        if not stock_name.strip() and stock_data.get('name'):
            updates['stock_name'] = stock_data['name']

        sector = props.get('Sector', {}).get('select', {}).get('name', '') if props.get('Sector', {}).get('select') else ''
        if not sector.strip() and stock_data.get('sector'):
            mapped_sector = map_sector(stock_data['sector'])
            if mapped_sector:
                updates['sector'] = mapped_sector

        # Update if we have data
        if updates:
            success = update_stock_entry(page_id, ticker, updates)
            if success:
                updated_count += 1
                logging.info(f"✓ Updated {ticker} with: {list(updates.keys())}")
            else:
                logging.error(f"✗ Failed to update {ticker}")
        else:
            logging.info(f"✓ {ticker} - no new data to add")

        # Rate limiting
        time.sleep(0.3)

    logging.info(f"Completed - Updated {updated_count} out of {len(empty_entries)} entries")
    logging.info(f"API Usage: Alpha Vantage: {alpha_vantage_calls}, EODHD: {eodhd_calls}")
    logging.info(f"SUCCESS: Empty fields populated in Stocks database")

if __name__ == "__main__":
    main()
