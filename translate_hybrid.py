#!/usr/bin/env python3
"""
Hybrid Sonnet-then-Opus translation pipeline using Claude Max subscription.

Step 1: Sonnet produces a fast first draft.
Step 2: Opus reviews the draft against the Chinese source and corrects errors.

Uses `claude` CLI (not API credits) via subprocess with env vars unset
to force subscription billing.

Usage:
  python3 translate_hybrid.py T0080          # translate one text
  python3 translate_hybrid.py T0080 T0081    # translate multiple
  python3 translate_hybrid.py --batch 10     # next 10 untranslated texts
  python3 translate_hybrid.py --review-only  # Opus review pass on existing drafts

Writes to translations/TNNNN_translation.md
"""

import json
import os
import subprocess
import sys
import time

BASE = "/Users/danzigmond/taisho-translation"
CATALOG = os.path.join(BASE, "full_catalog.json")
CHINESE_DIR = os.path.join(BASE, "chinese")
TRANSLATIONS_DIR = os.path.join(BASE, "translations")

SONNET_MODEL = "sonnet"
OPUS_MODEL = "opus"

TRANSLATION_PROMPT = """You are a scholar of Chinese Buddhist texts translating from the Taishō Tripiṭaka into English. Produce a complete, faithful, scholarly translation.

Translate the following Chinese Buddhist text into English following these conventions:

HEADER FORMAT (mandatory):
# {Chinese title}
## {English title}

Taishō Tripiṭaka No. {number}

Translated from the Chinese. {Dynasty in English}, translated by {Translator name in IAST/English} ({Chinese name})

---

If the translator is listed as 失譯, write: "Translator unknown (失譯)"

TRANSLATION CONVENTIONS:
- Use Sanskrit (not Pali) for all technical terms: bhikṣu (not bhikkhu), Dharma (not Dhamma), nirvāṇa (not nibbāna), etc.
- Use IAST diacritics for all Sanskrit/Pali names and terms: Śrāvastī, Ānanda, Māra, etc.
- Translate "世尊" as "World-Honored One" (capital H)
- Translate "佛" as "the Buddha" or "the World-Honored One" as context requires
- Translate "比丘" as "bhikṣu" (not "monk")
- Render verse passages with ">" prefix on each line
- Do NOT include "Fascicle N" headers or sub-headers
- Do NOT leave any Chinese characters in the translation
- Reconstruct proper names to their Sanskrit/Pali originals where identifiable
- Translate ALL text faithfully and completely. Do not summarize or skip passages.

Here is the Chinese text:

"""

REVIEW_PROMPT = """You are a senior scholar reviewing an AI-generated English translation of a Chinese Buddhist text from the Taishō Tripiṭaka. Your task is to compare the draft translation against the Chinese source and produce a corrected, improved version.

REVIEW INSTRUCTIONS:
1. Check every sentence against the Chinese source for accuracy and completeness.
2. Fix any mistranslations, omissions, or additions not in the source.
3. Ensure Sanskrit/Pali terms use IAST diacritics (e.g., Śrāvastī, bhikṣu, nirvāṇa).
4. Ensure proper names are reconstructed to Sanskrit/Pali originals where identifiable.
5. Ensure "世尊" → "World-Honored One", "比丘" → "bhikṣu", etc.
6. Ensure NO Chinese characters remain in the translation.
7. Ensure verse passages use ">" prefix on each line.
8. Ensure the translation is complete — no passages skipped or summarized.
9. Preserve the header format (# Chinese title / ## English title / Taishō No. / etc.)

OUTPUT: The complete corrected translation. Do NOT output a list of changes or commentary. Output ONLY the full corrected translation text, ready for publication.

CHINESE SOURCE:
---
{chinese}
---

DRAFT TRANSLATION:
---
{draft}
---

Output the corrected translation now:
"""


def load_catalog():
    with open(CATALOG) as f:
        return json.load(f)


def get_existing_translations():
    existing = set()
    for fn in os.listdir(TRANSLATIONS_DIR):
        if fn.startswith("T") and fn.endswith("_translation.md"):
            existing.add(fn.split("_")[0])
    return existing


MAX_CJK_CHARS = 15000  # Skip texts larger than this (would exceed output limit)
REVIEWED_DIR = os.path.join(BASE, "translations", ".reviewed")


def call_claude(prompt, model, timeout=600):
    """Call claude CLI with the given prompt and model. Returns (text, elapsed) or (None, elapsed)."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDECODE", "ANTHROPIC_API_KEY")}

    start = time.time()
    max_retries = 5
    result = None

    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                ["claude", "-p", prompt, "--model", model, "--output-format", "text"],
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            print(f"  ERROR: Timed out ({timeout}s)")
            return None, time.time() - start
        except Exception as e:
            print(f"  ERROR: CLI call failed: {e}")
            return None, time.time() - start

        if result.returncode == 0:
            break

        wait = 60 * (attempt + 1)
        print(f"  CLI returned {result.returncode}, retry {attempt+1}/{max_retries} in {wait}s...")
        time.sleep(wait)
    else:
        print(f"  ERROR: Failed after {max_retries} retries")
        if result and result.stderr:
            print(f"  stderr: {result.stderr[:500]}")
        return None, time.time() - start

    elapsed = time.time() - start
    text = result.stdout.strip()
    return text, elapsed


def is_reviewed(t_number):
    """Check if a translation has already been Opus-reviewed."""
    return os.path.exists(os.path.join(REVIEWED_DIR, f"{t_number}.done"))


def mark_reviewed(t_number):
    """Mark a translation as Opus-reviewed."""
    os.makedirs(REVIEWED_DIR, exist_ok=True)
    with open(os.path.join(REVIEWED_DIR, f"{t_number}.done"), "w") as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S\n"))


def review_translation(t_number):
    """Run Opus review pass on an existing Sonnet draft."""
    chinese_file = os.path.join(CHINESE_DIR, f"{t_number}.txt")
    output_file = os.path.join(TRANSLATIONS_DIR, f"{t_number}_translation.md")

    if not os.path.exists(chinese_file):
        print(f"  ERROR: No Chinese text for {t_number}")
        return False
    if not os.path.exists(output_file):
        print(f"  ERROR: No draft translation for {t_number}")
        return False

    with open(chinese_file) as f:
        chinese_text = f.read()
    with open(output_file) as f:
        draft = f.read()

    cjk_chars = sum(1 for c in chinese_text if "\u4e00" <= c <= "\u9fff")
    print(f"  Opus review of {t_number} ({cjk_chars:,} CJK chars)...")

    prompt = REVIEW_PROMPT.format(chinese=chinese_text, draft=draft)

    reviewed, elapsed = call_claude(prompt, OPUS_MODEL, timeout=900)

    if reviewed is None or len(reviewed) < 100:
        print(f"  ERROR: Review too short or failed")
        return False

    # Save reviewed version (overwrite draft)
    with open(output_file, "w") as f:
        f.write(reviewed + "\n")

    mark_reviewed(t_number)
    print(f"  Opus review done in {elapsed:.1f}s")
    return True


def get_untranslated(catalog, existing, limit=None):
    untranslated = []
    skipped_large = 0
    for t in sorted(catalog, key=lambda x: x["t_number"]):
        tn = t["t_number"]
        if tn not in existing:
            chinese_file = os.path.join(CHINESE_DIR, f"{tn}.txt")
            if os.path.exists(chinese_file):
                size = os.path.getsize(chinese_file)
                if size > 100:
                    # Count actual CJK characters
                    with open(chinese_file) as f:
                        text = f.read()
                    cjk = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
                    if cjk > MAX_CJK_CHARS:
                        skipped_large += 1
                        continue
                    untranslated.append((tn, t, size))
    # Sort by file size (smallest first) for fastest throughput
    untranslated.sort(key=lambda x: x[2])
    if skipped_large:
        print(f"Skipped {skipped_large} texts exceeding {MAX_CJK_CHARS:,} CJK chars")
    if limit:
        untranslated = untranslated[:limit]
    return untranslated


def translate_text(t_number, catalog_entry):
    chinese_file = os.path.join(CHINESE_DIR, f"{t_number}.txt")
    output_file = os.path.join(TRANSLATIONS_DIR, f"{t_number}_translation.md")

    if not os.path.exists(chinese_file):
        print(f"  ERROR: No Chinese text for {t_number}")
        return False, 0

    with open(chinese_file) as f:
        chinese_text = f.read()

    cjk_chars = sum(1 for c in chinese_text if "\u4e00" <= c <= "\u9fff")
    print(f"  Translating {t_number} ({catalog_entry.get('title_zh', '')})...")
    print(f"  CJK characters: {cjk_chars:,}")

    # Step 1: Sonnet draft
    prompt = TRANSLATION_PROMPT + chinese_text
    print(f"  Step 1: Sonnet draft...")

    translation, sonnet_time = call_claude(prompt, SONNET_MODEL)

    if translation is None or len(translation) < 100:
        print(f"  ERROR: Sonnet draft too short or failed")
        return False, 0

    with open(output_file, "w") as f:
        f.write(translation + "\n")

    rate = cjk_chars / sonnet_time * 3600 if sonnet_time > 0 else 0
    print(f"  Sonnet draft done in {sonnet_time:.1f}s ({rate:,.0f} CJK chars/hr)")

    # Step 2: Opus review
    print(f"  Step 2: Opus review...")
    ok = review_translation(t_number)
    if not ok:
        print(f"  WARNING: Opus review failed, keeping Sonnet draft")

    total_time = time.time()  # for outer timing
    print(f"  Output: {output_file}")

    return True, cjk_chars


def get_unreviewed():
    """Find translations that exist but haven't been Opus-reviewed."""
    unreviewed = []
    for fn in sorted(os.listdir(TRANSLATIONS_DIR)):
        if fn.startswith("T") and fn.endswith("_translation.md"):
            tn = fn.split("_")[0]
            if not is_reviewed(tn):
                unreviewed.append(tn)
    return unreviewed


def main():
    catalog = load_catalog()
    catalog_map = {t["t_number"]: t for t in catalog}
    existing = get_existing_translations()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 translate_hybrid.py T0080             # translate + review")
        print("  python3 translate_hybrid.py --batch 10        # next 10 untranslated")
        print("  python3 translate_hybrid.py --review-only     # Opus review unreviewed drafts")
        print("  python3 translate_hybrid.py --review-only 20  # review up to 20 drafts")
        sys.exit(1)

    if sys.argv[1] == "--review-only":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
        unreviewed = get_unreviewed()
        if limit:
            unreviewed = unreviewed[:limit]
        print(f"Opus reviewing {len(unreviewed)} unreviewed translations...")
        success = 0
        for tn in unreviewed:
            print(f"\n{'='*60}")
            print(f"[{success+1}/{len(unreviewed)}] {tn}")
            print(f"{'='*60}")
            ok = review_translation(tn)
            if ok:
                success += 1
        print(f"\nReviewed: {success}/{len(unreviewed)}")
        sys.exit(0)

    if sys.argv[1] == "--batch":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        texts = get_untranslated(catalog, existing, limit)
        print(f"Batch translating {len(texts)} texts (Sonnet draft + Opus review)...")
    else:
        texts = []
        for arg in sys.argv[1:]:
            tn = arg if arg.startswith("T") else f"T{arg}"
            if tn in catalog_map:
                chinese_file = os.path.join(CHINESE_DIR, f"{tn}.txt")
                size = os.path.getsize(chinese_file) if os.path.exists(chinese_file) else 0
                texts.append((tn, catalog_map[tn], size))
            else:
                print(f"WARNING: {tn} not in catalog")

    if not texts:
        print("No texts to translate.")
        sys.exit(0)

    total_chars = 0
    total_time = 0
    success = 0

    for tn, entry, size in texts:
        if tn in existing:
            print(f"Skipping {tn} (already translated)")
            continue

        print(f"\n{'='*60}")
        print(f"[{success+1}/{len(texts)}] {tn}: {entry.get('title_zh', '')}")
        print(f"{'='*60}")

        start = time.time()
        ok, chars = translate_text(tn, entry)
        elapsed = time.time() - start

        if ok:
            success += 1
            total_chars += chars
            total_time += elapsed

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Translated: {success}/{len(texts)}")
    if total_time > 0:
        print(f"Total CJK chars: {total_chars:,}")
        print(f"Total time: {total_time:.1f}s ({total_time/60:.1f}min)")
        print(f"Average rate: {total_chars / total_time * 3600:,.0f} CJK chars/hr")


if __name__ == "__main__":
    main()
