#!/usr/bin/env python3
"""
Translate T2058 (付法藏因緣傳) via Anthropic Batch API.

Splits into 6 fascicles, submits with comprehensive system prompt
enforcing all BDK conventions and style rules.
"""

import anthropic
import json
import re
import time
from pathlib import Path

BASE = Path(__file__).parent
CHINESE_FILE = BASE.parent / "chinese" / "T2058.txt"
GLOSSARY_FILE = BASE / "glossary.md"
OUTPUT_FILE = BASE.parent / "translations" / "T2058_translation.md"

MODEL = "claude-opus-4-6"

# Read glossary to include in system prompt
glossary_text = GLOSSARY_FILE.read_text(encoding="utf-8")

SYSTEM_PROMPT = r"""You are translating T2058 付法藏因緣傳 (Accounts of the Transmission of the Dharma Treasury), a Northern Wei text co-translated by Jikiyaye (吉迦夜) and Tanyao (曇曜), ca. 472 CE. It narrates the transmission of the Dharma from Śākyamuni Buddha through 23 Indian patriarchs to Siṃha Bhikṣu.

OUTPUT FORMAT:
- Output ONLY the English translation. No preamble, no commentary.
- Use ## for fascicle headings (e.g., "## Fascicle One")
- Use ### for patriarch/chapter headings
- Use > for verse blocks (gāthās)
- Preserve paragraph structure from the Chinese

STYLE RULES — ENFORCE STRICTLY:

DIACRITICS (always use IAST):
- sūtra, nirvāṇa, Śākyamuni, bhikṣu, kāṣāya, dhāraṇī, prajñā, samādhi
- Use "Sangha" (not "Saṅgha")

PUNCTUATION:
- NEVER use em-dashes (—). Use commas, semicolons, colons, or periods.
- No translator brackets [like this]. Integrate clarifications naturally.

BDK CONVENTIONS:
- "World-Honored One" for 世尊
- "Three Treasures" for 三宝
- "enlightenment" for 菩提 (not "awakening")
- "roots of merit" for 善根
- "Tathāgata" for 如来 (transliterated with macron)
- "skillful means" for 方便
- "sentient beings" for 衆生
- "wholesome/unwholesome" for 善/不善
- "arhat" for 阿羅漢 (lowercase, transliterated)
- "nirvāṇa" for 涅槃 (transliterated with IAST)
- "Four Noble Truths" (always capitalized)
- "Eightfold Path" (always capitalized)
- "Buddha-nature" (capital B, hyphenated)

WHERE CHINESE SAYS 云云:
- Write "and so forth" or "the standard formula is recited"

GENRE GUIDANCE:
- This is sacred narrative biography, not doctrinal exposition
- Maintain literary quality befitting the dignity of the subject
- Verse sections (gāthās) should be rendered as poetry with line breaks
- Death/parinirvāṇa accounts should maintain solemnity
- Dialogue should feel natural while preserving formality
- Past-life stories (jātaka-style) should be vivid and engaging

PATRIARCH NAMES (use these exact IAST forms throughout):
""" + """
1. Mahākāśyapa (摩訶迦葉)
2. Ānanda (阿難)
3. Śāṇakavāsa (商那和修)
4. Upagupta (憂波毱多)
5. Dhṛtaka (提多迦)
6. Micchaka (彌遮迦)
7. Buddhanandin (佛陀難提)
8. Buddhamitra (佛陀蜜多)
9. Pārśva (脇尊者)
10. Puṇyayaśas (富那夜奢)
11. Aśvaghoṣa (馬鳴)
12. Kapimala (迦毘摩羅)
13. Nāgārjuna (龍樹)
14. Āryadeva (迦那提婆/提婆)
15. Rāhulata (羅睺羅多)
16. Saṅghanandi (僧伽難提)
17. Saṅghayaśas (僧伽耶舍)
18. Kumārata (鳩摩羅多)
19. Jayata (闍夜多)
20. Vasubandhu (婆修盤頭)
21. Manorhita (摩拏羅)
22. Haklenayaśas (鶴勒那夜奢)
23. Siṃha Bhikṣu (師子比丘)

FULL GLOSSARY:
""" + glossary_text


def split_fascicles(text):
    """Split Chinese text at fascicle boundaries using ======== headers."""
    # Split at the ======== Fascicle NNN: headers
    pattern = r'={10,}\nFascicle \d+:.*?\n={10,}\n'
    parts = re.split(pattern, text)

    # First part is the file header (# title, etc.), skip it
    # Remaining parts are fascicle bodies (may have duplicate headers inside)
    fascicles = []
    for i, part in enumerate(parts):
        body = part.strip()
        if not body or body.startswith('#'):
            continue
        # Remove duplicate internal fascicle headers
        body = re.sub(r'={10,}\nFascicle \d+:.*?\n={10,}\n?', '', body).strip()
        if body:
            fascicles.append((len(fascicles) + 1, body))

    return fascicles


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retrieve", type=str, default=None)
    args = parser.parse_args()

    if args.retrieve:
        retrieve_results(args.retrieve)
        return

    # Read Chinese source
    chinese = CHINESE_FILE.read_text(encoding="utf-8")
    fascicles = split_fascicles(chinese)
    print(f"Split into {len(fascicles)} fascicles")

    # Build requests
    requests = []
    for fasc_num, fasc_text in fascicles:
        if not fasc_text.strip():
            continue

        user_msg = (
            f"Translate Fascicle {fasc_num} of the Accounts of the Transmission "
            f"of the Dharma Treasury (付法藏因緣傳, T2058) into English.\n\n"
            f"Translate EVERYTHING in full. Do not skip or summarize.\n\n"
            f"Chinese text:\n\n{fasc_text}"
        )

        request = {
            "custom_id": f"T2058_fasc_{fasc_num:02d}",
            "params": {
                "model": MODEL,
                "max_tokens": 16384,
                "system": [{
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }],
                "messages": [{"role": "user", "content": user_msg}]
            }
        }
        requests.append(request)

    print(f"Total requests: {len(requests)}")

    if args.dry_run:
        # Estimate cost
        input_chars = sum(len(f[1]) for f in fascicles)
        input_tokens = input_chars // 2 + len(SYSTEM_PROMPT) // 4
        output_tokens = input_tokens * 2
        cost = input_tokens / 1e6 * 2.50 + output_tokens / 1e6 * 12.50
        print(f"Estimated: {input_tokens:,} input tokens, {output_tokens:,} output")
        print(f"Estimated cost: ${cost:.2f}")
        return

    # Submit batch
    client = anthropic.Anthropic()
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch submitted: {batch.id}")

    # Save batch ID
    with open(BASE / "batch_info.json", "w") as f:
        json.dump({"batch_id": batch.id, "requests": len(requests)}, f, indent=2)

    # Poll
    while True:
        b = client.messages.batches.retrieve(batch.id)
        c = b.request_counts
        print(f"[{time.strftime('%H:%M:%S')}] succeeded={c.succeeded}, "
              f"processing={c.processing}, errored={c.errored}")
        if b.processing_status == "ended":
            break
        time.sleep(30)

    retrieve_results(batch.id)


def retrieve_results(batch_id):
    """Retrieve and assemble translation results."""
    client = anthropic.Anthropic()
    results = {}
    total_input = 0
    total_output = 0

    for r in client.messages.batches.results(batch_id):
        num = int(r.custom_id.split("_fasc_")[1])
        if r.result.type == "succeeded":
            results[num] = r.result.message.content[0].text
            total_input += r.result.message.usage.input_tokens
            total_output += r.result.message.usage.output_tokens

    # Assemble with header
    header = """# 付法藏因緣傳
## Accounts of the Transmission of the Dharma Treasury

Taishō Tripiṭaka No. 2058

Translated from the Chinese. Northern Wei dynasty (~472 CE),
co-translated by Jikiyaye (吉迦夜) and Tanyao (曇曜).

---

"""
    full = header + "\n\n".join(results[i] for i in sorted(results.keys()))
    OUTPUT_FILE.write_text(full, encoding="utf-8")
    print(f"Saved: {OUTPUT_FILE} ({len(full):,} chars, {len(results)} fascicles)")

    cost = total_input / 1e6 * 2.50 + total_output / 1e6 * 12.50
    print(f"Tokens: {total_input:,} input, {total_output:,} output")
    print(f"Cost: ${cost:.2f}")


if __name__ == "__main__":
    main()
