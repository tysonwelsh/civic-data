#!/usr/bin/env python3
"""
extract_roa_votes.py — integrate the recovered 2020-2024 Provo Planning Commission
Report-of-Action record (../pmn_backfill/) into the structured
planning_commission/all_votes.csv.

WHY THIS EXISTS
    The city never published consolidated PC minutes for 2020-2024 (a documented
    SOURCE gap — see minutes_unrecovered.csv), so extract_votes.py's structured
    record starts 2025-02-26. But the per-item PC "Reports of Action" for
    2020-2024 were later recovered from Utah Public Notice into ../pmn_backfill/.
    They are the SAME ROA format extract_votes.py already parses for 2025+, so we
    REUSE that audited parser here rather than writing a second one.

PROVENANCE
    A `provenance` column is added to all_votes.csv (and flows into the db):
      minutes  — canonical rows from extract_votes.py (AgendaCenter consolidated
                 minutes, born-digital, the audited layer)
      pmn_roa  — rows recovered here from pmn_backfill Reports of Action
                 (Utah Public Notice; additive, not previously audited)

RUN (after extract_votes.py):
    python3 planning_commission/extract_votes.py         # builds canonical all_votes.csv
    python3 planning_commission/extract_roa_votes.py     # merges ROAs + provenance
    python3 planning_commission/validate_votes.py        # QA (canonical rows)

    Idempotent: each run rebuilds the merged all_votes.csv from the canonical CSV
    plus a fresh parse of pmn_backfill. Re-running extract_votes.py ALONE reverts
    the CSV to canonical-only (no provenance column) until this is re-run.
"""
import os
import re
import csv
import sys
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PMN_INDEX = os.path.join(REPO, "pmn_backfill", "index.csv")
PMN_TEXT = os.path.join(REPO, "pmn_backfill", "text")
ALL_VOTES = os.path.join(HERE, "all_votes.csv")
REPORT = os.path.join(HERE, "votes", "_roa_extract_report.txt")

sys.path.insert(0, HERE)
import extract_votes as ev  # reuse the audited ROA parser (parse_meeting/classify/...)

CANON_PROVENANCE = "minutes"
ROA_PROVENANCE = "pmn_roa"

# ---------------------------------------------------------------------------
# Born-digital name resolution for the pre-2025 commissioners.
#
# The pmn ROAs are born-digital (0 OCR), so names arrive as clean "First Last".
# extract_votes.py's ROSTER only knows the 2025+ commissioners, so we:
#   1. canonicalize any name that matches the 2025 roster (folds e.g.
#      "Dan Gonzales" -> "Daniel Gonzales" AND unifies members who span both
#      eras onto ONE person_id downstream), then
#   2. trust the clean full name verbatim for pre-2025-only commissioners
#      (Andrew Howard, Robert Knudsen, ...), who the roster cannot know.
# This replaces ev.resolve_name / ev.resolve_list via monkeypatch so the audited
# parse_meeting() uses it unchanged.
# ---------------------------------------------------------------------------
# Extended first-name forms for cross-era nicknames not in the 2025 roster map.
FIRSTNAME_EXT = {m: set(v) for m, v in ev.FIRSTNAMES.items()}
FIRSTNAME_EXT["Daniel Gonzales"] |= {"dan"}


def roa_resolve_name(piece):
    toks = [t for t in re.findall(r"[A-Za-z.'\-]+", piece)
            if t.lower().strip(".") not in ev.ROLEWORDS]
    if len(toks) < 2:
        return None, None
    lows = [t.lower().strip(".") for t in toks]
    # (1) Fold onto the canonical 2025 roster ONLY when BOTH surname AND first
    # name match — i.e. genuinely the same person spanning both eras. Surnames
    # are NOT unique across eras (e.g. Deborah Jensen (pre-2025 Chair) vs Lisa
    # Jensen), so a surname-only fold would wrongly merge two people. When the
    # surname matches a 2025 member but the first name doesn't, it's a DIFFERENT
    # pre-2025 commissioner → fall through and keep the verbatim name.
    for i, l in enumerate(lows):
        sn = ev.SURNAME_ALIASES.get(l, l)
        if sn in ev.ROSTER:
            cand = ev.ROSTER[sn]
            fn = lows[i - 1] if i > 0 else ""
            if fn in FIRSTNAME_EXT[cand]:
                return cand, None
            break
    # (2) pre-2025-only commissioner: trust the clean born-digital full name
    return " ".join(toks), None


def roa_resolve_list(text):
    members, warns = [], []
    for piece in re.split(r",|\band\b|\n|;", text):
        piece = piece.strip()
        if not piece:
            continue
        canon, w = roa_resolve_name(piece)
        if w:
            warns.append(w)
        if canon and canon not in members:
            members.append(canon)
    return members, warns


ev.resolve_name = roa_resolve_name
ev.resolve_list = roa_resolve_list


# ---------------------------------------------------------------------------
# Tally-format normalization. The 2020-2024 ROAs carry a few formatting variants
# the audited VOTE_RE ("On a vote of N:N") doesn't match verbatim:
#   "On a vote of4:1"  (glued)   "On a vote of 9-0" (dash)
#   "Approved 4:0"     (some early ROAs omit the "On a vote of" preamble)
# Normalize the text so ev.parse_meeting sees the canonical phrasing.
# ---------------------------------------------------------------------------
_VOTE_NORM = re.compile(r"On a vote of\s*(\d+)\s*[-:]\s*(\d+)", re.IGNORECASE)
_BARE_ACTION = re.compile(r"\b(Approved|Denied|Continued|Tabled)\s+(\d+)\s*[-:]\s*(\d+)",
                          re.IGNORECASE)


def preprocess(text):
    # The pmn ROAs head items "*ITEM #4"; the 2025 canonical minutes use "*ITEM 4".
    # The audited ITEM_RE only matches the latter, so strip the "#" or every
    # recovered motion loses its description + PL code + motion_type.
    text = re.sub(r"(\bITEM)\s*#\s*(\d)", r"\1 \2", text, flags=re.IGNORECASE)
    text = _VOTE_NORM.sub(lambda m: f"On a vote of {m.group(1)}:{m.group(2)}", text)
    if not re.search(r"On a vote of \d+:\d+", text, re.IGNORECASE):
        m = _BARE_ACTION.search(text)
        if m:
            verb = m.group(1).lower()
            inject = (f"On a vote of {m.group(2)}:{m.group(3)}, the Planning Commission "
                      f"{verb} the above noted application. ")
            text = text[:m.start()] + inject + text[m.start():]
    return text


def item_no(slug):
    m = re.search(r"_item(\d+)_", slug)
    return int(m.group(1)) if m else 0


def main():
    # canonical PC meeting dates (to skip ROA dates already structured)
    canon_dates = set()
    canon_rows = []
    if os.path.exists(ALL_VOTES):
        with open(ALL_VOTES, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                # idempotent: drop any prior pmn_roa rows so we re-parse fresh;
                # only the canonical (minutes) rows seed canon_dates.
                if r.get("provenance", "") == ROA_PROVENANCE:
                    continue
                canon_dates.add(r["date"])
                canon_rows.append(r)
    else:
        sys.exit("run extract_votes.py first — canonical all_votes.csv is missing")

    # gather pmn PC ROA files, grouped by date, excluding dates already structured
    by_date = collections.defaultdict(list)
    with open(PMN_INDEX, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["body"] != "PlanningCommission" or r["doc_kind"] != "roa":
                continue
            if r["date"] in canon_dates:
                continue
            by_date[r["date"]].append(r["slug"])

    # per-meeting recovered-source files (real, traceable — the concatenated ROA
    # text we parse). Written under pmn_backfill/roa/ so `source` resolves on disk
    # and clearly marks the recovered provenance.
    roa_src_dir = os.path.join(REPO, "pmn_backfill", "roa")
    os.makedirs(roa_src_dir, exist_ok=True)

    roa_rows = []
    parsed_meetings = parsed_motions = 0
    novote_files = []
    all_warnings = []
    for date in sorted(by_date):
        slugs = sorted(by_date[date], key=item_no)
        raw_chunks, parse_chunks = [], []
        for slug in slugs:
            p = os.path.join(PMN_TEXT, slug + ".txt")
            if not os.path.exists(p):
                continue
            with open(p, encoding="utf-8") as f:
                original = f.read()
            raw_chunks.append(f"<!-- {slug} -->\n{original}")
            parse_chunks.append(preprocess(original))
        if not parse_chunks:
            continue
        votes, warnings = ev.parse_meeting("\n\n".join(parse_chunks))
        all_warnings += [f"{date}: {w}" for w in warnings]
        if not votes:
            novote_files += slugs
            continue
        parsed_meetings += 1
        # write the recovered-source artifact and reference it
        rel_src = f"pmn_backfill/roa/{date}_pc-roa.md"
        with open(os.path.join(REPO, rel_src), "w", encoding="utf-8") as f:
            f.write(f"# Recovered Planning Commission Reports of Action — {date}\n")
            f.write("# Source: Utah Public Notice (pmn_backfill); concatenated per-item ROA text.\n\n")
            f.write("\n\n".join(raw_chunks))
        source = rel_src
        for v in votes:
            parsed_motions += 1
            base = {
                "date": date, "year": date[:4], "title": ev.TITLE, "body": ev.BODY,
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": source, "provenance": ROA_PROVENANCE,
            }
            emitted = False
            for label, key in (("Aye", "aye"), ("Nay", "nay"), ("Abstain", "abstain"),
                               ("Absent", "absent"), ("Recuse", "recuse")):
                for member in v.get(key, []):
                    row = dict(base, member=member, vote=label)
                    roa_rows.append(row)
                    emitted = True
            if not emitted:
                roa_rows.append(dict(base, member="", vote=""))

    # merge: canonical rows (provenance=minutes) + recovered ROA rows (pmn_roa)
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    out = []
    for r in canon_rows:
        r = dict(r)
        r.setdefault("provenance", CANON_PROVENANCE)
        if not r["provenance"]:
            r["provenance"] = CANON_PROVENANCE
        out.append(r)
    out += roa_rows
    out.sort(key=lambda r: (r["date"], int(r["motion_no"]), r.get("member", "")))
    with open(ALL_VOTES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in out:
            w.writerow({c: r.get(c, "") for c in cols})

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("Provo PC ROA integration (pmn_backfill -> all_votes.csv)\n")
        f.write(f"recovered meetings parsed : {parsed_meetings}\n")
        f.write(f"recovered motions         : {parsed_motions}\n")
        f.write(f"recovered member-vote rows: {sum(1 for r in roa_rows if r['member'])}\n")
        f.write(f"canonical rows (minutes)  : {len(canon_rows)}\n")
        f.write(f"merged total rows         : {len(out)}\n")
        f.write(f"files with no parsed vote : {len(novote_files)}\n")
        for s in novote_files:
            f.write(f"    no-vote: {s}\n")
        f.write(f"name/parse warnings       : {len(all_warnings)}\n")
        for w in all_warnings:
            f.write(f"    warn: {w}\n")

    print(f"merged all_votes.csv: {len(canon_rows)} canonical (minutes) + "
          f"{len(roa_rows)} recovered (pmn_roa) rows; "
          f"{parsed_meetings} recovered meetings / {parsed_motions} motions; "
          f"{len(novote_files)} no-vote files. report -> {os.path.relpath(REPORT, REPO)}")


if __name__ == "__main__":
    main()
