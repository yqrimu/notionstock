#!/usr/bin/env python3
"""
Populate empty fields in Stocks database using Alpha Vantage and EODHD APIs.

Empty fields identified:
- $COIN: Market Cap, P/E Ratio, Stock Name, Sector
- $CRCL: Market Cap, P/E Ratio, Stock Name, Sector  
- $RGC, $RGTI, $ACHR, $HUSA: P/E Ratio only

Uses the same dual API approach as the Trading Research population script.
"""

import requests
import os
import time
import logging
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys
NOTION_TOKEN = os.getenv('NOTION_TOKEN')
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_KEY')
EODHD_API_KEY = os.getenv('EODHD_API_KEY')
STOCKS_DB_ID = '20be24d8-7d14-818a-9586-e5478b4e6c18'

# Notion headers
headers = {
    'Authorization': f'Bearer {NOTION_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

# API usage tracking
alpha_vantage_calls = 0
eodhd_calls = 0
ALPHA_VANTAGE_LIMIT = 25

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
    """Get stock fundamentals from EODHD."""
    global eodhd_calls
    
    url = f'https://eodhd.com/api/fundamentals/{symbol}.US'
    params = {
        'api_token': EODHD_API_KEY,
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

def update_stock_entry(page_id, updates):
    """Update stock entry with new data."""
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
    
    try:
        response = requests.patch(
            f'https://api.notion.com/v1/pages/{page_id}',
            headers=headers,
            json={'properties': properties}
        )
        
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Failed to update entry: {str(e)}")
        return False

def get_empty_entries():
    """Get entries with empty fields that need population."""
    empty_entries = []
    
    # Query for entries with empty Market Cap or P/E ratio
    query_filter = {
        'or': [
            {
                'property': 'Market Cap',
                'rich_text': {
                    'is_empty': True
                }
            },
            {
                'property': 'P/E ratio',
                'rich_text': {
                    'is_empty': True
                }
            }
        ]
    }
    
    # Get filtered entries
    has_more = True
    next_cursor = None
    
    while has_more:
        query_data = {
            'page_size': 100,
            'filter': query_filter
        }
        if next_cursor:
            query_data['start_cursor'] = next_cursor
        
        response = requests.post(
            f'https://api.notion.com/v1/databases/{STOCKS_DB_ID}/query',
            headers=headers,
            json=query_data
        )
        data = response.json()
        empty_entries.extend(data.get('results', []))
        has_more = data.get('has_more', False)
        next_cursor = data.get('next_cursor')
    
    return empty_entries

def main():
    logging.info("🚀 Starting Stocks database empty fields population...")
    
    # Get entries with empty fields
    logging.info("🔍 Fetching entries with empty fields...")
    empty_entries = get_empty_entries()
    logging.info(f"Found {len(empty_entries)} entries needing data")
    
    if not empty_entries:
        logging.info("✅ No empty entries found!")
        return
    
    updated_count = 0
    
    for i, entry in enumerate(empty_entries, 1):
        props = entry.get('properties', {})
        page_id = entry['id']
        
        # Get ticker
        ticker = ''
        if props.get('Ticker', {}).get('title'):
            ticker = ''.join([t.get('plain_text', '') for t in props['Ticker']['title']])
        
        logging.info(f"Processing entry {i}/{len(empty_entries)}: {ticker}")
        
        # Get stock data
        stock_data = get_stock_data(ticker)
        
        if not stock_data:
            continue
        
        # Debug: log what data we got
        logging.info(f"Retrieved data for {ticker}: {stock_data}")
        
        # Prepare updates for empty fields only
        updates = {}
        
        # Check what fields are empty
        market_cap = ''.join([t.get('plain_text', '') for t in props.get('Market Cap', {}).get('rich_text', [])])
        logging.info(f"Current Market Cap in Notion: '{market_cap}', Data from API: {stock_data.get('market_cap')}")
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
            success = update_stock_entry(page_id, updates)
            if success:
                updated_count += 1
                logging.info(f"✓ Updated {ticker} with: {list(updates.keys())}")
            else:
                logging.error(f"✗ Failed to update {ticker}")
        else:
            logging.info(f"✓ {ticker} - no new data to add")
        
        # Rate limiting
        time.sleep(0.3)
    
    logging.info(f"🎉 Completed! Updated {updated_count} out of {len(empty_entries)} entries")
    logging.info(f"📊 API Usage: Alpha Vantage: {alpha_vantage_calls}, EODHD: {eodhd_calls}")
    logging.info(f"✅ SUCCESS: Empty fields populated in Stocks database")

if __name__ == "__main__":
    main()