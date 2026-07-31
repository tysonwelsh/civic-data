#!/usr/bin/env python3
"""
South Jordan City Council vote extractor  (PURE deterministic — no LLM, no network).

Reads the council-meeting markdown under meeting_minutes/minutes/<year>/<week>/, parses
every recorded motion, tags the governing `body` (Council default; RDA for Redevelopment
Agency action items), normalizes member names, and emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<slug>.json   (resumable)
  - meeting_minutes/all_votes.csv   (13-col long format, one row per member-vote, w/ body)

South Jordan's narrative-tally vote grammar (parsed to THIS):
  * UNANIMOUS (tally only, NO names -> names_recorded:false):
      "Council Member X motioned to approve <Resolution/Ordinance ...>. Council Member Y
       seconded the motion. The motion passed with a vote of 5-0."
      "...seconded the motion; vote was 5-0 unanimous in favor."
      "...seconded the motion; vote was unanimous in favor."   (no number)
  * CONTESTED — dissent IS named, two forms both handled:
      1. Narrative: "...vote of 4-1; Council Member Harris voted 'No'." /
         "3-2. Council Member Johnson and Council Member McGuire voted No." /
         "Roll Call vote was 2-3, motion failed; Council Members Zander, McGuire and
          Harris with the no votes." / "...voted in opposition. By a vote of 3-2..."
      2. Tabular one-member-per-line: "Council Member <Name> - Yes|No" (hyphen/en-dash),
         under a "Roll Call Vote" header, then "The motion passed/denied with a vote of X-Y."
  * Absentees named separately: "Council Member Zander was absent from the vote." /
    "...with Council Member Marlor and Council Member Zander absent."
  * Died: "...failed due to lack of second." / "There was no second, motion failed."
  * Page-break footers (South Jordan City / <meeting> / <date> / <pagenum>) that interrupt
    roll-call blocks are flattened out before parsing.

MAYOR: Mayor Dawn R. Ramsey PRESIDES but is NOT a routine voter (max ordinary tally 5-0,
five district members). She is EXCLUDED from the voting roster, BUT when the source itself
records her casting a vote (tabular "Mayor Dawn R. Ramsey - Yes", or a narrative mayor
vote) the vote is captured FAITHFULLY and the motion is flagged `mayor_voted:true` (a real
event, surfaced by validate_votes.py). "Mayor Pro Tem[pore] <Surname>" is a COUNCIL member
acting as chair -> mapped to that councilmember, never to the Mayor.

Roster (canon; rows for any other name are dropped): D1 Patrick Harris, D2 Brad Marlor
(2020->2023) then Kathie Johnson (2023+), D3 Don Shelton, D4 Tamara Zander, D5 Jason
McGuire. Only these surnames map to a vote; county/other-city officials named in the
narrative ("County Council Member Suzanne Harrison", "Ross Romero", "Alvord", ...) never do.
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

# ---------------------------------------------------------------------------
# Roster / name normalization
# ---------------------------------------------------------------------------
ROSTER_MAP = {
    "harris": "Patrick Harris",
    "johnson": "Kathie Johnson",
    "shelton": "Don Shelton",
    "zander": "Tamara Zander",
    "zanders": "Tamara Zander",   # source typo variant
    "mcguire": "Jason McGuire",
    "marlor": "Brad Marlor",
}
MAYOR_NAME = "Dawn R. Ramsey"
MAYOR_TOKENS = {"ramsey"}

# role prefixes the minutes use for a councilmember (incl. board/pro-tem capacities)
ROLE_PREFIX = r"(?:Council\s*Members?|Board\s*Members?|Board\s*Chair|Mayor\s*Pro\s*Tem(?:pore)?)"


def find_member(phrase):
    """Scan a name phrase for a roster surname. Return (canonical_name, is_mayor).

    Council surnames win over the mayor token so "Mayor Pro Tempore Shelton" -> Shelton.
    Returns (None, False) when no recognizable member is present (never guesses)."""
    toks = re.findall(r"[A-Za-z']+", phrase.lower())
    for t in toks:
        if t in ROSTER_MAP:
            return ROSTER_MAP[t], False
    for t in toks:
        if t in MAYOR_TOKENS:
            return MAYOR_NAME, True
    return None, False


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories) — land-use checked FIRST (most are
# technically ordinances/resolutions but their signal is land-use).
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning ordinance|zone change|\bzone\b|annex|subdivision|"
                 r"\bplat\b|conditional use|land use|general plan|master plan|"
                 r"development agreement|floating zone|overlay|site plan|"
                 r"future land use|community reinvestment|redevelopment|"
                 r"project area|planned development", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend(?:ing)? the (?:fiscal|fy)?\s*.*budget|"
                 r"tentative budget|final budget|adopt.*budget|budget for", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|mayor pro tem|liaison|ratify the (?:results|canvass)|"
                 r"reappoint", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|franchise agreement|agreement with|"
                 r"interlocal|services agreement|enter into an agreement", t):
        return "Contract/Purchase"
    if re.search(r"zoning ordinance|\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed session|executive session|"
                 r"approve the (?:consent|agenda|minutes|order)|approve the .*minutes|"
                 r"\btable\b|continue|postpone|amend the agenda|move to|canvass", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
MOTION_INTRO = re.compile(
    ROLE_PREFIX + r"[.,]?\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2}?)\s+"
    r"(?:motioned|moved|made\s+a\s+motion)\b", re.I)
SECONDER = re.compile(
    ROLE_PREFIX + r"[.,]?\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){0,2}?)\s+"
    r"seconded\b", re.I)

# per-line tabular vote:  "Council Member <Name> - Yes"  /  "Mayor Dawn R. Ramsey – Yes"
TAB_RE = re.compile(
    r"^\s*(Council\s*Members?|Board\s*Members?|Board\s*Chair|Mayor\s*Pro\s*Tem(?:pore)?|Mayor)"
    r"[.,]?\s+(.+?)\s*[-–—]\s*"
    r"(Yes|No|Aye|Nay|Abstain(?:ed)?|Absent|Excused|Recuse[d]?)\s*\.?\s*$", re.I)

VOTE_MAP = {
    "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
    "abstain": "abstain", "abstained": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}

# name-list clause preceding a "No"/opposition verb  (narrative dissent)
_NAMELIST = (r"((?:" + ROLE_PREFIX + r"\s+[A-Za-z.'\-]+"
             r"(?:\s*(?:,|and)\s*(?:" + ROLE_PREFIX + r"\s+)?[A-Za-z.'\-]+)*))")
NAY_CLAUSE = re.compile(
    _NAMELIST + r"\s*(?:voted\s*[“”\"']?\s*no|voted\s+in\s+opposition|"
    r"with\s+the\s+no\s+votes|voted\s+no\s+to\s+the\s+motion)", re.I)
ABSENT_CLAUSE = re.compile(
    _NAMELIST + r"\s*(?:was|were)?\s*absent", re.I)

# page-break footer lines to strip so roll-call blocks flatten. These must be FULL-LINE
# matches (anchored) — a running footer is a line that is ONLY the footer text (+ maybe a
# page number), NOT a sentence that merely begins with "City Council meeting ...".
FOOTER_RE = re.compile(
    r"^\s*(?:"
    r"South Jordan City|"
    r"(?:Combined )?City Council(?: & RDA| & Redevelopment Agency)?"
    r"(?: Electronic| Study| Budget| Special| Regular| Work Session)? Meeting|"
    r"Redevelopment Agency Meeting|Combined City Council & Redevelopment Agency Meeting|"
    r"Board of Canvass(?: Meeting)?"
    r")\s*\d{0,3}\s*$", re.I)
FOOTER_DATE_RE = re.compile(
    r"^\s*(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+\d{4}\s*$", re.I)
PAGENUM_RE = re.compile(r"^\s*\d{1,3}\s*$")

# body-bracket markers (RDA)
RDA_OPEN = re.compile(
    r"recess.*move to.*redevelopment agency|move to (?:a|the) redevelopment agency|"
    r"redevelopment agency action item|action item:\s*resolution rda|"
    r"^\s*recess city council.*redevelopment agency", re.I)
RDA_CLOSE = re.compile(
    r"adjourn.*(?:rda|redevelopment agency)\s*meeting.*"
    r"(?:return to|go back|back into|reconvene).*city council|"
    r"adjourn.*redevelopment agency.*return to.*city council|"
    r"^\s*adjourn redevelopment agency.*return to city council|"
    r"(?:return to|go back into|back to|move to)\s+(?:a |the )?city council meeting|"
    r"reconvene.*city council", re.I)

# strong result signatures
DEATH_RE = re.compile(
    r"lack of (?:a )?second|no second,\s*(?:the )?motion (?:failed|died)|"
    r"failed due to lack|there was no second", re.I)
# A tally is a digit-dash-digit BOUND to a vote phrase (so Ordinance/Resolution numbers
# and addresses/dates like "2025-09" or "R2025-41" are NOT mistaken for a vote).
TALLY_RESULT = re.compile(
    r"(?:vote (?:of|was)|by a vote of|with a vote of|denied with a vote of|"
    r"a vote of|roll call vote(?:[^0-9\n]{0,60}?was)?)\s*(\d)\s*[-–]\s*(\d)"
    r"|(\d)\s*[-–]\s*(\d)\s*[,;.]?\s*(?:unanimous|in favor|motion (?:failed|passed|"
    r"carried|denied)|item\b)", re.I)
FAIL_RE = re.compile(r"denied|failed|did not (?:pass|carry)|motion (?:was )?denied", re.I)
UNANIMOUS_RE = re.compile(r"unanimous|passed unanimously", re.I)
# lines that merely discuss another body's vote — never a council result anchor
NOT_RESULT = re.compile(r"planning commission|recommend|percent|\bpc\b", re.I)


def result_info(line):
    """Return dict(kind, outcome, [a, b]) if `line` is a motion RESULT, else None."""
    if DEATH_RE.search(line):
        return {"kind": "death", "outcome": "Fail"}
    if NOT_RESULT.search(line):
        return None
    m = TALLY_RESULT.search(line)
    if m:
        if m.group(1) is not None:
            a, b = int(m.group(1)), int(m.group(2))
        else:
            a, b = int(m.group(3)), int(m.group(4))
        outcome = "Fail" if FAIL_RE.search(line) else "Pass"
        return {"kind": "tally", "outcome": outcome, "a": a, "b": b}
    if UNANIMOUS_RE.search(line) and re.search(r"\bvote\b|favor|motion", line, re.I):
        return {"kind": "unanimous", "outcome": "Pass"}
    return None


# ---------------------------------------------------------------------------
# Parsing one meeting
# ---------------------------------------------------------------------------
def load_lines(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if FOOTER_RE.match(s) or FOOTER_DATE_RE.match(s) or PAGENUM_RE.match(s):
            continue
        out.append(ln)
    return out


def bracket_state(lines):
    """line index -> body ('Council' | 'RDA') via an RDA recess/return state machine."""
    state = "Council"
    at = {}
    for i, ln in enumerate(lines):
        # markers frequently wrap across a line break ("...go back into a\nCity Council
        # meeting."), so test the current line joined with the next.
        probe = ln + " " + (lines[i + 1] if i + 1 < len(lines) else "")
        if state == "Council" and RDA_OPEN.search(probe):
            state = "RDA"
        elif state == "RDA" and RDA_CLOSE.search(probe):
            state = "Council"
        at[i] = state
    return at


def determine_body(text, bracket):
    low = text.lower()
    # procedural / transition motions are ALWAYS Council business, even when they merely
    # reference an RDA item (recess/adjourn into the board, amend the agenda, table an RDA
    # resolution, closed session, approve minutes/agenda). The board's SUBSTANTIVE votes are
    # the "approve/adopt Resolution RDA/MBA" motions below.
    if re.search(r"recess|adjourn|reconvene|convene|amend the agenda|closed session|"
                 r"executive session|\btable\b|approve the (?:agenda|minutes|consent|order)|"
                 r"go back into|return to|move to (?:a|the) (?:closed|city council)", low):
        return "Council"
    if re.search(r"resolution mba|\bmba \d|municipal building authority", low):
        return "MBA"
    if re.search(r"resolution rda|\brda \d|community reinvestment agency|"
                 r"cra (?:area plan|budget|draft)|redevelopment project area|"
                 r"reinvestment (?:project )?area", low):
        return "RDA"
    if bracket in ("RDA", "MBA"):
        return bracket
    return "Council"


def surnames_in(group, want_mayor=False):
    out, mayor_hit = [], False
    for chunk in re.split(r"(?:Council|Board)\s*Members?|Board\s*Chair|,|\band\b", group,
                          flags=re.I):
        nm, is_m = find_member(chunk)
        if nm is None:
            continue
        if is_m:
            mayor_hit = True
            if want_mayor and nm not in out:
                out.append(nm)
        elif nm not in out:
            out.append(nm)
    return out, mayor_hit


def parse_meeting(lines):
    at = bracket_state(lines)
    n = len(lines)
    votes = []
    pending = None
    i = 0

    def finalize(p, ri, anchor_idx):
        motion_text = re.sub(r"\s+", " ", " ".join(p["text"])).strip(" .;,")
        motion_text = re.split(r"\.\s+" + ROLE_PREFIX + r"\s+\S+\s+seconded", motion_text,
                               flags=re.I)[0].strip(" .;,")
        body = determine_body(motion_text, at.get(p["start"], "Council"))
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        mayor_voted, mayor = False, None
        names_recorded = False
        printed_tally = None

        # tabular window = whole motion body (intro .. result anchor + wraps).
        win_lines = lines[p["start"]:min(anchor_idx + 3, n)]
        # NARROW window for narrative name-callouts (dissent/absent sit on/next to the
        # tally, or just before it for "voted in opposition. By a vote of 3-2 ..."), so
        # discussion paragraphs earlier in the motion cannot leak names into the vote.
        nw0 = max(p["start"], anchor_idx - 3)
        win_str = re.sub(r"\s+", " ",
                         " ".join(x.strip() for x in lines[nw0:min(anchor_idx + 4, n)]))

        if ri["kind"] == "death":
            result_str = "Died (no second)"
            votes.append(_mk(p, motion_text, body, result_str, buckets, False,
                             None, False, None))
            return

        # ---- TABULAR roll call (one member per line) ----
        tab = []  # (canonical, vote_bucket, is_mayor)
        for wl in win_lines:
            tm = TAB_RE.match(wl)
            if not tm:
                continue
            role, namephrase, vlabel = tm.group(1), tm.group(2), tm.group(3).lower()
            is_mayor = role.lower().startswith("mayor") and "pro tem" not in role.lower()
            nm, m_from_name = find_member(role + " " + namephrase)
            if is_mayor or m_from_name:
                if nm is None or nm == MAYOR_NAME:
                    nm = MAYOR_NAME
                    is_mayor = True
                tab.append((nm, VOTE_MAP.get(vlabel, "aye"), is_mayor))
            elif nm:
                tab.append((nm, VOTE_MAP.get(vlabel, "aye"), False))

        if len(tab) >= 2:
            seen = set()
            for nm, bkt, is_m in tab:
                if nm in seen:
                    continue
                seen.add(nm)
                buckets[bkt].append(nm)
                if is_m:
                    mayor_voted, mayor = True, MAYOR_NAME
            names_recorded = True
            if ri["kind"] == "tally":
                printed_tally = (ri["a"], ri["b"])
                result_str = f"{ri['a']}-{ri['b']} {ri['outcome']}"
            else:
                result_str = f"{len(buckets['aye'])}-{len(buckets['nay'])} {ri['outcome']}"
            votes.append(_mk(p, motion_text, body, result_str, buckets, names_recorded,
                             printed_tally, mayor_voted, mayor))
            return

        # ---- NARRATIVE ----
        if ri["kind"] == "unanimous":
            # no printed number -> tally-only unanimous, names not recorded
            result_str = "Unanimous Pass"
            # still capture any explicitly-named absentee
            for mm in ABSENT_CLAUSE.finditer(win_str):
                names, _ = surnames_in(mm.group(1))
                for nm in names:
                    if nm not in buckets["absent"]:
                        buckets["absent"].append(nm)
            votes.append(_mk(p, motion_text, body, result_str, buckets, False,
                             None, False, None))
            return

        # tally with a printed number: aye = first, nay = second (city convention)
        a, b = ri["a"], ri["b"]
        printed_tally = (a, b)
        # named dissenters
        for mm in NAY_CLAUSE.finditer(win_str):
            names, m_hit = surnames_in(mm.group(1))
            for nm in names:
                if nm not in buckets["nay"]:
                    buckets["nay"].append(nm)
            if m_hit:
                mayor_voted, mayor = True, MAYOR_NAME
        # named absentees
        for mm in ABSENT_CLAUSE.finditer(win_str):
            names, _ = surnames_in(mm.group(1))
            for nm in names:
                if nm not in buckets["absent"] and nm not in buckets["nay"]:
                    buckets["absent"].append(nm)

        result_str = f"{a}-{b} {ri['outcome']}"
        # majority (ayes) is unnamed in narrative form -> names_recorded stays False
        votes.append(_mk(p, motion_text, body, result_str, buckets, False,
                         printed_tally, mayor_voted, mayor))

    while i < n:
        line = lines[i]

        intro = MOTION_INTRO.search(line)
        if intro:
            mover, _ = find_member(intro.group(0))
            pending = {"start": i, "mover": mover, "seconder": None,
                       "text": [line[intro.start():].strip()], "sec_found": False}
            # same-line seconder?
            sm = SECONDER.search(line)
            if sm:
                pending["seconder"], _ = find_member(sm.group(0))
                pending["sec_found"] = True
            # same-line inline result?
            ri = result_info(line)
            if ri:
                finalize(pending, ri, i)
                pending = None
            i += 1
            continue

        if pending is not None:
            # capture seconder
            if not pending["sec_found"]:
                sm = SECONDER.search(line)
                if sm:
                    pending["seconder"], _ = find_member(sm.group(0))
                    pending["sec_found"] = True
                    # motion text ends at the seconder clause
                    pending["text"].append(line[:sm.start()].strip())
                elif len(pending["text"]) < 15:
                    pending["text"].append(line.strip())

            # look for a result on this line (flatten up to 2 following lines for wraps)
            ri = None
            end = i
            for span in (1, 2, 3):
                joined = " ".join(x.strip() for x in lines[i:i + span])
                cand = result_info(joined)
                if cand:
                    ri, end = cand, i + span - 1
                    break
                if not re.search(r"vote|motion|second|favor|unanimous|roll call|denied|"
                                 r"failed|carried", joined, re.I):
                    break
            if ri:
                finalize(pending, ri, end)
                pending = None
                i = end + 1
                continue

            # abandon a runaway pending (no result within a long stretch — a motion whose
            # vote was never recorded; the next motion intro also resets `pending`)
            if i - pending["start"] > 160:
                pending = None

        i += 1

    return votes


def _mk(p, motion_text, body, result_str, buckets, names_recorded,
        printed_tally, mayor_voted, mayor):
    return {
        "body": body,
        "motion": motion_text[:600],
        "motion_type": classify_motion(motion_text),
        "result": result_str,
        "mover": p.get("mover"),
        "seconder": p.get("seconder"),
        "aye": buckets["aye"],
        "nay": buckets["nay"],
        "abstain": buckets["abstain"],
        "absent": buckets["absent"],
        "recuse": buckets["recuse"],
        "names_recorded": names_recorded,
        "printed_tally": list(printed_tally) if printed_tally else None,
        "mayor_voted": mayor_voted,
        "mayor": mayor,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def main():
    force = "--force" in sys.argv
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

        votes = parse_meeting(load_lines(path))
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        payload = {
            "date": r["date"],
            "year": int(year),
            "title": r["title"],
            "source": rel,
            "votes": votes,
        }
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON  (skipped {skipped} existing)")
    build_all_votes()


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n_rows = 0
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
                        n_rows += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")


if __name__ == "__main__":
    main()
