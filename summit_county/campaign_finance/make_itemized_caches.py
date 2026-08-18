#!/usr/bin/env python3
"""make_itemized_caches.py — merge ITEMIZED ledger transcription records into the existing
`vision/<key>.json` cover-page caches, IN PLACE (TRANCHE 3 Phase B, the SCAN tranche).

WHY IN PLACE. The 2026-08-01/02 cover tranche transcribed all 131 cover boxes and left the
donor/vendor ledgers untranscribed on the 116 SCANS. This script fills those caches' new
`contributions` / `expenditures` lists and stamps a `_meta_itemized` block, exactly as
`salt_lake_county/campaign_finance/make_itemized_caches.py` does for the SLCo clerk-legacy era.

DISCIPLINE (identical to the SLCo wave-B2 contract)
  * The COVER half of a cache is NEVER touched — not `cover`, not `form_variant`, not
    `field_confidence`, not `transcribed_by`, not `notes`. A cache with no matching record is
    left byte-identical.
  * Nothing is COMPUTED here. The reconciliation verdict comes from the TRANSCRIBER, who had
    the page in hand and its printed section total; this script copies it verbatim.
    `build_finance.py` sums the rows for `itemized_*`, and that sum is a report of what was
    transcribed, never a substitute for a figure the form printed.
  * Idempotent: re-running the same records reproduces the same caches byte-for-byte.
  * Each record declares its own `wave`, so re-materializing the whole directory cannot
    re-stamp an earlier wave's caches (the SLCo wave-stamp clobber, GOTCHAS-adjacent).

GEOMETRY (SCHEMA.md 2a, LEADS Tranche-3 enriched spec (a)).
Summit's ledgers are PRINTED GRID TABLES, so geometry here is MEASURED, not estimated: a row
carries `page` + `band` (its 1-based row band on that page) and this script resolves the band
to a `pct:x,y,w,h@p<page>` box by detecting the page's own horizontal and vertical rules
(`_backups/2026-08-14-tranche3/summit-b/rowbands.py`, deskewed projection). `geometry_fit` is
then `"measured"`. Where a page's rules cannot be detected the row falls back to the record's
declared `table_frame` and is marked `"declared"` — a declared pointer is never presented as
a measured one. A frame may set `"force_declared": true` when detection returns bands that are
CONTAMINATED rather than absent (text lines registering as rules on a lightly-ruled sheet), so
the transcriber's validated frame is used instead of a plausible-looking wrong band index. A row with neither is left without geometry rather than given a fake box.

Usage:
    python3 make_itemized_caches.py <records_dir> [--dry-run]
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROWBANDS = os.path.abspath(os.path.join(
    HERE, "..", "..", "_backups", "2026-08-14-tranche3", "summit-b"))
sys.path.insert(0, ROWBANDS)

VISION = os.path.join(HERE, "vision")

CONTRIB_KEYS = ("line_no", "date", "donor_raw", "donor_city", "donor_state", "amount",
                "in_kind", "needs_review", "confidence", "cell_confidence", "verified",
                "geometry", "geometry_fit", "note")
EXPEND_KEYS = ("line_no", "date", "vendor_raw", "purpose", "amount",
               "in_kind", "needs_review", "confidence", "cell_confidence", "verified",
               "geometry", "geometry_fit", "note")

_band_cache = {}


def cache_key(index_path):
    return hashlib.sha1(index_path.encode()).hexdigest()[:8]


def page_grid(pdf_rel, page):
    """Everything measurable about one page's printed grid. Memoised.

    Returns a dict with BOTH axes resolved, because a Summit ledger page is not always
    mounted upright (see `transposed` below):

      hbands  [{y,h}]  row bands from the HORIZONTAL rules  — the upright-page row
      vrules  [x…]     the vertical (column) rules, page-%
      vbands  [{x,w}]  bands between consecutive VERTICAL rules — the row of a page whose
                       landscape form was fed through the scanner SIDEWAYS
      hspan   (y,h)    the table's own y-extent from the outermost horizontal rules

    ({},[],[],None) when nothing is detectable; the caller then falls back to a declared
    frame, or to no geometry at all — never to a fabricated box.
    """
    key = (pdf_rel, page)
    if key in _band_cache:
        return _band_cache[key]
    val = {"hbands": [], "vrules": [], "vbands": [], "hspan": None}
    try:
        import math
        import rowbands as RB
        img = RB.render(os.path.join(HERE, pdf_rel), page, 200)
        if img:
            hr, vr, W, H, ang = RB.rules(img)
            tan = abs(math.tan(math.radians(ang)))
            # SKEW ALLOWANCE. The rules are detected on a DESKEWED copy, but the stored `pct:`
            # box is applied to the page as poppler actually renders it. On a scan skewed by
            # `ang` degrees a full-table-width row drifts vertically by tan(ang) * table_width,
            # so a band measured to the pixel would clip one end of its own row. The box is
            # therefore padded by that drift, centred — a provenance pointer must CONTAIN the
            # row it points at; it is not a measurement of the row's height.
            span = (vr[-1] - vr[0]) if len(vr) >= 2 else 0.84 * W
            drift = 100.0 * tan * span / H
            val["hbands"] = [{"y": 100.0 * a / H - drift / 2.0,
                              "h": 100.0 * (b - a) / H + drift} for a, b in RB.bands(hr)]
            val["vrules"] = [100.0 * x / W for x in vr]
            # The SAME allowance on the other axis, for a sideways-mounted page: a row is a
            # vertical strip and drifts HORIZONTALLY by tan(ang) * the table's y-extent.
            hspan_px = (hr[-1] - hr[0]) if len(hr) >= 2 else 0.0
            xdrift = 100.0 * tan * hspan_px / W
            val["vbands"] = [{"x": 100.0 * a / W - xdrift / 2.0,
                              "w": 100.0 * (b - a) / W + xdrift} for a, b in RB.bands(vr)]
            if len(hr) >= 2:
                val["hspan"] = (100.0 * hr[0] / H, 100.0 * (hr[-1] - hr[0]) / H)
    except Exception:
        val = {"hbands": [], "vrules": [], "vbands": [], "hspan": None}
    _band_cache[key] = val
    return val


def page_bands(pdf_rel, page):
    """(bands, v_rules) for one page, measured. Memoised; ([], []) when undetectable.

    Back-compat wrapper over `page_grid` — the upright-page view, unchanged.
    """
    g = page_grid(pdf_rel, page)
    return g["hbands"], g["vrules"]


def geometry_for(pdf_rel, page, band, table_frame):
    """Resolve a row's band to `pct:x,y,w,h@p<page>`.

    The box spans the table's full width (the useful crop is the WHOLE ROW: donor + amount
    together, so a crop-and-re-read verification sees both), bounded by the outermost detected
    vertical rules where they exist.
    """
    tf = table_frame or {}

    # TRANSPOSED PAGES (Olson 2022, 20641). Some filings were scanned with the LANDSCAPE form
    # fed through sideways: the page is mounted portrait (/Rotate 0) but a printed table ROW
    # runs VERTICALLY down the render. On such a page the horizontal projection measures the
    # table's COLUMN separators, so a `band` index resolved the ordinary way points at a strip
    # that does not contain its row — which is why the transcriber left those rows without
    # geometry rather than give them a wrong box. The row separators come back as the VERTICAL
    # rules, so the geometry is still MEASURED from the page's own printed grid; only the axes
    # swap. Gated behind an explicit per-side `"transposed": true` in the record's table_frame,
    # so no upright filing can reach this path.
    if tf.get("transposed"):
        g = page_grid(pdf_rel, page)
        vb, hs = g["vbands"], g["hspan"]
        if band and 1 <= band <= len(vb) and hs:
            b = vb[band - 1]
            return ("pct:%.2f,%.2f,%.2f,%.2f@p%d" % (b["x"], hs[0], b["w"], hs[1], page),
                    "measured")
        if band and tf.get("x0") is not None:
            x = tf["x0"] + (band - 1) * tf.get("pitch", 2.4)
            y = tf.get("y", 20.0)
            return ("pct:%.2f,%.2f,%.2f,%.2f@p%d"
                    % (x, y, tf.get("w", 2.4), tf.get("h", 70.0), page), "declared")
        return ("", "")

    forced = bool(tf.get("force_declared"))
    bands_, vr = ([], []) if forced else page_bands(pdf_rel, page)
    if band and 1 <= band <= len(bands_):
        b = bands_[band - 1]
        if len(vr) >= 2:
            x, w = vr[0], vr[-1] - vr[0]
        elif table_frame:
            x, w = table_frame.get("x", 8.0), table_frame.get("w", 84.0)
        else:
            x, w = 8.0, 84.0
        return ("pct:%.2f,%.2f,%.2f,%.2f@p%d" % (x, b["y"], w, b["h"], page), "measured")
    if table_frame and band:
        x = table_frame.get("x", 8.0)
        w = table_frame.get("w", 84.0)
        y = table_frame.get("y0", 20.0) + (band - 1) * table_frame.get("pitch", 1.8)
        h = table_frame.get("pitch", 1.8)
        return ("pct:%.2f,%.2f,%.2f,%.2f@p%d" % (x, y, w, h, page), "declared")
    return ("", "")


def clean(row, keys, pdf_rel, table_frame, defaults=None):
    """`defaults` are record-level per-row constants (confidence, cell_confidence, verified)
    so a 40-row ledger does not repeat the same three strings 40 times. A row's own value
    always wins; the defaults only fill what the row does not state."""
    row = dict(defaults or {}, **{k: v for k, v in row.items() if v is not None})
    out = {}
    page = row.get("page")
    band = row.get("band")
    geo, fit = ("", "")
    if page:
        geo, fit = geometry_for(pdf_rel, page, band, table_frame)
    for k in keys:
        if k == "geometry":
            out[k] = geo
        elif k == "geometry_fit":
            out[k] = fit
        elif k in row:
            out[k] = row[k]
        elif k in ("in_kind",):
            out[k] = False
        elif k in ("needs_review", "verified"):
            out[k] = 0
        elif k == "confidence":
            out[k] = "medium"
        else:
            out[k] = ""
    out["page"] = page
    out["band"] = band
    return out


def main():
    rec_dir = sys.argv[1]
    dry = "--dry-run" in sys.argv
    files = sorted(f for f in os.listdir(rec_dir)
                   if f.endswith(".json") and not f.startswith("_"))
    seen, written = {}, 0
    for f in files:
        for rec in json.load(open(os.path.join(rec_dir, f), encoding="utf-8")):
            ip = rec["index_path"]
            if ip in seen:
                raise SystemExit("DUPLICATE record for %s (%s and %s)" % (ip, seen[ip], f))
            seen[ip] = f
            key = rec.get("key") or cache_key(ip)
            if key != cache_key(ip):
                raise SystemExit("key %s != sha1(%s)[:8]" % (key, ip))
            cp = os.path.join(VISION, key + ".json")
            if not os.path.exists(cp):
                raise SystemExit("no cover cache for %s (%s)" % (ip, key))
            c = json.load(open(cp, encoding="utf-8"))
            tf = rec.get("table_frame") or {}
            rd = rec.get("row_defaults") or {}
            crows = [clean(r, CONTRIB_KEYS, ip, tf.get("contributions"), rd)
                     for r in rec.get("contributions", [])]
            erows = [clean(r, EXPEND_KEYS, ip, tf.get("expenditures"), rd)
                     for r in rec.get("expenditures", [])]
            # A WITHHELD side never reaches the published lists — but its transcription is
            # not thrown away either. Where a side was read and then withheld on a semantic
            # ground (the PERIOD-vs-CUMULATIVE grain question), the rows are parked under
            # `_meta_itemized.withheld_rows` so the owner's eventual ruling can be applied
            # without re-reading the page. Parked rows are NOT data the module publishes.
            sides = rec["sides"]
            parked = {}
            if sides.get("contributions") != "transcribed" and crows:
                parked["contributions"], crows = crows, []
            if sides.get("expenditures") != "transcribed" and erows:
                parked["expenditures"], erows = erows, []
            c["contributions"] = crows
            c["expenditures"] = erows
            c["itemized_transcribed"] = True
            c["_meta_itemized"] = {
                "wave": rec["wave"],
                "transcribed_date": rec.get("transcribed_date", ""),
                "pages_read": rec.get("pages_read", []),
                "sides": rec["sides"],
                "withheld_reason": rec.get("withheld_reason", {}),
                "recon": rec.get("recon", {}),
                "page_gates": rec.get("page_gates", ""),
                "escalations": rec.get("escalations", 0),
                "n_contrib_rows": len(c["contributions"]),
                "n_expend_rows": len(c["expenditures"]),
                "geometry": {
                    "measured": sum(1 for r in c["contributions"] + c["expenditures"]
                                    if r.get("geometry_fit") == "measured"),
                    "declared": sum(1 for r in c["contributions"] + c["expenditures"]
                                    if r.get("geometry_fit") == "declared"),
                    "none": sum(1 for r in c["contributions"] + c["expenditures"]
                                if not r.get("geometry")),
                    "basis": "rule-detection row banding (rowbands.py) on the page's own "
                             "printed grid; box spans the full table width of the row",
                },
                "withheld_rows": parked,
                "notes": rec.get("notes", ""),
            }
            if not dry:
                with open(cp, "w", encoding="utf-8") as fh:
                    json.dump(c, fh, indent=1, ensure_ascii=False)
                    fh.write("\n")
            written += 1
    print("%s %d cache(s) from %d record file(s)"
          % ("would write" if dry else "wrote", written, len(files)))


if __name__ == "__main__":
    main()
