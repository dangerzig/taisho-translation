#!/bin/bash
# Batch translation of Taishō texts using claude -p CLI.
# Pure bash to avoid Python subprocess TTY/pipe issues.
#
# Usage:
#   ./batch_translate.sh              # translate all untranslated texts
#   ./batch_translate.sh --hours 10   # with time limit
#   ./batch_translate.sh --dry-run    # list what would be translated

set -euo pipefail

# Ensure PATH includes homebrew (claude CLI lives here)
export PATH="/opt/homebrew/bin:$PATH"

# Configuration
BASE_DIR="$HOME/taisho-translation-sample"
CHINESE_DIR="$BASE_DIR/chinese"
TRANS_DIR="$BASE_DIR/translations"
LOG_DIR="$BASE_DIR/logs"
CATALOG="$BASE_DIR/full_catalog.json"

CHUNK_SIZE=5000   # CJK chars per chunk
MAX_JUAN=30       # skip texts larger than this
HOURS=10          # default time limit
DRY_RUN=false
TIMEOUT=600       # 10 min per chunk

# Strip env vars that interfere with Max plan auth
unset CLAUDECODE 2>/dev/null || true
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --hours) HOURS="$2"; shift 2 ;;
        --dry-run) DRY_RUN=true; shift ;;
        --max-juan) MAX_JUAN="$2"; shift 2 ;;
        --timeout) TIMEOUT="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOGFILE="$LOG_DIR/batch_${TIMESTAMP}.log"
mkdir -p "$CHINESE_DIR" "$TRANS_DIR" "$LOG_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOGFILE"
}

log "INFO  Batch translation starting. Log: $LOGFILE"
log "INFO  Time limit: ${HOURS} hours, max juan: ${MAX_JUAN}"

DEADLINE=$(( $(date +%s) + $(echo "$HOURS * 3600" | bc | cut -d. -f1) ))

# Build list of texts to translate, sorted by size (small first)
# Uses jq to parse the catalog
if ! command -v jq &>/dev/null; then
    log "ERROR jq not found. Install with: brew install jq"
    exit 1
fi

# Get texts sorted by juan count (small first), filtered by max_juan
TEXTS=$(jq -r --argjson maxj "$MAX_JUAN" '
    [.[] | select(.juan <= $maxj)]
    | sort_by(.juan)
    | .[]
    | [.t_number, .title_zh, (.juan | tostring), .translator, .xml_pattern, .volume] | @tsv
' "$CATALOG")

TOTAL=$(echo "$TEXTS" | wc -l | tr -d ' ')
ALREADY=0
TODO_COUNT=0
COMPLETED=0
FAILED=0

# Count already translated
while IFS=$'\t' read -r t_num title juan translator xml_pattern volume; do
    if [[ -f "$TRANS_DIR/${t_num}_translation.md" ]]; then
        ((ALREADY++)) || true
    else
        ((TODO_COUNT++)) || true
    fi
done <<< "$TEXTS"

log "INFO  Catalog: $TOTAL texts (filtered by max $MAX_JUAN juan)"
log "INFO  Already translated: $ALREADY"
log "INFO  Remaining: $TODO_COUNT texts"

if $DRY_RUN; then
    echo ""
    echo "Would translate $TODO_COUNT texts:"
    while IFS=$'\t' read -r t_num title juan translator xml_pattern volume; do
        [[ -f "$TRANS_DIR/${t_num}_translation.md" ]] && continue
        printf "  %-8s %-30s %3s juan\n" "$t_num" "${title:0:30}" "$juan"
    done <<< "$TEXTS" | head -50
    exit 0
fi

# Translation prompt template
make_prompt() {
    local title="$1" t_number="$2" chunk_info="$3" chinese_text="$4"
    cat <<PROMPT
You are translating a Chinese Buddhist text from the Taishō Tripiṭaka into English.

Title: ${title}
Taishō Number: ${t_number}
${chunk_info}

Rules (follow exactly):
1. Output ONLY the English translation. No preamble, no commentary, no "Here is the translation".
2. Use standard scholarly Buddhist terminology.
3. Transliterate Sanskrit/Pali proper names in IAST (e.g., Śāriputra, Ānanda, nirvāṇa).
4. Preserve verse structure: translate verses as indented lines with ">" prefix.
5. Mark dhāraṇī passages with [Dhāraṇī] and transliterate rather than translate.
6. For fascicle headers, output "## Fascicle N" on its own line.
7. For section headings, translate and output as "### Heading".
8. Maintain the dignity and literary quality appropriate to sacred scripture.
9. Translate the COMPLETE text below. Do not summarize or abbreviate.

Chinese text to translate:

${chinese_text}
PROMPT
}

# Count CJK characters in a string
count_cjk() {
    echo -n "$1" | perl -CS -ne 'print' | perl -CS -ne '
        my $count = 0;
        while (/[\x{4E00}-\x{9FFF}\x{3400}-\x{4DBF}]/g) { $count++; }
        print $count;
    '
}

# Split text into chunks at paragraph boundaries
# Outputs chunk files as /tmp/chunk_NNNN.txt
split_chunks() {
    local text="$1" max_chars="$2" prefix="$3"
    python3 -c "
import re, sys

text = open('$prefix_body.txt', encoding='utf-8').read()
max_chars = $max_chars

def count_cjk(t):
    return len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', t))

paragraphs = text.split('\n\n')
chunks = []
current = []
current_count = 0

for para in paragraphs:
    pc = count_cjk(para)
    if pc > max_chars:
        if current:
            chunks.append('\n\n'.join(current))
            current, current_count = [], 0
        sentences = re.split(r'(?<=[。！？])', para)
        sent_buf, sent_count = [], 0
        for sent in sentences:
            sc = count_cjk(sent)
            if sent_count + sc > max_chars and sent_buf:
                chunks.append(''.join(sent_buf))
                sent_buf, sent_count = [sent], sc
            else:
                sent_buf.append(sent)
                sent_count += sc
        if sent_buf:
            chunks.append(''.join(sent_buf))
        continue
    if current_count + pc > max_chars and current:
        chunks.append('\n\n'.join(current))
        current, current_count = [para], pc
    else:
        current.append(para)
        current_count += pc

if current:
    chunks.append('\n\n'.join(current))

for i, chunk in enumerate(chunks):
    with open(f'${prefix}_chunk_{i:04d}.txt', 'w', encoding='utf-8') as f:
        f.write(chunk)
print(len(chunks))
"
}

# Extract Chinese source using existing Python extraction
extract_chinese() {
    local t_num="$1" xml_pattern="$2" title="$3" translator="$4" juan="$5"
    local out_path="$CHINESE_DIR/${t_num}.txt"

    if [[ -f "$out_path" ]]; then
        echo "$out_path"
        return 0
    fi

    # Use the existing Python extraction
    python3 -c "
import sys
sys.path.insert(0, '$BASE_DIR')
from extract_chinese import build_char_map, extract_text, blocks_to_text
from pathlib import Path
import re

xml_base = Path.home() / 'taisho-canon' / 'xml' / 'T'
pattern = '$xml_pattern'
parts = pattern.split('/')
vol_dir = xml_base / parts[0]
xml_files = sorted(vol_dir.glob(parts[1]))
if not xml_files:
    sys.exit(1)

char_map = build_char_map(xml_files)
blocks = extract_text(xml_files, char_map)
readable = blocks_to_text(blocks)
char_count = len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', readable))
if char_count == 0:
    sys.exit(1)

header = (
    '# $title\n'
    '# Taishō $t_num, $juan fascicle(s)\n'
    '# Translator: $translator\n'
    f'# Characters: {char_count:,}\n\n'
)
Path('$out_path').write_text(header + readable, encoding='utf-8')
print(char_count)
" 2>/dev/null

    if [[ -f "$out_path" ]]; then
        echo "$out_path"
        return 0
    fi
    return 1
}

# Translate a single chunk with retry
translate_chunk() {
    local prompt_file="$1" output_file="$2"
    local attempt rc

    for attempt in 1 2; do
        # Run claude synchronously; no timeout to avoid TTY issues
        claude -p --output-format text --model sonnet --no-session-persistence < "$prompt_file" > "$output_file" 2>"${output_file}.err"
        rc=$?

        if [[ $rc -eq 0 ]] && [[ -s "$output_file" ]]; then
            rm -f "${output_file}.err"
            return 0
        fi

        local err_msg=""
        [[ -s "${output_file}.err" ]] && err_msg=$(head -1 "${output_file}.err")

        if [[ $attempt -eq 1 ]]; then
            log "WARN  Chunk attempt 1 failed (rc=$rc) ${err_msg}. Retrying in 10s..."
            sleep 10
        else
            log "ERROR Chunk attempt 2 failed (rc=$rc) ${err_msg}"
        fi
        rm -f "${output_file}.err"
    done
    return 1
}

# Main translation loop
while IFS=$'\t' read -r t_num title juan translator xml_pattern volume; do
    # Check time limit
    if [[ $(date +%s) -gt $DEADLINE ]]; then
        log "INFO  Time limit reached. Stopping."
        break
    fi

    # Skip already translated
    [[ -f "$TRANS_DIR/${t_num}_translation.md" ]] && continue

    text_start=$(date +%s)
    log "INFO  === $t_num: $title ($juan juan) ==="

    # Extract Chinese source
    chinese_path=$(extract_chinese "$t_num" "$xml_pattern" "$title" "$translator" "$juan" 2>/dev/null) || {
        log "ERROR $t_num: extraction failed"
        ((FAILED++)) || true
        continue
    }

    # Get the body (skip header lines starting with #)
    TMPDIR=$(mktemp -d)
    grep -v '^#' "$chinese_path" | sed '/^$/N;/^\n$/d' > "$TMPDIR/body.txt"

    # Count chars
    char_count=$(python3 -c "
import re
text = open('$TMPDIR/body.txt', encoding='utf-8').read()
print(len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', text)))
")

    if [[ "$char_count" -eq 0 ]]; then
        log "WARN  $t_num: no content to translate"
        rm -rf "$TMPDIR"
        ((FAILED++)) || true
        continue
    fi

    # Split into chunks using Python helper
    n_chunks=$(python3 -c "
import re

text = open('$TMPDIR/body.txt', encoding='utf-8').read()
max_chars = $CHUNK_SIZE

def count_cjk(t):
    return len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', t))

paragraphs = text.split('\n\n')
chunks = []
current = []
current_count = 0

for para in paragraphs:
    pc = count_cjk(para)
    if pc > max_chars:
        if current:
            chunks.append('\n\n'.join(current))
            current, current_count = [], 0
        sentences = re.split(r'(?<=[。！？])', para)
        sent_buf, sent_count = [], 0
        for sent in sentences:
            sc = count_cjk(sent)
            if sent_count + sc > max_chars and sent_buf:
                chunks.append(''.join(sent_buf))
                sent_buf, sent_count = [sent], sc
            else:
                sent_buf.append(sent)
                sent_count += sc
        if sent_buf:
            chunks.append(''.join(sent_buf))
        continue
    if current_count + pc > max_chars and current:
        chunks.append('\n\n'.join(current))
        current, current_count = [para], pc
    else:
        current.append(para)
        current_count += pc

if current:
    chunks.append('\n\n'.join(current))

for i, chunk in enumerate(chunks):
    with open(f'$TMPDIR/chunk_{i:04d}.txt', 'w', encoding='utf-8') as f:
        f.write(chunk)
print(len(chunks))
")

    log "INFO  $t_num: $char_count chars, $n_chunks chunk(s)"

    # Translate each chunk
    all_ok=true
    for i in $(seq 0 $((n_chunks - 1))); do
        chunk_file="$TMPDIR/chunk_$(printf '%04d' $i).txt"
        prompt_file="$TMPDIR/prompt_$(printf '%04d' $i).txt"
        output_file="$TMPDIR/output_$(printf '%04d' $i).txt"

        chunk_chars=$(python3 -c "
import re
text = open('$chunk_file', encoding='utf-8').read()
print(len(re.findall(r'[\u4E00-\u9FFF\u3400-\u4DBF]', text)))
")

        chunk_info=""
        if [[ $n_chunks -gt 1 ]]; then
            chunk_info="Part $((i+1)) of ${n_chunks}. Translate this portion only."
        fi

        chinese_text=$(cat "$chunk_file")
        make_prompt "$title" "$t_num" "$chunk_info" "$chinese_text" > "$prompt_file"

        log "INFO    chunk $((i+1))/$n_chunks ($chunk_chars chars)..."
        chunk_start=$(date +%s)

        if translate_chunk "$prompt_file" "$output_file"; then
            chunk_elapsed=$(( $(date +%s) - chunk_start ))
            log "INFO    chunk $((i+1))/$n_chunks done (${chunk_elapsed}s)"
        else
            log "ERROR   chunk $((i+1))/$n_chunks FAILED"
            echo "[TRANSLATION ERROR in chunk $((i+1))]" > "$output_file"
            all_ok=false
        fi

        # Brief pause between chunks
        [[ $i -lt $((n_chunks - 1)) ]] && sleep 2
    done

    # Check if any chunk succeeded
    success_count=0
    for f in "$TMPDIR"/output_*.txt; do
        if [[ -f "$f" ]] && ! grep -q '^\[TRANSLATION ERROR' "$f"; then
            ((success_count++)) || true
        fi
    done

    if [[ $success_count -eq 0 ]]; then
        log "ERROR $t_num: all chunks failed, not saving"
        rm -rf "$TMPDIR"
        ((FAILED++)) || true
        sleep 5
        continue
    fi

    # Assemble translation
    trans_path="$TRANS_DIR/${t_num}_translation.md"
    {
        echo "# $title"
        echo "## $title"
        echo ""
        echo "Taishō Tripiṭaka No. ${t_num#T}"
        echo ""
        if [[ -n "$translator" ]]; then
            echo "Translated from the Chinese. $translator"
            echo ""
        fi
        echo "---"
        echo ""
        for f in "$TMPDIR"/output_*.txt; do
            [[ -f "$f" ]] && cat "$f"
            echo ""
            echo ""
        done
    } > "$trans_path"

    text_elapsed=$(( $(date +%s) - text_start ))
    trans_size=$(wc -c < "$trans_path" | tr -d ' ')
    log "INFO  $t_num: translation saved (${trans_size} bytes, ${text_elapsed}s total)"
    ((COMPLETED++)) || true

    rm -rf "$TMPDIR"
    sleep 5

done <<< "$TEXTS"

# Summary
log "INFO  ==============================="
log "INFO  BATCH SUMMARY"
log "INFO    Completed: $COMPLETED"
log "INFO    Failed: $FAILED"
log "INFO  ==============================="
