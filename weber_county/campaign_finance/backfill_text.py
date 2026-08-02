#!/usr/bin/env python3
"""backfill_text.py — build the `text/` sidecar layer for weber_county/campaign_finance.

One sidecar per retained raw document, page-delimited by form feed (\\f) so a
consolidated multi-candidate PDF can be split at PAGE granularity later.

Method per file (measured, not guessed from the extension):
  1. `pdftotext -layout` — if the document has a real text layer (>=120 non-space chars),
     that is the sidecar and `format=text`.
  2. otherwise `pdftoppm -r 300 -gray` + `tesseract --psm 6` page by page, and
     `format=scanned`.
A page that yields nothing stays EMPTY — never filled in.

Writes `text_extraction.csv` (the measured manifest index.csv reads):
  path,pages,method,format,chars,per_page_chars

Usage: python3 backfill_text.py [--only <substring>] [--jobs N]
"""
from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
TXT = os.path.join(HERE, "text")
MIN_CHARS_PER_PAGE = 40   # below this on average -> treat as image-only


def n_pages(pdf: str) -> int:
    try:
        out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if line.startswith("Pages:"):
                return int(line.split()[1])
    except Exception:  # noqa: BLE001
        pass
    return 0


def native_text(pdf: str) -> str:
    p = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                       capture_output=True, text=True)
    return p.stdout


def ocr_text(pdf: str, pages: int, only_pages=None) -> str:
    out = []
    with tempfile.TemporaryDirectory() as td:
        for pg in range(1, pages + 1):
            if only_pages is not None and pg not in only_pages:
                out.append(None)
                continue
            stem = os.path.join(td, f"p{pg}")
            subprocess.run(["pdftoppm", "-r", "300", "-gray", "-f", str(pg), "-l", str(pg),
                            "-png", pdf, stem], capture_output=True)
            img = None
            for cand in os.listdir(td):
                if cand.startswith(f"p{pg}-") or cand == f"p{pg}.png":
                    img = os.path.join(td, cand)
                    break
            if not img:
                out.append("")
                continue
            # NOTE: tesseract's stdout sentinel is the literal "stdout", NOT "-"
            # (with "-" it silently writes a file named "-.txt" and returns nothing).
            r = subprocess.run(["tesseract", img, "stdout", "--psm", "6"],
                               capture_output=True, text=True)
            out.append(r.stdout)
            os.unlink(img)
    return "\f".join("" if o is None else o for o in out)


def process(rel: str) -> dict:
    pdf = os.path.join(RAW, rel)
    pages = n_pages(pdf)
    txt = native_text(pdf)
    dense = len(txt.replace(" ", "").replace("\n", "").replace("\f", ""))
    if pages and dense / pages >= MIN_CHARS_PER_PAGE:
        # A consolidated PDF can be MIXED: a few born-digital filings bound together with
        # scanned ones (the 2020/2024 archives are). Native extraction alone would leave
        # those pages silently blank, so OCR exactly the pages the text layer left empty.
        native_pages = txt.split("\f")
        while len(native_pages) < pages:
            native_pages.append("")
        blank = {i + 1 for i, p in enumerate(native_pages)
                 if len(p.replace(" ", "").replace("\n", "")) < MIN_CHARS_PER_PAGE}
        if blank:
            ocr_pages = ocr_text(pdf, pages, only_pages=blank).split("\f")
            merged = [ocr_pages[i] if (i + 1) in blank and ocr_pages[i] not in (None, "None")
                      else native_pages[i] for i in range(pages)]
            txt = "\f".join(x or "" for x in merged)
            method = "pdftotext -layout + tesseract --psm 6 on blank pages"
            fmt = "mixed"
        else:
            method, fmt = "pdftotext -layout", "text"
    else:
        txt = ocr_text(pdf, pages)
        method, fmt = "tesseract --psm 6 (pdftoppm 300dpi gray)", "scanned"
    stem = rel.replace("/", "__").rsplit(".", 1)[0]
    dest = os.path.join(TXT, stem + ".txt")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(txt)
    per_page = "|".join(str(len(p.strip())) for p in txt.split("\f"))
    return dict(path=f"raw/{rel}", text_path=f"text/{stem}.txt", pages=pages,
                method=method, format=fmt, chars=len(txt.strip()), per_page_chars=per_page)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()

    rels = []
    for root, _dirs, names in os.walk(RAW):
        for n in sorted(names):
            if not n.lower().endswith(".pdf"):
                continue
            rel = os.path.relpath(os.path.join(root, n), RAW)
            if a.only and a.only not in rel:
                continue
            rels.append(rel)
    os.makedirs(TXT, exist_ok=True)
    rows = []
    with ProcessPoolExecutor(max_workers=a.jobs) as ex:
        for r in ex.map(process, rels):
            rows.append(r)
            print(f"{r['format']:8} {r['pages']:>4}p {r['chars']:>8}c  {r['path']}", flush=True)

    man = os.path.join(HERE, "text_extraction.csv")
    old = {}
    if os.path.exists(man) and a.only:
        with open(man, encoding="utf-8") as f:
            old = {r["path"]: r for r in csv.DictReader(f)}
    for r in rows:
        old[r["path"]] = r
    with open(man, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "text_path", "pages", "method",
                                          "format", "chars", "per_page_chars"])
        w.writeheader()
        for k in sorted(old):
            w.writerow(old[k])
    print(f"\n{len(rows)} sidecars -> text/ ; manifest {man}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
