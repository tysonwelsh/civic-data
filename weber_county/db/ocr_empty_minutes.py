#!/usr/bin/env python3
"""OCR the image-only Weber County minutes whose markdown is front-matter only.

WHY (2026-07-26 audit F4): 21 of 533 legislative minutes are Konica-Minolta copier scans
with NO embedded text layer, and the original build had no OCR fallback — so each markdown
is ~307 bytes of front matter and contributes zero motions. `min_09212021.pdf` alone holds
7 named roll calls including `RESOLUTION 36-2021`, and `ordinances/adopted_instruments.csv`
is missing 37 of the 2021 resolution numbers as a direct result.

WHAT: for every index row whose markdown body is empty, render the RETAINED raw PDF with
pdftoppm and OCR it with tesseract, then rewrite the body under the original front matter
(restamping `provenance` to `county_portal_ocr` and `n_chars`). Born-digital rows are never
touched. Idempotent: a row whose body already has text is skipped.

Usage:  python3 db/ocr_empty_minutes.py [--dry-run] [--dpi 200] [--limit N]
"""
import csv, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "legislative", "minutes_index.csv")
DRY = "--dry-run" in sys.argv
DPI = int(sys.argv[sys.argv.index("--dpi") + 1]) if "--dpi" in sys.argv else 200
LIMIT = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10 ** 6


def split_front(text):
    m = re.match(r"---\n(.*?\n)---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else (None, text)


def ocr(pdf):
    """Render then OCR every page; returns text ('' on failure)."""
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(["pdftoppm", "-r", str(DPI), "-png", pdf,
                            os.path.join(td, "pg")], check=True,
                           capture_output=True, timeout=900)
        except Exception as e:
            print("   ! render failed:", os.path.basename(pdf), repr(e)[:70])
            return ""
        parts = []
        for img in sorted(os.listdir(td)):
            if not img.endswith(".png"):
                continue
            try:
                out = subprocess.run(["tesseract", os.path.join(td, img), "stdout"],
                                     capture_output=True, timeout=300)
                parts.append(out.stdout.decode("utf-8", "replace"))
            except Exception as e:
                print("   ! ocr failed:", img, repr(e)[:60])
        return "\n".join(parts)


def main():
    rows = list(csv.DictReader(open(IDX, encoding="utf-8")))
    cols = list(rows[0].keys())
    done = skipped = failed = 0
    for r in rows:
        md = os.path.join(ROOT, r["minutes_md"]) if r.get("minutes_md") else ""
        if not md or not os.path.isfile(md):
            continue
        text = open(md, encoding="utf-8", errors="replace").read()
        front, body = split_front(text)
        if front is None or len(body.strip()) > 200:
            skipped += 1
            continue                                   # already has a real body
        pdf = os.path.join(ROOT, r.get("source_pdf") or "")
        if not os.path.isfile(pdf):
            print("   ! no retained raw:", r["meeting_date"])
            failed += 1
            continue
        if done >= LIMIT:
            break
        got = ocr(pdf)
        if len(got.strip()) < 200:
            print("   ! OCR produced nothing usable:", r["meeting_date"])
            failed += 1
            continue
        newfront = front
        if "provenance:" in newfront:
            newfront = re.sub(r"provenance:.*", "provenance: county_portal_ocr", newfront)
        newfront = newfront.rstrip("\n") + "\nextraction: tesseract OCR (%ddpi, 2026-07-26 backfill)\n" % DPI
        if not DRY:
            open(md, "w", encoding="utf-8").write("---\n" + newfront + "---\n\n" + got.lstrip("\n"))
            r["n_chars"] = str(len(got.strip()))
            r["provenance"] = "county_portal_ocr"
        done += 1
        print("   %s  OCR ok (%d chars)" % (r["meeting_date"], len(got.strip())))
    if not DRY:
        with open(IDX, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    print("OCR'd %d, skipped %d (already had text), failed %d%s"
          % (done, skipped, failed, " [DRY RUN]" if DRY else ""))


if __name__ == "__main__":
    main()
