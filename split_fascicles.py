#!/usr/bin/env python3
"""
Split large Chinese text files into individual fascicle files for translation.

Reads chinese/TNNNN.txt files that exceed MAX_CJK_CHARS and splits them
on "Fascicle NNN:" markers. Writes to chinese/splits/TNNNN_fNNN.txt.

This is pure text processing — no AI calls, no quota usage.

Usage:
  python3 split_fascicles.py              # split all large untranslated texts
  python3 split_fascicles.py T1545        # split a specific text
  python3 split_fascicles.py --dry-run    # report what would be split
"""

import json
import os
import re
import sys

BASE = "/Users/danzigmond/taisho-translation"
CATALOG = os.path.join(BASE, "full_catalog.json")
CHINESE_DIR = os.path.join(BASE, "chinese")
SPLITS_DIR = os.path.join(BASE, "chinese", "splits")
TRANSLATIONS_DIR = os.path.join(BASE, "translations")

MAX_CJK_CHARS = 15000  # Match the pipeline threshold


def count_cjk(text):
    return sum(1 for c in text if "\u4e00" <= c <= "\u9fff")


def parse_header(text):
    """Extract header lines (starting with #) from the text."""
    lines = text.split("\n")
    header_lines = []
    for line in lines:
        if line.startswith("#"):
            header_lines.append(line)
        elif line.strip() == "":
            continue
        else:
            break
    return header_lines


def split_into_fascicles(text):
    """Split text on Fascicle markers, grouping by fascicle number."""
    # Pattern: ===...=== / Fascicle NNN: title / ===...===
    pattern = r"={10,}\nFascicle (\d+): [^\n]+\n={10,}\n"

    parts = re.split(pattern, text)
    # parts[0] = header/preamble, then alternating: fascicle_num, content

    header = parts[0]
    fascicles = {}

    i = 1
    while i < len(parts) - 1:
        fasc_num = int(parts[i])
        content = parts[i + 1]
        if fasc_num not in fascicles:
            fascicles[fasc_num] = []
        fascicles[fasc_num].append(content.strip())
        i += 2

    return header.strip(), fascicles


def split_text(t_number, dry_run=False):
    """Split a single text file into fascicle files."""
    chinese_file = os.path.join(CHINESE_DIR, f"{t_number}.txt")
    if not os.path.exists(chinese_file):
        print(f"  ERROR: {chinese_file} not found")
        return 0

    with open(chinese_file) as f:
        text = f.read()

    cjk = count_cjk(text)
    if cjk <= MAX_CJK_CHARS:
        return 0

    header_lines = parse_header(text)
    header_text = "\n".join(header_lines)
    _, fascicles = split_into_fascicles(text)

    if not fascicles:
        print(f"  WARNING: {t_number} has no fascicle markers ({cjk:,} CJK chars)")
        return 0

    if dry_run:
        fasc_sizes = []
        for num in sorted(fascicles):
            combined = "\n\n".join(fascicles[num])
            fasc_sizes.append((num, count_cjk(combined)))
        max_fasc = max(s for _, s in fasc_sizes)
        print(f"  {t_number}: {cjk:,} CJK chars → {len(fascicles)} fascicles "
              f"(largest: {max_fasc:,} chars)")
        return len(fascicles)

    os.makedirs(SPLITS_DIR, exist_ok=True)
    written = 0

    for num in sorted(fascicles):
        combined = "\n\n".join(fascicles[num])
        if not combined.strip():
            continue

        fasc_file = os.path.join(SPLITS_DIR, f"{t_number}_f{num:03d}.txt")
        fasc_cjk = count_cjk(combined)

        with open(fasc_file, "w") as f:
            # Include header for context
            f.write(f"{header_text}\n")
            f.write(f"# Fascicle {num} of {len(fascicles)}\n\n")
            f.write(combined)
            f.write("\n")

        written += 1

    print(f"  {t_number}: {cjk:,} CJK chars → {written} fascicle files in splits/")
    return written


def main():
    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    catalog = json.load(open(CATALOG))
    existing = set()
    for fn in os.listdir(TRANSLATIONS_DIR):
        if fn.startswith("T") and fn.endswith("_translation.md"):
            existing.add(fn.split("_")[0])

    if args:
        # Specific texts
        texts = []
        for arg in args:
            tn = arg if arg.startswith("T") else f"T{arg}"
            texts.append(tn)
    else:
        # All large untranslated texts
        texts = []
        for t in catalog:
            tn = t["t_number"]
            if tn in existing:
                continue
            cf = os.path.join(CHINESE_DIR, f"{tn}.txt")
            if not os.path.exists(cf):
                continue
            with open(cf) as f:
                text = f.read()
            cjk = count_cjk(text)
            if cjk > MAX_CJK_CHARS:
                texts.append(tn)

    if not texts:
        print("No texts to split.")
        return

    print(f"{'[DRY RUN] ' if dry_run else ''}Processing {len(texts)} texts...")
    total_fascicles = 0
    no_markers = 0

    for tn in texts:
        n = split_text(tn, dry_run=dry_run)
        if n == 0:
            cf = os.path.join(CHINESE_DIR, f"{tn}.txt")
            if os.path.exists(cf):
                with open(cf) as f:
                    cjk = count_cjk(f.read())
                if cjk > MAX_CJK_CHARS:
                    no_markers += 1
        total_fascicles += n

    print(f"\nTotal: {total_fascicles} fascicle files from {len(texts)} texts")
    if no_markers:
        print(f"WARNING: {no_markers} large texts had no fascicle markers")


if __name__ == "__main__":
    main()
