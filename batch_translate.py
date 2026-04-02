#!/usr/bin/env python3
"""Overnight batch translation of Taishō texts using Claude Code CLI.

Designed to run unattended. Processes texts from the full catalog,
extracts Chinese source, translates via `claude -p` (uses Max plan),
assembles translations, and generates PDFs.

Skips texts that already have translations. Stops after a time limit.

Usage:
    python3 batch_translate.py                    # default: 8 hours
    python3 batch_translate.py --hours 6          # 6-hour limit
    python3 batch_translate.py --start-from T0100 # start from specific text
    python3 batch_translate.py --volume T01       # only process one volume
    python3 batch_translate.py --dry-run          # list what would be translated
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# Import extraction functions from existing script
sys.path.insert(0, str(Path(__file__).parent))
from extract_chinese import (
    build_char_map, extract_text, blocks_to_text, get_metadata,
)
from generate_pdf import generate_pdf

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path.home() / 'taisho-translation-sample'
XML_BASE = Path.home() / 'taisho-canon' / 'xml' / 'T'
CHINESE_DIR = BASE_DIR / 'chinese'
TRANS_DIR = BASE_DIR / 'translations'
PDF_DIR = BASE_DIR / 'pdfs'
LOG_DIR = BASE_DIR / 'logs'

# Chunking: characters per Claude CLI call.
# Claude's context is ~200K tokens; 30K Chinese chars ≈ 45K tokens input,
# leaving ample room for output.
CHUNK_SIZE = 5_000

# Time between API calls to be polite to the service
PAUSE_BETWEEN_CHUNKS = 2  # seconds
PAUSE_BETWEEN_TEXTS = 5   # seconds

TRANSLATION_PROMPT = """You are translating a Chinese Buddhist text from the Taishō Tripiṭaka into English.

Title: {title}
Taishō Number: {t_number}
{chunk_info}

Rules (follow exactly):
1. Output ONLY the English translation. No preamble, no commentary, no "Here is the translation".
2. Use standard scholarly Buddhist terminology.
3. Transliterate Sanskrit/Pali proper names in IAST (e.g., Śāriputra, Ānanda, nirvāṇa).
4. Preserve verse structure: translate verses as indented lines with ">" prefix.
5. Mark dhāraṇī passages with [Dhāraṇī] and transliterate rather than translate.
6. For fascicle headers, output "## Fascicle N" on its own line.
7. For section headings, translate and output as "### Heading".
8. Maintain the dignity and literary quality appropriate to sacred scripture.
9. Translate the COMPLETE text below. Do not summarize or abbreviate.

Chinese text to translate:

{chinese_text}"""


def setup_logging():
    """Set up logging to both file and console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_DIR / f'batch_{timestamp}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    return log_file


def count_cjk(text: str) -> int:
    """Count Chinese characters in text."""
    return len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', text))


def split_into_chunks(text: str, max_chars: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries."""
    paragraphs = text.split('\n\n')
    chunks = []
    current = []
    current_count = 0

    for para in paragraphs:
        pc = count_cjk(para)

        # Oversized paragraph: split at sentence boundaries
        if pc > max_chars:
            if current:
                chunks.append('\n\n'.join(current))
                current, current_count = [], 0
            sentences = re.split(r'(?<=[。！？])', para)
            sent_buf, sent_count = [], 0
            for sent in sentences:
                sc = count_cjk(sent)
                if sent_count + sc > max_chars and sent_buf:
                    chunks.append(''.join(sent_buf))
                    sent_buf, sent_count = [sent], sc
                else:
                    sent_buf.append(sent)
                    sent_count += sc
            if sent_buf:
                chunks.append(''.join(sent_buf))
            continue

        if current_count + pc > max_chars and current:
            chunks.append('\n\n'.join(current))
            current, current_count = [para], pc
        else:
            current.append(para)
            current_count += pc

    if current:
        chunks.append('\n\n'.join(current))

    return chunks


def extract_chinese_source(text_entry: dict) -> Path | None:
    """Extract Chinese source for a text. Returns path to .txt file, or None on failure."""
    t_num = text_entry['t_number']
    out_path = CHINESE_DIR / f'{t_num}.txt'

    if out_path.exists():
        return out_path

    # Find XML files
    pattern = text_entry['xml_pattern']
    parts = pattern.split('/')
    vol_dir = XML_BASE / parts[0]
    xml_files = sorted(vol_dir.glob(parts[1]))

    if not xml_files:
        logging.warning(f"{t_num}: no XML files found for {pattern}")
        return None

    try:
        char_map = build_char_map(xml_files)
        blocks = extract_text(xml_files, char_map)
        readable = blocks_to_text(blocks)
        char_count = count_cjk(readable)

        if char_count == 0:
            logging.warning(f"{t_num}: extracted 0 characters")
            return None

        header = (
            f"# {text_entry['title_zh']}\n"
            f"# Taishō {t_num}, {text_entry['juan']} fascicle(s)\n"
            f"# Translator: {text_entry['translator']}\n"
            f"# Characters: {char_count:,}\n\n"
        )
        out_path.write_text(header + readable, encoding='utf-8')
        logging.info(f"{t_num}: extracted {char_count:,} chars")
        return out_path

    except Exception as e:
        logging.error(f"{t_num}: extraction failed: {e}")
        return None


def translate_chunk_via_cli(chinese_text: str, text_entry: dict,
                            chunk_num: int = 0, total_chunks: int = 1) -> str:
    """Translate a chunk of Chinese text using the claude CLI."""
    chunk_info = ""
    if total_chunks > 1:
        chunk_info = f"Part {chunk_num} of {total_chunks}. Translate this portion only."

    prompt = TRANSLATION_PROMPT.format(
        title=text_entry.get('title_zh', ''),
        t_number=text_entry['t_number'],
        chunk_info=chunk_info,
        chinese_text=chinese_text,
    )

    # Write prompt to temp file; redirect output to temp file.
    # Using file I/O avoids Python subprocess pipe/TTY issues with claude CLI.
    prompt_file = tempfile.mktemp(suffix='_prompt.txt')
    output_file = tempfile.mktemp(suffix='_output.txt')

    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    try:
        result = subprocess.run(
            f'env -u CLAUDECODE -u ANTHROPIC_API_KEY -u CLAUDE_CODE_ENTRYPOINT '
            f'claude -p --output-format text < "{prompt_file}" > "{output_file}" 2>&1',
            shell=True,
            timeout=600,  # 10 min max per chunk
        )

        if result.returncode != 0:
            err = ""
            if os.path.exists(output_file):
                err = open(output_file).read()[:500]
            raise RuntimeError(
                f"claude CLI exited {result.returncode}\n  output: {err}"
            )

        if not os.path.exists(output_file):
            raise RuntimeError("claude CLI produced no output file")

        output = open(output_file, encoding='utf-8').read().strip()
        if not output:
            raise RuntimeError("claude CLI returned empty output")

        return output
    finally:
        for f in (prompt_file, output_file):
            if os.path.exists(f):
                os.unlink(f)


def translate_text(text_entry: dict) -> bool:
    """Translate a full text. Returns True on success."""
    t_num = text_entry['t_number']
    trans_path = TRANS_DIR / f'{t_num}_translation.md'

    # Extract Chinese source
    chinese_path = extract_chinese_source(text_entry)
    if chinese_path is None:
        return False

    chinese_text = chinese_path.read_text(encoding='utf-8')

    # Strip header lines
    body_lines = []
    for line in chinese_text.split('\n'):
        if line.startswith('#'):
            continue
        body_lines.append(line)
    body = '\n'.join(body_lines).strip()

    char_count = count_cjk(body)
    if char_count == 0:
        logging.warning(f"{t_num}: no content to translate")
        return False

    # Chunk if needed
    chunks = split_into_chunks(body)
    logging.info(f"{t_num}: {char_count:,} chars, {len(chunks)} chunk(s)")

    # Translate each chunk
    translations = []
    for i, chunk in enumerate(chunks, 1):
        chunk_chars = count_cjk(chunk)
        logging.info(f"  {t_num} chunk {i}/{len(chunks)} ({chunk_chars:,} chars)...")
        start = time.time()

        for attempt in range(2):  # retry once on failure
            try:
                result = translate_chunk_via_cli(chunk, text_entry, i, len(chunks))
                elapsed = time.time() - start
                logging.info(f"  {t_num} chunk {i}/{len(chunks)} done ({elapsed:.0f}s)")
                translations.append(result)
                break
            except Exception as e:
                if attempt == 0:
                    logging.warning(f"  {t_num} chunk {i}/{len(chunks)} attempt 1 failed: {e}")
                    logging.info(f"  Retrying after 10s pause...")
                    time.sleep(10)
                else:
                    logging.error(f"  {t_num} chunk {i}/{len(chunks)} FAILED after retry: {e}")
                    translations.append(f"[TRANSLATION ERROR in chunk {i}: {e}]")

        if i < len(chunks):
            time.sleep(PAUSE_BETWEEN_CHUNKS)

    # Check if any chunk actually succeeded
    successful = [t for t in translations if not t.startswith('[TRANSLATION ERROR')]
    if not successful:
        logging.error(f"{t_num}: all chunks failed, not saving")
        return False

    # Assemble translation with header
    title_en = text_entry.get('title_zh', t_num)  # fallback to Chinese title
    header = (
        f"# {title_en}\n"
        f"## {text_entry.get('title_zh', '')}\n\n"
        f"Taishō Tripiṭaka No. {t_num.replace('T', '')}\n\n"
    )
    if text_entry.get('translator'):
        header += f"Translated from the Chinese. {text_entry['translator']}\n\n"
    header += "---\n\n"

    full_translation = header + '\n\n'.join(translations)
    trans_path.write_text(full_translation, encoding='utf-8')
    logging.info(f"{t_num}: translation saved ({len(full_translation):,} bytes)")

    return True


def generate_text_pdf(text_entry: dict) -> bool:
    """Generate PDF for a translated text."""
    t_num = text_entry['t_number']
    md_path = TRANS_DIR / f'{t_num}_translation.md'
    pdf_path = PDF_DIR / f'{t_num}_translation.pdf'

    if not md_path.exists():
        return False

    return generate_pdf(md_path, pdf_path)


def load_catalog(catalog_path: Path, start_from: str = None,
                 volume: str = None) -> list[dict]:
    """Load and filter the catalog."""
    with open(catalog_path) as f:
        catalog = json.load(f)

    if volume:
        catalog = [t for t in catalog if t['volume'] == volume]

    if start_from:
        # Find the index and slice
        idx = next((i for i, t in enumerate(catalog)
                     if t['t_number'] >= start_from), 0)
        catalog = catalog[idx:]

    return catalog


def main():
    parser = argparse.ArgumentParser(
        description='Overnight batch translation of Taishō texts')
    parser.add_argument('--hours', type=float, default=8,
                        help='Maximum hours to run (default: 8)')
    parser.add_argument('--start-from', type=str, default=None,
                        help='Start from this T-number (e.g., T0100)')
    parser.add_argument('--volume', type=str, default=None,
                        help='Only process texts in this volume (e.g., T01)')
    parser.add_argument('--dry-run', action='store_true',
                        help='List texts that would be translated, then exit')
    parser.add_argument('--no-pdf', action='store_true',
                        help='Skip PDF generation')
    parser.add_argument('--small-first', action='store_true',
                        help='Process smaller texts first (sort by fascicle count)')
    parser.add_argument('--max-juan', type=int, default=None,
                        help='Skip texts with more than N fascicles')
    args = parser.parse_args()

    log_file = setup_logging()
    logging.info(f"Batch translation starting. Log: {log_file}")
    logging.info(f"Time limit: {args.hours} hours")

    # Ensure directories exist
    for d in [CHINESE_DIR, TRANS_DIR, PDF_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Load catalog
    catalog_path = BASE_DIR / 'full_catalog.json'
    if not catalog_path.exists():
        logging.error("full_catalog.json not found. Run build_full_catalog.py first.")
        sys.exit(1)

    catalog = load_catalog(catalog_path, args.start_from, args.volume)
    logging.info(f"Catalog: {len(catalog)} texts")

    # Filter out already-translated texts
    todo = []
    for entry in catalog:
        t_num = entry['t_number']
        trans_path = TRANS_DIR / f'{t_num}_translation.md'
        if trans_path.exists():
            continue
        todo.append(entry)

    if args.max_juan:
        todo = [e for e in todo if e['juan'] <= args.max_juan]

    if args.small_first:
        todo.sort(key=lambda e: e['juan'])

    logging.info(f"Already translated: {len(catalog) - len(todo)}")
    logging.info(f"Remaining: {len(todo)} texts")

    if args.dry_run:
        print(f"\nWould translate {len(todo)} texts:")
        for entry in todo[:50]:
            print(f"  {entry['t_number']:8s} {entry['title_zh'][:30]:30s} "
                  f"{entry['juan']:3d} juan")
        if len(todo) > 50:
            print(f"  ... and {len(todo) - 50} more")
        return

    # Main translation loop
    deadline = time.time() + args.hours * 3600
    completed = 0
    failed = 0
    total_chars = 0

    batch_start = time.time()

    for entry in todo:
        # Check time limit
        if time.time() > deadline:
            logging.info("Time limit reached. Stopping.")
            break

        t_num = entry['t_number']
        text_start = time.time()

        try:
            success = translate_text(entry)
            if success:
                completed += 1
                # Count chars
                chinese_path = CHINESE_DIR / f'{t_num}.txt'
                if chinese_path.exists():
                    total_chars += count_cjk(
                        chinese_path.read_text(encoding='utf-8'))

                # Generate PDF
                if not args.no_pdf:
                    generate_text_pdf(entry)
            else:
                failed += 1

        except KeyboardInterrupt:
            logging.info("Interrupted by user. Stopping.")
            break
        except Exception as e:
            logging.error(f"{t_num}: unexpected error: {e}")
            failed += 1

        text_elapsed = time.time() - text_start
        logging.info(f"{t_num}: total time {text_elapsed:.0f}s")

        time.sleep(PAUSE_BETWEEN_TEXTS)

    # Summary
    batch_elapsed = time.time() - batch_start
    logging.info(f"\n{'=' * 60}")
    logging.info("BATCH SUMMARY")
    logging.info(f"  Elapsed: {batch_elapsed / 3600:.1f} hours")
    logging.info(f"  Completed: {completed}")
    logging.info(f"  Failed: {failed}")
    logging.info(f"  Remaining: {len(todo) - completed - failed}")
    logging.info(f"  Characters translated: {total_chars:,}")
    if batch_elapsed > 0 and total_chars > 0:
        rate = total_chars / (batch_elapsed / 3600)
        logging.info(f"  Rate: {rate:,.0f} chars/hour")
    logging.info(f"{'=' * 60}")


if __name__ == '__main__':
    main()
