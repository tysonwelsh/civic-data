#!/usr/bin/env python3
"""make_itemized_caches.py — materialize the ITEMIZED vision caches for Juab county-office filings.

TRANCHE 3 PHASE B, juab wave (2026-08-14). Reads the wave's raw transcription records
(default `_backups/2026-08-14-tranche3-juab/records.json`) and writes ONE cache per filing at

    vision/<sha256-of-the-raw-pdf>.json

keyed by the sha256 of the retained source PDF, with `applies_to` naming every filing that
document carries (Juab has no multi-filing bundles in 2010/2014, but the field is the contract
and the 2020 bundles are the reason it exists). A filing is transcribed ONCE per sha256.

This is the ONLY writer of those caches. It is idempotent and it never touches
`vision/transcripts.json` (the stated-totals / cover transcription layer).

`geometry` (SCHEMA.md 2a, `pct:x,y,w,h@p<page>`) is computed here from the form's own printed
grid. PITCH and the horizontal extents are family constants per scan variant (the 2010 folder is
scanned near full-bleed, the 2014 folders are inset), measured from the corpus's ruled lines.
The ORIGIN is PER PAGE (`_geometry.page_y0` in the records file): these scans carry up to a third
of a row of vertical shift, and one page is shifted a full 3.5% — a family origin alone points at
the wrong line there. Row n's band top = page_y0 + (printed_row - 1) * pitch. Verified by 600 dpi
RENDER-BACK on ten boxes across both variants and both schedules; the two that missed are recorded
as `_geometry.printed_row_corrections` and were fixed at the source. Geometry is a provenance
pointer, never a value.

Usage:  python3 make_itemized_caches.py [records.json]
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)
DEFAULT_RECORDS = os.path.abspath(
    os.path.join(HERE, "..", "..", "_backups", "2026-08-14-tranche3-juab", "records.json"))

WAVE = "tranche 3 phase B — juab wave (2026-08-14)"
TRANSCRIBED_BY = "vision-transcribed(claude-opus-5[1m]; Read tool; %s)" % WAVE

# printed-grid constants, percentages of the page (see module docstring)
VARIANTS = {
    "scan2010": {"x": 5.0, "w": 89.0, "y0": 8.86, "pitch": 2.318},
    "scan2014": {"x": 11.5, "w": 79.5, "y0": 14.40, "pitch": 2.092},
}
PAGE_OF = {"contributions": 2, "expenditures": 3}


def geometry(variant, side, printed_row, page_y0, path, page_override=None):
    v = VARIANTS[variant]
    page = page_override or PAGE_OF[side]
    y0 = page_y0.get("%s|p%d" % (path, page), v["y0"])   # per-page origin; family default only as fallback
    y = y0 + (printed_row - 1) * v["pitch"]
    return "pct:%.2f,%.2f,%.2f,%.2f@p%d" % (v["x"], y, v["w"], v["pitch"], page)


def build(records_path):
    recs = json.load(open(records_path))
    page_y0 = recs.get("_geometry", {}).get("page_y0", {})
    written = []
    for f in recs["filings"]:
        pdf = D(f["path"])
        sha = hashlib.sha256(open(pdf, "rb").read()).hexdigest()
        variant = f["variant"]
        # Garrett's retained page 2 IS the Form B page (his Form A page is absent upstream)
        exp_page = 2 if f["sides"].get("expenditures") == "transcribed" and \
            len(f["pages_read"]) == 2 and f["sides"].get("contributions") == "none" else None

        def rows(side):
            out = []
            for i, r in enumerate(f.get(side, []), 1):
                row = dict(r)
                pr = row.pop("printed_row")
                row["line_no"] = i
                row["printed_row"] = pr
                row["geometry"] = geometry(variant, side, pr, page_y0, f["path"],
                                           exp_page if side == "expenditures" else None)
                row.setdefault("in_kind", False)
                row.setdefault("needs_review", 0)
                out.append(row)
            return out

        cache = {
            "sha256": sha,
            "source_pdf": f["path"],
            "form": "carr_5_5_pg",
            "applies_to": [{"path": f["path"], "candidate": f["candidate"],
                            "election_year": f["election_year"], "bundle_pages": ""}],
            "contributions": rows("contributions"),
            "expenditures": rows("expenditures"),
            "_meta": {
                "itemized": {
                    "wave": WAVE,
                    "sides": f["sides"],
                    "reconciliation": f["recon"],
                    "pages_read": f["pages_read"],
                    "page_roles": f["page_roles"],
                    "render": "pdftoppm -jpeg -r 200 (FULL PAGE, every page)",
                    "escalations": f.get("escalations", []),
                    "geometry_basis": ("printed-grid band: family constants for the carr_5_5_pg %s scan "
                                       "variant (x=%s%%, w=%s%%, pitch=%s%%) with a PER-PAGE origin "
                                       "measured by rule-profile correlation; row top = page_y0 + "
                                       "(printed_row-1)*pitch. Verified by 600 dpi render-back."
                                       % (variant, VARIANTS[variant]["x"], VARIANTS[variant]["w"],
                                          VARIANTS[variant]["pitch"])),
                    "geometry_fit": "printed-grid, per-page origin",
                    "geometry_page_y0": {k: v for k, v in page_y0.items()
                                         if k.startswith(f["path"] + "|")},
                    "transcribed_by": TRANSCRIBED_BY,
                    "transcribed_date": "2026-08-14",
                    "notes": f.get("notes", ""),
                },
            },
        }
        if "stated_total_correction" in f:
            cache["_meta"]["stated_total_correction"] = f["stated_total_correction"]
        path = D("vision", "%s.json" % sha)
        with open(path, "w") as fh:
            json.dump(cache, fh, indent=1, sort_keys=False)
            fh.write("\n")
        written.append((f["candidate"], f["election_year"], sha[:12],
                        len(cache["contributions"]), len(cache["expenditures"])))
    return written


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECORDS
    w = build(rp)
    for cand, yr, sha, nc, ne in w:
        print("%-26s %s  %s  contrib=%2d expend=%2d" % (cand, yr, sha, nc, ne))
    print("caches written: %d  (contrib rows %d, expend rows %d)"
          % (len(w), sum(x[3] for x in w), sum(x[4] for x in w)))
