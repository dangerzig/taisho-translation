#!/usr/bin/env python3
"""Generate PDFs from translated Buddhist texts using pandoc + xelatex."""

import json
import subprocess
import sys
from pathlib import Path


PANDOC_HEADER = r"""\usepackage{newunicodechar}
\usepackage{xeCJK}
\setCJKmainfont{Noto Serif CJK SC}
\newunicodechar{→}{{\CJKfontspec{Noto Serif CJK SC}→}}
\newunicodechar{✓}{{\CJKfontspec{Noto Serif CJK SC}✓}}

% Buddhist text styling
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries\centering}{}{0em}{}
\titleformat{\subsection}{\large\bfseries\centering}{}{0em}{}

% Verse indentation
\usepackage{verse}
"""


def generate_pdf(md_path: Path, pdf_path: Path) -> bool:
    """Generate PDF from markdown translation using pandoc + xelatex."""
    header_path = md_path.parent / '_pandoc_header.tex'
    header_path.write_text(PANDOC_HEADER, encoding='utf-8')

    cmd = [
        'pandoc', str(md_path),
        '-o', str(pdf_path),
        '--from', 'markdown-smart',
        '-V', 'geometry:margin=2.5cm',
        '-V', 'fontsize=11pt',
        '--pdf-engine=xelatex',
        '-V', 'mainfont=Times New Roman',
        '-V', 'CJKmainfont=Noto Serif CJK SC',
        '-H', str(header_path),
        '--toc',
        '-V', 'toc-title=Contents',
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"  ERROR: pandoc failed for {md_path.name}")
            print(f"  stderr: {result.stderr[:500]}")
            return False
        print(f"  Generated {pdf_path.name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"  ERROR: timeout generating {md_path.name}")
        return False
    except FileNotFoundError:
        print("  ERROR: pandoc not found. Install with: brew install pandoc")
        return False


def main():
    base_dir = Path.home() / 'taisho-translation-sample'
    trans_dir = base_dir / 'translations'
    pdf_dir = base_dir / 'pdfs'
    pdf_dir.mkdir(parents=True, exist_ok=True)

    # Load sample texts config for filtering
    with open(base_dir / 'sample_texts.json') as f:
        sample_texts = json.load(f)

    # Parse args
    selected_tnums = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith('T'):
            selected_tnums = {arg}
        elif arg.isdigit():
            tier = int(arg)
            selected_tnums = {t['t_number'] for t in sample_texts if t['tier'] == tier}

    # Find translation files
    md_files = sorted(trans_dir.glob('T*_translation.md'))
    if selected_tnums:
        md_files = [f for f in md_files
                    if f.name.split('_')[0] in selected_tnums]

    if not md_files:
        print("No translation files found.")
        return

    print(f"Generating PDFs for {len(md_files)} translation(s)...")

    success = 0
    for md_path in md_files:
        t_num = md_path.name.split('_')[0]
        pdf_path = pdf_dir / f'{t_num}_translation.pdf'
        print(f"\n  {t_num}:", end=' ')
        if generate_pdf(md_path, pdf_path):
            success += 1

    print(f"\n\nGenerated {success}/{len(md_files)} PDFs in {pdf_dir}")


if __name__ == '__main__':
    main()
