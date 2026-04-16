#!/usr/bin/env python3
"""
Comprehensive cleanup of all translation files.

Fixes diacritics, capitalization, terminology, and em-dashes
based on lessons learned from the Collected Shingi project.

Run with --dry-run to see what would change without modifying files.
Run without flags to apply all fixes.
"""

import argparse
import re
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent / "translations"

# ============================================================
# Fix definitions
# ============================================================

# Diacritics: bare form -> correct IAST form
# Order matters: longer patterns first to avoid partial matches
DIACRITICS_FIXES = [
    # Case-sensitive replacements
    (r'\bSakyamuni\b', 'Śākyamuni'),
    (r'\bShakyamuni\b', 'Śākyamuni'),
    (r'\bSurangama\b', 'Śūraṅgama'),
    (r'\bsramanera\b', 'śrāmaṇera'),
    (r'\bSramanera\b', 'Śrāmaṇera'),
    (r'\bsramana\b', 'śrāmaṇa'),
    (r'\bnirvana\b', 'nirvāṇa'),
    (r'\bNirvana\b', 'Nirvāṇa'),
    (r'\bNIRVANA\b', 'NIRVĀṆA'),
    (r'\bsamadhi\b', 'samādhi'),
    (r'\bSamadhi\b', 'Samādhi'),
    (r'\bdharani\b', 'dhāraṇī'),
    (r'\bDharani\b', 'Dhāraṇī'),
    (r'\bprajna\b', 'prajñā'),
    (r'\bPrajna\b', 'Prajñā'),
    (r'\bbhiksu\b', 'bhikṣu'),
    (r'\bBhiksu\b', 'Bhikṣu'),
    (r'\bbhiksuni\b', 'bhikṣuṇī'),
    (r'\bBhiksuni\b', 'Bhikṣuṇī'),
    (r'\bkashaya\b', 'kāṣāya'),
    (r'\bKashaya\b', 'Kāṣāya'),
    (r'\bsutras\b', 'sūtras'),
    (r'\bSutras\b', 'Sūtras'),
    (r'\bsutra\b', 'sūtra'),
    (r'\bSutra\b', 'Sūtra'),
    (r'\bSUTRA\b', 'SŪTRA'),
    (r'\bDogen\b', 'Dōgen'),
    (r'\bObaku\b', 'Ōbaku'),
    (r'\bkasaya\b', 'kāṣāya'),
]

# Spelling standardization
SPELLING_FIXES = [
    # Saṅgha -> Sangha (established English form)
    ('Saṅgha', 'Sangha'),
    ('saṅgha', 'sangha'),
    # Pure Regulations -> Pure Rules
    ('Pure Regulations', 'Pure Rules'),
    # buddha-nature -> Buddha-nature (capitalize B)
    ('buddha-nature', 'Buddha-nature'),
    # BDK conventions
    ('Three Jewels', 'Three Treasures'),
    ('three jewels', 'Three Treasures'),
    ('Blessed One', 'World-Honored One'),
    ('Blessed Ones', 'World-Honored Ones'),
    ('expedient means', 'skillful means'),
    ('Expedient Means', 'Skillful Means'),
    ('Expedient means', 'Skillful means'),
    ('wholesome roots', 'roots of merit'),
    ('Wholesome roots', 'Roots of merit'),
    ('five skandhas', 'five aggregates'),
    ('Thus-Come One', 'Tathāgata'),
    ('Thus Come One', 'Tathāgata'),
]

# Capitalization fixes for running text (NOT headings)
# These use a function-based approach to skip headings
CAP_FIXES_RUNNING_TEXT = [
    ('Dharma Hall', 'Dharma hall'),
    ('Sangha Hall', 'Sangha hall'),
    ('Buddha Hall', 'Buddha hall'),
    ('Bath Hall', 'bath hall'),
]


def fix_diacritics(text):
    """Fix bare Sanskrit/Japanese terms missing diacritics."""
    count = 0
    for pattern, replacement in DIACRITICS_FIXES:
        matches = len(re.findall(pattern, text))
        if matches:
            text = re.sub(pattern, replacement, text)
            count += matches
    return text, count


def fix_spelling(text):
    """Fix spelling standardization issues."""
    count = 0
    for old, new in SPELLING_FIXES:
        n = text.count(old)
        if n:
            text = text.replace(old, new)
            count += n
    return text, count


def fix_capitalization(text):
    """Fix capitalization in running text, preserving Title Case in headings."""
    lines = text.split('\n')
    count = 0
    for i, line in enumerate(lines):
        # Skip headings (## or ###)
        if line.startswith('#'):
            continue
        for old, new in CAP_FIXES_RUNNING_TEXT:
            n = line.count(old)
            if n:
                lines[i] = line.replace(old, new)
                count += n
                line = lines[i]
    return '\n'.join(lines), count


def fix_em_dashes(text):
    """Replace em-dashes with appropriate punctuation.

    This is a conservative automated fix that handles the most common patterns.
    Complex cases may need manual review.
    """
    lines = text.split('\n')
    count = 0

    for i, line in enumerate(lines):
        # Skip headings and the first 8 lines (header)
        if line.startswith('#') or i < 8:
            # In headings: replace — with :
            if line.startswith('#') and '—' in line:
                lines[i] = line.replace('—', ':')
                count += line.count('—')
            continue

        if '—' not in line:
            continue

        original = line

        # Pattern 1: Paired em-dashes (parenthetical) -> commas
        # "word—inserted text—word" -> "word, inserted text, word"
        line = re.sub(r'(\w)—([^—]+)—(\w)', r'\1, \2, \3', line)

        # Pattern 2: Em-dash before a list or elaboration -> colon
        # "three items—incense, candles" -> "three items: incense, candles"
        line = re.sub(r'(\w)—(\w)', r'\1; \2', line)

        # Pattern 3: Em-dash at end of line (trailing) -> ellipsis
        line = re.sub(r'—\s*$', '...', line)

        # Pattern 4: Space-em-dash-space -> semicolon
        line = re.sub(r'\s—\s', '; ', line)

        # Pattern 5: Any remaining em-dashes -> semicolons
        line = line.replace('—', '; ')

        if line != original:
            lines[i] = line
            count += 1

    return '\n'.join(lines), count


def process_file(filepath, dry_run=False):
    """Process a single translation file."""
    text = filepath.read_text(encoding='utf-8')
    original = text
    total_fixes = 0
    details = []

    # 1. Diacritics
    text, n = fix_diacritics(text)
    if n:
        details.append(f"  diacritics: {n}")
        total_fixes += n

    # 2. Spelling standardization
    text, n = fix_spelling(text)
    if n:
        details.append(f"  spelling: {n}")
        total_fixes += n

    # 3. Capitalization (running text only)
    text, n = fix_capitalization(text)
    if n:
        details.append(f"  capitalization: {n}")
        total_fixes += n

    # 4. Em-dashes
    text, n = fix_em_dashes(text)
    if n:
        details.append(f"  em-dashes: {n}")
        total_fixes += n

    if total_fixes > 0:
        if not dry_run:
            filepath.write_text(text, encoding='utf-8')
        return total_fixes, details
    return 0, []


def main():
    parser = argparse.ArgumentParser(description="Clean up all translation files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would change without modifying files")
    args = parser.parse_args()

    files = sorted(TRANSLATIONS_DIR.glob("T*_translation.md"))
    print(f"Found {len(files)} translation files")
    if args.dry_run:
        print("DRY RUN — no files will be modified\n")

    total_files_changed = 0
    total_fixes = 0
    category_totals = {"diacritics": 0, "spelling": 0,
                       "capitalization": 0, "em-dashes": 0}

    for filepath in files:
        n, details = process_file(filepath, dry_run=args.dry_run)
        if n > 0:
            total_files_changed += 1
            total_fixes += n
            print(f"{filepath.name}: {n} fixes")
            for d in details:
                print(d)
                # Track category totals
                for cat in category_totals:
                    if cat in d:
                        category_totals[cat] += int(d.split(":")[1].strip())

    print(f"\n{'DRY RUN ' if args.dry_run else ''}SUMMARY:")
    print(f"  Files changed: {total_files_changed} / {len(files)}")
    print(f"  Total fixes: {total_fixes}")
    for cat, n in sorted(category_totals.items(), key=lambda x: -x[1]):
        if n > 0:
            print(f"    {cat}: {n}")


if __name__ == "__main__":
    main()
