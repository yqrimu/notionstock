#!/usr/bin/env python3
"""
Fix Obsidian Trading Research filenames to use Chinese notes text.
Renames files from structured names (e.g., "$TSLA R438 - 12032025.md")
to Chinese notes text (e.g., "特斯拉438今天大概率是涨盘.md")
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Mapping of old filenames to new filenames (Chinese notes)
filename_mapping = {
    "$TSLA R438 - 12032025.md": "今天大概率是涨盘。突破438，趋势仍然不确定。站稳445，才安全.md",
    "$NVDA R176 - 12032025.md": "今天是有人砸盘。176仍然有效.md",
    "$META R646 S639 - 12032025.md": "比较好分析一点。646站稳，趋势是涨.md",
    "$AMZN - 12032025.md": "今天大概率是跌盘。不动它.md",
    "$MSTR R166 - 12032025.md": "站稳166，趋势就是涨，但是不突破190，就是反弹。涨，是一个台阶一个台阶.md",
    "$MSFT S466 Buy466 - 12032025.md": "不跌破466，可以买.md",
    "$QCOM Buy155 - 12032025.md": "是常拿的，如果到155-159，可以加一仓.md",
    "$BMNR R34.8 - 12032025.md": "上次突破过一次34.8，看今天能不能再次突破.md",
    "$CRWV S72.88 - 12032025.md": "支撑72.88-73.3.md",
    "$CRCL R81.5 S75 - 12032025.md": "支撑75，等待突破81.5-82.3。不突破83.98，记得减仓。跌了再买会减仓的.md",
    "$DJT - 12032025.md": "我一直没提了，小散没有割肉的，耐心等待吧。希望有一个大跌，好进场，我看到一个卖的价格，不知道哪天能到.md",
    "$VST S166 - 12032025.md": "支撑166，不加不减。等到12号左右看有没有加仓机会.md",
    "$ASST Buy0.98 - 12032025.md": "跟它耗，预设买入0.98，1.17卖。操盘手一直在等小散割肉.md",
    "$ORCL S198 Buy197 - 12032025.md": "198支撑，不破197，买一点，设止损.md",
    "$QUBT S10.58 - 12032025.md": "支撑10.58.md",
    "$FIG - 12032025.md": "不是等价格，是等小散割肉，我们接他们卖的。如果到19号还没有割肉的，可以追.md",
}

def rename_file(old_path: Path, new_filename: str):
    """Rename file to new filename"""
    if not old_path.exists():
        print(f"✗ File not found: {old_path.name}")
        return False

    new_path = old_path.parent / new_filename

    # Check if target already exists
    if new_path.exists():
        print(f"⚠ Target already exists: {new_filename}")
        return False

    try:
        old_path.rename(new_path)
        print(f"✓ Renamed: {old_path.name} → {new_filename}")
        return True
    except Exception as e:
        print(f"✗ Failed to rename {old_path.name}: {e}")
        return False

def main():
    research_path = Path(os.getenv('OBSIDIAN_TRADING_RESEARCH_PATH'))

    if not research_path or not research_path.exists():
        print("✗ Trading Research path not found")
        return

    print(f"📝 Renaming {len(filename_mapping)} files to Chinese notes...\n")

    renamed = 0
    skipped = 0
    failed = 0

    for old_filename, new_filename in filename_mapping.items():
        old_path = research_path / old_filename

        result = rename_file(old_path, new_filename)
        if result:
            renamed += 1
        elif old_path.exists():
            skipped += 1
        else:
            failed += 1

    print(f"\n🎉 Completed!")
    print(f"✓ Renamed: {renamed} files")
    print(f"⚠ Skipped: {skipped} files (target already exists)")
    print(f"✗ Failed: {failed} files (not found)")

if __name__ == "__main__":
    main()
