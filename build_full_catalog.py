#!/usr/bin/env python3
"""Scan CBETA XML corpus and build a complete catalog of all Taishō texts.

Reads metadata (title, translator, fascicle count) from teiHeader of each text.
Outputs full_catalog.json with one entry per text.
"""

import json
import re
from collections import defaultdict
from pathlib import Path

from lxml import etree

# Namespaces
TEI = '{http://www.tei-c.org/ns/1.0}'
CB = '{http://www.cbeta.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'


def scan_xml_corpus(xml_base: Path) -> dict[str, list[Path]]:
    """Find all XML files and group by CBETA text ID (e.g., T01n0001, T02n0128a)."""
    texts = defaultdict(list)
    for xml_file in sorted(xml_base.glob('T*/T*n*_*.xml')):
        match = re.match(r'(T\d+n\d+[a-bA-B]?)_\d+\.xml', xml_file.name)
        if match:
            texts[match.group(1)].append(xml_file)
    return dict(texts)


def cbeta_id_to_t_number(cbeta_id: str) -> str:
    """Convert CBETA ID to Taishō number: T01n0001 -> T0001, T02n0128a -> T0128a."""
    match = re.match(r'T\d+n(\d+)([a-bA-B]?)', cbeta_id)
    if match:
        num = int(match.group(1))
        suffix = match.group(2)
        return f'T{num:04d}{suffix}'
    return cbeta_id


def get_metadata(xml_path: Path) -> dict:
    """Extract metadata from a single XML file's teiHeader."""
    meta = {}
    try:
        tree = etree.parse(str(xml_path))
    except etree.XMLSyntaxError:
        return meta

    root = tree.getroot()
    header = root.find(f'{TEI}teiHeader')
    if header is None:
        return meta

    # Title: prefer level="m" (monograph = individual text title)
    # over level="s" (series = 大正新脩大藏經)
    for title in header.iter(f'{TEI}title'):
        lang = title.get(f'{XML}lang', '')
        level = title.get('level', '')
        if lang == 'zh-Hant' and level == 'm':
            meta['title_zh'] = (title.text or '').strip()
            break
    # Fallback: first zh-Hant title without level="s"
    if 'title_zh' not in meta:
        for title in header.iter(f'{TEI}title'):
            lang = title.get(f'{XML}lang', '')
            level = title.get('level', '')
            if lang == 'zh-Hant' and level != 's':
                meta['title_zh'] = (title.text or '').strip()
                break

    # Author/translator
    author_elem = header.find(f'.//{TEI}author')
    if author_elem is not None:
        meta['translator'] = (author_elem.text or '').strip()

    # Extent (fascicle count)
    extent_elem = header.find(f'.//{TEI}extent')
    if extent_elem is not None:
        extent_text = extent_elem.text or ''
        m = re.search(r'(\d+)', extent_text)
        if m:
            meta['juan'] = int(m.group(1))

    return meta


def main():
    xml_base = Path.home() / 'taisho-canon' / 'xml' / 'T'
    output_path = Path.home() / 'taisho-translation' / 'full_catalog.json'

    print("Scanning CBETA XML corpus...")
    texts = scan_xml_corpus(xml_base)
    print(f"Found {len(texts)} texts")

    catalog = []
    for cbeta_id in sorted(texts.keys()):
        xml_files = texts[cbeta_id]
        t_number = cbeta_id_to_t_number(cbeta_id)
        volume = cbeta_id[:3]  # T01, T02, etc.

        # Get metadata from first file
        meta = get_metadata(xml_files[0])

        entry = {
            't_number': t_number,
            'cbeta_id': cbeta_id,
            'title_zh': meta.get('title_zh', ''),
            'translator': meta.get('translator', ''),
            'juan': meta.get('juan', len(xml_files)),
            'volume': volume,
            'xml_pattern': f"{volume}/{cbeta_id}_*.xml",
            'file_count': len(xml_files),
        }
        catalog.append(entry)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    # Summary
    total_juan = sum(e['juan'] for e in catalog)
    print(f"\nCatalog written to {output_path}")
    print(f"  {len(catalog)} texts, {total_juan} total fascicles")
    print(f"  Volumes: {catalog[0]['volume']} - {catalog[-1]['volume']}")

    # Size distribution
    sizes = [e['juan'] for e in catalog]
    print(f"  1 fascicle: {sum(1 for s in sizes if s == 1)} texts")
    print(f"  2-5 fascicles: {sum(1 for s in sizes if 2 <= s <= 5)} texts")
    print(f"  6-20 fascicles: {sum(1 for s in sizes if 6 <= s <= 20)} texts")
    print(f"  21-60 fascicles: {sum(1 for s in sizes if 21 <= s <= 60)} texts")
    print(f"  60+ fascicles: {sum(1 for s in sizes if s > 60)} texts")


if __name__ == '__main__':
    main()
