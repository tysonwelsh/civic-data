#!/usr/bin/env python3
"""make_itemized_caches.py — merge ITEMIZED Schedule A/B transcription records into the
existing `vision/<key>.json` stated-totals caches, IN PLACE.

Utah County's sibling of the wave-B2 reference implementation
(`salt_lake_county/campaign_finance/make_itemized_caches.py`) and of weber's. Written
2026-08-18 for the utah_county Phase B wave. What differs here, and why:

  * **Cache key.** Utah is one filing per PDF, so the key is the repo-standard
    `sha1(index.csv path)[:8]` (`scripts/campaign_finance/vision_lib.cache_key`) — no page
    range. A record carries `index_path` alone.
  * **TWO PDFs are genuine multi-report bundles** (Buhman 2014 original+amendment,
    Westmoreland 2024). Those caches hold TWO `reports` and therefore two `filing_totals`
    rows. A record may target one of them with `report_index` (1-based); the itemized block
    is stored per report so a bundle never merges its two ledgers.
  * **THE REGIME IS PER-PERIOD AND INVERTED** relative to summit/weber (wave brief §2a).
    The promoted anchor is Column A / Box B / Box D — the PER-PERIOD cell; the cumulative
    Column B / Box C / Box E is never summed as an increment. Nothing here computes that:
    the transcriber, who had the page and its printed anchors in hand, records the verdict
    and this script copies it verbatim.
  * **Geometry.** Utah's schedules are printed grids (`modern_boxAF`) or per-column underline
    forms (`legacy_colAB`), so the grid is MEASURABLE. A per-page frame records the Amount
    column's band on the fixed axis plus one measured band per printed table row; a row's
    `geometry` is their intersection, in pct of the page AS POPPLER RENDERS IT. Measured with
    the promoted `scripts/campaign_finance/rowbands.py` (raw-render frame since 2026-08-18).

DISCIPLINE (identical to the reference impl — this is the SOLE WRITER of the itemized half)
  * The stated-totals half of a cache is NEVER touched: not `totals`, not `totals_verbatim`,
    not `confidence`, not `unreadable`, not the report-level `notes`, not `transcribed_by`.
    The cover tranche is already verified and must not change. A cache with no matching
    record is left byte-identical.
  * Nothing is computed here. Reconciliation verdicts come from the TRANSCRIBER;
    `build_finance.py` sums the rows, and that sum is a report of what was transcribed,
    never a substitute for a figure the form printed.
  * Idempotent: re-running the same records reproduces the same caches byte-for-byte.

Usage:
    python3 make_itemized_caches.py <records_dir> [--dry-run] [--wave STR] [--date YYYY-MM-DD]
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VISION = os.path.join(HERE, "vision")
WAVE = "itemized-vision(claude-fable-5; 2026-08-18 wave B2 utah)"
DATE = "2026-08-18"
GEO_PROV = ("printed-rule detection on the rendered page (scripts/campaign_finance/"
            "rowbands.py, raw-render frame): per-page frame = the Amount column band x one "
            "measured band per printed table row; a row's box is their intersection, in pct "
            "of the page as poppler renders it (rotation included)")

CONTRIB_KEYS = ("line_no", "date", "donor_raw", "donor_city", "donor_state", "amount",
                "in_kind", "needs_review", "confidence", "verified",
                "geometry", "geometry_frame", "geometry_provenance", "note")
EXPEND_KEYS = ("line_no", "date", "vendor_raw", "purpose", "amount",
               "in_kind", "needs_review", "confidence", "verified",
               "geometry", "geometry_frame", "geometry_provenance", "note")


def cache_key(path):
    """The repo-standard key — must equal vision_lib.cache_key(path)."""
    return hashlib.sha1(path.encode()).hexdigest()[:8]


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def stamp_geometry(rows, frames):
    """Give every row a durable `pct:` pointer at its amount cell.

    A row declares `page` + `row` (1-based index of its printed table row). The page frame
    gives `axis` ("y" = rows advance top-to-bottom on the rendered page, the utah norm;
    "x" = left-to-right on a rotated landscape sheet), `cell` = the Amount column's band on
    the OTHER axis, and `rows` = one measured [start,end] band per printed row. A row that
    already carries an explicit `geometry` string passes through untouched — a hand-measured
    box wins over a frame, and the record must say it was hand-measured.
    """
    stats = {"measured": 0, "explicit": 0, "no_frame": 0, "row_out_of_frame": 0}
    for r in rows:
        if (r.get("geometry") or "").strip():
            stats["explicit"] += 1
            continue
        page, ri = r.get("page"), r.get("row")
        fr = (frames or {}).get(str(page))
        if not fr or not ri:
            r["needs_review"] = r.get("needs_review") or "1"
            stats["no_frame"] += 1
            continue
        bands = fr.get("rows") or []
        if int(ri) > len(bands):
            r["needs_review"] = r.get("needs_review") or "1"
            r["geometry_provenance"] = "row index beyond the measured frame — NOT anchored"
            stats["row_out_of_frame"] += 1
            continue
        b0, b1 = bands[int(ri) - 1]
        c0, c1 = fr["cell"]
        if fr.get("axis", "y") == "x":
            x0, x1, y0, y1 = b0, b1, c0, c1
        else:
            x0, x1, y0, y1 = c0, c1, b0, b1
        x0, y0 = _clamp(x0), _clamp(y0)
        r["geometry"] = "pct:%.2f,%.2f,%.2f,%.2f@p%d" % (
            x0, y0, _clamp(x1 - x0, hi=100.0 - x0), _clamp(y1 - y0, hi=100.0 - y0), int(page))
        r["geometry_frame"] = ("p%s axis=%s cell=%.2f-%.2f rowband=%.2f-%.2f (%d of %d "
                               "measured bands)" % (page, fr.get("axis", "y"), c0, c1, b0, b1,
                                                    int(ri), len(bands)))
        r["geometry_provenance"] = GEO_PROV
        stats["measured"] += 1
    return stats


def _clean(row, keys):
    out = {}
    for k in keys:
        v = row.get(k)
        if v is None or v == "":
            continue
        out[k] = v
    return out


def merge(rec, cache, wave, date):
    crows = list(rec.get("contributions") or [])
    erows = list(rec.get("expenditures") or [])
    wd = rec.get("geometry_withdrawn")
    if wd:
        # A measurement that is WRONG is withheld, never published in a weaker form (the
        # weber 2026-08-17 precedent). The VALUES stay — they are gated by the filing's own
        # printed arithmetic — but the pointer goes, and the reason travels with the filing.
        for r in crows + erows:
            r.pop("geometry", None)
            r.pop("geometry_frame", None)
            r["geometry_provenance"] = wd.get("reason", "geometry withdrawn")
        gstats = {"measured": 0, "explicit": 0, "no_frame": 0, "row_out_of_frame": 0,
                  "withdrawn": len(crows) + len(erows)}
    else:
        gstats = stamp_geometry(crows + erows, rec.get("frames"))

    it = {
        "wave": rec.get("wave") or wave,
        "transcribed_date": rec.get("transcribed_date") or date,
        "pages_read": rec.get("pages_read") or [],
        "itemized_pages_A": rec.get("itemized_pages_A", ""),
        "itemized_pages_B": rec.get("itemized_pages_B", ""),
        "sides": rec.get("sides") or {},
        "withheld_reason": rec.get("withheld_reason") or {},
        "recon": rec.get("recon") or {},
        "in_kind_convention": rec.get("in_kind_convention", ""),
        "escalations": rec.get("escalations", 0),
        "escalation_note": rec.get("escalation_note", ""),
        "n_contrib_rows": len(crows),
        "n_expend_rows": len(erows),
        "geometry": dict(gstats, provenance=(wd.get("reason") if wd else GEO_PROV)),
        "notes": rec.get("notes", ""),
    }

    ri = int(rec.get("report_index") or 1)
    nreports = len(cache.get("reports") or [])
    if nreports > 1 or ri > 1:
        # BUNDLE: the itemized layer is stored PER REPORT so two ledgers never merge.
        if ri > max(1, nreports):
            raise SystemExit("report_index %d exceeds the %d report(s) in cache %s"
                             % (ri, nreports, cache.get("key")))
        rep = cache["reports"][ri - 1]
        rep["contributions"] = [_clean(r, CONTRIB_KEYS) for r in crows]
        rep["expenditures"] = [_clean(r, EXPEND_KEYS) for r in erows]
        rep["itemized_transcribed"] = bool(crows or erows or rec.get("sides"))
        rep.setdefault("_meta", {})["itemized"] = it
    else:
        cache["contributions"] = [_clean(r, CONTRIB_KEYS) for r in crows]
        cache["expenditures"] = [_clean(r, EXPEND_KEYS) for r in erows]
        cache["itemized_transcribed"] = bool(crows or erows or rec.get("sides"))
        cache.setdefault("_meta", {})["itemized"] = it
    return it


def main(rec_dir, dry=False, wave=None, date=None):
    wave, date = wave or WAVE, date or DATE
    seen, written, skipped, partial = set(), 0, [], []
    tot_c = tot_e = 0
    for name in sorted(os.listdir(rec_dir)):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        try:
            recs = json.load(open(os.path.join(rec_dir, name)))
        except json.JSONDecodeError as e:
            # A record file caught MID-WRITE by a concurrent chunk agent. Skipping it is
            # correct and recoverable; a crash here would lose the whole merge.
            partial.append("%s (%s at char %d)" % (name, e.msg, e.pos))
            continue
        if isinstance(recs, dict):
            recs = [recs]
        for rec in recs:
            key = cache_key(rec["index_path"])
            if rec.get("key") and rec["key"] != key:
                raise SystemExit("%s: key mismatch for %s: %s != %s"
                                 % (name, rec["index_path"], rec["key"], key))
            dedupe = (key, int(rec.get("report_index") or 1))
            if dedupe in seen:
                raise SystemExit("%s: duplicate record for %s report %d (dedupe before "
                                 "running)" % (name, key, dedupe[1]))
            seen.add(dedupe)
            cpath = os.path.join(VISION, key + ".json")
            if not os.path.exists(cpath):
                skipped.append(key)
                continue
            cache = json.load(open(cpath))
            it = merge(rec, cache, wave, date)
            tot_c += it["n_contrib_rows"]
            tot_e += it["n_expend_rows"]
            if not dry:
                with open(cpath, "w") as fh:
                    json.dump(cache, fh, indent=1, sort_keys=False)
                    fh.write("\n")
            written += 1
    print("%s itemized records into %d caches (%d contribution rows, %d expenditure rows)"
          % ("would merge" if dry else "merged", written, tot_c, tot_e))
    if partial:
        print("SKIPPED %d record file(s) mid-write: %s" % (len(partial), partial))
    if skipped:
        print("NO STATED-TOTALS CACHE for %d record(s): %s" % (len(skipped), skipped[:8]))


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
