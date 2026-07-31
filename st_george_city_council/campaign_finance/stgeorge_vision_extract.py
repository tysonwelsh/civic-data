#!/usr/bin/env python3
"""stgeorge_vision_extract.py — GATED Claude-vision escalation for the St. George campaign-finance
sections the OCR parser could not reconcile.  (St. George is the compilation-PDF city — Phase 4.)

St.George-UNIQUE twist vs the sandy/park_city vision extractors: each raw PDF is a MULTI-CANDIDATE
compilation, so a filing is only a PAGE RANGE inside its packet. This script reads that range from
`segments.csv` (the segmenter's regenerable mapping) and renders ONLY that candidate's pages
(`pdftoppm -jpeg -f <first> -l <last>`), never the whole packet.

Discipline (mirrors slc public_comments + sandy/park_city vision): used ONLY for filings whose
itemized rows did not reconcile against the form's printed total after OCR + whitelisted repair,
and NEVER for a filing already marked `superseded` (its primary twin carries the numbers). It asks
Claude to TRANSCRIBE EXACTLY — copy digits, never infer/compute, mark illegible null. The
transcription is cached verbatim to `vision/<doc8>.json`; `build_finance.py` feeds it through the
SAME reconciliation as the OCR rows (driver `rows_override_fn`), so a vision filing earns confidence
only if it reconciles. A figure that will not reconcile stays blank + needs_review + low, never
guessed.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 stgeorge_vision_extract.py            # every currently-flagged (non-superseded) filing
    python3 stgeorge_vision_extract.py <doc8> ... # only these document ids
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
VISION_DIR = HERE / "vision"
SEG_CSV = HERE / "segments.csv"
FT_CSV = HERE / "filing_totals.csv"
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05 (update as models evolve)
DPI = 150                          # letter page ~ long edge 1650px (kept <= Anthropic 1568 after JPEG)
API = "https://api.anthropic.com/v1/messages"


def _load_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env = HERE.parents[1] / "slc_city_council" / "public_comments" / ".env"   # reuse the same account
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("ANTHROPIC_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ANTHROPIC_API_KEY not found (env or slc .env)")


PROMPT = (
    "You are transcribing ONE candidate's scanned Utah municipal 'Campaign Finance Report' "
    "(St. George City). The pages are: a COVER (stated totals), Form 'A' = ITEMIZED CONTRIBUTION "
    "REPORT (columns: Date Received | Name of Contributor | Amount of Contribution | In-Kind "
    "Description), and Form 'B' = ITEMIZED EXPENDITURE REPORT (columns: Date | Payee | Amount of "
    "Expenditure | Purpose). Transcribe EXACTLY what is printed on these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as printed, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- A contribution row whose In-Kind Description column says 'In-kind' (or the row is otherwise "
    "marked in-kind) -> in_kind=true; a normal cash contribution -> in_kind=false. Record the "
    "amount as printed regardless.\n"
    "- Ignore the 'Total ... for reporting period' and grand-total lines: transcribe only individual "
    "dated line items.\n"
    "- From the COVER copy the printed 'Itemized total of contributions ...' as total_contributions, "
    "'Itemized total of expenditures ...' as total_expenditures, and the ending 'Balance ...' as "
    "ending_balance (for the 2021 form these are 'Total Contributions of all donors' / 'Total "
    "campaign expenses'). If a cover figure is blank or a dash, use null.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"total_contributions":"..","total_expenditures":"..","ending_balance":".."}'
)


def _render(pdf: Path, first: int, last: int):
    out = VISION_DIR / "_tmp"
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("p*.jpg"):
        f.unlink()
    stem = str(out / "p")
    subprocess.run(["pdftoppm", "-jpeg", "-r", str(DPI), "-f", str(first), "-l", str(last),
                    str(pdf), stem], check=True, capture_output=True)
    blocks = []
    for im in sorted(out.glob("p*.jpg")):
        b = base64.standard_b64encode(im.read_bytes()).decode()
        blocks.append({"type": "image",
                       "source": {"type": "base64", "media_type": "image/jpeg", "data": b}})
        im.unlink()
    return blocks


def _call(key, image_blocks):
    import urllib.request
    body = {"model": MODEL, "max_tokens": 32768,
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
        raise ValueError("response truncated at max_tokens (split the page range)")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _targets():
    """Flagged (not both-sides-reconciling) filings that are NOT superseded duplicates, joined to
    their segment page range + source PDF."""
    seg = {r["document_id"]: r for r in csv.DictReader(open(SEG_CSV)) if r["document_id"]}
    out = []
    for r in csv.DictReader(open(FT_CSV)):
        if r["reconciles_contrib"] == "True" and r["reconciles_expend"] == "True":
            continue
        if "supersed" in r["notes"]:
            continue
        s = seg.get(r["document_id"])
        if not s or not s["page_range"]:
            continue
        a, b = s["page_range"].replace("p", "").split("-")
        out.append((r["document_id"], r["source_filing"], r["candidate"], int(a), int(b)))
    return out


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    targets = [t for t in _targets() if not want or t[0] in want]
    tin = tout = done = 0
    for doc8, rel, cand, first, last in targets:
        # repo-standard cache key (2026-07-19): sha1(path + "|" + candidate)[:8] (multi-candidate compilation)
        cache = VISION_DIR / f"{hashlib.sha1((rel + chr(124) + cand).encode()).hexdigest()[:8]}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        imgs = _render(pdf, first, last)
        try:
            parsed, i, o = _call(key, imgs)
        except Exception as e:                     # per-filing failure never aborts the batch
            print(f"  SKIP {doc8} p{first}-{last}  ({type(e).__name__}: {str(e)[:70]}) — re-run to retry")
            continue
        tin += i
        tout += o
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8}  p{first}-{last} ({len(imgs)}pg)  "
              f"contrib={len(parsed.get('contributions', []))} expend={len(parsed.get('expenditures', []))}"
              f"  tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15         # Anthropic Sonnet list price (2026)
    print(f"\nfilings vision-processed this run: {done}  |  input_tok={tin}  output_tok={tout}"
          f"  |  approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
