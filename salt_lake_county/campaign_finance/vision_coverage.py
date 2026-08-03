#!/usr/bin/env python3
"""vision_coverage.py — print the CURRENT coverage of the vision stated-totals tranche.

Read-only. Run it after adding caches so the counts quoted in CLAUDE.md / AVAILABILITY.md can
be refreshed from the files rather than remembered (the repo rule: measured coverage, not
recalled coverage).

    python3 vision_coverage.py
"""
import csv
import glob
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
STATED = ("total_contributions", "total_expenditures", "beginning_balance", "ending_balance")


def _money(v):
    """Verbatim printed figure -> float, for REPORTING only. Never written back anywhere."""
    if not v:
        return 0.0
    s = re.sub(r"[^0-9.\-]", "", str(v).replace("(", "-").replace(")", ""))
    try:
        return float(s)
    except ValueError:
        return 0.0


def main():
    with open(os.path.join(HERE, "index.csv"), newline="") as fh:
        idx = list(csv.DictReader(fh))
    era_of = {}
    for r in idx:
        if r["source"] == "clerk_legacy":
            era_of[r["path"]] = "clerk_legacy"
        elif r["source"] == "easyvote" and r["election_year"] == "2022":
            era_of[r["path"]] = "easyvote_2022"
    totals = Counter(era_of.values())

    caches = {}
    for f in glob.glob(os.path.join(HERE, "vision", "*.json")):
        d = json.load(open(f))
        caches[d["_meta"]["index_path"]] = d

    done = Counter()
    nosum = Counter()
    val = blank = illegible = 0
    conf = Counter()
    for p, d in caches.items():
        era = d["_meta"].get("era") or era_of.get(p, "?")
        if d["_meta"].get("summary_page_found"):
            done[era] += 1
        else:
            nosum[era] += 1
        for f in STATED:
            v = d.get(f)
            if v is None:
                illegible += 1
            elif v == "":
                blank += 1
            else:
                val += 1
        for k, v in (d.get("confidence") or {}).items():
            conf[v] += 1

    print(f"{'era':<16} {'filings':>8} {'transcribed':>12} {'no-summary':>11} {'remaining':>10}")
    for era in ("clerk_legacy", "easyvote_2022"):
        t, dn, ns = totals[era], done[era], nosum[era]
        print(f"{era:<16} {t:>8} {dn:>12} {ns:>11} {t - dn - ns:>10}")
    T, D, N = sum(totals.values()), sum(done.values()), sum(nosum.values())
    print(f"{'TOTAL':<16} {T:>8} {D:>12} {N:>11} {T - D - N:>10}")
    print(f"\ncaches: {len(caches)}   stated fields: value={val} blank-on-form={blank} "
          f"ILLEGIBLE/absent={illegible}")
    print("per-field transcriber confidence:", dict(conf))

    # ---- ITEMIZED layer (wave B2, 2026-08-02). The queue is the CLERK-LEGACY filings that
    # HAVE a Summary Page: a document with no Summary Page has no Schedule A/B either, and a
    # filing whose schedules are blank-by-construction is `transcribed` with zero rows — a
    # real zero, distinct from a withheld side (unfinished) and from `none` (no such page).
    it_done = Counter()
    sides = Counter()
    recon = Counter()
    waves = Counter()
    rows_c = rows_e = 0
    withheld = []
    gaps = []
    for p, d in caches.items():
        era = d["_meta"].get("era") or era_of.get(p, "?")
        if era != "clerk_legacy" or not d["_meta"].get("summary_page_found"):
            continue
        it = (d["_meta"].get("itemized") or {})
        if not it:
            it_done["queued"] += 1
            continue
        it_done["itemized"] += 1
        waves[it.get("wave", "?")] += 1
        rows_c += len(d.get("contributions") or [])
        rows_e += len(d.get("expenditures") or [])
        for s, fld in (("contributions", "total_contributions"),
                       ("expenditures", "total_expenditures")):
            v = (it.get("sides") or {}).get(s, "none")
            sides[f"{s}:{v}"] += 1
            recon[f"{s}:{((it.get('recon') or {}).get(s) or {}).get('result', 'unset')}"] += 1
            if v == "withheld":
                withheld.append((p, s, (it.get("withheld_reason") or {}).get(s, "")))
            # A side whose schedule page does NOT EXIST while the form states a non-zero
            # total is the one honest gap left inside this layer: money is asserted and no
            # itemization was ever filed. Distinct from a blank schedule (a real zero).
            if v == "none":
                amt = _money(d.get(fld))
                if amt:
                    gaps.append((p.split("/")[-1], s, amt))
    q = it_done["itemized"] + it_done["queued"]
    print(f"\nITEMIZED (clerk_legacy filings that have a Summary Page): "
          f"{it_done['itemized']} of {q} done, {it_done['queued']} queued")
    print(f"  rows: {rows_c} contributions / {rows_e} expenditures")
    print("  sides: " + " | ".join(f"{k}={v}" for k, v in sorted(sides.items())))
    # The TRANSCRIBER's verdict, straight from the cache. It is NOT identical to the verdict
    # shipped in filing_totals.csv: build_finance re-checks each side arithmetically and prints
    # the disagreements, and it scores a `none`/blank-stated side as unknown. Quote the
    # filing_totals figures (wave_stats.py) for "as shipped"; quote these for "as read".
    print("  reconciliation AS READ by the transcriber (see wave_stats.py for as-shipped): "
          + " | ".join(f"{k}={v}" for k, v in sorted(recon.items())))
    for w, n in waves.most_common():
        print(f"    {n:4}  {w}")
    if withheld:
        print(f"  WITHHELD sides ({len(withheld)}) — honest incompleteness, never a zero:")
        for p, s, why in withheld:
            print(f"     {p} [{s}] {why[:90]}")
    else:
        print("  WITHHELD sides: 0 — no side is abandoned mid-read")
    gc = sum(a for _, s, a in gaps if s == "contributions")
    ge = sum(a for _, s, a in gaps if s == "expenditures")
    print(f"\n  DOCUMENTED GAPS — side='none' (no such schedule page) with a NON-ZERO stated "
          f"total:\n    {len(gaps)} sides across {len({g[0] for g in gaps})} filings; "
          f"${gc:,.2f} contributions + ${ge:,.2f} expenditures unitemizable from the document")
    for n, s, a in sorted(gaps, key=lambda x: -x[2]):
        print(f"     {n:52} {s:13} ${a:>12,.2f}")

    ftp = os.path.join(HERE, "filing_totals.csv")
    if os.path.exists(ftp):
        with open(ftp, newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if "VISION-TRANSCRIBED" in r["notes"]]
        print(f"\nfiling_totals tranche rows: {len(rows)}")
        print("  filing-level confidence:", dict(Counter(r["extraction_confidence"] for r in rows)))
        print("  filing_type:", dict(Counter(r["filing_type"] for r in rows)))
        c = sum(float(r["stated_total_contributions"]) for r in rows if r["stated_total_contributions"])
        e = sum(float(r["stated_total_expenditures"]) for r in rows if r["stated_total_expenditures"])
        print(f"  stated period figures observed (NEVER a cycle total — filings overlap): "
              f"${c:,.2f} contributions / ${e:,.2f} expenditures")


if __name__ == "__main__":
    main()
