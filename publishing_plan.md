# Plan: Complete English Taishō Tripiṭaka

## The Vision

Publish the first complete English translation of the Taishō Tripiṭaka: all ~2,993 texts across the full 85-volume set (including the Japanese volumes 56-84), available both electronically (free) and as print-on-demand books. Build a reproducible pipeline so the entire corpus can be re-translated every six months as AI models improve.

---

## Current State

### Two Pools of Texts

The Taishō Tripiṭaka spans 85 main volumes plus supplementary material:

1. **Volumes 1-55 + 85** (main Chinese canon): 2,452 texts
2. **Volumes 56-84** (Japanese Buddhist writings): 541 texts, extracted from the SAT Taishōzō database

**Total scope: ~2,993 texts.** All now merged into a single `full_catalog.json`.

### Progress

- **1,225 of 2,993 texts translated** (~41% by text count, ~6% by volume)
- Done: ~16.5M bytes of Chinese → 19.4M bytes of English
- Remaining: **1,768 texts, ~331M bytes** of Chinese source
- **The remaining work is ~20x larger by volume** because we've done the small texts first
- 4 texts already produced as print-ready 6×9 books (T0222, T0374, T1602, T2682)
- Working book pipeline exists: `generate_taisho_book.py`, `generate_cover.py`

### What Remains by Size (all volumes)

| Fascicle count | Texts remaining | Examples |
|---|---|---|
| 1 fascicle | 774 | Short sūtras, a/b variant recensions, Japanese commentaries |
| 2-5 fascicles | 623 | Medium sūtras, commentaries |
| 6-20 fascicles | 286 | Major sūtras, Abhidharma texts, Japanese treatises |
| 21-50 fascicles | 54 | Avataṃsaka, Nirvāṇa, etc. |
| 51+ fascicles | 31 | Prajñāpāramitā (600), Yogācārabhūmi (100), Mahāvibhāṣā (200) |

These counts include the 154 a/b variant recensions (two different translations filed under one T-number) and the 540 remaining Japanese volumes (56-84), which include commentaries, historical records, and doctrinal treatises by Japanese Buddhist scholars (Saichō, Kūkai, Dōgen, Hōnen, Shinran, Nichiren, etc.). The Japanese texts are classical Chinese/kanbun, so the same translation approach applies, though some may have Japanese-inflected syntax.

### Source Data: Complete

As of 2026-04-05, all 2,993 texts have Chinese source files in `chinese/T{XXXX}.txt`:
- The SAT catalog (541 texts, vols 56-84) has been merged into `full_catalog.json`
- 154 a/b variant recensions (texts with suffixed T-numbers like T0128a/T0128b) have been extracted from CBETA XML
- **Coverage: 2,993 / 2,993 = 100%**

### The Monsters (51+ fascicle texts)

These 24 texts alone account for ~2,500 fascicles. The largest include:
- T0220 大般若波羅蜜多經 (Mahāprajñāpāramitā Sūtra) — 600 fascicles
- T1545 阿毘達磨大毘婆沙論 (Abhidharma-mahāvibhāṣā) — 200 fascicles
- T0310 大寶積經 (Mahāratnakūṭa) — 120 fascicles
- T1579 瑜伽師地論 (Yogācārabhūmi) — 100 fascicles
- T1509 大智度論 (Mahāprajñāpāramitā-śāstra) — 100 fascicles
- T2122 法苑珠林 (Fayuan Zhulin) — 100 fascicles
- T2016 宗鏡錄 (Zongjing Lu) — 100 fascicles

---

## Phase 1: Complete All Translations

### Approach

Continue the current workflow: read Chinese source, translate to markdown, verify header, mark done. Process texts in order of ascending size, working through batches.

For multi-fascicle texts, translate one fascicle at a time within a session. Very large texts (50+ fascicles) will span many sessions.

### Time Estimate (using Claude Max subscription)

The remaining work totals ~98M output tokens across 10,095 fascicles. Based on our observed throughput of ~250K output tokens per 2-3 hour session:

| Throughput assumption | Days | Months |
|---|---|---|
| Conservative (500K tokens/day) | 196 | **6.5** |
| Moderate (750K tokens/day) | 130 | **4.3** |
| Optimistic (1M tokens/day) | 98 | **3.3** |

The moderate estimate of **4-5 months** is most realistic, assuming several hours of active session management per day on the $200/month Max plan. The main bottleneck is the 31 texts with 51+ fascicles (2,826 fascicles total, including the 600-fascicle Prajñāpāramitā), which alone account for ~25M output tokens.

### Cost (Max Subscription Approach)

| Duration | Max @ $100/month | Max @ $200/month |
|---|---|---|
| 4 months | $400 | $800 |
| 5 months | $500 | $1,000 |
| 7 months | $700 | $1,400 |

The $200/month tier is recommended for higher throughput. **Total translation cost via Max: ~$800-1,400.**

**Trade-off**: Max is slower (days/months vs hours) but requires no automation code and allows interactive quality control.

### Cost Option B: API (Faster, Possibly Cheaper)

With the Claude 4.6 generation, API pricing dropped dramatically. Opus 4.6 is $5/$25 per million input/output tokens (vs the old Opus 4.1 at $15/$75). Combined with batch API (50% off) and prompt caching (90% off cached input), the math changes significantly.

**Token volumes for remaining 1,768 texts (~331M bytes Chinese, 10,095 fascicles):**
- Input: ~181M tokens (110M Chinese source + 71M system prompts across 10K calls)
- Output: ~98M tokens (English translations)

**Translation costs (Opus 4.6 only — best quality required):**

| Optimization level | Input cost | Output cost | Total |
|---|---|---|---|
| Standard API ($5/$25 per M) | $905 | $2,450 | **$3,350** |
| Batch API (50% off) | $453 | $1,225 | **$1,678** |
| Batch + prompt caching (estimated) | $298 | $1,225 | **$1,523** |
| **Batch + caching (empirical, POC)** | **~$420** | **~$2,080** | **~$2,500** |

The empirical cost from POC testing ($0.008/KB of Chinese source) is higher than the token-based estimate because output tokens (which dominate at 83% of cost) were underestimated. Output cost is the main driver and is not reduced by caching.

**Glossary + index generation (all 2,993 texts, using Sonnet batch):** ~$630

**Important note on interactive vs. batch costs:** The batch estimates above assume each fascicle is an independent API call with a small, fixed system prompt. In practice, interactive use (Claude Code, claude.ai, or Max overflow billing) is **3-4x more expensive** because: (1) conversation context accumulates with each turn, inflating input tokens; (2) no batch discount; (3) no prompt caching. When the Max subscription hit its limit in early April 2026, overflow billing for a few volumes cost tens of dollars — consistent with ~$5,000-6,000 for the full corpus at interactive rates.

**Key advantage of batch API: speed and cost.** The batch API processes all submitted requests within 24 hours. The entire remaining corpus (~10,095 fascicle-level requests) could be translated in **1-3 days** for ~$2,500 (empirically validated at $0.008/KB of Chinese source), vs. months at $5,000+ interactively.

**Trade-off**: Requires building a `translate_all.py` automation script (~1-2 weeks of development), but this script is exactly what we need for the reproducible re-run pipeline anyway.

### POC Validation (April 2026)

Three rounds of empirical testing validated the batch approach:

| Round | Texts | Source KB | Requests | Cost | Cost/KB |
|---|---|---|---|---|---|
| R1 | 12 (pilot) | ~50 | 12 | ~$2 | ~$0.04 |
| R2 | 97 | ~1,140 | 133 | $13.28 | $0.012 |
| R3 | 4 (large) | 777 | 31 | $6.28 | $0.008 |

**Key finding:** The steady-state cost per KB of Chinese source (excluding one-time cache-write overhead) is **$0.008/KB**, remarkably consistent between R2 ($0.00796/KB) and R3 ($0.00799/KB). R2's higher raw cost/KB ($0.012) was inflated by cache-write overhead (32% of R2 cost vs. 1% of R3).

**Revised full-corpus projection:** 305,500 KB × $0.008/KB = **~$2,500** (not the earlier token-based estimate of $1,500). The discrepancy is because output tokens (57-83% of cost at $12.50/M batch rate) were underestimated.

**Quality:** 96% of texts passed completeness checks. 6 of 133 texts had truncation issues in R2 (fixable by retry or fascicle-level splitting). IAST diacritics, verse formatting, and headers were consistently good. Dhāraṇī reconstruction quality was validated via the era-aware transliteration system built in parallel with the POC.

**Speed:** R3 batch (31 requests) completed in under 24 hours. The full corpus (~10,000 requests) should complete in 1-3 days.

**Total POC cost:** $19.56 of $100 budget.

### Recommended Approach: Batch API with Selective Max Review

1. Build `translate_all.py` and use **Opus batch API** for all translations (~$2,500, 1-3 days)
2. Use **Max subscription** selectively to review and revise the most complex texts (the "monsters" with 50+ fascicles, texts with unusual formatting)
3. Use **Sonnet batch API** for glossary and index generation (~$630)

**Estimated total translation cost:**
- Opus batch+cache for all 1,768 remaining texts: ~$2,500
- Max subscription for 2-3 months of review/revision: $400-600
- Sonnet batch for glossaries/indices: ~$630
- **Total: ~$3,500-3,700**

---

## Phase 2: Automated Book Production Pipeline

### What We Need to Build

Take the existing per-book pipeline (`generate_taisho_book.py` + `generate_cover.py`) and wrap it in a batch orchestrator that can process all ~656 volumes (2,993 texts bundled/split per the plan below) without manual intervention.

### Components

1. **Batch glossary generator** (`batch_glossary.py`)
   - For each translation, use AI to extract 60-200 glossary entries
   - Standard categories: doctrinal terms, proper names, places, texts cited
   - Output: `glossaries/glossary_T{XXXX}.md` for each text
   - Estimated cost: ~$0.50-1.00 per text using Haiku/Sonnet = ~$1,500 via API, or included in Max sessions

2. **Batch index term extractor** (`batch_index.py`)
   - For each translation, extract 100-600 indexable terms
   - Output: `indices/index_terms_T{XXXX}.txt`
   - Can run alongside glossary generation

3. **Batch interior PDF generator** (`batch_interior.py`)
   - Run `generate_taisho_book.py` for each text
   - Handle multi-volume splitting for texts over ~600 pages
   - Estimated time: ~2-5 minutes per text × 2,452 = ~5-8 days of compute
   - No AI cost; purely local LaTeX compilation

4. **Batch cover generator** (`batch_covers.py`)
   - Generate IngramSpark-compliant cover spreads for each text
   - Auto-calculate spine width from page count
   - Standard back-cover text with per-text customization
   - Estimated time: ~30 seconds per text × 2,452 = ~20 hours

5. **Volume bundling logic**
   - Very short texts (under ~20 pages): bundle into collected volumes by topic/section
   - Very large texts (over ~600 pages): split into multiple volumes
   - Maintain a mapping of T-number → volume(s)

### Time Estimate

- Design and build the batch pipeline: **2-3 weeks**
- Run full batch (glossaries + indices + PDFs + covers): **2-3 weeks**
- Debug and fix edge cases: **1-2 weeks**

### Cost

Primarily Max subscription time. The LaTeX compilation is local compute (free). AI-assisted glossary/index generation for all 2,993 texts could be done via Sonnet batch API (~$630) or in ~50-100 Max sessions over 2-3 weeks.

---

## Phase 3: Electronic Distribution (Free)

### Options

1. **Internet Archive (archive.org)**
   - Free, permanent hosting
   - Scholarly credibility
   - Full-text search
   - Bulk upload via their API or S3-like interface
   - Supports PDF, EPUB, and other formats
   - Already used by many Buddhist text projects

2. **GitHub Releases / GitHub Pages**
   - Free hosting via GitHub repository
   - Version-controlled (perfect for our re-run pipeline)
   - Each release tagged with the model version and date
   - Users can see diff between translation versions
   - Markdown source also available for remixing

3. **Dedicated website** (e.g., taisho-english.org or similar)
   - Static site generated from the translations
   - Full-text search
   - Side-by-side Chinese/English view
   - Hosting: ~$10-50/month (Netlify, Vercel, or basic VPS)
   - Domain: ~$12/year

### Recommended Approach

Use all three:
- **Internet Archive** as the permanent, canonical home for PDFs
- **GitHub** as the source repository (markdown + build pipeline)
- **Static website** as the user-friendly reading interface

### Time Estimate

- Internet Archive bulk upload: **1-2 days** (scripted)
- GitHub releases: **1 day** (scripted)
- Static website (basic): **1-2 weeks** to build
- Static website (polished): **1-2 months** if we want search, cross-references, etc.

### Cost

- Internet Archive: free
- GitHub: free
- Static site hosting: ~$50-200/year
- Domain name: ~$12/year

---

## Phase 4: Print-on-Demand via IngramSpark

### How IngramSpark Works

- No per-title setup fee (current pricing)
- Upload interior PDF + cover PDF + metadata per title
- They handle printing, fulfillment, and distribution
- Books appear on Amazon, Barnes & Noble, etc.
- Can set any list price (including near-cost for accessibility)
- Print cost per copy: ~$3-8 depending on page count

### At Scale: ~656 Volumes

IngramSpark supports bulk title setup via spreadsheet (ONIX feed). The workflow:

1. **Generate metadata spreadsheet** — title, author, ISBN, trim size, page count, price, description, categories, keywords
2. **Upload interior + cover PDFs** — can be scripted via their publisher portal
3. **ISBNs** — need one per volume. With ~656 volumes, a block of 1,000 ISBNs from Bowker ($1,500) provides coverage with margin. Alternatively, use IngramSpark's free ISBNs (but these show IngramSpark as imprint, not Open Canon Press).
4. **Pricing** — set at cost + $1-2 to cover IngramSpark's minimum margin. A 300-page book might list at ~$8-12.

### Volume Packaging

See "Volume Bundling and Splitting Plan" section below for full details. Estimated total: **~656 volumes**.

### Time Estimate

- ISBN acquisition: **1-2 weeks** (purchase + assignment)
- Metadata spreadsheet: **1-2 weeks** (scripted from catalog)
- Bulk upload to IngramSpark: **2-4 weeks** (their review process per title takes 1-3 days, done in batches)
- Total: **2-3 months** for the full catalog to be live

### Cost

- ISBNs: $1,500 (1,000-block from Bowker under Open Canon Press imprint)
- IngramSpark publisher account: free (or $49/year for the premium tier)
- No per-title fees
- No inventory risk (print-on-demand)
- **Total setup: ~$1,500-1,600**

---

## Phase 5: Reproducible Re-Run Pipeline

### The Key Idea

Every six months, re-translate the entire corpus using the latest AI model. Each generation improves. Version everything.

### Pipeline Architecture

```
full_catalog.json
    ↓
[1] translate_all.py          → translations/T{XXXX}_translation.md  (AI)
    ↓
[2] batch_glossary.py         → glossaries/glossary_T{XXXX}.md       (AI)
    ↓
[3] batch_index.py            → indices/index_terms_T{XXXX}.txt      (AI)
    ↓
[4] batch_interior.py         → pdfs/T{XXXX}_english.pdf             (LaTeX)
    ↓
[5] batch_covers.py           → covers/T{XXXX}_cover.pdf             (LaTeX)
    ↓
[6] batch_upload.py           → Internet Archive + IngramSpark        (API)
```

### Versioning

- Each run tagged with: model name, date, version number (e.g., `v3-opus4.6-2026-10`)
- Git tag for the full corpus at each release
- Internet Archive: upload as new edition (old editions remain available)
- IngramSpark: update interior PDF (no new ISBN needed for revisions)
- Website: show "translated with [model] on [date]" and link to previous versions

### What Improves Each Cycle

- Translation quality (better models)
- Glossary consistency (learn from previous runs)
- Index coverage (better term extraction)
- Formatting (pipeline improvements)
- Coverage (any newly available Chinese source texts)

### Re-Run Time and Cost

Each re-run after the pipeline is built:

- Opus batch+cache translation of all ~2,993 texts: 1-3 days, ~$2,500
- Sonnet batch glossary/index regen: 1-2 days, ~$630
- Max subscription for selective review: 1-2 months, $200-400
- PDF regeneration + upload: 3-5 weeks
- **Total per cycle: ~$3,400-3,800 and 2-3 months**

As models get faster and cheaper, each successive cycle should cost less. If Opus pricing drops another 50% (plausible within 1-2 years), a full API re-run would cost under $2,000 total.

---

## Cost Summary (Recommended Approach)

| Item | First Run | Each Re-Run |
|---|---|---|
| Opus 4.6 batch+cache (translation) | $2,500 | $2,500 |
| Max subscription (2-3 months review/revision) | $400-600 | $200-400 |
| Sonnet 4.6 batch (glossary/index) | $630 | $630 |
| ISBNs (1,000 block from Bowker) | $1,500 | — |
| IngramSpark account | $0-49/year | $0-49/year |
| Web hosting + domain | ~$60-200/year | ~$60-200/year |
| **Total** | **~$5,100-5,500** | **~$3,400-3,800** |

Using IngramSpark's free ISBNs instead of Bowker saves $1,500 (but ISBNs show IngramSpark as imprint, not Open Canon Press).

**A note on Max subscription costs vs. API costs:** Interactive use via Max (including overflow billing) is 3-4x more expensive per token than batch API because of conversation context accumulation, no batch discount, and no prompt caching. For the full corpus, interactive-only translation would cost ~$5,000-6,000 vs. ~$2,500 via batch (validated by POC at $0.008/KB). Building the batch automation pipeline pays for itself immediately.

## Timeline (Recommended)

| Phase | Duration | Start |
|---|---|---|
| 0. Build `translate_all.py` batch automation | 2 weeks | Now |
| 1. Batch-translate all ~1,768 texts (Opus) | 1-3 days | Month 1 |
| 2. Build batch PDF pipeline + bundling logic | 3-5 weeks | Month 1 (parallel) |
| 3. Quality review + revision via Max | 2-3 months | Month 1 (parallel) |
| 4. Generate all PDFs + covers | 2-3 weeks | Month 2 |
| 5. Electronic distribution | 1-2 weeks | Month 3 |
| 6. IngramSpark setup (batches of ~100 titles) | 2-3 months | Month 3 |
| 7. **First full release** | — | **Month 5-6** |
| 8. First re-run with improved model | — | Month 11-12 |

---

## Volume Bundling and Splitting Plan

### Principles

1. **Minimum volume size**: 250 pages (to justify a printed book)
2. **Target bundle size**: ~400 pages (comfortable reading length)
3. **Maximum volume size**: 1,200 pages (physical limit for POD 6×9 binding)
4. **Grouping**: by Taishō section (thematic), not by consecutive T-number
5. **Split texts**: titled "Volume 1 of N," "Volume 2 of N," etc. in subtitle
6. **Imprint**: Open Canon Press

### Size Distribution (all 2,993 texts)

| Category | Texts | % | Treatment |
|---|---|---|---|
| Under 50 pages | 2,136 | 71% | Bundle into collected volumes |
| 50-199 pages | 560 | 19% | Bundle (under 250pp) or standalone |
| 200-1,200 pages | 255 | 9% | Standalone volumes |
| Over 1,200 pages | 40 | 1% | Split into multiple volumes |

### Estimated Volumes by Taishō Section

| Section | T-numbers | Texts | Pages | Bundle vols | Standalone | Split vols | **Total** |
|---|---|---|---|---|---|---|---|
| Āgama (阿含部) | T0001-T0151 | 151 | 9,927 | 6 | 17 | 8 | **31** |
| Jātaka (本緣部) | T0152-T0219 | 68 | 3,476 | 4 | 6 | 2 | **12** |
| Prajñāpāramitā (般若部) | T0220-T0261 | 42 | 9,159 | 2 | 5 | 14 | **21** |
| Lotus (法華部) | T0262-T0277 | 16 | 951 | 2 | 1 | 0 | **3** |
| Avataṃsaka (華嚴部) | T0278-T0309 | 32 | 3,685 | 3 | 4 | 4 | **11** |
| Ratnakūṭa (寶積部) | T0310-T0373 | 64 | 4,073 | 4 | 7 | 2 | **13** |
| Nirvāṇa (涅槃部) | T0374-T0396 | 23 | 2,041 | 2 | 3 | 2 | **7** |
| Great Assembly (大集部) | T0397-T0424 | 28 | 2,397 | 3 | 2 | 2 | **7** |
| Sūtra Collection (經集部) | T0425-T0847 | 433 | 14,015 | 18 | 12 | 7 | **37** |
| Esoteric (密教部) | T0848-T1420 | 573 | 10,703 | 18 | 8 | 4 | **30** |
| Vinaya (律部) | T1421-T1504 | 84 | 13,143 | 4 | 10 | 16 | **30** |
| Abhidharma (釋經論部) | T1505-T1535 | 31 | 6,629 | 2 | 5 | 8 | **15** |
| Mādhyamaka/Yogācāra (毘曇部) | T1536-T1578 | 28 | 14,716 | 2 | 4 | 26 | **32** |
| Yogācāra (瑜伽部) | T1579-T1627 | 49 | 7,606 | 3 | 8 | 14 | **25** |
| Logic (論集部) | T1628-T1692 | 65 | 2,668 | 5 | 3 | 0 | **8** |
| Chinese Commentary (經疏-諸宗) | T1693-T2025 | 343 | 65,607 | 41 | 48 | 54 | **143** |
| History/Biography (史傳部) | T2026-T2120 | 95 | 16,419 | 7 | 8 | 15 | **30** |
| Encyclopedia (事彙部) | T2121-T2136 | 16 | 8,424 | 1 | 3 | 8 | **12** |
| Siddham/Phonology (外教-聲明) | T2137-T2144 | 8 | 459 | 1 | 0 | 0 | **1** |
| Catalogs (目錄部) | T2145-T2184 | 30 | 4,860 | 3 | 4 | 2 | **9** |
| Japanese/Supplementary (日本撰述+續藏) | T2185+ | 733 | 79,706 | 97 | 47 | 42 | **186** |
| **Totals** | | **2,993** | **280,665** | **227** | **255** | **174** | **~656** |

### Bundle Naming Convention

Bundled volumes are titled by section and sequence number:

- *Collected Āgama Sūtras, Volume 1* (containing T0001-T0026, etc.)
- *Collected Esoteric Texts, Volume 3* (containing T0912-T0945, etc.)
- *Collected Japanese Buddhist Writings, Volume 12* (containing T2250-T2268, etc.)

Each bundle's table of contents lists the individual texts with their Taishō numbers.

### Split Naming Convention

Texts over 1,200 pages are split at natural fascicle boundaries (~500 pages per volume):

- *Mahāprajñāpāramitā Sūtra (T0220), Volume 1 of 10*
- *Abhidharma-mahāvibhāṣā (T1545), Volume 1 of 8*

The largest splits:

| Text | Pages | Volumes |
|---|---|---|
| T0220 Mahāprajñāpāramitā Sūtra | ~4,642 | 10 |
| T1545 Abhidharma-mahāvibhāṣā | ~3,879 | 8 |
| T1736 Huayan Sūtra Commentary | ~2,974 | 6 |
| T1509 Mahāprajñāpāramitā-śāstra | ~2,960 | 6 |
| T1579 Yogācārabhūmi | ~2,498 | 5 |

### ISBN Requirements

With ~656 volumes, we need approximately 700-750 ISBNs (some buffer for corrections/reprints). Bowker pricing:
- 1,000 ISBNs: $1,500 (sufficient with margin)
- Under the **Open Canon Press** imprint

---

## Open Questions

1. ~~**Bundling strategy**~~: **RESOLVED.** Bundle short texts by Taishō section (thematic grouping). Target ~400 pages per bundle, minimum 250. Texts 200-1,200 pages stand alone. See "Volume Bundling and Splitting Plan" above. Estimated ~227 bundled volumes from 2,696 short texts.

2. ~~**Multi-volume naming**~~: **RESOLVED.** Split texts use "Volume X of N" in subtitle. E.g., *Mahāprajñāpāramitā Sūtra (T0220), Volume 1 of 10*. Split at natural fascicle boundaries, targeting ~500 pages per volume. 40 texts need splitting into ~174 volumes.

3. ~~**Imprint name**~~: **RESOLVED.** Open Canon Press. ISBNs via Bowker (1,000 block for $1,500).

4. **EPUB/Kindle**: Generate EPUB alongside PDF for e-reader distribution? Pandoc can do this from the same markdown source.

5. **Quality tiers**: Release all texts simultaneously, or stagger by quality (shorter well-checked texts first, massive texts later)?

6. **Community review**: Open the translations to scholarly review/correction between cycles?

7. **Existing translations**: Some Taishō texts already have published English translations (BDK, Numata, individual scholars). Include ours anyway for completeness, or skip those?

8. ~~**Chinese source gaps**~~: **RESOLVED.** All 2,993 catalog entries now have Chinese source files (100% coverage). The apparent gap was 154 a/b variant recensions whose suffixed T-numbers weren't handled by the original extraction script. All extracted from CBETA XML on 2026-04-05.

9. **Japanese kanbun handling**: The 541 texts in volumes 56-84 are classical Chinese written by Japanese authors. Some may have Japanese syntactic patterns (kanbun). Do we need a variant prompt or can we use the same translation pipeline?

10. ~~**Japanese text metadata**~~: **RESOLVED.** The SAT catalog (541 entries) was merged into `full_catalog.json` on 2026-04-05. Total catalog: 2,993 entries.

11. ~~**Supplementary volumes**~~: **RESOLVED.** Volumes 86-97 are the 圖像部 (Pictorial/Iconographic section), consisting of drawings of buddhas, bodhisattvas, maṇḍalas, and ritual implements. Not translatable text. Volumes 98-100 are bibliographic indices. Our catalog (vols 1-85) covers all translatable text in the Taishō, including the 192 Shōwa-era supplementary texts in vol. 85.
