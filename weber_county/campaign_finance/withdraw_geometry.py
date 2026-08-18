#!/usr/bin/env python3
"""withdraw_geometry.py — mark a staged itemized record's measured geometry as WITHDRAWN.

WHY.  The B2 contract stores, per row, a `pct:` box pointing at the AMOUNT cell that figure
was read from, computed by `make_itemized_caches.py` from the record's own per-page frame.
The 2026-08-17 resume audit rendered that stored box back off the retained PDF for a sample row
of every itemized filing and READ it.  On the filings listed below the box did not reproduce
the recorded amount — the frame's Amount-column band, or its row indexing, or both, are wrong.

WHAT IS AND IS NOT AFFECTED.  The VALUES are not in question: every one of these sides still
closes on a figure the filing itself prints (and one pair, the Harvey 2016 twin, was
transcribed independently by two agents from two channels and agreed on all 161 rows). What is
in question is only the POINTER.  A measurement that is wrong is not published in a weaker
form and is not quietly left in place: it is WITHHELD, with the reason travelling into
`filing_totals.notes` and the cache's `_meta.itemized.geometry`.  Re-measuring these frames is
a separate, cheap pass (no re-reading of values) and is filed as follow-up work.

The record keeps its frames under `frames_withdrawn` so the re-measure pass can see exactly
what was measured before.  Idempotent.

Run:  python3 withdraw_geometry.py [--dry-run]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RECS = os.path.join(HERE, "_itemized_records")

REASON = ("WITHDRAWN 2026-08-17: this filing's per-page geometry frame failed the resume "
          "wave's render-back audit — the stored box did not reproduce the amount recorded "
          "for the sampled row (wrong Amount-column band and/or wrong row index). The "
          "measurement is withheld rather than published wrong; the VALUE is unaffected and "
          "remains gated by the figure the filing itself prints. Re-measurement is queued.")

# keys whose sampled row(s) failed the render-back audit, 2026-08-17
# NOT withdrawn, and the reason matters: `14230ff0`, `4dedb81d`, `8b392841` and `1b428642`
# FAILED the first render-back and were cleared on re-test. Their pages carry `/Rotate 90|270`,
# and `scripts/campaign_finance/make_snippet.py` resolves a `pct:` box against the UNROTATED
# MediaBox that `pdfinfo` reports while `pdftoppm` renders the page WITH rotation applied — so
# the audit tool, not the record, was wrong (found independently by two chunk agents,
# 2026-08-17; the shared script is frozen and was NOT patched). Re-cropped against the RENDERED
# raster, all eight sampled boxes on those four filings reproduce their recorded amounts
# exactly. The withdrawals below are all on `/Rotate 0` pages, where the tool is sound and the
# crops returned real content from the WRONG column — those are genuine.
KEYS = [
    "14e72210", "21be8e3d", "2613aa33", "3e0ccb6b", "4acceac4", "4b8c476a",
    "6803c289", "6d5e0e17", "7a944882", "7fe3188c", "8acc2c9b",
    "8f779dee", "9f7bfdf9", "a6dfbcd8", "a82c7768", "b3e6d32e", "bfab7ea1", "d3100af5",
]


def main(dry=False):
    want, done = set(KEYS), []
    for fn in sorted(os.listdir(RECS)):
        if not fn.endswith(".json") or fn.startswith("_"):
            continue
        p = os.path.join(RECS, fn)
        recs = json.load(open(p))
        touched = False
        for rec in recs:
            if rec["key"] not in want:
                continue
            if "frames" in rec:
                rec["frames_withdrawn"] = rec.pop("frames")
                touched = True
            if rec.get("geometry_withdrawn", {}).get("reason") != REASON:
                rec["geometry_withdrawn"] = {"date": "2026-08-17", "reason": REASON}
                touched = True
            done.append(rec["key"])
        if touched and not dry:
            json.dump(recs, open(p, "w"), indent=1)
    missing = want - set(done)
    print("%s geometry on %d record(s)%s"
          % ("would withdraw" if dry else "withdrew", len(set(done)),
             ("; NOT FOUND: %s" % sorted(missing)) if missing else ""))


if __name__ == "__main__":
    main(dry="--dry-run" in sys.argv)
