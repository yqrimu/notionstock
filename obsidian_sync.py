#!/usr/bin/env python3
"""
Obsidian Sync Utility Module

Provides functions to write Notion data to Obsidian markdown files with YAML frontmatter.
This is NOT a sync module - it's a dual-insert utility that writes to Obsidian
when scripts update Notion.

Usage:
    from obsidian_sync import ObsidianWriter

    writer = ObsidianWriter(
        stocks_path="/path/to/Stocks List/Entries",
        trading_research_path="/path/to/Trading Research/Entries"
    )

    writer.write_stock_entry(ticker="$TSLA", notion_id="...", properties={...})
"""

import os
import re
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)


class ObsidianWriter:
    """Handles writing Notion data to Obsidian markdown files"""

    def __init__(self, stocks_path: str, trading_research_path: str):
        """
        Initialize ObsidianWriter with paths to Obsidian directories.

        Args:
            stocks_path: Path to "Stocks List/Entries" directory
            trading_research_path: Path to "Trading Research/Entries" directory
        """
        self.stocks_path = Path(stocks_path) if stocks_path else None
        self.trading_research_path = Path(trading_research_path) if trading_research_path else None

        # Check if paths exist
        self.stocks_enabled = self.stocks_path and self.stocks_path.exists()
        self.research_enabled = self.trading_research_path and self.trading_research_path.exists()

        if not self.stocks_enabled:
            logger.warning(f"Stocks path not available: {stocks_path}")

        if not self.research_enabled:
            logger.warning(f"Trading Research path not available: {trading_research_path}")

    @staticmethod
    def ticker_to_wikilink(ticker: str) -> str:
        """
        Convert ticker to Obsidian wiki-link format.

        Args:
            ticker: Ticker symbol (e.g., "$TSLA" or "TSLA")

        Returns:
            Wiki-link format: "[[$TSLA|$TSLA]]"
        """
        clean = ticker.replace("$", "").strip()
        return f"[[${clean}|${clean}]]"

    def generate_trading_research_filename(
        self,
        ticker: str,
        date: str,
        resistance: Optional[str] = None,
        support: Optional[str] = None,
        buy_point: Optional[str] = None,
        sell_point: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Generate Trading Research filename matching existing pattern.

        If notes are provided, use them as the primary filename (Chinese text).
        Otherwise, use the pattern: $TICKER [R/S/Buy/Sell info] - [MMDDYYYY].md

        Examples:
            - With notes: "特斯拉438今天大概率是涨盘.md"
            - Without notes: "$TSLA R354.8 - 632025.md"

        Args:
            ticker: Ticker symbol
            date: Date in YYYY-MM-DD format
            resistance: Resistance level (optional)
            support: Support level (optional)
            buy_point: Buy point (optional)
            sell_point: Sell point (optional)
            notes: Trading notes text (optional) - if provided, becomes primary filename

        Returns:
            Filename string
        """
        # If notes are provided, use them as the filename (like existing entries)
        if notes and notes.strip():
            # Clean the notes text for filename (remove invalid characters)
            clean_notes = notes.strip()
            # Remove characters that are invalid in filenames
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                clean_notes = clean_notes.replace(char, '')

            # Limit filename length to avoid filesystem issues
            if len(clean_notes) > 200:
                clean_notes = clean_notes[:200]

            return f"{clean_notes}.md"

        # Fallback to structured filename if no notes
        clean_ticker = ticker.replace("$", "").strip()

        # Parse date to MMDDYYYY format
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_suffix = date_obj.strftime("%m%d%Y")  # 632025
        except ValueError:
            date_suffix = "00000000"

        # Build filename parts
        parts = [f"${clean_ticker}"]

        # Add descriptive fields (priority: R > S > Buy > Sell)
        if resistance:
            # Clean resistance value (remove ranges, take first value)
            r_value = str(resistance).split("-")[0].strip()
            parts.append(f"R{r_value}")

        if support:
            s_value = str(support).split("-")[0].strip()
            parts.append(f"S{s_value}")

        if buy_point and not resistance:
            buy_value = str(buy_point).split("-")[0].strip()
            parts.append(f"Buy{buy_value}")

        if sell_point and not resistance and not buy_point:
            sell_value = str(sell_point).split("-")[0].strip()
            parts.append(f"Sell{sell_value}")

        # Combine parts
        if len(parts) > 1:
            filename = f"{' '.join(parts)} - {date_suffix}.md"
        else:
            filename = f"${clean_ticker} - {date_suffix}.md"

        return filename

    def write_markdown_file(self, filepath: Path, frontmatter: Dict, body: str = "") -> bool:
        """
        Write markdown file with YAML frontmatter.

        Args:
            filepath: Path to markdown file
            frontmatter: Dictionary of frontmatter fields
            body: Markdown body content (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure parent directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Write file with YAML frontmatter
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump(
                    frontmatter,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False
                )
                f.write("---\n")

                if body:
                    f.write("\n")
                    f.write(body)

            logger.debug(f"Wrote markdown file: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to write markdown file {filepath}: {e}")
            return False

    def read_frontmatter(self, filepath: Path) -> Optional[Dict]:
        """
        Read YAML frontmatter from markdown file.

        Args:
            filepath: Path to markdown file

        Returns:
            Dictionary of frontmatter fields, or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract frontmatter
            match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not match:
                return None

            frontmatter_str = match.group(1)
            frontmatter = yaml.safe_load(frontmatter_str)

            return frontmatter

        except Exception as e:
            logger.error(f"Failed to read frontmatter from {filepath}: {e}")
            return None

    def fast_extract_notion_id(self, filepath: Path) -> Optional[str]:
        """
        Fast extraction of notion-id without full YAML parse.

        Args:
            filepath: Path to markdown file

        Returns:
            Notion ID string, or None if not found
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                header = f.read(500)  # Only first 500 chars

            match = re.search(r'notion-id:\s*([a-f0-9\-]+)', header)
            return match.group(1) if match else None

        except Exception as e:
            logger.debug(f"Failed to extract notion-id from {filepath}: {e}")
            return None

    def build_notion_id_cache(self, directory: Path) -> Dict[str, Path]:
        """
        Build cache of notion-id → filepath mappings.

        Args:
            directory: Directory to scan for markdown files

        Returns:
            Dictionary mapping notion-id to filepath
        """
        cache = {}

        if not directory or not directory.exists():
            logger.warning(f"Cannot build cache: directory does not exist: {directory}")
            return cache

        logger.info(f"Building notion-id cache from {directory}...")
        start_time = datetime.now()

        # Scan all .md files
        for filepath in directory.glob("*.md"):
            notion_id = self.fast_extract_notion_id(filepath)
            if notion_id:
                cache[notion_id] = filepath

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Built cache with {len(cache)} entries in {elapsed:.2f} seconds")

        return cache

    def write_stock_entry(
        self,
        ticker: str,
        notion_id: str,
        properties: Dict
    ) -> bool:
        """
        Write or update Stocks List entry.

        Args:
            ticker: Ticker symbol (e.g., "$TSLA")
            notion_id: Notion page ID
            properties: Dictionary with keys: market_cap, pe_ratio, stock_name, sector

        Returns:
            True if successful, False otherwise
        """
        if not self.stocks_enabled:
            logger.debug("Stocks path not enabled, skipping")
            return False

        # Generate filename
        clean_ticker = ticker.replace("$", "").strip()
        filename = f"${clean_ticker}.md"
        filepath = self.stocks_path / filename

        # Read existing frontmatter if file exists
        existing_frontmatter = {}
        if filepath.exists():
            existing_frontmatter = self.read_frontmatter(filepath) or {}

        # Build frontmatter (merge with existing)
        frontmatter = {
            'notion-id': notion_id,
            'base': '[[Stocks List.base]]',
            'Market Cap': properties.get('market_cap') or existing_frontmatter.get('Market Cap', 'N/A'),
            'P/E ratio': properties.get('pe_ratio') or existing_frontmatter.get('P/E ratio', 'N/A'),
            'Related to Trading Research (Stock 1)': existing_frontmatter.get('Related to Trading Research (Stock 1)', []),
            'Sector': properties.get('sector') or existing_frontmatter.get('Sector', ''),
            'Stock Name': properties.get('stock_name') or existing_frontmatter.get('Stock Name', '')
        }

        # Write file
        success = self.write_markdown_file(filepath, frontmatter)

        if success:
            logger.info(f"Wrote Stocks entry: {filename}")

        return success

    def write_trading_research_entry(
        self,
        filename: str,
        notion_id: str,
        properties: Dict
    ) -> bool:
        """
        Write or update Trading Research entry.

        Args:
            filename: Filename for the entry (generated by generate_trading_research_filename)
            notion_id: Notion page ID
            properties: Dictionary with keys: date, ticker, resistance, support, buy_point,
                       sell_point, ladder, notes

        Returns:
            True if successful, False otherwise
        """
        if not self.research_enabled:
            logger.debug("Trading Research path not enabled, skipping")
            return False

        filepath = self.trading_research_path / filename

        # Check for collision (file exists with different notion-id)
        if filepath.exists():
            existing_id = self.fast_extract_notion_id(filepath)
            if existing_id and existing_id != notion_id:
                # Collision: append numeric suffix
                base_name = filename[:-3]  # Remove .md
                counter = 2
                while True:
                    new_filename = f"{base_name} ({counter}).md"
                    new_filepath = self.trading_research_path / new_filename
                    if not new_filepath.exists():
                        filepath = new_filepath
                        logger.warning(f"Filename collision detected, using: {new_filename}")
                        break
                    counter += 1

        # Build frontmatter (ordered to match Obsidian table structure)
        frontmatter = {
            'notion-id': notion_id,
            'base': '[[Trading Research.base]]',
            'Support': properties.get('support', ''),
            'Stock 1': [self.ticker_to_wikilink(properties.get('ticker', ''))],
            'Trades Made': [],
            'Sell Point': properties.get('sell_point', ''),
            'Prev. Low': properties.get('prev_low', ''),
            'Buy Point': properties.get('buy_point', ''),
            'Date': properties.get('date', ''),
            'Prev. High': properties.get('prev_high', ''),
            'Resistance': properties.get('resistance', ''),
            'Note': properties.get('notes', ''),
            'Ladder': properties.get('ladder'),
            'Prev. Close': properties.get('prev_close'),
            'Prev. Volume': properties.get('prev_volume'),
            'Last API Fetch': properties.get('last_api_fetch'),
        }

        # Remove None values but keep empty strings
        frontmatter = {k: v for k, v in frontmatter.items() if v is not None}

        # No body content needed - notes are in frontmatter
        body = ""

        # Write file
        success = self.write_markdown_file(filepath, frontmatter, body)

        if success:
            logger.info(f"Wrote Trading Research entry: {filename}")

        return success

    def update_trading_research_ohlcv_by_path(
        self,
        filepath: Path,
        ohlcv_data: Dict
    ) -> bool:
        """
        Update OHLCV fields in existing Trading Research file.

        Args:
            filepath: Path to existing markdown file
            ohlcv_data: Dictionary with keys: prev_close, prev_high, prev_low,
                       prev_volume, last_api_fetch

        Returns:
            True if successful, False otherwise
        """
        if not self.research_enabled:
            logger.debug("Trading Research path not enabled, skipping")
            return False

        if not filepath.exists():
            logger.warning(f"File does not exist: {filepath}")
            return False

        # Read existing frontmatter
        frontmatter = self.read_frontmatter(filepath)
        if not frontmatter:
            logger.warning(f"Could not read frontmatter from: {filepath}")
            return False

        # Update OHLCV fields
        frontmatter['Prev. Close'] = ohlcv_data.get('prev_close')
        frontmatter['Prev. High'] = ohlcv_data.get('prev_high')
        frontmatter['Prev. Low'] = ohlcv_data.get('prev_low')
        frontmatter['Prev. Volume'] = ohlcv_data.get('prev_volume')

        if ohlcv_data.get('last_api_fetch'):
            frontmatter['Last API Fetch'] = ohlcv_data['last_api_fetch']

        # Write updated file
        success = self.write_markdown_file(filepath, frontmatter)

        if success:
            logger.info(f"Updated OHLCV in: {filepath.name}")

        return success
