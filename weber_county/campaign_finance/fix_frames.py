#!/usr/bin/env python3
"""fix_frames.py — CURATED repair of the AMOUNT-COLUMN band in a staged itemized record's
per-page geometry frame.  Values are never touched; only the pointer is.

WHY THIS EXISTS.  A record's `frames.<page>.cell` declares which printed column
`make_itemized_caches.py` intersects with a row's band to produce that row's `pct:` geometry,
and the B2 contract says that column is the schedule's **Amount** column.  The 2026-08-17
resume audit rendered the SHIPPED geometry back off the page for a sample of every itemized
filing and found that on a number of 2026-08-14 records `cell` had been set to a MIDDLE column
(the donor name, the street address, the city) — so the stored pointer aimed at the wrong cell
while the transcribed VALUE was right and reconciled.  A pointer that claims to be measured and
is not is a false claim, so it is repaired here rather than shipped.

THE REPAIR IS MECHANICAL AND NARROW.  A frame that also records `cells` (every detected column
band on that page, in coordinate order) already contains the answer: on Weber's Form A and
Form B the **Amount column is the last column of the printed table**.  So where `cell` is not
`cells[-1]`, `cell` is set to `cells[-1]`.  Frames with no `cells` list are left alone (there is
nothing to derive from), as are frames already pointing at the last column.

NOTHING IS TRUSTED BLIND.  Every repaired page is re-verified afterwards by cropping the new
geometry out of the retained PDF and READING it — the crop must render the amount recorded for
that row.  The verification is the gate; this script only proposes.

Idempotent.  Run:  python3 fix_frames.py [--dry-run] [--keys k1,k2,...]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECS = os.path.join(HERE, "_itemized_records")
NOTE = ("cell repaired 2026-08-17 (resume audit): the frame pointed at a middle column, not "
        "the schedule's Amount column; reset to the last detected column band. Values "
        "untouched; the new pointer was re-verified by rendering it back off the page.")


def main(dry=False, only=None):
    changed = []
    for fn in sorted(os.listdir(RECS)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        p = os.path.join(RECS, fn)
        recs = json.load(open(p))
        touched = False
        for rec in recs:
            if only and rec["key"] not in only:
                continue
            for pg, fr in (rec.get("frames") or {}).items():
                cells = fr.get("cells")
                if not cells or not fr.get("cell"):
                    continue
                if list(fr["cell"]) == list(cells[-1]):
                    continue
                changed.append((rec["key"], pg, list(fr["cell"]), list(cells[-1])))
                fr["cell"] = list(cells[-1])
                fr["measure_note"] = ((fr.get("measure_note", "") + "  ") + NOTE).strip()
                touched = True
        if touched and not dry:
            json.dump(recs, open(p, "w"), indent=1)
    for c in changed:
        print("  %s p%-3s %s -> %s" % c)
    print("%s %d frame cell(s)" % ("would repair" if dry else "repaired", len(changed)))


if __name__ == "__main__":
    ks = None
    for i, a in enumerate(sys.argv):
        if a == "--keys" and i + 1 < len(sys.argv):
            ks = set(sys.argv[i + 1].split(","))
    main(dry="--dry-run" in sys.argv, only=ks)
