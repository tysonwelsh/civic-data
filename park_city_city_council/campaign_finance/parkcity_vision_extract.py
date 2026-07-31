#!/usr/bin/env python3
"""parkcity_vision_extract.py — GATED Claude-vision escalation for the SCANNED Park City
campaign-finance filings whose OCR could not be reconciled against the form's printed Form-A /
Form-B totals.

Discipline (mirrors orem_city_council/campaign_finance/vision_extract.py + the repo anti-
fabrication rule): a fallback used ONLY for `format=scanned` filings that still fail
reconciliation after tesseract OCR + the whitelisted currency repair. It renders those filings'
pages and asks Claude to TRANSCRIBE EXACTLY — copy digits, never infer/compute, mark illegible as
null. The transcription is cached verbatim to `vision/<doc8>.json`; `build_finance.py` then feeds
it through the SAME reconciliation as the OCR rows (driver `rows_override_fn`), so a vision filing
earns confidence only if it reconciles. Born-digital filings are NEVER escalated here.

`<doc8>` = sha1(dataset-relative path)[:8] (index.csv carries no sha256) — matches build_finance.py.
Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 parkcity_vision_extract.py            # process every currently-flagged SCANNED filing
    python3 parkcity_vision_extract.py <doc8> ... # only these document ids
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
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05 (per Orem run)
DPI = 130
API = "https://api.anthropic.com/v1/messages"


def _did8(path):
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]


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
    "You are transcribing a scanned PARK CITY municipal 'Campaign Financial Report' (UCA 10-3-208 / "
    "Park City Municipal Code 3-3). The form has a cover page of totals and two itemized sections: "
    "'ITEMIZED CONTRIBUTION REPORT (Form A)' (Date / Name of Contributor / Mailing Address / Amount; "
    "some rows are marked 'in kind') and 'ITEMIZED EXPENDITURE REPORT (Form B)' (Date / Name of "
    "recipient / Purpose / Expense amount). Transcribe EXACTLY what is printed on these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as printed, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- Put every Form-A contribution row in `contributions`; set in_kind=true when the row is marked "
    "'in kind' (amount = the printed in-kind value if any, else null). Put every Form-B expenditure "
    "row in `expenditures` (amount = the 'Expense' column value).\n"
    "- Ignore SUBTOTAL / TOTAL / running-total lines and empty placeholder rows: transcribe only real "
    "dated line items.\n"
    "- Copy the form's printed totals into total_contributions (the Form-A total / 'Total amount from "
    "donors giving more than $50' / '1b. Itemized total of contributions'), and total_expenditures "
    "(the Form-B total / 'Total campaign expenditures' / '3b. Itemized total of campaign "
    "expenditures'). If the cover page shows a value, prefer it.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"total_contributions":"..","total_expenditures":".."}'
)


def _render(doc: Path):
    ext = doc.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png"):
        media = "image/png" if ext == ".png" else "image/jpeg"
        b = base64.standard_b64encode(doc.read_bytes()).decode()
        return [{"type": "image", "source": {"type": "base64", "media_type": media, "data": b}}]
    out = VISION_DIR / "_tmp"
    out.mkdir(parents=True, exist_ok=True)
    stem = str(out / "p")
    subprocess.run(["pdftoppm", "-jpeg", "-r", str(DPI), str(doc), stem],
                   check=True, capture_output=True)
    blocks = []
    for im in sorted(out.glob("p*.jpg")):
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
    r = urllib.request.urlopen(req, timeout=180)
    d = json.load(r)
    txt = "".join(b.get("text", "") for b in d.get("content", []))
    u = d.get("usage", {})
    if d.get("stop_reason") == "max_tokens":
        raise ValueError("response truncated at max_tokens (raise the limit or split pages)")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _flagged_scanned():
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
    for doc8, rel in targets:
        cache = VISION_DIR / f"{doc8}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        try:
            imgs = _render(pdf)
            parsed, i, o = _call(key, imgs)
        except Exception as e:
            print(f"  SKIP {doc8} ({type(e).__name__}: {str(e)[:80]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8} pages={len(imgs)} contrib={len(parsed.get('contributions', []))}"
              f" expend={len(parsed.get('expenditures', []))} tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15   # Sonnet list price 2026: $3/Mtok in, $15/Mtok out
    print(f"\nfilings vision-processed this run: {done} | input_tok={tin} output_tok={tout}"
          f" | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
