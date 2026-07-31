#!/usr/bin/env python3
"""nephi_vision_extract.py — GATED Claude-vision transcription for the SCANNED, HANDWRITTEN Nephi
campaign-finance filings, whose itemized amounts are written without a `$` sign and so read as
essentially nothing under tesseract OCR (vision is the primary itemization path here, exactly like
Logan).

Nephi-unique twin of logan_city_council/campaign_finance/logan_vision_extract.py. The one thing
that differs from Logan: Nephi's 2021/2023 uploads are MULTI-CANDIDATE COMPILATIONS — one PDF
holds several candidates' 2-page filings — so index.csv splits them into per-candidate rows
carrying a `page_range` (e.g. "3-4", "9-10,15-16,19-20"). This extractor renders ONLY that
candidate's page span (never the whole compilation), so each candidate is transcribed in isolation.
Single-filing rows (2019 / 2025, blank page_range) render the whole PDF. The un-attributable
"(unidentified filers)" row is skipped (out of scope — see build_finance.py).

Discipline is the repo anti-fabrication rule: TRANSCRIBE EXACTLY — copy digits, never infer or
compute, mark illegible as null. The transcription is cached verbatim to `vision/<doc8>.json`
(doc8 = sha1(path|page_range)[:8], matching build_finance._did8), and build_finance.py feeds it
through the SAME reconciliation as the OCR rows (driver `rows_override_fn`), so a vision filing
earns confidence only if it reconciles against the form's own printed cover totals.

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 nephi_vision_extract.py            # process every in-scope, un-cached filing
    python3 nephi_vision_extract.py <doc8> ... # only these document ids
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
MODEL = "claude-sonnet-5"          # confirmed available 2026-07-05 (used by Logan/Orem)
DPI = 150                          # handwriting needs a touch more than Orem's 120
API = "https://api.anthropic.com/v1/messages"
UNIDENTIFIED = "(unidentified filers)"


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
    "'Nephi City Campaign Financial Report' form (Utah Code 10-3-208). These page images are ONE "
    "candidate's filing: a COVER page stating totals, plus itemized 'Form A' / 'Form B' pages. "
    "Transcribe EXACTLY what is written/printed.\n"
    "The cover block is one of two layouts:\n"
    "  2025 form:  1a Aggregate total of contributions UNDER $500  |  1b Itemized total of "
    "contributions $500 or more (= 'Form A' total)  |  2a Aggregate total of campaign expenditures "
    "UNDER $500  |  2b Itemized total of campaign expenditures (= 'Form B' total).\n"
    "  Older form (2019/2021/2023):  line 1 'Contributions received totaling $500 or LESS'  |  "
    "line 2 'Enter the total of all received from Form A' (itemized contributions)  |  line 3 "
    "'Expenditures totaling $500 or LESS'  |  line 4 'Enter the total of all expenditures from "
    "Form B' (itemized expenditures)  |  line 5 'Balance at the end of the reporting period'.\n"
    "The itemized pages are 'ITEMIZED CONTRIBUTION REPORT (Form A)' (Date Received / Name of "
    "Contributor / Mailing Address / Amount of Contribution) and 'ITEMIZED EXPENDITURE REPORT "
    "(Form B)' (Date / Person or Organization To Whom Expenditure was made / Mailing Address / "
    "Amount of Expenditure).\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as written, including the decimal point. "
    "Do NOT compute, sum, round, or infer any number.\n"
    "- If a digit/character/field is illegible, use null for that field. NEVER guess a value.\n"
    "- For each contribution use the amount the donor actually GAVE (the gross amount), not a "
    "net-of-fee figure.\n"
    "- Mark a contribution in_kind=true only if the form marks that row in-kind; else false.\n"
    "- Ignore blank placeholder rows and any itemized-list SUBTOTAL/TOTAL summary line (do not "
    "transcribe a 'Total' line as a data row).\n"
    "- Transcribe the numbered COVER-block figures into: contributions_under_500 (2025 1a / older "
    "line 1), contributions_itemized (2025 1b / older line 2 'total received from Form A'), "
    "expenditures_under_500 (2025 2a / older line 3), expenditures_itemized (2025 2b / older line 4 "
    "'total expenditures from Form B'), and ending_balance (older line 5, else null). If the cover "
    "prints an explicit grand total line for a side, also give total_contributions / "
    "total_expenditures; else null. Use null for any cover figure that is blank or illegible.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"contributions_under_500":"..","contributions_itemized":"..","total_contributions":"..",'
    '"expenditures_under_500":"..","expenditures_itemized":"..","total_expenditures":"..",'
    '"ending_balance":".."}'
)


def _did8(path, page_range):
    return hashlib.sha1(f"{path}|{page_range}".encode("utf-8")).hexdigest()[:8]


def _parse_ranges(page_range):
    """'3-4' -> [(3,4)]; '9-10,15-16,19-20' -> [(9,10),(15,16),(19,20)]; '11' -> [(11,11)];
    '' -> None (render the whole PDF)."""
    pr = (page_range or "").strip()
    if not pr:
        return None
    spans = []
    for chunk in pr.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            a, b = chunk.split("-", 1)
            spans.append((int(a), int(b)))
        else:
            spans.append((int(chunk), int(chunk)))
    return spans


def _render(doc: Path, page_range):
    """Rasterize the requested page span(s) via pdftoppm into the working dir (never /tmp). For a
    compilation, only that candidate's pages are rendered; blank page_range -> the whole PDF."""
    out = VISION_DIR / "_tmp"
    if out.exists():
        for f in out.glob("p*.jpg"):
            f.unlink()
    out.mkdir(parents=True, exist_ok=True)
    stem = str(out / "p")
    spans = _parse_ranges(page_range)
    if spans is None:
        subprocess.run(["pdftoppm", "-jpeg", "-r", str(DPI), str(doc), stem],
                       check=True, capture_output=True)
    else:
        for a, b in spans:
            subprocess.run(["pdftoppm", "-jpeg", "-r", str(DPI), "-f", str(a), "-l", str(b),
                            str(doc), stem], check=True, capture_output=True)
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


def _targets():
    """(doc8, path, page_range, label) for every in-scope index row (all handwritten scans)."""
    out = []
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        for ix in csv.DictReader(fh):
            if (ix.get("candidate") or "").strip() == UNIDENTIFIED:
                continue
            pr = ix.get("page_range", "")
            out.append((_did8(ix["path"], pr), ix["path"], pr,
                        f"{ix.get('candidate','')} {ix.get('election_year','')}"))
    return out


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    want = set(argv)
    targets = [t for t in _targets() if not want or t[0] in want]
    tin = tout = done = pages = 0
    for doc8, rel, pr, label in targets:
        cache = VISION_DIR / f"{doc8}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        try:
            imgs = _render(pdf, pr)             # render inside try: one bad file never aborts batch
            parsed, i, o = _call(key, imgs)
        except Exception as e:
            print(f"  SKIP {doc8} ({type(e).__name__}: {str(e)[:90]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        pages += len(imgs)
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8} [{label} pp={pr or 'all'}] pages={len(imgs)} "
              f"contrib={len(parsed.get('contributions',[]))} "
              f"expend={len(parsed.get('expenditures',[]))} tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15   # Sonnet list price 2026: $3/Mtok in, $15/Mtok out
    print(f"\nfilings vision-processed this run: {done} | pages={pages} | input_tok={tin} "
          f"output_tok={tout} | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
