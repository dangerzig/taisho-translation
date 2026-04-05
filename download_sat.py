#!/usr/bin/env python3
"""
Download Taishō texts from volumes 56-84 from the SAT Daizōkyō Text Database.

These volumes contain Japanese Buddhist commentaries (續經疏部, 續律疏部,
續論疏部, 續諸宗部, 悉曇部, 古逸部, 疑似部) that are not in the CBETA
XML corpus we already have.

SAT API endpoints used (all under https://21dzk.l.u-tokyo.ac.jp/SAT/):
  - master30.php (2018): catalog tree with all T-numbers per volume
  - satdb2015.php?mode=scrtit&num1=NNNN_: fascicle start pages for a text
  - satdb2015.php?mode=detail&useid=NNNN_,VV,PPPP&mode3=1&nohd=3: page index (first/last page)
  - satdb2015.php?mode=detail&useid=NNNN_,VV,PPPP&mode3=3&nohd=3: title and author info
  - satdb2015.php?mode=detail&useid=NNNN_,VV,PPPP&ob=1&mode2=2: text content (paginated)

Output format matches existing chinese/T{NNNN}.txt files:
  # Title
  # Taishō T{NNNN}, N fascicle(s)
  # Author/Translator: ...
  # Characters: N,NNN
  (blank line)
  (text content, one paragraph per line)
"""

import json
import logging
import os
import re
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests

# Configuration
BASE_URL = "https://21dzk.l.u-tokyo.ac.jp/SAT"
SAT_2018_URL = f"{BASE_URL}2018/master30.php"
SAT_2015_URL = f"{BASE_URL}/satdb2015.php"

OUTPUT_DIR = Path.home() / "taisho-translation" / "chinese"
CACHE_DIR = Path.home() / "taisho-translation" / "sat_html"
CATALOG_CACHE = Path.home() / "taisho-translation" / "sat_catalog_v56_84.json"
LOG_DIR = Path.home() / "taisho-translation" / "logs"

MIN_VOLUMES = 56
MAX_VOLUMES = 84

# Rate limiting: seconds between requests
REQUEST_DELAY = 1.5
# Timeout for HTTP requests
REQUEST_TIMEOUT = 60

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_DIR / "download_sat.log"),
    ],
)
log = logging.getLogger(__name__)


def get_session():
    """Create a requests session with appropriate headers."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; research use) SAT-downloader/1.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,ja;q=0.3",
    })
    return s


def polite_get(session, url, desc="", max_retries=3):
    """Make an HTTP GET with rate limiting, retries, and error handling."""
    for attempt in range(max_retries):
        time.sleep(REQUEST_DELAY)
        try:
            resp = session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            resp.encoding = "utf-8"
            return resp.text
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait = REQUEST_DELAY * (attempt + 2)
                log.warning(
                    "Retry %d/%d for %s: %s (waiting %.1fs)",
                    attempt + 1, max_retries, desc, e, wait,
                )
                time.sleep(wait)
            else:
                log.error("Failed after %d attempts for %s: %s", max_retries, desc, e)
                return None


# ---------------------------------------------------------------------------
# Step 1: Build catalog of texts in volumes 56-84
# ---------------------------------------------------------------------------

def build_catalog(session):
    """
    Parse the SAT 2018 master page to extract all text entries for
    volumes 56-84. Returns a list of dicts with keys:
      t_number, volume, title, sat_id
    """
    if CATALOG_CACHE.exists():
        log.info("Loading cached catalog from %s", CATALOG_CACHE)
        with open(CATALOG_CACHE) as f:
            return json.load(f)

    log.info("Downloading SAT 2018 master catalog...")
    html = polite_get(session, SAT_2018_URL, "master catalog")
    if not html:
        log.error("Failed to download master catalog")
        sys.exit(1)

    # The catalog tree is embedded as JavaScript with escaped quotes.
    # Pattern: data-n=\"NNNN_VV\">TNNNN title</span>
    pattern = r'data-n=\\"(\d+[A-Za-z]?)_(\d+)\\">T(\d+[A-Za-z]?)\s+([^<]+)</span>'
    entries = re.findall(pattern, html)

    if not entries:
        # Try double-escaped pattern (varies by server response)
        pattern2 = r'data-n=\\\\\"(\d+[A-Za-z]?)_(\d+)\\\\\">T(\d+[A-Za-z]?)\s+([^<]+)</span>'
        entries = re.findall(pattern2, html)

    log.info("Found %d total entries in SAT catalog", len(entries))

    catalog = []
    for sat_id, vol_str, tnum, title in entries:
        vol = int(vol_str)
        if MIN_VOLUMES <= vol <= MAX_VOLUMES:
            catalog.append({
                "t_number": f"T{tnum}",
                "volume": vol,
                "title": title.strip(),
                "sat_id": sat_id,
            })

    log.info("Found %d texts in volumes %d-%d", len(catalog), MIN_VOLUMES, MAX_VOLUMES)

    # Save cache
    CATALOG_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with open(CATALOG_CACHE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    return catalog


# ---------------------------------------------------------------------------
# Step 2: Get metadata for each text (fascicles, page range, author)
# ---------------------------------------------------------------------------

def get_fascicle_starts(session, sat_id):
    """
    Get fascicle start page references for a text via the scrtit endpoint.
    Returns list of (page_ref, fascicle_title) tuples.
    """
    url = f"{SAT_2015_URL}?mode=scrtit&num1={sat_id}_"
    html = polite_get(session, url, f"scrtit {sat_id}")
    if not html:
        return []

    # Pattern: <span class="scrln" n="0001a03">Title</span>
    pattern = r'class="scrln"[^>]*\bn="(\d{4}[abc]\d{2})"[^>]*>([^<]+)</span>'
    matches = re.findall(pattern, html)
    return matches


def get_page_range(session, sat_id, volume, start_page):
    """
    Get the first and last page numbers for a text via the page index endpoint.
    Returns (first_page, last_page) as 4-digit strings, or (None, None).
    """
    url = (
        f"{SAT_2015_URL}?mode=detail"
        f"&useid={sat_id}_,{volume},{start_page}"
        f"&mode3=1&nohd=3&mode4="
    )
    html = polite_get(session, url, f"page index {sat_id}")
    if not html:
        return None, None

    # First page: the span.pindex whose child is <img src="first.gif">
    # HTML: <span class="pindex" n="2185_,56,0001&nonum=&kaeri="><img src="first.gif" ...
    first_match = re.search(
        r'n="\d+_,\d+,(\d+)[^"]*"[^>]*><img[^>]*first\.gif', html
    )
    # Last page: the span.pindex whose child is <img src="last.gif">
    last_match = re.search(
        r'n="\d+_,\d+,(\d+)[^"]*"[^>]*><img[^>]*last\.gif', html
    )

    first = first_match.group(1) if first_match else None
    last = last_match.group(1) if last_match else None
    return first, last


def get_title_author(session, sat_id, volume, start_page):
    """
    Get title and author from the mode3=3 endpoint.
    Returns (title, author_string).
    """
    url = (
        f"{SAT_2015_URL}?mode=detail"
        f"&useid={sat_id}_,{volume},{start_page}"
        f"&mode3=3&nohd=3&mode4="
    )
    html = polite_get(session, url, f"title {sat_id}")
    if not html:
        return None, None

    # Title: text before (No. NNNN
    title_match = re.search(r'<div>(.+?)\s*\(No\.', html)
    title = title_match.group(1).strip() if title_match else None

    # Author: extract the section between the number link and ") in Vol."
    # Format: <a href="...">2185</a>  <a href="...">聖徳太子</a>撰 ) in Vol.
    author_section = re.search(
        r'</a>\s+(.+?)\s*\)\s*in\s+Vol\.',
        html[html.find("No."):] if "No." in html else html,
    )
    if author_section:
        author_html = author_section.group(1).strip()
        # Extract author names from <a> tags and roles from text after </a>
        # e.g., <a href="...">聖徳太子</a>撰
        parts = re.findall(r'>([^<]+)</a>([^<]*)', author_html)
        if parts:
            author = "".join(f"{name}{role.strip()}" for name, role in parts)
        else:
            # Strip any remaining HTML tags
            author = re.sub(r'<[^>]+>', '', author_html).strip()
    else:
        author = ""

    return title, author


# ---------------------------------------------------------------------------
# Step 3: Fetch and parse text content
# ---------------------------------------------------------------------------

def fetch_text_content(session, sat_id, volume, first_page, last_page):
    """
    Fetch all text content for a text, paginating through the SAT API.
    Returns a dict mapping line references (e.g., '0001a03') to text strings.
    """
    cache_file = CACHE_DIR / f"T{sat_id}_v{volume}.json"
    if cache_file.exists():
        log.info("  Loading cached content for T%s", sat_id)
        with open(cache_file) as f:
            return json.load(f)

    first_num = int(first_page)
    last_num = int(last_page)

    all_lines = {}  # line_ref -> text
    current_page = first_page

    while int(current_page) <= last_num:
        url = (
            f"{SAT_2015_URL}?mode=detail"
            f"&useid={sat_id}_,{volume},{current_page}"
            f"&ob=1&mode2=2"
        )

        # Check for cached HTML
        html_cache = CACHE_DIR / f"T{sat_id}_v{volume}_p{current_page}.html"
        if html_cache.exists():
            with open(html_cache, encoding="utf-8") as f:
                html = f.read()
        else:
            html = polite_get(session, url, f"content T{sat_id} p{current_page}")
            if not html:
                log.warning("  Failed to fetch page %s for T%s", current_page, sat_id)
                break
            # Cache the HTML
            html_cache.parent.mkdir(parents=True, exist_ok=True)
            with open(html_cache, "w", encoding="utf-8") as f:
                f.write(html)

        # Parse lines from HTML
        # Each line: <a name="PPPPcLL" class="al"><span class="tx">...chars...</span></a>
        line_pattern = (
            r'<a\s+name="(\d{4}[abc]\d{2})"\s+class="al">'
            r'<span class="tx">(.*?)</span></a>'
        )
        matches = re.findall(line_pattern, html, re.DOTALL)

        if not matches:
            log.warning("  No lines found for T%s page %s", sat_id, current_page)
            break

        # Find the last page returned in this batch
        batch_last_page = "0000"
        new_lines = 0
        for line_ref, content_html in matches:
            page_num = line_ref[:4]
            if int(page_num) > last_num:
                # Past the end of this text
                continue
            if line_ref not in all_lines:
                # Extract text from <span class="ec"> elements
                chars = re.findall(
                    r'<span class="ec"[^>]*>(.*?)</span>', content_html
                )
                text = "".join(chars)
                all_lines[line_ref] = text
                new_lines += 1
            if page_num > batch_last_page:
                batch_last_page = page_num

        log.info(
            "  Fetched pages %s-%s (%d new lines, %d total)",
            current_page, batch_last_page, new_lines, len(all_lines),
        )

        if new_lines == 0:
            # No new content; we've reached the end or hit an overlap loop
            break

        # Move to the next page after the batch
        next_page_num = int(batch_last_page) + 1
        if next_page_num > last_num:
            break
        current_page = f"{next_page_num:04d}"

    # Cache the parsed content
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(all_lines, f, ensure_ascii=False, indent=2)

    return all_lines


# ---------------------------------------------------------------------------
# Step 4: Format and save output
# ---------------------------------------------------------------------------

def count_cjk_chars(text):
    """Count CJK characters in a string."""
    count = 0
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or       # CJK Unified Ideographs
            0x3400 <= cp <= 0x4DBF or       # CJK Unified Extension A
            0x20000 <= cp <= 0x2A6DF or     # CJK Unified Extension B
            0xF900 <= cp <= 0xFAFF or       # CJK Compatibility Ideographs
            0x2F800 <= cp <= 0x2FA1F):      # CJK Compatibility Supplement
            count += 1
    return count


def _is_header_line(text, t_number):
    """Check if a line is a catalog/header line that should be excluded."""
    stripped = text.strip().lstrip("\u3000")
    if not stripped:
        return False
    # "No. 2185 [cf. No. 353]" or "No. 2185"
    if re.match(r'No\.\s*\d+', stripped):
        return True
    # Lines that are purely ASCII/Latin (page numbers, volume markers)
    if all(ord(c) < 0x2000 for c in stripped):
        return True
    return False


def format_and_save(entry, fascicles, lines, title, author):
    """
    Format the text content and save to a .txt file matching our existing format.
    """
    t_number = entry["t_number"]
    volume = entry["volume"]
    num_fascicles = len(fascicles) if fascicles else 1

    # Sort lines by reference
    sorted_refs = sorted(lines.keys())
    if not sorted_refs:
        log.warning("No text content for %s; skipping", t_number)
        return False

    # Use SAT title if we didn't get one from the API
    if not title:
        title = entry["title"]

    # Build the text body with fascicle headers
    body_parts = []
    current_para = []
    fas_idx = 0
    fas_header_written = False

    for ref in sorted_refs:
        text = lines[ref].strip()

        # Skip catalog header lines (e.g., "No. 2185 [cf. No. 353]")
        if _is_header_line(text, t_number):
            continue

        # Check if we need to write a fascicle header
        if fascicles:
            # Check for new fascicle boundary
            while fas_idx < len(fascicles) - 1 and ref >= fascicles[fas_idx + 1][0]:
                if current_para:
                    body_parts.append("".join(current_para))
                    current_para = []
                fas_idx += 1
                fas_title = fascicles[fas_idx][1]
                body_parts.append("")
                body_parts.append("=" * 40)
                body_parts.append(f"Fascicle {fas_idx + 1:03d}: {fas_title}")
                body_parts.append("=" * 40)
                body_parts.append("")
                fas_header_written = True

            # First fascicle header
            if not fas_header_written:
                fas_title = fascicles[0][1]
                body_parts.append("")
                body_parts.append("=" * 40)
                body_parts.append(f"Fascicle 001: {fas_title}")
                body_parts.append("=" * 40)
                body_parts.append("")
                fas_header_written = True

        if not text:
            # Empty line = paragraph break
            if current_para:
                body_parts.append("".join(current_para))
                current_para = []
        else:
            text = text.lstrip("\u3000")
            current_para.append(text)

    if current_para:
        body_parts.append("".join(current_para))

    body = "\n".join(body_parts)

    # Count CJK characters
    cjk_count = count_cjk_chars(body)

    # Format author line
    if author:
        author_line = f"# Author: {author}"
    else:
        author_line = "# Author: (unknown)"

    # Build header
    header = (
        f"# {title}\n"
        f"# Taishō {t_number}, {num_fascicles} fascicle(s)\n"
        f"{author_line}\n"
        f"# CJK characters: {cjk_count:,}\n"
        f"# Source: SAT Daizōkyō Text Database, Vol. {volume}\n"
    )

    # Write output
    output_file = OUTPUT_DIR / f"{t_number}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(header)
        f.write("\n\n")
        f.write(body)
        f.write("\n")

    log.info(
        "Saved %s: %s (%d fascicles, %s CJK chars)",
        t_number, title[:30], num_fascicles, f"{cjk_count:,}",
    )
    return True


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_text(session, entry):
    """Process a single text: fetch metadata, content, and save."""
    t_number = entry["t_number"]
    sat_id = entry["sat_id"]
    volume = entry["volume"]

    # Check if already downloaded
    output_file = OUTPUT_DIR / f"{t_number}.txt"
    if output_file.exists():
        log.info("Skipping %s (already exists)", t_number)
        return True

    log.info("Processing %s: %s (vol. %d)", t_number, entry["title"][:40], volume)

    # Step 1: Get fascicle list
    fascicles = get_fascicle_starts(session, sat_id)
    if not fascicles:
        log.warning("  No fascicles found for %s; trying direct fetch", t_number)
        # Use the catalog title as a fallback
        fascicles = []

    log.info("  %d fascicle(s) found", len(fascicles))

    # Step 2: Get first page from fascicle list or try page 0001
    if fascicles:
        first_fascicle_page = fascicles[0][0][:4]  # e.g., "0001"
    else:
        first_fascicle_page = "0001"

    # Step 3: Get page range
    first_page, last_page = get_page_range(session, sat_id, volume, first_fascicle_page)
    if not first_page or not last_page:
        log.error("  Could not determine page range for %s", t_number)
        return False

    log.info("  Page range: %s-%s", first_page, last_page)

    # Step 4: Get title and author from SAT
    title, author = get_title_author(session, sat_id, volume, first_fascicle_page)
    log.info("  Title: %s, Author: %s", title, author or "(unknown)")

    # Step 5: Fetch all text content
    lines = fetch_text_content(session, sat_id, volume, first_page, last_page)
    if not lines:
        log.error("  No text content retrieved for %s", t_number)
        return False

    log.info("  Retrieved %d lines of text", len(lines))

    # Step 6: Format and save
    return format_and_save(entry, fascicles, lines, title, author)


def main():
    # Ensure directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    session = get_session()

    # Build catalog
    catalog = build_catalog(session)
    if not catalog:
        log.error("No texts found in catalog")
        sys.exit(1)

    # Sort by volume and T-number for orderly processing
    catalog.sort(key=lambda x: (x["volume"], x["t_number"]))

    # Count already downloaded
    already_done = sum(
        1 for entry in catalog
        if (OUTPUT_DIR / f"{entry['t_number']}.txt").exists()
    )
    log.info(
        "Catalog: %d texts total, %d already downloaded, %d remaining",
        len(catalog), already_done, len(catalog) - already_done,
    )

    # Process each text
    success = 0
    failed = 0
    skipped = 0

    for i, entry in enumerate(catalog):
        t_number = entry["t_number"]
        output_file = OUTPUT_DIR / f"{t_number}.txt"

        if output_file.exists():
            skipped += 1
            continue

        try:
            if process_text(session, entry):
                success += 1
            else:
                failed += 1
        except Exception as e:
            log.error("Exception processing %s: %s", t_number, e, exc_info=True)
            failed += 1

        # Progress report every 10 texts
        total_done = skipped + success + failed
        if (success + failed) % 10 == 0 and (success + failed) > 0:
            log.info(
                "Progress: %d/%d done (%d success, %d failed, %d skipped)",
                total_done, len(catalog), success, failed, skipped,
            )

    log.info(
        "Complete: %d success, %d failed, %d skipped (of %d total)",
        success, failed, skipped, len(catalog),
    )


if __name__ == "__main__":
    main()
