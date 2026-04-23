#!/usr/bin/env python3
"""
Generate a BDK English Tripiṭaka-style cover spread for IngramSpark.

Uses extracted BDK images (Dharma wheel, divider) with transparent backgrounds.
Color scheme: dark forest green (#1c322a) with gold text, cream spine text.

Usage:
    python3 generate_bdk_cover.py \
        --pages 164 \
        --title "ACCOUNTS OF THE TRANSMISSION OF THE DHARMA TREASURY" \
        --back-text "Description here..." \
        -o T2058_cover.pdf
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.expanduser("~/nirvana-sutra"))
from generate_cover import calculate_dimensions, compile_cover

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def generate_bdk_cover(pages, paper, title, back_text, output,
                       wheel_path=None, divider_path=None,
                       spine_wheel_path=None):
    """Generate a BDK-style cover PDF."""

    # Default image paths (in same directory as this script)
    if wheel_path is None:
        wheel_path = os.path.join(SCRIPT_DIR, "bdk_wheel_gold.png")
    if divider_path is None:
        divider_path = os.path.join(SCRIPT_DIR, "bdk_divider_gold.png")
    if spine_wheel_path is None:
        spine_wheel_path = os.path.join(SCRIPT_DIR, "bdk_spine_wheel.png")

    # Use absolute paths for LaTeX
    wheel_path = os.path.abspath(wheel_path)
    divider_path = os.path.abspath(divider_path)
    spine_wheel_path = os.path.abspath(spine_wheel_path)

    spine, total_w, total_h, margin, panel_w, panel_h, hinge = \
        calculate_dimensions(pages, paper, "paperback")

    back_center = margin + panel_w / 2
    spine_left = margin + panel_w + hinge
    spine_center = spine_left + spine / 2
    front_center = spine_left + spine + hinge + panel_w / 2
    spine_wheel_size = min(spine * 0.85, 0.35)

    # Split title into lines (expects \n separators)
    title_lines = title.split("\n") if "\n" in title else [title]

    # Vertical positions
    y_bdk = margin + panel_h - 1.3       # "BDK ENGLISH TRIPITAKA"
    y_div = y_bdk - 0.55                 # divider
    y_t_start = y_div - 0.65             # first title line
    line_gap = 0.42                      # gap between title lines

    # Build title nodes
    title_nodes = ""
    for i, line in enumerate(title_lines):
        y = y_t_start - i * line_gap
        title_nodes += (
            f"\\node[anchor=center, text=bdkgold] "
            f"at ({front_center:.4f}, {y:.4f})\n"
            f"    {{\\fontsize{{22}}{{26}}\\selectfont\\bfseries {line}}};\n"
        )

    y_wheel = margin + 2.5

    # Build spine title (all caps, single line)
    spine_title = " ".join(title_lines).upper()

    latex = rf"""
\documentclass[12pt]{{article}}
\usepackage[paperwidth={total_w:.4f}in, paperheight={total_h:.4f}in, margin=0pt]{{geometry}}
\usepackage{{fontspec}}
\usepackage{{xeCJK}}
\usepackage{{tikz}}
\usepackage{{xcolor}}
\usepackage{{graphicx}}

\setmainfont{{Times New Roman}}
\setCJKmainfont{{Noto Serif CJK SC}}

%% BDK colors
%% Front: gold on dark green (#1c322a, measured with Nix Color Sensor)
%% Spine: cream on dark green
\definecolor{{bdkgreen}}{{RGB}}{{28, 50, 42}}
\definecolor{{bdkgold}}{{RGB}}{{215, 195, 145}}
\definecolor{{spinecream}}{{RGB}}{{235, 230, 215}}

\pagestyle{{empty}}
\parindent=0pt

\begin{{document}}%
\null%
\begin{{tikzpicture}}[remember picture, overlay, shift={{(current page.south west)}},
    x=1in, y=1in, every node/.style={{inner sep=0pt, outer sep=0pt}}]

%% Background
\fill[bdkgreen] (0,0) rectangle ({total_w:.4f}, {total_h:.4f});

%% ==================== FRONT COVER ====================

%% "BDK ENGLISH TRIPITAKA" -- large, nearly title-sized
\node[anchor=center, text=bdkgold] at ({front_center:.4f}, {y_bdk:.4f})
    {{\fontsize{{17}}{{20}}\selectfont\bfseries BDK ENGLISH TRIPI\d{{T}}AKA}};

%% Decorative divider (extracted from BDK cover)
\node[anchor=center] at ({front_center:.4f}, {y_div:.4f})
    {{\includegraphics[width=2.2in]{{{divider_path}}}}};

%% Title lines
{title_nodes}

%% Dharma wheel (extracted from BDK cover, gold-tinted)
\node[anchor=center] at ({front_center:.4f}, {y_wheel:.4f})
    {{\includegraphics[width=2.6in]{{{wheel_path}}}}};

%% ==================== SPINE ====================

%% Dharma wheel at top (white version)
\node[anchor=center] at ({spine_center:.4f}, {total_h - margin - 0.55:.4f})
    {{\includegraphics[width={spine_wheel_size:.3f}in]{{{spine_wheel_path}}}}};

%% Title -- large all-caps cream, spanning most of spine
\node[anchor=center, text=spinecream, rotate=-90, text width=6.5in, align=center]
    at ({spine_center:.4f}, {total_h / 2 - 0.1:.4f})
    {{\fontsize{{14}}{{17}}\selectfont\bfseries {spine_title}}};

%% "Numata Center" horizontal at bottom, two separate lines
\node[anchor=center, text=spinecream]
    at ({spine_center:.4f}, {margin + 0.62:.4f})
    {{\fontsize{{11}}{{13}}\selectfont Numata}};
\node[anchor=center, text=spinecream]
    at ({spine_center:.4f}, {margin + 0.42:.4f})
    {{\fontsize{{11}}{{13}}\selectfont Center}};

%% ==================== BACK COVER ====================

\node[anchor=north, text width=4.2in, align=justify, text=bdkgold]
    at ({back_center:.4f}, {margin + panel_h - 1.5:.4f})
    {{\fontsize{{10}}{{14}}\selectfont {back_text}}};

\node[anchor=center, text=bdkgold] at ({back_center:.4f}, {margin + 1.0:.4f})
    {{\fontsize{{9}}{{11}}\selectfont BDK English Tripi\d{{t}}aka Series}};

\end{{tikzpicture}}%
\end{{document}}
"""

    compile_cover(latex, output)
    print(f"Spine width: {spine:.3f}in")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate BDK-style cover")
    parser.add_argument("--pages", type=int, required=True)
    parser.add_argument("--paper", default="white", choices=["white", "cream"])
    parser.add_argument("--title", required=True,
                        help="Title lines separated by \\n")
    parser.add_argument("--back-text", required=True,
                        help="LaTeX text for back cover")
    parser.add_argument("--wheel", default=None,
                        help="Path to gold wheel PNG (default: bdk_wheel_gold.png)")
    parser.add_argument("--divider", default=None,
                        help="Path to gold divider PNG (default: bdk_divider_gold.png)")
    parser.add_argument("--spine-wheel", default=None,
                        help="Path to white spine wheel PNG")
    parser.add_argument("-o", "--output", default="cover.pdf")
    args = parser.parse_args()

    generate_bdk_cover(
        pages=args.pages,
        paper=args.paper,
        title=args.title,
        back_text=args.back_text,
        output=args.output,
        wheel_path=args.wheel,
        divider_path=args.divider,
        spine_wheel_path=args.spine_wheel,
    )
