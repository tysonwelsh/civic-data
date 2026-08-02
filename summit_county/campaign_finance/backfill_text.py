#!/usr/bin/env python3
"""backfill_text.py — build the `text/` sidecars and record HOW each one was made.

For every `raw/<year>/*.pdf`:
  1. `pdftotext -layout` first. If the PDF carries a usable text layer (>=50 alphanumerics)
     that sidecar is kept. Summit's scans are frequently pre-OCR'd by the clerk's scanner, so
     "has a text layer" does NOT mean "born-digital" — `format` is decided separately by
     build_index.py from the raster-image probe.
  2. Otherwise `pdftoppm -r 300 -png` + `tesseract` per page.

Writes `text_extraction.csv` (the manifest build_index.py reads for `extraction_method`).
Idempotent; `--force` re-extracts everything (slow — the OCR pass is several minutes).

    python3 summit_county/campaign_finance/backfill_text.py [--force]
"""
from __future__ import annotations

import csv
import glob
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_ALNUM = 50


def alnum(s: str) -> int:
    return len(re.sub(r"[^A-Za-z0-9]", "", s))


def main(force=False):
    rows = []
    for pdf in sorted(glob.glob(os.path.join(HERE, "raw", "*", "*.pdf"))):
        stem = os.path.splitext(os.path.basename(pdf))[0]
        out = os.path.join(HERE, "text", stem + ".txt")
        rel = os.path.relpath(pdf, HERE)
        native = subprocess.run(["pdftotext", "-layout", pdf, "-"],
                                capture_output=True, text=True, timeout=180).stdout
        if alnum(native) >= MIN_ALNUM:
            method = "pdftotext -layout"
            text = native
        else:
            method = "tesseract OCR (pdftoppm 300dpi)"
            with tempfile.TemporaryDirectory() as td:
                subprocess.run(["pdftoppm", "-r", "300", "-png", pdf,
                                os.path.join(td, "pg")], timeout=900)
                parts = []
                for png in sorted(glob.glob(os.path.join(td, "pg*.png"))):
                    parts.append(subprocess.run(["tesseract", png, "stdout"],
                                                capture_output=True, text=True,
                                                timeout=600).stdout)
                text = "".join(parts)
        if force or not os.path.exists(out):
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as f:
                f.write(text)
        rows.append(dict(path=rel, text_path=os.path.relpath(out, HERE),
                         extraction_method=method,
                         native_text_alnum=str(alnum(native)),
                         sidecar_alnum=str(alnum(open(out, errors="replace").read()))))
    with open(os.path.join(HERE, "text_extraction.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "text_path", "extraction_method",
                                          "native_text_alnum", "sidecar_alnum"])
        w.writeheader()
        w.writerows(rows)
    n_ocr = sum(1 for r in rows if r["extraction_method"].startswith("tesseract"))
    print(f"{len(rows)} sidecars   pdftotext {len(rows) - n_ocr}   tesseract {n_ocr}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
