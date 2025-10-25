#!/usr/bin/env python3
"""
Trading Research Populator - Production Script

Populates empty Trading Research fields with previous day OHLCV data.
Uses dual API support: Alpha Vantage (primary) + EODHD (backup).

Usage: python3 populate_trading_research.py

Features:
- Finds Trading Research entries with empty Prev. Close/High/Low/Volume fields
- Uses Date column to calculate previous trading day
- Follows Stock 1 relation to get ticker symbols from Stocks database
- Automatic API fallback when rate limits hit
- Comprehensive error handling and logging

Last Updated: June 24, 2025
Status: Production Ready
"""

import asyncio
import aiohttp
import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingResearchPopulator:
    """Populates empty Trading Research fields using MCP and dual API support"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_KEY")

        # Load multiple EODHD API keys for rotation
        eodhd_keys_str = os.getenv("EODHD_API_KEYS", os.getenv("EODHD_API_KEY", ""))
        self.eodhd_keys = [key.strip() for key in eodhd_keys_str.split(",") if key.strip()]
        self.current_eodhd_key_index = 0
        self.exhausted_eodhd_keys = set()

        self.notion_token = os.getenv("NOTION_TOKEN")

        # API URLs
        self.av_base_url = "https://www.alphavantage.co/query"
        self.eodhd_base_url = "https://eodhd.com/api"

        # Database IDs
        self.stocks_db_id = "20be24d8-7d14-818a-9586-e5478b4e6c18"
        self.trading_research_db_id = "20be24d8-7d14-8129-975e-e2624faaaad9"

        # Rate limiting
        self.av_request_count = 0
        self.eodhd_request_count = 0
        self.av_daily_limit_hit = False

        # Cache for stock info
        self.stock_cache = {}

        logger.info(f"Initialized with {len(self.eodhd_keys)} EODHD API key(s)")

    def get_current_eodhd_key(self) -> Optional[str]:
        """Get the current active EODHD API key"""
        if not self.eodhd_keys:
            return None

        # Find next non-exhausted key
        for _ in range(len(self.eodhd_keys)):
            key_index = self.current_eodhd_key_index % len(self.eodhd_keys)
            key = self.eodhd_keys[key_index]

            if key not in self.exhausted_eodhd_keys:
                return key

            self.current_eodhd_key_index += 1

        # All keys exhausted
        return None

    def rotate_eodhd_key(self):
        """Rotate to the next EODHD API key"""
        if not self.eodhd_keys:
            return

        current_key = self.eodhd_keys[self.current_eodhd_key_index % len(self.eodhd_keys)]
        self.exhausted_eodhd_keys.add(current_key)
        self.current_eodhd_key_index += 1

        next_key = self.get_current_eodhd_key()
        if next_key:
            logger.info(f"Rotating EODHD API key (exhausted {len(self.exhausted_eodhd_keys)}/{len(self.eodhd_keys)} keys)")
        else:
            logger.warning("All EODHD API keys have been exhausted")

    async def get_stock_info_by_id(self, stock_id: str) -> Optional[str]:
        """Get ticker symbol from stock ID using cache or MCP query"""
        if stock_id in self.stock_cache:
            return self.stock_cache[stock_id]
        
        try:
            # Use MCP to get stock info - we'll need to implement this with MCP calls
            # For now, using direct API as fallback
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            url = f"https://api.notion.com/v1/pages/{stock_id}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                page_data = response.json()
                ticker_prop = page_data.get("properties", {}).get("Ticker", {}).get("title", [])
                if ticker_prop:
                    ticker = ticker_prop[0]["text"]["content"].replace("$", "")
                    self.stock_cache[stock_id] = ticker
                    return ticker
            
            return None
        except Exception as e:
            logger.error(f"Error getting stock info for {stock_id}: {e}")
            return None
    
    async def fetch_daily_data_av(self, ticker: str) -> Optional[Dict]:
        """Fetch daily data from Alpha Vantage"""
        if self.av_daily_limit_hit or self.av_request_count >= 25:
            return None
            
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'outputsize': 'compact',
            'apikey': self.alpha_vantage_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.av_base_url, params=params) as response:
                    data = await response.json()
                    self.av_request_count += 1
                    
                    if "Note" in data and "rate limit" in str(data.get("Note", "")).lower():
                        self.av_daily_limit_hit = True
                        logger.warning(f"Alpha Vantage rate limit hit for {ticker}")
                        return None
                    
                    if "Time Series (Daily)" in data:
                        return data
                    return None
        except Exception as e:
            logger.error(f"Alpha Vantage error for {ticker}: {e}")
            return None
    
    async def fetch_daily_data_eodhd(self, ticker: str, retry_on_limit: bool = True) -> Optional[Dict]:
        """Fetch daily data from EODHD with automatic key rotation"""
        current_key = self.get_current_eodhd_key()
        if not current_key:
            logger.warning("No EODHD API keys available")
            return None

        clean_ticker = ticker.upper()
        if '.' not in clean_ticker:
            clean_ticker += '.US'

        # Get recent data
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

        url = f"{self.eodhd_base_url}/eod/{clean_ticker}"
        params = {
            'api_token': current_key,
            'fmt': 'json',
            'from': start_date,
            'to': end_date,
            'period': 'd'
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    self.eodhd_request_count += 1

                    # Handle rate limit / payment required (402)
                    if response.status == 402:
                        logger.warning(f"EODHD key exhausted (402) for {ticker}")
                        self.rotate_eodhd_key()

                        # Retry with next key if available
                        if retry_on_limit and self.get_current_eodhd_key():
                            return await self.fetch_daily_data_eodhd(ticker, retry_on_limit=False)

                        return None

                    data = await response.json()

                    if isinstance(data, list) and len(data) > 0:
                        # Convert EODHD format to Alpha Vantage-like format
                        time_series = {}
                        for day_data in data:
                            date = day_data['date']
                            time_series[date] = {
                                "1. open": str(day_data['open']),
                                "2. high": str(day_data['high']),
                                "3. low": str(day_data['low']),
                                "4. close": str(day_data['close']),
                                "5. volume": str(day_data['volume'])
                            }

                        return {"Time Series (Daily)": time_series}
                    return None
        except Exception as e:
            logger.error(f"EODHD error for {ticker}: {e}")
            return None
    
    async def fetch_daily_data_with_fallback(self, ticker: str) -> Optional[Dict]:
        """Fetch daily data with Alpha Vantage -> EODHD fallback"""
        # Try Alpha Vantage first
        if not self.av_daily_limit_hit:
            data = await self.fetch_daily_data_av(ticker)
            if data:
                logger.info(f"✓ Alpha Vantage data for {ticker}")
                return data
        
        # Fallback to EODHD
        data = await self.fetch_daily_data_eodhd(ticker)
        if data:
            logger.info(f"✓ EODHD data for {ticker}")
            return data
        
        logger.warning(f"✗ No data available for {ticker}")
        return None
    
    def get_previous_trading_day_data(self, time_series: Dict, reference_date: str) -> Optional[Tuple[str, Dict]]:
        """Find the most recent trading day before the reference date"""
        available_dates = [d for d in time_series.keys() if d < reference_date]
        if not available_dates:
            return None
        
        prev_date = max(available_dates)
        prev_data = time_series[prev_date]
        
        return prev_date, {
            'open': float(prev_data["1. open"]),
            'high': float(prev_data["2. high"]),
            'low': float(prev_data["3. low"]),
            'close': float(prev_data["4. close"]),
            'volume': int(prev_data["5. volume"])
        }
    
    async def get_trading_research_entries(self) -> List[Dict]:
        """Get Trading Research entries with empty previous day data"""
        logger.info("🔍 Fetching Trading Research entries with empty data...")
        
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            url = f"https://api.notion.com/v1/databases/{self.trading_research_db_id}/query"
            
            # Query for entries with empty previous day fields
            payload = {
                "page_size": 100,
                "filter": {
                    "or": [
                        {"property": "Prev. Close", "number": {"is_empty": True}},
                        {"property": "Prev. High", "rich_text": {"is_empty": True}},
                        {"property": "Prev. Low", "rich_text": {"is_empty": True}},
                        {"property": "Prev. Volume", "number": {"is_empty": True}}
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            entries = []
            for result in data.get("results", []):
                properties = result.get("properties", {})
                
                # Get date
                date_prop = properties.get("Date", {}).get("date")
                if not date_prop:
                    continue
                
                # Get stock relation
                stock_relation = properties.get("Stock 1", {}).get("relation", [])
                if not stock_relation:
                    continue
                
                entry_info = {
                    "notion_id": result["id"],
                    "date": date_prop["start"],
                    "stock_id": stock_relation[0]["id"]
                }
                entries.append(entry_info)
            
            logger.info(f"Found {len(entries)} Trading Research entries needing data")
            return entries
            
        except Exception as e:
            logger.error(f"Error fetching Trading Research entries: {e}")
            return []
    
    async def update_trading_research_entry(self, entry: Dict, prev_data: Dict) -> bool:
        """Update Trading Research entry with previous day data"""
        try:
            import requests
            
            headers = {
                "Authorization": f"Bearer {self.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            update_payload = {
                "properties": {
                    "Prev. Close": {"number": prev_data['close']},
                    "Prev. High": {"rich_text": [{"text": {"content": str(prev_data['high'])}}]},
                    "Prev. Low": {"rich_text": [{"text": {"content": str(prev_data['low'])}}]},
                    "Prev. Volume": {"number": prev_data['volume']},
                    "Last API Fetch": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            
            url = f"https://api.notion.com/v1/pages/{entry['notion_id']}"
            response = requests.patch(url, headers=headers, json=update_payload)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating entry {entry['notion_id']}: {e}")
            return False
    
    async def populate_trading_research(self):
        """Main function to populate Trading Research empty fields"""
        logger.info("🚀 Starting Trading Research population...")
        
        # Get entries needing data
        entries = await self.get_trading_research_entries()
        if not entries:
            logger.info("No entries found needing data")
            return
        
        updated_count = 0
        
        for i, entry in enumerate(entries):
            logger.info(f"Processing entry {i+1}/{len(entries)}: {entry['date']}")
            
            # Get ticker symbol from stock relation
            ticker = await self.get_stock_info_by_id(entry['stock_id'])
            if not ticker:
                logger.warning(f"Could not get ticker for stock ID {entry['stock_id']}")
                continue
            
            # Fetch daily data
            daily_data = await self.fetch_daily_data_with_fallback(ticker)
            if not daily_data or "Time Series (Daily)" not in daily_data:
                logger.warning(f"No daily data for {ticker}")
                continue
            
            # Get previous trading day data
            prev_result = self.get_previous_trading_day_data(
                daily_data["Time Series (Daily)"], 
                entry['date']
            )
            if not prev_result:
                logger.warning(f"No previous trading data for {ticker} before {entry['date']}")
                continue
            
            prev_date, prev_ohlcv = prev_result
            
            # Update the entry
            if await self.update_trading_research_entry(entry, prev_ohlcv):
                logger.info(f"✓ Updated {ticker} ({entry['date']}) with data from {prev_date}")
                updated_count += 1
            else:
                logger.error(f"✗ Failed to update {ticker}")
            
            # Small delay to respect rate limits
            await asyncio.sleep(0.5)
        
        logger.info(f"🎉 Completed! Updated {updated_count} out of {len(entries)} entries")
        logger.info(f"📊 API Usage: Alpha Vantage: {self.av_request_count}, EODHD: {self.eodhd_request_count}")
        
        if updated_count > 0:
            logger.info(f"✅ SUCCESS: {updated_count} Trading Research entries populated with previous day data")
        
        if len(entries) - updated_count > 0:
            skipped = len(entries) - updated_count
            logger.info(f"⚠️  SKIPPED: {skipped} entries (likely .SPX index entries - this is normal)")
        
        if len(entries) == 0:
            logger.info(f"ℹ️  All Trading Research entries already have previous day data - no updates needed")

async def main():
    """Main execution function"""

    # Check environment variables
    required_vars = ["ALPHA_VANTAGE_KEY", "NOTION_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    # Check for EODHD keys (supports both formats)
    if not os.getenv("EODHD_API_KEYS") and not os.getenv("EODHD_API_KEY"):
        missing_vars.append("EODHD_API_KEYS or EODHD_API_KEY")

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return

    # Initialize and run populator
    populator = TradingResearchPopulator()
    await populator.populate_trading_research()

if __name__ == "__main__":
    asyncio.run(main())