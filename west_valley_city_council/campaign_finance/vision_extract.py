#!/usr/bin/env python3
"""vision_extract.py — GATED Claude-vision escalation for the SCANNED West Valley City
"CAMPAIGN FINANCE STATEMENT" (Form A/B) filings whose tesseract OCR could not be reconciled
against the form's printed cover totals.

Discipline (mirrors ogden/orem/sandy/st_george vision_extract.py + the repo anti-fabrication rule):
a fallback used ONLY for `format=scanned` filings that still fail reconciliation after OCR. It
renders those filings' pages (pdftoppm -jpeg) and asks Claude to TRANSCRIBE EXACTLY — copy digits,
never infer/compute/sum, mark illegible as null. The transcription is cached verbatim to
`vision/<ADID>.json`; `build_finance.py` then feeds it through the SAME reconciliation as the OCR
rows (driver `rows_override_fn`), so a vision filing earns confidence only if it reconciles.
Born-digital filings are NEVER escalated here.

WVC form specifics: a cover page with numbered totals ("1. Total contributions $X",
"2. Total campaign expenses $Y", "3. Balance at the end of reporting period $Z"), then an
ITEMIZED CONTRIBUTION REPORT (FORM "A") and an ITEMIZED EXPENDITURE REPORT (FORM "B"). MANY are
HANDWRITTEN. In-kind / loan are marked inline in the donor name. Vision returns each cover total
verbatim as a scalar (never summed by the model) plus the itemized line items.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 vision_extract.py                 # every currently-flagged SCANNED filing
    python3 vision_extract.py --max-pages 5   # skip filings with more than N pages (OCR floor)
    python3 vision_extract.py <ADID> …        # only these filings (document_id)
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
MODEL = "claude-sonnet-5"          # confirmed available (ogden/orem/st_george runs 2026-07)
DPI = 150
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
    "You are transcribing a scanned West Valley City (Utah) municipal 'CAMPAIGN FINANCE STATEMENT' "
    "(often HANDWRITTEN). It has a cover page with three numbered totals — '1. Total contributions "
    "$X', '2. Total campaign expenses $Y', '3. Balance at the end of reporting period $Z' — then an "
    "'ITEMIZED CONTRIBUTION REPORT (FORM A)' with columns Date Received / Name of Contributor / "
    "Mailing Address & Zip / Amount, and an 'ITEMIZED EXPENDITURE REPORT (FORM B)' with Date / "
    "Recipient (and Purpose) / Mailing Address & Zip / Amount. In-kind and loan contributions are "
    "marked inline in the name (e.g. '(In-kind)', '(Loan)'). Transcribe EXACTLY what is printed or "
    "handwritten on these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as written, including the decimal point. Do "
    "NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- Put every contribution line item in `contributions` (in_kind=true only if the row is marked "
    "in-kind), and every expenditure line item in `expenditures`. Transcribe only real filled rows — "
    "skip blank template rows and the numbered cover-summary lines.\n"
    "- Copy the cover-page '1. Total contributions' value verbatim into `total_contributions`, "
    "'2. Total campaign expenses' into `total_expenditures`, and '3. Balance at the end...' into "
    "`ending_balance` (each a single string; null if blank/illegible). Do NOT add anything together.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"123.45","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"total_contributions":"123.45","total_expenditures":"12.34","ending_balance":"1.00"}'
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
    body = {"model": MODEL, "max_tokens": 16384,
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
        raise ValueError("response truncated at max_tokens")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _flagged_scanned():
    """(document_id, source_filing, pages) for filings that did NOT both-side reconcile AND are
    scanned (document_id = index.csv source_id, e.g. ADID3496)."""
    idx = {r["path"]: r for r in csv.DictReader(open(HERE / "index.csv"))}
    out = []
    for r in csv.DictReader(open(HERE / "filing_totals.csv")):
        clean = r["reconciles_contrib"] == "True" and r["reconciles_expend"] == "True"
        ix = idx.get(r["source_filing"], {})
        if not clean and ix.get("format", "") == "scanned":
            out.append((r["document_id"], r["source_filing"], int(ix.get("pages", "0") or 0)))
    return out


def main(argv):
    max_pages = None
    if "--max-pages" in argv:
        i = argv.index("--max-pages")
        max_pages = int(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    targets = [(d, p, pg) for d, p, pg in _flagged_scanned()
               if (not want or d in want) and (max_pages is None or pg <= max_pages)]
    tin = tout = done = 0
    for doc, rel, pg in targets:
        # repo-standard cache key (2026-07-19): sha1(index path)[:8], NOT the doc id
        cache = VISION_DIR / f"{hashlib.sha1(rel.encode()).hexdigest()[:8]}.json"
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
            print(f"  SKIP {doc} ({type(e).__name__}: {str(e)[:90]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc} pages={len(imgs)} contrib={len(parsed.get('contributions',[]))}"
              f" expend={len(parsed.get('expenditures',[]))} tc={parsed.get('total_contributions')}"
              f" te={parsed.get('total_expenditures')} tok_in={i} tok_out={o}", flush=True)
    cost = tin / 1e6 * 3 + tout / 1e6 * 15   # Sonnet list price: $3/Mtok in, $15/Mtok out
    print(f"\nfilings vision-processed this run: {done} | input_tok={tin} output_tok={tout}"
          f" | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
