#!/usr/bin/env python3
"""
Generate a BDK English Tripiṭaka-format PDF from a Taisho translation.

Matches the exact typesetting conventions of the BDK English Tripiṭaka series:
page size, fonts, front matter sequence, running headers, margin refs, etc.

Usage:
    python3 generate_bdk_book.py \\
      ~/taisho-translation/translations/T2058_translation.md \\
      --glossary ~/taisho-translation/T2058/glossary.md \\
      --index-terms ~/taisho-translation/T2058/index_terms.txt \\
      --introduction ~/taisho-translation/T2058/introduction.md \\
      --front-matter ~/taisho-translation/T2058/bdk_front_matter.md \\
      --xml-dir ~/taisho-canon/xml/T/T50 \\
      --title "ACCOUNTS OF THE TRANSMISSION OF THE DHARMA TREASURY" \\
      --taisho-vol 50 --taisho-num 2058 \\
      --translator "Dan Zigmond" \\
      -o ~/taisho-translation/T2058/T2058_book.pdf
"""

import argparse
import os
import re
import shutil
import sys
import unicodedata

# Import shared utilities from the existing typesetting infrastructure
sys.path.insert(0, os.path.expanduser("~/nirvana-sutra"))
from generate_bilingual_book import (
    escape_latex,
    md_inline_to_latex,
    smart_quotes,
)
from generate_taisho_book import (
    build_index_terms,
    compile_xelatex,
    extract_paragraphs,
    extract_taisho_refs,
    insert_auto_index,
    latex_quotes,
    map_refs_to_paragraphs,
    split_into_fascicles,
)


# ---------------------------------------------------------------------------
# BDK-format glossary parser (paragraph-style, not table-style)
# ---------------------------------------------------------------------------

def parse_bdk_glossary(path):
    """Parse a BDK-style glossary.md where each entry is a paragraph:

        **Term** (Chinese; Skt. *term*): Definition text.

    Returns a list of dicts with keys: term, parenthetical, definition, raw.
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    entries = []
    # Split into paragraphs (blank-line separated)
    paragraphs = re.split(r"\n\s*\n", text)

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Skip the heading line
        if para.startswith("#"):
            continue

        # Match: **Term** (parenthetical): definition
        m = re.match(
            r"\*\*(.+?)\*\*\s*"        # bold term
            r"(?:\(([^)]*)\))?\s*"      # optional parenthetical
            r"(?::\s*)?"                # optional colon
            r"(.*)",                    # definition (rest)
            para, re.DOTALL
        )
        if m:
            term = m.group(1).strip()
            paren = m.group(2).strip() if m.group(2) else ""
            defn = m.group(3).strip()
            entries.append({
                "term": term,
                "parenthetical": paren,
                "definition": defn,
                "raw": para,
            })

    return entries


def format_bdk_glossary_latex(entries):
    """Render BDK-style glossary entries as LaTeX with hanging indent."""
    lines = []
    lines.append(r"\clearpage")
    lines.append(r"\phantomsection")
    lines.append(r"\addcontentsline{toc}{chapter}{Glossary}")
    lines.append(r"\fancyhead[LE]{\small\textit{Glossary}}")
    lines.append(r"\fancyhead[RO]{\small\textit{Glossary}}")
    lines.append(r"\vspace*{1\baselineskip}")
    lines.append(r"\begin{center}")
    lines.append(r"{\Large\bfseries Glossary}")
    lines.append(r"\end{center}")
    lines.append(r"\vspace{1\baselineskip}")
    lines.append("")

    # Hanging-indent list
    lines.append(r"\begin{list}{}{%")
    lines.append(r"  \setlength{\leftmargin}{1.5em}%")
    lines.append(r"  \setlength{\itemindent}{-1.5em}%")
    lines.append(r"  \setlength{\itemsep}{0.4\baselineskip}%")
    lines.append(r"  \setlength{\parsep}{0pt}%")
    lines.append(r"  \setlength{\topsep}{0pt}%")
    lines.append(r"}")

    for entry in entries:
        term = escape_latex(entry["term"])
        paren = entry["parenthetical"]
        defn = entry["definition"]

        # Process parenthetical: contains Chinese and Skt. *italics*
        if paren:
            # Escape LaTeX but preserve *italic* markers first
            paren_latex = escape_latex(paren)
            paren_latex = md_inline_to_latex(paren_latex)
            item_text = r"\textbf{" + term + r"} (" + paren_latex + ")"
        else:
            item_text = r"\textbf{" + term + "}"

        if defn:
            defn_latex = escape_latex(defn)
            defn_latex = md_inline_to_latex(defn_latex)
            defn_latex = smart_quotes(defn_latex)
            defn_latex = latex_quotes(defn_latex)
            item_text += ": " + defn_latex

        lines.append(r"\item " + item_text)

    lines.append(r"\end{list}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Front matter text extraction
# ---------------------------------------------------------------------------

def extract_front_matter_sections(path):
    """Extract 'A Message' and 'Editorial Foreword' from bdk_front_matter.md.

    Returns dict with keys 'message' and 'foreword', each a string of
    the body text (without the heading).
    """
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    sections = {}
    # Split by ## headings
    parts = re.split(r"^## ", text, flags=re.MULTILINE)
    for part in parts:
        if part.startswith("A Message"):
            # Everything after the heading line
            body = part.split("\n", 1)[1].strip() if "\n" in part else ""
            sections["message"] = body
        elif part.startswith("Editorial Foreword"):
            body = part.split("\n", 1)[1].strip() if "\n" in part else ""
            sections["foreword"] = body

    return sections


def front_matter_to_latex(text):
    """Convert front-matter markdown text to LaTeX paragraphs."""
    lines = []
    paragraphs = text.split("\n\n")
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Escape and convert
        p = escape_latex(para)
        p = md_inline_to_latex(p)
        p = smart_quotes(p)
        p = latex_quotes(p)
        # Preserve line breaks within a paragraph (for signature blocks)
        # If lines are short (< 60 chars each), treat as line-break block
        sublines = para.split("\n")
        if len(sublines) > 1 and all(len(s.strip()) < 70 for s in sublines):
            processed = []
            for sl in sublines:
                sl = sl.strip()
                sl = escape_latex(sl)
                sl = md_inline_to_latex(sl)
                sl = smart_quotes(sl)
                sl = latex_quotes(sl)
                processed.append(sl)
            lines.append(r"\noindent " + r" \\" + "\n".join(processed))
        else:
            lines.append(p)
        lines.append("")
    return "\n".join(lines)


def introduction_to_latex(path):
    """Convert introduction.md to LaTeX body text."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = []
    # Remove the top-level heading if present
    text = re.sub(r"^#\s+.*\n", "", text)

    paragraphs_raw = re.split(r"\n\s*\n", text)
    after_heading = False

    for para in paragraphs_raw:
        para = para.strip()
        if not para:
            continue

        # Check for heading
        hm = re.match(r"^(#{2,4})\s+(.+)$", para)
        if hm:
            level = len(hm.group(1))
            title = escape_latex(hm.group(2))
            title = md_inline_to_latex(title)
            title = smart_quotes(title)
            title = latex_quotes(title)
            if level == 2:
                lines.append(r"\vspace{0.8\baselineskip}")
                lines.append(r"\begin{center}")
                lines.append(r"{\large\bfseries " + title + "}")
                lines.append(r"\end{center}")
                lines.append(r"\addcontentsline{toc}{section}{" + title + "}")
            elif level == 3:
                lines.append(r"\vspace{0.6\baselineskip}")
                lines.append(r"\noindent{\bfseries " + title + "}")
            else:
                lines.append(r"\vspace{0.4\baselineskip}")
                lines.append(r"\noindent{\bfseries\itshape " + title + "}")
            lines.append(r"\nopagebreak")
            lines.append("")
            after_heading = True
            continue

        # Check for blockquote (verse)
        if para.startswith("> "):
            bq_lines = []
            for bl in para.split("\n"):
                bl = bl.strip()
                if bl.startswith("> "):
                    bl = bl[2:]
                elif bl == ">":
                    bl = ""
                bl = re.sub(r'\s*\\$', '', bl)
                bl = escape_latex(bl)
                bl = md_inline_to_latex(bl)
                bl = smart_quotes(bl)
                bl = latex_quotes(bl)
                if bl.startswith("["):
                    bl = "{}" + bl
                bq_lines.append(bl)
            lines.append(r"\begin{verse-quote}")
            lines.append(" \\\\\n".join(bq_lines))
            lines.append(r"\end{verse-quote}")
            lines.append("")
            after_heading = False
            continue

        # Regular paragraph
        p = escape_latex(para)
        p = md_inline_to_latex(p)
        p = smart_quotes(p)
        p = latex_quotes(p)
        # Join wrapped lines into single paragraph
        p = re.sub(r"\s*\n\s*", " ", p)

        if after_heading:
            lines.append(r"\noindent " + p)
            after_heading = False
        else:
            lines.append(p)
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# BDK fascicle body builder (uses imported extract_paragraphs)
# ---------------------------------------------------------------------------

def build_bdk_fascicle_body(fascicle_label, paragraphs, title,
                            index_terms=None, index_chinese=None,
                            taisho_refs=None):
    """Build LaTeX for one fascicle in BDK format."""
    lines = []

    if fascicle_label:
        safe_label = escape_latex(fascicle_label)
        lines.append(r"\cleardoublepage")
        lines.append(r"\thispagestyle{plain}")
        lines.append(r"\phantomsection")
        # Fascicle entries in TOC as group headers without page numbers
        lines.append(r"\addtocontents{toc}{\protect\vspace{4pt}\protect\noindent " + safe_label + r"\protect\par}")
        lines.append(r"\fancyhead[RO]{\small\textit{" + safe_label + r"}}")
        lines.append(r"\vspace*{4\baselineskip}")
        lines.append(r"\begin{center}")
        lines.append(r"{\Large\bfseries " + safe_label + r"}")
        lines.append(r"\end{center}")
        lines.append(r"\vspace{2\baselineskip}")
        lines.append("")

    after_heading = bool(fascicle_label)  # noindent first para after fascicle heading
    # Map Taisho refs to body paragraphs
    body_content = [ep for ep in paragraphs if ep[0] in ("paragraph", "verse")]
    taisho_map = map_refs_to_paragraphs(taisho_refs or [], len(body_content))
    body_para_idx = 0

    for i, ep in enumerate(paragraphs):
        etype = ep[0]
        content = ep[1] if len(ep) > 1 else ""

        if etype == "heading":
            level = ep[3] if len(ep) >= 4 else 3

            if level <= 3:
                heading_text = content
                toc_text = heading_text
                lines.append(r"\vspace{0.8\baselineskip}")
                lines.append(r"\begin{center}")
                lines.append(r"{\large\bfseries " + heading_text + "}")
                lines.append(r"\end{center}")
                toc_level = "section" if level <= 3 else "subsection"
                lines.append(r"\addcontentsline{toc}{" + toc_level
                             + "}{" + toc_text + "}")
                # Update running header to current section
                lines.append(r"\fancyhead[RO]{\small\textit{"
                             + heading_text + r"}}")
                lines.append(r"\nopagebreak")
            else:
                lines.append(r"\vspace{0.6\baselineskip}")
                lines.append(r"\noindent{\bfseries\itshape " + content + "}")
                if level == 4:
                    lines.append(r"\addcontentsline{toc}{subsection}{"
                                 + content + "}")
                lines.append(r"\nopagebreak")

            after_heading = True
            lines.append("")

        elif etype == "verse":
            margin = ""
            if body_para_idx in taisho_map:
                ref = taisho_map[body_para_idx]
                margin = (r"\marginnote{\tiny\textsf{\color{black!55}["
                          + ref + r"]}}")
            body_para_idx += 1
            lines.append(margin + r"\begin{verse-quote}")
            lines.append(content)
            lines.append(r"\end{verse-quote}")
            after_heading = False
            lines.append("")

        elif etype == "paragraph":
            if index_terms:
                content = insert_auto_index(content, index_terms, index_chinese)
            margin = ""
            if body_para_idx in taisho_map:
                ref = taisho_map[body_para_idx]
                margin = (r"\marginnote{\tiny\textsf{\color{black!55}["
                          + ref + r"]}}")
            body_para_idx += 1
            if after_heading:
                lines.append(r"\noindent " + margin + content)
                after_heading = False
            else:
                lines.append(margin + content)
            lines.append("")

        elif etype == "rule":
            lines.append(r"\vspace{0.5\baselineskip}")
            lines.append(r"\noindent\rule{2cm}{0.3pt}")
            lines.append(r"\vspace{0.3\baselineskip}")
            after_heading = True
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Full BDK document assembly
# ---------------------------------------------------------------------------

def build_bdk_document(title, taisho_vol, taisho_num, translator, year,
                       fascicles_data, full_text,
                       front_matter_path=None, introduction_path=None,
                       glossary_path=None, index_terms_path=None,
                       xml_dir=None, chinese_authors=None,
                       running_title=None):
    """Assemble the complete BDK-format LaTeX document."""

    escaped_title = escape_latex(title)
    escaped_translator = escape_latex(translator)
    escaped_running = escape_latex(running_title) if running_title else escaped_title

    # -----------------------------------------------------------------------
    # Preamble
    # -----------------------------------------------------------------------
    preamble = r"""\documentclass[11pt,twoside,openright]{book}

%% Page geometry: 6.14" x 9.21" (IngramSpark Royal, close to BDK format)
\usepackage[
  paperwidth=6.14in,
  paperheight=9.21in,
  inner=0.95in,
  outer=0.75in,
  top=0.7in,
  bottom=0.8in,
  marginparwidth=0.4in,
  marginparsep=0.12in
]{geometry}

%% Font setup
\usepackage{fontspec}
\usepackage{xeCJK}
\usepackage{microtype}

\setmainfont{Times New Roman}
%% Fake small caps command (Times New Roman may lack native smcp)
\newcommand{\fakesc}[1]{{\footnotesize\MakeUppercase{#1}}}
\setCJKmainfont[AutoFakeBold=2]{Noto Serif CJK SC}

%% Packages
\usepackage{fancyhdr}
\usepackage{setspace}
\usepackage{xcolor}
\usepackage{changepage}
\usepackage{marginnote}
\usepackage{tocloft}
\usepackage{multicol}
\usepackage{imakeidx}
\makeindex[columns=2]

%% MUST be loaded last
\usepackage[hidelinks,linktoc=all]{hyperref}

%% Line spacing: BDK uses ~1.12
\setstretch{1.12}

%% Paragraph formatting: indent, no extra spacing
\setlength{\parskip}{0pt}
\setlength{\parindent}{1.5em}

%% Widow/orphan control
\widowpenalty=10000
\clubpenalty=10000

%% Running headers
\pagestyle{fancy}
\fancyhf{}
\fancyhead[LE]{\small\textit{""" + escaped_running + r"""}}
\fancyhead[RO]{\small\textit{}}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0pt}

%% Suppress fancy headers on chapter-opening pages (page number centered)
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\small\thepage}%
  \renewcommand{\headrulewidth}{0pt}%
}

%% Margin notes for Taisho references (outer margin -- default for twoside)

%% Verse / quoted-speech environment
\newenvironment{verse-quote}{%
  \vspace{0.4\baselineskip}%
  \begin{adjustwidth}{2.5em}{1em}%
  \setlength{\parskip}{0pt}\setlength{\parindent}{0pt}%
}{%
  \end{adjustwidth}%
  \vspace{0.4\baselineskip}%
}

%% TOC formatting -- match BDK style (no dot leaders, modest title)
\renewcommand{\cfttoctitlefont}{\hfill\Large\bfseries}
\renewcommand{\cftaftertoctitle}{\hfill}
\setlength{\cftbeforetoctitleskip}{2\baselineskip}
\setlength{\cftaftertoctitleskip}{1.5\baselineskip}
%% Chapter-level TOC entries (front/back matter)
\setlength{\cftbeforechapskip}{4pt}
\renewcommand{\cftchapfont}{\normalsize}
\renewcommand{\cftchappagefont}{\normalsize}
\renewcommand{\cftchapleader}{\hfill}
%% Section entries: show page numbers
\setlength{\cftbeforesecskip}{1pt}
\renewcommand{\cftsecfont}{\normalsize}
\renewcommand{\cftsecpagefont}{\normalsize}
\renewcommand{\cftsecleader}{\hfill}
%% Subsection entries
\setlength{\cftbeforesubsecskip}{1pt}
\renewcommand{\cftsubsecfont}{\normalsize}
\renewcommand{\cftsubsecpagefont}{\normalsize}
\renewcommand{\cftsubsecleader}{\hfill}

%% Suppress chapter numbering
\renewcommand{\chaptermark}[1]{}

%% Make blank pages from \cleardoublepage truly blank (no headers/footers)
\makeatletter
\def\cleardoublepage{\clearpage\if@twoside \ifodd\c@page\else
\thispagestyle{empty}\hbox{}\newpage\if@twocolumn\hbox{}\newpage\fi\fi\fi}
\makeatother

\begin{document}

%% ==================== FRONT MATTER ====================
\frontmatter
\pagestyle{fancy}
\fancyhf{}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0pt}
"""

    parts = [preamble]

    # -----------------------------------------------------------------------
    # 1. Half-title page
    # -----------------------------------------------------------------------
    parts.append(r"""
%% ==================== HALF TITLE ====================
\thispagestyle{empty}
\begin{center}
\vspace*{2.5in}
{\large\bfseries """ + escaped_title + r"""}
\end{center}
\vfill
\newpage
\thispagestyle{empty}
\mbox{}
\newpage
""")

    # -----------------------------------------------------------------------
    # 2. Title page
    # -----------------------------------------------------------------------
    parts.append(r"""
%% ==================== TITLE PAGE ====================
\thispagestyle{empty}
\begin{center}
\vspace*{0.5in}
{\small\bfseries BDK English Tripi\d{t}aka Series}

\vspace{2in}

{\LARGE\bfseries """ + escaped_title + r"""}\\[0.4cm]
{\normalsize (Taish\=o Volume """ + str(taisho_vol) + r""", Number """ + str(taisho_num) + r""")}

\vspace{1.5in}

{\normalsize AI-Assisted Translation from the Chinese}\\[0.15cm]
{\normalsize by}\\[0.15cm]
{\normalsize """ + escaped_translator + r"""}

\vfill

{\normalsize\bfseries Numata Center}\\
{\normalsize\bfseries for Buddhist Translation and Research}\\[0.3cm]
{\normalsize\bfseries """ + str(year) + r"""}
\end{center}
\newpage
""")

    # -----------------------------------------------------------------------
    # 3. Copyright page (verso of title)
    # -----------------------------------------------------------------------
    parts.append(r"""
%% ==================== COPYRIGHT PAGE ====================
\thispagestyle{empty}
\vspace*{\fill}
\begin{center}
\small
\textcopyright{} """ + str(year) + r""" by Bukky\=o Dend\=o Ky\=okai and\\
Numata Center for Buddhist Translation and Research

\vspace{1\baselineskip}

All rights reserved. No part of this book may be reproduced, stored\\
in a retrieval system, or transcribed in any form or by any means\\
---electronic, mechanical, photocopying, recording, or otherwise---\\
without the prior written permission of the publisher.

\vspace{1\baselineskip}

First Printing, """ + str(year) + r"""

\vspace{1\baselineskip}

Published by\\
Numata Center for Buddhist Translation and Research\\
2620 Warring Street\\
Berkeley, California 94704

\vspace{1\baselineskip}

Printed in the United States of America
\end{center}
\newpage
""")

    # -----------------------------------------------------------------------
    # 4-5. "A Message" and "Editorial Foreword" from front matter file
    # -----------------------------------------------------------------------
    if front_matter_path and os.path.exists(front_matter_path):
        fm_sections = extract_front_matter_sections(front_matter_path)

        if "message" in fm_sections:
            parts.append(r"""
%% ==================== A MESSAGE ====================
\cleardoublepage
\thispagestyle{plain}
\fancyhead[LE]{\small\textit{A Message on the Publication of the English Tripi\d{t}aka}}
\fancyhead[RO]{\small\textit{A Message on the Publication of the English Tripi\d{t}aka}}
\addcontentsline{toc}{chapter}{A Message on the Publication of the English Tripi\d{t}aka}
\begin{spacing}{1.05}
\raggedright\setlength{\parindent}{1.5em}
\vspace*{0.5\baselineskip}
\begin{center}
{\Large\bfseries A Message on the Publication of the\\English Tripi\d{t}aka}
\end{center}
\vspace{0.5\baselineskip}

\noindent The Buddhist canon is said to contain eighty-four thousand different teachings. I believe that this is because the Buddha's basic approach was to prescribe a different treatment for every spiritual ailment, much as a doctor prescribes a different medicine for every medical ailment. Thus his teachings were always appropriate for the particular suffering individual and for the time at which the teaching was given, and over the ages not one of his prescriptions has failed to relieve the suffering to which it was addressed.

Ever since the Buddha's Great Demise over twenty-five hundred years ago, his message of wisdom and compassion has spread throughout the world. Yet no one has ever attempted to translate the entire Buddhist canon into English throughout the history of Japan. It is my greatest wish to see this done and to make the translations available to the many English-speaking people who have never had the opportunity to learn about the Buddha's teachings.

Of course, it would be impossible to translate all of the Buddha's eighty-four thousand teachings in a few years. I have, therefore, had one hundred thirty-nine of the scriptural texts in the prodigious Taish\=o edition of the Chinese Buddhist canon selected for inclusion in the First Series of this translation project.

It is in the nature of this undertaking that the results are bound to be criticized. Nonetheless, I am convinced that unless someone takes it upon himself or herself to initiate this project, it will never be done. At the same time, I hope that an improved, revised edition will appear in the future.

It is most gratifying that, thanks to the efforts of more than a hundred Buddhist scholars from the East and the West, this monumental project has finally gotten off the ground. May the rays of the Wisdom of the Compassionate One reach each and every person in the world.

\vspace{0.5\baselineskip}

\noindent\begin{minipage}[t]{0.35\textwidth}
\raggedright
August 7, 1991
\end{minipage}%
\hfill
\begin{minipage}[t]{0.5\textwidth}
\raggedleft
\fakesc{Numata} Yehan\\
Founder of the English\\
Tripi\d{t}aka Project
\end{minipage}
\end{spacing}

""")
            # We already hardcoded the message text above, skip front_matter_to_latex
            parts.append(r"\newpage")

        if "foreword" in fm_sections:
            parts.append(r"""
%% ==================== EDITORIAL FOREWORD ====================
\cleardoublepage
\thispagestyle{plain}
\fancyhead[LE]{\small\textit{Editorial Foreword}}
\fancyhead[RO]{\small\textit{Editorial Foreword}}
\addcontentsline{toc}{chapter}{Editorial Foreword}
\raggedright\setlength{\parindent}{1.5em}
\vspace*{2\baselineskip}
\begin{center}
{\Large\bfseries Editorial Foreword}
\end{center}
\vspace{1\baselineskip}

\noindent In January 1982, Dr.\ \fakesc{Numata} Yehan, the founder of the Bukky\=o Dend\=o Ky\=okai
(Society for the Promotion of Buddhism), decided to begin the monumental task
of translating the complete Taish\=o edition of the Chinese Tripi\d{t}aka (Buddhist
canon) into the English language. Under his leadership, a special preparatory
committee was organized in April 1982. By July of the same year, the Translation Committee of the English Tripi\d{t}aka was officially convened.

\hspace{1.5em}The initial Committee consisted of the following members: (late) \fakesc{Hanayama}
Sh\=oy\=u (Chairperson), (late) \fakesc{Band\=o} Sh\=ojun, \fakesc{Ishigami} Zenn\=o, (late) \fakesc{Kamata}
Shigeo, \fakesc{Kanaoka} Sh\=uy\=u, \fakesc{Mayeda} Sengaku, \fakesc{Nara} Yasuaki, (late) \fakesc{Sayeki}
Shink\=o, (late) \fakesc{Shioiri} Ry\=otatsu, \fakesc{Tamaru} Noriyoshi, (late) \fakesc{Tamura} Kwansei,
\fakesc{Ury\=uzu} Ry\=ushin, and \fakesc{Yuyama} Akira. Assistant members of the Committee
were as follows: \fakesc{Kanazawa} Atsushi, \fakesc{Watanabe} Sh\=ogo, Rolf Giebel of New
Zealand, and Rudy Smet of Belgium.

\hspace{1.5em}After holding planning meetings on a monthly basis, the Committee selected
one hundred thirty-nine texts for the First Series of translations, an estimated
one hundred printed volumes in all. The texts selected are not necessarily limited to those originally written in India but also include works written or composed in China and Japan. While the publication of the First Series proceeds,
the texts for the Second Series will be selected from among the remaining works;
this process will continue until all the texts, in Japanese as well as in Chinese,
have been published.

\hspace{1.5em}Frankly speaking, it will take perhaps one hundred years or more to accomplish the English translation of the complete Chinese and Japanese texts, for
they consist of thousands of works. Nevertheless, as Dr.\ \fakesc{Numata} wished, it is
the sincere hope of the Committee that this project will continue unto completion, even after all its present members have passed away.

\hspace{1.5em}It must be mentioned here that the final object of this project is not academic fulfillment but the transmission of the teaching of the Buddha to the whole
world in order to create harmony and peace among humankind. To that end, the
translators have been asked to minimize the use of explanatory notes of the kind
that are indispensable in academic texts, so that the attention of general readers
will not be unduly distracted from the primary text. Also, a glossary of
selected terms is appended to aid in understanding the text.

\vspace{1\baselineskip}

\begin{flushright}
\fakesc{Mayeda} Sengaku\\
Chairperson\\
Editorial Committee of\\
the BDK English Tripi\d{t}aka
\end{flushright}

""")
            parts.append(r"\newpage")

    # -----------------------------------------------------------------------
    # 6. Table of Contents (before Translator's Introduction, per BDK order)
    # -----------------------------------------------------------------------
    parts.append(r"""
%% ==================== TABLE OF CONTENTS ====================
\cleardoublepage
\fancyhead[LE]{\small\textit{Contents}}
\fancyhead[RO]{\small\textit{Contents}}
\tableofcontents
\clearpage
""")

    # -----------------------------------------------------------------------
    # 7. Translator's Introduction (after TOC, per BDK order)
    # -----------------------------------------------------------------------
    if introduction_path and os.path.exists(introduction_path):
        parts.append(r"""
%% ==================== TRANSLATOR'S INTRODUCTION ====================
\cleardoublepage
\thispagestyle{plain}
\fancyhead[LE]{\small\textit{Translator's Introduction}}
\fancyhead[RO]{\small\textit{Translator's Introduction}}
\addcontentsline{toc}{chapter}{Translator's Introduction}
\vspace*{2\baselineskip}
\begin{center}
{\Large\bfseries Translator's Introduction}
\end{center}
\vspace{1\baselineskip}

""")
        parts.append(introduction_to_latex(introduction_path))
        parts.append(r"\newpage")

    # -----------------------------------------------------------------------
    # Main matter
    # -----------------------------------------------------------------------
    parts.append(r"""
%% ==================== TEXT TITLE PAGE ====================
\cleardoublepage
\thispagestyle{empty}
\vspace*{2in}
\begin{center}
{\normalsize """ + escaped_title + r"""}

\vspace{0.8in}

""" + (chinese_authors if chinese_authors else r"{\normalsize Translated from the Chinese}") + r"""
\end{center}
\vfill
\newpage
\thispagestyle{empty}
\mbox{}
\newpage

%% ==================== MAIN MATTER ====================
\mainmatter
\fancyhead[LE]{\small\textit{""" + escaped_running + r"""}}
""")

    # Build index terms
    index_terms, index_chinese = build_index_terms(
        full_text,
        glossary_path=glossary_path,
        index_terms_path=index_terms_path,
    )
    print(f"  Index terms: {len(index_terms)}")
    print(f"  Index terms with Chinese: {len(index_chinese)}")

    # Extract Taisho refs from CBETA XML
    taisho_refs_all = None
    if xml_dir:
        taisho_refs_all = extract_taisho_refs(
            xml_dir, str(taisho_num), len(fascicles_data)
        )
        total_refs = sum(len(r) for r in taisho_refs_all)
        print(f"  Taisho refs: {total_refs} across "
              f"{len(fascicles_data)} fascicle(s)")

    # Render each fascicle
    for fi, (fascicle_label, fascicle_text) in enumerate(fascicles_data):
        print(f"  Processing {fascicle_label or 'body'}...")
        paragraphs = extract_paragraphs(fascicle_text)
        print(f"    Paragraphs: {len(paragraphs)}")
        t_refs = taisho_refs_all[fi] if taisho_refs_all else None
        fascicle_latex = build_bdk_fascicle_body(
            fascicle_label, paragraphs, title,
            index_terms, index_chinese, t_refs,
        )
        parts.append(fascicle_latex)
        parts.append("")

    # -----------------------------------------------------------------------
    # Back matter
    # -----------------------------------------------------------------------
    parts.append(r"""
%% ==================== BACK MATTER ====================
\backmatter
""")

    # Glossary
    if glossary_path and os.path.exists(glossary_path):
        print("  Processing glossary...")
        entries = parse_bdk_glossary(glossary_path)
        print(f"    Glossary entries: {len(entries)}")
        glossary_latex = format_bdk_glossary_latex(entries)
        parts.append(glossary_latex)

    # Index
    parts.append(r"""
\clearpage
\phantomsection
\addcontentsline{toc}{chapter}{Index}
\fancyhead[LE]{\small\textit{Index}}
\fancyhead[RO]{\small\textit{Index}}
\printindex

\end{document}
""")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate a BDK English Tripiṭaka-format PDF."
    )
    parser.add_argument(
        "input", type=str,
        help="Path to the translation markdown file.",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Output PDF path.",
    )
    parser.add_argument(
        "--title", type=str, default=None,
        help="Book title (overrides title from markdown header).",
    )
    parser.add_argument(
        "--taisho-vol", type=int, default=None,
        help="Taishō volume number.",
    )
    parser.add_argument(
        "--taisho-num", type=int, default=None,
        help="Taishō text number.",
    )
    parser.add_argument(
        "--translator", type=str, default="Dan Zigmond",
        help="Translator name.",
    )
    parser.add_argument(
        "--year", type=int, default=2026,
        help="Publication year.",
    )
    parser.add_argument(
        "--chinese-authors", type=str, default=None,
        help="LaTeX text for Chinese authors on text title page.",
    )
    parser.add_argument(
        "--running-title", type=str, default=None,
        help="Mixed-case title for running headers (defaults to --title).",
    )
    parser.add_argument(
        "--glossary", "-g", type=str, default=None,
        help="Path to glossary.md.",
    )
    parser.add_argument(
        "--index-terms", type=str, default=None,
        help="Path to index_terms.txt (TERM | CHINESE per line).",
    )
    parser.add_argument(
        "--introduction", type=str, default=None,
        help="Path to introduction.md.",
    )
    parser.add_argument(
        "--front-matter", type=str, default=None,
        help="Path to bdk_front_matter.md.",
    )
    parser.add_argument(
        "--xml-dir", type=str, default=None,
        help="Directory containing CBETA XML for Taishō margin refs.",
    )
    parser.add_argument(
        "--tex-only", action="store_true",
        help="Write .tex file without compiling to PDF.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found.", file=sys.stderr)
        sys.exit(1)

    if not args.tex_only and shutil.which("xelatex") is None:
        print("Error: xelatex not found.", file=sys.stderr)
        sys.exit(1)

    # Read translation
    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract title from markdown if not given on command line
    title = args.title
    if not title:
        m = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
        if m:
            title = m.group(1)
        else:
            title = "Untitled"

    # Determine Taishō number
    taisho_num = args.taisho_num
    if not taisho_num:
        m = re.search(r"No\.?\s*(\d+)", text)
        taisho_num = int(m.group(1)) if m else 0

    taisho_vol = args.taisho_vol or 0

    print(f"Title: {title}")
    print(f"Taishō Vol. {taisho_vol}, No. {taisho_num}")
    print(f"Translator: {args.translator}")

    # Split into fascicles
    fascicles = split_into_fascicles(text)
    print(f"Fascicles: {len(fascicles)}")

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(os.path.basename(args.input))[0]
        output_path = os.path.join(
            os.path.dirname(args.input) or ".", f"{base}_bdk.pdf"
        )

    # Build LaTeX
    latex_source = build_bdk_document(
        title=title,
        taisho_vol=taisho_vol,
        taisho_num=taisho_num,
        translator=args.translator,
        year=args.year,
        fascicles_data=fascicles,
        full_text=text,
        front_matter_path=args.front_matter,
        introduction_path=args.introduction,
        glossary_path=args.glossary,
        index_terms_path=args.index_terms,
        xml_dir=args.xml_dir,
        chinese_authors=args.chinese_authors,
        running_title=args.running_title,
    )
    print(f"LaTeX: {len(latex_source):,} characters")

    if args.tex_only:
        tex_path = output_path.replace(".pdf", ".tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_source)
        print(f"Written to: {tex_path}")
    else:
        print("Compiling to PDF...")
        success = compile_xelatex(latex_source, output_path, passes=3,
                                  timeout=300)
        if success:
            print(f"Output: {output_path}")
        else:
            print("FAILED to compile.", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
