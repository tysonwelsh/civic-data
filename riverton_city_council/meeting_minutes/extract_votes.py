#!/usr/bin/env python3
"""
Riverton City Council vote extractor  (PURE deterministic — no LLM, no network).

Reads the council-meeting markdown under meeting_minutes/minutes/<year>/<week>/, parses
every recorded motion, and emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<slug>.json   (resumable)
  - meeting_minutes/all_votes.csv   (13-col long format, one row per member-vote)

Riverton's roll-call grammar (verified on the 2024-04-02 and 2025-12-16 PMN minutes):
  * NAMED per-member roll call:
      "Councilmember McDougal MOVED that the City Council approve Resolution No. 24-40 ...
       Councilmember Pierucci SECONDED the motion. Mayor Pro Tempore Buroker called for a
       roll-call vote. The vote was as follows: Buroker-yes, Haymond-yes, McCay-yes,
       McDougal-yes, and Pierucci-yes. The motion passed unanimously."
    -> yes->Aye, no->Nay (case varies Yes/yes/No/no; the hyphen may wrap a line as
       "McCay-\nyes", flattened before parsing).
  * TALLY-ONLY (no names), typically adjournments:
      "All voted in favor and the motion passed unanimously."
    -> names_recorded:false, one placeholder row.
  * MAYOR TIE-BREAK (six-member council form; Park City model). The Mayor is NON-voting on
    ordinary motions (max council tally = 5) and votes ONLY to break a tie:
      "The vote was as follows: Buroker-no, McCay-no, McDougal-yes, and Pierucci-yes. The
       motion ended in a tie, 2 to 2. Mayor Staggs was called to vote to break the tie and
       voted yes. The motion passed."
    -> the Mayor's surname is read from the tie-break sentence, captured as a vote row with
       value "Aye (Mayor tie-break)" / "Nay (Mayor tie-break)" and flagged mayor_tiebreak.
       The Mayor is NEVER counted in the ordinary 5-member roll.

MAYOR / roster drift (recon.md):
  * Mayor Trent Staggs presided 2020->Dec 2025; Tish Buroker was Councilmember (D3) through
    2025 (often Mayor Pro Tempore) then won the mayoralty (Jan 2026). She therefore votes as
    a councilmember 2020-2025 and, from 2026, appears only as a tie-break Mayor.
  * 2020-2025 voting bench = Buroker, Haymond, McCay, McDougal, Pierucci (under Mayor Staggs).
  * Jan 2026 seating: McCay(D4)->Smith, Buroker's D3->Johnson; Buroker->Mayor.
Only the roster surnames below map to a vote; any other name is dropped (never guessed) and
surfaced by validate_votes.py.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER_CSV = ROOT / "roster.csv"

# ---------------------------------------------------------------------------
# Roster / name normalization
# ---------------------------------------------------------------------------
ROSTER_MAP = {
    "buroker": "Tish Buroker",       # councilmember (D3) 2020-2025, Mayor 2026+
    "haymond": "Spencer Haymond",    # D5 2024+
    "mccay": "Tawnee McCay",         # D4 through 2025
    "mcdougal": "Troy McDougal",     # D2
    "pierucci": "Andy Pierucci",     # D1 2023+
    "johnson": "Alexander Johnson",  # D3 2026+
    "smith": "Shannon Smith",        # D4 2026+
    "stewart": "Sheldon Stewart",    # D1 2020-2022 (often Mayor Pro Tem); -> Pierucci 2023
    "wells": "Claude Wells",         # D5 2020-2023; -> Haymond 2024
}
MAYOR_MAP = {                        # mayors (non-voting except tie-break)
    "staggs": "Trent Staggs",        # Mayor 2020-2025
    "buroker": "Tish Buroker",       # Mayor 2026+ (also a councilmember 2020-2025)
}
COUNCIL_SIZE = 5

VOTE_MAP = {
    "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
    "abstain": "abstain", "abstained": "abstain", "abstaining": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}

ROLE = r"(?:Councilmember|Council\s*Member|Mayor\s*Pro\s*Tem(?:pore)?|Mayor)"
# Roster surnames as printed (case-explicit — the re-anchor rules below intentionally do
# NOT use re.I so an uppercase first-name constraint and a case-sensitive "MOVED" caps
# token stay meaningful; the minutes always print the motion verb as caps "MOVED").
SURNAMES = (r"Buroker|Haymond|McCay|McDougal|Pierucci|Johnson|Smith|Stewart|Wells")


# ---------------------------------------------------------------------------
# Motion-type taxonomy (shared 12-category style; land-use checked first)
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning ordinance|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development agreement|"
                 r"overlay|site plan|future land use|redevelopment|project area|"
                 r"planned (?:unit )?development", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend(?:ing)? the (?:fiscal|fy)?\s*.*budget|"
                 r"tentative budget|final budget|adopt.*budget|budget for", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|mayor pro tem|liaison|ratify the (?:results|canvass)|reappoint", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|franchise agreement|agreement with|"
                 r"services agreement|enter into an agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|executive session|"
                 r"approve the (?:consent|agenda|minutes|order)|\btable\b|continue|"
                 r"postpone|amend the agenda|canvass", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
MOVED = re.compile(ROLE + r"\s+([A-Z][A-Za-z.'\-]+)\s+MOVED\b", re.I)
SECONDED = re.compile(ROLE + r"\s+([A-Z][A-Za-z.'\-]+)\s+SECONDED\b", re.I)
ROLLCALL = re.compile(r"the vote was as follows:\s*(.*?)(?=\bmotion\b|$)", re.I | re.S)
NAMEVOTE = re.compile(
    r"([A-Z][A-Za-z'\-]+)\s*[-–—]\s*"
    r"(yes|no|aye|nay|abstain(?:ed|ing)?|absent|excused|recuse[d]?)", re.I)
TIE = re.compile(r"ended in a tie", re.I)
TIEBREAK = re.compile(
    r"Mayor\s+([A-Z][A-Za-z'\-]+).*?(?:break the tie|to break a tie).*?"
    r"voted\s+(yes|no|aye|nay)", re.I | re.S)
# A substitute motion whose name is NOT adjacent to MOVED ("<Name> made a substitute
# motion and MOVED that ...") is invisible to the MOVED anchor, so the substitute's
# roll call gets folded onto the SUPERSEDED original and mis-attributed to the wrong
# mover (2024-08-06 cargo-container case: Buroker's carried substitute was credited to
# McDougal's superseded original). Re-anchor the mover on the substitutor's name — but
# ONLY when the substitute was actually SECONDED (a live motion that could be voted).
# The zero-width lookahead requires a SECONDED to appear before any DIED or the next
# motion's MOVED anchor, so a substitute that "DIED for lack of a Second" (2020-05-19:
# Stewart's died substitute; the roll call there belongs to Buroker's ORIGINAL motion,
# already extracted correctly) is left untouched. Surgical: fires on 2024-08-06 only.
SUBST_MOVED = re.compile(
    r"(" + ROLE + r"\s+[A-Z][A-Za-z.'\-]+)\s+made an?\s+substitute\s+motion\s+and\s+MOVED\b"
    r"(?=(?:(?!\bDIED\b|" + ROLE + r"\s+[A-Z][A-Za-z.'\-]+\s+MOVED\b).)*?\bSECONDED\b)",
    re.I | re.S)
# A superseded ORIGINAL motion that is RE-PRESENTED for a vote after a substitute motion
# fails carries NO "MOVED" anchor ("Councilmember X's original motion was presented before
# the council again."), so its roll call is a SECOND roll call inside the substitute's
# MOVED-window and the first-roll-call-per-window rule drops it entirely (2021-04-06 Res
# 21-26: Stewart's substitute Failed 2-3 is captured; McDougal's re-presented original
# Passed 4-1 is lost). This re-anchors the re-presentation as its own motion, reusing the
# superseded original's parsed mover/seconder/text (stashed per meeting) and this segment's
# own roll call + outcome. The literal "presented before the council again" grammar is
# UNIQUE in the corpus (verified across every council file), so this fires ONLY on
# 2021-04-06 — a surgical recovery, not a general window-split.
REPRESENT = re.compile(
    ROLE + r"\s+([A-Z][A-Za-z.'\-]+)['‘’]s\s+original motion was presented "
    r"before the council again", re.I)
# --- Three narrow re-anchor rules (sibling to SUBST_MOVED / REPRESENT) -------------
# Each recovers a genuinely-missing SECOND motion whose roll call was folded onto the
# prior MOVED-window because the missing motion's own MOVED anchor is invisible to the
# standard adjacent-name MOVED regex. All three are grep-verified to fire on exactly one
# meeting each (corpus-wide), and are deliberately case-explicit (no re.I) so they cannot
# creep onto lowercase "moved" (closed-session "also moved to close") or non-name tokens.
#
# (1) TWO-WORD FIRST NAME. 2020-05-05 Ord 20-12: the clerk wrote the mover's FULL name
#     "Council Member Troy McDougal MOVED" — two capitalized words before MOVED, which the
#     single-token `ROLE (name) MOVED` anchor cannot see, so the Ord 20-12 roll call was
#     absorbed by the consent-agenda window. Strip the first name so the standard anchor
#     fires on the roster surname. Grep-unique: the ONLY "ROLE <First> <Last> MOVED" in the
#     corpus (every other mover is printed surname-only).
#     The `(?!…)` guard stops a section-header "Mayor Pro Tem" from being read as the ROLE
#     with the following "Councilmember" as the first name (the Jan Mayor-Pro-Tem-election
#     headers), so the first-name slot must be a real given name, never a role word.
FULLNAME_MOVED = re.compile(
    r"(" + ROLE + r"\s+)(?!(?:Councilmember|Council|Member|Mayor|Pro|Tem)\b)"
    r"[A-Z][A-Za-z.'\-]+\s+(" + SURNAMES + r")\s+MOVED\b")
# (2) NON-ADJACENT "and MOVED". 2021-06-01 Ord 21-14 ("Councilmember Buroker supported
#     this proposal and MOVED …") and 2024-06-04 Pierucci fee motion ("Councilmember
#     Pierucci asked to bring back the original motion made by Councilmember McCay and
#     MOVED …"): the mover's name is separated from MOVED by an intervening clause, so the
#     anchor is invisible and the roll call folds onto the previous window. Re-anchor the
#     mover on the FIRST roster surname of the sentence (the sentence subject). The
#     `(?<![Mm]otion)` lookbehind EXCLUDES the four sibling "… motion and MOVED" cases that
#     are NOT in scope and are handled elsewhere or left untouched: the substitute-motion
#     re-anchors 2024-08-06 (already rewritten by SUBST_MOVED above), 2025-05-06 ("offered
#     a substitute motion and MOVED") and 2020-05-19 ("made a Substitute Motion and MOVED",
#     a died substitute whose roll belongs to the original), plus 2023-12-06 ("amended his
#     motion and MOVED"). In all four the word immediately before "and MOVED" is
#     "motion"/"Motion"; in the two targets it is "proposal"/"McCay". `[^.]*?` keeps the
#     match inside one sentence.
ANDMOVED = re.compile(
    r"(" + ROLE + r"\s+(?:" + SURNAMES + r")\b)"
    r"[^.]*?(?<![Mm]otion)\s+and\s+MOVED\b")
# (3) NOMINATION grammar (no MOVED verb). 2023-01-17 Election of Mayor Pro Tem:
#     "Councilmember Wells nominated Councilmember McDougal to be the Mayor Pro Tempore.
#      Councilmember McCay seconded this nomination." A nomination IS a motion, but carries
#     no "MOVED", so its roll call was folded onto the work-session-adjournment window.
#     Handled by a dedicated emitter (below) rather than a re-anchor so the motion text
#     keeps the "Mayor Pro Tempore" appointment phrasing (which the generic text-splitter
#     would truncate). Grep-unique: the only "nominated"/"seconded this nomination" pair in
#     the corpus. group(1)=nominator surname, group(2)=verbatim nomination clause.
NOMINATE = re.compile(
    r"(?:" + ROLE + r")\s+(" + SURNAMES + r")\s+"
    r"(nominated\s+(?:" + ROLE + r")\s+(?:" + SURNAMES + r")\s+to be"
    r"(?:\s+the)?\s+Mayor\s*Pro\s*Tem(?:pore)?)")
NOMINATE_SEC = re.compile(
    r"(?:" + ROLE + r")\s+(" + SURNAMES + r")\s+seconded this nomination")
ALLINFAVOR = re.compile(r"all voted in favor", re.I)
# matched in the sentence that FOLLOWS the roll call (searched from rc.end()), so the
# leading "The " is already consumed into the roll-call capture — anchor on "motion".
OUTCOME = re.compile(
    r"motion\s+(passed unanimously|passed|failed|carried|died|was denied|was approved|"
    r"did not (?:pass|carry)|does not (?:pass|carry))", re.I)
DEATH = re.compile(r"lack of (?:a )?second|no second|died for lack", re.I)


def _flatten(s):
    return re.sub(r"\s+", " ", s).strip()


def find_roster(surname):
    return ROSTER_MAP.get(surname.lower())


# ---------------------------------------------------------------------------
# Parse one meeting
# ---------------------------------------------------------------------------
def strip_header(text):
    m = re.match(r"^#[^\n]*\n(?:>[^\n]*\n)*\n", text)
    return text[m.end():] if m else text


def parse_meeting(text):
    body = strip_header(text)
    # re-anchor a seconded substitute's mover onto its own name (see SUBST_MOVED)
    body = SUBST_MOVED.sub(r"\1 MOVED", body)
    # re-anchor a full-name ("Troy McDougal") mover onto its roster surname (FULLNAME_MOVED)
    body = FULLNAME_MOVED.sub(r"\1\2 MOVED", body)
    # re-anchor a non-adjacent "… and MOVED" mover onto the sentence subject (ANDMOVED).
    # Runs AFTER SUBST_MOVED so a rewritten substitute ("… substitute motion MOVED") no
    # longer carries "and MOVED" and cannot double-fire here.
    body = ANDMOVED.sub(r"\1 MOVED", body)
    # locate every MOVED as a motion anchor; motion window = from MOVED to the next MOVED
    anchors = [m.start() for m in MOVED.finditer(body)]
    anchors.append(len(body))
    votes = []
    pending_original = {}   # mover surname (lower) -> parsed motion awaiting a vote
    for i in range(len(anchors) - 1):
        seg = body[anchors[i]:anchors[i + 1]]
        flat = _flatten(seg)
        mv = MOVED.search(flat)
        mover = find_roster(mv.group(1)) if mv else None
        sec = SECONDED.search(flat)
        seconder = find_roster(sec.group(1)) if sec else None

        # motion text: after "MOVED" up to the seconder / roll-call / outcome
        mt = flat[mv.end():] if mv else flat
        mt = re.split(r"\bSECONDED\b|the vote was as follows|Mayor Pro Tempore|"
                      r"Mayor\s+\w+\s+called|All voted in favor", mt, 1, flags=re.I)[0]
        motion_text = mt.strip(" .;,:")
        # drop a leading "the motion" fragment; keep verbs like approve/deny/table
        motion_text = re.sub(r"^(that the City Council|to)\s+", "", motion_text, flags=re.I).strip()

        # stash this window's parsed motion so a later re-presentation of an ORIGINAL
        # motion (which carries no MOVED anchor) can reuse the mover/seconder/text.
        if mv:
            pending_original[mv.group(1).lower()] = {
                "motion": motion_text[:600],
                "motion_type": classify_motion(motion_text),
                "mover": mover, "seconder": seconder}

        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        names_recorded = False
        mayor_tiebreak = []

        rc = ROLLCALL.search(flat)
        if rc:
            seen = set()
            for nm in NAMEVOTE.finditer(rc.group(1) + " "):
                canon = find_roster(nm.group(1))
                if not canon or canon in seen:
                    continue
                seen.add(canon)
                buckets[VOTE_MAP.get(nm.group(2).lower(), "aye")].append(canon)
            if buckets["aye"] or buckets["nay"] or buckets["abstain"] or buckets["recuse"]:
                names_recorded = True

        # tie-break by the Mayor
        if TIE.search(flat):
            tb = TIEBREAK.search(flat)
            if tb:
                mname = MAYOR_MAP.get(tb.group(1).lower(), f"Mayor {tb.group(1).title()}")
                mbucket = VOTE_MAP.get(tb.group(2).lower(), "aye")
                mayor_tiebreak.append({"member": mname, "vote": mbucket})

        # result (native phrasing, faithful). Pair the outcome with the sentence that
        # FOLLOWS this roll call (search from rc.end()), so a second in-window roll call's
        # outcome can't bleed onto the first (2021-04-06 substitute-then-original case).
        om = OUTCOME.search(flat, rc.end() if rc else 0)
        if om:
            phrase = om.group(1).lower()
            if "did not" in phrase or "does not" in phrase:
                result = "Failed"
            elif "denied" in phrase:
                result = "Denied"
            elif "unanim" in phrase:
                result = "Passed unanimously"
            elif "pass" in phrase or "carr" in phrase or "approved" in phrase:
                result = "Passed"
            elif "died" in phrase:
                result = "Died"
            else:
                result = "Failed"
        elif DEATH.search(flat):
            result = "Died (no second)"
        else:
            result = ""
        if TIE.search(flat) and mayor_tiebreak:
            result = "Passed (Mayor tie-break)" if mayor_tiebreak[0]["vote"] == "aye" \
                else "Failed (Mayor tie-break)"

        # skip pure noise: a MOVED with neither a roll call, all-in-favor, nor an outcome
        if not (names_recorded or mayor_tiebreak or ALLINFAVOR.search(flat) or result):
            continue

        votes.append({
            "body": "Council",
            "motion": motion_text[:600],
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"],
            "abstain": buckets["abstain"], "absent": buckets["absent"],
            "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "mayor_tiebreak": mayor_tiebreak,
        })

        # A superseded ORIGINAL motion re-presented for a vote inside this same window
        # (no MOVED anchor of its own). Emit it as its OWN motion, reusing the stashed
        # original's mover/seconder/text and this re-presentation's roll call + outcome.
        rep = REPRESENT.search(flat)
        orig = pending_original.get(rep.group(1).lower()) if rep else None
        if rep and orig:
            seg_b = flat[rep.start():]
            b2 = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
            names2 = False
            rc2 = ROLLCALL.search(seg_b)
            if rc2:
                seen2 = set()
                for nm in NAMEVOTE.finditer(rc2.group(1) + " "):
                    canon = find_roster(nm.group(1))
                    if not canon or canon in seen2:
                        continue
                    seen2.add(canon)
                    b2[VOTE_MAP.get(nm.group(2).lower(), "aye")].append(canon)
                if b2["aye"] or b2["nay"] or b2["abstain"] or b2["recuse"]:
                    names2 = True
            om2 = OUTCOME.search(seg_b, rc2.end() if rc2 else 0)
            if om2:
                p2 = om2.group(1).lower()
                if "did not" in p2 or "does not" in p2:
                    result2 = "Failed"
                elif "denied" in p2:
                    result2 = "Denied"
                elif "unanim" in p2:
                    result2 = "Passed unanimously"
                elif "pass" in p2 or "carr" in p2 or "approved" in p2:
                    result2 = "Passed"
                elif "died" in p2:
                    result2 = "Died"
                else:
                    result2 = "Failed"
            else:
                result2 = ""
            if names2 or result2:
                votes.append({
                    "body": "Council",
                    "motion": orig["motion"],
                    "motion_type": orig["motion_type"],
                    "result": result2,
                    "mover": orig["mover"],
                    "seconder": orig["seconder"],
                    "aye": b2["aye"], "nay": b2["nay"],
                    "abstain": b2["abstain"], "absent": b2["absent"],
                    "recuse": b2["recuse"],
                    "names_recorded": names2,
                    "mayor_tiebreak": [],
                })

        # A NOMINATION motion (no MOVED verb) that lives inside this window, after the
        # window's own roll call (2023-01-17 Mayor Pro Tem election). Emit it as its own
        # motion, reading the nominator (mover), "seconded this nomination" (seconder), and
        # the nomination's OWN roll call + outcome (searched from the nomination onward, so
        # the window's earlier roll call is never reused).
        nom = NOMINATE.search(flat)
        if nom:
            seg_n = flat[nom.start():]
            nmover = find_roster(nom.group(1))
            nsec = NOMINATE_SEC.search(seg_n)
            nseconder = find_roster(nsec.group(1)) if nsec else None
            nom_text = nom.group(2).strip(" .;,:")
            bn = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
            namesn = False
            rcn = ROLLCALL.search(seg_n)
            if rcn:
                seenn = set()
                for nm in NAMEVOTE.finditer(rcn.group(1) + " "):
                    canon = find_roster(nm.group(1))
                    if not canon or canon in seenn:
                        continue
                    seenn.add(canon)
                    bn[VOTE_MAP.get(nm.group(2).lower(), "aye")].append(canon)
                if bn["aye"] or bn["nay"] or bn["abstain"] or bn["recuse"]:
                    namesn = True
            omn = OUTCOME.search(seg_n, rcn.end() if rcn else 0)
            if omn:
                pn = omn.group(1).lower()
                if "did not" in pn or "does not" in pn:
                    resultn = "Failed"
                elif "denied" in pn:
                    resultn = "Denied"
                elif "unanim" in pn:
                    resultn = "Passed unanimously"
                elif "pass" in pn or "carr" in pn or "approved" in pn:
                    resultn = "Passed"
                elif "died" in pn:
                    resultn = "Died"
                else:
                    resultn = "Failed"
            else:
                resultn = ""
            if namesn or resultn:
                votes.append({
                    "body": "Council",
                    "motion": nom_text[:600],
                    "motion_type": classify_motion(nom_text),
                    "result": resultn,
                    "mover": nmover,
                    "seconder": nseconder,
                    "aye": bn["aye"], "nay": bn["nay"],
                    "abstain": bn["abstain"], "absent": bn["absent"],
                    "recuse": bn["recuse"],
                    "names_recorded": namesn,
                    "mayor_tiebreak": [],
                })
    return votes


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    force = "--force" in sys.argv
    if not INDEX.exists():
        print(f"no index at {INDEX} — run fetch_new.py --backfill first", file=sys.stderr)
        build_all_votes()
        return
    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    for r in rows:
        rel = r["path"]
        path = ROOT / rel
        if not path.exists():
            print(f"MISSING: {rel}", file=sys.stderr)
            continue
        week = Path(rel).parent.name
        year = r["year"]
        slug = Path(rel).stem
        out_dir = VOTES_DIR / year / week
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(path.read_text(encoding="utf-8", errors="replace"))
        for k, v in enumerate(votes, 1):
            v["motion_no"] = k
        out_json.write_text(json.dumps(
            {"date": r["date"], "year": int(year), "title": r["title"],
             "source": rel, "votes": votes}, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON  (skipped {skipped} existing)")
    build_all_votes()


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n_rows = 0
    roster = {}   # OBSERVED member -> {first_seen, last_seen, vote_rows, tiebreaks}

    def touch(member, date, tiebreak=False):
        r = roster.setdefault(member, {"first": date, "last": date,
                                       "votes": 0, "tiebreaks": 0})
        r["first"] = min(r["first"], date)
        r["last"] = max(r["last"], date)
        r["votes"] += 1
        if tiebreak:
            r["tiebreaks"] += 1

    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            if jp.name.startswith("_"):
                continue
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                   ("absent", "Absent"), ("recuse", "Recuse")):
                    for member in v.get(key, []):
                        w.writerow(base + [member, label, data["source"]])
                        touch(member, data["date"])
                        n_rows += 1
                        emitted = True
                for tb in v.get("mayor_tiebreak", []):
                    label = "Aye (Mayor tie-break)" if tb["vote"] == "aye" \
                        else "Nay (Mayor tie-break)"
                    w.writerow(base + [tb["member"], label, data["source"]])
                    touch(tb["member"], data["date"], tiebreak=True)
                    n_rows += 1
                    emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    with ROSTER_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["member", "role", "first_seen", "last_seen", "vote_rows", "mayor_tiebreaks"])
        for name in sorted(roster, key=lambda n: (-roster[n]["votes"], n)):
            r = roster[name]
            role = "Mayor (tie-break)" if name in MAYOR_MAP.values() and r["tiebreaks"] \
                and r["votes"] == r["tiebreaks"] else "Councilmember"
            w.writerow([name, role, r["first"], r["last"], r["votes"], r["tiebreaks"]])
    print(f"Wrote {ROSTER_CSV} with {len(roster)} observed members")
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")
    return n_rows


if __name__ == "__main__":
    main()
