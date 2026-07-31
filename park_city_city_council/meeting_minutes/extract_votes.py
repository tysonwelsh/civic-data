#!/usr/bin/env python3
"""
extract_votes.py — Park City (Utah) City Council vote extraction.

Reads the 238 minutes markdown files under meeting_minutes/minutes/<year>/<week>/
(indexed in meeting_minutes/minutes_index.csv), parses each recorded motion + vote,
emits one JSON per meeting to meeting_minutes/votes/<year>/<week>/<date>_<slug>.json,
then rebuilds meeting_minutes/all_votes.csv (long format, one row per member-vote).

Park City CivicClerk minutes record a motion in prose —
  "Council Member Parigian moved to continue Ordinance No. 2024-09 ...
   Council Member Rubell seconded the motion."
— immediately (or a paragraph of discussion) followed by a tabular result block:
  RESULT:  CONTINUED TO A DATE UNCERTAIN
  AYES:    Council Members Ciraco, Parigian, and Rubell
  NAYS:    Council Members Dickey and Toly
  EXCUSED: Council Member <name>
  ABSTAIN: Council Member <name>
We map AYE->aye, NAY->nay, ABSTAIN(ED)->abstain, EXCUSED/ABSENT->absent,
RECUSE(D)->recuse. When only a RESULT word is printed with no member list (rare —
"approved unanimously" prose) we set names_recorded=false and leave the lists EMPTY:
we never guess who voted how.

Governing body {Council, RDA, HA}: mid-meeting the Council recesses and convenes as
the Park City REDEVELOPMENT AGENCY (RDA) or the HOUSING AUTHORITY (HA) — same people,
board capacity. The minutes mark this with a standalone section header
"PARK CITY REDEVELOPMENT AGENCY MEETING" / "PARK CITY HOUSING AUTHORITY MEETING"
(the recurring page FOOTER "PARK CITY COUNCIL MEETING / SUMMIT COUNTY, UTAH" is NOT a
header and is ignored). While sitting as a board the minutes say "Board Member" / "Chair"
and the result block reads "AYES: Board Members ...". Body is decided per motion: a
"Board Member(s)" signal -> the most-recent board header (RDA or HA); otherwise Council.

Mayor does NOT vote (council-manager form) except to break a tie, in which case the
minutes literally list "Mayor <Name>" inside an AYES/NAYS block. Those tie-break rows are
captured and flagged (mayor_tiebreak=true). A mayor's surname must NEVER appear in a
routine (un-prefixed) member list during their mayoral term; validate_votes.py asserts
this. Mayoral terms: Beerman <2022, Worel 2022-2025, Dickey 2026+ (each was a voting
council member BEFORE their mayoral term).

Run:  python3 meeting_minutes/extract_votes.py          (resumable: skips existing JSON)
      python3 meeting_minutes/extract_votes.py --force   (re-extract all)

See meeting_minutes/CLAUDE.md for the full pipeline + heuristics writeup.
"""
import argparse
import csv
import json
import os
import re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MM = os.path.join(REPO, "meeting_minutes")
MINUTES_INDEX = os.path.join(MM, "minutes_index.csv")
VOTES_DIR = os.path.join(MM, "votes")
ALL_VOTES_CSV = os.path.join(MM, "all_votes.csv")

# ---------------------------------------------------------------------------
# Canonical roster. Surname -> "First Last". Park City Council = Mayor + 5
# members. Built by scanning every AYES/NAYS/ABSTAIN/EXCUSED/RECUSED member list
# and every roll-call roster in the 2020-2026 minutes; no two members share a
# surname (no disambiguation needed). Beerman/Worel/Dickey also served as Mayor
# (see MAYOR_TERMS) — when Mayor they do not vote except a flagged tie-break.
# County councilors / planning commissioners who appear only in joint-meeting
# narrative (Armstrong, Robinson, Stevens, Harte, Wright, Clyde, Thimm, ...) are
# deliberately NOT in this map, so they are never bucketed as Park City voters.
# ---------------------------------------------------------------------------
ROSTER = {
    "worel": "Nann Worel",        # council 2020-21, Mayor 2022-2025
    "toly": "Tana Toly",          # council; Mayor Pro Tem
    "dickey": "Ryan Dickey",      # council 2022-2025, Mayor 2026+
    "gerber": "Becca Gerber",
    "doilney": "Max Doilney",
    "rubell": "Jeremy Rubell",
    "ciraco": "Bill Ciraco",
    "parigian": "Ed Parigian",
    "henney": "Tim Henney",       # council pre-2022
    "joyce": "Steve Joyce",       # council pre-2022
    "beerman": "Andy Beerman",    # Mayor 2020-2021
    "zegarra": "Diego Zegarra",   # council 2024+
    "miller": "Molly Miller",     # council 2024+
}
SURNAME_ALIASES = {}  # none observed; placeholder for OCR/spelling variants

# Mayoral terms (inclusive of the start year-month). A person listed in a vote
# block during their mayoral term is presiding, not a routine voter — only an
# explicit "Mayor <Name>" tie-break counts. Date thresholds verified against the
# minutes (last Beerman meeting 2021-12-16; first Worel-as-Mayor 2022-01-06;
# first Dickey-as-Mayor 2026-01-08).
def mayor_surname_at(date):
    if date < "2022-01-01":
        return "beerman"
    if date < "2026-01-01":
        return "worel"
    return "dickey"


def norm_surname(token):
    t = token.strip().strip(".,;:()").lower()
    return SURNAME_ALIASES.get(t, t)


def canon(token):
    return ROSTER.get(norm_surname(token))


# ---------------------------------------------------------------------------
# Governing body (Council / RDA / HA) — standalone section headers only.
# ---------------------------------------------------------------------------
BODY_HEADER_RE = re.compile(
    r"^\s*(?:[IVXLC]+\)\s*)?PARK CITY (HOUSING AUTHORITY|REDEVELOPMENT AGENCY) MEETING",
    re.IGNORECASE)
BOARD_SIGNAL_RE = re.compile(r"\bBoard\s*Members?\b", re.IGNORECASE)


def board_header_body(line):
    m = BODY_HEADER_RE.match(line)
    if not m:
        return None
    return "HA" if "HOUSING" in m.group(1).upper() else "RDA"


# ---------------------------------------------------------------------------
# Motion-type classification (fixed 12-category taxonomy, shared across cities).
# ---------------------------------------------------------------------------
def classify(text):
    t = " ".join(text.split()).lower()
    landuse_kw = ["zone", "zoning", "rezone", "general plan", "overlay", "subdivision",
                  "plat", "annex", "right-of-way", "right of way", "vacat", "land use",
                  "land management code", "lmc", "setback", "conditional use", "pud",
                  "master plan", "development agreement", "specially planned area",
                  "spa", "plat amendment", "easement"]
    if any(k in t for k in landuse_kw):
        return "Land-Use/Zoning"
    if "budget amendment" in t or "amend the budget" in t or re.search(r"budget.{0,30}amend", t) \
            or "tentative budget" in t or "truth in taxation" in t or "final budget" in t \
            or "budget for fiscal" in t:
        return "Budget Amendment"
    if "interlocal" in t or "inter-local" in t or "mutual aid" in t:
        return "Interlocal"
    if "grant" in t and ("apply" in t or "accept" in t or "award" in t or "funding" in t
                         or "application" in t or "cdbg" in t or "sub-grant" in t):
        return "Grant-Funding"
    if "appoint" in t or "reappoint" in t:
        return "Appointment"
    if any(k in t for k in ["contract", "agreement", "purchase", "bid", "procure",
                            "professional services", "lease", "task order", "execute"]) \
            and "interlocal" not in t and "ordinance" not in t and "resolution" not in t:
        return "Contract/Purchase"
    if "ordinance" in t:
        return "Ordinance"
    if "resolution" in t:
        return "Resolution"
    if re.search(r"\b(proclamation|proclaiming|recognition|recognizing|honoring|"
                 r"commend(?:ing|ation)?|ceremonial|in memoriam|awareness (month|week|day))\b", t):
        return "Ceremonial"
    if any(k in t for k in ["open the public hearing", "close the public hearing",
                            "open public comment", "close public comment",
                            "continue the public hearing"]):
        return "Public Hearing Action"
    proc_kw = ["minutes", "agenda", "continue", "table", "consent", "adjourn", "recess",
               "ratify", "set the date", "schedule", "executive session", "closed session",
               "close the meeting", "reconsider", "calendar", "appointment to"]
    if any(k in t for k in proc_kw):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Name-list parsing.  Handles comma- AND "and"-separated lists, with or without
# the Oxford comma, the "Council Members"/"Board Members" prefix, parenthetical
# annotations like "(remote)"/"(via Zoom)", and trailing qualifiers like
# "Gerber from the July 30 minutes" (only roster surnames are kept). A name token
# immediately preceded by "Mayor" is returned in the mayor-prefixed set (tie-break).
# ---------------------------------------------------------------------------
NAME_TOKEN_RE = re.compile(r"\b(?:Mc|Mac)?[A-Z][a-z]+\b")
STOPWORDS = {"council", "councilmember", "councilmembers", "member", "members", "board",
             "chair", "vice", "mayor", "and", "pro", "tem", "via", "zoom", "remote",
             "present", "absent", "excused", "none", "the", "from", "city"}


def parse_name_list(segment):
    """Return (names, mayor_prefixed) — canonical full names found in `segment`,
    de-duplicated in order; mayor_prefixed is the subset that followed the word
    'Mayor' (an explicit tie-break)."""
    names, mayor_set = [], set()
    seen = set()
    prev_was_mayor = False
    for m in NAME_TOKEN_RE.finditer(segment):
        tok = m.group(0)
        low = tok.lower()
        if low == "mayor":
            prev_was_mayor = True
            continue
        if low in STOPWORDS:
            # keep tracking 'mayor' across "Mayor Pro Tem <Name>" etc.
            if low not in ("pro", "tem"):
                prev_was_mayor = prev_was_mayor and low in ("pro", "tem")
            continue
        full = canon(tok)
        if full:
            if full not in seen:
                seen.add(full)
                names.append(full)
            if prev_was_mayor:
                mayor_set.add(full)
        prev_was_mayor = False
    return names, mayor_set


# ---------------------------------------------------------------------------
# Vote (result) block parsing.
# ---------------------------------------------------------------------------
# CASE-SENSITIVE (2026-07-02): CivicClerk result blocks are always UPPERCASE
# (all 1,524 in the corpus). Case-insensitive matching created 2 spurious
# motions from wrapped lowercase prose: a public comment continuing
# "...cost savings as a\nresult: https://www.orlando.gov/..." (2020-06-25) and
# a sentence wrapping onto a bare "excused." line (2023-03-02).
RESULT_RE = re.compile(r"^\s*RESULT\s*:\s*(.*)$")
# A label line: AYE(S)/NAY(S)/ABSTAIN(ED)/EXCUSED/ABSENT/RECUSE(D), optionally
# prefixed by line-number noise from the source ("29   AYES: ...").
LABEL_RE = re.compile(
    r"^\s*\d*\s*(AYES?|NAYS?|ABSTAINED|ABSTAIN|EXCUSED|ABSENT|RECUSED|RECUSE)\s*[:.]?\s*(.*)$")
LABEL_BUCKET = {
    "AYE": "aye", "AYES": "aye",
    "NAY": "nay", "NAYS": "nay",
    "ABSTAIN": "abstain", "ABSTAINED": "abstain",
    "EXCUSED": "absent", "ABSENT": "absent",
    "RECUSE": "recuse", "RECUSED": "recuse",
}
# Page-footer lines interleaved by the PDF->md conversion; skip when scanning a
# result block so a wrapped member list isn't cut by a footer.
FOOTER_RE = re.compile(
    r"^\s*(PARK CITY( COUNCIL MEETING| MEETING)?|SUMMIT COUNTY|Page\s*\|?\s*\d+|"
    r"P\s*a\s*g\s*e|Park City\s+Page|\d{1,2}/\d{1,2}/\d{2,4}|"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d)",
    re.IGNORECASE)
MOVED_RE = re.compile(
    r"(Council\s*Member|Board\s*Member|Mayor\s*Pro\s*Tem|Mayor|Chair)\s+"
    r"((?:Mc|Mac)?[A-Z][a-z]+)\s+(?:made\s+a\s+motion|moved|motioned)", re.IGNORECASE)
SECOND_RE = re.compile(
    r"(?:seconded\s+by\s+)?(?:Council\s*Member|Board\s*Member|Mayor\s*Pro\s*Tem|Mayor|Chair)\s+"
    r"((?:Mc|Mac)?[A-Z][a-z]+)\s+seconded", re.IGNORECASE)
SECOND_BY_RE = re.compile(
    r"seconded\s+by\s+(?:Council\s*Member|Board\s*Member|Mayor\s*Pro\s*Tem|Mayor|Chair)?\s*"
    r"((?:Mc|Mac)?[A-Z][a-z]+)", re.IGNORECASE)


def outcome_label(result_word):
    w = (result_word or "").strip().upper()
    if not w:
        return "Pass"
    if w.startswith("APPROVED") or w.startswith("ADOPTED") or w.startswith("PASSED") \
            or w.startswith("GRANTED") or w.startswith("AUTHORIZED"):
        return "Pass"
    if "FAIL" in w or w.startswith("DENIED") or "DEFEAT" in w or w.startswith("REJECT") \
            or "DID NOT PASS" in w:
        return "Fail"
    if w.startswith("CONTINUED"):
        return "Continued"
    if w.startswith("POSTPONED"):
        return "Postponed"
    if w.startswith("TABLED"):
        return "Tabled"
    if w.startswith("WITHDRAWN"):
        return "Withdrawn"
    # default: title-case the leading word(s)
    return w.title()


def parse_meeting(text, date):
    lines = text.split("\n")
    n = len(lines)
    mayor_sn = mayor_surname_at(date)

    votes = []
    motion_no = 0
    last_board = None          # 'RDA' / 'HA' most-recent board header
    preamble_start = 0         # index where the current motion preamble begins
    i = 0
    while i < n:
        line = lines[i]

        # body section header?
        bh = board_header_body(line)
        if bh:
            last_board = bh
            preamble_start = i + 1
            i += 1
            continue

        rm = RESULT_RE.match(line)
        lm = LABEL_RE.match(line)
        # A result block starts at a RESULT: line, or at a label line not preceded
        # by a RESULT: line (a handful of blocks omit the RESULT: header).
        if rm or lm:
            result_word = rm.group(1).strip() if rm else ""
            buckets = {"aye": [], "nay": [], "absent": [], "abstain": [], "recuse": []}
            mayor_tb = {}  # full_name -> bucket, for explicit "Mayor <Name>" tie-breaks
            cur_bucket = None
            j = i + 1 if rm else i
            blanks = 0
            while j < n:
                nl = lines[j]
                if FOOTER_RE.match(nl):
                    j += 1
                    continue
                lj = LABEL_RE.match(nl)
                if lj:
                    cur_bucket = LABEL_BUCKET[lj.group(1).upper()]
                    names, mset = parse_name_list(lj.group(2))
                    buckets[cur_bucket] += names
                    for nm in mset:
                        mayor_tb[nm] = cur_bucket
                    j += 1
                    blanks = 0
                    continue
                if RESULT_RE.match(nl) or board_header_body(nl) or MOVED_RE.search(nl):
                    break
                if nl.strip() == "":
                    blanks += 1
                    if blanks >= 1 and cur_bucket is None:
                        # blank right after a bare RESULT: line and no labels yet ->
                        # peek one more line for a label, else stop.
                        k = j + 1
                        while k < n and (lines[k].strip() == "" or FOOTER_RE.match(lines[k])):
                            k += 1
                        if k < n and LABEL_RE.match(lines[k]):
                            j = k
                            continue
                        break
                    if blanks >= 1 and cur_bucket is not None:
                        break
                    j += 1
                    continue
                # a continuation line (wrapped member list) for the current label
                if cur_bucket is not None and not nl.strip()[:1].isdigit():
                    # only treat as continuation if it carries roster names
                    names, mset = parse_name_list(nl)
                    if names:
                        buckets[cur_bucket] += names
                        for nm in mset:
                            mayor_tb[nm] = cur_bucket
                        j += 1
                        continue
                break
            block_end = j

            # de-dup each bucket preserving order
            def dedup(lst):
                s, o = set(), []
                for x in lst:
                    if x not in s:
                        s.add(x)
                        o.append(x)
                return o
            for b in buckets:
                buckets[b] = dedup(buckets[b])

            # ---- mayor handling: pull explicit tie-break names out into a flag,
            # and drop any routine (un-flagged) mayor leak (defensive; asserted in
            # validate_votes.py). A mayor name is one whose surname == mayor_sn.
            mayor_full = ROSTER.get(mayor_sn)
            tiebreak_rows = []
            leaked = []
            for b in list(buckets.keys()):
                kept = []
                for nm in buckets[b]:
                    if nm == mayor_full:
                        if nm in mayor_tb:
                            tiebreak_rows.append((nm, b))
                        else:
                            leaked.append((nm, b))  # routine leak -> drop, record
                    else:
                        kept.append(nm)
                buckets[b] = kept

            # ---- motion text / mover / seconder from the preamble ----
            preamble = "\n".join(
                l for l in lines[preamble_start:i] if not FOOTER_RE.match(l))
            preamble_flat = " ".join(preamble.split())
            mover = seconder = None
            desc = ""
            mv_iter = list(MOVED_RE.finditer(preamble_flat))
            if mv_iter:
                mv = mv_iter[-1]
                if canon(mv.group(2)):
                    mover = canon(mv.group(2))
                # description = motion text from the mover up to the "seconded"
                # clause (the seconder sentence is metadata, not the motion). Falls
                # back to a sentence split that does NOT break on abbreviations like
                # "Ordinance No." / "Section 15-2.4" / "Resolution 06-2024.".
                tail = preamble_flat[mv.start():]
                sc = re.search(
                    r"\.?\s*(?:Council\s*Member|Board\s*Member|Mayor\s*Pro\s*Tem|Mayor|"
                    r"Chair)\s+\S+\s+seconded", tail, re.IGNORECASE)
                sb = re.search(r",?\s*(?:and\s+)?seconded\s+by\b", tail, re.IGNORECASE)
                end = min([m.start() for m in (sc, sb) if m] or [len(tail)])
                desc = tail[:end].strip().rstrip(".,;: ")
                if not desc:
                    desc = tail.strip()
                # seconder: look in the whole preamble tail
                sm = SECOND_RE.search(preamble_flat) or SECOND_BY_RE.search(preamble_flat)
                if sm and canon(sm.group(1)):
                    seconder = canon(sm.group(1))
            if not desc:
                desc = preamble_flat[-400:].strip()

            # ---- body for this motion ----
            block_text = "\n".join(lines[i:block_end])
            is_board = bool(BOARD_SIGNAL_RE.search(block_text)
                            or re.search(r"\b(?:RDA|HA)\b", block_text))
            if is_board:
                body = last_board or "RDA"
            else:
                body = "Council"

            names_recorded = bool(buckets["aye"] or buckets["nay"]
                                  or buckets["abstain"] or buckets["recuse"])
            n_aye = len(buckets["aye"]) + sum(1 for _, b in tiebreak_rows if b == "aye")
            n_nay = len(buckets["nay"]) + sum(1 for _, b in tiebreak_rows if b == "nay")
            olabel = outcome_label(result_word)
            if names_recorded:
                result = f"{n_aye}-{n_nay} {olabel}"
            else:
                result = (result_word.title() if result_word else olabel)

            motion_no += 1
            rec = {
                "motion_no": motion_no,
                "motion": desc[:600],
                "body": body,
                "motion_type": classify(desc + " " + result_word),
                "result": result,
                "result_text": result_word,
                "mover": mover,
                "seconder": seconder,
                "aye": buckets["aye"],
                "nay": buckets["nay"],
                "abstain": buckets["abstain"],
                "absent": buckets["absent"],
                "recuse": buckets["recuse"],
                "names_recorded": names_recorded,
            }
            if tiebreak_rows:
                rec["mayor_tiebreak"] = [
                    {"member": nm, "vote": b} for nm, b in tiebreak_rows]
            if leaked:
                rec["_mayor_leak"] = [{"member": nm, "vote": b} for nm, b in leaked]
            votes.append(rec)

            preamble_start = block_end
            i = block_end
            continue

        i += 1

    return votes


# ---------------------------------------------------------------------------
# Driver.
# ---------------------------------------------------------------------------
def load_index():
    with open(MINUTES_INDEX, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def json_path_for(row):
    rel = row["path"]                     # minutes/<year>/<week>/<file>.md
    rel = rel.replace("minutes/", "", 1)
    rel = rel[:-3] + ".json" if rel.endswith(".md") else rel + ".json"
    return os.path.join(VOTES_DIR, rel)


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
        date, title, source = mtg["date"], mtg["title"], mtg["source"]
        year = date[:4]
        for v in mtg["votes"]:
            base = {
                "date": date, "year": year, "title": title,
                "body": v.get("body", "Council"),
                "motion_no": v["motion_no"], "motion": v["motion"],
                "motion_type": v["motion_type"], "result": v["result"],
                "mover": v.get("mover") or "", "seconder": v.get("seconder") or "",
                "source": source,
            }
            emitted = False
            # explicit mayor tie-break rows first (flagged in the vote value)
            for tb in v.get("mayor_tiebreak", []):
                r = dict(base)
                r["member"] = tb["member"]
                r["vote"] = {"aye": "Aye", "nay": "Nay", "abstain": "Abstain",
                             "absent": "Absent", "recuse": "Recuse"}[tb["vote"]] \
                    + " (Mayor tie-break)"
                rows_out.append(r)
                emitted = True
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
        w = csv.writer(f)          # csv.writer for comma-safe quoting
        w.writerow(cols)
        for r in rows_out:
            w.writerow([r.get(c, "") for c in cols])
    return len(rows_out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="re-extract even if JSON exists")
    args = ap.parse_args()

    rows = load_index()
    unparsed = []
    for row in rows:
        md_path = os.path.join(MM, row["path"])
        if not os.path.exists(md_path):
            unparsed.append(row["path"] + " (missing file)")
            continue
        out_json = json_path_for(row)
        os.makedirs(os.path.dirname(out_json), exist_ok=True)
        if os.path.exists(out_json) and not args.force:
            continue
        with open(md_path, encoding="utf-8") as f:
            text = f.read()
        try:
            votes = parse_meeting(text, row["date"])
        except Exception as e:  # noqa
            unparsed.append(f"{row['path']} (parse error: {e})")
            continue
        meeting_obj = {
            "date": row["date"],
            "title": row["title"],
            "body_slug": row.get("slug", "city-council-meeting"),
            "source": row["path"],
            "format": row.get("format", "text"),
            "votes": votes,
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(meeting_obj, f, indent=1, ensure_ascii=False)

    n_rows = rebuild_csv()

    # quick aggregate for stdout
    meetings = motions = contested = tally_only = 0
    body_ct = {"Council": 0, "RDA": 0, "HA": 0}
    for jp in iter_jsons():
        with open(jp, encoding="utf-8") as f:
            mtg = json.load(f)
        meetings += 1
        for v in mtg["votes"]:
            motions += 1
            body_ct[v.get("body", "Council")] = body_ct.get(v.get("body", "Council"), 0) + 1
            if not v["names_recorded"]:
                tally_only += 1
            if v["nay"] or v["abstain"] or v["recuse"] or v.get("mayor_tiebreak"):
                contested += 1
    print(json.dumps({
        "meetings_processed": meetings,
        "motions_extracted": motions,
        "member_vote_rows": n_rows,
        "body": body_ct,
        "tally_only_motions": tally_only,
        "contested_motions": contested,
        "unparsed_meetings": unparsed,
    }, indent=2))


if __name__ == "__main__":
    main()
