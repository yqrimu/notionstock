#!/usr/bin/env python3
"""
Update existing Obsidian Trading Research files to add Notes content.
This is a one-time fix script for the December 3, 2025 entries.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from obsidian_sync import ObsidianWriter

load_dotenv()

# Mapping of filenames to their notes content
notes_content = {
    "$TSLA R438 - 12032025.md": "今天大概率是涨盘。突破438，趋势仍然不确定。站稳445，才安全",
    "$NVDA R176 - 12032025.md": "今天是有人砸盘。176仍然有效",
    "$META R646 S639 - 12032025.md": "比较好分析一点。646站稳，趋势是涨",
    "$AMZN - 12032025.md": "今天大概率是跌盘。不动它",
    "$MSTR R166 - 12032025.md": "站稳166，趋势就是涨，但是不突破190，就是反弹。涨，是一个台阶一个台阶",
    "$MSFT S466 Buy466 - 12032025.md": "不跌破466，可以买",
    "$QCOM Buy155 - 12032025.md": "是常拿的，如果到155-159，可以加一仓",
    "$BMNR R34.8 - 12032025.md": "上次突破过一次34.8，看今天能不能再次突破",
    "$CRWV S72.88 - 12032025.md": "支撑72.88-73.3",
    "$CRCL R81.5 S75 - 12032025.md": "支撑75，等待突破81.5-82.3。不突破83.98，记得减仓。跌了再买会减仓的",
    "$DJT - 12032025.md": "我一直没提了，小散没有割肉的，耐心等待吧。希望有一个大跌，好进场，我看到一个卖的价格，不知道哪天能到",
    "$VST S166 - 12032025.md": "支撑166，不加不减。等到12号左右看有没有加仓机会",
    "$ASST Buy0.98 - 12032025.md": "跟它耗，预设买入0.98，1.17卖。操盘手一直在等小散割肉",
    "$ORCL S198 Buy197 - 12032025.md": "198支撑，不破197，买一点，设止损",
    "$QUBT S10.58 - 12032025.md": "支撑10.58",
    "$FIG - 12032025.md": "不是等价格，是等小散割肉，我们接他们卖的。如果到19号还没有割肉的，可以追",
}

def update_file_with_notes(filepath: Path, notes: str):
    """Add notes content to existing file"""
    if not filepath.exists():
        print(f"✗ File not found: {filepath.name}")
        return False

    # Read existing content
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if notes already added
    if "## Notes" in content:
        print(f"⏩ Already has notes: {filepath.name}")
        return True

    # Check if file ends with just frontmatter (ends with ---)
    if content.rstrip().endswith("---"):
        # Append notes after frontmatter
        new_content = content.rstrip() + "\n\n## Notes\n\n" + notes + "\n"
    else:
        # File already has body content, append notes
        new_content = content.rstrip() + "\n\n## Notes\n\n" + notes + "\n"

    # Write updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✓ Updated: {filepath.name}")
    return True

def main():
    research_path = Path(os.getenv('OBSIDIAN_TRADING_RESEARCH_PATH'))

    if not research_path or not research_path.exists():
        print("✗ Trading Research path not found")
        return

    print(f"📝 Updating {len(notes_content)} files with notes content...\n")

    updated = 0
    skipped = 0
    failed = 0

    for filename, notes in notes_content.items():
        filepath = research_path / filename

        if update_file_with_notes(filepath, notes):
            if "Already has notes" not in str(filepath.name):
                updated += 1
            else:
                skipped += 1
        else:
            failed += 1

    print(f"\n🎉 Completed!")
    print(f"✓ Updated: {updated} files")
    print(f"⏩ Skipped: {skipped} files (already had notes)")
    print(f"✗ Failed: {failed} files")

if __name__ == "__main__":
    main()
