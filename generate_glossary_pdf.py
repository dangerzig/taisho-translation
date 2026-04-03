#!/usr/bin/env python3
"""Generate a formatted Markdown glossary from glossary_data.json for PDF conversion."""

import json
from collections import defaultdict

with open("/Users/danzigmond/taisho-translation/glossary_data.json") as f:
    entries = json.load(f)

# Sort entries alphabetically by English within each category
category_labels = {
    "person": "Personal Names",
    "place": "Place Names",
    "title": "Titles and Honorifics",
    "doctrinal": "Doctrinal Terms",
    "practice": "Practices and Attainments",
    "cosmological": "Cosmological Terms",
    "monastic_item": "Monastic Items",
    "other": "Other Terms",
}

# Group by category
by_category = defaultdict(list)
for e in entries:
    by_category[e["category"]].append(e)

# Sort each group
for cat in by_category:
    by_category[cat].sort(key=lambda x: x["english"].lower())

lines = []
lines.append("---")
lines.append("title: \"Master Glossary of Buddhist Terms\"")
lines.append("subtitle: \"Taishō Tripiṭaka Translation Project\"")
lines.append("author: \"Dan Zigmond\"")
lines.append("date: \"April 2026\"")
lines.append("---")
lines.append("")
lines.append("# Master Glossary of Buddhist Terms")
lines.append("")
lines.append(f"This glossary contains {len(entries)} terms extracted from {len(set(s for e in entries for s in e['sources']))} translated texts in the Taishō Tripiṭaka Translation Project. Each entry lists the English rendering, Chinese original, Sanskrit or Pali equivalent (where known), and the source texts where the term appears.")
lines.append("")

# Category order
cat_order = ["person", "place", "title", "doctrinal", "practice", "cosmological", "monastic_item", "other"]

for cat in cat_order:
    if cat not in by_category:
        continue
    group = by_category[cat]
    label = category_labels.get(cat, cat.title())
    lines.append(f"## {label} ({len(group)} entries)")
    lines.append("")

    for e in group:
        english = e["english"]
        chinese = e.get("chinese", "")
        sanskrit = e.get("sanskrit", "")
        sources = e.get("sources", [])

        # Build the entry line
        parts = [f"**{english}**"]
        if chinese:
            parts.append(f"({chinese})")
        if sanskrit and sanskrit != english:
            parts.append(f"Skt. *{sanskrit}*")

        source_str = ", ".join(sorted(sources))
        parts.append(f"[{source_str}]")

        lines.append(" ".join(parts))
        lines.append("")

output_path = "/Users/danzigmond/taisho-translation/glossary.md"
with open(output_path, "w") as f:
    f.write("\n".join(lines))

print(f"Glossary written to {output_path}")
print(f"Total entries: {len(entries)}")
print(f"Categories: {len(by_category)}")
