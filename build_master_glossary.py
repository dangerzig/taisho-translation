#!/usr/bin/env python3
"""
Build a master glossary merging BDK published glossaries with our own translations.

Sources:
  1. BDK glossary entries (bdk_glossary_entries.json) — from published BDK English Tripitaka volumes
  2. Our translation glossary (glossary_data.json) — extracted from our Taishō translations

Output:
  master_glossary.md — formatted Markdown for PDF conversion
"""

import json
import os
from collections import defaultdict

BASE = "/Users/danzigmond/taisho-translation"
BDK_FILE = os.path.join(BASE, "bdk_glossary_entries.json")
OUR_FILE = os.path.join(BASE, "glossary_data.json")
OUTPUT_MD = os.path.join(BASE, "master_glossary.md")

CATEGORY_LABELS = {
    "person": "Personal Names",
    "place": "Place Names",
    "title": "Titles and Honorifics",
    "doctrinal": "Doctrinal Terms",
    "practice": "Practices and Attainments",
    "cosmological": "Cosmological Terms",
    "monastic_item": "Monastic Items",
    "other": "Other Terms",
}

CATEGORY_ORDER = ["doctrinal", "practice", "cosmological", "person", "place",
                   "title", "monastic_item", "other"]


def normalize_term(term):
    """Normalize a term for matching (lowercase, strip diacritics loosely)."""
    return term.strip().lower()


def load_bdk_entries():
    """Load BDK glossary entries."""
    if not os.path.exists(BDK_FILE):
        print(f"WARNING: {BDK_FILE} not found, skipping BDK entries")
        return []
    with open(BDK_FILE) as f:
        return json.load(f)


def load_our_entries():
    """Load our translation glossary entries."""
    with open(OUR_FILE) as f:
        return json.load(f)


def merge_glossaries(bdk_entries, our_entries):
    """Merge BDK and our entries, preferring BDK definitions where available."""
    merged = {}

    # Index our entries by normalized English term
    for e in our_entries:
        key = normalize_term(e["english"])
        merged[key] = {
            "english": e["english"],
            "chinese": e.get("chinese", ""),
            "sanskrit": e.get("sanskrit", ""),
            "category": e.get("category", "other"),
            "definition": "",
            "source": "own",
        }

    # Overlay BDK entries — add definitions, mark source
    bdk_count = 0
    bdk_new = 0
    for e in bdk_entries:
        key = normalize_term(e["english"])
        if key in merged:
            # Existing term: add BDK definition and update source
            merged[key]["definition"] = e.get("definition", "")
            merged[key]["source"] = f"BDK {e.get('source', '')}"
            if e.get("sanskrit") and not merged[key]["sanskrit"]:
                merged[key]["sanskrit"] = e["sanskrit"]
            bdk_count += 1
        else:
            # New term from BDK
            merged[key] = {
                "english": e["english"],
                "chinese": "",
                "sanskrit": e.get("sanskrit", ""),
                "category": categorize_bdk_term(e),
                "definition": e.get("definition", ""),
                "source": f"BDK {e.get('source', '')}",
            }
            bdk_new += 1
            bdk_count += 1

    print(f"Our entries: {len(our_entries)}")
    print(f"BDK entries matched: {bdk_count - bdk_new}")
    print(f"BDK entries new: {bdk_new}")
    print(f"Total merged: {len(merged)}")

    return list(merged.values())


def categorize_bdk_term(entry):
    """Guess category for a BDK-only term based on its definition."""
    defn = (entry.get("definition", "") + " " + entry.get("english", "")).lower()

    person_hints = ["person", "saint", "sage", "buddha", "bodhisattva", "monk",
                    "king", "deity", "god", "goddess", "demon"]
    place_hints = ["place", "land", "realm", "mountain", "city", "heaven", "hell",
                   "world", "continent"]
    practice_hints = ["meditation", "practice", "concentration", "attainment",
                      "perfection", "stage", "path", "precept", "virtue"]
    cosmological_hints = ["eon", "kalpa", "age", "period", "realm", "existence",
                          "rebirth", "cycle"]

    for hint in person_hints:
        if hint in defn:
            return "person"
    for hint in place_hints:
        if hint in defn:
            return "place"
    for hint in practice_hints:
        if hint in defn:
            return "practice"
    for hint in cosmological_hints:
        if hint in defn:
            return "cosmological"
    return "doctrinal"


def generate_markdown(entries):
    """Generate formatted Markdown grouped by category."""
    by_category = defaultdict(list)
    for e in entries:
        by_category[e["category"]].append(e)

    for cat in by_category:
        by_category[cat].sort(key=lambda x: x["english"].lower())

    bdk_count = sum(1 for e in entries if e["source"].startswith("BDK"))
    own_count = sum(1 for e in entries if e["source"] == "own")

    lines = []
    lines.append("---")
    lines.append('title: "Master Glossary of Buddhist Terms"')
    lines.append('subtitle: "Taishō Tripiṭaka Translation Project"')
    lines.append('author: "Dan Zigmond"')
    lines.append('date: "April 2026"')
    lines.append("---")
    lines.append("")
    lines.append("# Master Glossary of Buddhist Terms")
    lines.append("")
    lines.append(f"This glossary contains {len(entries)} terms compiled from "
                 f"published BDK English Tripiṭaka glossaries ({bdk_count} entries) "
                 f"and our own Taishō translations ({own_count} entries). "
                 f"Each entry lists the English rendering, Chinese original, "
                 f"Sanskrit or Pali equivalent (where known), and source.")
    lines.append("")

    for cat in CATEGORY_ORDER:
        if cat not in by_category:
            continue
        group = by_category[cat]
        label = CATEGORY_LABELS.get(cat, cat.title())
        lines.append(f"## {label} ({len(group)} entries)")
        lines.append("")

        for e in group:
            english = e["english"]
            chinese = e.get("chinese", "")
            sanskrit = e.get("sanskrit", "")
            definition = e.get("definition", "")
            source = e.get("source", "own")

            # Build the entry
            parts = [f"**{english}**"]
            if chinese:
                parts.append(f"({chinese})")
            if sanskrit and sanskrit != english:
                parts.append(f"Skt. *{sanskrit}*")

            line = " ".join(parts)

            if definition:
                line += f": {definition}"

            # Source tag
            if source.startswith("BDK"):
                line += f" [{source}]"

            lines.append(line)
            lines.append("")

    return "\n".join(lines)


def main():
    bdk_entries = load_bdk_entries()
    our_entries = load_our_entries()
    merged = merge_glossaries(bdk_entries, our_entries)
    md = generate_markdown(merged)

    with open(OUTPUT_MD, "w") as f:
        f.write(md)

    print(f"\nMaster glossary written to {OUTPUT_MD}")


if __name__ == "__main__":
    main()
