#!/usr/bin/env python3
"""vision_extract.py — GATED Claude-vision escalation for the SCANNED Orem campaign-finance
filings whose OCR could not be reconciled against the form's printed section TOTALs.

Discipline (mirrors sandy_city_council/campaign_finance/vision_extract.py + the repo anti-
fabrication rule): a fallback used ONLY for `format=scanned` filings that still fail
reconciliation after tesseract OCR + the whitelisted currency repair. It renders those filings'
pages and asks Claude to TRANSCRIBE EXACTLY — copy digits, never infer/compute, mark illegible as
null. The transcription is cached verbatim to `vision/<doc8>.json`; `build_finance.py` then feeds
it through the SAME reconciliation as the OCR rows (driver `rows_override_fn`), so a vision filing
earns confidence only if it reconciles. Born-digital filings are NEVER escalated here.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 vision_extract.py            # process every currently-flagged SCANNED filing
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
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05
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
    "You are transcribing a scanned Utah municipal campaign-finance filing — the self-hosted "
    "'Financial Disclosure / Report of Contributions and Expenditures' form. It has three itemized "
    "sections: 'Cash Contributions' (Date / Name of Donor / Amount), 'In-Kind Contributions' "
    "(Date / Name of Donor / Estimated Amount), and 'Cash Expenditures' (Date / Name of Recipient / "
    "Political Purpose / Amount), each ending in a printed TOTAL. Transcribe EXACTLY what is printed "
    "on these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as printed, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- Put every 'Cash Contributions' row in `contributions` with in_kind=false, and every "
    "'In-Kind Contributions' row in `contributions` with in_kind=true (amount = the estimated "
    "in-kind value). Put 'Cash Expenditures' rows in `expenditures`.\n"
    "- Ignore SUBTOTAL / TOTAL / GRAND TOTAL lines and empty placeholder rows (a bare '$ -' or "
    "'None'): transcribe only real dated line items.\n"
    "- Copy the form's printed section TOTALs into total_contributions (Cash Contributions TOTAL), "
    "total_in_kind_contributions (In-Kind TOTAL), and total_expenditures (Cash Expenditures TOTAL).\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34","in_kind":false}],'
    '"total_contributions":"..","total_in_kind_contributions":"..","total_expenditures":".."}'
)


def _render(doc: Path):
    """Return a list of Anthropic image blocks. A PDF is rasterized page-by-page via pdftoppm; a
    JPEG/PNG filing (Orem publishes some as photographed images, not PDFs) is fed directly."""
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


def _flagged_scanned():
    """(doc8, source_filing) for filings that (a) did not both-side reconcile AND (b) are scanned."""
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
        # repo-standard cache key (2026-07-19): sha1(index path)[:8], NOT the doc id
        cache = VISION_DIR / f"{hashlib.sha1(rel.encode()).hexdigest()[:8]}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        try:
            imgs = _render(pdf)                 # render inside the try: one bad file never aborts the batch
            parsed, i, o = _call(key, imgs)
        except Exception as e:
            print(f"  SKIP {doc8} ({type(e).__name__}: {str(e)[:80]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8} pages={len(imgs)} contrib={len(parsed.get('contributions',[]))}"
              f" expend={len(parsed.get('expenditures',[]))} tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15   # Sonnet list price 2026: $3/Mtok in, $15/Mtok out
    print(f"\nfilings vision-processed this run: {done} | input_tok={tin} output_tok={tout}"
          f" | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
