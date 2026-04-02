#!/usr/bin/env python3
"""Translate Chinese Buddhist texts to English using Claude API.

Processes texts fascicle by fascicle, records timing data,
and saves translations with metadata.
"""

import json
import re
import sys
import time
from pathlib import Path

import anthropic

# Maximum chars per API call (Claude can handle ~100K+ tokens, but we chunk
# for better quality and to stay within output limits)
CHUNK_SIZE = 8000  # CJK chars per chunk (~24K tokens input)

SYSTEM_PROMPT = """You are an expert translator of classical Chinese Buddhist texts (漢文佛典). \
Translate the following Chinese Buddhist text into clear, accurate English.

Guidelines:
- Preserve the meaning and tone of the original
- Use standard English Buddhist terminology (e.g., "Thus have I heard" for 如是我聞)
- Transliterate Sanskrit/Pali proper names rather than translating them \
(e.g., Śāriputra not "Son of Śāri"; Ānanda not "Joy")
- For technical terms, use the most widely accepted English rendering \
(e.g., "suffering" or "duḥkha" for 苦, "emptiness" for 空, "nirvāṇa" for 涅槃)
- Preserve verse structure: translate verses as verses with line breaks
- Mark dhāraṇī passages with [Dhāraṇī] and transliterate rather than translate
- Use paragraph breaks to match the source structure
- For fascicle headers (lines starting with "Fascicle"), render as "Fascicle N" section headers
- For section headings (lines starting with "##"), translate the heading
- Do not add explanatory notes or commentary; produce a clean translation only
- Maintain the dignity and literary quality appropriate to sacred scripture"""


def count_cjk(text: str) -> int:
    """Count CJK characters in text."""
    return len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', text))


def split_into_chunks(text: str, max_cjk: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks at paragraph boundaries, respecting max CJK char count."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = []
    current_count = 0

    for para in paragraphs:
        para_count = count_cjk(para)

        # If a single paragraph exceeds the limit, split it at sentence boundaries
        if para_count > max_cjk:
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_count = 0
            # Split long paragraph at Chinese sentence boundaries
            sentences = re.split(r'(?<=[。！？])', para)
            sent_chunk = []
            sent_count = 0
            for sent in sentences:
                sc = count_cjk(sent)
                if sent_count + sc > max_cjk and sent_chunk:
                    chunks.append(''.join(sent_chunk))
                    sent_chunk = [sent]
                    sent_count = sc
                else:
                    sent_chunk.append(sent)
                    sent_count += sc
            if sent_chunk:
                chunks.append(''.join(sent_chunk))
            continue

        if current_count + para_count > max_cjk and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = [para]
            current_count = para_count
        else:
            current_chunk.append(para)
            current_count += para_count

    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))

    return chunks


def translate_chunk(client: anthropic.Anthropic, chunk: str, text_info: dict,
                    chunk_num: int, total_chunks: int) -> str:
    """Translate a single chunk of Chinese text."""
    user_msg = f"""Translate this passage from {text_info['title_zh']} ({text_info['title_en']}), \
Taishō {text_info['t_number']}, {text_info['genre']} genre.

Chunk {chunk_num}/{total_chunks}:

{chunk}"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text


def translate_text(client: anthropic.Anthropic, chinese_path: Path,
                   text_info: dict, output_dir: Path) -> dict:
    """Translate a full text, recording timing data."""
    t_num = text_info['t_number']
    print(f"\n{'=' * 60}")
    print(f"Translating {t_num}: {text_info['title_zh']} ({text_info['title_en']})")
    print(f"Genre: {text_info['genre']}, Tier: {text_info['tier']}, "
          f"Juan: {text_info['juan']}")
    print(f"{'=' * 60}")

    # Read Chinese source
    chinese_text = chinese_path.read_text(encoding='utf-8')

    # Skip header lines (starting with #)
    body_lines = []
    for line in chinese_text.split('\n'):
        if line.startswith('#') and not line.startswith('##'):
            continue
        body_lines.append(line)
    body = '\n'.join(body_lines).strip()

    cjk_count = count_cjk(body)
    print(f"Source: {cjk_count:,} CJK characters")

    # Split into chunks
    chunks = split_into_chunks(body)
    print(f"Split into {len(chunks)} chunks")

    # Translate each chunk
    translations = []
    start_time = time.time()

    for i, chunk in enumerate(chunks, 1):
        chunk_cjk = count_cjk(chunk)
        print(f"  Chunk {i}/{len(chunks)} ({chunk_cjk:,} CJK chars)...", end='', flush=True)
        chunk_start = time.time()

        try:
            translation = translate_chunk(client, chunk, text_info, i, len(chunks))
            chunk_elapsed = time.time() - chunk_start
            print(f" done ({chunk_elapsed:.1f}s)")
            translations.append(translation)
        except Exception as e:
            chunk_elapsed = time.time() - chunk_start
            print(f" ERROR ({chunk_elapsed:.1f}s): {e}")
            translations.append(f"[TRANSLATION ERROR: {e}]")

    total_time = time.time() - start_time

    # Combine translations
    full_translation = '\n\n'.join(translations)

    # Build output with header
    header = (
        f"# {text_info['title_en']}\n"
        f"## {text_info['title_zh']}\n\n"
        f"Taishō Tripiṭaka No. {t_num.replace('T', '')}\n\n"
    )
    if text_info.get('title_skt'):
        header += f"Sanskrit: *{text_info['title_skt']}*\n\n"
    header += (
        f"Translated from the Chinese by {text_info['translator']}\n\n"
        f"---\n\n"
    )

    output_text = header + full_translation

    # Save translation
    out_path = output_dir / f'{t_num}_translation.md'
    out_path.write_text(output_text, encoding='utf-8')
    print(f"\nSaved translation to {out_path}")

    # Timing data
    timing = {
        't_number': t_num,
        'title_zh': text_info['title_zh'],
        'title_en': text_info['title_en'],
        'genre': text_info['genre'],
        'tier': text_info['tier'],
        'juan': text_info['juan'],
        'cjk_chars': cjk_count,
        'chunks': len(chunks),
        'translation_time_sec': round(total_time, 1),
        'translation_time_min': round(total_time / 60, 1),
        'chars_per_hour': round(cjk_count / (total_time / 3600)) if total_time > 0 else 0,
    }

    print(f"\nTiming: {timing['translation_time_min']} min "
          f"({timing['chars_per_hour']:,} chars/hour)")

    return timing


def main():
    base_dir = Path.home() / 'taisho-translation-sample'
    chinese_dir = base_dir / 'chinese'
    output_dir = base_dir / 'translations'
    logs_dir = base_dir / 'logs'
    output_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Load sample texts config
    with open(base_dir / 'sample_texts.json') as f:
        sample_texts = json.load(f)

    # Parse command-line args for tier/text selection
    selected = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('T'):
            # Specific text: translate.py T0002
            selected = [t for t in sample_texts if t['t_number'] == arg]
        elif arg.isdigit():
            # Tier: translate.py 1
            tier = int(arg)
            selected = [t for t in sample_texts if t['tier'] == tier]
    if selected is None:
        selected = sample_texts

    print(f"Will translate {len(selected)} text(s)")

    # Initialize Claude client
    client = anthropic.Anthropic()

    # Load existing timing log
    timing_path = logs_dir / 'timing_log.json'
    if timing_path.exists():
        with open(timing_path) as f:
            timing_log = json.load(f)
    else:
        timing_log = []

    existing_tnums = {t['t_number'] for t in timing_log}

    for text_info in selected:
        t_num = text_info['t_number']
        chinese_path = chinese_dir / f'{t_num}.txt'

        if not chinese_path.exists():
            print(f"\nSkipping {t_num}: Chinese source not yet extracted")
            continue

        # Check if already translated
        trans_path = output_dir / f'{t_num}_translation.md'
        if trans_path.exists() and t_num in existing_tnums:
            print(f"\nSkipping {t_num}: already translated")
            continue

        timing = translate_text(client, chinese_path, text_info, output_dir)

        # Update timing log
        timing_log = [t for t in timing_log if t['t_number'] != t_num]
        timing_log.append(timing)
        with open(timing_path, 'w') as f:
            json.dump(timing_log, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'=' * 60}")
    print("TRANSLATION SUMMARY")
    print(f"{'=' * 60}")
    for t in sorted(timing_log, key=lambda x: x['tier']):
        print(f"  {t['t_number']:8s} {t['title_en'][:40]:40s} "
              f"{t['translation_time_min']:6.1f} min  "
              f"{t['chars_per_hour']:>10,} chars/hr")

    total_chars = sum(t['cjk_chars'] for t in timing_log)
    total_time = sum(t['translation_time_sec'] for t in timing_log)
    if total_time > 0:
        overall_rate = round(total_chars / (total_time / 3600))
        print(f"\n  Total: {total_chars:,} chars in {total_time/60:.1f} min "
              f"({overall_rate:,} chars/hr)")


if __name__ == '__main__':
    main()
