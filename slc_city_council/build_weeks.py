#!/usr/bin/env python3
# NOTE (REFACTOR_PLAN 4.1, 2026-07-07): documented divergence from scripts/weeks_lib.py.
# This SLC script predates the shared lib and is a genuine fork (~120 changed lines:
# PC/comments handling, hardcoded Tuesday grid, index wording differ). The other 15
# cities are thin stubs over weeks_lib.build(); SLC deliberately is not.
"""
Build a derived, analysis-friendly weekly view that unifies the two canonical
datasets (which stay untouched):

  public_comments/all_comments_clean.csv       public comments  (by date_normalized)
  meeting_minutes/all_votes.csv                council votes     (by meeting date)
  meeting_minutes/minutes/**/*.md|*.txt        meeting minutes   (by meeting date)

Everything is bucketed onto one weekly grid: the **Tuesday that ends each council
week** (the cadence is Wed -> the following Tue, the Tuesday being meeting night).
For each week we emit a self-contained bundle:

  weeks/<tuesday>/
    summary.md      orientation: meetings, vote outcomes (incl. contested), comment volume
    comments.csv    that week's public comments (full schema)
    votes.csv       that week's council votes (long format)
    (minutes are linked from summary.md, not copied — REFACTOR_PLAN 5.5)

Plus weeks/index.csv + weeks/index.md linking every week. The bundles are derived
and regenerable -- safe to delete; re-run to rebuild. Sources of truth are the
canonical files above; do aggregate/time-series analysis there, and per-meeting
contextual analysis (comment <-> vote <-> minutes) in the bundles.

Usage:  python3 build_weeks.py
"""

import csv
import datetime
import shutil
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
COMMENTS_CSV = BASE / "public_comments" / "all_comments_clean.csv"
VOTES_CSV = BASE / "meeting_minutes" / "all_votes.csv"
MINUTES_DIR = BASE / "meeting_minutes" / "minutes"
WEEKS = BASE / "weeks"


def week_tuesday(d):
    """The Tuesday that ends the council week (Wed->Tue) containing date d."""
    return d + datetime.timedelta(days=(1 - d.weekday()) % 7)


def iso(s):
    try:
        return datetime.date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f)), csv.DictReader(open(path)).fieldnames


def main():
    if WEEKS.exists():
        shutil.rmtree(WEEKS)
    WEEKS.mkdir()

    # --- bucket comments by council-week Tuesday (on their real date) ---
    crows, ccols = load_csv(COMMENTS_CSV)
    comments = defaultdict(list)
    for r in crows:
        d = iso(r.get("date_normalized", ""))
        if d:
            comments[week_tuesday(d)].append(r)

    # --- bucket votes by council-week Tuesday (meeting date) ---
    vrows, vcols = load_csv(VOTES_CSV)
    votes = defaultdict(list)
    for r in vrows:
        d = iso(r.get("date", ""))
        if d:
            votes[week_tuesday(d)].append(r)

    # --- bucket minutes files by council-week Tuesday (date in filename) ---
    minutes = defaultdict(list)
    for f in sorted(list(MINUTES_DIR.rglob("*.md")) + list(MINUTES_DIR.rglob("*.txt"))):
        if f.name.endswith(".votes.json"):
            continue
        d = iso(f.stem[:10])
        if d:
            minutes[week_tuesday(d)].append(f)

    all_weeks = sorted(set(comments) | set(votes) | set(minutes))
    index = []

    for tue in all_weeks:
        wk = WEEKS / tue.isoformat()
        wk.mkdir()
        period_start = tue - datetime.timedelta(days=6)   # Wed

        # comments.csv
        crs = comments.get(tue, [])
        if crs:
            with open(wk / "comments.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=ccols)
                w.writeheader(); w.writerows(crs)

        # votes.csv
        vrs = votes.get(tue, [])
        if vrs:
            with open(wk / "votes.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=vcols)
                w.writeheader(); w.writerows(vrs)

        # minutes are LINKED, not copied (REFACTOR_PLAN 5.5 — same change as
        # scripts/weeks_lib.py; canonical files live in meeting_minutes/minutes/)
        mfs = minutes.get(tue, [])

        # ---- per-motion view for the summary (votes.csv is member-level) ----
        motions = defaultdict(lambda: {"type": "", "result": "", "title": "",
                                       "aye": [], "nay": [], "abstain": [], "absent": []})
        for r in vrs:
            m = motions[(r["source"], r["motion_no"])]
            m["type"] = r["motion_type"]; m["result"] = r["result"]
            m["title"] = r["motion"]
            m[r["vote"].lower()].append(r["member"])
        contested = [m for m in motions.values() if m["nay"] or m["abstain"]]

        meeting_types = sorted({f.stem[11:].replace("-", " ") for f in mfs})

        # ---- summary.md ----
        L = [f"# Council week ending {tue.isoformat()} (Tue)",
             f"_Comment window {period_start.isoformat()} (Wed) – {tue.isoformat()} (Tue)_", ""]
        L.append(f"- **Meetings:** {len(mfs)}" + (f" — {', '.join(meeting_types)}" if mfs else ""))
        L.append(f"- **Votes:** {len(motions)} motions"
                 + (f", **{len(contested)} contested**" if contested else ""))
        L.append(f"- **Public comments:** {len(crs)}")
        L.append("")
        if contested:
            L.append("## Contested votes (where members split)")
            for m in contested:
                L.append(f"- **{m['result']}** · {m['type']} — {m['title'][:140]}")
                if m["nay"]:
                    L.append(f"  - Nay: {', '.join(m['nay'])}")
                if m["abstain"]:
                    L.append(f"  - Abstain: {', '.join(m['abstain'])}")
            L.append("")
        if crs:
            subs = [r["subject"].strip() for r in crs if r.get("subject", "").strip()]
            top = [s for s, _ in __import__("collections").Counter(subs).most_common(8)]
            if top:
                L.append("## Most common comment subjects")
                L += [f"- {s}" for s in top]
                L.append("")
        L.append("## Files")
        if crs: L.append(f"- `comments.csv` — {len(crs)} public comments")
        if vrs: L.append(f"- `votes.csv` — {len(vrs)} member-vote rows across {len(motions)} motions")
        if mfs: L += [f"- [{f.name}](../../{f.relative_to(BASE).as_posix()})" for f in mfs]
        (wk / "summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")

        index.append({
            "week_tuesday": tue.isoformat(), "period_start": period_start.isoformat(),
            "n_comments": len(crs), "n_meetings": len(mfs),
            "n_motions": len(motions), "n_contested": len(contested),
            "meeting_types": "; ".join(meeting_types),
        })

    # ---- top-level index ----
    icols = ["week_tuesday", "period_start", "n_comments", "n_meetings",
             "n_motions", "n_contested", "meeting_types"]
    with open(WEEKS / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=icols)
        w.writeheader(); w.writerows(index)
    md = ["# Weekly index — SLC City Council", "",
          "One folder per council week (ending Tuesday). Each bundles that week's "
          "public comments, council votes, and meeting minutes + a `summary.md`.", "",
          "| Week (Tue) | Comments | Meetings | Motions | Contested |",
          "|---|---|---|---|---|"]
    for r in index:
        md.append(f"| [{r['week_tuesday']}]({r['week_tuesday']}/summary.md) | "
                  f"{r['n_comments']} | {r['n_meetings']} | {r['n_motions']} | {r['n_contested']} |")
    (WEEKS / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Built {len(all_weeks)} week bundles in {WEEKS.relative_to(BASE)}/")
    print(f"  comments weeks: {len(comments)} | vote weeks: {len(votes)} | "
          f"minutes weeks: {len(minutes)}")
    print(f"  index: weeks/index.csv + weeks/index.md")


if __name__ == "__main__":
    main()
