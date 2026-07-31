#!/usr/bin/env python3
"""Fetch all CH packets into packets/raw/<date>/ via polite_fetch.py."""
import json, subprocess, os, sys

PF = "/Users/tysonwelsh/civic-data/.claude/skills/expand-city-sources/scripts/polite_fetch.py"
BASE = os.path.dirname(os.path.abspath(__file__))
REFERER = "https://www.cottonwoodheights.utah.gov/your-government/elected-officials/council-meeting-agendas-and-minutes"

manifest = json.load(open("/tmp/ch_manifest.json"))
ok = 0
for i, r in enumerate(manifest, 1):
    outdir = os.path.join(BASE, "raw", r["date"])
    os.makedirs(outdir, exist_ok=True)
    dest = os.path.join(outdir, r["filename"])
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(i, "skip(exists)", r["filename"])
        ok += 1
        continue
    cmd = ["python3", PF, r["url"], "--out", outdir, "--name", r["filename"],
           "--referer", REFERER]
    res = subprocess.run(cmd, capture_output=True, text=True)
    good = os.path.exists(dest) and os.path.getsize(dest) > 1000
    print(i, "OK" if good else "FAIL", r["date"], r["body"], r["filename"],
          os.path.getsize(dest) if os.path.exists(dest) else 0)
    if good:
        ok += 1
    else:
        print("   stderr:", res.stdout[-300:])
print("fetched", ok, "of", len(manifest))
