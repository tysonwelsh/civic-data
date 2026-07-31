#!/usr/bin/env python3
"""
extract_votes.py — South Jordan Planning Commission vote extractor.

PURE deterministic parser (NO LLM, NO network) over the 125 PC minutes markdown
files under planning_commission/minutes/. Modeled on the sibling narrative-tally
extractor (sandy_city_council/meeting_minutes/extract_votes.py): South Jordan's
clerk records votes as a NARRATIVE TALLY, never a per-name roll-call block, so
vote majorities are honestly UNNAMED — only dissenters and absentees are named.

The corpus vote grammar (measured, not assumed):
  * Unanimous:  "Roll Call Vote was 5-0, unanimous in favor."  /  "Vote was 4-0
    unanimous in favor."  /  "Vote was unanimous in favor." (no numeric tally).
    -> tally captured, NO individual names (names_recorded:false), one placeholder
       row. The X ayes are NEVER guessed.
  * Named dissent: "Vote was 6-1 with Commissioner Bevans voting No." /
    "Roll Call Vote was 3-2, majority in favor with Chair Hollist and Commissioner
    Bevans issuing no votes." / "3-2 Vote. Commissioner Hollist and Commissioner
    Catmull Voted No." / "4-1, with Chair Hollist voting no."
    -> the named dissenter(s) go to the `nay` bucket; the majority stays UNNAMED
       (names_recorded:false, exactly like Sandy's inline-tally form). Emitted rows
       are the named dissenters (+ named absentees) only.
  * Unnamed dissent: "Roll Call Vote was 3-2, majority of negative votes."
    -> contested tally with NO dissenter named -> placeholder row, names blank
       (never invented).
  * Named absentees: "Commissioner Bishop and Commissioner Harding were absent
    from the vote." -> `absent` rows (explicit source statement, not a guess).
  * Mover/seconder on every motion: "Commissioner X motioned to ... Chair Y
    seconded the motion."
  * Case numbers "File No. PL..." (PLCUP*/PLSPR*/PLPP*/PLPLA*/PLZBA*/PLZTA*/...)
    are captured into the motion record (feeds the referral layer).
  * Recommendation-vs-final-action: legislative items (rezone/general plan/code
    or text amendment/annexation/resolution) are "positive/negative recommendation
    to City Council"; CUP / site plan / plat / subdivision / dwelling-unit items
    are PC FINAL ACTIONS. Encoded in the JSON `action_kind` field (alongside the
    verbatim `result`) and reflected in `motion_type`.

Faithful-capture rules (SCHEMA_SPEC.md §2/§4):
  * `result` and the numeric tally are VERBATIM as printed.
  * The parseable region is CUT at the "true and correct copy" certification line
    so quoted prior-meeting motions inside post-adjournment attachments (a real
    hazard in 2 files) can never fabricate a phantom motion.
  * Deterministic, resumable: writes votes/<year>/<week>/<date>_<slug>.json per
    meeting, then rebuilds all_votes.csv (13-col long schema, body=PlanningCommission).

Run:  python3 extract_votes.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "minutes_index.csv"
VOTES_DIR = ROOT / "votes"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"

BODY = "PlanningCommission"

# --------------------------------------------------------------------------- roster canon
# surname (lowercased) -> canonical full name. Built from the corpus's titled
# ("Chair"/"Vice Chair"/"Commissioner") full-name mentions; OCR/first-name variants
# fold to the canonical spelling by surname. Surnames are unique across the SJ PC,
# so surname resolution never collides (no shared-surname ambiguity here).
CANON = {
    "hollist": "Michele Hollist", "holist": "Michele Hollist",
    "gedge": "Nathan Gedge",
    "bevans": "Laurel Bevans",
    "catmull": "Steven Catmull",
    "darby": "Trevor Darby",
    "morrissey": "Sean Morrissey", "morrisey": "Sean Morrissey",
    "bishop": "Sam Bishop", "bisop": "Sam Bishop",
    "bevan": "Laurel Bevans", "gedged": "Nathan Gedge",
    "starks": "Aaron Starks", "stark": "Aaron Starks",
    "wimmer": "Ray Wimmer",
    "harding": "Lori Harding", "hading": "Lori Harding",
    "farnsworth": "Bryan Farnsworth", "farnworth": "Bryan Farnsworth",
    "peirce": "Michael Peirce", "pierce": "Michael Peirce",
    "sanderson": "Brad Sanderson",
}
TITLE = r"(?:Chair|Vice[- ]?Chair|Commissioner|Commissoner)"
UNKNOWN_SURNAMES: dict[str, int] = {}


def canon_name(raw: str):
    """Resolve a title-stripped name phrase (e.g. 'Nathan Gedge' or 'Gedge') to a
    canonical commissioner full name via its surname. Returns None if the surname
    is not a known commissioner (never invents)."""
    toks = re.findall(r"[A-Za-z]+", raw)
    if not toks:
        return None
    surname = toks[-1].lower()
    if surname in CANON:
        return CANON[surname]
    # a leading first-name token might disambiguate a mangled surname; try each
    for t in toks:
        if t.lower() in CANON:
            return CANON[t.lower()]
    UNKNOWN_SURNAMES[surname] = UNKNOWN_SURNAMES.get(surname, 0) + 1
    return None


# --------------------------------------------------------------------------- regexes
# End-of-meeting cut: everything from the clerk certification onward is footer +
# attachments (quoted prior motions live here -> phantom-motion hazard).
CERT_RE = re.compile(r"true and correct copy", re.I)

# A vote declaration: "Roll Call Vote was 5-0 ...", "Vote was 4-0 ...",
# "Roll Call Vote 5-0 ...", "Vote was unanimous ...". Tight enough that prose
# "a no vote would indicate" / "a yes vote would mean" does NOT match (needs a
# digit-pair or 'unanimous' right after the optional was/is).
VOTE_RE = re.compile(
    r"(?P<lead>Roll\s*[Cc]all\s*[Vv]ote|[Vv]ote)\s+"
    r"(?:(?:wa[s]?|is)\s+)?,?\s*"
    r"(?:(?P<a>\d)\s*[-–]\s*(?P<b>\d)|(?P<unan>unanimous))",
)

# A motion start (mover). Optional full name; verb variants incl. 'amended'.
MOVER_RE = re.compile(
    TITLE + r"\s+(?P<name>[A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)"
    r"\s+(?:motioned|made\s+a\s+motion|moved|moves|amended|said,?\s+I\s+move[sd]?)",
)
SECOND_RE = re.compile(
    TITLE + r"\s+(?P<name>[A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)"
    r"\s+secon(?:ded|d|eded)",
)

# named dissenters. The clerk phrases dissent many ways (all observed in-corpus):
#   "... voting No" / "... voted no" / '... voting "no,"' (smart quotes) /
#   "... issuing no votes" / "... was a no vote" / '... gave "no" vote' /
#   "... voting against"  AND the name-AFTER form "no votes made by X, Y, and Z".
# up to two connector tokens between names handles the Oxford ", and" ("A, B, and C")
_NAMELIST = r"(?:" + TITLE + r"\s+[A-Z][A-Za-z'’.\-]+(?:\s*(?:,|and)\s*){0,2})+"
_Q = r"[\"'“”‘’]?"
NEG_BEFORE_RE = re.compile(
    r"(?P<names>" + _NAMELIST + r")\s*"
    r"(?:issuing\s+no\s+votes|voting\s+" + _Q + r"\s*no|voted\s+" + _Q + r"\s*no|"
    r"voting\s+against|voted\s+against|(?:was|were)\s+a?\s*no\s+vote|"
    r"gave\s+(?:a\s+)?" + _Q + r"\s*no" + _Q + r"\s*vote)",
    re.I,
)
NEG_AFTER_RE = re.compile(
    r"no\s+votes?\s+(?:made\s+|cast\s+)?by\s+(?P<names>" + _NAMELIST + r")", re.I,
)
# named absentees "... was/were absent from the vote"
ABS_RE = re.compile(
    r"(?P<names>" + _NAMELIST + r")\s*(?:was|were)\s+absent\s+from\s+the\s+vote",
    re.I,
)
# named abstentions "... abstained / abstaining"
ABSTAIN_RE = re.compile(
    r"(?P<names>" + _NAMELIST + r")\s*abstain(?:ed|ing|s)?",
    re.I,
)
FILE_NO_RE = re.compile(r"PL[A-Z]{2,4}\d{5,}")


def _names_from(span: str):
    """Split a captured name-list ('Chair Hollist and Commissioner Bevans') into
    canonical commissioner names, order-preserving, deduped."""
    out = []
    for m in re.finditer(TITLE + r"\s+([A-Z][A-Za-z'’.\-]+(?:\s+[A-Z][A-Za-z'’.\-]+)?)", span):
        nm = canon_name(m.group(1))
        if nm and nm not in out:
            out.append(nm)
    return out


def _commissioners_in(chunk: str):
    """Titled commissioners PLUS any bare known-surname mention (the SJ clerk
    sometimes lists a commissioner in the Present block without the 'Commissioner'
    title, e.g. 'Steven Catmull'). Surnames are unique to commissioners here, so a
    bare-surname scan does not collide with staff/public names."""
    names = _names_from(chunk)
    for surname, full in CANON.items():
        if full not in names and re.search(r"\b" + re.escape(surname) + r"\b", chunk, re.I):
            names.append(full)
    return names


# --------------------------------------------------------------------------- classification
LANDUSE_KW = ("subdivision", "plat", "site plan", "conditional use", "cup",
              "rezone", "zone change", "zoning", "general plan", "annex",
              "pud", "dwelling unit", "land use", "floating zone", "master plan",
              "development", "final action")
LEGISLATIVE_KW = ("rezone", "zone change", "general plan", "annex", "code amendment",
                  "text amendment", "land use amendment", "master plan", "ordinance",
                  "floating zone")
PROC_KW = ("agenda", "minutes", "adjourn", "nominate", "elect ", "table",
           "continue", "recess", "reconvene", "extend", "by-law", "bylaw",
           "rules of procedure", "commission rules")


def classify(motion: str, result: str, filenos):
    t = (motion or "").lower()
    r = (result or "").lower()
    has_file = bool(filenos)

    # --- procedural / administrative ---
    proc = any(k in t for k in PROC_KW) and not has_file
    # "approve the ... agenda"/"approve the minutes" without a file number
    if proc:
        return "Procedural/Administrative", "procedural"

    # --- recommendation vs final action ---
    is_rec = ("recommend" in t or "recommend" in r or "forward" in t
              or ("council" in t and ("positive" in t or "negative" in t or "send" in t))
              or "positive recommendation" in r or "negative recommendation" in r)
    is_legislative = any(k in t for k in LEGISLATIVE_KW)
    if is_rec or is_legislative:
        action = "recommendation"
    elif has_file or any(k in t for k in LANDUSE_KW):
        action = "final_action"
    else:
        action = "other"

    # --- motion_type (fixed 12-cat) ---
    if any(k in t for k in ("ordinance", "code amendment", "text amendment")) \
            and not any(k in t for k in ("rezone", "zone change", "site plan", "plat")):
        mtype = "Ordinance"
    elif "resolution" in t and not any(k in t for k in LANDUSE_KW):
        mtype = "Resolution"
    elif has_file or any(k in t for k in LANDUSE_KW) or is_legislative:
        mtype = "Land-Use/Zoning"
    elif any(k in t for k in PROC_KW):
        mtype = "Procedural/Administrative"
    else:
        mtype = "Other"
    return mtype, action


# --------------------------------------------------------------------------- parsing
def cut_meeting(text: str) -> str:
    m = CERT_RE.search(text)
    return text[:m.start()] if m else text


def parse_attendance(text: str):
    """Commissioners in the meeting's Present:/Absent: header blocks (title-prefixed
    names only; staff/public excluded). Returns (present, absent) canonical lists."""
    def block(label):
        m = re.search(rf"^\s*{label}\s*:(.*?)(?:\n\s*\n|^\s*(?:Present|Absent|Others|Excused|Staff)\s*:)",
                      text, re.I | re.S | re.M)
        if not m:
            return []
        chunk = re.sub(r"\s+", " ", m.group(1))
        return _commissioners_in(chunk)
    return block("Present"), block("Absent")


def parse_meeting(path: Path):
    raw = path.read_text(encoding="utf-8")
    text = cut_meeting(raw)
    present, absent_hdr = parse_attendance(text)

    motions = []
    for vm in VOTE_RE.finditer(text):
        # ---- backward window: nearest preceding mover + seconder + file numbers ----
        pre = text[max(0, vm.start() - 900):vm.start()]
        movers = list(MOVER_RE.finditer(pre))
        if movers:
            mv = movers[-1]
            motion_span = pre[mv.start():]
            mover = canon_name(mv.group("name")) or ""
        else:
            motion_span = pre[-300:]
            mover = ""
        sec = None
        for sm in SECOND_RE.finditer(motion_span):
            sec = sm
        seconder = canon_name(sec.group("name")) if sec else ""
        # motion text: mover phrase up to (not including) the vote clause, cleaned
        motion_text = re.sub(r"\s+", " ", motion_span).strip()
        # drop a trailing seconder sentence fragment from the visible motion text
        motion_text = re.sub(r"\s*" + TITLE + r"\s+[A-Z][\w'.\-]+\s+secon(?:ded|d|eded)\b.*$",
                             "", motion_text).strip()
        motion_text = motion_text[:600]
        filenos = list(dict.fromkeys(FILE_NO_RE.findall(motion_span)))

        # ---- forward tail: the vote sentence(s) for tally + named dissent/absent ----
        tail_raw = text[vm.start():vm.start() + 320]
        # stop at the next motion start (avoid bleeding into the next item)
        nxt = MOVER_RE.search(tail_raw, 40)
        if nxt:
            tail_raw = tail_raw[:nxt.start()]
        tail = re.sub(r"\s+", " ", tail_raw).strip()

        # verbatim result string: from the tally token to the end of its sentence
        res_m = re.search(r"(?:\d\s*[-–]\s*\d|unanimous)[^.]*", tail)
        result = (res_m.group(0).strip().strip(".") if res_m else tail[:120]).strip()
        result = re.sub(r"\s+", " ", result)

        if vm.group("unan") and vm.group("a") is None:
            tally = None  # "unanimous in favor" with no numeric tally
            aye_ct = nay_ct = None
        else:
            aye_ct, nay_ct = int(vm.group("a")), int(vm.group("b"))
            tally = (aye_ct, nay_ct)

        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        for neg in (NEG_BEFORE_RE, NEG_AFTER_RE):
            for nm in neg.finditer(tail):
                for x in _names_from(nm.group("names")):
                    if x not in buckets["nay"]:
                        buckets["nay"].append(x)
        am = ABS_RE.search(tail)
        if am:
            buckets["absent"] = _names_from(am.group("names"))
        # abstain: only if the word 'abstain' is genuinely in the tail
        if re.search(r"abstain", tail, re.I):
            ab = ABSTAIN_RE.search(tail)
            if ab:
                for x in _names_from(ab.group("names")):
                    if x not in buckets["nay"] and x not in buckets["absent"]:
                        buckets["abstain"].append(x)

        mtype, action = classify(motion_text, result, filenos)

        # majorities are NEVER named in this corpus -> names_recorded reflects only
        # whether any dissenter/absentee/abstainer was explicitly named.
        names_recorded = any(buckets[k] for k in buckets)

        motions.append({
            "body": BODY,
            "motion": motion_text,
            "motion_type": mtype,
            "action_kind": action,       # normalized, alongside verbatim result
            "result": result,
            "tally_aye": aye_ct,
            "tally_nay": nay_ct,
            "file_numbers": filenos,
            "mover": mover,
            "seconder": seconder,
            "names_recorded": names_recorded,
            "aye": buckets["aye"],
            "nay": buckets["nay"],
            "abstain": buckets["abstain"],
            "absent": buckets["absent"],
            "recuse": buckets["recuse"],
        })
    return motions, present, absent_hdr


# --------------------------------------------------------------------------- driver
def main():
    rows = list(csv.DictReader(INDEX.open()))
    roster = {}  # name -> {first, last, present, votes}

    def touch(name, date, present=False):
        r = roster.setdefault(name, {"first": date, "last": date,
                                     "present": 0, "votes": 0})
        r["first"] = min(r["first"], date)
        r["last"] = max(r["last"], date)
        if present:
            r["present"] += 1

    processed = 0
    for r in rows:
        path = ROOT / r["path"]
        if not path.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        date, year = r["date"], int(r["year"])
        week = Path(r["path"]).parent.name
        slug = Path(r["path"]).stem
        out_dir = VOTES_DIR / str(year) / week
        out_dir.mkdir(parents=True, exist_ok=True)

        motions, present, absent_hdr = parse_meeting(path)
        for k, m in enumerate(motions, start=1):
            m["motion_no"] = k
        for nm in present:
            touch(nm, date, present=True)
        for nm in absent_hdr:
            touch(nm, date)

        (out_dir / f"{slug}.json").write_text(json.dumps({
            "date": date, "year": year, "title": r["title"], "source": r["path"],
            "present": present, "absent_header": absent_hdr,
            "votes": motions,
        }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        processed += 1

    print(f"Processed {processed} meetings -> JSON")
    n_rows, n_motions = build_all_votes(roster)
    build_roster(roster)
    print(f"Wrote {ALL_VOTES}: {n_motions} motions, {n_rows} member-vote rows")
    if UNKNOWN_SURNAMES:
        print("WARNING unknown surnames (not in CANON, votes dropped):",
              dict(sorted(UNKNOWN_SURNAMES.items(), key=lambda x: -x[1])), file=sys.stderr)


def build_all_votes(roster):
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    bucket_map = [("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                  ("absent", "Absent"), ("recuse", "Recuse")]
    n_rows = n_motions = 0
    with ALL_VOTES.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            data = json.loads(jp.read_text(encoding="utf-8"))
            for v in data["votes"]:
                n_motions += 1
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key, label in bucket_map:
                    for member in v.get(key, []):
                        w.writerow(base + [member, label, data["source"]])
                        roster.setdefault(member, {"first": data["date"],
                                                   "last": data["date"],
                                                   "present": 0, "votes": 0})
                        roster[member]["votes"] += 1
                        n_rows += 1
                        emitted = True
                if not emitted:
                    # tally-only / voice / majority-unnamed -> one placeholder row
                    w.writerow(base + ["", "", data["source"]])
                    n_rows += 1
    return n_rows, n_motions


def build_roster(roster):
    with ROSTER.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen",
                    "meetings_present", "vote_rows"])
        for name in sorted(roster, key=lambda n: (-roster[n]["present"], n)):
            r = roster[name]
            w.writerow([name, r["first"], r["last"], r["present"], r["votes"]])


if __name__ == "__main__":
    main()
