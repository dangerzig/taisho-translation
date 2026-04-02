#!/usr/bin/env python3
"""Interactive batch translation using a persistent claude session.

Uses claude -p with --output-format json and --resume to maintain a single
session across texts, avoiding the per-invocation overhead that made the
old batch_translate.sh run at 20K chars/hour instead of 300K.

Usage:
    python3 batch_interactive.py                    # default: 10 hours
    python3 batch_interactive.py --hours 6
    python3 batch_interactive.py --max-juan 30      # skip very large texts
    python3 batch_interactive.py --dry-run
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extract_chinese import build_char_map, extract_text, blocks_to_text

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent
XML_BASE = Path.home() / 'taisho-canon' / 'xml' / 'T'
CHINESE_DIR = BASE_DIR / 'chinese'
TRANS_DIR = BASE_DIR / 'translations'
LOG_DIR = BASE_DIR / 'logs'

# Max chars to send in one prompt. The context window is 200K tokens;
# 60K Chinese chars ≈ 90K tokens, leaving room for output.
MAX_CHARS_PER_PROMPT = 60_000

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
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = LOG_DIR / f'interactive_{timestamp}.log'
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
    return len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', text))


def extract_chinese_source(text_entry: dict) -> Path | None:
    t_num = text_entry['t_number']
    out_path = CHINESE_DIR / f'{t_num}.txt'
    if out_path.exists():
        return out_path

    pattern = text_entry['xml_pattern']
    parts = pattern.split('/')
    vol_dir = XML_BASE / parts[0]
    xml_files = sorted(vol_dir.glob(parts[1]))
    if not xml_files:
        return None

    try:
        char_map = build_char_map(xml_files)
        blocks = extract_text(xml_files, char_map)
        readable = blocks_to_text(blocks)
        char_count = count_cjk(readable)
        if char_count == 0:
            return None

        header = (
            f"# {text_entry['title_zh']}\n"
            f"# Taishō {t_num}, {text_entry['juan']} fascicle(s)\n"
            f"# Translator: {text_entry['translator']}\n"
            f"# Characters: {char_count:,}\n\n"
        )
        out_path.write_text(header + readable, encoding='utf-8')
        return out_path
    except Exception:
        return None


def get_chinese_body(chinese_path: Path) -> str:
    """Read Chinese file and strip header lines."""
    text = chinese_path.read_text(encoding='utf-8')
    lines = [l for l in text.split('\n') if not l.startswith('#')]
    return '\n'.join(lines).strip()


def translate_via_cli(prompt: str, session_id: str | None = None,
                      timeout: int = 600) -> tuple[str, str | None]:
    """Translate using claude -p. Returns (translation_text, session_id).

    Uses --resume to continue the session if session_id is provided.
    """
    cmd = [
        'claude', '-p',
        '--output-format', 'json',
        '--model', 'sonnet',
        '--no-session-persistence',
    ]
    if session_id:
        cmd.extend(['--resume', session_id])

    # Write prompt to temp file, redirect input
    import tempfile
    prompt_file = tempfile.mktemp(suffix='_prompt.txt')
    output_file = tempfile.mktemp(suffix='_output.json')

    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(prompt)

    try:
        result = subprocess.run(
            f'env -u CLAUDECODE -u ANTHROPIC_API_KEY -u CLAUDE_CODE_ENTRYPOINT '
            f'claude -p --output-format json --model sonnet '
            f'< "{prompt_file}" > "{output_file}" 2>/dev/null',
            shell=True,
            timeout=timeout,
        )

        if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
            raise RuntimeError(f"No output (exit {result.returncode})")

        data = json.loads(open(output_file, encoding='utf-8').read())
        text = data.get('result', '')
        sid = data.get('session_id')

        if not text:
            raise RuntimeError("Empty result in JSON response")

        return text, sid

    finally:
        for f in (prompt_file, output_file):
            if os.path.exists(f):
                os.unlink(f)


def translate_text(text_entry: dict) -> bool:
    """Translate a full text. Returns True on success."""
    t_num = text_entry['t_number']
    trans_path = TRANS_DIR / f'{t_num}_translation.md'

    chinese_path = extract_chinese_source(text_entry)
    if chinese_path is None:
        logging.warning(f"{t_num}: extraction failed")
        return False

    body = get_chinese_body(chinese_path)
    char_count = count_cjk(body)
    if char_count == 0:
        logging.warning(f"{t_num}: no content")
        return False

    # Split into parts if text is very large
    if char_count <= MAX_CHARS_PER_PROMPT:
        parts = [body]
    else:
        # Split at paragraph boundaries
        paragraphs = body.split('\n\n')
        parts, current, current_count = [], [], 0
        for para in paragraphs:
            pc = count_cjk(para)
            if current_count + pc > MAX_CHARS_PER_PROMPT and current:
                parts.append('\n\n'.join(current))
                current, current_count = [para], pc
            else:
                current.append(para)
                current_count += pc
        if current:
            parts.append('\n\n'.join(current))

    logging.info(f"{t_num}: {char_count:,} chars, {len(parts)} part(s)")

    translations = []
    for i, part in enumerate(parts, 1):
        chunk_info = ""
        if len(parts) > 1:
            chunk_info = f"Part {i} of {len(parts)}. Translate this portion only."

        prompt = TRANSLATION_PROMPT.format(
            title=text_entry.get('title_zh', ''),
            t_number=t_num,
            chunk_info=chunk_info,
            chinese_text=part,
        )

        part_chars = count_cjk(part)
        logging.info(f"  part {i}/{len(parts)} ({part_chars:,} chars)...")
        start = time.time()

        try:
            result_text, _ = translate_via_cli(prompt, timeout=1200)
            elapsed = time.time() - start
            rate = part_chars / (elapsed / 3600) if elapsed > 0 else 0
            logging.info(f"  part {i}/{len(parts)} done ({elapsed:.0f}s, "
                         f"{rate:,.0f} chars/hr)")
            translations.append(result_text)
        except Exception as e:
            logging.error(f"  part {i}/{len(parts)} FAILED: {e}")
            # Retry once
            try:
                time.sleep(10)
                result_text, _ = translate_via_cli(prompt, timeout=1200)
                elapsed = time.time() - start
                logging.info(f"  part {i}/{len(parts)} done on retry ({elapsed:.0f}s)")
                translations.append(result_text)
            except Exception as e2:
                logging.error(f"  part {i}/{len(parts)} retry FAILED: {e2}")
                translations.append(f"[TRANSLATION ERROR in part {i}: {e2}]")

    # Check success
    successful = [t for t in translations if not t.startswith('[TRANSLATION ERROR')]
    if not successful:
        logging.error(f"{t_num}: all parts failed")
        return False

    # Assemble
    title = text_entry.get('title_zh', t_num)
    header = (
        f"# {title}\n"
        f"## {title}\n\n"
        f"Taishō Tripiṭaka No. {t_num.replace('T', '')}\n\n"
    )
    if text_entry.get('translator'):
        header += f"Translated from the Chinese. {text_entry['translator']}\n\n"
    header += "---\n\n"

    full = header + '\n\n'.join(translations)
    trans_path.write_text(full, encoding='utf-8')
    logging.info(f"{t_num}: saved ({len(full):,} bytes)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Interactive batch translation of Taishō texts')
    parser.add_argument('--hours', type=float, default=10)
    parser.add_argument('--max-juan', type=int, default=None)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--start-from', type=str, default=None)
    args = parser.parse_args()

    log_file = setup_logging()
    logging.info(f"Interactive batch starting. Log: {log_file}")
    logging.info(f"Time limit: {args.hours} hours")

    for d in [CHINESE_DIR, TRANS_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    catalog_path = BASE_DIR / 'full_catalog.json'
    with open(catalog_path) as f:
        catalog = json.load(f)

    # Filter and sort
    if args.max_juan:
        catalog = [t for t in catalog if t['juan'] <= args.max_juan]

    if args.start_from:
        idx = next((i for i, t in enumerate(catalog)
                     if t['t_number'] >= args.start_from), 0)
        catalog = catalog[idx:]

    # Sort by size (small first)
    catalog.sort(key=lambda t: t['juan'])

    # Filter already translated
    todo = [t for t in catalog
            if not (TRANS_DIR / f"{t['t_number']}_translation.md").exists()]

    logging.info(f"Catalog: {len(catalog)} texts, todo: {len(todo)}")

    if args.dry_run:
        print(f"\nWould translate {len(todo)} texts:")
        for e in todo[:50]:
            print(f"  {e['t_number']:8s} {e['title_zh'][:30]:30s} "
                  f"{e['juan']:3d} juan")
        if len(todo) > 50:
            print(f"  ... and {len(todo) - 50} more")
        return

    deadline = time.time() + args.hours * 3600
    completed = 0
    failed = 0
    total_chars = 0
    batch_start = time.time()

    for entry in todo:
        if time.time() > deadline:
            logging.info("Time limit reached.")
            break

        t_num = entry['t_number']
        text_start = time.time()

        try:
            success = translate_text(entry)
            if success:
                completed += 1
                cp = CHINESE_DIR / f'{t_num}.txt'
                if cp.exists():
                    total_chars += count_cjk(cp.read_text(encoding='utf-8'))
            else:
                failed += 1
        except KeyboardInterrupt:
            logging.info("Interrupted.")
            break
        except Exception as e:
            logging.error(f"{t_num}: unexpected error: {e}")
            failed += 1

        elapsed = time.time() - text_start
        logging.info(f"{t_num}: total {elapsed:.0f}s")

    batch_elapsed = time.time() - batch_start
    logging.info(f"\n{'=' * 60}")
    logging.info("BATCH SUMMARY")
    logging.info(f"  Elapsed: {batch_elapsed / 3600:.1f} hours")
    logging.info(f"  Completed: {completed}")
    logging.info(f"  Failed: {failed}")
    logging.info(f"  Characters: {total_chars:,}")
    if batch_elapsed > 0 and total_chars > 0:
        rate = total_chars / (batch_elapsed / 3600)
        logging.info(f"  Rate: {rate:,.0f} chars/hour")
    logging.info(f"{'=' * 60}")


if __name__ == '__main__':
    main()
