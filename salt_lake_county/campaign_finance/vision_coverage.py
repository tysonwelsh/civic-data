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
# The eras with a transcribed Schedule A/B layer. `easyvote_2022` is NOT here: its itemized
# half comes from the structured API, not from a vision read of its schedules.
ITEMIZED_ERAS = ("clerk_legacy", "globalassets_2015_2021")


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
        elif r["source"] == "globalassets":
            era_of[r["path"]] = "globalassets_2015_2021"
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

    # The three eras of the STATED-TOTALS tranche. The W2 easyvote_2024_2026 caches are NOT
    # part of it and are reported in their own section below — so the TOTAL row must sum only
    # these three eras. (Summing `done`/`nosum` wholesale double-counts the W2 caches and
    # prints a negative `remaining`; that bug shipped 2026-08-24 and was fixed 2026-09-01.)
    TRANCHE_ERAS = ("clerk_legacy", "easyvote_2022", "globalassets_2015_2021")
    print(f"{'era':<24} {'filings':>8} {'transcribed':>12} {'no-summary':>11} {'remaining':>10}")
    for era in TRANCHE_ERAS:
        t, dn, ns = totals[era], done[era], nosum[era]
        print(f"{era:<24} {t:>8} {dn:>12} {ns:>11} {t - dn - ns:>10}")
    T = sum(totals[e] for e in TRANCHE_ERAS)
    D = sum(done[e] for e in TRANCHE_ERAS)
    N = sum(nosum[e] for e in TRANCHE_ERAS)
    print(f"{'TOTAL':<24} {T:>8} {D:>12} {N:>11} {T - D - N:>10}")
    print(f"\ncaches: {len(caches)}   stated fields: value={val} blank-on-form={blank} "
          f"ILLEGIBLE/absent={illegible}")
    print("per-field transcriber confidence:", dict(conf))

    # ---- ITEMIZED layer. Two waves now feed it: B2 (2026-08-02, clerk_legacy) and W1
    # (2026-08-23, the globalassets 2015-2021 paper slice). The queue is the filings in those
    # eras that HAVE a Summary Page: a document with no Summary Page has no Schedule A/B either, and a
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
        if era not in ITEMIZED_ERAS or not d["_meta"].get("summary_page_found"):
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
    print(f"\nITEMIZED ({'+'.join(ITEMIZED_ERAS)} filings that have a Summary Page): "
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

    # ---- W2 (2026-08-24): the EasyVote row-less residue — THE WAVE'S CLOSE-OUT CONDITION.
    # The queue is DERIVED, never a hand-kept list: every EasyVote filing whose document_id
    # has NO rows in the advanced-search API (ungated — a school-board filing whose rows are
    # gated out of the county CSVs is excluded here too). That is the audit's 240-filing
    # cohort: 97 row-less 2022 (itemization only; stated totals exist) + 143 row-less
    # 2024/2026 (BOTH halves owed). `remaining` counts queue filings with no `_meta.itemized`
    # block — the wave closes at 0, and nothing else closes it.
    api_docids = set()
    for name in ("advancedsearch_contributions.json", "advancedsearch_distributions.json"):
        p = os.path.join(HERE, "raw", "easyvote_api", name)
        if os.path.exists(p):
            for rr in json.load(open(p)):
                fid = (rr.get("DocumentFilingId") or "").replace("_Redacted", "").upper()
                if fid:
                    api_docids.add(fid)
    queue = [r for r in idx
             if r["source"] == "easyvote"
             and (r["document_id"] or "").upper() not in api_docids]
    # Owner ruling (school-board, proven at the cover 2026-08-24, wave W2 chunk_17): these
    # two are ledgered OUT OF SCOPE in the wave's records — excluded from the transcribe
    # queue and reported separately, mirrors build_finance._OUT_OF_SCOPE_PATHS.
    oos = [r for r in queue
           if r["path"] in ("raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__AE07FEF8.pdf",
                            "raw/easyvote/FIFE-JEPPERSON-CHARLOTTE__D20522DA.pdf")]
    queue = [r for r in queue if r not in oos]
    qc = Counter(r["election_year"] for r in queue)
    w2tot, w2it, w2nosum = Counter(), Counter(), Counter()
    for r in queue:
        d = caches.get(r["path"])
        if d and d["_meta"].get("summary_page_found"):
            w2tot[r["election_year"]] += 1
        elif d:
            w2nosum[r["election_year"]] += 1
        if d and (d["_meta"].get("itemized") or {}):
            w2it[r["election_year"]] += 1
    print(f"\nW2 — EASYVOTE ROW-LESS RESIDUE (derived queue: easyvote & no API itemized rows): "
          f"{len(queue)} filings {dict(sorted(qc.items()))}")
    print(f"{'cycle':<8} {'filings':>8} {'totals':>7} {'no-summary':>11} "
          f"{'itemized':>9} {'remaining':>10}")
    for y in sorted(qc):
        rem = qc[y] - w2it[y]
        print(f"{y:<8} {qc[y]:>8} {w2tot[y]:>7} {w2nosum[y]:>11} {w2it[y]:>9} {rem:>10}")
    TQ = sum(qc.values())
    print(f"{'ALL':<8} {TQ:>8} {sum(w2tot.values()):>7} {sum(w2nosum.values()):>11} "
          f"{sum(w2it.values()):>9} {TQ - sum(w2it.values()):>10}")
    print(f"  (+ {len(oos)} filing(s) ledgered OUT OF SCOPE — school board, owner ruling; "
          f"no county cache by design)")


if __name__ == "__main__":
    main()
