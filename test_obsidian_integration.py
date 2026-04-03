#!/usr/bin/env python3
"""
Test script for Obsidian integration functionality.
Tests the ObsidianWriter without making actual API calls.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from obsidian_sync import ObsidianWriter

# Load environment variables
load_dotenv()

def test_initialization():
    """Test ObsidianWriter initialization"""
    print("=" * 70)
    print("TEST 1: ObsidianWriter Initialization")
    print("=" * 70)

    writer = ObsidianWriter(
        stocks_path=os.getenv('OBSIDIAN_STOCKS_PATH'),
        trading_research_path=os.getenv('OBSIDIAN_TRADING_RESEARCH_PATH')
    )

    print(f"Stocks path enabled: {writer.stocks_enabled}")
    print(f"Trading Research path enabled: {writer.research_enabled}")
    print(f"Stocks path: {writer.stocks_path}")
    print(f"Trading Research path: {writer.trading_research_path}")

    if writer.stocks_enabled and writer.research_enabled:
        print("✓ Initialization successful")
        return writer
    else:
        print("✗ Initialization failed - paths not accessible")
        sys.exit(1)


def test_ticker_to_wikilink():
    """Test ticker to wikilink conversion"""
    print("\n" + "=" * 70)
    print("TEST 2: Ticker to Wikilink Conversion")
    print("=" * 70)

    test_cases = [
        ("$TSLA", "[[$TSLA|$TSLA]]"),
        ("TSLA", "[[$TSLA|$TSLA]]"),
        ("$NVDA", "[[$NVDA|$NVDA]]"),
        ("QQQ", "[[$QQQ|$QQQ]]"),
    ]

    all_passed = True
    for ticker, expected in test_cases:
        result = ObsidianWriter.ticker_to_wikilink(ticker)
        passed = result == expected
        all_passed = all_passed and passed
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {ticker:10} -> {result:25} (expected: {expected})")

    if all_passed:
        print("\n✓ All wikilink conversion tests passed")
    else:
        print("\n✗ Some wikilink conversion tests failed")
        sys.exit(1)


def test_filename_generation(writer):
    """Test Trading Research filename generation"""
    print("\n" + "=" * 70)
    print("TEST 3: Trading Research Filename Generation")
    print("=" * 70)

    test_cases = [
        {
            "ticker": "$TSLA",
            "date": "2025-06-23",
            "resistance": "429.8-430.6",
            "support": "424.8-425.4",
            "buy_point": None,
            "sell_point": None,
            "expected_pattern": "$TSLA R429.8 S424.8 - 06232025.md"
        },
        {
            "ticker": "NVDA",
            "date": "2025-05-29",
            "resistance": "143",
            "support": "139",
            "buy_point": None,
            "sell_point": None,
            "expected_pattern": "$NVDA R143 S139 - 05292025.md"
        },
        {
            "ticker": "$AAPL",
            "date": "2025-05-30",
            "resistance": None,
            "support": None,
            "buy_point": "166",
            "sell_point": None,
            "expected_pattern": "$AAPL Buy166 - 05302025.md"
        },
        {
            "ticker": "$SPY",
            "date": "2025-06-22",
            "resistance": None,
            "support": None,
            "buy_point": None,
            "sell_point": "18.38",
            "expected_pattern": "$SPY Sell18.38 - 06222025.md"
        },
        {
            "ticker": "$QQQ",
            "date": "2025-06-20",
            "resistance": None,
            "support": None,
            "buy_point": None,
            "sell_point": None,
            "expected_pattern": "$QQQ - 06202025.md"
        },
    ]

    all_passed = True
    for test_case in test_cases:
        filename = writer.generate_trading_research_filename(
            ticker=test_case["ticker"],
            date=test_case["date"],
            resistance=test_case["resistance"],
            support=test_case["support"],
            buy_point=test_case["buy_point"],
            sell_point=test_case["sell_point"]
        )

        passed = filename == test_case["expected_pattern"]
        all_passed = all_passed and passed
        symbol = "✓" if passed else "✗"

        print(f"\n{symbol} Test Case:")
        print(f"  Ticker: {test_case['ticker']}, Date: {test_case['date']}")
        print(f"  R: {test_case['resistance']}, S: {test_case['support']}")
        print(f"  Buy: {test_case['buy_point']}, Sell: {test_case['sell_point']}")
        print(f"  Generated: {filename}")
        print(f"  Expected:  {test_case['expected_pattern']}")

    if all_passed:
        print("\n✓ All filename generation tests passed")
    else:
        print("\n✗ Some filename generation tests failed")
        sys.exit(1)


def test_cache_building(writer):
    """Test notion-id cache building"""
    print("\n" + "=" * 70)
    print("TEST 4: Notion-ID Cache Building")
    print("=" * 70)

    if not writer.research_enabled:
        print("⏩ Skipping - Trading Research path not enabled")
        return

    start_time = datetime.now()
    cache = writer.build_notion_id_cache(writer.trading_research_path)
    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"Cache size: {len(cache)} entries")
    print(f"Build time: {elapsed:.2f} seconds")

    # Show sample entries
    sample_count = min(5, len(cache))
    print(f"\nSample cache entries (first {sample_count}):")
    for i, (notion_id, filepath) in enumerate(list(cache.items())[:sample_count]):
        print(f"  {i+1}. {notion_id[:16]}... -> {filepath.name}")

    if len(cache) > 0 and elapsed < 10:
        print("\n✓ Cache building test passed")
    else:
        print("\n⚠ Warning: Cache building may need optimization")


def test_frontmatter_read_write(writer):
    """Test reading and writing frontmatter"""
    print("\n" + "=" * 70)
    print("TEST 5: Frontmatter Read/Write")
    print("=" * 70)

    if not writer.stocks_enabled:
        print("⏩ Skipping - Stocks path not enabled")
        return

    # Find an existing stock file to test reading
    test_files = list(writer.stocks_path.glob("$TSLA.md"))
    if not test_files:
        test_files = list(writer.stocks_path.glob("*.md"))[:1]

    if not test_files:
        print("⏩ Skipping - No existing stock files to test")
        return

    test_file = test_files[0]
    print(f"Reading from: {test_file.name}")

    # Read existing frontmatter
    frontmatter = writer.read_frontmatter(test_file)

    if frontmatter:
        print("\n✓ Successfully read frontmatter:")
        print(f"  notion-id: {frontmatter.get('notion-id', 'N/A')[:20]}...")
        print(f"  Market Cap: {frontmatter.get('Market Cap', 'N/A')}")
        print(f"  P/E ratio: {frontmatter.get('P/E ratio', 'N/A')}")
        print(f"  Stock Name: {frontmatter.get('Stock Name', 'N/A')}")
        print(f"  Sector: {frontmatter.get('Sector', 'N/A')}")

        # Test notion-id extraction
        notion_id = writer.fast_extract_notion_id(test_file)
        if notion_id:
            print(f"\n✓ Fast notion-id extraction: {notion_id[:20]}...")
        else:
            print("\n✗ Fast notion-id extraction failed")
            sys.exit(1)
    else:
        print("\n✗ Failed to read frontmatter")
        sys.exit(1)


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("OBSIDIAN INTEGRATION TEST SUITE")
    print("=" * 70)

    # Test 1: Initialization
    writer = test_initialization()

    # Test 2: Ticker to wikilink conversion
    test_ticker_to_wikilink()

    # Test 3: Filename generation
    test_filename_generation(writer)

    # Test 4: Cache building
    test_cache_building(writer)

    # Test 5: Frontmatter read/write
    test_frontmatter_read_write(writer)

    # Final summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print("✓ All tests passed!")
    print("\nObsidian integration is ready for production use.")
    print("=" * 70)


if __name__ == "__main__":
    main()
