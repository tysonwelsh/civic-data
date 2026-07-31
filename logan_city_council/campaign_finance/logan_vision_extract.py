#!/usr/bin/env python3
"""logan_vision_extract.py — GATED Claude-vision escalation for the SCANNED Logan campaign-
finance filings whose handwritten OCR could not be reconciled against the form's printed totals.

Logan-unique twin of orem_city_council/campaign_finance/vision_extract.py. Discipline is
identical (the repo anti-fabrication rule): used ONLY for `format=scanned` filings that still
fail reconciliation after tesseract OCR. Logan filings are ALL handwritten scans and their
itemized amounts are written without a `$` sign, so OCR reads essentially no line items —
vision is the primary itemization path here (expected: nearly every filing escalates).

It renders each filing's pages with `pdftoppm -jpeg` into a WORKING DIR (`vision/_tmp`, never
/tmp) and asks Claude (`claude-sonnet-5`) to TRANSCRIBE EXACTLY — copy digits, never infer or
compute, mark illegible as null. The transcription is cached verbatim to `vision/<doc8>.json`;
`build_finance.py` feeds it through the SAME reconciliation as the OCR rows (driver
`rows_override_fn`), so a vision filing earns confidence only if it reconciles.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 logan_vision_extract.py            # process every currently-flagged filing
    python3 logan_vision_extract.py <doc8> ... # only these document ids
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
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05
DPI = 150                          # handwriting needs a touch more than Orem's 120
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
    "You are transcribing a scanned, HANDWRITTEN Utah municipal campaign-finance filing — the "
    "City of Logan 'Campaign Finance Statement / Report of Contributions and Expenditures' form "
    "(Utah Code 10-3-208). Transcribe EXACTLY what is written/printed on these page images.\n"
    "The form has a numbered COVER block stating totals, then itemized pages. The cover block is "
    "one of two layouts:\n"
    "  2025 form:  1a Aggregate total of contributions UNDER $500  |  1b Itemized total of "
    "contributions $500 or more (= 'Form A' total)  |  2a Aggregate total of campaign "
    "expenditures UNDER $500  |  2b Itemized total of campaign expenditures (= 'Form B' total).\n"
    "  2021 form:  1 Total aggregate amount of less than $500 (contributions+expenditures)  |  "
    "2 Itemized contributions of more than $500  |  3 Itemized expenditures of more than $500.\n"
    "The itemized pages are a 'Form A' contribution list (Date / Name of Contributor / Amount / "
    "In-Kind if applicable) and a 'Form B' expenditure list (Date / To Whom / Amount / Purpose). "
    "SOME candidates instead attach a printed ledger (e.g. a Venmo/PayPal/cash export, or a "
    "spreadsheet) — treat each contribution/donation line there as a contribution row and each "
    "expense line as an expenditure row.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as written, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a digit/character/field is illegible, use null for that field. NEVER guess a value.\n"
    "- For each contribution use the amount the donor actually GAVE (the gross/'total' amount if "
    "a ledger shows gross vs net vs fee columns), not a net-of-fee figure.\n"
    "- Mark a contribution in_kind=true only if the form's in-kind column is filled for that row; "
    "else in_kind=false.\n"
    "- Ignore blank placeholder rows and the itemized-list's own SUBTOTAL/TOTAL summary lines "
    "(do not transcribe a 'Total'/'TOTAL DONATIONS'/'Total Expenses' line as a row).\n"
    "- Transcribe the numbered COVER-block figures into: contributions_under_500 (1a / the 2021 "
    "under-$500 aggregate), contributions_itemized (1b / 2021 line 2), expenditures_under_500 "
    "(2a), expenditures_itemized (2b / 2021 line 3). If the cover prints an explicit grand total "
    "line for either side, also give total_contributions / total_expenditures; else leave those "
    "null. Use null for any cover figure that is blank or illegible.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"contributions_under_500":"..","contributions_itemized":"..","total_contributions":"..",'
    '"expenditures_under_500":"..","expenditures_itemized":"..","total_expenditures":".."}'
)


def _render(doc: Path):
    """Rasterize a PDF page-by-page via pdftoppm into the working dir; feed a JPEG/PNG directly."""
    ext = doc.suffix.lower()
    if ext in (".jpg", ".jpeg", ".png"):
        media = "image/png" if ext == ".png" else "image/jpeg"
        b = base64.standard_b64encode(doc.read_bytes()).decode()
        return [{"type": "image",
                 "source": {"type": "base64", "media_type": media, "data": b}}]
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
    r = urllib.request.urlopen(req, timeout=600)
    d = json.load(r)
    txt = "".join(b.get("text", "") for b in d.get("content", []))
    u = d.get("usage", {})
    if d.get("stop_reason") == "max_tokens":
        raise ValueError("response truncated at max_tokens (raise the limit or split pages)")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _did8(path):
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]


def _flagged():
    """(doc8, source_filing) for filings that did not both-side reconcile (all Logan = scanned)."""
    out = []
    for r in csv.DictReader(open(HERE / "filing_totals.csv")):
        if not (r["reconciles_contrib"] == "True" and r["reconciles_expend"] == "True"):
            out.append((r["document_id"], r["source_filing"]))
    return out


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    targets = [(d, p) for d, p in _flagged() if not want or d in want]
    tin = tout = done = pages = 0
    for doc8, rel in targets:
        cache = VISION_DIR / f"{doc8}.json"
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
            print(f"  SKIP {doc8} ({type(e).__name__}: {str(e)[:90]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        pages += len(imgs)
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8} pages={len(imgs)} contrib={len(parsed.get('contributions',[]))}"
              f" expend={len(parsed.get('expenditures',[]))} tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15   # Sonnet list price 2026: $3/Mtok in, $15/Mtok out
    print(f"\nfilings vision-processed this run: {done} | pages={pages} | input_tok={tin} "
          f"output_tok={tout} | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
