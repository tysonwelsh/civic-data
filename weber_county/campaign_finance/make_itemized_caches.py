#!/usr/bin/env python3
"""make_itemized_caches.py — merge ITEMIZED Form A/B transcription records into the
existing `vision/<key>.json` stated-totals caches, IN PLACE.

Weber's sibling of `salt_lake_county/campaign_finance/make_itemized_caches.py` (the wave-B2
reference implementation).  Two things differ, both forced by this module:

  * **Cache key.**  Weber's key is `sha1(index path + "|" + "<page_start>-<page_end>")[:8]`,
    because one archive PDF holds up to 50 filings.  A record therefore carries
    `index_path` + `page_start`/`page_end`, not a path alone.
  * **Geometry provenance.**  Weber's schedules are RULED tables, so the grid itself is
    measurable rather than estimated: the printed rules are detected on the rendered page
    (long runs of dark pixels) and a per-page FRAME records the Amount column's fixed-axis
    band plus one measured band per printed table row.  A row's `geometry` is the
    intersection of its row band with the Amount column band, in page percentages.  Many of
    these scans render ROTATED (the archive sheets are landscape), so a frame declares which
    axis the rows advance along (`axis: "x"` or `"y"`); the percentages are always of the
    page AS POPPLER RENDERS IT, which is what a re-render will reproduce.
    Every row records `geometry_provenance` so a consumer can tell a rule-measured pointer
    from a hand-measured box.

DISCIPLINE (identical to the reference impl)
  * The stated-totals half of a cache is NEVER touched — not `stated`, not `confidence`, not
    `candidate_stated`/`office_stated`/`report_type_stated`/`filing_date_stated`, not `notes`.
    Only the two row lists, the `itemized_transcribed` flag and a new `_meta.itemized` block
    are written.  A cache with no matching record is left byte-identical.
  * Nothing is computed here.  Reconciliation verdicts come from the TRANSCRIBER (who had the
    page in hand and the printed anchors); this script copies them verbatim.
    `build_finance.py` sums the rows, and that sum is a report of what was transcribed, never
    a substitute for a figure the form printed.
  * Idempotent: re-running the same records reproduces the same caches.

Usage:
    python3 make_itemized_caches.py <records_dir> [--dry-run] [--wave STR] [--date YYYY-MM-DD]
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VISION = os.path.join(HERE, "vision")
WAVE = "itemized-vision(claude-opus-5; 2026-08-14 wave B2 weber)"
DATE = "2026-08-14"
GEO_PROV = ("printed-rule detection on the rendered page: per-page frame = the Amount "
            "column band x one measured band per printed table row; a row's box is their "
            "intersection, in pct of the page as poppler renders it (rotation included)")

CONTRIB_KEYS = ("line_no", "date", "donor_raw", "donor_city", "donor_state", "amount",
                "in_kind", "needs_review", "confidence", "verified",
                "geometry", "geometry_frame", "geometry_provenance", "note")
EXPEND_KEYS = ("line_no", "date", "vendor_raw", "purpose", "amount",
               "in_kind", "needs_review", "confidence", "verified",
               "geometry", "geometry_frame", "geometry_provenance", "note")


def cache_key(path, page_start, page_end):
    return hashlib.sha1(("%s|%s-%s" % (path, page_start, page_end)).encode()).hexdigest()[:8]


def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def stamp_geometry(rows, frames):
    """Give every row a durable `pct:` pointer at its amount cell.

    A row declares `page` + `row` (1-based index of its printed table row).  The page frame
    gives `axis` ("x" = rows advance left-to-right on the rendered page, "y" = top-to-bottom),
    `cell` = the Amount column's band on the OTHER axis, and `rows` = one measured
    [start,end] band per printed row.  A row that already carries an explicit `geometry`
    string passes through untouched (hand-measured wins).
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
    # GEOMETRY WITHDRAWAL (2026-08-17).  A record may declare `geometry_withdrawn` when its
    # per-page frame FAILED the render-back audit — the stored box did not reproduce the
    # amount recorded for that row, so the pointer is wrong even though the VALUE is still
    # gated by the filing's own printed arithmetic.  A measurement that is wrong is not
    # published in a weaker form: it is withheld, and the reason travels with the filing.
    # The frames stay in the record (renamed `frames_withdrawn`) as the audit trail.
    wd = rec.get("geometry_withdrawn")
    if wd:
        for r in crows + erows:
            r.pop("geometry", None)
            r.pop("geometry_frame", None)
            r["geometry_provenance"] = wd.get("reason", "geometry withdrawn 2026-08-17")
        gstats = {"measured": 0, "explicit": 0, "no_frame": 0, "row_out_of_frame": 0,
                  "withdrawn": len(crows) + len(erows)}
    else:
        gstats = stamp_geometry(crows + erows, rec.get("frames"))
    cache["contributions"] = [_clean(r, CONTRIB_KEYS) for r in crows]
    cache["expenditures"] = [_clean(r, EXPEND_KEYS) for r in erows]
    cache["itemized_transcribed"] = bool(crows or erows or rec.get("sides"))
    it = {
        "wave": rec.get("wave") or wave,
        "transcribed_date": date,
        "pages_read": rec.get("pages_read") or [],
        "itemized_pages_A": rec.get("itemized_pages_A", ""),
        "itemized_pages_B": rec.get("itemized_pages_B", ""),
        "sides": rec.get("sides") or {},
        "withheld_reason": rec.get("withheld_reason") or {},
        "recon": rec.get("recon") or {},
        "escalations": rec.get("escalations", 0),
        "escalation_note": rec.get("escalation_note", ""),
        "n_contrib_rows": len(crows),
        "n_expend_rows": len(erows),
        "geometry": dict(gstats, provenance=(rec["geometry_withdrawn"].get("reason")
                                            if rec.get("geometry_withdrawn") else GEO_PROV)),
        "notes": rec.get("notes", ""),
    }
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
            partial.append(f"{name} ({e.msg} at char {e.pos})")
            continue
        for rec in recs:
            key = cache_key(rec["index_path"], rec["page_start"], rec["page_end"])
            if rec.get("key") and rec["key"] != key:
                raise SystemExit(f"{name}: key mismatch for {rec['index_path']} "
                                 f"pp{rec['page_start']}-{rec['page_end']}: "
                                 f"{rec['key']} != {key}")
            if key in seen:
                raise SystemExit(f"{name}: duplicate record for {key} (dedupe before running)")
            seen.add(key)
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
    print(f"{'would merge' if dry else 'merged'} itemized records into {written} caches "
          f"({tot_c} contribution rows, {tot_e} expenditure rows)")
    if partial:
        print(f"SKIPPED {len(partial)} record file(s) mid-write: {partial}")
    if skipped:
        print(f"NO STATED-TOTALS CACHE for {len(skipped)} record(s): {skipped[:8]}")


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
