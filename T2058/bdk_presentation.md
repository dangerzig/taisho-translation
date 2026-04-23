---
title: "Toward a Complete English Tripitaka"
subtitle: "A Pilot Proposal for AI-Assisted Translation of the Taisho Canon"
author: "Dan Zigmond"
date: "June 4, 2026"
theme: "metropolis"
aspectratio: 169
fontsize: 11pt
header-includes:
  - \usepackage{fontspec}
  - \usepackage{tikz}
  - \usetikzlibrary{arrows.meta,positioning,fit,calc,shapes.geometric,backgrounds}
  - \definecolor{bdkgreen}{RGB}{28, 50, 42}
  - \definecolor{bdkgold}{RGB}{215, 195, 145}
  - \definecolor{bdklightgreen}{RGB}{60, 100, 80}
  - \definecolor{bdkpale}{RGB}{230, 240, 235}
  - \definecolor{phase0col}{RGB}{70, 130, 100}
  - \definecolor{phase1col}{RGB}{45, 90, 120}
  - \definecolor{phase2col}{RGB}{140, 90, 50}
  - \definecolor{phase3col}{RGB}{100, 60, 110}
  - \definecolor{phase4col}{RGB}{50, 110, 90}
  - \definecolor{phase5col}{RGB}{130, 70, 70}
  - \definecolor{phase6col}{RGB}{80, 80, 130}
  - \definecolor{phase7col}{RGB}{28, 50, 42}
  - \setbeamercolor{frametitle}{bg=bdkgreen, fg=bdkgold}
  - \setbeamercolor{title}{fg=bdkgreen}
  - \setbeamercolor{structure}{fg=bdkgreen}
  - \setbeamercolor{normal text}{fg=black}
  - \tikzset{phasebox/.style={rounded corners=4pt, minimum width=3.8cm, minimum height=1.1cm, text=white, font=\scriptsize\bfseries, align=center, text width=3.5cm}}
  - \tikzset{srcbox/.style={rounded corners=3pt, minimum width=2.4cm, minimum height=0.7cm, font=\tiny\bfseries, align=center, draw=bdkgreen!60, fill=bdkpale, text=bdkgreen}}
  - \tikzset{detailbox/.style={rounded corners=3pt, minimum width=4.2cm, minimum height=0.55cm, font=\tiny, align=left, text width=4.0cm, fill=white, draw=gray!40}}
  - \tikzset{fatarrow/.style={-{Stealth[length=4pt,width=3pt]}, line width=1pt, color=bdkgreen!70}}
---

# The Problem

## The Gap

- The BDK English Tripitaka has published **~50 volumes** over 40+ years
- The Taisho canon contains **2,993 texts** in Chinese and Japanese
- At the current pace, completion would take **centuries**
- The full Chinese text is digitized and freely available (CBETA, SAT)
- But it remains largely inaccessible to the English-speaking world

## Untranslated Texts

- Hundreds of Pure Land, Abhidharma, Vinaya, and commentary texts
- The complete Japanese Buddhist canon (vols. 56–84), including major works by Honen, Shinran, and Genshin
- Foundational texts like T2058 (the source of all Zen lineage charts) have **never been translated**
- Making these texts accessible serves the founding mission of BDK

# The Opportunity

## AI Has Made a Long-Impossible Effort Newly Feasible

- Large language models can now generate surprisingly strong first-draft translations from classical Chinese and Japanese, especially when guided by glossaries, house conventions, and automated checks
- This dramatically reduces the time and cost of producing initial drafts
- The translations still benefit greatly from expert review and editorial oversight
- **This was not possible even two years ago**

## Example: AI vs. BDK Scholarly Translation

\begin{center}\footnotesize
如是我聞：一時佛在拘尸那國力士生地阿利羅跋提河邊娑羅雙樹間。
\end{center}

\vspace{0.2cm}
\footnotesize
\begin{columns}[T]
\begin{column}{0.47\textwidth}
\textbf{Blum (BDK, 2013):}
\smallskip

\textit{Thus have I heard. At one time the Buddha was between a pair of sal trees by the banks of the Ajiravat\=\i{} River in Ku\'{s}inagara, the native land of the Malla people~.~.~.}
\end{column}
\begin{column}{0.47\textwidth}
\textbf{AI-Assisted (2026):}
\smallskip

\textit{Thus have I heard. At one time the Buddha was in the land of Ku\'{s}inagara, in the Mall\=a territory, between the twin \'{s}\=ala trees on the bank of the Ajitavat\=\i{} River~.~.~.}
\end{column}
\end{columns}
\normalsize

\vspace{0.4cm}
Closely parallel. Minor differences reflect legitimate translation choices.

## Example: Emotional Narrative

\begin{center}\footnotesize
是諸眾生見聞是已，心大憂愁，同時舉聲悲啼號哭：嗚呼慈父，痛哉苦哉。
\end{center}

\vspace{0.2cm}
\footnotesize
\begin{columns}[T]
\begin{column}{0.47\textwidth}
\textbf{Blum (BDK, 2013):}
\smallskip

\textit{Those who saw and heard these things felt great sorrow. Simultaneously they raised their voices in a doleful cry, ``O compassionate father! How distressing, how awful this is!''}
\end{column}
\begin{column}{0.47\textwidth}
\textbf{AI-Assisted (2026):}
\smallskip

\textit{When all these beings saw and heard this, their hearts were filled with great sorrow. Together they raised their voices in grief, weeping and wailing: ``Alas, our compassionate father! How painful, how bitter!''}
\end{column}
\end{columns}
\normalsize

\vspace{0.4cm}
Both capture the emotional intensity. The AI hews closer to the literal Chinese (痛 pain, 苦 bitter).

## Example: Where Expert Review Adds Value

\begin{center}\footnotesize
半字者謂九部經，毘伽羅論者所謂方等大乘經典
\end{center}

\vspace{0.2cm}
\footnotesize
\begin{columns}[T]
\begin{column}{0.47\textwidth}
\textbf{Blum (BDK, 2013):}
\smallskip

\textit{The \textbf{letters of the alphabet}~.~.~. are an allusion to the ninefold sutras, and the \textbf{grammar treatises} are an allusion to~.~.~. the Mah\=ay\=ana scriptures.}

\medskip
Recognizes 半字 as an idiom for ``alphabet'' and 毘伽羅論 as Sanskrit \textit{vy\=akara\d{n}a} (grammar).
\end{column}
\begin{column}{0.47\textwidth}
\textbf{AI-Assisted (2026):}
\smallskip

\textit{The \textbf{half-characters} represent the ninefold canon~.~.~. The \textbf{Vy\=akara\d{n}a treatise} refers to~.~.~. the sutras of the Great Vehicle.}

\medskip
Translates 半字 literally instead of recognizing the idiom. Treats 毘伽羅論 as a proper noun rather than translating.
\end{column}
\end{columns}
\normalsize

\vspace{0.4cm}
These are the layers where expert review adds the most value.

## Quality Still Matters

- AI-generated content needs **careful quality checking**
- Glossaries and indices need **cross-referencing**
- Typesetting must match **BDK standards**
- The goal is not to replace translators or bypass BDK standards
- The goal is to make first-draft production dramatically faster so that **expert effort can be focused where it matters most**

# The Workflow

## Overview: Eight-Phase Pipeline

\begin{center}
\begin{tikzpicture}[node distance=0.25cm]
  % Source nodes
  \node[srcbox] (cbeta) {CBETA XML\\Vols 1–55, 85};
  \node[srcbox, right=0.4cm of cbeta] (sat) {SAT Database\\Vols 56–84};
  \node[srcbox, right=0.4cm of sat] (ref) {84000 / rKTs\\Tibetan parallels};

  % Phase boxes in two columns
  \node[phasebox, fill=phase0col, below=0.6cm of sat] (p0) {Phase 0\\Research \& Glossary};
  \node[phasebox, fill=phase1col, below=0.25cm of p0] (p1) {Phase 1\\AI Translation};
  \node[phasebox, fill=phase2col, below=0.25cm of p1] (p2) {Phase 2\\Automated QA};
  \node[phasebox, fill=phase3col, below=0.25cm of p2] (p3) {Phase 3\\Introduction \& Glossary};

  \node[phasebox, fill=phase4col, right=1.5cm of p0] (p4) {Phase 4\\Interior Typesetting};
  \node[phasebox, fill=phase5col, right=1.5cm of p1] (p5) {Phase 5\\Cover, Index \&\\Back Matter};
  \node[phasebox, fill=phase6col, right=1.5cm of p2] (p6) {Phase 6\\PDF Verification};
  \node[phasebox, fill=phase7col, right=1.5cm of p3] (p7) {Phase 7\\Upload \& Print};

  % Arrows from sources
  \draw[fatarrow] (cbeta.south) -- ++(0,-0.25) -| ([xshift=-0.3cm]p0.north);
  \draw[fatarrow] (sat.south) -- (p0.north);
  \draw[fatarrow] (ref.south) -- ++(0,-0.25) -| ([xshift=0.3cm]p0.north);

  % Left column arrows
  \draw[fatarrow] (p0) -- (p1);
  \draw[fatarrow] (p1) -- (p2);
  \draw[fatarrow] (p2) -- (p3);

  % Bridge arrow
  \draw[fatarrow] (p3.east) -- ++(0.3,0) |- ([yshift=0.0cm]p4.west);

  % Right column arrows
  \draw[fatarrow] (p4) -- (p5);
  \draw[fatarrow] (p5) -- (p6);
  \draw[fatarrow] (p6) -- (p7);

  % Output
  \node[rounded corners=4pt, minimum width=3.8cm, minimum height=0.8cm, fill=bdkgold, text=bdkgreen, font=\scriptsize\bfseries, align=center, below=0.25cm of p7] (out) {Print-ready books\\Free electronic distribution};
  \draw[fatarrow] (p7) -- (out);
\end{tikzpicture}
\end{center}

## Phases 0–1: Research and Translation

\begin{center}
\begin{tikzpicture}[node distance=0.2cm]
  \node[phasebox, fill=phase0col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries] (p0title) {Phase 0: Research \& Preparation};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p0title] (p0d) {%
    \textbullet{} Research each text: author, date, school, existing translations\\
    \textbullet{} Build per-text glossary (60–200 terms) BEFORE translating\\
    \textbullet{} Extract index terms (200–600 entries per text)\\
    \textbullet{} Identify CBETA XML for Taisho margin references};

  \node[phasebox, fill=phase1col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries, below=0.35cm of p0d] (p1title) {Phase 1: AI Translation (Batch API)};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p1title] (p1d) {%
    \textbullet{} Claude Opus via Anthropic Batch API\\
    \textbullet{} System prompt includes: full glossary, BDK house style conventions, IAST diacritics, genre guidance\\
    \textbullet{} Validated cost: \raise.17ex\hbox{$\scriptstyle\sim$}\$0.008/KB of source text per round\\
    \textbullet{} Full corpus processable in weeks};

  \draw[fatarrow] (p0d.south) -- (p1title.north);
\end{tikzpicture}
\end{center}

## Phases 2–3: Quality Assurance and Scholarly Content

\begin{center}
\begin{tikzpicture}[node distance=0.2cm]
  \node[phasebox, fill=phase2col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries] (p2title) {Phase 2: Automated Quality Checks};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p2title] (p2d) {%
    \textbullet{} Automated BDK terminology enforcement (World-Honored One, Three Treasures, etc.)\\
    \textbullet{} Copy editing for Chicago Manual of Style compliance\\
    \textbullet{} Systematic checks: em-dashes, wrong terms, brackets, diacritics\\
    \textbullet{} Completeness verification (no truncated fascicles)};

  \node[phasebox, fill=phase3col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries, below=0.35cm of p2d] (p3title) {Phase 3: Introduction, Glossary \& Index};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p3title] (p3d) {%
    \textbullet{} AI-drafted scholarly introduction from research notes\\
    \textbullet{} Careful quality checking of all generated content\\
    \textbullet{} Generate glossary (60–200 terms) and comprehensive index (200–600 terms)\\
    \textbullet{} Cross-reference consistency check across all files};

  \draw[fatarrow] (p2d.south) -- (p3title.north);
\end{tikzpicture}
\end{center}

## Phases 4–5: Typesetting and Cover

\begin{center}
\begin{tikzpicture}[node distance=0.2cm]
  \node[phasebox, fill=phase4col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries] (p4title) {Phase 4: BDK Interior Typesetting};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p4title] (p4d) {%
    \textbullet{} Automated LaTeX generation; 3 XeLaTeX passes + makeindex\\
    \textbullet{} Front matter: half-title, title page, copyright, A Message, Editorial Foreword, Table of Contents, Introduction\\
    \textbullet{} Body: Taisho margin refs from CBETA XML, running headers, verse blocks\\
    \textbullet{} Output: print-ready interior PDF};

  \node[phasebox, fill=phase5col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries, below=0.35cm of p4d] (p5title) {Phase 5: Cover, Index \& Back Matter};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p5title] (p5d) {%
    \textbullet{} Two-column index with letter headings; glossary with hanging indent\\
    \textbullet{} BDK cover: dark green (\#1c322a) background, gold text, Dharma wheel\\
    \textbullet{} Spine: cream text, wheel, ``Numata Center''\\
    \textbullet{} IngramSpark-compliant cover spread (front + spine + back)};

  \draw[fatarrow] (p4d.south) -- (p5title.north);
\end{tikzpicture}
\end{center}

## Phases 6–7: Verification and Publication

\begin{center}
\begin{tikzpicture}[node distance=0.2cm]
  \node[phasebox, fill=phase6col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries] (p6title) {Phase 6: PDF Verification};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p6title] (p6d) {%
    \textbullet{} Page-by-page comparison against BDK reference volumes\\
    \textbullet{} 20+ item checklist: every front matter element, body formatting, back matter\\
    \textbullet{} Cross-reference consistency (all files agree on names, dates, numbers)\\
    \textbullet{} Font embedding verification};

  \node[phasebox, fill=phase7col, minimum width=12cm, text width=11.5cm, minimum height=0.9cm, font=\small\bfseries, below=0.35cm of p6d] (p7title) {Phase 7: Upload to Print-on-Demand};
  \node[detailbox, minimum width=12cm, text width=11.5cm, font=\small, below=0.1cm of p7title] (p7d) {%
    \textbullet{} Upload interior + cover PDFs to IngramSpark; no inventory required\\
    \textbullet{} Free electronic distribution: Internet Archive, GitHub, dedicated website\\
    \textbullet{} Re-translatable: entire corpus can be re-run as AI models improve\\
    \textbullet{} Each edition incorporates better models and community feedback};

  \draw[fatarrow] (p6d.south) -- (p7title.north);
\end{tikzpicture}
\end{center}

# Working Prototype

## T2058: From Chinese to BDK-Format Book in Hours

- **Input**: 6 fascicles of classical Chinese (付法藏因緣傳)
- **Translation**: Claude Opus batch API, 6 requests, \$0.95
- **Quality**: Zero wrong BDK terms, zero brackets on first pass
- **Typesetting**: Automated BDK-format interior (166 pages) + cover
- **Result**: Print-ready PDF closely matching BDK house style

\vspace{0.3cm}

This text has **never before been translated into English**.

## Additional Prototype Volumes

\footnotesize

| Taisho | Title | Pages |
|---|---|---:|
| T0374 | The Nirvana Sutra | 1,187 |
| T1602 | Compendium Elucidating the Sacred Teaching | 514 |
| T2589 | Keizan Shingi | 329 |
| T2682 | Essentials of Birth in the Pure Land | 322 |
| T0222 | Brilliance Praise Sutra | 307 |

\normalsize

Physical copies available for review at this meeting.

## Lessons Learned from Prototyping

1. **Front-loading quality in prompts works**: Including the full glossary and BDK conventions in the system prompt eliminated most terminology errors at source
2. **AI-generated content needs careful quality checking**: Our introduction contained plausible-sounding errors (wrong century, wrong Sanskrit spelling) that were caught through dedicated review
3. **Automated typesetting is achievable**: BDK format can be closely replicated in LaTeX, with front matter, margin references, glossary, and index generated automatically
4. **The pipeline is reproducible**: When models improve, texts can be re-translated and re-typeset in weeks

## Pilot Cost Validation

A small-scale pilot validated the approach across three rounds of testing:

| Round | Texts | Cost | Cost/KB |
|---|---|---|---|
| Pilot (12 texts) | 12 | ~\$2 | \$0.04 |
| Medium batch (97 texts) | 133 requests | \$13.28 | \$0.012 |
| Large texts (4 texts) | 31 requests | \$6.28 | \$0.008 |

- **Steady-state cost: \$0.008/KB** of source text per round (multiple rounds may be needed)
- **96% of texts** passed automated completeness checks on first attempt
- IAST diacritics, verse formatting, and BDK conventions consistently correct
- Full batch processing completed within 24 hours

# What the Pilot Would Test

## Questions the Pilot Is Designed to Answer

- **Quality across genres**: Do sutras, commentaries, Vinaya texts, and Japanese works all translate well?
- **Quality control workflow**: What level of review is needed, and how should it be prioritized across 2,500+ texts?
- **Cost realism**: Do the prototype cost figures hold up at meaningful scale?
- **House-style consistency**: Can BDK conventions be reliably enforced across diverse texts?
- **Feasibility at scale**: Can the pipeline handle the full range of the canon?

# About Me

## Why I Am the Person to Do This

**Technical**: 30+ years in data science and AI (Apple, Google, Facebook, Instagram). Published research in computational linguistics (Pali Tipiṭaka). Author of the R package `tipitaka`. Deep experience with AI pipelines at scale.

**Buddhist**: Ordained Zen priest, transmitted teacher (Sōtōshū, zuise at Eiheiji and Sōjiji 2025). Board Chair, San Francisco Zen Center. Former Guiding Teacher, Jikoji Zen Center. Trustee, Naropa University.

**Publications**: Contributing Editor, *Tricycle*. Contributor, *Lion's Roar*. Author, *Buddha's Office* and *Buddha's Diet*.

**The rare intersection**: both the technical skills to build the pipeline and the Buddhist training to understand what quality means for these texts.

# The Pilot Proposal

## Pilot Budget (\$50,000)

\vspace{0.2cm}

| Category | Estimate |
|---|---:|
| Pipeline engineering (2–3 months) | \$25,000 |
| AI API costs (translation, glossary, quality checking) | \$10,000 |
| Dedicated hardware | \$5,000 |
| Infrastructure (hosting, ISBNs, IngramSpark) | \$3,000 |
| Contingency | \$7,000 |
| **Subtotal** | **\$50,000** |

**Deliverable**: 20–50 BDK-format volumes for committee review, with physical printed copies.

**Timeline**: 3 months from funding.

## What We Are Asking For

We are seeking BDK's partnership on a focused pilot project:

1. **Fund the pilot** (\$50,000 over 3 months)
2. **Help select pilot texts** across genres, schools, and difficulty levels
3. **Review the results** through BDK's editorial process
4. **Conversation about future expansion** if the pilot succeeds

\vspace{0.3cm}

The purpose is not to bypass BDK's standards, but to determine whether a hybrid AI-assisted workflow can reliably accelerate first-draft translation while preserving editorial quality.

## The Vision: Completion in One Year

If the pilot succeeds, full production of all remaining texts could be completed within **12 months**:

| Months | Activity |
|---|---|
| 1–3 | Pilot: 20–50 texts selected with BDK |
| 4–5 | Translate full remaining corpus |
| 6–9 | Generate all ~2,500+ volumes |
| 10–12 | Final verification and upload |

It took 1,000 years to translate the canon into Chinese. With AI assistance, we could complete the English translation in one.

The pipeline is designed so that translations improve over time: each new edition incorporates better AI models and community feedback.

## Thank You

\begin{center}
\Large
May the rays of the Wisdom of the Compassionate One\\
reach each and every person in the world.\\[0.5cm]
\normalsize
--- \textsc{Numata} Yehan, ``A Message on the Publication\\of the English Tripi\d{t}aka,'' August 7, 1991
\end{center}
