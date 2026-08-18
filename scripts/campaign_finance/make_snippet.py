#!/usr/bin/env python3
"""make_snippet.py — resolve a CF itemized row's `geometry` to an image snippet + region URL.

The evidential-anchoring utility for the itemized campaign-finance layer (tranche 3,
2026-08-02): given a row's `geometry` value and its source PDF, emit

  * an IIIF-Image-API-shaped REGION string   ->  <page>/pct:x,y,w,h   (resolution-independent
    percentages of the page — the durable, serve-ready form; IIIF region syntax per
    https://iiif.io/api/image/3.0/#41-region), and
  * optionally a cropped PNG of that region (a "snippet") rendered from the retained raw.

Geometry vocabularies accepted (SCHEMA.md §2a):
  p<page>:l<line>:c<c0>-<c1>   laid-out text span (parser families). Resolved to page
                               coordinates by locating the SAME printed token via
                               `pdftotext -bbox` word geometry — the mapping is
                               occurrence-counted so a value repeated on the page still
                               resolves to the right instance.
  pct:x,y,w,h@p<page>          already-normalized percentages (the preferred stored form
                               for vision rows going forward; wave B2 contract).
  p<page>:x,y,w,h@<dpi>dpi     transitional pixel box from a vision pass; converted to pct
                               via the page's true size (pdfinfo points at 72/inch).
  <Sheet>!<A1>                 spreadsheet cell — NO page image exists; a structured
                               citation is printed instead (honest n/a for imagery).

Default snippet mode is --row: a full-width strip at the value's vertical band (plus
padding) — a row snippet with context beats a tight value box for human verification.
--value crops the tight box instead.

Usage:
  python3 scripts/campaign_finance/make_snippet.py --pdf <raw.pdf> --geometry 'p3:l48:c85-91' \
      [--sidecar <text.txt>] [--out snippet.png] [--dpi 200] [--value]
  python3 scripts/campaign_finance/make_snippet.py --csv <contributions.csv> --row 12 \
      --module <entity>/campaign_finance [--out snippet.png]

With --csv/--row the PDF and sidecar are resolved from the module's index/text conventions
(source_filing is module-relative). Prints the region string either way; --out also writes
the PNG. Read-only with respect to every dataset file.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

PT_PER_INCH = 72.0
SPLASH_MAX_BYTES = 2 ** 31   # poppler splash: rowSize*height must fit int32
SPLASH_BYTES_PER_PX = 3      # RGB8 row stride
SPLASH_SAFETY = 0.95         # stay clear of the exact boundary
ROW_PAD_PCT = 0.6      # vertical padding around the value band, in % of page height
VALUE_PAD_PCT = 0.35


def die(msg):
    sys.exit("make_snippet: " + msg)


# ---------------------------------------------------------------- geometry parsing

RE_SPAN = re.compile(r"^p(\d+):l(\d+):c(\d+)-(\d+)$")
RE_PCT = re.compile(r"^pct:([\d.]+),([\d.]+),([\d.]+),([\d.]+)@p(\d+)$")
RE_PX = re.compile(r"^p(\d+):(\d+),(\d+),(\d+),(\d+)@(\d+)dpi$")
RE_CELL = re.compile(r"^[^!]+![A-Z]+\d+$")


def page_box_pts(pdf, page):
    """(mediabox_width_pts, mediabox_height_pts, rotation_degrees) of one page.

    These are the values pdfinfo prints: the UNROTATED MediaBox plus the page's /Rotate.
    Callers almost always want `page_size_pts` (the RENDERED frame) instead.
    """
    out = subprocess.run(["pdfinfo", "-f", str(page), "-l", str(page), pdf],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r"Page +\d+ +size: +([\d.]+) x ([\d.]+) pts", out)
    if not m:
        m = re.search(r"Page size: +([\d.]+) x ([\d.]+) pts", out)
    if not m:
        die("could not read page size from pdfinfo")
    r = re.search(r"Page +\d+ +rot: +(-?\d+)", out) or re.search(r"Page rot: +(-?\d+)", out)
    rot = int(r.group(1)) % 360 if r else 0
    return float(m.group(1)), float(m.group(2)), rot


def page_size_pts(pdf, page):
    """(width_pts, height_pts) of one page AS POPPLER RENDERS IT — /Rotate APPLIED.

    pdfinfo prints the UNROTATED MediaBox, but every consumer of this function works in
    the RENDERED frame:

      * `pdftoppm` rasterizes with /Rotate applied, and its -x/-y/-W/-H crop window is in
        that rendered raster; and
      * `pdftotext -bbox` emits WORD coordinates in that same rotated frame (only its
        <page> header keeps the unrotated MediaBox — verified against a /Rotate 90
        specimen: a word at unrotated y_top 74.77-96.97 pts on a 612x792 page reports
        xMin/xMax 695.03/717.23, i.e. 792 - y_top, which exceeds the reported page width).

    On a /Rotate 90|270 page the axes are therefore SWAPPED relative to pdfinfo, and a
    `pct:` box measured against the render resolved somewhere else entirely. Swapping
    here fixes the pct, px and span paths at once. On /Rotate 0|180 it is a no-op.
    """
    w, h, rot = page_box_pts(pdf, page)
    return (h, w) if rot in (90, 270) else (w, h)


def bbox_words(pdf, page):
    """[(text, xMin, yMin, xMax, yMax)] for one page from `pdftotext -bbox` (pts,
    origin top-left)."""
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "b.html")
        subprocess.run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), pdf, out],
                       check=True, capture_output=True)
        raw = open(out, encoding="utf-8", errors="replace").read()
    # poppler's -bbox output is xhtml; namespace varies by version — strip it.
    raw = re.sub(r'xmlns="[^"]*"', "", raw, count=1)
    root = ET.fromstring(raw)
    words = []
    for w in root.iter("word"):
        words.append((w.text or "",
                      float(w.get("xMin")), float(w.get("yMin")),
                      float(w.get("xMax")), float(w.get("yMax"))))
    return words


def _norm_token(t):
    return re.sub(r"[^0-9A-Za-z.]", "", t or "")


def resolve_span(pdf, sidecar_text, page, line_1b, c0, c1):
    """Map a layout text span to a pct-of-page box via occurrence-counted token match."""
    lines = sidecar_text.split("\n")
    if line_1b > len(lines):
        die(f"sidecar has {len(lines)} lines; l{line_1b} out of range (wrong sidecar?)")
    line = lines[line_1b - 1]
    token = line[c0:c1].strip()
    if not token:
        die(f"empty span at l{line_1b}:c{c0}-{c1}")
    # which occurrence of this token is ours, counting within THIS PAGE of the sidecar?
    # (sidecar pages are form-feed separated in the file the families read; the module's
    # text/ sidecars keep \f, or '===== PAGE nn =====' markers — handle both.)
    page_texts = re.split(r"\f|=====\s*PAGE\s*\d+\s*=====", sidecar_text)
    page_texts = [p for p in page_texts if p.strip() != ""]
    if page - 1 >= len(page_texts):
        # single-page sidecar or unmarked pages: fall back to the whole text
        page_text = sidecar_text
    else:
        page_text = page_texts[page - 1]
    norm = _norm_token(token)
    # our token's occurrence index within the page, in reading order: normalized-token
    # matches in the page's lines BEFORE our line, plus in our line before c0
    li = _line_index_in_page(page_text, line, line_1b, sidecar_text)
    before = "\n".join(page_text.split("\n")[:li])
    occurrence = sum(1 for t in before.split() if _norm_token(t) == norm) + \
        sum(1 for t in line[:c0].split() if _norm_token(t) == norm)

    words = bbox_words(pdf, page)
    matches = [w for w in words if _norm_token(w[0]) == norm]
    if not matches:
        # try containment (token split across words, e.g. "$" separate)
        matches = [w for w in words if norm and norm in _norm_token(w[0])]
    if not matches:
        die(f"token {token!r} not found in page {page} word geometry")
    w = matches[min(occurrence, len(matches) - 1)]
    pw, ph = page_size_pts(pdf, page)
    x0, y0, x1, y1 = w[1], w[2], w[3], w[4]
    return page, (100 * x0 / pw, 100 * y0 / ph, 100 * (x1 - x0) / pw, 100 * (y1 - y0) / ph)


def _line_index_in_page(page_text, line, line_1b, full_text):
    """Index of our sidecar line within its page's line list (first exact match at or
    after the proportional position; exact-match fallback 0)."""
    plines = page_text.split("\n")
    for i, ln in enumerate(plines):
        if ln == line:
            return i
    return 0


def parse_geometry(geom):
    """-> ('span'|'pct'|'px'|'cell', payload)"""
    g = (geom or "").strip()
    m = RE_SPAN.match(g)
    if m:
        return "span", tuple(int(x) for x in m.groups())
    m = RE_PCT.match(g)
    if m:
        x, y, w, h, p = m.groups()
        return "pct", (int(p), (float(x), float(y), float(w), float(h)))
    m = RE_PX.match(g)
    if m:
        p, x, y, w, h, dpi = (int(v) for v in m.groups())
        return "px", (p, (x, y, w, h), dpi)
    if RE_CELL.match(g):
        return "cell", g
    die(f"unrecognized geometry {geom!r}")


# ---------------------------------------------------------------- output

def region_string(page, pct_box):
    x, y, w, h = pct_box
    return f"{page}/pct:{x:.2f},{y:.2f},{w:.2f},{h:.2f}"


def _fit_dpi(pw_pts, ph_pts, dpi):
    """Clamp `dpi` so the FULL-PAGE raster stays inside poppler's splash allocation guard.

    `pdftoppm -x/-y/-W/-H` crops a window out of a page it still rasterizes WHOLE, so the
    ceiling is set by the page, not by the crop. Splash allocates rowSize*height bytes with
    rowSize = 3*width (RGB8) and guards that product against int32. Past it poppler prints
    "Bogus memory allocation size" to stderr, EXITS 0, and writes an all-white PNG — a
    silent blank that reads as evidence of absence.

    This bites oversized-MediaBox pages, where a scan is placed at ~1 pt per source pixel:
    weber_county 2026_ugd_92078f_f36d6ca9.pdf is 2310 x 3012 pts, so `--dpi 900` asks for a
    28875 x 37650 raster and returns blank (measured 2026-08-18; the same page renders
    normally to 700 dpi, and a letter page holds to 2000 dpi).

    Clamping keeps the requested REGION exactly and only lowers its resolution to the most
    poppler can give, with a printed notice. Returns `dpi` unchanged where it already fits.
    """
    budget = SPLASH_MAX_BYTES / SPLASH_BYTES_PER_PX          # max full-page pixels
    want = (pw_pts / PT_PER_INCH) * (ph_pts / PT_PER_INCH)   # px per dpi^2
    if want <= 0 or want * dpi * dpi < budget:
        return dpi
    fit = int((budget / want) ** 0.5 * SPLASH_SAFETY)
    fit = max(72, fit)
    print(f"dpi clamped {dpi} -> {fit}: a {int(pw_pts / PT_PER_INCH * dpi)} x "
          f"{int(ph_pts / PT_PER_INCH * dpi)} px full-page raster exceeds poppler's "
          f"allocation guard (oversized MediaBox {pw_pts:.0f} x {ph_pts:.0f} pts); "
          f"the region is unchanged, only its resolution")
    return fit


def cut_png(pdf, page, pct_box, out, dpi, row_mode):
    pw_pts, ph_pts = page_size_pts(pdf, page)
    x, y, w, h = pct_box
    pad = ROW_PAD_PCT if row_mode else VALUE_PAD_PCT
    if row_mode:
        x, w = 0.0, 100.0                      # full-width strip: row context
    y = max(0.0, y - pad)
    h = min(100.0 - y, h + 2 * pad)
    if not row_mode:
        x = max(0.0, x - pad)
        w = min(100.0 - x, w + 2 * pad)
    dpi = _fit_dpi(pw_pts, ph_pts, dpi)
    scale = dpi / PT_PER_INCH
    px = {"x": int(x / 100 * pw_pts * scale), "y": int(y / 100 * ph_pts * scale),
          "W": max(1, int(w / 100 * pw_pts * scale)),
          "H": max(1, int(h / 100 * ph_pts * scale))}
    r = subprocess.run(["pdftoppm", "-png", "-r", str(dpi), "-f", str(page), "-l", str(page),
                        "-x", str(px["x"]), "-y", str(px["y"]),
                        "-W", str(px["W"]), "-H", str(px["H"]),
                        "-singlefile", pdf, out[:-4] if out.endswith(".png") else out],
                       check=True, capture_output=True, text=True)
    if "Bogus memory allocation" in (r.stderr or ""):
        # Belt-and-braces: _fit_dpi should have prevented this. Never let a silently
        # BLANK crop out the door — a white PNG reads as evidence of absence.
        die(f"poppler refused the page raster at {dpi} dpi (\"Bogus memory allocation "
            f"size\"); the crop would be BLANK, not empty. Lower --dpi.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf")
    ap.add_argument("--geometry")
    ap.add_argument("--sidecar")
    ap.add_argument("--csv")
    ap.add_argument("--row", type=int, help="1-based DATA row in --csv")
    ap.add_argument("--module", help="entity campaign_finance dir (for --csv path resolution)")
    ap.add_argument("--out")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--value", action="store_true", help="tight value box (default: row strip)")
    a = ap.parse_args()

    geom, pdf, sidecar = a.geometry, a.pdf, a.sidecar
    if a.csv:
        rows = list(csv.DictReader(open(a.csv)))
        if not a.row or a.row > len(rows):
            die(f"--row must be 1..{len(rows)}")
        r = rows[a.row - 1]
        geom = r.get("geometry", "")
        mod = a.module or os.path.dirname(a.csv)
        pdf = os.path.join(mod, r["source_filing"])
        if not sidecar:
            # authoritative mapping first: the module's text_extraction.csv manifest
            man = os.path.join(mod, "text_extraction.csv")
            if os.path.exists(man):
                for m in csv.DictReader(open(man)):
                    if m.get("raw_path") == r["source_filing"] and m.get("text_path"):
                        sidecar = os.path.join(mod, m["text_path"])
                        break
            if not sidecar:
                guess = os.path.join(mod, "text",
                                     os.path.splitext(os.path.basename(r["source_filing"]))[0] + ".txt")
                sidecar = guess if os.path.exists(guess) else None
        print(f"row {a.row}: {r.get('donor_raw') or r.get('vendor_raw')!r} "
              f"amount={r.get('amount')!r} geometry={geom!r}")
    if not geom or not pdf:
        die("need --geometry and --pdf (or --csv/--row/--module)")

    kind, payload = parse_geometry(geom)

    # MULTI-FILE FILINGS (washco_split): source_filing is the group PRIMARY, but the row
    # may have been parsed from a sibling part (the Contributions/Expenditures ledger),
    # and Phase-A geometry does not stamp the part. Resolve by SPAN-CONTENT VALIDATION:
    # accept the candidate sidecar (and its raw) only where the span text reproduces the
    # row's own amount — self-verifying, never guessed. (Family-level part stamping is
    # the queued durable fix.)
    if a.csv and kind == "span":
        page_, l_, c0_, c1_ = payload
        want = _norm_token(r.get("amount", ""))
        mod = a.module or os.path.dirname(a.csv)
        man = os.path.join(mod, "text_extraction.csv")
        cands = []
        if sidecar:
            cands.append((sidecar, pdf))
        if os.path.exists(man) and want:
            pdir = os.path.dirname(r["source_filing"])
            surname = (r.get("candidate", "").split() or [""])[-1].lower()
            for m in csv.DictReader(open(man)):
                if os.path.dirname(m.get("raw_path", "")) == pdir and \
                        surname in os.path.basename(m.get("raw_path", "")).lower():
                    cands.append((os.path.join(mod, m["text_path"]),
                                  os.path.join(mod, m["raw_path"])))
        # line-origin tolerance: some Phase-A families emitted line numbers off by one
        # vs the stored sidecar (summit specimen: geometry l48, sidecar line 47 —
        # evidence-cited family bug, queued). Trying l, l-1, l+1 is SAFE because a
        # candidate is only accepted when the span reproduces the row's own amount.
        hit = None
        for sc, sp in cands:
            if not os.path.exists(sc):
                continue
            lns = open(sc, encoding="utf-8", errors="replace").read().split("\n")
            for dl in (0, -1, 1):
                li = l_ + dl
                if 1 <= li <= len(lns) and want and \
                        want in _norm_token(lns[li - 1][c0_:c1_]):
                    hit = (sc, sp, li)
                    break
            if hit:
                break
        if hit:
            sc, sp, li = hit
            if (sc, sp) != (sidecar, pdf):
                print(f"part-resolved: geometry validates against "
                      f"{os.path.basename(sp)} (group sibling of the primary)")
            if li != l_:
                print(f"line-origin corrected: l{l_} -> sidecar line {li} "
                      f"(validated by amount match; family off-by-one, queued)")
            sidecar, pdf = sc, sp
            payload = (page_, li, c0_, c1_)
        elif cands and want:
            die("span does not reproduce the row amount in any group part "
                "(tried l, l±1): " + ", ".join(os.path.basename(s) for s, _ in cands))

    if kind == "cell":
        print(f"structured citation: {payload} in {pdf} — spreadsheet cell; no page image "
              f"exists (honest n/a for imagery)")
        return
    if kind == "span":
        page, l, c0, c1 = payload
        if not sidecar:
            die("span geometry needs the module text sidecar (--sidecar)")
        text = open(sidecar, encoding="utf-8", errors="replace").read()
        page, box = resolve_span(pdf, text, page, l, c0, c1)
    elif kind == "pct":
        page, box = payload
    else:  # px
        page, (x, y, w, h), dpi = payload
        pw, ph = page_size_pts(pdf, page)
        s = dpi / PT_PER_INCH
        box = (100 * x / (pw * s), 100 * y / (ph * s), 100 * w / (pw * s), 100 * h / (ph * s))

    print("region:", region_string(page, box), f"  (source: {os.path.basename(pdf)})")
    if a.out:
        cut_png(pdf, page, box, a.out, a.dpi, row_mode=not a.value)
        print("snippet:", a.out)


if __name__ == "__main__":
    main()
