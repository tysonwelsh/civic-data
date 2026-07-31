#!/usr/bin/env python3
"""vision_extract.py — GATED Claude-vision escalation for the OCR filings the parser could not
reconcile.  (Sandy campaign-finance, Phase 4.)

Discipline (mirrors slc_city_council/public_comments/vision_extract.py + the repo's anti-fabrication
rule): this is a fallback used ONLY for filings whose itemized rows did not reconcile against the
form's printed Summary total after OCR + whitelisted repair. It renders those filings' pages and
asks Claude to TRANSCRIBE EXACTLY — copy digits, never infer/compute, mark illegible as null. The
transcription is cached verbatim to `vision/<doc8>.json`; `build_finance.py` then feeds it through
the SAME normalization + reconciliation as the OCR rows (driver `rows_override_fn`), so a vision
filing is judged by the identical printed-total test and earns confidence only if it reconciles.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 vision_extract.py            # process every currently-flagged filing
    python3 vision_extract.py <doc8> ... # only these document ids
"""
from __future__ import annotations

import base64
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VISION_DIR = HERE / "vision"
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05 (update as models evolve)
DPI = 120                          # letter page ~ long edge 1300px (<=1568 Anthropic cap)
API = "https://api.anthropic.com/v1/messages"


def _load_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    # reuse the gitignored SLC .env (same account) — never printed
    env = HERE.parents[1] / "slc_city_council" / "public_comments" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("ANTHROPIC_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ANTHROPIC_API_KEY not found (env or slc .env)")


PROMPT = (
    "You are transcribing a scanned Utah municipal campaign-finance filing ('Report of "
    "Contributions and Expenditures', Schedule A = itemized contributions, Schedule B = itemized "
    "expenditures). Transcribe EXACTLY what is printed on these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as printed, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- A row's amount in the right-hand In-Kind column (or a row explicitly labelled in-kind) -> "
    "in_kind=true, amount=that in-kind value. A normal cash Amount -> in_kind=false.\n"
    "- Ignore SUBTOTAL / TOTAL / grand-total lines: transcribe only individual dated line items.\n"
    "- From the Summary Page copy the printed totals (Column A / 'Total this Period').\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34","in_kind":false}],'
    '"total_contributions":"..","total_in_kind_contributions":"..","total_expenditures":"..",'
    '"total_in_kind_expenditures":"..","beginning_balance":"..","ending_balance":".."}'
)


def _render(pdf: Path):
    out = VISION_DIR / "_tmp"
    out.mkdir(parents=True, exist_ok=True)
    stem = str(out / "p")
    subprocess.run(["pdftoppm", "-jpeg", "-r", str(DPI), str(pdf), stem],
                   check=True, capture_output=True)
    imgs = sorted(out.glob("p*.jpg"))
    blocks = []
    for im in imgs:
        b = base64.standard_b64encode(im.read_bytes()).decode()
        blocks.append({"type": "image",
                       "source": {"type": "base64", "media_type": "image/jpeg", "data": b}})
        im.unlink()
    return blocks


def _call(key, image_blocks):
    body = {"model": MODEL, "max_tokens": 32768,   # big filings (200+ donor rows) need the room
            "messages": [{"role": "user",
                          "content": image_blocks + [{"type": "text", "text": PROMPT}]}]}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    r = urllib.request.urlopen(req, timeout=600)
    d = json.load(r)
    txt = "".join(b.get("text", "") for b in d.get("content", []))
    u = d.get("usage", {})
    if d.get("stop_reason") == "max_tokens":
        raise ValueError("response truncated at max_tokens (raise the limit or split pages)")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _flagged_docs():
    ft = HERE / "filing_totals.csv"
    docs = []
    for r in csv.DictReader(open(ft)):
        if not (r["reconciles_contrib"] == "True" and r["reconciles_expend"] == "True"):
            docs.append((r["document_id"], r["source_filing"]))
    return docs


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    targets = [(d, p) for d, p in _flagged_docs() if not want or d in want]
    tin = tout = 0
    done = 0
    for doc8, rel in targets:
        # repo-standard cache key (2026-07-19): sha1(index path)[:8], NOT the doc id
        cache = VISION_DIR / f"{hashlib.sha1(rel.encode()).hexdigest()[:8]}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        imgs = _render(pdf)
        try:
            parsed, i, o = _call(key, imgs)
        except Exception as e:                     # per-filing failure never aborts the batch
            print(f"  SKIP {doc8}  ({type(e).__name__}: {str(e)[:80]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8}  pages={len(imgs)}  contrib={len(parsed.get('contributions',[]))}"
              f"  expend={len(parsed.get('expenditures',[]))}  tok_in={i} tok_out={o}")
    # Anthropic Sonnet list price (2026): $3 / Mtok in, $15 / Mtok out
    cost = tin / 1e6 * 3 + tout / 1e6 * 15
    print(f"\nfilings vision-processed this run: {done}  |  input_tok={tin}  output_tok={tout}"
          f"  |  approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
