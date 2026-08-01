"""
Shared build_weeks logic (REFACTOR_PLAN 4.1) — lifted verbatim from the 15
near-identical per-city build_weeks.py copies (2026-07-07). Each city's
build_weeks.py is now a thin config stub that calls build().

Build a derived, analysis-friendly weekly view unifying the canonical datasets
(which stay untouched):

  public_comments/all_comments_clean.csv   public comments (by date_normalized) [optional]
  meeting_minutes/all_votes.csv            council votes    (by meeting date)
  meeting_minutes/minutes/**/*.md|*.txt    meeting minutes  (by meeting date)

Everything is bucketed onto one weekly grid: the council meeting_weekday that ends
each council week.

For each week we emit a bundle:
  weeks/<weekday-date>/{summary.md, comments.csv, votes.csv}
plus weeks/index.{md,csv}. Minutes are LINKED from summary.md (relative paths into
meeting_minutes/minutes/), not copied — since 2026-07-07 (REFACTOR_PLAN 5.5); the
copies used to double the markdown footprint. Derived + regenerable — safe to
delete; re-run to rebuild.

Parameters (exactly the observed per-city deltas — nothing speculative):
  city_dir             the city repo dir (stubs pass Path(__file__).resolve().parent)
  city_name            e.g. "Lehi", "West Valley City"
  meeting_weekday      Mon=0 Tue=1 Wed=2 Thu=3 ... the council meeting day
  index_council_label  "Council" (default) or "City Council" (provo, st_george)

slc_city_council/build_weeks.py is a documented divergence (predates this lib;
PC/comments handling differs) and does NOT use this module.
"""

import csv
import datetime
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path


def iso(s):
    try:
        return datetime.date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        return None


def load_csv(path):
    if not path.exists():
        return [], []
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(path, newline="", encoding="utf-8") as f:
        cols = csv.DictReader(f).fieldnames or []
    return rows, cols


def build(city_dir, city_name, meeting_weekday, index_council_label="Council"):
    CITY = city_name
    MEETING_WEEKDAY = meeting_weekday

    BASE = Path(city_dir).resolve()
    COMMENTS_CSV = BASE / "public_comments" / "all_comments_clean.csv"
    VOTES_CSV = BASE / "meeting_minutes" / "all_votes.csv"
    MINUTES_DIR = BASE / "meeting_minutes" / "minutes"
    WEEKS = BASE / "weeks"

    def week_end(d):
        """The MEETING_WEEKDAY that ends the council week containing date d."""
        return d + datetime.timedelta(days=(MEETING_WEEKDAY - d.weekday()) % 7)

    if WEEKS.exists():
        shutil.rmtree(WEEKS)
    WEEKS.mkdir()

    crows, ccols = load_csv(COMMENTS_CSV)
    comments = defaultdict(list)
    for r in crows:
        d = iso(r.get("date_normalized", "")) or iso(r.get("date", ""))
        if d:
            comments[week_end(d)].append(r)

    vrows, vcols = load_csv(VOTES_CSV)
    votes = defaultdict(list)
    for r in vrows:
        d = iso(r.get("date", ""))
        if d:
            votes[week_end(d)].append(r)

    minutes = defaultdict(list)
    if MINUTES_DIR.exists():
        for f in sorted(list(MINUTES_DIR.rglob("*.md")) + list(MINUTES_DIR.rglob("*.txt"))):
            if f.name.endswith(".votes.json"):
                continue
            d = iso(f.stem[:10])
            if not d:
                # DEBT fix 2026-07-31: not every city date-prefixes its minutes
                # filenames (bluffdale: council_2020-09-09_807.md, 166/166 files),
                # which left every such city's weeks bundle printing "Meetings: 0"
                # with no minutes links. Fall back to the first ISO date anywhere
                # in the filename, then anywhere in the path (the date-named
                # parent dirs).
                m = (re.search(r"\d{4}-\d{2}-\d{2}", f.name)
                     or re.search(r"\d{4}-\d{2}-\d{2}", str(f)))
                if m:
                    d = iso(m.group(0))
            if d:
                minutes[week_end(d)].append(f)

    # DEBT fix 2026-07-31 (part 2): votes recovered from Utah Public Notice live
    # in pmn_backfill/text/, outside minutes/ — their weeks printed "Meetings: 0"
    # beside real votes (70 bundles across 8 cities). Link the recovered text for
    # any date that has NO minutes-dir file (mirrors the G5 FTS dedup rule:
    # promoted copies win; a pmn file is linked only where it is the sole record).
    dated_in_minutes = set()
    for fl in minutes.values():
        for f in fl:
            m = re.search(r"\d{4}-\d{2}-\d{2}", f.name) or \
                re.search(r"\d{4}-\d{2}-\d{2}", str(f))
            if m:
                dated_in_minutes.add(m.group(0))
    PMN_TEXT = BASE / "pmn_backfill" / "text"
    if PMN_TEXT.exists():
        for f in sorted(list(PMN_TEXT.glob("*.md")) + list(PMN_TEXT.glob("*.txt"))):
            m = re.search(r"\d{4}-\d{2}-\d{2}", f.name)
            date_str = m.group(0) if m else None
            if not date_str:
                # some cities' pmn filenames carry no date (vineyard:
                # RDA_2598_457993.txt) — peek at the file head for an ISO or
                # long-form ("December 12, 2018") date
                try:
                    head = open(f, encoding="utf-8", errors="replace").read(500)
                except OSError:
                    head = ""
                m2 = re.search(r"\d{4}-\d{2}-\d{2}", head)
                if m2:
                    date_str = m2.group(0)
                else:
                    m3 = re.search(
                        r"(January|February|March|April|May|June|July|August|"
                        r"September|October|November|December)\s+(\d{1,2}),?\s+"
                        r"(20\d\d)", head)
                    if m3:
                        month = ("January February March April May June July "
                                 "August September October November December"
                                 ).split().index(m3.group(1)) + 1
                        date_str = "%s-%02d-%02d" % (m3.group(3), month,
                                                     int(m3.group(2)))
            if not date_str or date_str in dated_in_minutes:
                continue
            d = iso(date_str)
            if d:
                minutes[week_end(d)].append(f)

    all_weeks = sorted(set(comments) | set(votes) | set(minutes))
    index = []

    for wend in all_weeks:
        wk = WEEKS / wend.isoformat()
        wk.mkdir()
        period_start = wend - datetime.timedelta(days=6)

        crs = comments.get(wend, [])
        if crs and ccols:
            with open(wk / "comments.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=ccols)
                w.writeheader(); w.writerows(crs)

        vrs = votes.get(wend, [])
        if vrs and vcols:
            with open(wk / "votes.csv", "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=vcols)
                w.writeheader(); w.writerows(vrs)

        # minutes are LINKED, not copied (REFACTOR_PLAN 5.5 — the copies doubled the
        # markdown footprint and added no retrieval value; canonical files live in
        # meeting_minutes/minutes/, full-text searchable via cities.db fts_minutes)
        mfs = minutes.get(wend, [])

        motions = defaultdict(lambda: {"type": "", "result": "", "title": "",
                                       "aye": [], "nay": [], "abstain": [], "absent": []})
        for r in vrs:
            m = motions[(r.get("source", ""), r.get("motion_no", ""))]
            m["type"] = r.get("motion_type", ""); m["result"] = r.get("result", "")
            m["title"] = r.get("motion", "")
            v = r.get("vote", "").lower()
            if v in m:
                m[v].append(r.get("member", ""))
        contested = [m for m in motions.values() if m["nay"] or m["abstain"]]

        meeting_types = sorted({f.stem[11:].replace("-", " ") for f in mfs})

        L = [f"# {CITY} council week ending {wend.isoformat()}",
             f"_Window {period_start.isoformat()} – {wend.isoformat()}_", ""]
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
            subs = [r.get("subject", "").strip() for r in crs if r.get("subject", "").strip()]
            top = [s for s, _ in Counter(subs).most_common(8)]
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
            "week_ending": wend.isoformat(), "period_start": period_start.isoformat(),
            "n_comments": len(crs), "n_meetings": len(mfs),
            "n_motions": len(motions), "n_contested": len(contested),
            "meeting_types": "; ".join(meeting_types),
        })

    icols = ["week_ending", "period_start", "n_comments", "n_meetings",
             "n_motions", "n_contested", "meeting_types"]
    with open(WEEKS / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=icols)
        w.writeheader(); w.writerows(index)
    md = [f"# Weekly index — {CITY} {index_council_label}", "",
          "One folder per council week. Each bundles that week's public comments and "
          "council votes + a `summary.md` that links the week's minutes files "
          "(canonical copies live in `meeting_minutes/minutes/`).", "",
          "| Week | Comments | Meetings | Motions | Contested |",
          "|---|---|---|---|---|"]
    for r in index:
        md.append(f"| [{r['week_ending']}]({r['week_ending']}/summary.md) | "
                  f"{r['n_comments']} | {r['n_meetings']} | {r['n_motions']} | {r['n_contested']} |")
    (WEEKS / "index.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Built {len(all_weeks)} week bundles in {WEEKS.relative_to(BASE)}/")
    print(f"  comments weeks: {len(comments)} | vote weeks: {len(votes)} | "
          f"minutes weeks: {len(minutes)}")
