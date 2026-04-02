#!/bin/bash
# Test the stream-json protocol with claude CLI
set -euo pipefail
export PATH="/opt/homebrew/bin:$PATH"
unset CLAUDECODE 2>/dev/null || true
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDE_CODE_ENTRYPOINT 2>/dev/null || true

echo "=== Test 1: -p with stream-json output + verbose ==="
echo '{"type":"user","content":"Say hello in exactly one word"}' | \
  claude -p --output-format stream-json --verbose --no-session-persistence \
  > /tmp/stream_t1_out.txt 2>/tmp/stream_t1_err.txt
echo "Exit: $?"
echo "Stdout bytes: $(wc -c < /tmp/stream_t1_out.txt)"
echo "First 3 lines:"
head -3 /tmp/stream_t1_out.txt
echo "---"
echo "Last 3 lines:"
tail -3 /tmp/stream_t1_out.txt
echo ""

echo "=== Test 2: -p with json output (get session_id) ==="
claude -p --output-format json --no-session-persistence "Say goodbye in one word" \
  > /tmp/stream_t2_out.txt 2>/tmp/stream_t2_err.txt
echo "Exit: $?"
cat /tmp/stream_t2_out.txt
echo ""

echo "=== DONE ==="
