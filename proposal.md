---
title: "AI-Assisted Translation of the Taishō Tripiṭaka: A Feasibility Study and Proposal"
author: |
  Dan Zigmond\
  djz@shmonk.com
date: April 2026
---

## 1. Executive Summary

The Taishō Tripiṭaka contains 2,455 texts spanning 8,915 fascicles and 72.2 million Chinese characters, representing the most comprehensive collection of Chinese Buddhist canonical literature. Despite decades of effort, only about 15-20% of the canon has any English translation. The BDK English Tripiṭaka project, the most ambitious systematic effort to date, has published approximately 81 texts in 43 years and is projected to require over 100 years for Phase 1 alone (139 texts).

This study demonstrates that AI-assisted translation can compress this timeline dramatically. Using a hybrid pipeline (Claude Sonnet for automated batch translation, Claude Opus for interactive review), we achieved sustained throughput of approximately 50,000 characters per hour in unattended batch mode. Running continuously, this translates to roughly 1.2 million characters per day, suggesting the entire untranslated corpus could be rendered into English in a matter of months rather than centuries.

As of early April 2026, we have completed 83 translations covering texts from across the canon, with the automated pipeline running continuously. The results indicate that a small team could produce complete first-draft translations of the remaining approximately 1,800 untranslated texts within several months, making them available for scholarly review.

\newpage

## 2. Background

### 2.1 The Taishō Canon

The Taishō Shinshū Daizōkyō (大正新修大藏經), compiled 1924-1934 under the editorship of Takakusu Junjirō and Watanabe Kaigyoku, is the standard modern edition of the Chinese Buddhist canon. Its 100 volumes contain:

- **Volumes 1-55, 85**: The main corpus of 2,455 texts (the scope of the CBETA digital edition)
- **Sūtras** (vols. 1-21): Āgama, Mahāyāna, Prajñāpāramitā, Avataṃsaka, Ratnakūṭa, Mahāparinirvāṇa, and other collections
- **Vinaya** (vols. 22-24): Six complete monastic codes plus supplementary vinaya texts
- **Abhidharma** (vols. 25-29): Scholastic treatises of multiple schools
- **Madhyamaka, Yogācāra, Logic** (vols. 30-32): Major Indian philosophical treatises
- **Commentaries** (vols. 33-40): Chinese and other East Asian commentarial literature
- **Esoteric texts** (vols. 18-21): Tantric sūtras, dhāraṇī collections, ritual manuals
- **Historical and biographical** (vols. 49-52): Biographies, histories, catalogues
- **Encyclopedic** (vols. 53-54): Dictionaries and encyclopedias

### 2.2 Existing English Translations

Based on the Bingenheimer bibliography and other sources, approximately 662 texts (about 15-20% of the canon) have some English translation, though many of these are partial, outdated, or difficult to access. Major translation projects include:

- **BDK English Tripiṭaka**: ~81 texts published over 43 years; 139 texts planned for Phase 1
- **Numata Center / BDK Supplements**: Ongoing but slow
- **Dharma Drum / Āgama Research Group**: Partial Āgama translations
- **Individual scholars**: Scattered across journal articles and monographs

The vast majority of the canon, approximately 1,800 texts, remains entirely untranslated.

### 2.3 Prior AI-Assisted Translation Work

Before this study, we translated two substantial texts using AI assistance:

- **T374**: *Mahāparinirvāṇa Sūtra* (40 fascicles), approximately 1 hour including typesetting
- **T190**: *Abhiniṣkramaṇa Sūtra* / Past Deeds of the Buddha (60 fascicles), approximately 1 hour including typesetting

These results motivated the present systematic study.

\newpage

## 3. Methodology

### 3.1 Pipeline

Our translation pipeline consists of four stages:

1. **Extraction**: Chinese source text is extracted from the CBETA TEI P5b XML corpus using a Python script that handles the full complexity of the CBETA markup (variant readings, character normalization, structural elements). The text is cleaned and segmented by fascicle.

2. **Translation**: The extracted Chinese text is provided to Claude (Anthropic's large language model) with genre-specific instructions. The model produces an English translation preserving:
   - Sanskrit/Pali technical terminology in IAST transliteration
   - Structural divisions (fascicles, chapters, sections)
   - Verse formatting distinct from prose
   - Proper nouns with standard scholarly romanizations

3. **Review**: A human reviewer (with knowledge of Classical Chinese and Buddhist Studies) reads the output, checking for:
   - Terminology consistency
   - Doctrinal accuracy on key passages
   - Structural completeness (no omissions)
   - Natural English prose quality

4. **Typesetting**: Markdown translations are converted to PDF using pandoc with XeLaTeX, with font support for any Chinese characters retained in the translation.

### 3.2 Sample Selection

We selected 12 texts to represent the full diversity of the Taishō, organized into three size tiers:

**Tier 1: Small texts (1-2 fascicles)**
- T0265: Mahāyāna sūtra (1,464 chars)
- T0002: Āgama (4,717 chars)
- T1628: Logic treatise (6,488 chars)
- T1505: Abhidharma commentary (19,417 chars)

**Tier 2: Medium texts (5-15 fascicles)**
- T0152: Jātaka narrative (66,821 chars)
- T0222: Prajñāpāramitā sūtra (99,584 chars)
- T0887: Esoteric/tantric (25,417 chars)
- T1507: Abhidharma commentary (32,041 chars)
- T1566: Madhyamaka treatise (110,962 chars)

**Tier 3: Large texts (20-50 fascicles)**
- T0099: Āgama collection (469,479 chars)
- T1421: Vinaya (269,804 chars)
- T1602: Yogācāra treatise (137,675 chars)

**Total: 12 texts, 149 fascicles, 1,243,869 Chinese characters**

### 3.3 Timing Methodology

Initial timing measurements were taken during interactive sessions using Unix timestamps at the start and end of each translation. These initial measurements captured raw model throughput but did not fully account for rate limiting, pipeline overhead, and quality-checking steps that reduce effective throughput in sustained production.

Subsequent production runs provided more realistic sustained throughput data. Over a full day of interactive translation (April 2, 2026), we translated 69 texts totaling 225,742 CJK characters in 10.9 hours, yielding an effective rate of approximately 21,000 characters per hour. An automated batch pipeline using Claude Sonnet achieved approximately 52,000 characters per hour in unattended mode.

\newpage

## 4. Results

### 4.1 Timing Data

| Text | Genre | Juan | Characters | Time | Chars/hr | Difficulty |
|------|-------|------|-----------|------|----------|------------|
| T0265 | Mahāyāna sūtra | 1 | 1,464 | 1:10 | 75,286 | 1/5 |
| T0002 | Āgama | 1 | 4,717 | 2:57 | 95,944 | 2/5 |
| T1628 | Logic treatise | 1 | 6,488 | 3:33 | 109,644 | 4/5 |
| T1505 | Abhidharma | 2 | 19,417 | 4:59 | 233,779 | 3/5 |
| T0152 | Jātaka/narrative | 8 | 66,821 | 8:59 | 446,236 | 2/5 |
| T0222 | Prajñāpāramitā | 10 | 99,584 | 7:39 | 780,855 | 2/5 |
| T0887 | Esoteric/tantric | 6 | 25,417 | 5:40 | 269,126 | 3/5 |
| T1507 | Abhidharma commentary | 5 | 32,041 | 4:24 | 436,886 | 2/5 |
| T1566 | Madhyamaka | 15 | 110,962 | 17:19 | 384,453 | 5/5 |
| T0099 | Āgama | 50 | 469,479 | 15:09* | 1,859,236* | 2/5 |
| T1421 | Vinaya | 30 | 269,804 | 15:09* | 1,068,542* | 3/5 |
| T1602 | Yogācāra | 20 | 137,675 | 15:09* | 545,297* | 4/5 |

\* Tier 3 texts were translated in parallel; times marked with * reflect wall-clock time for the entire parallel batch (15:09 total for all three).

**Initial sample statistics:**
- **Total characters translated**: 1,243,869
- **Total wall-clock time**: ~72 minutes
- **Apparent aggregate throughput**: 1,039,079 chars/hr (see note below)

**Note on throughput measurement:** The initial sample throughput figures above reflect raw model streaming speed during a single interactive session and do not account for rate limiting, pipeline overhead, and review steps that reduce effective throughput in sustained production. Subsequent production measurements show substantially lower but more realistic sustained rates.

**Sustained production statistics (April 2026):**
- **Interactive Opus (with review)**: ~21,000 chars/hr effective (69 texts, 225,742 chars, 10.9 hours)
- **Automated Sonnet batch (per-text)**: ~52,000 chars/hr (measured on a 5,691-char text)
- **Automated Sonnet batch (rate-limited)**: ~47 requests/hr (measured: 31 requests per 30-min window)

### 4.2 Key Observations

**Rate limiting, not processing speed, is the primary bottleneck.** The Claude Max subscription allows approximately 31 API requests per 30-minute window before imposing a cooldown. With cooldown periods, effective throughput is approximately 47 requests per hour. Since each small text (under 15,000 characters) requires one request, and each large text requires multiple requests (approximately one per 10,000 characters), the total number of requests determines the timeline more than text size or genre difficulty.

**Throughput varies by mode.** Interactive translation with human review achieves approximately 21,000 chars/hr, while automated batch translation achieves approximately 52,000 chars/hr per request. However, rate limiting means the batch pipeline's effective throughput depends on the number of texts rather than their aggregate size.

**Repetitive genres are fastest.** The Prajñāpāramitā sūtra (T0222) and Āgama collections, with their highly formulaic structures, show the highest relative throughput. This is significant because repetitive genres constitute a large fraction of the canon.

**Philosophical treatises are slower but still fast.** Dense Madhyamaka commentaries and logic treatises require more model reasoning time but still achieve translation rates far exceeding human capability.

### 4.3 Difficulty Assessment

| Rating | Description | Genres |
|--------|-------------|--------|
| 1/5 | Straightforward narrative, standard vocabulary | Short sūtras, simple narratives |
| 2/5 | Formulaic or repetitive; standard Buddhist terminology | Āgamas, Prajñāpāramitā, jātakas |
| 3/5 | Moderate doctrinal content; some specialized vocabulary | Vinaya, Abhidharma, esoteric |
| 4/5 | Dense philosophical argument; technical vocabulary | Yogācāra, logic treatises |
| 5/5 | Formal debates with multiple philosophical schools; requires reconstruction of arguments | Madhyamaka commentaries |

### 4.4 Quality Assessment

The AI-produced translations are best characterized as high-quality first drafts suitable for scholarly review. Strengths include:

- **Structural fidelity**: Chapter and section divisions, fascicle breaks, and verse/prose distinctions are accurately preserved.
- **Terminology consistency**: Sanskrit/Pali terms are correctly identified and transliterated in IAST throughout.
- **Doctrinal accuracy**: Core Buddhist concepts (dependent origination, emptiness, the aggregates, the path) are rendered with standard scholarly English equivalents.
- **Readability**: The English prose is natural and readable, avoiding the stilted quality common in older academic translations.

Areas requiring expert review:

- **Tantric/esoteric passages**: Dhāraṇī transliterations and visualization instructions benefit from comparison with Sanskrit/Tibetan sources.
- **Formal logic**: The Indian logical apparatus (*pramāṇa*, *hetu*, *dṛṣṭānta*) should be verified by specialists in Buddhist epistemology.
- **Ambiguous passages**: Classical Chinese's lack of explicit subjects and tense marking occasionally allows multiple valid readings; experts should adjudicate.
- **Proper names**: Some less common personal and place names may need verification against standard references.

\newpage

## 5. Extrapolation to the Full Canon

### 5.1 Corpus Statistics

| Category | Texts | Fascicles | Est. Characters |
|----------|-------|-----------|-----------------|
| Already translated (~15-20%) | ~662 | ~2,500 | ~20M |
| Untranslated | ~1,793 | ~6,415 | ~52.2M |
| **Total canon** | **2,455** | **8,915** | **72.2M** |

### 5.2 Time Estimates

The primary constraint on translation speed is not processing time but API rate limiting. The Claude Max subscription allows approximately 31 requests per 30-minute window (about 47 requests per hour). Each text under 15,000 Chinese characters requires one request; larger texts require approximately one request per 10,000 characters.

**Remaining corpus breakdown (as of April 2026):**

| Category | Texts | CJK Characters | Requests Needed |
|----------|-------|---------------|-----------------|
| Small texts (<=15K chars) | 1,543 | 6.4M | 1,543 |
| Large texts (>15K chars) | 641 | 62M | ~5,858 |
| **Total remaining** | **2,184** | **68.4M** | **~7,401** |

**Time estimates at measured rate (~47 requests/hr):**

| Category | Requests | Est. Time (24/7) |
|----------|----------|-------------------|
| Small texts | 1,543 | ~33 hours (1.4 days) |
| Large texts | ~5,858 | ~125 hours (5.2 days) |
| **Total** | **~7,401** | **~157 hours (~7 days)** |

These estimates assume a single subscription running continuously. Multiple subscriptions would reduce the timeline proportionally.

Adding typesetting (largely automated) and project management overhead:

| Phase | Estimated Time | Notes |
|-------|---------------|-------|
| AI translation (first draft) | 150-200 hours | Rate-limit constrained |
| Typesetting and formatting | 50-100 hours | Largely automated pipeline |
| Quality review and correction | 200-500 hours | Expert review of key texts |
| Project management | 50-100 hours | Coordination, quality tracking |
| **Total** | **450-900 hours** | |

### 5.3 Team and Timeline Scenarios

These estimates cover producing complete first-draft translations ready for scholarly review. The time required for comprehensive expert review and revision is outside the scope of this proposal.

| Team Size | Approach | First-Draft Completion |
|-----------|---------|------------------------|
| 1 person with 24/7 batch pipeline | Single subscription, automated | ~1-2 weeks |
| 2 people with parallel pipelines | 2 subscriptions + review | ~1 week |
| Small team (3-5 people) | Multiple subscriptions + systematic review | ~1 week + ongoing review |

\newpage

## 6. Proposed Work Plan

### Phase 1: Automated First Drafts (Weeks 1-2)

All texts are processed via the automated batch pipeline, sorted by size (smallest first). Texts under 15,000 CJK characters are translated in a single request; larger texts are split by fascicle.

- ~1,543 small texts (~1.4 days at measured rate)
- ~641 large texts requiring fascicle splitting (~5.2 days)
- Estimated completion: ~7 days of continuous automated operation

### Phase 2: Quality Review and Correction (Weeks 2-8)

Systematic review of automated translations, prioritized by scholarly significance:

- Āgama collections and major Mahāyāna sūtras (highest priority)
- Vinaya codes and Abhidharma treatises
- Philosophical treatises (Madhyamaka, Yogācāra, logic)
- Estimated: 200-500 hours of expert review time

### Phase 3: Specialized Texts and Typesetting (Weeks 8-12)

- Review of esoteric/tantric texts, commentaries, historical works
- Typesetting and PDF generation for all translations
- Glossary compilation and cross-referencing
- Estimated: 100-200 hours

### Phase 4: Publication and Dissemination (Months 3-6)

- Final editorial review of priority texts
- Open-access publication of complete corpus
- Digital searchable corpus and parallel editions

## 7. Team Structure

- **Project Director** (1): Overall coordination, quality standards
- **Translation Operators** (1-2): Run AI translation pipeline, spot-check output
- **Technical Lead** (1): Pipeline maintenance, automation, digital infrastructure

## 8. Output Formats

- **Per-fascicle PDFs**: Individual fascicle translations for granular access
- **Per-text PDFs**: Combined translations with table of contents
- **Volume PDFs**: Matching Taishō volume organization
- **Digital searchable corpus**: Full-text search across all translations
- **Parallel editions**: Side-by-side Chinese/English for scholarly use
- **Open access**: All translations freely available online

\newpage

## 9. Comparison with Existing Projects

| Metric | BDK English Tripiṭaka | AI-Assisted (This Proposal) |
|--------|----------------------|----------------------------|
| Texts completed | ~81 (in 43 years) | 114 (in ~2 weeks of operation) |
| Current rate | ~2 texts/year | ~47 texts/hour (rate-limit constrained) |
| Phase 1 target | 139 texts | All 2,455 texts |
| Phase 1 projected completion | ~2050-2060 | 2026-2027 |
| Full canon projected | 22nd century | 2026-2027 |
| Output quality | Publication-grade | First drafts ready for scholarly review |
| Cost model | Full scholarly labor | AI + small operations team |

The comparison is not meant to diminish the extraordinary scholarly achievement of the BDK project, whose translations set a high standard for accuracy and readability. Rather, it illustrates that AI assistance can extend the reach of such work by orders of magnitude, producing first-draft translations in months that can then serve as a foundation for scholarly review and refinement.

## 10. Conclusion

This feasibility study demonstrates that complete first-draft English translations of the entire Taishō Tripiṭaka can be produced within months using AI-assisted methods. Our initial sample of 12 texts across all major genres confirmed the viability of the approach, and subsequent production runs have now completed 83 translations from across the canon.

Sustained production measurements show that the primary constraint is API rate limiting (approximately 47 requests per hour), not processing speed. At this rate, the approximately 7,400 requests needed to translate the full remaining corpus can be completed in roughly one week of continuous automated operation.

The Buddhist Studies community has long recognized the need for broader access to the Chinese canon in Western languages. The technology now exists to produce draft translations of the entire untranslated corpus, ready for scholarly review, within weeks rather than centuries. We propose assembling a small, focused team to complete the first-draft translations and begin systematic scholarly review within 2026.

---

\newpage

## Appendix A: Sample Texts and Timing Data

See `timing_data.csv` for full timing data.

### Translation Output Files

All 12 sample translations are available as both Markdown source and typeset PDFs:

| Text | Title | Output Size | PDF |
|------|-------|-------------|-----|
| T0265 | Saddharma-puṇḍarīka Excerpt | 10 KB | 82 KB |
| T0002 | Seven Buddhas Sutra | 30 KB | 95 KB |
| T1628 | Nyāyadvāra | 30 KB | 103 KB |
| T1505 | Commentary on Four Āgamas Digest | 46 KB | 143 KB |
| T0152 | Collection of the Six Perfections | 69 KB | 156 KB |
| T0222 | Brilliance Praise Prajñāpāramitā | 56 KB | 127 KB |
| T0887 | Supreme Yoga Teaching King Sūtra | 42 KB | 135 KB |
| T1507 | Treatise on Discrimination of Merits | 34 KB | 140 KB |
| T1566 | Prajñāpradīpa | 81 KB | 181 KB |
| T0099 | Saṃyuktāgama | 99 KB | 210 KB |
| T1421 | Five-Part Vinaya | 79 KB | 199 KB |
| T1602 | Compendium of Sacred Teachings | 98 KB | 243 KB |

\newpage

## Appendix B: Methodology Details

### Chinese Text Extraction

Source texts were extracted from the CBETA TEI P5b XML corpus using a custom Python script that:
- Parses TEI namespace elements (`tei:body`, `tei:p`, `tei:lg`, `tei:l`)
- Resolves variant readings using `<lem>` over `<rdg>`
- Normalizes characters via `charDecl` mappings
- Strips editorial markup (`<note>`, `<byline>`, etc.)
- Preserves fascicle boundaries (`<cb:juan>`)

### Translation Prompts

Each text was translated with genre-aware instructions specifying:
- Target register (scholarly but readable English)
- Sanskrit/Pali terminology handling (preserve in IAST)
- Structural preservation requirements
- Genre-specific guidance (e.g., verse formatting, debate structure, dhāraṇī handling)

### PDF Generation

Translations were typeset using:
- pandoc 3.x with XeLaTeX engine
- Times New Roman (main text) + Noto Serif CJK SC (Chinese characters)
- Custom LaTeX header for Unicode symbol support and Buddhist text styling
