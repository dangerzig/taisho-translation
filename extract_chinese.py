#!/usr/bin/env python3
"""Extract readable Chinese text from CBETA TEI P5b XML for translation.

Unlike digest_detector/extract.py (which strips to CJK-only), this preserves:
- Chinese punctuation (。，、；：「」『』（）！？etc.)
- Paragraph breaks
- Verse structure (<lg>/<l> → indented lines)
- Fascicle boundaries
- Section headings
"""

import json
import re
import sys
from pathlib import Path

from lxml import etree

# Namespaces
TEI = '{http://www.tei-c.org/ns/1.0}'
CB = '{http://www.cbeta.org/ns/1.0}'
XML = '{http://www.w3.org/XML/1998/namespace}'

# Tags to skip entirely
SKIP_TAGS = frozenset([
    f'{TEI}note',
    f'{TEI}rdg',
    f'{TEI}byline',
    f'{CB}docNumber',
    f'{TEI}lb',
    f'{TEI}pb',
    f'{TEI}milestone',
    f'{CB}mulu',
])

# Characters to preserve (CJK + Chinese punctuation + common symbols)
PRESERVE_RE = re.compile(
    r'[\u4E00-\u9FFF'         # CJK Unified
    r'\u3400-\u4DBF'          # CJK Extension A
    r'\U00020000-\U0002A6DF'  # CJK Extension B
    r'\U0002A700-\U0002B73F'  # CJK Extension C
    r'\U0002B740-\U0002B81F'  # CJK Extension D
    r'\u3000-\u303F'          # CJK Symbols and Punctuation (。、「」etc.)
    r'\uFF01-\uFF5E'          # Fullwidth Forms (！？，：；etc.)
    r'\uFE30-\uFE4F'          # CJK Compatibility Forms
    r'\u2018-\u201F'          # Quotation marks
    r'\u2E80-\u2EFF'          # CJK Radicals Supplement
    r']+'
)


def build_char_map(xml_files: list[Path]) -> dict[str, str]:
    """Build CB special character → Unicode map from XML charDecl sections."""
    char_map = {}
    for xml_path in xml_files:
        try:
            tree = etree.parse(str(xml_path))
        except etree.XMLSyntaxError:
            continue
        for char_elem in tree.iter(f'{TEI}char'):
            char_id = char_elem.get(f'{XML}id')
            if not char_id or char_id in char_map:
                continue
            resolved = None
            # Priority 1: normalized form
            for prop in char_elem.iter(f'{TEI}charProp'):
                local_name = prop.findtext(f'{TEI}localName')
                if local_name == 'normalized form':
                    value = prop.findtext(f'{TEI}value')
                    if value:
                        resolved = value
                        break
            # Priority 2: normal_unicode
            if not resolved:
                for mapping in char_elem.iter(f'{TEI}mapping'):
                    if mapping.get('type') == 'normal_unicode':
                        hex_val = mapping.text
                        if hex_val:
                            resolved = _decode_unicode_hex(hex_val)
                            break
            # Priority 3: unicode
            if not resolved:
                for mapping in char_elem.iter(f'{TEI}mapping'):
                    if mapping.get('type') == 'unicode':
                        hex_val = mapping.text
                        if hex_val:
                            resolved = _decode_unicode_hex(hex_val)
                            break
            if resolved:
                char_map[char_id] = resolved
    return char_map


def _decode_unicode_hex(hex_str: str) -> str | None:
    hex_str = hex_str.strip()
    if hex_str.startswith(('U+', 'u+')):
        try:
            return chr(int(hex_str[2:], 16))
        except (ValueError, OverflowError):
            return None
    return None


def extract_readable(elem, char_map: dict[str, str], context: str = 'body') -> list[dict]:
    """Extract readable text preserving structure.

    Returns list of dicts: {'type': 'para'|'verse'|'heading'|'juan', 'text': str}
    """
    results = []
    tag = elem.tag

    if tag in SKIP_TAGS:
        return results

    # Handle <app>: only process <lem>
    if tag == f'{TEI}app':
        for child in elem:
            if child.tag == f'{TEI}lem':
                results.extend(extract_readable(child, char_map, context))
        return results

    # Fascicle marker
    if tag == f'{CB}juan':
        juan_n = elem.get('n', '')
        title_text = _get_all_text(elem, char_map)
        results.append({'type': 'juan', 'text': title_text.strip(), 'n': juan_n})
        return results

    # Section heading
    if tag == f'{TEI}head':
        head_text = _get_all_text(elem, char_map)
        if head_text.strip():
            results.append({'type': 'heading', 'text': head_text.strip()})
        return results

    # Verse group
    if tag == f'{TEI}lg':
        verse_lines = []
        for child in elem:
            if child.tag == f'{TEI}l':
                line_text = _get_all_text(child, char_map).strip()
                if line_text:
                    verse_lines.append(line_text)
            elif child.tail:
                pass  # tail handled below
        if verse_lines:
            results.append({'type': 'verse', 'text': '\n'.join(verse_lines)})
        # Handle tail text after the verse group
        return results

    # Single verse line (when not inside <lg>)
    if tag == f'{TEI}l' and context != 'lg':
        line_text = _get_all_text(elem, char_map).strip()
        if line_text:
            results.append({'type': 'verse', 'text': line_text})
        return results

    # Paragraph
    if tag == f'{TEI}p':
        is_dharani = elem.get(f'{CB}type') == 'dharani'
        p_text = _get_all_text(elem, char_map, dharani=is_dharani).strip()
        if p_text:
            results.append({
                'type': 'dharani' if is_dharani else 'para',
                'text': p_text
            })
        return results

    # For container elements, recurse into children
    for child in elem:
        child_context = 'lg' if tag == f'{TEI}lg' else context
        results.extend(extract_readable(child, char_map, child_context))

    return results


# Phonetic annotations to preserve in dhāraṇī passages
_DHARANI_ANNOTATIONS = frozenset(['引', '二合', '三合', '去', '入', '上', '平',
                                   '去聲', '上聲', '平聲', '入聲'])


def _get_all_text(elem, char_map: dict[str, str], dharani: bool = False) -> str:
    """Get all text content from an element, resolving special chars.

    Args:
        dharani: If True, preserve phonetic annotations (引, 二合, etc.)
                 from inline notes as {annotation} markers.
    """
    parts = []

    # In dharani mode, preserve phonetic inline notes
    if elem.tag == f'{TEI}note' and dharani:
        place = elem.get('place', '')
        if place == 'inline':
            note_text = (elem.text or '').strip()
            # Check if this is a phonetic annotation (not a number/counter)
            # Handle combined annotations like "二合、引"
            annotations = [a.strip() for a in note_text.replace('、', ',').split(',')]
            kept = [a for a in annotations if a in _DHARANI_ANNOTATIONS]
            if kept:
                for a in kept:
                    parts.append('{' + a + '}')
                return ''.join(parts)
        # Non-phonetic notes (numbers, editorial) still skipped
        return ''

    if elem.tag in SKIP_TAGS:
        return ''

    # Handle <g> special character reference
    if elem.tag == f'{TEI}g':
        ref = elem.get('ref', '')
        if ref.startswith('#'):
            char_id = ref[1:]
            resolved = char_map.get(char_id, '')
            if resolved:
                parts.append(resolved)
        return ''.join(parts)

    # Handle <app>: only use <lem>
    if elem.tag == f'{TEI}app':
        for child in elem:
            if child.tag == f'{TEI}lem':
                parts.append(_get_all_text(child, char_map, dharani))
                if child.tail:
                    parts.append(child.tail)
        return ''.join(parts)

    # Skip <rdg> elements
    if elem.tag == f'{TEI}rdg':
        return ''

    if elem.text:
        parts.append(elem.text)

    for child in elem:
        parts.append(_get_all_text(child, char_map, dharani))
        if child.tail:
            parts.append(child.tail)

    return ''.join(parts)


def clean_text(text: str, keep_annotations: bool = False) -> str:
    """Clean extracted text: normalize whitespace, keep CJK + punctuation.

    Args:
        keep_annotations: If True, also preserve {annotation} markers
                         used for dhāraṇī phonetic annotations.
    """
    # Remove line breaks and collapse whitespace
    text = re.sub(r'\s+', '', text)
    if keep_annotations:
        # Keep CJK + punctuation + {annotation} markers
        matches = re.findall(
            r'\{[^}]+\}|' + PRESERVE_RE.pattern, text)
        return ''.join(matches)
    # Keep only CJK characters and Chinese punctuation
    matches = PRESERVE_RE.findall(text)
    return ''.join(matches)


def extract_text(xml_files: list[Path], char_map: dict[str, str]) -> list[dict]:
    """Extract structured text from a list of XML files (one text, multiple fascicles)."""
    all_blocks = []
    for xml_path in sorted(xml_files):
        try:
            tree = etree.parse(str(xml_path))
        except etree.XMLSyntaxError:
            print(f"  Warning: XML parse error in {xml_path}", file=sys.stderr)
            continue
        root = tree.getroot()
        body = root.find(f'.//{TEI}body')
        if body is not None:
            blocks = extract_readable(body, char_map)
            all_blocks.extend(blocks)
    return all_blocks


def blocks_to_text(blocks: list[dict]) -> str:
    """Convert structured blocks to readable text for translation."""
    lines = []
    for block in blocks:
        btype = block['type']
        text = clean_text(block['text'], keep_annotations=(btype == 'dharani'))

        if not text:
            continue

        if btype == 'juan':
            n = block.get('n', '')
            lines.append(f'\n{"=" * 40}')
            lines.append(f'Fascicle {n}: {text}')
            lines.append(f'{"=" * 40}\n')
        elif btype == 'heading':
            lines.append(f'\n## {text}\n')
        elif btype == 'verse':
            # Preserve verse line breaks
            verse_lines = block['text'].split('\n')
            for vl in verse_lines:
                cleaned = clean_text(vl)
                if cleaned:
                    lines.append(f'  {cleaned}')
            lines.append('')
        elif btype == 'dharani':
            lines.append(f'[Dhāraṇī] {text}')
            lines.append('')
        else:  # para
            lines.append(text)
            lines.append('')

    return '\n'.join(lines)


def get_metadata(xml_files: list[Path]) -> dict:
    """Extract metadata from the first XML file's teiHeader."""
    if not xml_files:
        return {}
    try:
        tree = etree.parse(str(xml_files[0]))
    except etree.XMLSyntaxError:
        return {}
    root = tree.getroot()
    text_id = root.get(f'{XML}id', '')
    meta = {'text_id': text_id}

    header = root.find(f'{TEI}teiHeader')
    if header is not None:
        for title in header.iter(f'{TEI}title'):
            lang = title.get(f'{XML}lang', '')
            if lang == 'zh-Hant' and title.get('level') == 'm':
                meta['title'] = title.text or ''
                break
        author_elem = header.find(f'.//{TEI}author')
        if author_elem is not None:
            meta['author'] = author_elem.text or ''
        extent_elem = header.find(f'.//{TEI}extent')
        if extent_elem is not None:
            extent_text = extent_elem.text or ''
            m = re.search(r'(\d+)', extent_text)
            meta['extent_juan'] = int(m.group(1)) if m else 1
    return meta


def main():
    xml_base = Path.home() / 'taisho-canon' / 'xml' / 'T'
    output_dir = Path.home() / 'taisho-translation-sample' / 'chinese'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load sample texts config
    config_path = Path.home() / 'taisho-translation-sample' / 'sample_texts.json'
    with open(config_path) as f:
        sample_texts = json.load(f)

    print(f"Extracting {len(sample_texts)} texts from CBETA XML corpus...")

    for text_info in sample_texts:
        t_num = text_info['t_number']
        pattern = text_info['xml_pattern']

        # Find XML files
        parts = pattern.split('/')
        vol_dir = xml_base / parts[0]
        file_pattern = parts[1]
        xml_files = sorted(vol_dir.glob(file_pattern))

        if not xml_files:
            print(f"  WARNING: No XML files found for {t_num} ({pattern})")
            continue

        print(f"\n  Extracting {t_num} ({text_info['title_zh']})...")
        print(f"    Found {len(xml_files)} XML file(s)")

        # Build char map for this text's files
        char_map = build_char_map(xml_files)
        print(f"    Char map: {len(char_map)} entries")

        # Extract structured text
        blocks = extract_text(xml_files, char_map)
        print(f"    Extracted {len(blocks)} text blocks")

        # Get metadata
        meta = get_metadata(xml_files)

        # Convert to readable text
        readable = blocks_to_text(blocks)
        char_count = len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', readable))
        print(f"    CJK characters: {char_count:,}")

        # Save Chinese text
        out_path = output_dir / f'{t_num}.txt'
        header = (
            f"# {text_info['title_zh']} ({text_info['title_en']})\n"
            f"# Taishō {t_num}, {text_info['juan']} fascicle(s)\n"
            f"# Translator: {text_info['translator']}\n"
            f"# Genre: {text_info['genre']}\n"
            f"# CJK characters: {char_count:,}\n\n"
        )
        out_path.write_text(header + readable, encoding='utf-8')
        print(f"    Saved to {out_path}")

        # Save metadata
        meta_path = output_dir / f'{t_num}_meta.json'
        meta.update({
            't_number': t_num,
            'cjk_char_count': char_count,
            'block_count': len(blocks),
            'file_count': len(xml_files),
        })
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    print("\nExtraction complete!")


if __name__ == '__main__':
    main()
