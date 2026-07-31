#!/usr/bin/env python3
"""wj_vision_extract.py — GATED Claude-vision transcription for West Jordan's SCANNED campaign-
finance filings (Phase 4 — the 2021 handwritten city form + the image-scanned EasyVote reports).

Twin of sandy/logan vision_extract.py; same anti-fabrication discipline (the repo cardinal rule):
used ONLY for `format=scanned` in-scope C&E filings whose handwriting / image scan tesseract OCR
cannot reconcile against the form's printed totals (WJ's scans OCR far worse than Sandy's — the
OCR-only pass reconciles ~2/30, so vision is the primary itemization path here). It renders each
filing's pages with `pdftoppm -jpeg` into a WORKING DIR (`vision/_tmp`, never /tmp) and asks Claude
(`claude-sonnet-5`) to TRANSCRIBE EXACTLY — copy digits, never infer/compute, mark illegible null.
The transcription is cached verbatim to `vision/<doc8>.json`; `build_finance.py` feeds it through
the SAME reconciliation as the OCR rows (driver `rows_override_fn`), so a vision filing earns
confidence only if it reconciles.

TWO form families, one script (prompt chosen by the filing's `path`):
  * raw/city/    -> the 2021 West Jordan "Campaign Financial Disclosure Report" (numbered cover
                   block lines 1-6 + Attachment A-1 contributions + Attachment B expenditures).
  * raw/easyvote/-> the EasyVote "Report of Contributions and Expenditures" (Summary Page +
                   Schedule A/B) — same form as the born-digital 43, but image-scanned.
Both prompts emit ONE JSON schema (below); build_finance maps the cover figures per form.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 wj_vision_extract.py            # every in-scope scanned filing without a cache
    python3 wj_vision_extract.py <doc8> ... # only these document ids
"""
from __future__ import annotations

import base64
import csv
import hashlib
import os
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
VISION_DIR = HERE / "vision"
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05
DPI = 150                          # handwriting/scan detail (matches Logan)
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


_JSON_SHAPE_EV = (
    'Return ONLY a JSON object, no prose:\n'
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34","in_kind":false}],'
    '"total_contributions":"..","total_expenditures":"..",'
    '"contributions_50_or_less":"..","beginning_balance":"..","ending_balance":".."}'
)

PROMPT_CITY = (
    "You are transcribing a scanned West Jordan City municipal campaign-finance filing — the "
    "'CAMPAIGN FINANCIAL DISCLOSURE REPORT / Report of Contributions & Expenditures' (West Jordan "
    "Municipal Code 1-15-4, Utah Code 10-3-208). It is a fillable form; entries may be typed or "
    "HANDWRITTEN. Transcribe EXACTLY what appears on these page images.\n"
    "IMPORTANT: this PDF often BUNDLES MORE THAN ONE report (e.g. an interim report AND a final "
    "report, each a full form with its own numbered cover block + its own Attachment A & B). Return "
    "ONE ARRAY ENTRY PER REPORT you find. The long pages of statute / ordinance text between forms "
    "are boilerplate — ignore them. A report is recognizable by its 'CANDIDATE CAMPAIGN FINANCIAL "
    "STATEMENT' cover with the numbered lines 1-6.\n"
    "Each report's numbered COVER block:\n"
    "  1. Balance carried forward from last report\n"
    "  2. Total contributions of $50 or less per donor during this reporting period (unitemized)\n"
    "  3. Total contributions of more than $50 per donor during this reporting period\n"
    "  4. Total contributions as of this report (= line 2 + line 3)\n"
    "  5. Total expenditures or obligations incurred during this reporting period "
    "(= the printed TOTAL at the bottom of Attachment B)\n"
    "  6. Ending Balance for this reporting period\n"
    "Then that report's ATTACHMENT A-1 (itemized contributions: Date / Name of contributor / "
    "Address / Amount) and ATTACHMENT B (itemized expenditures: Date / Person or Organization paid "
    "/ Address / Purpose / Amount). An in-kind item is written with '(In Kind)' next to it.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as written, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number. A figure written in (parentheses) or with a "
    "leading minus is the amount — report its positive magnitude.\n"
    "- If a digit/character/field is illegible, use null for that field. NEVER guess a value.\n"
    "- Attribute each Attachment A / Attachment B row to the report it belongs to.\n"
    "- Mark a contribution or expenditure in_kind=true ONLY when the form labels that row in-kind; "
    "else in_kind=false.\n"
    "- Ignore blank placeholder rows and the Attachment's own TOTAL summary line (do not transcribe "
    "a 'Total' line as a data row).\n"
    "- Per report map the cover block into: total_contributions = line 4 (Total contributions as "
    "of this report); total_expenditures = line 5 (the Attachment B total); contributions_50_or_"
    "less = line 2; beginning_balance = line 1; ending_balance = line 6. Use null for any cover "
    "figure that is blank or illegible.\n"
    'Return ONLY a JSON object, no prose:\n'
    '{"reports":[{"reporting_period":"(which box is checked / the period)",'
    '"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34","in_kind":false}],'
    '"total_contributions":"..","total_expenditures":"..",'
    '"contributions_50_or_less":"..","beginning_balance":"..","ending_balance":".."}]}'
)

PROMPT_EV = (
    "You are transcribing a scanned Utah municipal campaign-finance filing — the West Jordan "
    "EasyVote 'Report of Contributions and Expenditures' (Summary Page, then Schedule A = itemized "
    "contributions, Schedule B = itemized expenditures). Transcribe EXACTLY what is printed on "
    "these page images.\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as printed, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a character/field is illegible, use null for that field. Never guess.\n"
    "- A row's amount in the right-hand In-Kind column (or a row explicitly labelled in-kind) -> "
    "in_kind=true, amount=that in-kind value. A normal cash Amount -> in_kind=false.\n"
    "- Ignore SUBTOTAL / TOTAL / grand-total lines: transcribe only individual dated line items.\n"
    "- From the Summary Page copy the printed totals from Column A ('Total this Period'): "
    "total_contributions = TOTAL CONTRIBUTIONS RECEIVED; total_expenditures = TOTAL EXPENDITURES "
    "MADE; beginning_balance = Balance at Beginning of Reporting Period; ending_balance = Balance "
    "at Close of Reporting Period. Leave contributions_50_or_less null (this form has no such "
    "line).\n"
    + _JSON_SHAPE_EV
)


def _prompt_for(rel: str) -> str:
    return PROMPT_CITY if rel.startswith("raw/city/") else PROMPT_EV


def _did8(ix):
    """Match build_finance: EasyVote -> trailing 8-hex of the filename; city -> sha1(path)[:8]."""
    stem = os.path.splitext(os.path.basename(ix["path"]))[0]
    m = re.search(r"([0-9A-F]{8})$", stem)
    if m:
        return m.group(1)
    return hashlib.sha1(ix["path"].encode("utf-8")).hexdigest()[:8]


def _in_scope_scanned(ix):
    return (ix.get("format", "").strip().lower() == "scanned"
            and ix.get("filing_type", "").strip() in ("interim", "summary"))


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


def _call(key, image_blocks, prompt):
    body = {"model": MODEL, "max_tokens": 32768,
            "messages": [{"role": "user",
                          "content": image_blocks + [{"type": "text", "text": prompt}]}]}
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


def _targets(want):
    rows = list(csv.DictReader(open(HERE / "index.csv")))
    out = []
    for ix in rows:
        if not _in_scope_scanned(ix):
            continue
        d8 = _did8(ix)
        if want and d8 not in want:
            continue
        out.append((d8, ix["path"]))
    return out


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    tin = tout = done = pages = 0
    for doc8, rel in _targets(want):
        cache = VISION_DIR / f"{doc8}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        try:
            imgs = _render(pdf)                 # one bad file never aborts the batch
            parsed, i, o = _call(key, imgs, _prompt_for(rel))
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
