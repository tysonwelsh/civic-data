#!/usr/bin/env python3
"""promote_to_audited.py — promote the verified pmn_backfill/ recoveries into the
audited minutes layers (2026-07-16 minutes-promotion, TODO "South Salt Lake expansion
follow-ups (a)").

WHAT
    The 2026-07-13 expand-city-sources sweep recovered 130 recorded-minutes PDFs from
    the CivicPlus AgendaCenter's hidden `ArchivedMinutes` slot (see ./CLAUDE.md). Every
    doc was re-verified 2026-07-16 from in-body content (date line, meeting banner,
    roll-call grammar, DRAFT indicators, and content-level dedup against the audited
    layer) before promotion. PMN/portal LABELS LIE: the backfill index's `body`/kind
    slugs were taken from portal slots and are wrong for a large share of docs — the
    tables below carry the CONTENT-VERIFIED classification:

      * most council docs slugged `_WM` are the 7:00 p.m. REGULAR meeting minutes
        (banner "CITY COUNCIL MEETING"); only 4 carry the true
        "CITY COUNCIL WORK MEETING" banner;
      * 2025-02-12_rda_RC is COUNCIL regular minutes mis-filed in the RDA slot;
      * 2024-08-07 is the Truth-in-Taxation hearing (kind TT, matching the
        unrecovered-log vocabulary); 2024-09-25 and 2025-12-10 are regular meetings
        despite SM/BoC slugs;
      * 11 docs are NOT promoted (2 work-meeting agenda packets that carry no minutes;
        9 content-duplicates of meetings already in the audited layer) — REJECTS below.

HOW
    For each promoted doc: trim any leading agenda pages (5 PC docs), prepend the
    audited-layer provenance header (`source: agendacenter`, blank pmn_file, the
    AgendaCenter id in `ac_file`), write minutes/<year>/<week-monday>/<slug>.md,
    copy the raw PDF into the dataset's raw/, and append the minutes_index.csv row.
    Then drop the now-satisfied rows from minutes_unrecovered.csv (exact
    (date,body,kind) matches + one documented label-mismatch case). Idempotent:
    slugs already indexed are skipped.

    Vote extraction is NOT done here — run each dataset's extract_votes.py +
    validate_votes.py afterwards (the audited parser; promoted rows carry
    provenance=agendacenter_minutes in all_votes.csv).
"""
import csv
import re
import shutil
import sys
from datetime import date as _date
from pathlib import Path

HERE = Path(__file__).resolve().parent          # pmn_backfill/
CITY = HERE.parent
MM = CITY / "meeting_minutes"
PC = CITY / "planning_commission"

# ---------------------------------------------------------------- REJECTS
# slug -> reason (verified 2026-07-16; kept as pmn_backfill sidecars, never promoted)
REJECTS = {
    "2023-07-26_council_WM": "work-meeting AGENDA packet (no minutes content; sweep false positive)",
    "2024-07-10_council_WM": "work-meeting AGENDA packet (no minutes content; sweep false positive)",
    "2025-03-12_council_WM": "content-duplicate of audited 2025-03-12_council_RC (same 8 motions)",
    "2026-06-10_council_WM": "content-duplicate of audited 2026-06-10_council_RC (same 9 motions)",
    "2026-06-17_council_WM": "content-duplicate of audited 2026-06-17_council_RC (same 17 motions)",
    "2023-03-16_pc_WM": "content-duplicate of audited 2023-03-16_pc_PC (same motion sequence)",
    "2023-06-01_pc_WM": "content-duplicate of audited 2023-06-01_pc_PC (same motion sequence; extra bulk is attachments)",
    "2023-09-21_pc_WM": "content-duplicate of audited 2023-09-21_pc_PC (backfill copy has one extra ADJOURN motion - follow-up noted)",
    "2024-07-11_pc_WM": "content-duplicate of audited 2024-07-11_pc_PC (same 2 motions; extra bulk is agenda+attachments)",
    "2025-07-10_pc_WM": "content-duplicate of audited 2025-07-10_pc_PC (same 4 motions)",
    "2026-05-07_pc_WM": "content-duplicate of audited 2026-05-07_pc_PC (same first-7 motion sequence)",
}

# ------------------------------------- content-verified body/kind overrides
# slug -> (body, kind). Everything not listed keeps its index body and slug kind.
OVERRIDES = {
    # council docs slugged WM whose banner/content is the 7:00 p.m. REGULAR meeting
    **{s: ("Council", "RC") for s in [
        "2022-09-14_council_WM", "2022-09-28_council_WM", "2022-10-12_council_WM",
        "2022-10-26_council_WM", "2023-04-26_council_WM", "2023-05-10_council_WM",
        "2023-05-24_council_WM", "2023-07-12_council_WM", "2023-08-23_council_WM",
        "2023-09-13_council_WM", "2023-09-27_council_WM", "2023-11-15_council_WM",
        "2024-03-13_council_WM", "2024-03-27_council_WM", "2024-04-24_council_WM",
        "2024-05-08_council_WM", "2024-06-05_council_WM", "2024-07-31_council_WM",
        "2024-08-28_council_WM", "2024-10-09_council_WM", "2024-10-23_council_WM",
        "2024-11-13_council_WM", "2024-12-11_council_WM", "2025-01-22_council_WM",
        "2025-03-26_council_WM", "2025-05-28_council_WM", "2025-06-11_council_WM",
        "2025-07-23_council_WM", "2025-08-13_council_WM", "2025-08-27_council_WM",
        "2025-09-10_council_WM", "2025-10-15_council_WM", "2025-11-12_council_WM",
        "2026-01-28_council_WM", "2026-02-11_council_WM", "2026-02-25_council_WM",
        "2026-03-11_council_WM", "2026-03-25_council_WM", "2026-04-15_council_WM",
        "2026-04-29_council_WM", "2026-05-13_council_WM",
    ]},
    "2024-09-25_council_SM": ("Council", "RC"),   # banner CITY COUNCIL MEETING, 4th Wed 7:00
    "2025-12-10_council_BoC": ("Council", "RC"),  # banner CITY COUNCIL MEETING, 2nd Wed 7:04
    "2024-08-07_council_RC": ("Council", "TT"),   # banner TRUTH IN TAXATION PUBLIC HEARING
    "2025-02-12_rda_RC": ("Council", "RC"),       # COUNCIL minutes mis-filed in the RDA slot
    # PC docs: kind from the in-body minutes title
    "2022-01-20_pc_WM": ("PlanningCommission", "PC"),   # bundles WM (6:00) + regular (7:00) minutes
    "2022-02-17_pc_PC": ("PlanningCommission", "WM"),   # Work Meeting Minutes (no regular held)
    "2022-05-19_pc_WM": ("PlanningCommission", "WM"),
    "2023-08-31_pc_PC": ("PlanningCommission", "PC"),
}

# docs whose text sidecar leads with agenda pages -> cut at the first minutes header
TRIM_LEADING_AGENDA = {
    "2022-01-20_pc_WM", "2022-02-17_pc_PC", "2022-04-07_pc_PC",
    "2022-05-19_pc_WM", "2023-08-17_pc_PC",
}
# all TRIM docs are PC; the true minutes body starts at the first minutes-title line
MINUTES_HDR = re.compile(r"^\s*Planning Commission( Work| Regular)? Meeting Minutes\s*$")

# label-mismatch unrecovered rows satisfied by a promoted doc of a DIFFERENT kind
# (the unrecovered kind came from the PMN notice label; the city's own minutes title wins)
UNRECOVERED_SPECIAL_DROPS = {
    ("2023-08-31", "PlanningCommission", "WM"),  # satisfied by 2023-08-31_pc_PC (regular minutes)
}

STREAM = {"Council": "council", "RDA": "rda", "PlanningCommission": "pc"}


def monday(iso):
    y, m, d = map(int, iso.split("-"))
    dt = _date(y, m, d)
    from datetime import timedelta
    return (dt - timedelta(days=dt.weekday())).isoformat()


def load_index(ds):
    with open(ds / "minutes_index.csv", newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        return rdr.fieldnames, list(rdr)


def main():
    src_rows = list(csv.DictReader(open(HERE / "index.csv", newline="", encoding="utf-8")))
    idx = {}
    for ds in (MM, PC):
        idx[ds] = load_index(ds)
    existing_slugs = {r["slug"] for ds in (MM, PC) for r in idx[ds][1]}
    existing_keys = {(r["date"], r["body"], r["meeting_kind"]) for ds in (MM, PC) for r in idx[ds][1]}

    promoted, skipped = [], []
    for r in src_rows:
        old_slug = r["slug"]
        if old_slug in REJECTS:
            continue
        body, kind = OVERRIDES.get(old_slug, (r["body"], old_slug.rsplit("_", 1)[-1]))
        ds = PC if body == "PlanningCommission" else MM
        date = r["date"]
        slug = f"{date}_{STREAM[body]}_{kind}"
        if slug in existing_slugs:
            skipped.append(slug)
            continue
        if (date, body, kind) in existing_keys:
            sys.exit(f"ABORT: ({date},{body},{kind}) already audited but slug {slug} new - dedup bug")

        text = (HERE / "text" / (old_slug + ".txt")).read_text(encoding="utf-8", errors="replace")
        if old_slug in TRIM_LEADING_AGENDA:
            lines = text.split("\n")
            for i, ln in enumerate(lines):
                if MINUTES_HDR.match(ln):
                    text = "\n".join(lines[i:])
                    break
            else:
                sys.exit(f"ABORT: no minutes header found while trimming {old_slug}")

        ac_id = Path(r["path"]).stem.split("_")[-1]          # e.g. 01202022-86
        header = (f"<!-- source: agendacenter | body: {body} | pmn_file:  | ac_file: {ac_id} | "
                  f"label: {r['title']} | date: {date} | meeting_kind: {kind} | "
                  f"source_url: {r['source_url']} | retrieved: {r['retrieved_date']} | "
                  f"recovery: {r['recovery_source']} | promoted: 2026-07-16 -->")
        wk = monday(date)
        md_rel = Path("minutes") / date[:4] / wk / f"{slug}.md"
        md_path = ds / md_rel
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(header + "\n\n" + text.lstrip("\n"), encoding="utf-8")

        raw_dst = ds / "raw" / f"{slug}_{ac_id}.pdf"
        if not raw_dst.exists():
            shutil.copy2(HERE / r["path"], raw_dst)

        idx[ds][1].append({
            "date": date, "year": date[:4],
            "title": f"{body} {kind} Meeting {date}",
            "slug": slug, "path": str(md_rel),
            "source": "agendacenter", "source_url": r["source_url"],
            "format": "pdf-text", "body": body, "meeting_kind": kind, "pmn_file": "",
        })
        existing_slugs.add(slug)
        existing_keys.add((date, body, kind))
        promoted.append((slug, body, kind))

    # rewrite indexes, sorted
    for ds in (MM, PC):
        fields, rows = idx[ds]
        rows.sort(key=lambda x: (x["date"], x["slug"]))
        with open(ds / "minutes_index.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    # drop satisfied unrecovered rows
    for ds in (MM, PC):
        keys = {(r["date"], r["body"], r["meeting_kind"]) for r in idx[ds][1]}
        path = ds / "minutes_unrecovered.csv"
        with open(path, newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            ufields, urows = rdr.fieldnames, list(rdr)
        kept, dropped = [], []
        for r in urows:
            k = (r["date"], r["body"], r["meeting_kind"])
            if k in keys or k in UNRECOVERED_SPECIAL_DROPS:
                dropped.append(k)
            else:
                kept.append(r)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=ufields)
            w.writeheader()
            w.writerows(kept)
        print(f"{ds.name}: unrecovered {len(urows)} -> {len(kept)} (dropped {len(dropped)})")

    print(f"promoted {len(promoted)} docs ({len(skipped)} already present, "
          f"{len(REJECTS)} rejected)")
    from collections import Counter
    print("  by body/kind:", dict(Counter((b, k) for _, b, k in promoted)))
    print("Next: run extract_votes.py + validate_votes.py in both datasets, then the "
          "derived chain (db, referrals, weeks, motions_std, sources, validate_city).")


if __name__ == "__main__":
    main()
