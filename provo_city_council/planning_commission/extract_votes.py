#!/usr/bin/env python3
"""
extract_votes.py — Provo City PLANNING COMMISSION vote extraction.

Reads the 26 Planning Commission minutes markdown files under
planning_commission/minutes/<year>/<week-monday>/ (indexed in
planning_commission/minutes_index.csv), parses every "Report of Action" (ROA)
vote block, emits one JSON per meeting to
planning_commission/votes/<year>/<week>/<date>_planning-commission-meeting.json,
then rebuilds planning_commission/all_votes.csv (long format, one row per
member-vote) and the validation report.

PROVO PC "REPORT OF ACTION" FORMAT
----------------------------------
Each minutes PDF is the agenda packet with a per-application Report of Action
appended. A vote block looks like:

    On a vote of 7:0, the Planning Commission recommended that the Municipal
    Council approve the above noted application.
    Motion By: Lisa Jensen
    Second By: Adam Shin
    Votes in Favor of Motion: Lisa Jensen, Jonathon Hill, Melissa Kendall, ...
    Votes Against the Motion: Barbara DeSoto, ...

Parsed: tally from "On a vote of N:N"; mover/seconder from "Motion By:" /
"Second By:"; per-member ayes from "Votes in Favor of Motion:"; nays from
"Votes Against/Opposed the Motion:" AND from prose ("X voted against the
motion"); absences from prose ("X was excused" / "not feeling well ... excused").
in-favor -> Aye, against/opposed -> Nay. (No abstain/recuse appear in the
corpus.) Multiple ROAs per meeting -> one motion each.

RECOMMENDATION vs FINAL ACTION (encoded in `result`)
----------------------------------------------------
The ROA text states it explicitly:
  "recommended that the Municipal Council approve/deny" / "recommended
   approval|denial"  -> RECOMMENDATION (advisory to Municipal Council)
       -> result = "Positive recommendation N:N" / "Negative recommendation N:N"
  "approved/denied/continued the above noted application" (PC's OWN final action,
   e.g. Project Plan, Conditional Use, or a Board-of-Adjustment variance)
       -> result = "N:N Approved (Final Action)" / "N:N Denied (Final Action)"
                 / "N:N Continued (Final Action)" / "N:N Tabled (Final Action)"
  anything else -> "N:N Pass" (procedural fallback)
Downstream DBs key on substring "recommend" (-> pc_recommendation) vs its
absence (-> pc_final_action), plus "Positive"/"Negative" for direction. Each
JSON vote also carries an explicit `action_class` field.

Run:  python3 planning_commission/extract_votes.py          (resumable)
      python3 planning_commission/extract_votes.py --force   (re-extract all)

See planning_commission/CLAUDE.md for the full writeup.
"""
import argparse
import csv
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PC = os.path.join(REPO, "planning_commission")
MINUTES_INDEX = os.path.join(PC, "minutes_index.csv")
VOTES_DIR = os.path.join(PC, "votes")
ALL_VOTES_CSV = os.path.join(PC, "all_votes.csv")
ROSTER_CSV = os.path.join(PC, "roster.csv")
VALIDATION_REPORT = os.path.join(VOTES_DIR, "_validation_report.txt")

BODY = "PlanningCommission"
TITLE = "Planning Commission"

# ---------------------------------------------------------------------------
# Roster. Provo PC commissioners are APPOINTED (no election). Surnames are
# UNIQUE across the 2025-2026 roster, so we map primarily on surname and use the
# first name only to disambiguate / catch garbles. Variants (OCR + transcription
# typos) observed in the minutes are folded in below.
# ---------------------------------------------------------------------------
ROSTER = {
    "jensen": "Lisa Jensen",
    "kendall": "Melissa Kendall",
    "hill": "Jonathon Hill",
    "desoto": "Barbara DeSoto",
    "gonzales": "Daniel Gonzales",
    "allen": "Anne Allen",
    "temple": "Joel Temple",
    "wheelwright": "Matt Wheelwright",
    "lyons": "Jon Lyons",
    "south": "Andrew South",
    "shin": "Adam Shin",
    "whitlock": "Jeff Whitlock",
    "metzger": "Tosh Metzger",  # new commissioner, first seen 2026-07-08 (Q3-2026 refresh)
}
# Surname-level OCR/spelling variants -> canonical surname key.
SURNAME_ALIASES = {}
# Accepted first-name forms per commissioner (incl. observed OCR variants).
FIRSTNAMES = {
    "Lisa Jensen": {"lisa"},
    "Melissa Kendall": {"melissa"},
    "Jonathon Hill": {"jonathon", "jonathan", "johnathan", "johathan", "jonhathan"},
    "Barbara DeSoto": {"barbara", "barabara"},
    "Daniel Gonzales": {"daniel", "daneil"},
    "Anne Allen": {"anne"},
    "Joel Temple": {"joel"},
    "Matt Wheelwright": {"matt", "matthew"},
    "Jon Lyons": {"jon", "john"},
    "Andrew South": {"andrew"},
    "Adam Shin": {"adam"},
    "Jeff Whitlock": {"jeff", "jeffrey"},
    "Tosh Metzger": {"tosh"},
}
# first name -> the single commissioner who uses it (no collisions in this roster)
FN_INDEX = {}
for _m, _fns in FIRSTNAMES.items():
    for _fn in _fns:
        FN_INDEX[_fn] = _m
# Full-name aliases for transcription errors where the SURNAME itself is wrong
# but the person is unambiguous. "Anne Black" appears exactly once (2025-02-26,
# Item 1), in a 4:3 vote whose 7th voter is otherwise unaccounted for; "Anne
# Allen" is the only "Anne" across all 26 meetings, so this is a clear typo.
FULL_ALIAS = {
    ("anne", "black"): "Anne Allen",
}
ROLEWORDS = {
    "commissioner", "commissioners", "chair", "chairman", "vice", "acting", "and",
    "the", "motion", "present", "as", "was", "board", "member", "members",
    "planning", "commission", "city", "provo", "municipal", "council", "staff",
    "report", "director", "of", "development", "services", "adjustment", "voted",
    "against", "in", "favor", "opposed",
}


def resolve_name(piece):
    """Map a raw name fragment to a canonical commissioner, or (None, warning)."""
    toks = re.findall(r"[A-Za-z.]+", piece)
    lows = [t.lower().strip(".") for t in toks if t.lower().strip(".") not in ROLEWORDS]
    if not lows:
        return None, None
    for i in range(len(lows) - 1):
        if (lows[i], lows[i + 1]) in FULL_ALIAS:
            return FULL_ALIAS[(lows[i], lows[i + 1])], None
    for i, l in enumerate(lows):
        sn = SURNAME_ALIASES.get(l, l)
        if sn in ROSTER:
            cand = ROSTER[sn]
            fn = lows[i - 1] if i > 0 else ""
            if fn == "" or fn in FIRSTNAMES[cand]:
                return cand, None
            other = FN_INDEX.get(fn)
            if other and other != cand:
                return None, (f"ambiguous name '{piece.strip()}' "
                              f"(surname->{cand}, first name->{other}); skipped")
            return cand, None  # unrecognized first name -> trust unique surname
    return None, None


def resolve_list(text):
    """Resolve a comma/'and'-separated names blob. Returns (members, warnings)."""
    members, warns = [], []
    for piece in re.split(r",|\band\b|\n|;", text):
        piece = piece.strip()
        if not piece:
            continue
        canon, w = resolve_name(piece)
        if w:
            warns.append(w)
        if canon and canon not in members:
            members.append(canon)
    return members, warns


# ---------------------------------------------------------------------------
# Motion-type taxonomy (land-use oriented — PC business is almost entirely
# land-use). Keyed off the application text first, PL-code prefix as fallback.
# ---------------------------------------------------------------------------
PL_PREFIX_TYPE = {
    "PLOTA": "Ordinance Text Amendment",
    "PLGPA": "General Plan Amendment",
    "PLRZ": "Rezone",
    "PLPPA": "Project Plan",
    "PLCP": "Project Plan",
    "PLRCP": "Project Plan",
    "PLRC": "Project Plan",
    "PLCUP": "Conditional Use Permit",
    "PLVAR": "Variance",
    "PLANEX": "Annexation",
    "PLSV": "Vacation",
    "PLFSUB": "Subdivision/Plat",
    "PLPSUB": "Subdivision/Plat",
    "PLLDR": "Design Review",
    "PLRA": "Land-Use/Other",
}


def classify(item_text, pl_code):
    t = item_text.lower()
    if "text amendment" in t or "code amendment" in t or "ordinance amendment" in t:
        return "Ordinance Text Amendment"
    if "general plan" in t or "future land use" in t:
        return "General Plan Amendment"
    if "annex" in t:
        return "Annexation"
    if "conditional use" in t:
        return "Conditional Use Permit"
    if "variance" in t:
        return "Variance"
    if "subdivision" in t or "plat" in t:
        return "Subdivision/Plat"
    if "vacat" in t:
        return "Vacation"
    if "design review" in t:
        return "Design Review"
    if "zone map amendment" in t or "zone change" in t or "rezone" in t \
            or "zoning map" in t or "map amendment" in t:
        return "Rezone"
    if "project plan" in t:
        return "Project Plan"
    if pl_code:
        m = re.match(r"(PL[A-Z]+)", pl_code)
        if m and m.group(1) in PL_PREFIX_TYPE:
            return PL_PREFIX_TYPE[m.group(1)]
    return "Land-Use/Other"


# ---------------------------------------------------------------------------
# Block / field parsing.
# ---------------------------------------------------------------------------
VOTE_RE = re.compile(r"On a vote of\s+(\d+)\s*:\s*(\d+)")
ITEM_RE = re.compile(r"^\s*\*?\s*ITEM\s+\d", re.IGNORECASE)
PAGE_RE = re.compile(r"^\s*Page\s+\d+\s+of\s+\d+", re.IGNORECASE)
PL_RE = re.compile(r"PL[A-Z]+\d+")

FAVOR_RE = re.compile(r"^\s*Votes\s+in\s+Favor\b[^:]*:\s*(.*)", re.IGNORECASE)
# Nay labels vary: "Votes Against the Motion", "Votes Opposed to the Motion",
# "Votes in Opposition to the Motion", "Votes Not in Favor of Motion" (and the
# "Montion" OCR typo) — match any "Votes ..." line carrying a dissent keyword.
AGAINST_RE = re.compile(
    r"^\s*Votes\b[^:]*?\b(?:Against|Opposed|Opposition|Not\s+in\s+Favor)\b[^:]*:\s*(.*)",
    re.IGNORECASE)
MOVER_RE = re.compile(r"^\s*Motion\s+By:\s*(.*)", re.IGNORECASE)
SECOND_RE = re.compile(r"^\s*Second\s+By:\s*(.*)", re.IGNORECASE)

# Lines that terminate a gathered name field's continuation.
STOP_RE = re.compile(
    r"^\s*(?:Votes\s|Motion\s+By|Second\s+By|Includes\b|New\s+findings|•|\*|ITEM\b|"
    r"Conditions\b|RELATED\b|DEVELOPMENT\b|LEGAL\b|STAFF\b|CITY\b|NEIGHBORHOOD\b|"
    r"CONCERNS\b|APPLICANT\b|PLANNING\s+COMMISSION\b|Page\s+\d|TEXT\s+AMENDMENT|"
    r"See\s+Key|Legislative\b|Administrative\b|BUILDING\s+PERMITS|Director\b|"
    r"---|EXHIBIT\b|APPROVED|DENIED|CONTINUED|TABLED|RECOMMENDED)", re.IGNORECASE)


def gather_field(window_lines, label_re):
    """Return the value following a labeled field, joining wrapped continuation
    lines, or None if the label is absent in the window."""
    for i, ln in enumerate(window_lines):
        m = label_re.match(ln)
        if m:
            buf = [m.group(1)]
            j = i + 1
            while j < len(window_lines):
                nl = window_lines[j]
                if not nl.strip():
                    break
                if STOP_RE.search(nl) or re.search(r"was\s+present\s+as", nl, re.IGNORECASE):
                    break
                buf.append(nl.strip())
                j += 1
            return " ".join(buf).strip()
    return None


def names_from_field(value):
    """Resolve a Votes-in-Favor/Against value, dropping any trailing prose
    sentence (names lists never contain '. ')."""
    if not value:
        return [], []
    cut = re.split(r"\.\s", value, 1)[0]  # keep up to first sentence end
    return resolve_list(cut)


def result_and_class(vote_line, fav, agn):
    low = vote_line.lower()
    if "recommend" in low:
        action_class = "pc_recommendation"
        if "approv" in low:
            result = f"Positive recommendation {fav}:{agn}"
        elif "den" in low:
            result = f"Negative recommendation {fav}:{agn}"
        else:
            result = f"Recommendation {fav}:{agn}"
    else:
        action_class = "pc_final_action"
        if "approv" in low:
            result = f"{fav}:{agn} Approved (Final Action)"
        elif "den" in low:
            result = f"{fav}:{agn} Denied (Final Action)"
        elif "continu" in low:
            result = f"{fav}:{agn} Continued (Final Action)"
        elif "tabl" in low:
            result = f"{fav}:{agn} Tabled (Final Action)"
        else:
            result = f"{fav}:{agn} Pass"
    return result, action_class


def parse_meeting(text):
    lines = text.split("\n")
    n = len(lines)
    vote_idxs = [i for i, ln in enumerate(lines) if VOTE_RE.search(ln)]
    item_idxs = [i for i, ln in enumerate(lines) if ITEM_RE.match(ln)]
    page_idxs = [i for i, ln in enumerate(lines) if PAGE_RE.match(ln)]

    votes = []
    warnings = []
    motion_no = 0
    for vi in vote_idxs:
        m = VOTE_RE.search(lines[vi])
        fav, agn = int(m.group(1)), int(m.group(2))
        vote_line = lines[vi]
        # grab a possible wrap of the vote sentence (next non-blank line)
        if vi + 1 < n and "application" not in vote_line.lower() and lines[vi + 1].strip():
            vote_line = vote_line + " " + lines[vi + 1].strip()

        # nearest preceding ITEM line -> description + PL code
        prev_items = [ii for ii in item_idxs if ii < vi]
        ii = prev_items[-1] if prev_items else None
        desc, pl_code = "", ""
        if ii is not None:
            dbuf = []
            for k in range(ii, vi):
                if "the following action was taken" in lines[k].lower():
                    break
                dbuf.append(lines[k].strip())
            desc = re.sub(r"\s+", " ", " ".join(dbuf)).strip()
            plm = PL_RE.search(desc)
            pl_code = plm.group(0) if plm else ""

        # field window: vi+1 .. next page-break/item/vote (whichever first)
        ends = [e for e in page_idxs + item_idxs + vote_idxs if e > vi]
        win_end = min(ends) if ends else min(vi + 30, n)
        window = lines[vi + 1:win_end]

        aye, w1 = names_from_field(gather_field(window, FAVOR_RE))
        nay, w2 = names_from_field(gather_field(window, AGAINST_RE))
        warnings += w1 + w2

        # prose nays: "X voted against the motion"
        wtext = "\n".join(window)
        for pm in re.finditer(
                r"((?:Commissioner\s+)?[A-Z][a-zA-Z.]+\s+[A-Z][a-zA-Z.]+)\s+voted\s+against",
                wtext):
            canon, w = resolve_name(pm.group(1))
            if w:
                warnings.append(w)
            if canon and canon not in nay:
                nay.append(canon)

        # prose absences: "X was excused" / "X ... not feeling well ... excused" / absent
        absent = []
        for pm in re.finditer(
                r"([A-Z][a-zA-Z.]+\s+[A-Z][a-zA-Z.]+)\s+was\s+"
                r"(?:not\s+feeling\s+well|excused|absent)", wtext):
            canon, _ = resolve_name(pm.group(1))
            if canon and canon not in absent and canon not in aye and canon not in nay:
                absent.append(canon)

        mover, _ = (resolve_name(gather_field(window, MOVER_RE) or "")
                    if gather_field(window, MOVER_RE) else (None, None))
        seconder, _ = (resolve_name(gather_field(window, SECOND_RE) or "")
                       if gather_field(window, SECOND_RE) else (None, None))

        acting_body = ("BoardOfAdjustment"
                       if re.search(r"board of adjustment", vote_line, re.IGNORECASE)
                       else "PlanningCommission")
        result, action_class = result_and_class(vote_line, fav, agn)
        mtype = classify(desc, pl_code)

        names_recorded = bool(aye or nay or absent)
        motion_no += 1
        votes.append({
            "motion_no": motion_no,
            "motion": desc[:600],
            "body": BODY,
            "acting_body": acting_body,
            "pl_code": pl_code,
            "motion_type": mtype,
            "action_class": action_class,
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "aye": aye,
            "nay": nay,
            "abstain": [],
            "absent": absent,
            "recuse": [],
            "names_recorded": names_recorded,
            "_tally": [fav, agn],
        })
    return votes, sorted(set(warnings))


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def load_index():
    with open(MINUTES_INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def json_path_for(row):
    rel = row["path"].replace("planning_commission/minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    rows = load_index()
    unparsed = []
    for row in rows:
        md_path = os.path.join(REPO, row["path"])
        if not os.path.exists(md_path):
            unparsed.append(row["path"] + " (missing)")
            continue
        out_json = json_path_for(row)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        if os.path.exists(out_json) and not args.force:
            continue
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
        try:
            votes, warns = parse_meeting(text)
        except Exception as e:  # noqa
            unparsed.append(f"{row['path']} (parse error: {e})")
            continue
        clean = []
        for v in votes:
            v.pop("_tally", None)
            clean.append(v)
        meeting_obj = {
            "date": row["date"],
            "title": TITLE,
            "source": row["path"],
            "format": row.get("format", "text"),
            "parse_warnings": warns,
            "votes": clean,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting_obj, f, indent=1, ensure_ascii=False)

    rebuild_csv()
    rebuild_roster()
    stats = recompute_stats()
    mismatches = validate_tallies()
    write_validation(stats, mismatches)

    print(json.dumps({
        "meetings_processed": stats["meetings"],
        "motions_extracted": stats["motions"],
        "member_vote_rows": stats["member_rows"],
        "recommendations": stats["recommendations"],
        "final_actions": stats["final_actions"],
        "contested": stats["contested"],
        "tally_only": stats["tally_only"],
        "tally_mismatches": len(mismatches),
        "distinct_commissioners": stats["distinct"],
        "unparsed": unparsed,
    }, indent=2))


def iter_jsons():
    for dp, _, files in os.walk(VOTES_DIR):
        for fn in sorted(files):
            if fn.endswith(".json") and not fn.startswith("_"):
                yield os.path.join(dp, fn)


def rebuild_csv():
    rows_out = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        date = mtg["date"]
        year = date[:4]
        source = mtg["source"]
        for v in mtg["votes"]:
            base = {
                "date": date, "year": year, "title": TITLE, "body": BODY,
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": source,
            }
            emitted = False
            for label, key in (("Aye", "aye"), ("Nay", "nay"), ("Abstain", "abstain"),
                               ("Absent", "absent"), ("Recuse", "recuse")):
                for member in v.get(key, []):
                    r = dict(base)
                    r["member"] = member
                    r["vote"] = label
                    rows_out.append(r)
                    emitted = True
            if not emitted:
                r = dict(base)
                r["member"] = ""
                r["vote"] = ""
                rows_out.append(r)
    rows_out.sort(key=lambda r: (r["date"], r["motion_no"], r["member"]))
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    with open(ALL_VOTES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows_out:
            w.writerow({c: r.get(c, "") for c in cols})


def rebuild_roster():
    seen = {}  # member -> {first, last, meetings:set}
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        date = mtg["date"]
        present = set()
        for v in mtg["votes"]:
            for key in ("aye", "nay", "abstain", "absent", "recuse"):
                present.update(v.get(key, []))
            if v.get("mover"):
                present.add(v["mover"])
            if v.get("seconder"):
                present.add(v["seconder"])
        for mbr in present:
            d = seen.setdefault(mbr, {"first": date, "last": date, "mtgs": set()})
            d["first"] = min(d["first"], date)
            d["last"] = max(d["last"], date)
            d["mtgs"].add(date)
    with open(ROSTER_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        for mbr in sorted(seen, key=lambda m: (-len(seen[m]["mtgs"]), m)):
            d = seen[mbr]
            w.writerow([mbr, d["first"], d["last"], len(d["mtgs"])])


def recompute_stats():
    meetings = motions = member_rows = recs = finals = contested = tally_only = 0
    distinct = set()
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        for v in mtg["votes"]:
            motions += 1
            if v["action_class"] == "pc_recommendation":
                recs += 1
            else:
                finals += 1
            if v["nay"] or v["abstain"] or v["recuse"]:
                contested += 1
            if not v["names_recorded"]:
                tally_only += 1
            for key in ("aye", "nay", "abstain", "absent", "recuse"):
                member_rows += len(v.get(key, []))
                distinct.update(v.get(key, []))
    return {"meetings": meetings, "motions": motions, "member_rows": member_rows,
            "recommendations": recs, "final_actions": finals, "contested": contested,
            "tally_only": tally_only, "distinct": len(distinct)}


def validate_tallies():
    """Flag motions where the named aye/nay counts disagree with the printed
    tally. Absences are excluded from the tally by definition. Logged, never
    auto-corrected — names are kept verbatim from the minutes."""
    lines = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        for v in mtg["votes"]:
            mt = re.search(r"(\d+):(\d+)", v["result"])
            if not mt:
                continue
            fav, agn = int(mt.group(1)), int(mt.group(2))
            na, nn = len(v["aye"]), len(v["nay"])
            if na != fav or nn != agn:
                lines.append(
                    f"{mtg['date']} motion {v['motion_no']}: aye={na} nay={nn} "
                    f"but printed tally {fav}:{agn} :: {v['result']}")
    return lines


def write_validation(stats, mismatches):
    os.makedirs(VOTES_DIR, exist_ok=True)
    # off-roster check (by construction members are canonical, but verify)
    off = []
    canon_vals = set(ROSTER.values())
    out_of_range = []
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        if not (mtg["date"][:4] >= "2020"):
            out_of_range.append(mtg["date"])
        for v in mtg["votes"]:
            for key in ("aye", "nay", "abstain", "absent", "recuse"):
                for mbr in v.get(key, []):
                    if mbr not in canon_vals:
                        off.append(f"{mtg['date']} m{v['motion_no']}: {mbr}")
    with open(VALIDATION_REPORT, "w", encoding="utf-8") as f:
        f.write("Provo Planning Commission — vote extraction validation\n")
        f.write("=" * 70 + "\n")
        f.write(f"Meetings: {stats['meetings']}  Motions: {stats['motions']}  "
                f"Member-vote rows: {stats['member_rows']}\n")
        f.write(f"Recommendations: {stats['recommendations']}  "
                f"Final actions: {stats['final_actions']}  "
                f"Contested: {stats['contested']}  "
                f"Tally-only: {stats['tally_only']}\n")
        f.write(f"Distinct commissioners: {stats['distinct']}\n")
        f.write(f"Off-roster members: {len(off)}\n")
        f.write(f"Out-of-range dates (<2020): {len(out_of_range)}\n")
        f.write("-" * 70 + "\n")
        f.write("COVERAGE: Provo published consolidated PC minutes (agenda packet + "
                "Report of Action) starting 2025. 2020-2024 PC minutes do not exist "
                "on AgendaCenter / OnBase (documented gap, see CLAUDE.md). Data floor "
                "2020, but PC data only exists 2025+.\n")
        f.write("-" * 70 + "\n")
        if off:
            f.write("OFF-ROSTER (should be 0):\n" + "\n".join(off) + "\n")
        f.write("\nTALLY vs NAMED-COUNT MISMATCHES (logged, NOT auto-corrected):\n")
        if mismatches:
            f.write("\n".join(mismatches) + "\n")
        else:
            f.write("(none)\n")
        # gather parse warnings
        warns = []
        for jp in iter_jsons():
            with open(jp, encoding="utf-8") as f2:
                mtg = json.load(f2)
            for w in mtg.get("parse_warnings", []):
                warns.append(f"{mtg['date']}: {w}")
        f.write("\nPARSE WARNINGS (ambiguous/garbled tokens, NOT mapped — not guessed):\n")
        f.write(("\n".join(warns) + "\n") if warns else "(none)\n")


if __name__ == "__main__":
    main()
