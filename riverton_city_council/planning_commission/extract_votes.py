#!/usr/bin/env python3
"""
Riverton Planning Commission vote extractor  (PURE deterministic — no LLM, no network).

Reads the PC minutes markdown under planning_commission/minutes/<year>/<week>/, parses every
recorded motion, and emits:
  - one JSON per meeting under planning_commission/votes/<year>/<week>/<slug>.json  (resumable)
  - planning_commission/all_votes.csv  (13-col long format, one row per member-vote, body=PlanningCommission)
  - planning_commission/roster.csv     (OBSERVED commissioners: attendance + vote rows)

Riverton PC vote grammar (verified across the 2020->2026 PMN corpus):
  * MOVER/SECONDER, always named:
      "Commissioner Cluff moved that the Planning Commission recommend APPROVAL of
       Application PLZ-26-4001 ... Commissioner Keele seconded the motion."
  * UNANIMOUS -> "unanimous consent", NAMES NOT PRINTED (majority honestly unnamed):
      "The motion passed with the unanimous consent of the Commission."  /
      "The motion passed unanimously."
    -> names_recorded:false, one placeholder row. The ayes are NEVER guessed.
  * DIVIDED -> a FULL named roll call (every member) precedes the tally:
      "Commissioner Rushton-Aye; Commissioner Matheson-Aye; Chair Cluff-Nay;
       Commissioner Gilchrist-Aye; ... The motion passed 5-to-1."
    -> each Name-vote token parsed; names_recorded:true; numeric tally captured verbatim.
    (Tokens wrap lines — "Rushton-\nAye", "Cannon – Abstained" — flattened before parsing.)
  * DIED -> "The motion died for lack of a second." -> result "Died (no second)", no names.
Unlike South Jordan's PC (dissenter-only tallies), Riverton's clerk names EVERY member on a
divided vote, so the majority is captured too. There is NO mayor and NO tie-break on the PC.

Commissioners resolve through a fixed surname->canonical-name canon built from the corpus's
titled full-name mentions + the "Planning Commission Members:" attendance block; OCR/first-
name variants fold by surname. Monique Mortensen -> Monique Beck (same member, name change).
Any surname not in the canon is dropped (never guessed) and surfaced by validate_votes.py.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "minutes_index.csv"
VOTES_DIR = ROOT / "votes"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER_CSV = ROOT / "roster.csv"

BODY = "PlanningCommission"

# --------------------------------------------------------------------------- roster canon
CANON = {
    "rushton": "Troy Rushton", "ruston": "Troy Rushton", "rishton": "Troy Rushton",
    "cluff": "Shelly Cluff",
    "park": "Darren Park",
    "cannon": "Gary Cannon", "canno": "Gary Cannon",
    "russell": "Brian Russell", "russel": "Brian Russell",
    "matheson": "Evan Matheson",
    "lefgren": "Grant Lefgren",
    "james": "Ed James",
    "gilchrist": "Jon Gilchrist",
    "brown": "Natalia Brown",
    "breinholt": "Keith Breinholt",
    "beck": "Monique Beck", "mortensen": "Monique Beck",   # name change; same member
    "keele": "Crystal Keele",
    "marzo": "Joe Marzo",
    "hansen": "Dennis Hansen",
    "hartley": "Kent Hartley",
    "knudsen": "Chris Knudsen",
}
TITLE = r"(?:Chair|Vice[- ]?Chair|Chair\s+Pro\s+Tem(?:pore)?|Commissioner|Commissoner)"
UNKNOWN_SURNAMES = {}

VOTE_MAP = {
    "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
    "abstain": "abstain", "abstained": "abstain", "abstaining": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}


def lookup(raw):
    """Resolve a name phrase to a canonical commissioner via surname, WITHOUT counting
    misses (used for attendance/motion-text scans where non-commissioner tokens abound)."""
    for t in re.findall(r"[A-Za-z]+", raw or ""):
        if t.lower() in CANON:
            return CANON[t.lower()]
    return None


def canon_name(raw):
    """Resolve a mover/seconder/roll-call name; count genuine surname misses (a dropped
    voter is a real signal here) for validate_votes.py."""
    toks = re.findall(r"[A-Za-z]+", raw or "")
    if not toks:
        return None
    nm = lookup(raw)
    if nm:
        return nm
    UNKNOWN_SURNAMES[toks[-1].lower()] = UNKNOWN_SURNAMES.get(toks[-1].lower(), 0) + 1
    return None


# --------------------------------------------------------------------------- regexes
CERT_RE = re.compile(r"true and correct copy|respectfully submitted", re.I)

MOVER = re.compile(TITLE + r"\s+([A-Z][A-Za-z'’.\-]+)\s+(?:moved|made\s+a\s+motion)\b", re.I)
SECOND = re.compile(TITLE + r"\s+([A-Z][A-Za-z'’.\-]+)\s+secon(?:ded|d)\b", re.I)
NAMEVOTE = re.compile(
    r"([A-Z][A-Za-z'’\-]+)\s*[-–—]\s*"
    r"(aye|nay|yes|no|abstain(?:ed|ing)?|absent|excused|recuse[d]?)\b", re.I)
TALLY = re.compile(
    r"the motion\s+(?:passed|failed|carried)\s+(?:by a vote of\s+)?(\d+)\s*-?\s*to\s*-?\s*(\d+)",
    re.I)
UNAN = re.compile(r"unanimous(?:ly)?", re.I)
DIED = re.compile(r"died for lack of a second|for lack of a second|no second", re.I)
OUTCOME_SENT = re.compile(r"the motion\s+(passed|failed|carried|died)[^.]*", re.I)
FILE_NO = re.compile(r"\b([A-Z]{2,4}-\d{2}-\d{3,4})\b")


def _flatten(s):
    return re.sub(r"\s+", " ", s).strip()


# --------------------------------------------------------------------------- classification
def classify(text):
    t = (text or "").lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|\bcup\b|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|planned (?:unit )?development|"
                 r"home occupation|preliminary|final plat|lot line|density", t):
        mtype = "Land-Use/Zoning"
    elif re.search(r"\bordinance\b|code amendment|text amendment", t):
        mtype = "Ordinance"
    elif re.search(r"\bresolution\b", t):
        mtype = "Resolution"
    elif re.search(r"minutes|agenda|adjourn|elect|nominat|table|continue|recess|"
                   r"bylaw|by-law|rules of procedure", t):
        mtype = "Procedural/Administrative"
    else:
        mtype = "Other"
    # recommendation vs final action
    if re.search(r"recommend|forward|positive recommendation|negative recommendation", t):
        action = "recommendation"
    elif re.search(r"rezon|zone change|general plan|annex|code amendment|text amendment", t):
        action = "recommendation"
    elif mtype == "Land-Use/Zoning":
        action = "final_action"
    elif mtype == "Procedural/Administrative":
        action = "procedural"
    else:
        action = "other"
    return mtype, action


# --------------------------------------------------------------------------- parsing
def cut_meeting(text):
    m = CERT_RE.search(text)
    return text[:m.start()] if m else text


def strip_header(text):
    m = re.match(r"^#[^\n]*\n(?:>[^\n]*\n)*\n", text)
    return text[m.end():] if m else text


def parse_attendance(text):
    """Commissioners named under the 'Planning Commission Members:' block (full names,
    one per line) up to the 'Staff:' column / first numbered agenda item."""
    m = re.search(r"Planning Commission Members?\s*:?(.*?)(?:\n\s*\d+\.\s|CALL TO ORDER)",
                  text, re.I | re.S)
    if not m:
        return []
    seen, out = set(), []
    for line in m.group(1).splitlines():
        # left column only (drop the 'Staff:' names sharing the line via wide spacing)
        left = re.split(r"\s{3,}", line.strip())[0]
        nm = lookup(left)
        if nm and nm not in seen:
            seen.add(nm)
            out.append(nm)
    return out


def parse_meeting(text):
    body = strip_header(cut_meeting(text))
    # strip the running page header ("\x0cRiverton City Planning Commission Meeting 11"
    # + a "March 9, 2023" date line) — it lands MID-ROLL when a roll call wraps a page
    # break ("Commissioner Breinholt-<header>Aye;"), dropping that member's vote
    # (T3.1 Tier-A 2026-07-12: 2020-05-14 m1 Hartley, 2023-03-09 m2 Breinholt)
    body = re.sub(r"(?m)^\x0c?Riverton City[^\n]*Meeting[ \t]*\d*[ \t]*\n"
                  r"(?:(?:January|February|March|April|May|June|July|August|September|"
                  r"October|November|December)\s+\d{1,2},?\s+\d{4}[ \t]*\n)?", "", body)
    anchors = [m.start() for m in MOVER.finditer(body)]
    anchors.append(len(body))
    votes = []
    for i in range(len(anchors) - 1):
        seg = body[anchors[i]:anchors[i + 1]]
        flat = _flatten(seg)
        mv = MOVER.search(flat)
        mover = canon_name(mv.group(1)) if mv else None

        # motion text: after the mover verb, up to seconder / roll call / outcome
        mt = flat[mv.end():] if mv else flat
        mt = re.split(r"\bsecon(?:ded|d)\b|The motion\s+(?:passed|failed|died|carried)|"
                      r"[A-Z][A-Za-z'’\-]+\s*[-–—]\s*(?:aye|nay|yes|no)",
                      mt, 1, flags=re.I)[0]
        motion_text = re.sub(r"^(?:that the (?:Planning Commission|Commission)\s+)?", "",
                             mt.strip(" .;,:"), flags=re.I).strip()[:600]

        sec = SECOND.search(flat)
        seconder = canon_name(sec.group(1)) if sec else None
        filenos = list(dict.fromkeys(FILE_NO.findall(flat)))

        # named roll call (divided votes only)
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        seen = set()
        for nm in NAMEVOTE.finditer(flat):
            canon = canon_name(nm.group(1))
            if not canon or canon in seen:
                continue
            seen.add(canon)
            buckets[VOTE_MAP.get(nm.group(2).lower(), "aye")].append(canon)
        names_recorded = any(buckets[k] for k in buckets)

        tally = TALLY.search(flat)
        tally_aye = int(tally.group(1)) if tally else None
        tally_nay = int(tally.group(2)) if tally else None

        om = OUTCOME_SENT.search(flat)
        died = bool(DIED.search(flat)) and not tally and not names_recorded

        # result (native-faithful)
        if died:
            result = "Died (no second)"
        elif tally:
            verb = "Passed" if tally_aye >= tally_nay else "Failed"
            if om and re.search(r"\bfailed\b", om.group(0), re.I):
                verb = "Failed"
            result = f"{verb} {tally_aye}-to-{tally_nay}"
        elif om and re.search(r"\bfailed\b", om.group(0), re.I):
            result = "Failed"
        elif om and UNAN.search(om.group(0) + flat[om.end():om.end() + 60]):
            result = "Passed unanimously"
        elif UNAN.search(flat) and om:
            result = "Passed unanimously"
        elif om:
            result = "Passed"
        else:
            result = ""

        # skip noise: a "moved" with no outcome and no roll call and no death
        if not (names_recorded or tally or died or om or UNAN.search(flat)):
            continue

        mtype, action = classify(motion_text)
        votes.append({
            "body": BODY,
            "motion": motion_text,
            "motion_type": mtype,
            "action_kind": action,
            "result": result,
            "tally_aye": tally_aye, "tally_nay": tally_nay,
            "file_numbers": filenos,
            "mover": mover, "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"],
            "abstain": buckets["abstain"], "absent": buckets["absent"],
            "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
        })
    return votes


# --------------------------------------------------------------------------- driver
def main():
    force = "--force" in sys.argv
    if not INDEX.exists():
        print(f"no index at {INDEX} — run fetch_new.py first", file=sys.stderr)
        build_all_votes()
        return
    rows = list(csv.DictReader(INDEX.open()))
    roster = {}
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
        text = path.read_text(encoding="utf-8", errors="replace")
        present = parse_attendance(strip_header(text))
        for nm in present:
            rr = roster.setdefault(nm, {"first": r["date"], "last": r["date"],
                                        "present": 0, "votes": 0})
            rr["first"] = min(rr["first"], r["date"])
            rr["last"] = max(rr["last"], r["date"])
            rr["present"] += 1
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(text)
        for k, v in enumerate(votes, 1):
            v["motion_no"] = k
        out_json.write_text(json.dumps(
            {"date": r["date"], "year": int(year), "title": r["title"],
             "source": rel, "present": present, "votes": votes},
            indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON  (skipped {skipped} existing)")
    build_all_votes(roster)
    build_roster(roster)
    if UNKNOWN_SURNAMES:
        print("WARNING unknown surnames (not in CANON, dropped):",
              dict(sorted(UNKNOWN_SURNAMES.items(), key=lambda x: -x[1])), file=sys.stderr)


def build_all_votes(roster=None):
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
                        if roster is not None:
                            roster.setdefault(member, {"first": data["date"],
                                                       "last": data["date"],
                                                       "present": 0, "votes": 0})
                            roster[member]["votes"] += 1
                        n_rows += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    print(f"Wrote {ALL_VOTES} with {n_rows} data rows")


def build_roster(roster):
    with ROSTER_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "meetings_present", "vote_rows"])
        for name in sorted(roster, key=lambda n: (-roster[n]["present"], n)):
            r = roster[name]
            w.writerow([name, r["first"], r["last"], r["present"], r["votes"]])
    print(f"Wrote {ROSTER_CSV} with {len(roster)} commissioners")


if __name__ == "__main__":
    main()
