#!/bin/bash
set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"
unset CLAUDECODE 2>/dev/null || true
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true

echo "Testing claude -p..."
echo "PATH: $(which claude)"
echo "Start: $(date)"

claude -p --output-format text < /tmp/test_chunk.txt > /tmp/quick_test_result.txt 2>/tmp/quick_test_err.txt
rc=$?

echo "Exit: $rc"
echo "End: $(date)"
echo "Output size: $(wc -c < /tmp/quick_test_result.txt) bytes"
echo "Stderr: $(cat /tmp/quick_test_err.txt)"
echo "First line: $(head -1 /tmp/quick_test_result.txt)"
