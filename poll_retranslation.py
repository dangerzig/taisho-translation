#!/usr/bin/env python3
"""Poll retranslation batch and retrieve results when complete."""
import anthropic
import json
import time
import re
from pathlib import Path

BATCH_ID = json.load(open("retranslation_batch.json"))["batch_id"]
client = anthropic.Anthropic()

while True:
    b = client.messages.batches.retrieve(BATCH_ID)
    c = b.request_counts
    print(f"[{time.strftime('%H:%M:%S')}] succeeded={c.succeeded}, "
          f"processing={c.processing}, errored={c.errored}")
    if b.processing_status == "ended":
        break
    time.sleep(60)

print("\nBatch complete! Retrieving results...")

# Collect results by text
results = {}
for result in client.messages.batches.results(BATCH_ID):
    custom_id = result.custom_id
    t_num = custom_id.split("_fasc_")[0]
    fasc_num = int(custom_id.split("_fasc_")[1])
    
    if result.result.type == "succeeded":
        text = result.result.message.content[0].text
        if t_num not in results:
            results[t_num] = {}
        results[t_num][fasc_num] = text

# Assemble and save
for t_num, fascicles in results.items():
    assembled = []
    for i in sorted(fascicles.keys()):
        assembled.append(fascicles[i])
    
    full_text = "\n\n".join(assembled)
    outpath = Path(f"translations/{t_num}_translation.md")
    outpath.write_text(full_text, encoding="utf-8")
    print(f"  Saved {outpath} ({len(full_text):,} chars, {len(fascicles)} fascicles)")

# Calculate cost
total_input = sum(
    r.result.message.usage.input_tokens
    for r in client.messages.batches.results(BATCH_ID)
    if r.result.type == "succeeded"
)
total_output = sum(
    r.result.message.usage.output_tokens
    for r in client.messages.batches.results(BATCH_ID)
    if r.result.type == "succeeded"
)
cost = total_input / 1e6 * 2.50 + total_output / 1e6 * 12.50
print(f"\nTokens: {total_input:,} input, {total_output:,} output")
print(f"Estimated cost: ${cost:.2f}")
