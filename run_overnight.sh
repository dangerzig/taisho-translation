#!/bin/bash
# Overnight batch translation of the Taishō Tripiṭaka.
# Designed to be run from cron. Stops after 8 hours.
#
# To install in cron:
#   crontab -e
#   0 0 * * * /Users/danzigmond/taisho-translation-sample/run_overnight.sh
#
# To run manually:
#   ./run_overnight.sh
#
# To check progress:
#   ls ~/taisho-translation-sample/translations/ | wc -l
#   tail -f ~/taisho-translation-sample/logs/batch_*.log

set -euo pipefail

# Ensure claude CLI uses Max plan auth, not API key
unset ANTHROPIC_API_KEY 2>/dev/null || true
unset CLAUDECODE 2>/dev/null || true

cd /Users/danzigmond/taisho-translation-sample

echo "=== Overnight batch translation starting: $(date) ==="

# Run batch translation with 10-hour limit
# Pure bash script avoids Python subprocess TTY issues with claude -p
# --max-juan 30: skip very large texts for now
bash batch_translate.sh --hours 10 --max-juan 30 2>&1

echo "=== Overnight batch translation finished: $(date) ==="
