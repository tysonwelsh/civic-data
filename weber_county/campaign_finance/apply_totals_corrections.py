#!/usr/bin/env python3
"""apply_totals_corrections.py — CURATED corrections to the STATED-TOTALS half of a
`vision/<key>.json` cache, each carrying the primary-source evidence that decided it.

WHY THIS EXISTS. `CLAUDE.md` says corrections to a published figure "go in
`vision/<key>.json` with a note saying what was re-read at the source — never in the derived
CSVs". This script is the ONE place that happens, so a correction is a reviewable diff and
not an untraceable hand-edit. Idempotent: re-running rewrites the same values and the same
note.

THE RULE THAT DECIDES A CORRECTION (GOTCHAS, the Rhodes reversal): escalation resolves
LEGIBILITY, never TRUTH. A published figure is changed only when the document's OWN
ARITHMETIC — schedule sums, page subtotals, balance closure — closes on the new value and
does not close on the old one. Every entry below states those identities.

Run:  python3 apply_totals_corrections.py [--dry-run]
Then: python3 build_finance.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
VISION = os.path.join(HERE, "vision")

# key -> {"set": {dotted.path: (new_verbatim, new_confidence_or_None)}, "note": str}
CORRECTIONS = {
    # ---------------------------------------------------------------- Corey Combe 2012
    # `raw/wayback/wb20160824082859_CCombeCampaign.pdf` (6 pp), found by the 2026-08-14
    # itemization wave while transcribing Schedule A/B.
    "6803c289": {
        "set": {
            "stated.contrib_gt50.cum": ("24,122.52", "high"),
            "stated.ending_balance.cum": ("4,287.87", "high"),
        },
        "note": (
            "CORRECTED 2026-08-14 (tranche 3 Phase B, weber itemization wave). The "
            "2026-08-01 totals tranche read the cover's line-1 cumulative as 24,622.52 and "
            "left the ending balance BLANK ('reads as either 4,287.87 or 4,957.87, did not "
            "resolve at 900 dpi'). Both are settled by the DOCUMENT'S OWN ARITHMETIC, not by "
            "any glyph re-read, and all three identities agree on 24,122.52 / 4,287.87 while "
            "none closes under 24,622.52: (a) Schedule A page 2's printed SUBTOTAL 1,950.00 + "
            "page 3's printed total 22,172.52 = 24,122.52, which is exactly what page 2's own "
            "'TOTAL CONTRIBUTIONS RECEIVED (Sum of Subtotals from All Schedule A Pages)' line "
            "prints; (b) the filer's Summary Page (p6, Column A line 1) states 24,292.52 = "
            "24,122.52 + the 170.00 sub-$50 aggregate on cover line 2; (c) the cover's own "
            "line-4 balance 4,287.87 = 24,122.52 - 19,834.65 (line 3) exactly. The misread is "
            "explained by this filer's hand, which writes the digit 2 as a 'd' -- '24,1dd' is "
            "24,122. Schedule B is untouched and already exact (17,846.84 + 1,987.81 = "
            "19,834.65). Evidence: pp. 1-6 of the filing; 700 dpi tight crops of the page-2 "
            "amount column, the page-2 subtotal/total lines and the cover summary cells were "
            "used for LEGIBILITY only."
        ),
    },
    # ------------------------------------------------- Katrina C. Gibson 2026 — SWAPPED PAIR
    # The 2026-08-01 totals tranche transcribed these two filings' covers into each other's
    # cache.  Established at the SOURCE on 2026-08-17 by rendering page 1 of each retained
    # PDF (sha256 of both files re-verified against index.csv first, both MATCH, so the bytes
    # have not moved since the 2026-08-01 fetch):
    #   raw/y2026/2026_ugd_92078f_fd9d0787.pdf (key 76c91f61) page 1 prints the JUNE 16 -
    #     PRIMARY ELECTION box ticked and 66,670.65 / 21,550.00 / 88,220.65 on line 1,
    #     49,653.62 / 36,573.66 / 86,227.28 on line 2, 17,017.03 / (15,023.66) / 1,993.37 on
    #     line 3, signed 7/23/2026.
    #   raw/y2026/2026_ugd_92078f_d8532285.pdf (key 8a163a02) page 1 prints the 30-DAYS-AFTER
    #     WITHDRAWAL OR PRIMARY ELECTION ELIMINATION box ticked and 88,220.65 / 4,168.61 /
    #     92,389.26, 86,227.28 / 5,341.07 / 91,568.35, 1,993.37 / (1,172.46) / 820.91, also
    #     signed 7/23/2026.
    # Each cover closes internally (last + this = cumulative on all three lines, and
    # contributions - expenditures = the balance line), and the pair chains: the 30-day
    # report's Last-Report column IS the primary report's Cumulative column.  So the two
    # readings are correct FIGURES that were filed under each other's key.  Nothing is
    # recomputed here; the verbatim cells are exchanged and the report_type/notes with them.
    "76c91f61": {
        "marker": "CORRECTED 2026-08-17",
        "set": {
            "report_type_stated": ("June 16 - Primary Election", None),
            "stated.contrib_all.last": ("66,670.65", None),
            "stated.contrib_all.this": ("21,550.00", None),
            "stated.contrib_all.cum": ("88,220.65", None),
            "stated.expenditures.last": ("49,653.62", None),
            "stated.expenditures.this": ("36,573.66", None),
            "stated.expenditures.cum": ("86,227.28", None),
            "stated.ending_balance.last": ("17,017.03", None),
            "stated.ending_balance.this": ("(15,023.66)", None),
            "stated.ending_balance.cum": ("1,993.37", None),
        },
        "note": (
            "CORRECTED 2026-08-17 (tranche 3 Phase B, weber itemization wave, resume leg). "
            "The 2026-08-01 totals tranche SWAPPED this filing's cover with Katrina C. "
            "Gibson's other 7/23/2026 filing (key 8a163a02, "
            "raw/y2026/2026_ugd_92078f_d8532285.pdf): the cells written here were that "
            "document's. Page 1 of THIS pdf was re-rendered at 200 dpi on 2026-08-17 and "
            "prints the 'June 16 - Primary Election' box ticked with 66,670.65 / 21,550.00 / "
            "88,220.65 (contributions), 49,653.62 / 36,573.66 / 86,227.28 (expenditures) and "
            "17,017.03 / (15,023.66) / 1,993.37 (balance), signed 7/23/2026. The sha256 of "
            "the retained file was re-verified against index.csv before the read (MATCH), so "
            "the bytes did not move. The verbatim cells above are exchanged with 8a163a02's; "
            "no figure is recomputed and no arithmetic was used to choose them - the page "
            "itself decided. This is the report that supersedes the 6/16/2026 primary report "
            "(cache 32f407e4), which the 2026-08-01 tranche read correctly."
            " NOTE ON THE PRECEDING SENTENCES: the 2026-08-01 note text that appears BEFORE this correction describes the OTHER filing of the swapped pair and is retained verbatim only as the record of the swap - read it as belonging to the other key."
        ),
    },
    "8a163a02": {
        "marker": "CORRECTED 2026-08-17",
        "set": {
            "report_type_stated": ("30 days after withdrawal or Primary Election elimination",
                                   None),
            "stated.contrib_all.last": ("88,220.65", None),
            "stated.contrib_all.this": ("4,168.61", None),
            "stated.contrib_all.cum": ("92,389.26", None),
            "stated.expenditures.last": ("86,227.28", None),
            "stated.expenditures.this": ("5,341.07", None),
            "stated.expenditures.cum": ("91,568.35", None),
            "stated.ending_balance.last": ("1,993.37", None),
            "stated.ending_balance.this": ("(1,172.46)", None),
            "stated.ending_balance.cum": ("820.91", None),
        },
        "note": (
            "CORRECTED 2026-08-17 (tranche 3 Phase B, weber itemization wave, resume leg). "
            "The 2026-08-01 totals tranche SWAPPED this filing's cover with key 76c91f61 "
            "(raw/y2026/2026_ugd_92078f_fd9d0787.pdf). Page 1 of THIS pdf was re-rendered at "
            "200 dpi on 2026-08-17 and prints the '30 days after withdrawal or Primary "
            "Election elimination' box ticked with 88,220.65 / 4,168.61 / 92,389.26 "
            "(contributions), 86,227.28 / 5,341.07 / 91,568.35 (expenditures) and 1,993.37 / "
            "(1,172.46) / 820.91 (balance), signed 7/23/2026. sha256 re-verified against "
            "index.csv before the read (MATCH). The verbatim cells are exchanged with "
            "76c91f61's; nothing is recomputed. This is the filer's LAST 2026 report and the "
            "largest 2026 county campaign in the dataset ($92,389.26 raised)."
            " NOTE ON THE PRECEDING SENTENCES: the 2026-08-01 note text that appears BEFORE this correction describes the OTHER filing of the swapped pair and is retained verbatim only as the record of the swap - read it as belonging to the other key."
        ),
    },
}


def dotted_set(obj, path, value):
    parts = path.split(".")
    for p in parts[:-1]:
        obj = obj[p]
    obj[parts[-1]] = value


def dotted_get(obj, path):
    for p in path.split("."):
        obj = obj[p]
    return obj


def main(dry=False):
    n = 0
    for key, spec in sorted(CORRECTIONS.items()):
        p = os.path.join(VISION, key + ".json")
        if not os.path.exists(p):
            raise SystemExit("no cache for %s" % key)
        cache = json.load(open(p))
        changes = []
        for path, (val, conf) in spec["set"].items():
            old = dotted_get(cache, path)
            if old != val:
                changes.append("%s: %r -> %r" % (path, old, val))
            dotted_set(cache, path, val)
            if conf:
                field = path.split(".")[1] if "." in path else path
                if cache.get("confidence", {}).get(field) != conf:
                    changes.append("confidence.%s: %r -> %r"
                                   % (field, cache.get("confidence", {}).get(field), conf))
                cache.setdefault("confidence", {})[field] = conf
        marker = spec.get("marker", "CORRECTED 2026-08-14")
        if marker not in (cache.get("notes") or ""):
            cache["notes"] = ((cache.get("notes") or "").strip() + "  " + spec["note"]).strip()
        cache.setdefault("_meta", {})["totals_corrections"] = {
            "applied": marker.split()[-1],
            "by": "tranche-3 Phase B weber itemization wave (claude-opus-5)",
            "fields": sorted(spec["set"]),
        }
        print("%s: %s" % (key, "; ".join(changes) if changes else "already applied"))
        if not dry:
            with open(p, "w") as fh:
                json.dump(cache, fh, indent=1, sort_keys=False)
                fh.write("\n")
            n += 1
    print("%s %d cache(s)" % ("would write" if dry else "wrote", n))


if __name__ == "__main__":
    main(dry="--dry-run" in sys.argv)
