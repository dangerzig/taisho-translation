#!/usr/bin/env python3
"""Minimal test to debug claude -p subprocess behavior."""
import subprocess
import tempfile
import os
import time

prompt = """Translate this Chinese Buddhist text to English. Output ONLY the translation:

夫宗極絕於稱謂，賢聖以之沖默；玄旨非言不傳，釋迦所以致教。
"""

prompt_file = tempfile.mktemp(suffix='_prompt.txt')
output_file = tempfile.mktemp(suffix='_output.txt')

with open(prompt_file, 'w', encoding='utf-8') as f:
    f.write(prompt)

print(f"Prompt file: {prompt_file} ({os.path.getsize(prompt_file)} bytes)")
print(f"Output file: {output_file}")
print(f"CLAUDECODE in env: {'CLAUDECODE' in os.environ}")
print(f"ANTHROPIC_API_KEY in env: {'ANTHROPIC_API_KEY' in os.environ}")
print(f"CLAUDE_CODE_ENTRYPOINT in env: {'CLAUDE_CODE_ENTRYPOINT' in os.environ}")
print("Starting claude -p...")

start = time.time()
result = subprocess.run(
    f'env -u CLAUDECODE -u ANTHROPIC_API_KEY -u CLAUDE_CODE_ENTRYPOINT '
    f'claude -p --output-format text < "{prompt_file}" > "{output_file}" 2>&1',
    shell=True,
    timeout=120,
)
elapsed = time.time() - start

print(f"Exit code: {result.returncode} (took {elapsed:.1f}s)")
if os.path.exists(output_file):
    content = open(output_file).read()
    print(f"Output ({len(content)} bytes): {content[:200]}")
else:
    print("No output file!")

os.unlink(prompt_file)
if os.path.exists(output_file):
    os.unlink(output_file)
