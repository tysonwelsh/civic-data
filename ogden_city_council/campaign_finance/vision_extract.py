#!/usr/bin/env python3
"""vision_extract.py — GATED Claude-vision escalation for the SCANNED Ogden campaign-finance
"Combined Report of Contributions & Expenditures" packets whose tesseract OCR could not be
reconciled against the form's printed attachment TOTALs.

Discipline (mirrors orem/sandy/st_george vision_extract.py + the repo anti-fabrication rule): a
fallback used ONLY for `format=scanned` filings that still fail reconciliation after OCR. It
renders those filings' pages (pdftoppm -jpeg) and asks Claude to TRANSCRIBE EXACTLY — copy digits,
never infer/compute/sum, mark illegible as null. The transcription is cached verbatim to
`vision/<viewid>.json`; `build_finance.py` then feeds it through the SAME reconciliation as the OCR
rows (driver `rows_override_fn`), so a vision filing earns confidence only if it reconciles.
Born-digital filings are NEVER escalated here.

Ogden specifics vs the generic Utah form: the packet bundles the WHOLE cycle (First/Second/Third/
Final reports), organized as repeated "ITEMIZED REPORT OF CAMPAIGN CONTRIBUTIONS – ATTACHMENT A"
and "…EXPENDITURES – ATTACHMENT B" tables, each ending in its own printed TOTAL; IN-KIND is a
per-row flag ("Yes" column or purpose "In-Kind"), NOT a separate section. To keep vision to pure
transcription, it returns EVERY printed attachment TOTAL verbatim as a list; build_finance.py sums
them (never the model) to form the packet's stated totals, exactly like the text parser.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 vision_extract.py            # process every currently-flagged SCANNED filing
    python3 vision_extract.py <viewid> … # only these filings (document_id = DocumentCenter View id)
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
import urllib.request

HERE = Path(__file__).resolve().parent
VISION_DIR = HERE / "vision"
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05 (orem/st_george runs)
DPI = 120
API = "https://api.anthropic.com/v1/messages"


def _load_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    env = HERE.parents[1] / "slc_city_council" / "public_comments" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("ANTHROPIC_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ANTHROPIC_API_KEY not found (env or slc .env)")


PROMPT = (
    "You are transcribing a scanned Ogden City (Utah) campaign-finance filing — a 'Combined Report "
    "of Contributions & Expenditures' packet that bundles a candidate's whole election cycle of "
    "reports. Each report has two itemized tables: 'ITEMIZED REPORT OF CAMPAIGN CONTRIBUTIONS "
    "(Attachment A)' with columns Date / Name / Address / Amount / Purpose, and 'ITEMIZED REPORT OF "
    "CAMPAIGN EXPENDITURES (Attachment B)' with Date / Name / Address / Amount / Purpose. Each table "
    "ends in a printed TOTAL. IN-KIND contributions are marked by a 'Yes' in an in-kind column or a "
    "purpose of 'In-Kind' (there is NO separate in-kind table). Transcribe EXACTLY what is printed "
    "on these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as printed, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- Put every contribution line item in `contributions` (in_kind=true only if the row is marked "
    "in-kind), and every expenditure line item in `expenditures`. Transcribe only real dated line "
    "items — skip the numbered SUMMARY box (lines 1-6), blank rows, and '$50 or less' aggregate "
    "description rows.\n"
    "- Copy each Attachment A's printed contribution TOTAL (verbatim string) into "
    "`contribution_totals` as a list, and each Attachment B's printed expenditure TOTAL into "
    "`expenditure_totals` — one entry per report in the packet. Do NOT add them together.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"contribution_totals":["1234.56"],"expenditure_totals":["12.34"]}'
)


def _render(doc: Path):
    out = VISION_DIR / "_tmp"
    out.mkdir(parents=True, exist_ok=True)
    stem = str(out / "p")
    subprocess.run(["pdftoppm", "-jpeg", "-r", str(DPI), str(doc), stem],
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
    body = {"model": MODEL, "max_tokens": 32768,
            "messages": [{"role": "user",
                          "content": image_blocks + [{"type": "text", "text": PROMPT}]}]}
    req = urllib.request.Request(API, data=json.dumps(body).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                                          "content-type": "application/json"})
    r = urllib.request.urlopen(req, timeout=300)
    d = json.load(r)
    txt = "".join(b.get("text", "") for b in d.get("content", []))
    u = d.get("usage", {})
    if d.get("stop_reason") == "max_tokens":
        raise ValueError("response truncated at max_tokens (raise the limit or split pages)")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _flagged_scanned():
    """(document_id, source_filing) for filings that did NOT both-side reconcile AND are scanned."""
    idx = {r["path"]: r for r in csv.DictReader(open(HERE / "index.csv"))}
    out = []
    for r in csv.DictReader(open(HERE / "filing_totals.csv")):
        clean = r["reconciles_contrib"] == "True" and r["reconciles_expend"] == "True"
        scanned = idx.get(r["source_filing"], {}).get("format", "") == "scanned"
        if not clean and scanned:
            out.append((r["document_id"], r["source_filing"]))
    return out


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    targets = [(d, p) for d, p in _flagged_scanned() if not want or d in want]
    tin = tout = done = 0
    for doc, rel in targets:
        # repo-standard cache key (2026-07-19): sha1(index path)[:8], NOT the doc id
        cache = VISION_DIR / f"{hashlib.sha1(rel.encode()).hexdigest()[:8]}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        try:
            imgs = _render(pdf)                 # render inside try: one bad file never aborts the batch
            parsed, i, o = _call(key, imgs)
        except Exception as e:
            print(f"  SKIP {doc} ({type(e).__name__}: {str(e)[:90]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc} pages={len(imgs)} contrib={len(parsed.get('contributions',[]))}"
              f" expend={len(parsed.get('expenditures',[]))} tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15   # Sonnet list price 2026: $3/Mtok in, $15/Mtok out
    print(f"\nfilings vision-processed this run: {done} | input_tok={tin} output_tok={tout}"
          f" | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
