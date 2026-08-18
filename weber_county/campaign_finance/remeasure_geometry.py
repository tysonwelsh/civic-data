#!/usr/bin/env python3
"""remeasure_geometry.py — REINSTATE a withdrawn geometry frame from a proved re-measurement.

THE COUNTERPART TO `withdraw_geometry.py`.  On 2026-08-17 the resume audit rendered every
itemized row's stored `pct:` box back off the retained PDF and read it; on 18 filings the box
did not reproduce the recorded amount, so the POINTER was withheld (the VALUES were never in
doubt — each side still closes on a figure the filing itself prints).  This script applies the
2026-08-18 re-measure pass that puts a PROVED pointer back.

WHY A PATCH FILE AND NOT A DIRECT EDIT.  The 18 keys live in 6 shared record files, and the
re-measure ran as three concurrent agents; editing the records in place would have raced.  Each
agent therefore wrote one patch per filing to `_remeasure/<key>.json`, and this script applies
them centrally, one process, in key order.

WHAT A PATCH MAY AND MAY NOT DO.  A patch carries `frames` (and optionally `unmeasurable`,
`proof`, `measure_note`) and NOTHING ELSE is read from it.  It cannot touch an amount, a name,
a date, a `page`/`row` index or a reconciliation verdict — this pass re-measured a pointer and
re-read no value, and the code enforces that by construction: only `frames` is copied onto the
record.  A patch that declares `unmeasurable` for every page, or carries no `frames` at all, is
a legitimate outcome and leaves the withdrawal standing: a measurement that cannot be proved is
withheld, never published in a weaker form.

The withdrawn frames stay on the record as `frames_withdrawn` (the audit trail) whatever
happens.  Where a patch reinstates a frame, `geometry_withdrawn` is replaced by
`geometry_remeasured` carrying the date, the agent's proof line and any page still unmeasured;
`make_itemized_caches.py` then stamps those rows normally again.  Where a filing is only
PARTIALLY remeasured, the rows on an unmeasured page get no frame and `make_itemized_caches.py`
leaves them unanchored with `needs_review` — an honest per-page result, not a per-filing one.

Idempotent.  Run:  python3 remeasure_geometry.py [--dry-run]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECS = os.path.join(HERE, "_itemized_records")
PATCH = os.path.join(HERE, "_remeasure")


def load_patches():
    out = {}
    if not os.path.isdir(PATCH):
        return out
    for fn in sorted(os.listdir(PATCH)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        p = json.load(open(os.path.join(PATCH, fn), encoding="utf-8"))
        key = p.get("key") or fn[:-5]
        if key in out:
            raise SystemExit("duplicate patch for %s" % key)
        out[key] = p
    return out


def main(dry=False):
    patches = load_patches()
    applied, declined, unseen = [], [], set(patches)
    for fn in sorted(os.listdir(RECS)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        path = os.path.join(RECS, fn)
        recs = json.load(open(path, encoding="utf-8"))
        touched = False
        for rec in recs:
            p = patches.get(rec["key"])
            if not p:
                continue
            unseen.discard(rec["key"])
            frames = p.get("frames") or {}
            if not frames:
                declined.append((rec["key"], p.get("unmeasurable") or "no frames offered"))
                continue
            # keep the audit trail; NEVER discard what was withdrawn
            if "frames" in rec and "frames_withdrawn" not in rec:
                rec["frames_withdrawn"] = rec.pop("frames")
            rec["frames"] = frames
            rec.pop("geometry_withdrawn", None)
            rec["geometry_remeasured"] = {
                "date": "2026-08-18",
                "pages": sorted(frames, key=lambda s: int(s)),
                "unmeasurable": p.get("unmeasurable") or {},
                "proof": p.get("proof", ""),
            }
            applied.append((rec["key"], sorted(frames, key=lambda s: int(s)),
                            sorted(p.get("unmeasurable") or {})))
            touched = True
        if touched and not dry:
            json.dump(recs, open(path, "w"), indent=1)
    for k, pages, un in applied:
        print("  reinstated %s  pages %s%s"
              % (k, ",".join(pages), ("  (still unmeasurable: %s)" % ",".join(un)) if un else ""))
    for k, why in declined:
        print("  DECLINED   %s  withdrawal stands: %s" % (k, why))
    print("%s %d frame(s); %d patch(es) declined%s"
          % ("would reinstate" if dry else "reinstated", len(applied), len(declined),
             ("; NO RECORD for %s" % sorted(unseen)) if unseen else ""))


if __name__ == "__main__":
    main(dry="--dry-run" in sys.argv)
