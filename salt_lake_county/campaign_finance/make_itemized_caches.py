#!/usr/bin/env python3
"""make_itemized_caches.py — merge ITEMIZED Schedule A/B transcription records into the
existing `vision/<key>.json` stated-totals caches, IN PLACE.

WHY IN PLACE. The 2026-08-01/02 totals tranche deliberately shipped every cache with empty
`contributions` / `expenditures` lists (CLAUDE.md: "a later itemization tranche can fill them
without a schema change"). Wave B2 (2026-08-02) fills them. This script is the ONE place the
itemization provenance stamp and the geometry conversion happen, exactly as
`make_vision_caches.py` is the one place the totals stamp happens.

DISCIPLINE
  * The stated-totals half of a cache is NEVER touched — not `total_*`, not `aggregate`,
    not `cover`, not `confidence`, not the existing `_meta` keys. Only the two row lists and
    a new `_meta.itemized` block are written. A cache with no matching record is left byte-
    identical.
  * Nothing is computed from the rows here. Reconciliation verdicts come from the
    TRANSCRIBER (who had the page in hand and the printed subtotals); this script copies them
    verbatim. `build_finance.py` sums the rows for `itemized_*`, and that sum is a report of
    what was transcribed, never a substitute for a figure the form printed.
  * Idempotent: re-running the same records reproduces the same caches.

GEOMETRY (SCHEMA.md 2a). Rows may arrive with a pixel box
`p<page>[(landscape,rot-90)]:x,y,w,h@<dpi>dpi` or already as `pct:x,y,w,h@p<page>`. Pixel
boxes are converted to the durable `pct:` form against the page's TRUE size (`pdfinfo -f/-l`),
undoing any declared rotation so the percentages are of the page as poppler renders it.
The verbatim pixel string is preserved in `geometry_px` — a converted pointer must always be
traceable back to what the transcriber actually measured.

A pilot-era caveat this handles honestly: some first-wave boxes are ESTIMATES that overflow
their declared frame (recorded in `_audits/cf-calibration-suite/runs.md`). For each
(filing, page, orientation, dpi) group the script picks the first CANDIDATE FRAME that
contains every box in the group; if none does, it clamps to [0,100] and marks the row
`geometry_fit: "clamped"` so a consumer can tell a measured pointer from a drifted one.
Never silently rescaled.

Usage:
    python3 make_itemized_caches.py <records_dir> [--dry-run]
                                    [--wave STR] [--date YYYY-MM-DD]
"""
import csv
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "scripts", "campaign_finance")))
import vision_lib as VL  # noqa: E402

VISION = os.path.join(HERE, "vision")
WAVE = "itemized-vision(claude-opus-5; 2026-08-02 wave B2)"
DATE = "2026-08-02"

_PX = re.compile(r"^p(\d+)(?:\(([^)]*)\))?:x(-?\d+),y(-?\d+),w(\d+),h(\d+)@(\d+)dpi$")
_PCT = re.compile(r"^pct:")

CONTRIB_KEYS = ("line_no", "date", "donor_raw", "donor_city", "donor_state", "amount",
                "in_kind", "needs_review", "confidence", "cell_confidence", "verified",
                "geometry", "geometry_px", "geometry_fit", "note")
EXPEND_KEYS = ("line_no", "date", "vendor_raw", "purpose", "amount",
               "in_kind", "needs_review", "confidence", "cell_confidence", "verified",
               "geometry", "geometry_px", "geometry_fit", "note")

_pagesize_cache = {}


def page_size_pts(pdf_path, page):
    """(width_pts, height_pts) of ONE page, measured — never assumed to be letter."""
    key = (pdf_path, page)
    if key in _pagesize_cache:
        return _pagesize_cache[key]
    out = subprocess.run(["pdfinfo", "-f", str(page), "-l", str(page), pdf_path],
                         capture_output=True, text=True).stdout
    m = re.search(r"Page\s+%d size:\s+([\d.]+) x ([\d.]+)" % page, out)
    if not m:
        m = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", out)
    val = (float(m.group(1)), float(m.group(2))) if m else None
    _pagesize_cache[key] = val
    return val


def _frames(w_pts, h_pts, dpi, rot):
    """Candidate (frame_w, frame_h, dpi_used, rot_used) the transcriber's box may live in.

    ONLY the declared orientation is ever tried — a rotation is never INVENTED to make an
    oversized box fit. (It was, in a first cut, and it silently mapped 55 rows of a plainly
    PORTRAIT page — `20_june_auger_janice06.pdf` p3, verified at the page image — onto the
    wrong axis. An overflowing box is an estimate, and the honest response is to clamp and
    say so, not to reinterpret the page.) The one drift that IS accommodated is a mislabelled
    dpi at the same orientation: `08_jwinder_jan31.pdf` p3 declares 200 dpi but its boxes are
    a 300 dpi frame, which the render-back check confirms. Declared dpi is tried first, so a
    correct declaration is never overridden."""
    out = []
    for d in (dpi, 300, 250, 200, 260, 150, 110):
        W, H = int(round(w_pts * d / 72.0)), int(round(h_pts * d / 72.0))
        fw, fh = (H, W) if rot else (W, H)
        if (fw, fh, d, rot) not in out:
            out.append((fw, fh, d, rot))
    return out


def _to_pct(x, y, w, h, frame_w, frame_h, rot, page_w_px, page_h_px):
    """Rotated-image box -> page-space box -> percentages of the page.

    `-rotate -90` (ImageMagick, counter-clockwise): original (x,y) lands at (y, W-1-x), so a
    rotated box (x',y',w',h') came from page box (W-y'-h', x', h', w').
    `-rotate +90` (clockwise): original (x,y) lands at (H-1-y, x), so the page box is
    (y', H-x'-w', h', w')."""
    if rot == -90:
        px, py, pw, ph = page_w_px - y - h, x, h, w
    elif rot == 90:
        px, py, pw, ph = y, page_h_px - x - w, h, w
    else:
        px, py, pw, ph = x, y, w, h
    return (100.0 * px / page_w_px, 100.0 * py / page_h_px,
            100.0 * pw / page_w_px, 100.0 * ph / page_h_px)


def convert_geometry(rows, pdf_path):
    """Stamp `geometry` (pct:) / `geometry_px` / `geometry_fit` on every row that carries a
    pixel box. Rows already in `pct:` form, or with no geometry, pass through untouched."""
    groups = defaultdict(list)
    for r in rows:
        g = (r.get("geometry") or "").strip()
        if not g or _PCT.match(g):
            continue
        m = _PX.match(g)
        if not m:
            r["geometry_fit"] = "unparsed"
            continue
        page = int(m.group(1))
        tag = m.group(2) or ""
        rot = -90 if "rot-90" in tag else (90 if "rot+90" in tag else 0)
        box = tuple(int(v) for v in m.group(3, 4, 5, 6))
        dpi = int(m.group(7))
        groups[(page, rot, dpi)].append((r, box))

    stats = {"converted": 0, "clamped": 0, "unparsed": 0, "no_pagesize": 0}
    for (page, rot, dpi), items in groups.items():
        size = page_size_pts(pdf_path, page)
        if not size:
            for r, _ in items:
                r["geometry_fit"] = "no-page-size"
            stats["no_pagesize"] += len(items)
            continue
        w_pts, h_pts = size
        maxx = max(b[0] + b[2] for _, b in items)
        maxy = max(b[1] + b[3] for _, b in items)
        chosen = None
        for fw, fh, d, rr in _frames(w_pts, h_pts, dpi, rot):
            if maxx <= fw and maxy <= fh:
                chosen = (fw, fh, d, rr)
                break
        clamped = chosen is None
        if clamped:                      # honest fallback: declared frame + clamp, flagged
            d, rr = dpi, rot
            W, H = int(round(w_pts * d / 72.0)), int(round(h_pts * d / 72.0))
            chosen = ((H, W, d, rr) if rr else (W, H, d, rr))
        fw, fh, d, rr = chosen
        page_w_px = int(round(w_pts * d / 72.0))
        page_h_px = int(round(h_pts * d / 72.0))
        for r, (x, y, w, h) in items:
            px, py, pw, ph = _to_pct(x, y, w, h, fw, fh, rr, page_w_px, page_h_px)
            px, py = max(0.0, min(100.0, px)), max(0.0, min(100.0, py))
            pw, ph = max(0.0, min(100.0 - px, pw)), max(0.0, min(100.0 - py, ph))
            r["geometry_px"] = r["geometry"]
            r["geometry"] = "pct:%.2f,%.2f,%.2f,%.2f@p%d" % (px, py, pw, ph, page)
            r["geometry_fit"] = "clamped" if clamped else (
                "measured" if (d, rr) == (dpi, rot) else "refit(%ddpi,rot%d)" % (d, rr))
            stats["clamped" if clamped else "converted"] += 1
    stats["unparsed"] = sum(1 for r in rows if r.get("geometry_fit") == "unparsed")
    return stats


def _clean(row, keys):
    """Keep the declared keys in declared order; drop blanks so a cache stays readable."""
    out = {}
    for k in keys:
        v = row.get(k)
        if v is None or v == "":
            continue
        out[k] = v
    return out


def merge(rec, cache, pdf_path, wave, date):
    crows = list(rec.get("contributions") or [])
    erows = list(rec.get("expenditures") or [])
    gstats = convert_geometry(crows + erows, pdf_path)
    cache["contributions"] = [_clean(r, CONTRIB_KEYS) for r in crows]
    cache["expenditures"] = [_clean(r, EXPEND_KEYS) for r in erows]
    it = {
        # A record may DECLARE its own wave — the 24 filings promoted from the opus pilot
        # are not wave-B2 transcriptions and must not be stamped as if they were.
        "wave": rec.get("wave") or wave,
        "transcribed_date": date,
        "pages_read": rec.get("pages_read") or [],
        "itemized_pages_A": rec.get("itemized_pages_A", ""),
        "itemized_pages_B": rec.get("itemized_pages_B", ""),
        "sides": rec.get("sides") or {},
        "withheld_reason": rec.get("withheld_reason") or {},
        "recon": rec.get("recon") or {},
        "page_subtotal_gates": rec.get("page_subtotal_gates", ""),
        "escalations": rec.get("escalations", 0),
        "escalation_note": rec.get("escalation_note", ""),
        "n_contrib_rows": len(crows),
        "n_expend_rows": len(erows),
        "geometry": dict(gstats, provenance=rec.get("geometry_provenance", "")),
        "notes": rec.get("notes", ""),
    }
    cache.setdefault("_meta", {})["itemized"] = it
    return it


def main(rec_dir, dry=False, wave=None, date=None):
    wave, date = wave or WAVE, date or DATE
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        idx = {r["path"] for r in csv.DictReader(fh)}
    seen, written, skipped, partial = set(), 0, [], []
    tot_c = tot_e = 0
    for name in sorted(os.listdir(rec_dir)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        # A transcription agent may be REWRITING its whole record file at this instant
        # (the brief tells them to re-save every ~6 filings). A half-written file must
        # never abort the checkpoint — skip it loudly; the next checkpoint picks it up.
        try:
            recs = json.load(open(os.path.join(rec_dir, name)))
        except json.JSONDecodeError as e:
            partial.append(f"{name} ({e.msg} at char {e.pos})")
            continue
        for rec in recs:
            ip = rec["index_path"]
            if ip not in idx:
                raise SystemExit(f"{name}: {ip} is not an index.csv path")
            key = VL.cache_key(ip)
            if rec.get("key") and rec["key"] != key:
                raise SystemExit(f"{name}: key mismatch for {ip}: {rec['key']} != {key}")
            if key in seen:
                raise SystemExit(f"{name}: duplicate record for {ip} (dedupe before running)")
            seen.add(key)
            cpath = os.path.join(VISION, key + ".json")
            if not os.path.exists(cpath):
                skipped.append(ip)
                continue
            cache = json.load(open(cpath))
            it = merge(rec, cache, os.path.join(HERE, ip), wave, date)
            tot_c += it["n_contrib_rows"]
            tot_e += it["n_expend_rows"]
            if not dry:
                with open(cpath, "w") as fh:
                    json.dump(cache, fh, indent=1, sort_keys=False)
                    fh.write("\n")
            written += 1
    print(f"{'would merge' if dry else 'merged'} itemized rows into {written} caches "
          f"({tot_c} contribution rows, {tot_e} expenditure rows)")
    if partial:
        print(f"SKIPPED {len(partial)} record file(s) mid-write (agent re-saving) — "
              f"they merge at the next checkpoint: {partial}")
    if skipped:
        print(f"NO STATED-TOTALS CACHE for {len(skipped)} record(s) — not created here: {skipped[:5]}")


def _opt(name):
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == name and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(name + "="):
            return a.split("=", 1)[1]
    return None


if __name__ == "__main__":
    _flagvals = {v for n in ("--wave", "--date") for v in ([_opt(n)] if _opt(n) else [])}
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a not in _flagvals]
    if not args:
        print(__doc__)
        sys.exit(2)
    main(args[0], dry="--dry-run" in sys.argv, wave=_opt("--wave"), date=_opt("--date"))
