#!/usr/bin/env python3
"""extract_packet_text.py — text sidecars for stored agenda-packet PDFs
(REFACTOR_PLAN 5.6; feeds cities.db `document.has_text` + `fts_packet`).

    python3 scripts/extract_packet_text.py <slug> [...] | --all

For every packets/index.csv row whose `path` resolves to a PDF on disk:
`pdftotext -layout` → packets/text/<stem>.txt. IDEMPOTENT (existing sidecars are
skipped) — safe to re-run after every packet fetch. Honesty rules:
- a sidecar is kept only if it carries ≥200 chars of real text; image-only PDFs
  yield no sidecar and are logged (vision/OCR is the documented path for those);
- every outcome lands in packets/text/_extraction_log.csv
  (stem, bytes, chars, status ∈ extracted/image_only/too_big/error/skipped-exists);
- raw PDFs and index.csv are never modified.
Files over 120 MB are skipped (too_big) — bundle scans, not parseable staff text.
"""
import csv
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cities import DIRS, SLUGS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_BYTES = 120 * 1024 * 1024
MIN_CHARS = 200


def resolve(cdir, rel):
    for base in (os.path.join(ROOT, cdir, "packets", rel),
                 os.path.join(ROOT, cdir, rel)):
        if os.path.exists(base):
            return base
    return None


def process_city(slug):
    cdir = DIRS[slug]
    idx = os.path.join(ROOT, cdir, "packets", "index.csv")
    if not os.path.exists(idx):
        return
    tdir = os.path.join(ROOT, cdir, "packets", "text")
    counts = {}
    log_rows = []
    for r in csv.DictReader(open(idx, encoding="utf-8-sig")):
        rel = (r.get("path") or "").strip()
        if not rel or not rel.lower().endswith(".pdf"):
            continue
        src = resolve(cdir, rel)
        if not src:
            continue
        stem = os.path.splitext(os.path.basename(rel))[0]
        out = os.path.join(tdir, stem + ".txt")
        size = os.path.getsize(src)
        if os.path.exists(out):
            status, chars = "skipped-exists", len(open(out, errors="replace").read())
        elif size > MAX_BYTES:
            status, chars = "too_big", 0
        else:
            os.makedirs(tdir, exist_ok=True)
            p = subprocess.run(["pdftotext", "-layout", src, out],
                               capture_output=True, text=True)
            if p.returncode != 0 or not os.path.exists(out):
                status, chars = "error", 0
                if os.path.exists(out):
                    os.remove(out)
            else:
                chars = len(open(out, errors="replace").read().strip())
                if chars < MIN_CHARS:
                    os.remove(out)
                    status = "image_only"
                else:
                    status = "extracted"
        counts[status] = counts.get(status, 0) + 1
        log_rows.append((stem, size, chars, status))
    if log_rows:
        os.makedirs(tdir, exist_ok=True)
        with open(os.path.join(tdir, "_extraction_log.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["stem", "bytes", "chars", "status"])
            w.writerows(log_rows)
    print("%-13s %s" % (slug, counts or "no stored pdfs"), flush=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    slugs = SLUGS if "--all" in sys.argv else args
    if not slugs:
        sys.exit(__doc__)
    for s in slugs:
        process_city(s)


if __name__ == "__main__":
    main()
