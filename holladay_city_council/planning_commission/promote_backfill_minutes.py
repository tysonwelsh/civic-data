#!/usr/bin/env python3
"""
promote_backfill_minutes.py — promote the Wayback-recovered 2020/2021 Planning
Commission minutes from ../pmn_backfill/ into this audited PC layer (2026-07-16).

WHY
    PMN body 389 never received the 2020/2021/2023 PC minutes (agenda/packet-only
    notices — the documented upstream gap). 27 of them (2020-01→2020-09 + 2021-01→
    2021-06) were recovered from the city's FORMER WordPress site cityofholladay.com
    via the Wayback Machine (see ../pmn_backfill/CLAUDE.md). All 27 are born-digital
    `pdftotext -layout` PDFs, header-verified (in-body meeting date == keyed date,
    Holladay PC header, sha256-unique, none already in the audited index), carry no
    draft markers, and sit inside the era's minutes-approval chain — so they are
    promoted as full audited documents, not vote-only sidecars.

WHAT IT DOES (idempotent; never overwrites an existing doc)
    For each ../pmn_backfill/index.csv row with source=wayback,
    body=PlanningCommission whose date is NOT already in minutes_index.csv:
      1. copies raw/pc_<date>_minutes.pdf  -> raw/<date>_planning-commission_wayback.pdf
      2. writes minutes/<year>/<week-monday>/<date>_planning-commission_wayback.md
         (standard header block + the pdftotext -layout sidecar text; Wayback
          snapshot URL recorded in the header — honest provenance)
      3. appends the index row (source=wayback, source_url = the original
         cityofholladay.com URL) and rewrites minutes_index.csv date-sorted.

    Vote extraction is NOT done here — run extract_votes.py afterwards (it reads
    minutes_index.csv and tags provenance from the index `source` column:
    pmn -> 'minutes', wayback -> 'wayback_minutes').

RUN
    python3 promote_backfill_minutes.py
    python3 extract_votes.py && python3 validate_votes.py
"""
import csv
import datetime
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PMN = ROOT.parent / "pmn_backfill"
INDEX = ROOT / "minutes_index.csv"
INDEX_COLS = ["date", "year", "title", "slug", "path", "source", "source_url",
              "format", "body"]

HEADER_TMPL = """# {title} — {date}
> Source: {source_url} (former city WordPress site cityofholladay.com; these minutes were never posted to PMN body 389)
> Wayback snapshot: {wayback_url}
> Meeting date: {date}
> Public body: PlanningCommission (PMN body 389 — agenda/packet-only there for this date)
> Retrieved: {retrieved} via the Wayback Machine; promoted from pmn_backfill/ on 2026-07-16

---

"""


def week_monday(date_iso):
    d = datetime.date.fromisoformat(date_iso)
    return (d - datetime.timedelta(days=d.weekday())).isoformat()


def main():
    with open(INDEX, newline="", encoding="utf-8") as f:
        idx_rows = list(csv.DictReader(f))
    have = {r["date"] for r in idx_rows}

    with open(PMN / "index.csv", newline="", encoding="utf-8") as f:
        cand = [r for r in csv.DictReader(f)
                if r.get("source") == "wayback"
                and r.get("body") == "PlanningCommission"]

    added = skipped = 0
    for r in sorted(cand, key=lambda x: x["date"]):
        d = r["date"]
        if d in have:
            skipped += 1
            continue
        src_pdf = PMN / r["path"]
        src_txt = PMN / "text" / f"pc_{d}_minutes.txt"
        if not (src_pdf.exists() and src_txt.exists()):
            raise SystemExit(f"missing recovered artifact for {d} — aborting")
        # 1. raw pdf (retained verbatim; pmn_backfill original is never removed)
        dst_pdf = ROOT / "raw" / f"{d}_planning-commission_wayback.pdf"
        if not dst_pdf.exists():
            shutil.copy2(src_pdf, dst_pdf)
        # 2. minutes markdown
        rel_md = f"minutes/{d[:4]}/{week_monday(d)}/{d}_planning-commission_wayback.md"
        dst_md = ROOT / rel_md
        dst_md.parent.mkdir(parents=True, exist_ok=True)
        if not dst_md.exists():
            head = HEADER_TMPL.format(title=r["title"], date=d,
                                      source_url=r["source_url"],
                                      wayback_url=r["wayback_url"],
                                      retrieved=r["retrieved_date"])
            dst_md.write_text(head + src_txt.read_text(encoding="utf-8",
                                                       errors="replace"),
                              encoding="utf-8")
        # 3. index row
        idx_rows.append({"date": d, "year": d[:4], "title": r["title"],
                         "slug": r["slug"], "path": rel_md, "source": "wayback",
                         "source_url": r["source_url"], "format": "pdf-text",
                         "body": "PlanningCommission"})
        have.add(d)
        added += 1

    idx_rows.sort(key=lambda x: (x["date"], x["path"]))
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_COLS)
        w.writeheader()
        for r in idx_rows:
            w.writerow({c: r.get(c, "") for c in INDEX_COLS})

    print(f"promoted {added} wayback PC minutes (skipped {skipped} already present); "
          f"index now {len(idx_rows)} docs {idx_rows[0]['date']} -> {idx_rows[-1]['date']}")


if __name__ == "__main__":
    main()
