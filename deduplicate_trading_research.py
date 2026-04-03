#!/usr/bin/env python3
"""
Deduplicate Trading Research entries in Notion and Obsidian.

Identifies duplicates by (date, stock_1_relation_id, notes_text).
Keeps the oldest entry (earliest created_time), archives the rest from Notion,
and deletes the corresponding Obsidian files.
"""

import os
import time
import logging
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
import requests

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
TRADING_RESEARCH_DB_ID = "20be24d8-7d14-8129-975e-e2624faaaad9"
OBSIDIAN_RESEARCH_PATH = Path(os.getenv("OBSIDIAN_TRADING_RESEARCH_PATH", ""))

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}


def fetch_all_entries():
    """Fetch all Trading Research entries from Notion (handles pagination)."""
    url = f"https://api.notion.com/v1/databases/{TRADING_RESEARCH_DB_ID}/query"
    all_results = []
    start_cursor = None

    while True:
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if response.status_code != 200:
            logger.error(f"Failed to fetch entries: {data}")
            break

        all_results.extend(data.get("results", []))

        if data.get("has_more"):
            start_cursor = data.get("next_cursor")
        else:
            break

        time.sleep(0.3)

    return all_results


def extract_key(page):
    """Extract deduplication key: (date, stock_relation_id, notes_text)."""
    props = page.get("properties", {})

    # Date
    date_obj = props.get("Date", {}).get("date") or {}
    date = date_obj.get("start", "")

    # Stock 1 relation
    relations = props.get("Stock 1", {}).get("relation", [])
    stock_id = relations[0]["id"] if relations else ""

    # Notes (title field)
    title_parts = props.get("Notes", {}).get("title", [])
    notes = "".join(p.get("plain_text", "") for p in title_parts)

    return (date, stock_id, notes)


def archive_notion_page(page_id):
    """Archive (soft-delete) a Notion page."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.patch(url, headers=headers, json={"archived": True})
    return response.status_code == 200


def build_obsidian_cache():
    """Build notion-id -> filepath cache from Obsidian files."""
    cache = {}
    if not OBSIDIAN_RESEARCH_PATH.exists():
        logger.warning(f"Obsidian path not found: {OBSIDIAN_RESEARCH_PATH}")
        return cache

    import re
    for filepath in OBSIDIAN_RESEARCH_PATH.glob("*.md"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                header = f.read(500)
            match = re.search(r'notion-id:\s*([a-f0-9\-]+)', header)
            if match:
                cache[match.group(1)] = filepath
        except Exception:
            pass

    logger.info(f"Built Obsidian cache: {len(cache)} files")
    return cache


def main():
    print("Fetching all Trading Research entries from Notion...")
    all_entries = fetch_all_entries()
    print(f"Total entries fetched: {len(all_entries)}")

    # Group by deduplication key
    groups = defaultdict(list)
    for page in all_entries:
        key = extract_key(page)
        groups[key].append(page)

    # Find duplicates
    duplicates_to_delete = []
    for key, pages in groups.items():
        if len(pages) > 1:
            # Sort by created_time ascending, keep first, delete the rest
            pages_sorted = sorted(pages, key=lambda p: p["created_time"])
            to_delete = pages_sorted[1:]  # all but the oldest
            duplicates_to_delete.extend(to_delete)
            date, stock_id, notes_preview = key
            print(f"  Duplicate ({len(pages)}x): [{date}] {notes_preview[:60]}")

    print(f"\nFound {len(duplicates_to_delete)} duplicate entries to remove.")

    if not duplicates_to_delete:
        print("Nothing to do.")
        return

    # Build Obsidian cache
    obsidian_cache = build_obsidian_cache()

    print(f"Proceeding with deletion...\n")

    notion_deleted = 0
    notion_failed = 0
    obsidian_deleted = 0

    for page in duplicates_to_delete:
        page_id = page["id"]
        clean_id = page_id.replace("-", "")

        # Archive from Notion
        if archive_notion_page(page_id):
            notion_deleted += 1
            print(f"  ✓ Archived Notion page: {page_id}")
        else:
            notion_failed += 1
            print(f"  ✗ Failed to archive: {page_id}")

        # Delete from Obsidian (try both with and without dashes)
        obsidian_file = obsidian_cache.get(page_id) or obsidian_cache.get(clean_id)
        if obsidian_file and obsidian_file.exists():
            obsidian_file.unlink()
            obsidian_deleted += 1
            print(f"  ✓ Deleted Obsidian file: {obsidian_file.name}")
        else:
            print(f"  - No Obsidian file found for: {page_id}")

        time.sleep(0.3)

    print(f"\nDone!")
    print(f"  Notion archived: {notion_deleted}")
    print(f"  Notion failed:   {notion_failed}")
    print(f"  Obsidian deleted: {obsidian_deleted}")


if __name__ == "__main__":
    main()
