#!/usr/bin/env python3
"""rowbands.py — printed-rule row banding for scanned campaign-finance ledger pages.

PROMOTED 2026-08-18 from the summit/weber wave kits (`_backups/2026-08-14-tranche3/
summit-b/rowbands.py`, byte-identical weber copy) for the utah_county Phase B wave, with
the filed [DEBT] defects FIXED (TODO 2026-08-17 entry; wave brief §3b). The backup copies
are frozen wave records and are deliberately NOT updated.

WHY. County CF schedule pages are printed grids or underline forms: every data row sits
on/next to a printed rule. Detecting those rules gives two things vision alone does not:

  1. a **ROW-COUNT gate** — an independent count of how many data bands the page
     physically has, which catches a dropped or duplicated line that a sum can hide;
  2. **measured `pct:` geometry** for every transcribed row, from the page itself.

It is a MEASURING instrument only: it never reads a value and never decides what a row
says. A page whose rules it cannot find returns no bands, and the transcriber falls back
to a declared table frame — recorded as such, never as a measurement.

THE 2026-08-18 FIXES (each was a real failure on wave pages):

  * **RAW-frame coordinates.** The old tool measured on a DESKEWED copy while
    `make_snippet.py` crops the RAW poppler render — a full row of drift on skewed scans.
    Detection still happens on the deskewed copy (that is what makes a skewed rule land on
    one pixel row), but every reported coordinate is now mapped BACK to the raw render
    frame at the rule's own x-extent midpoint, so `pct:` boxes built from these numbers
    aim at the page as poppler renders it. `skew_deg` and `skew_drift_pct` (end-to-end
    y-drift of a full-width rule, pct of page height) are reported so a consumer can pad
    a box that must CONTAIN its whole row.
  * **Thickness discrimination.** A printed rule is 2–4 px at 200 dpi. A typed text line,
    a clerk's redaction bar, a shaded spacer band, and a solid black notice box are all
    DARK RUNS MANY PIXELS THICK, and the old tool returned them as rules (utah: redaction
    bars and the black "PLEASE NOTE" box). Runs thicker than `max_rule_px` are now
    classified as BARS, reported separately (`bars_pct`), and never counted as rules. On
    request (`--text-lines`) the thick bands are reported as `text_bands_pct` — a drafting
    aid for rule-less TYPED sheets, never presented as printed rules.
  * **Fill/segment discrimination.** Thickness alone does not catch a TEXT BASELINE, which
    can be as thin as a rule (the typed-sheet defect: baselines registered as rules, "the
    real grid is every other one"). A printed rule is a few long segments — ONE on a boxed
    grid, one per column on an underline form; a line of type is dozens of glyph
    fragments. Measured on real wave pages (2026-08-18): printed rules `fill` ≥ 0.88 with
    ≤ 6 segments (utah underline Schedule A: 4 segments, fill 0.95; weber boxed grid: 1
    segment, fill 1.00), text baselines fill 0.25–0.70 with 8–40 segments. A run is a rule
    only if `fill >= min_fill` AND `n_segments <= max_segments`.
  * **Data-band subsequence.** The old tool returned the header band and the shaded/spacer
    band as data rows, which put every stored row one or two rows early — the single
    commonest cause of the 18 weber geometry withdrawals. `data_bands_pct` now reports the
    longest consecutive run of bands at a REGULAR pitch, i.e. the printed data grid with
    the header and spacer bands trimmed. It is a proposal to be proved by crop, never a
    substitute for the two-crop proof.
  * **Skew-robust angle search.** The old angle score was the single sharpest projection
    row, which a redaction bar or black box dominates at EVERY angle, so the search could
    return an arbitrary angle and the grid was lost (~0.4° skew was enough). The score is
    now the summed coverage of THIN runs only — bars cancel out of the comparison.
  * **Column-restricted scan** (`--col x0,x1`, raw-frame pct): scan for dark runs only in
    one column's own band on the other axis — the recovery that worked on weber when a
    text-dense sheet drowned the full-width scan. Coverage is then measured relative to
    the band width.
  * **Per-rule segments.** Each detected rule reports its dark x-extent and its contiguous
    segments (`h_rules_detail`), so an underline form's four per-column underlines (the
    utah legacy Schedule A/B shape) yield the column bands directly.

ADDED 2026-08-19 (both found by utah wave chunk agents, on real pages):

  * **Thickness is the MEDIAN across a run's own columns, not its maximum.** Where a filer's
    heavy ink or a pen stroke CROSSES a printed rule, the run thickens locally, its overall
    height exceeds `max_rule_px`, and the rule was misfiled as a BAR — so the row grid silently
    lost a line and every band below it shifted. Hit four times in one chunk; on one page it
    decided row 1 itself (the two candidate frames rendered `22.17` vs `2500.00`). A printed
    rule is thin along MOST of its length even when ink crosses part of it, so the median
    column-height separates it from a genuine bar, which is thick throughout. Verified to leave
    every previously-proven specimen byte-identical (weber's audited box `pct:85.23,16.62,10.66,
    3.17@p2` still resolves to y=16.62 h=3.18 with column bands 4.72/12.87/43.17/85.24/95.90).


  * **Adaptive VERTICAL threshold.** The column-rule scan was fixed at 0.60 of the table's
    y-extent while the row scan had a relaxing ladder. On a filer's boxed LANDSCAPE
    attachment ledger that returned **28 row rules and ZERO column rules**, because a
    printed column rule commonly stops at a header band, breaks at a spanning cell, or
    fades on a scan. It now relaxes 0.60 → 0.18, **strict first, stopping at the first
    threshold that yields a real column structure**, and reports `v_cover_used`.
    ⚠ It is deliberately NOT scored by pitch regularity the way the row rules are: table
    columns are unequal by design, so "most regular spacing" prefers junk — a
    regularity-scored ladder was tried and replaced weber's correct column bands with a run
    of text stems 0.6 pct apart. Strict-wins is what preserves them.

ADDED 2026-08-20 — **DEFECT 7 and its two siblings** (TODO [DEBT] filed 2026-08-20 off the
utah wave; reproducer `utah_county/.../2026_Taylor_Fox_Redacted.pdf` p3, where the tool
returned **15 rules for a 15-row grid** — dropping the TOP one — and **1 of 5** column
rules). This is the dangerous class: a ledger opened at row 2 STILL SUMS, so the side
reconciles to the cent while every entry is filed against the wrong printed line. It was
contained only by the B2 contract's mandatory two-crop proof.

  * **Background-normalised dark-run scan** (`bg_norm_mask`) — subtract a Gaussian blur of
    the page from the page, then threshold, UNIONed with the old absolute threshold. On a
    faded photocopy a real rule is only ~20-40 grey levels darker than its own paper, so a
    single absolute cut catches it on some pixel rows and misses it on others; the run then
    SPLITS and each half fails the `fill` gate that rejects lines of type. Measured on the
    reproducer: the top rule's dark run is 441-464 px, rows 455-458 fall under the absolute
    threshold, and the two halves score fill 0.71 / 0.40 against `min_fill` 0.80 — so the
    rule vanished. The ladder is now run on BOTH masks and the more regular grid wins (ties
    to raw), so a page the old mask read correctly keeps its exact answer.
  * **Per-band column scan** (`_v_per_band`) — the vertical half. The reproducer's column
    rules SHEAR: the Amount column's right rule runs at 87.9 pct of page width beside row 1
    and 91.1 pct beside row 15, because the page is a curved photocopy. A global deskew is a
    rigid rotation and cannot straighten a shear, so the whole-height projection accumulates
    nothing. Scanning each row band separately recovers all five; `v_shear_pct` and
    `v_rules_per_band_pct` report the drift, because a single median x is wrong by half the
    shear at each end. Taken ONLY when the projection failed (< 3 rules).
  * **Off-grid rules** (`split_off_grid`) — sibling 1: the tool proposed a **subtotal
    underline / footer box as a data band** (Voeks p2, Forbush p2). Those are real printed
    rules that are not grid rules, and they are separable by width: Forbush p2's 16 grid
    rules all run x 5.7 -> 94.2 pct while its two footer rules stop at 49.1. They are now
    reported in `off_grid_pct` and excluded from the bands. Skipped under `--col`, where
    every rule is measured over the same narrow band.
  * **The tool audits its own output** (`grid_audit` + the leading-rule probe) — a short
    list is as dangerous as a wrong one. `interior_missing_pct` names any rule missing at the
    measured pitch, and the leading probe asks the image whether there is ink one pitch ABOVE
    the first rule (the DEFECT 7 signature, which leaves a perfectly regular ladder one line
    short). Both are reported flagged, never inserted: the answer is a crop proof, not a
    number the tool invents.
  * **`--expect-rows N` assert** — a caller that knows the row count makes a short list FAIL
    LOUDLY (`geometry_status: row-count-mismatch`, CLI exit 2) instead of trusting it.
  * **Honest degradation** — `geometry_status` is one of `ok` / `gaps` / `row-count-mismatch`
    / `no-reliable-geometry`, with `notes` saying what to do. A legitimately unruled grid
    returns `no-reliable-geometry` and exit 2: an honest unknown is data, a confident wrong
    answer is the defect being fixed. Sibling 2, the four schedule pages that returned ZERO
    rules, resolves here — the normalised mask recovers the grid on some of them, and the
    ones it cannot are now SAID to be unmeasured rather than returned as an empty list.

Usage:
    python3 rowbands.py <pdf> <page> [--dpi 200] [--json] [--col x0,x1]
                        [--max-rule-px N] [--text-lines] [--expect-rows N]
                        [--no-normalize]

Output: detected horizontal/vertical rules and the implied row bands, all as percentages
of the page AS POPPLER RENDERS IT (`frame: "raw"`), ready for `pct:x,y,w,h@p<page>`.
Exit code 0 for `ok`/`gaps`, 2 for `row-count-mismatch`/`no-reliable-geometry`.
"""
import json
import math
import subprocess
import sys
import tempfile
import os

import numpy as np
from PIL import Image, ImageFilter


def render(pdf, page, dpi=200):
    d = tempfile.mkdtemp()
    subprocess.run(["pdftoppm", "-gray", "-png", "-r", str(dpi), "-f", str(page),
                    "-l", str(page), pdf, os.path.join(d, "p")],
                   check=True, capture_output=True)
    files = [f for f in os.listdir(d) if f.endswith(".png")]
    if not files:
        return None
    return os.path.join(d, files[0])


def deskewed_to_raw(x_d, y_d, ang, W, H):
    """Map a point in the deskewed (PIL rotate(ang)) frame back to the raw render frame.

    PIL `rotate(ang)` maps raw -> deskewed by x_d = cx + cos*dx + sin*dy,
    y_d = cy - sin*dx + cos*dy (verified empirically 2026-08-18); this is the inverse.
    """
    th = math.radians(ang)
    cx, cy = W / 2.0, H / 2.0
    dx, dy = x_d - cx, y_d - cy
    return (cx + math.cos(th) * dx - math.sin(th) * dy,
            cy + math.sin(th) * dx + math.cos(th) * dy)


def raw_to_deskewed(x_r, y_r, ang, W, H):
    th = math.radians(ang)
    cx, cy = W / 2.0, H / 2.0
    dx, dy = x_r - cx, y_r - cy
    return (cx + math.cos(th) * dx + math.sin(th) * dy,
            cy - math.sin(th) * dx + math.cos(th) * dy)


def _runs(idx, gap=4):
    """Group sorted indices into runs [(start, end)] tolerating `gap` blank rows."""
    out, s, e = [], None, None
    for i in idx:
        if s is None:
            s = e = i
        elif i - e > gap:
            out.append((s, e))
            s = e = i
        else:
            e = i
    if s is not None:
        out.append((s, e))
    return out


def _grid_score(bs):
    """Longest run of consecutive bands of near-equal height (pitch regularity).

    Choosing the coverage threshold by RAW BAND COUNT is wrong and was tried: at a loose
    threshold the page's own TEXT LINES start registering, multiplying the count while
    destroying the grid. A printed table row is a REGULAR pitch, so the threshold to
    prefer is the one whose bands are most regular, not the one that finds most edges.
    """
    if not bs:
        return 0
    hs = [b - a for a, b in bs]
    best = run = 1
    for i in range(1, len(hs)):
        ref = hs[i - 1]
        if ref and abs(hs[i] - ref) <= 0.20 * ref:
            run += 1
            best = max(best, run)
        else:
            run = 1
    return best


def _thin_runs(dk, cover, max_thick, x0=0, x1=None, min_fill=0.0, max_segments=8):
    """(rules, other) runs of dark rows in dk[:, x0:x1]; entries (center, s, e, xs, xe).

    xs/xe = extent of dark columns across the run (absolute image coords). A run is a
    RULE only if it is thin (<= max_thick) AND solid (`fill` = dark fraction of its own
    extent >= min_fill) AND made of few segments — together these separate a printed rule
    from a redaction bar, a shaded band, and a line of type.
    """
    seg = dk[:, x0:x1]
    width = seg.shape[1]
    counts = seg.sum(axis=1)
    idx = [y for y in range(seg.shape[0]) if counts[y] >= cover * width]
    rules_, other = [], []
    for s, e in _runs(idx):
        cols = np.where(seg[s:e + 1].any(axis=0))[0]
        xs = int(cols.min()) + x0 if len(cols) else x0
        xe = int(cols.max()) + x0 if len(cols) else x0
        item = ((s + e) / 2.0, s, e, xs, xe)
        # THICKNESS IS THE MEDIAN ACROSS THE RUN'S OWN COLUMNS, NOT ITS MAXIMUM.
        # Added 2026-08-19 after utah chunk agents hit this four times in one chunk: where a
        # filer's heavy ink or a pen stroke CROSSES a printed rule, the run thickens locally,
        # its overall height exceeds max_thick, and the rule is misfiled as a BAR — so the row
        # grid silently loses a line and every band below it shifts. The agents' recovery was to
        # spot the gap at `first + k*pitch`, find the rule in `bars_pct`, reinstate it and
        # crop-prove it; on one page that decision changed row 1 itself (22.17 vs 2500.00).
        # A printed rule is thin along MOST of its length even when ink crosses part of it, so
        # the median column-height separates it from a genuine bar, which is thick throughout.
        seg_rows = seg[s:e + 1, xs - x0:xe - x0 + 1]
        colheights = seg_rows.sum(axis=0)
        colheights = colheights[colheights > 0]
        thick_px = (int(np.median(colheights)) if len(colheights) else (e - s + 1))
        is_rule = thick_px <= max_thick
        if is_rule and min_fill > 0:
            segs = _segments(seg[s:e + 1, xs - x0:xe - x0 + 1], xs)
            span = max(1.0, float(xe - xs))
            fill = sum(b - a for a, b in segs) / span
            is_rule = fill >= min_fill and len(segs) <= max_segments
        (rules_ if is_rule else other).append(item)
    return rules_, other


def bg_norm_mask(a, dark=170, sigma=16, norm_t=25):
    """Background-normalised dark mask: absolute threshold UNION local-contrast threshold.

    ADDED 2026-08-20 — the DEFECT 7 fix (TODO [DEBT] filed 2026-08-20; reproducer
    `utah_county/.../2026_Taylor_Fox_Redacted.pdf` p3).

    WHY. On a photocopied/faded scan a printed rule is only ~20-40 grey levels darker than
    the paper around it, and the paper itself is not uniform. A single absolute threshold
    (`a < dark`) then catches the rule on SOME pixel rows and misses it on others, so the
    rule's dark run SPLITS in two and each half fails the `fill` gate that separates a rule
    from a line of type — the rule vanishes from the grid. Measured on the reproducer: the
    grid's top rule sits at 441-464 px, but rows 455-458 fall under the absolute threshold,
    splitting it into runs of fill 0.71 and 0.40 (both < min_fill 0.80), and the tool
    returned 15 rules for a 15-row grid instead of 16 — opening the ledger at row 2.

    Subtracting a Gaussian blur of the page from the page measures each pixel against its
    OWN local background, so a faint-but-real rule stays continuous. This is the recovery
    the utah wave's chunk agents ran by hand every time this happened; folding it into the
    tool is the terminating fix.

    The mask is a UNION, never a replacement: it can only ADD dark pixels to what the
    absolute threshold already found, so a page the old mask read correctly cannot lose a
    rule to it. Whether the normalised candidate is USED is decided by `_detect_rows`
    scoring (see `analyze`), not by this function.
    """
    m = a < dark
    bl = np.asarray(Image.fromarray(a).filter(ImageFilter.GaussianBlur(sigma))).astype(np.int16)
    return m | ((bl - a.astype(np.int16)) > norm_t)


def _detect_rows(dk, cover, x0, x1, max_rule_px, min_fill, max_segments):
    """The adaptive-coverage ladder, factored out so it can be run on more than one mask.

    Returns (grid_score, cover_used, thin, thick).
    """
    ladder = (cover, 0.28, 0.22, 0.17, 0.13, 0.10)
    best = None
    for cv in ladder:
        thin, thick = _thin_runs(dk, cv, max_rule_px, x0, x1, min_fill, max_segments)
        n = _grid_score(bands([t[0] for t in thin]))
        if best is None or n > best[0]:
            best = (n, cv, thin, thick)
    return best


def split_off_grid(detail, min_span_ratio=0.70, min_overlap=0.70):
    """Mark rules that are not part of the page's own table grid.

    ADDED 2026-08-20 — DEFECT 7 sibling: the tool proposed a **subtotal underline / footer
    box rule as a data band** (utah wave, Voeks p2 + Forbush p2). Those rules are real
    printed rules — they are simply not grid rules. Measured on Forbush p2: every one of the
    16 grid rules runs x 5.7 -> 94.2 pct, while the two footer-box rules run 5.6 -> 49.1,
    barely half the width. A rule whose horizontal extent is materially shorter than the
    page's modal rule, or which barely overlaps it, is reported but excluded from the bands.

    Sets `off_grid` on each detail dict and returns (grid_detail, off_grid_detail).
    """
    if len(detail) < 3:
        for d in detail:
            d["off_grid"] = False
        return list(detail), []
    spans = np.array([d["x1"] - d["x0"] for d in detail], dtype=float)
    med_span = float(np.median(spans))
    med_x0 = float(np.median([d["x0"] for d in detail]))
    med_x1 = float(np.median([d["x1"] for d in detail]))
    grid, off = [], []
    for d in detail:
        span = d["x1"] - d["x0"]
        ov = max(0.0, min(d["x1"], med_x1) - max(d["x0"], med_x0))
        d["off_grid"] = bool(med_span > 0 and (span < min_span_ratio * med_span
                                               or ov < min_overlap * med_span))
        (off if d["off_grid"] else grid).append(d)
    return grid, off


def grid_audit(ys, pitch_tol=0.25):
    """Self-consistency audit of a detected rule ladder (all coords in the same unit).

    ADDED 2026-08-20 with the DEFECT 7 fix. A short rule list is exactly as dangerous as a
    wrong one and NO arithmetic gate can see it: a ledger opened one line late still sums.
    So the tool now audits its own output against the pitch it measured and says out loud
    where a rule is missing, instead of handing back a short list that looks complete.

    Returns {pitch, gaps, interior_missing, complete}. Interior positions are INTERPOLATED
    (never treated as measurements) and are reported flagged, for a crop proof.
    """
    out = {"pitch": None, "n_rules": len(ys), "interior_missing": [], "complete": None}
    if len(ys) < 3:
        return out
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    pitch = float(np.median(gaps))
    out["pitch"] = pitch
    if pitch <= 0:
        return out
    miss = []
    for a, g in zip(ys, gaps):
        k = int(round(g / pitch))
        if k >= 2 and abs(g - k * pitch) <= pitch_tol * pitch:
            miss.extend(a + j * (g / k) for j in range(1, k))
    out["interior_missing"] = miss
    out["complete"] = not miss
    return out


def best_angle(a, dark=170, angles=None, max_thick=6, cover=0.18):
    """Deskew search. These are scans: a rule 0.3 deg off horizontal drifts several px
    across the table and never lands on one pixel row. Score each candidate angle by the
    summed coverage of THIN dark runs only — a redaction bar or black box is equally dark
    at every angle and must not decide it (the old single-max score failure)."""
    if angles is None:
        angles = [i / 10.0 for i in range(-20, 21)]
    im = Image.fromarray(a)
    best, best_score = 0.0, -1.0
    for ang in angles:
        r = np.asarray(im.rotate(ang, resample=Image.BILINEAR, fillcolor=255)) if ang else a
        dk = r < dark
        counts = dk.sum(axis=1) / dk.shape[1]
        idx = [y for y in range(dk.shape[0]) if counts[y] >= cover]
        score = 0.0
        for s, e in _runs(idx):
            if (e - s + 1) <= max_thick:
                score += float(counts[s:e + 1].max())
        if score > best_score:
            best, best_score = ang, score
    return best, best_score


def _segments(dk_rows, x0, gap=5):
    """Contiguous dark-column segments across a run's rows -> [(xs, xe)] absolute."""
    cols = np.where(dk_rows.any(axis=0))[0]
    if not len(cols):
        return []
    segs = _runs(list(cols), gap=gap)
    return [(int(s) + x0, int(e) + x0) for s, e in segs]


def _v_per_band(dk, ys, W, max_rule_px, thresh=0.75, pad=8, min_bands=0.6):
    """Column rules measured band-by-band, then matched by order across the bands.

    ADDED 2026-08-20 — the vertical half of DEFECT 7. On the reproducer the full-height
    projection returned **1 of 5** column rules, and the reason is measurable: the page is a
    curved photocopy, so its column rules SHEAR — the Amount column's right rule runs at
    87.9 pct of page width beside row 1 and at 91.1 pct beside row 15. A single global
    deskew angle is a rigid rotation and cannot straighten a shear, so no single pixel
    column accumulates enough ink and the projection ladder finds nothing but the leftmost
    (nearly straight) rule.

    Inside ONE row band the shear is a fraction of a rule width, so a per-band scan sees the
    rules cleanly. Bands are scanned independently and their peaks matched BY ORDER; a
    column is reported only if it appears in at least `min_bands` of the bands with the
    modal peak count. Returns (median_xs, per_band_xs, shear) — `shear` is the top-to-bottom
    drift of each column, which the consumer needs because a median x is wrong by half the
    shear at both ends of a sheared page.
    """
    if len(ys) < 3:
        return [], [], []
    per = []
    for y0, y1 in zip(ys, ys[1:]):
        s, e = int(y0) + pad, int(y1) - pad
        if e - s < 10:
            continue
        span = e - s
        cc = dk[s:e].sum(axis=0)
        idx = [x for x in range(W) if cc[x] >= thresh * span]
        pk = [(a + b) / 2.0 for a, b in _runs(idx, gap=3) if (b - a + 1) <= max_rule_px * 2]
        per.append(pk)
    if not per:
        return [], [], []
    counts = {}
    for pk in per:
        counts[len(pk)] = counts.get(len(pk), 0) + 1
    modal = max(counts, key=lambda k: (counts[k], k))
    if modal < 2 or counts[modal] < min_bands * len(per):
        return [], [], []
    keep = [pk for pk in per if len(pk) == modal]
    cols = list(zip(*keep))
    med = [float(np.median(c)) for c in cols]
    shear = [float(max(c) - min(c)) for c in cols]
    return med, keep, shear


def data_bands(bs, tol=0.18, min_run=3):
    """Longest consecutive run of bands at a REGULAR pitch — the printed data grid.

    Trims the header band and the shaded/spacer band the forms print above the first data
    row (the commonest cause of an off-by-one row pointer). Returns (start_index, bands).
    A PROPOSAL, to be proved by crop like any other measurement.
    """
    if len(bs) < min_run:
        return 0, list(bs)
    hs = [b - a for a, b in bs]
    best = (0, 0, 0)  # (length, start, end_exclusive)
    i = 0
    while i < len(hs):
        j = i + 1
        while j < len(hs) and hs[j - 1] and abs(hs[j] - hs[j - 1]) <= tol * hs[j - 1]:
            j += 1
        if j - i > best[0]:
            best = (j - i, i, j)
        i = j
    if best[0] < min_run:
        return 0, list(bs)
    return best[1], list(bs[best[1]:best[2]])


def analyze(img_path, dark=170, cover=0.35, col=None, max_rule_px=None, dpi=200,
            text_lines=False, min_fill=0.80, max_segments=8, normalize=True,
            norm_sigma=None, norm_t=25):
    """Full detection. Returns a dict; all coordinates are RAW-render-frame pixels.

    col: optional (x0_pct, x1_pct) raw-frame band to restrict the horizontal-rule scan to
    (e.g. the Amount column). Coverage is then relative to the band width.
    normalize: also try the background-normalised mask (DEFECT 7 fix) and keep whichever
    mask yields the more regular grid. `normalize=False` restores the pre-2026-08-20 mask.
    """
    if max_rule_px is None:
        max_rule_px = max(5, round(dpi * 0.03))
    if norm_sigma is None:
        norm_sigma = max(4, round(dpi * 0.08))
    a0 = np.asarray(Image.open(img_path).convert("L"))
    H, W = a0.shape
    ang, _ = best_angle(a0, dark, max_thick=max_rule_px)
    a = (np.asarray(Image.fromarray(a0).rotate(ang, resample=Image.BILINEAR, fillcolor=255))
         if ang else a0)
    dk_raw = a < dark
    dk = dk_raw

    # column restriction: map the raw-frame band into the deskewed frame (at page centre y;
    # the approximation error is < tan(ang) * H/2 within the band and the final coordinates
    # are mapped back exactly, so it only shifts the scan window slightly)
    if col:
        cx0 = raw_to_deskewed(col[0] / 100.0 * W, H / 2.0, ang, W, H)[0]
        cx1 = raw_to_deskewed(col[1] / 100.0 * W, H / 2.0, ang, W, H)[0]
        x0, x1 = max(0, int(min(cx0, cx1))), min(W, int(max(cx0, cx1)))
    else:
        x0, x1 = 0, W

    # ADAPTIVE COVERAGE. Some sheets rule only PART of the page width (an underline form's
    # four short segments; a landscape sheet ruling the Amount column heavily), so a single
    # fixed threshold finds a handful of rules on a page that plainly has twenty-five.
    # Relax until the page yields a real band structure, judged by PITCH REGULARITY over
    # THIN runs only; the threshold actually used is reported.
    #
    # TWO MASKS, ONE SCORE (2026-08-20, DEFECT 7). The ladder is run on the absolute-threshold
    # mask (the pre-2026-08-20 behaviour, proven across the summit/weber/utah waves) AND on the
    # background-normalised mask, and the more REGULAR grid wins — same criterion the ladder
    # itself uses. Ties go to the raw mask, so a page the old tool already read correctly keeps
    # its exact answer unless normalisation strictly lengthens its regular-pitch run.
    best = _detect_rows(dk_raw, cover, x0, x1, max_rule_px, min_fill, max_segments)
    mask_used = "raw"
    if normalize:
        dk_n = bg_norm_mask(a, dark, norm_sigma, norm_t)
        alt = _detect_rows(dk_n, cover, x0, x1, max_rule_px, min_fill, max_segments)
        if alt[0] > best[0]:
            best, dk, mask_used = alt, dk_n, "bg-normalised"
    _, cover_used, thin, thick = best

    # vertical rules, measured only over the table's own y-extent (a column rule is short
    # relative to the page); same thickness discrimination on the x axis.
    #
    # ⚠ THE THRESHOLD IS ADAPTIVE, exactly as it is for the horizontal rules. A fixed 0.60
    # was the original behaviour and it FAILED on a real wave page: a filer's boxed landscape
    # attachment ledger returned 28 horizontal rules and **ZERO vertical rules** (utah chunk 02,
    # 2026-08-19), because a printed column rule commonly stops at a header band, breaks at a
    # spanning cell, or fades on a scan, so it covers well under 60% of the table's y-extent.
    # Relaxing until the page yields a real column structure — judged by SPACING REGULARITY,
    # not by edge count, the same criterion used on the other axis — recovers it; the threshold
    # actually used is reported as `v_cover_used` so a loose detection is never passed off as a
    # tight one.
    v_rules, v_bars, v_cover_used = [], [], None
    if len(thin) >= 2:
        y0v = int(min(t[1] for t in thin))
        y1v = int(max(t[2] for t in thin))
        span = max(1, y1v - y0v)
        colcounts = dk[y0v:y1v].sum(axis=0)
        # STRICT FIRST, relax ONLY on failure — and never prefer a looser threshold over a
        # working stricter one. ⚠ Do NOT score these by pitch regularity the way the row rules
        # are scored: table COLUMNS are deliberately unequal widths (a narrow Date, a wide Name,
        # a wide Address, a narrow Amount), so "most regular spacing" actively prefers junk —
        # measured 2026-08-19, a regularity-scored ladder replaced weber's correct column bands
        # (4.72 / 12.87 / 43.17 / 85.24 / 95.90) with a run of text stems 0.6 pct apart.
        for cv in (0.60, 0.45, 0.35, 0.25, 0.18):
            vidx = [x for x in range(W) if colcounts[x] >= cv * span]
            rr, bb = [], []
            for s, e in _runs(vidx):
                item = ((s + e) / 2.0, s, e)
                (rr if (e - s + 1) <= max_rule_px else bb).append(item)
            v_rules, v_bars, v_cover_used = rr, bb, cv
            if len(rr) >= 3:               # a real column structure; take it and stop
                break

    # PER-BAND RESCUE (2026-08-20, DEFECT 7). If the whole-height projection still cannot
    # find a column structure, the usual cause is not faintness but SHEAR: a curved
    # photocopy's column rules are not parallel to each other, and a rigid deskew cannot
    # straighten them. Scan each row band on its own instead. Only taken when the projection
    # FAILED (< 3 rules), so every page the projection already reads keeps its exact answer —
    # including weber's audited column bands, which the projection returns.
    v_method = "projection"
    v_shear, v_per_band = [], []
    if len(v_rules) < 3 and len(thin) >= 4:
        med, per, shear = _v_per_band(dk, [t[0] for t in thin], W, max_rule_px)
        if len(med) >= 3:
            y0v = int(min(t[1] for t in thin))
            y1v = int(max(t[2] for t in thin))
            v_rules = [(x, y0v, y1v) for x in med]
            v_method, v_shear, v_per_band = "per-band", shear, per

    # map everything back to the RAW render frame
    h_detail = []
    for c, s, e, xs, xe in thin:
        xm = (xs + xe) / 2.0
        xr, yr = deskewed_to_raw(xm, c, ang, W, H)
        segs = _segments(dk[s:e + 1, xs:xe + 1], xs)
        segs_raw = []
        for ss, se in segs:
            sx0 = deskewed_to_raw(ss, c, ang, W, H)[0]
            sx1 = deskewed_to_raw(se, c, ang, W, H)[0]
            segs_raw.append((sx0, sx1))
        x0r = deskewed_to_raw(xs, c, ang, W, H)[0]
        x1r = deskewed_to_raw(xe, c, ang, W, H)[0]
        span = max(1.0, float(xe - xs))
        h_detail.append({"y": yr, "x0": min(x0r, x1r), "x1": max(x0r, x1r),
                         "thick": e - s + 1,
                         "fill": sum(b - a for a, b in segs) / span,
                         "n_segments": len(segs), "segments": segs_raw})
    # OFF-GRID SPLIT (2026-08-20): a subtotal underline / footer-box rule is a real printed
    # rule but not a row of the table, and letting it through produced a false data band.
    # A column-restricted scan measures every rule over the same narrow band, so the width
    # test carries no information there and is skipped.
    if col:
        for d in h_detail:
            d["off_grid"] = False
        h_grid, h_off = list(h_detail), []
    else:
        h_grid, h_off = split_off_grid(h_detail)
    hs = [d["y"] for d in h_grid]
    ym = (min(t[1] for t in thin) + max(t[2] for t in thin)) / 2.0 if thin else H / 2.0
    vs = [deskewed_to_raw(c, ym, ang, W, H)[0] for c, s, e in v_rules]
    bars = []
    for c, s, e, xs, xe in thick:
        _, yr0 = deskewed_to_raw((xs + xe) / 2.0, s, ang, W, H)
        _, yr1 = deskewed_to_raw((xs + xe) / 2.0, e, ang, W, H)
        bars.append({"y": min(yr0, yr1), "h": abs(yr1 - yr0) + 1,
                     "x0": deskewed_to_raw(xs, c, ang, W, H)[0],
                     "x1": deskewed_to_raw(xe, c, ang, W, H)[0]})

    # LEADING-RULE PROBE (2026-08-20). The DEFECT 7 failure mode is a grid that is missing
    # its TOP rule, and unlike an interior gap that leaves a double-height band, a missing
    # top rule leaves NOTHING to notice: the ladder is perfectly regular, one line short. So
    # the tool asks the image directly whether there is ink one pitch above its first rule,
    # over the grid's own x-extent, and reports the measurement. It never inserts the rule —
    # the answer is a flag for a crop proof, exactly like `interior_missing`.
    grid_thin = [t for t, d in zip(thin, h_detail) if not d.get("off_grid")]
    probe = None
    missing_rules, unsupported_gaps = [], []
    if len(grid_thin) >= 3:
        cs = [t[0] for t in grid_thin]
        pitch_d = float(np.median([b - a for a, b in zip(cs, cs[1:])]))
        gx0 = int(np.median([t[3] for t in grid_thin]))
        gx1 = int(np.median([t[4] for t in grid_thin]))
        wseg = max(1, gx1 - gx0)
        cov = dk[:, gx0:gx1 + 1].sum(axis=1) / float(wseg)
        rule_cov = float(np.median([cov[int(t[1]):int(t[2]) + 1].max() for t in grid_thin]))
        interior = []
        for (a_, b_) in zip(cs, cs[1:]):
            lo, hi = int(a_ + 0.25 * pitch_d), int(b_ - 0.25 * pitch_d)
            if hi > lo:
                interior.append(float(np.median(cov[lo:hi])))
        bg = float(np.median(interior)) if interior else 0.0

        def ink(py):
            """Is there ink at `py` (deskewed), over the grid's own x-extent?

            The predicate both probes make. A rule the ladder says SHOULD be there but the
            page does not show is not a missing rule — it is a section break, a form header,
            or an underline sheet that simply has no rule above its first row. Asking the
            image is what keeps the audit a measurement instead of arithmetic.
            """
            lo, hi = int(py - 0.35 * pitch_d), int(py + 0.35 * pitch_d)
            if pitch_d <= 0 or lo < 0 or hi >= H:
                return None
            pc = float(cov[lo:hi + 1].max())
            return {"y_deskewed": py, "coverage": pc, "rule_coverage": rule_cov,
                    "band_bg_coverage": bg,
                    "supported": bool(pc >= 0.55 * rule_cov and pc >= max(2.0 * bg, 0.03)),
                    "y": deskewed_to_raw((gx0 + gx1) / 2.0, py, ang, W, H)[1]}

        probe = ink(cs[0] - pitch_d)
        # INTERIOR GAPS ARE PROBED TOO, for the same reason. Measured on the regression
        # sample: an underline schedule (utah `2010_CountyRecorder-CampbellRodney` p3) has a
        # 3-pitch gap between its form header and its first row that the arithmetic reads as
        # two missing rules, and the page shows no ink at either position. Unsupported gaps
        # are reported separately so a section break is never presented as a lost row.
        ga_d = grid_audit(cs)
        for py in ga_d["interior_missing"]:
            pr = ink(py)
            (missing_rules if (pr and pr["supported"]) else unsupported_gaps).append(
                (pr or {}).get("y", deskewed_to_raw((gx0 + gx1) / 2.0, py, ang, W, H)[1]))

    res = {
        "px": [W, H], "deskew_deg": ang, "frame": "raw", "cover_used": cover_used,
        "max_rule_px": max_rule_px, "col": col, "v_cover_used": v_cover_used,
        "mask_used": mask_used, "v_method": v_method, "v_shear": v_shear,
        "v_per_band": v_per_band, "leading_probe": probe,
        "h_rules": hs, "v_rules": vs, "h_detail": h_detail, "h_off_grid": h_off,
        "bars": bars,
    }

    # HONEST DEGRADATION (2026-08-20). An honest unknown is data; a confident wrong answer is
    # DEFECT 7. The status is computed HERE, not in main(), so a library caller gets the same
    # signal the CLI prints. `--expect-rows` layers its assert on top of this in main().
    ga = grid_audit(hs)
    ga["interior_missing"] = missing_rules          # ink-supported only (see above)
    ga["unsupported_gaps"] = unsupported_gaps
    res["grid_audit"] = ga
    notes, status = [], "ok"
    if len(hs) < 3 or not bands(hs):
        status = "no-reliable-geometry"
        notes.append("fewer than 3 grid rules / no bands — the page's rules were not found; "
                     "fall back to --col, then to a declared frame, never to these numbers")
    else:
        if ga["interior_missing"]:
            status = "gaps"
            notes.append("interior rule(s) missing at the measured pitch — positions are "
                         "INTERPOLATED, not measured; crop-prove before use")
        if probe and probe["supported"]:
            status = "gaps"
            notes.append("ink found one pitch ABOVE the first rule (DEFECT 7 signature): the "
                         "grid may open one row earlier — crop-prove row 1 before use")
    res["geometry_status"] = status
    res["notes"] = notes

    if text_lines:
        # drafting aid for rule-less TYPED sheets: the THICK bands at a loose threshold
        # are the text lines. Never presented as rules.
        _, tthick = _thin_runs(dk, 0.06, max_rule_px, x0, x1)
        tb = []
        for c, s, e, xs, xe in tthick:
            _, ty0 = deskewed_to_raw((xs + xe) / 2.0, s, ang, W, H)
            _, ty1 = deskewed_to_raw((xs + xe) / 2.0, e, ang, W, H)
            tb.append({"y": min(ty0, ty1), "h": abs(ty1 - ty0) + 1})
        res["text_bands"] = tb
    return res


def rules(img_path, dark=170, cover=0.35, col=None, max_rule_px=None, dpi=200):
    """Back-compat surface: (h_rules, v_rules, W, H, angle).

    ⚠ SEMANTIC CHANGE vs the frozen wave-kit copies: coordinates are now in the RAW
    render frame (the frame `make_snippet.py` crops), not the deskewed copy. `angle` is
    still reported so a consumer can pad a full-width box by the skew drift.
    """
    r = analyze(img_path, dark, cover, col, max_rule_px, dpi)
    W, H = r["px"]
    return r["h_rules"], r["v_rules"], W, H, r["deskew_deg"]


def bands(h_rules, min_h=8, max_h=200):
    """Consecutive rule pairs whose gap is a plausible table row."""
    out = []
    for a, b in zip(h_rules, h_rules[1:]):
        if min_h <= (b - a) <= max_h:
            out.append((a, b))
    return out


def main():
    pdf, page = sys.argv[1], int(sys.argv[2])
    dpi = 200
    if "--dpi" in sys.argv:
        dpi = int(sys.argv[sys.argv.index("--dpi") + 1])
    col = None
    if "--col" in sys.argv:
        col = tuple(float(v) for v in sys.argv[sys.argv.index("--col") + 1].split(","))
    max_rule_px = None
    if "--max-rule-px" in sys.argv:
        max_rule_px = int(sys.argv[sys.argv.index("--max-rule-px") + 1])
    expect_rows = None
    if "--expect-rows" in sys.argv:
        expect_rows = int(sys.argv[sys.argv.index("--expect-rows") + 1])
    img = render(pdf, page, dpi)
    if not img:
        print(json.dumps({"pdf": pdf, "page": page,
                          "geometry_status": "no-reliable-geometry",
                          "reason": "page did not render"}))
        return 2
    r = analyze(img, col=col, max_rule_px=max_rule_px, dpi=dpi,
                text_lines="--text-lines" in sys.argv,
                normalize="--no-normalize" not in sys.argv)
    W, H = r["px"]
    bs = bands(r["h_rules"])
    res = {
        "pdf": pdf, "page": page, "dpi": dpi, "px": [W, H],
        "frame": "raw", "deskew_deg": r["deskew_deg"],
        "skew_drift_pct": round(100.0 * abs(math.tan(math.radians(r["deskew_deg"]))) * W / H, 2),
        "cover_used": r["cover_used"], "v_cover_used": r.get("v_cover_used"),
        "max_rule_px": r["max_rule_px"],
        "mask_used": r.get("mask_used"), "v_method": r.get("v_method"),
        "h_rules_pct": [round(100.0 * y / H, 2) for y in r["h_rules"]],
        "v_rules_pct": [round(100.0 * x / W, 2) for x in r["v_rules"]],
        "h_rules_detail": [{"y": round(100.0 * d["y"] / H, 2),
                            "x0": round(100.0 * d["x0"] / W, 2),
                            "x1": round(100.0 * d["x1"] / W, 2),
                            "thick_px": d["thick"],
                            "fill": round(d["fill"], 2),
                            "off_grid": d.get("off_grid", False),
                            "n_segments": d["n_segments"],
                            "segments": [[round(100.0 * s / W, 2), round(100.0 * e / W, 2)]
                                         for s, e in d["segments"]]}
                           for d in r["h_detail"]],
        "bars_pct": [{"y": round(100.0 * b["y"] / H, 2), "h": round(100.0 * b["h"] / H, 2),
                      "x0": round(100.0 * b["x0"] / W, 2), "x1": round(100.0 * b["x1"] / W, 2)}
                     for b in r["bars"]],
        "n_bands": len(bs),
        "bands_pct": [{"i": i + 1,
                       "y": round(100.0 * a / H, 2),
                       "h": round(100.0 * (b - a) / H, 2)}
                      for i, (a, b) in enumerate(bs)],
    }
    off, dbs = data_bands(bs)
    res["data_bands_trimmed"] = {"leading": off, "trailing": len(bs) - off - len(dbs)}
    res["n_data_bands"] = len(dbs)
    res["data_bands_pct"] = [{"i": i + 1,
                              "y": round(100.0 * a / H, 2),
                              "h": round(100.0 * (b - a) / H, 2)}
                             for i, (a, b) in enumerate(dbs)]
    if col:
        res["col"] = list(col)
    if "text_bands" in r:
        res["text_bands_pct"] = [{"y": round(100.0 * t["y"] / H, 2),
                                  "h": round(100.0 * t["h"] / H, 2)} for t in r["text_bands"]]

    # --- what the tool did NOT count, and what it thinks is missing (2026-08-20) ---------
    res["off_grid_pct"] = [{"y": round(100.0 * d["y"] / H, 2),
                            "x0": round(100.0 * d["x0"] / W, 2),
                            "x1": round(100.0 * d["x1"] / W, 2)}
                           for d in r.get("h_off_grid", [])]
    if r.get("v_method") == "per-band":
        res["v_shear_pct"] = [round(100.0 * s / W, 2) for s in r.get("v_shear", [])]
        res["v_rules_per_band_pct"] = [[round(100.0 * x / W, 2) for x in pk]
                                       for pk in r.get("v_per_band", [])]
    ga = r["grid_audit"]
    res["grid_audit"] = {
        "n_rules": ga["n_rules"],
        "pitch_pct": round(100.0 * ga["pitch"] / H, 3) if ga["pitch"] else None,
        "interior_missing_pct": [round(100.0 * y / H, 2) for y in ga["interior_missing"]],
        "unsupported_gaps_pct": [round(100.0 * y / H, 2) for y in ga.get("unsupported_gaps", [])],
    }
    lp = r.get("leading_probe")
    if lp:
        res["grid_audit"]["leading_rule_probe"] = {
            "y_pct": round(100.0 * lp["y"] / H, 2),
            "coverage": round(lp["coverage"], 3),
            "rule_coverage": round(lp["rule_coverage"], 3),
            "band_bg_coverage": round(lp["band_bg_coverage"], 3),
            "supported": lp["supported"],
        }

    # --- THE ROW-COUNT ASSERT (layered on analyze()'s own honest status) -----------------
    # A caller that knows how many rows the page has can make a SHORT LIST FAIL rather than
    # be trusted — the gate DEFECT 7 slipped through, since a shifted ledger still sums.
    status, notes = r["geometry_status"], list(r["notes"])
    if expect_rows is not None:
        res["expect_rows"] = expect_rows
        if res["n_data_bands"] != expect_rows:
            status = "row-count-mismatch"
            notes.append(f"ASSERT FAILED: {expect_rows} rows expected, "
                         f"{res['n_data_bands']} data bands detected")
    res["geometry_status"] = status
    res["notes"] = notes

    if "--json" in sys.argv:
        print(json.dumps(res))
    else:
        print(json.dumps(res, indent=1))
    return 0 if status in ("ok", "gaps") else 2


if __name__ == "__main__":
    sys.exit(main() or 0)
