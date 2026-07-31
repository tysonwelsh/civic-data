#!/usr/bin/env python3
"""vineyard_vision_extract.py — GATED Claude-vision transcription for the Vineyard campaign-finance
filings that did NOT both-reconcile after the born-digital / OCR pass (build_finance.py).

Vineyard-unique twin of the Orem/Logan/Nephi vision extractors. Vineyard is the MIXED case:
  * SCANNED filings (typed scans + handwritten) whose itemized rows OCR to garbage; and
  * BORN-DIGITAL filings whose amounts are BARE numbers / multi-line cells (Welsh, Herring-interim,
    Kuder) that the anti-fabrication $-anchored family (correctly) cannot itemize.
Both get vision. Born-digital filings whose $-rows already reconciled are NOT re-visioned (they stay
born-digital direct) — this extractor only targets the flagged set recorded in filing_totals.csv.

Discipline = the repo anti-fabrication rule: TRANSCRIBE EXACTLY — copy digits, never infer or compute,
mark illegible as null. Cached verbatim to `vision/<doc8>.json` (doc8 = sha1(path)[:8], matching
build_finance._did8); build_finance.py feeds it through the SAME reconciliation as the born-digital /
OCR rows (driver `rows_override_fn`), so a vision filing earns confidence only if it reconciles against
the form's own printed cover totals.

The 4 archive-truncated filings (1-MiB Wayback truncations) are attempted too; pdftoppm typically
renders nothing from a truncated PDF, so they stay honest blanks (never fabricated).

Idempotent: a filing already cached in `vision/` is skipped. Cost is printed at the end.

    python3 vineyard_vision_extract.py            # every flagged, un-cached filing
    python3 vineyard_vision_extract.py <doc8> ... # only these document ids
    python3 vineyard_vision_extract.py --all      # every in-scope filing (ignore reconcile state)
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
MODEL = "claude-sonnet-5"          # confirmed available (used by Orem/Logan/Nephi)
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
    "You are transcribing a Utah municipal campaign-finance filing — the 'Municipal Campaign Financial "
    "Disclosure' form for Vineyard City (Utah Code 10-3-208). The page images are ONE candidate's "
    "filing: a COVER page stating totals, plus itemized 'Form A' (contributions) / 'Form B' "
    "(expenditures) pages. Some are born-digital, some are scanned or HANDWRITTEN. Transcribe EXACTLY "
    "what is written/printed.\n"
    "The numbered COVER block is one of three layouts:\n"
    "  2015 form: line1 'Total Contributions of donors who gave more than $50.00 (Form A total)' | "
    "line2 'Aggregate total of contributions of $50.00 or less' | line3 'Total Campaign expenses "
    "(Form B total)' | line4 'Balance'.\n"
    "  2019 form: line1 'Aggregate total of contributions of more than $50.00' | line2 '... of $50.00 "
    "or less' | line3 'Total Contributions (Form A total)' | line4 'Total Campaign expenses (Form B "
    "total)' | line5 'Balance'.\n"
    "  2021/2025 form: 1a 'Aggregate total of contributions under $500.00' | 1b 'Itemized total of "
    "contributions totaling $500.00 or more (Form A total)' | 2a 'Aggregate total of campaign "
    "expenditures under $500.00' | 2b 'Itemized total of campaign expenditures (Form B total)' | "
    "3 'Balance'.\n"
    "The itemized pages: 'Itemized Contribution Report (Form A)' (Date Received / Name of Contributor "
    "and mailing address / Amount of Contribution / Donation type) and 'Itemized Expenditure Report "
    "(Form B)' (Date / Name of Payee / Description / Amount of Expenditure).\n"
    "RULES (strict — this is a legal record):\n"
    "- Copy every dollar amount digit-for-digit exactly as written, including the decimal point. Do "
    "NOT compute, sum, round, or infer any number.\n"
    "- If a digit/character/field is illegible, use null for that field. NEVER guess a value.\n"
    "- For each contribution use the amount the donor actually GAVE (gross), not a net-of-fee figure.\n"
    "- For 'name', give ONLY the contributor/payee name (not the mailing address).\n"
    "- Mark a contribution in_kind=true only if the form marks that row in-kind (Donation type "
    "'In-Kind' / 'In Kind'); else false.\n"
    "- Ignore blank placeholder rows and any itemized-list TOTAL/SUBTOTAL summary line (do not "
    "transcribe a 'Total' line as a data row).\n"
    "- Transcribe the numbered COVER figures into: contributions_itemized (the 'Form A total' = 2015 "
    "line1 / 2019 line3 / 2021 1b), contributions_under_500 (2021 1a / 2019 line2 / 2015 line2 — the "
    "aggregate small-donor figure), expenditures_itemized (the 'Form B total' = 2015/2019 'Total "
    "Campaign expenses' / 2021 2b), expenditures_under_500 (2021 2a, else null), and ending_balance. "
    "Use null for any cover figure that is blank, 'n/a', or illegible.\n"
    "Return ONLY a JSON object, no prose:\n"
    '{"contributions":[{"date":"MM/DD/YYYY","name":"..","amount":"1234.56","in_kind":false}],'
    '"expenditures":[{"date":"MM/DD/YYYY","recipient":"..","purpose":"..","amount":"12.34"}],'
    '"contributions_under_500":"..","contributions_itemized":"..","total_contributions":"..",'
    '"expenditures_under_500":"..","expenditures_itemized":"..","total_expenditures":"..",'
    '"ending_balance":".."}'
)


def _did8(path):
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:8]


def _render(doc: Path):
    out = VISION_DIR / "_tmp"
    if out.exists():
        for f in out.glob("p*.jpg"):
            f.unlink()
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
        raise ValueError("response truncated at max_tokens")
    m = re.search(r"\{.*\}", txt, re.S)
    parsed = json.loads(m.group(0)) if m else {}
    return parsed, u.get("input_tokens", 0), u.get("output_tokens", 0)


def _flagged():
    """doc8 set of filings to (re)transcribe, from the last build's filing_totals.csv:
      * any filing that did NOT both-reconcile; PLUS
      * any BORN-DIGITAL filing that produced itemized rows — Vineyard's fillable form floats the
        donor NAME onto a different text line than the amount, so the born-digital direct parse
        reconciles the AMOUNTS but mangles donor_raw (captures the address line); vision restores
        correct donor identity. Born-digital NIL filings (0 rows) stay born-digital direct."""
    ft = HERE / "filing_totals.csv"
    if not ft.exists():
        return None
    fmt = {r["path"]: r.get("format", "") for r in csv.DictReader(open(HERE / "index.csv", newline=""))}
    flagged = set()
    for r in csv.DictReader(open(ft, newline="")):
        both = r["reconciles_contrib"] == "True" and r["reconciles_expend"] == "True"
        has_rows = (r["n_contrib_rows"] not in ("", "0")) or (r["n_expend_rows"] not in ("", "0"))
        born = fmt.get(r["source_filing"], "") == "text"
        if (not both) or (born and has_rows):
            flagged.add(_did8(r["source_filing"]))
    return flagged


def _targets():
    out = []
    with open(HERE / "index.csv", newline="", encoding="utf-8") as fh:
        for ix in csv.DictReader(fh):
            out.append((_did8(ix["path"]), ix["path"],
                        f"{ix.get('candidate','')} {ix.get('election_year','')} {ix.get('filing_type','')}"))
    return out


def main(argv):
    key = _load_key()
    VISION_DIR.mkdir(exist_ok=True)
    take_all = "--all" in argv
    want = {a for a in argv if not a.startswith("--")}
    flagged = None if (take_all or want) else _flagged()
    targets = _targets()
    if want:
        targets = [t for t in targets if t[0] in want]
    elif flagged is not None:
        targets = [t for t in targets if t[0] in flagged]
    tin = tout = done = pages = 0
    for doc8, rel, label in targets:
        cache = VISION_DIR / f"{doc8}.json"
        if cache.exists():
            continue
        pdf = HERE / rel
        if not pdf.exists():
            print("MISSING PDF", rel)
            continue
        try:
            imgs = _render(pdf)
            if not imgs:
                print(f"  SKIP {doc8} [{label}] — pdftoppm rendered 0 pages (truncated?) — honest blank")
                continue
            parsed, i, o = _call(key, imgs)
        except Exception as e:
            print(f"  SKIP {doc8} [{label}] ({type(e).__name__}: {str(e)[:80]}) — not cached, re-run to retry")
            continue
        tin += i
        tout += o
        pages += len(imgs)
        cache.write_text(json.dumps(parsed, indent=1))
        done += 1
        print(f"  vision {doc8} [{label}] pages={len(imgs)} "
              f"contrib={len(parsed.get('contributions',[]))} "
              f"expend={len(parsed.get('expenditures',[]))} tok_in={i} tok_out={o}")
    cost = tin / 1e6 * 3 + tout / 1e6 * 15
    print(f"\nfilings vision-processed this run: {done} | pages={pages} | input_tok={tin} "
          f"output_tok={tout} | approx cost ${cost:.2f} (synchronous list price)")


if __name__ == "__main__":
    main(sys.argv[1:])
