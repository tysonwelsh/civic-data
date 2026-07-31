#!/usr/bin/env python3
"""
Murray Planning Commission vote extractor  (PURE deterministic — no LLM, no network).

Reads the PC-meeting markdown under planning_commission/minutes/<year>/<week>/, parses
every recorded motion, resolves each named voter against the fixed commissioner roster,
and emits:
  - one JSON per meeting under planning_commission/votes/<year>/<week>/<slug>.json  (resumable)
  - planning_commission/all_votes.csv   (13-col long format; body=PlanningCommission)
  - planning_commission/roster.csv      (OBSERVED: member,first_seen,last_seen,n_votes)

MURRAY PC VOTE GRAMMAR (built to this; corpus is 2020-2022, 61 files)
---------------------------------------------------------------------
 A) TALLY-ONLY prose (dominant): mover + seconder named, NO per-member roll call:
      "Scot Woodbury made a motion to approve the Findings of Fact ...
       Seconded by Lisa Milkavich.
       A voice vote was made, motion passed 7-0."
    Result forms: "Motion passed 7-0." / "Motion Passes 7-0." / "Voice vote of 6-0." /
      "Motion passed 7-0, unanimous in favor." -> ONE placeholder row, blank member/vote.
 B) NAMED roll call (2022 only) — a "<code> <surname>" column under "Roll Call Vote:":
      "Seconded by Mr. Richards. Roll Call Vote:
        A     Patterson
        A     Richards
        A     Milkavich
        A     Nay          (code A = Aye; 'Nay' here is Commissioner Travis NAY's surname)
        A     Hacker
        A     Pehrson
        A     Lowry
       Motion Passes 7-0."
    -> named Aye/Nay/... rows (code -> vote value; surname -> roster).

Only the roster surnames below map to a vote; PLANNING STAFF (Jared Hall, Zac/Zachary
Smallwood, Susan Nixon, Seth Rios, Briant Farnsworth, ...) and APPLICANTS never do.
NOTE: Commissioner "Travis Nay" — surname collides with the vote word "Nay"; it is only
ever resolved in a NAME position (mover/seconder/roll-call surname column), never a value.
"""
import csv
import json
import re
import sys
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
ROSTER = ROOT / "roster.csv"
FORCE = "--force" in sys.argv
BODY = "PlanningCommission"

# ---------------------------------------------------------------------------
# Commissioner roster (OBSERVED 2020-2026; 2023-2026 names added at the 2026-07-16
# pmn_backfill promotion — verified against the attendance blocks, which mark staff
# with a role suffix; STAFF never enter this map: Phil Markham is CED DIRECTOR from
# 2023 (kept only for his 2020-21 Chair era votes), and "David Rodgers, Senior
# Planner" is STAFF here — his surname must NOT map (he is a COUNCIL member in the
# sibling dataset; a stray "Rodgers" would also fuzzy-collide with Katie Rogers).
# ---------------------------------------------------------------------------
SURNAME_TO_FULL = {
    "markham": "Phil Markham",      # Chair 2020-2021
    "woodbury": "Scot Woodbury",    # Vice Chair
    "nay": "Travis Nay",
    "patterson": "Maren Patterson", # Chair 2024
    "milkavich": "Lisa Milkavich",
    "wilson": "Sue Wilson",
    "hacker": "Ned Hacker",         # Chair 2026
    "lowry": "Jeremy Lowry",        # Chair 2022
    "pehrson": "Jake Pehrson",
    "richards": "Michael Richards", # Chair 2025
    "hristou": "Pete Hristou",      # 2023+
    "henrie": "Michael Henrie",     # 2023-2024
    "hildreth": "Aaron Hildreth",   # 2024+
    "klinge": "Peter Klinge",       # 2024+
    "rogers": "Katie Rogers",       # 2024+
}
FIRST_TO_FULL = {
    "phil": "Phil Markham", "scot": "Scot Woodbury", "scott": "Scot Woodbury",
    "travis": "Travis Nay", "maren": "Maren Patterson", "lisa": "Lisa Milkavich",
    "sue": "Sue Wilson", "ned": "Ned Hacker", "jeremy": "Jeremy Lowry",
    "jake": "Jake Pehrson", "michael": "Michael Richards",
    "pete": "Pete Hristou", "peter": "Peter Klinge",
    "aaron": "Aaron Hildreth", "katie": "Katie Rogers",
    # NB "michael" is genuinely ambiguous 2023-24 (Richards vs Henrie) — the clerk
    # only ever uses surnames in vote positions, so the mapping is kept for the
    # 2020-22 corpus; "Commissioner Michaels" (2024-03-07 typo) resolves to neither.
}
SURNAME_ALIASES = {
    "miklavich": "milkavich", "milkavitch": "milkavich", "milkavick": "milkavich",
    "woodbery": "woodbury", "woodberry": "woodbury", "pierson": "pehrson",
    "pearson": "pehrson", "hacker": "hacker",
}
SURNAMES = list(SURNAME_TO_FULL.keys())
FULLNAMES = set(SURNAME_TO_FULL.values())


def canon(chunk):
    if not chunk:
        return None
    words = [w for w in re.split(r"[^A-Za-z']+", chunk.lower()) if len(w) >= 2]
    if not words:
        return None
    for w in words:
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in SURNAME_TO_FULL:
            return SURNAME_TO_FULL[w2]
    for w in words:
        w2 = SURNAME_ALIASES.get(w, w)
        if w2 in FIRST_TO_FULL:
            return FIRST_TO_FULL[w2]
    for w in words:
        if len(w) < 5:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.84)
        if m:
            return SURNAME_TO_FULL[m[0]]
    return None


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories) — PC is land-use heavy.
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|"
                 r"development agreement|overlay|site plan|design review|"
                 r"street vacation|\bvacat|redevelopment|project area|"
                 r"reinvestment|planned (?:unit )?development|\bpud\b|"
                 r"preliminary|final plat|findings of fact|home occupation|"
                 r"variance|setback|\btod\b|accessory|lot line", t):
        return "Land-Use/Zoning"
    if re.search(r"budget|appropriat", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperative agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|ratify|nominat|chair|vice-chair|vice chair|elect", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|professional services|agreement with|lease", t):
        return "Contract/Purchase"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"proclamation|recogniz|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"\bminutes\b|adjourn|recess|reconvene|convene|amend the agenda|"
                 r"closed session|\btable\b|continue|postpone|approve the agenda", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Line loading — strip page-break footers.
# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(
    r"^\s*(?:Planning Commission(?:\s+\w+)*\s+Meeting|Page\s+\d+|"
    r"(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s+\d{4})\s*$", re.I)


def load_lines(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"\n---\n", text, maxsplit=1)
    body = parts[1] if len(parts) > 1 else text
    return [ln for ln in body.split("\n") if not FOOTER_RE.match(ln)]


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
ROLE = r"(?:Commissioner|Chair|Vice[\s-]?Chair|Mr\.|Ms\.|Mrs\.)"
NAME = r"[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?"

# 2026-07-16 (2023-2026 corpus): + bare "move" (clerk typo "Commissioner Nay move to
# grant...", 2023-12-07) and "made a recommendation that" (2024-03-21) — both are real
# seconded roll-call motions in the promoted minutes.
VERB = r"(?:mov(?:ed|es|e)|motioned|made (?:a|the) (?:motion|recommendation)|makes? (?:a|the) motion)"
INTRO_RE = re.compile(r"(" + ROLE + r"\s+)?(" + NAME + r")\s+" + VERB + r"\b", re.I)
VERB_LEAD = re.compile(r"^\s*(" + VERB + r")\b(.*)", re.I)
# 2026-07-16: mid-sentence pronoun motion ("Commissioner Patterson said that ...,
# she moves that the Planning Commission continue this item", 2023-09-07) — the mover
# is the last roster name named earlier in the same sentence/paragraph.
PRONOUN_INTRO = re.compile(r"\b(?:she|he)\s+mov(?:es|ed)\s+that\b(.*)", re.I)
# 2020-2021 passive form: "A motion was made by <Name> to ..."
PASSIVE_INTRO = re.compile(
    r"(?:A\s+)?motion\s+was\s+made\s+by\s+" + ROLE + r"?\s*(" + NAME + r")\b(.*)", re.I)
SEC_BY = re.compile(r"secon\w*d(?:ed)?\s+(?:by|from)\s+" + ROLE + r"?\s*(" + NAME + r")", re.I)
# 2026-07-16: 2023+ clerk pre-form "Mr. Hacker seconded. Roll call vote:" (also
# "Commissioner Milkavich Seconded.") — same as the council extractor's SEC_PRE.
SEC_PRE = re.compile(ROLE + r"\s+(" + NAME + r")\s+secon\w*d", re.I)

# named roll-call row: "<code>  <surname>"  (code A/N/AB/EX/R or the full word)
CODE_MAP = {
    "a": "Aye", "aye": "Aye", "ayes": "Aye", "y": "Aye", "yes": "Aye",
    "n": "Nay", "nay": "Nay", "nays": "Nay", "no": "Nay",
    "ab": "Abstain", "abs": "Abstain", "abstain": "Abstain", "abstained": "Abstain",
    "abstention": "Abstain",
    "ex": "Excused", "excused": "Excused", "absent": "Absent",
    "r": "Recuse", "re": "Recuse", "recuse": "Recuse", "recused": "Recuse",
}
# 2020-2021 roll row: "__A__ Ned Hacker"  (code wrapped in underscores + FULL NAME)
PC_ROLL_UNDER = re.compile(
    r"^\s*_+\s*([A-Za-z]{1,3})\s*_+\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+)?)\s*$")
# 2022 roll row: " A   Patterson"  (bare 1-2-letter code + surname; only inside a roll block)
PC_ROLL_BARE = re.compile(r"^\s*([A-Za-z]{1,2})\s{1,}([A-Z][a-z][A-Za-z'\-]+)\s*$")
ROLL_HEADER = re.compile(r"roll\s*call|call\s+vote|vote\s+recorded", re.I)

RES_PATTERNS = [
    (re.compile(r"[Tt]he motion was not seconded[^.\n]*", re.I), "Fail"),
    # 2026-07-16: "Seeing no second, the motion failed." (2024-07-18)
    (re.compile(r"Seeing no second[^.\n]*", re.I), "Fail"),
    (re.compile(r"(?:A\s+)?voice vote was made,\s*motion\s+failed[^.\n]*", re.I), "Fail"),
    (re.compile(r"(?:A\s+)?voice vote was made,\s*motion\s+(?:passed|passes)[^.\n]*", re.I), "Pass"),
    # 2026-07-16: "fail(?:ed|s)" covers the 2025+ clerk form "Motion fails: 0-6";
    # the bare failed-pattern is line-anchored so narrative prose ("... if the current
    # motion to approve failed", 2025-08-07 discussion) can no longer swallow a roll call.
    (re.compile(r"Motion\s+fail(?:ed|s)\s*:?\s*\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Fail"),
    (re.compile(r"^\s*(?:The\s+)?[Mm]otion\s+fail(?:ed|s)\b[^.\n]*", re.I), "Fail"),
    (re.compile(r"Motion\s+(?:passed|passes|carried)\s*:?\s*\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Pass"),
    (re.compile(r"Voice vote of\s*\d+\s*[-–]\s*\d+[^.\n]*", re.I), "Pass"),
    (re.compile(r"Voice vote taken,?\s*all\s*[“”\"']?\s*[Aa]yes[.“”\"']*(?:\s*Approved\s*\d+\s*[-–]\s*\d+)?[^.\n]*", re.I), "Pass"),
    # 2023-2026 clerk form (76 instances in the promoted PMN-recovered minutes):
    #   "A voice vote was made/taken(,) with all in favor (of adjournment)."
    (re.compile(r"(?:A\s+)?voice vote was (?:made|taken),?\s*with all in favor[^.\n]*", re.I), "Pass"),
    (re.compile(r"Motion\s+(?:passed|passes|carried)[^.\n]*", re.I), "Pass"),
]


def match_result(text):
    for rx, outcome in RES_PATTERNS:
        m = rx.search(text)
        if m:
            return re.sub(r"\s+", " ", m.group(0)).strip(" ."), outcome
    return None


def clean_motion(parts):
    s = re.sub(r"\s+", " ", " ".join(parts)).strip()
    s = re.split(r"\s*Seconded\s+by", s, flags=re.I)[0]
    s = re.split(ROLL_HEADER, s)[0]
    s = re.split(r"A voice vote", s, flags=re.I)[0]
    return s.strip(" .,;:")[:500]


# ---------------------------------------------------------------------------
def parse_meeting(lines):
    n = len(lines)

    def scan_intro(i):
        """(mover, first_motion_text) for a motion at line i, else None.  Accepts a
        role-prefixed OR bare roster-surname mover, and a wrapped intro whose verb opens
        line i with the mover's name on line i-1."""
        m = INTRO_RE.search(lines[i])
        if m and (m.group(1) or canon(m.group(2))):
            return canon(m.group(2)), lines[i][m.end():]
        pm = PASSIVE_INTRO.search(lines[i])
        if pm and canon(pm.group(1)):
            return canon(pm.group(1)), pm.group(2)
        vl = VERB_LEAD.match(lines[i])
        if vl and i > 0:
            m2 = INTRO_RE.search(lines[i - 1].rstrip() + " " + vl.group(1))
            if m2 and canon(m2.group(2)):
                return canon(m2.group(2)), vl.group(2)
        pn = PRONOUN_INTRO.search(lines[i])
        if pn:
            # mover = the last ROLE-prefixed roster name in the sentence leading up to
            # the pronoun (same line first, then up to two prior lines) — never guessed.
            for probe in (lines[i][:pn.start()],
                          lines[i - 1] if i > 0 else "",
                          lines[i - 2] if i > 1 else ""):
                cands = [canon(m.group(0)) for m in
                         re.finditer(ROLE + r"\s+" + NAME, probe)]
                cands = [c for c in cands if c]
                if cands:
                    return cands[-1], pn.group(1)
        return None

    intros = []
    for i in range(n):
        si = scan_intro(i)
        if si:
            intros.append((i, si[0], si[1]))
    intro_starts = [i for i, _, _ in intros]

    votes = []
    consumed_until = -1
    for k, (idx, mover, first_text) in enumerate(intros):
        if idx <= consumed_until:
            continue
        nxt = intro_starts[k + 1] if k + 1 < len(intros) else n
        window_end = min(nxt + 2, n)

        seconder = None
        buckets = {"Aye": [], "Nay": [], "Abstain": [], "Absent": [],
                   "Excused": [], "Recuse": []}
        motion_parts = [first_text]
        in_roll = False
        result = None
        result_line = None

        j = idx
        while j < window_end:
            # 2026-07-16: if a named roll has been collected but no result was printed
            # before the NEXT motion's intro (clerk omission, e.g. 2023-10-19 Fairborn
            # CUP), stop here — never steal the next motion's result line; the tally is
            # synthesized from the roll below.
            if j >= nxt and j > idx and any(buckets[b] for b in buckets):
                break
            line = lines[j]
            if seconder is None:
                sm = SEC_BY.search(line) or SEC_PRE.search(line)
                if sm:
                    seconder = canon(sm.group(1))

            # underscore roll row "__A__ Ned Hacker" (self-evident — parse anywhere)
            um = PC_ROLL_UNDER.match(line)
            if um:
                in_roll = True
                code = um.group(1).lower().strip("_")
                nm = canon(um.group(2))
                if code in CODE_MAP and nm:
                    b = CODE_MAP[code]
                    if nm not in buckets[b]:
                        buckets[b].append(nm)
                j += 1
                continue

            if ROLL_HEADER.search(line):
                in_roll = True
                j += 1
                continue

            # bare "A  Patterson" roll row — only inside a roll block (else attendance bleeds).
            # A non-matching line does NOT end the block (page-break footers split roll blocks);
            # the block ends naturally at the result line / next motion intro.
            # 2026-07-16: a roll block printed with NO "Roll call vote:" header (2025-08-07,
            # "N Hildreth / N Hristou / ..." straight after discussion) self-opens when TWO
            # consecutive lines are code+roster-surname rows — a single stray two-token line
            # can never fake a roll.
            if not in_roll and j + 1 < n:
                b1, b2 = PC_ROLL_BARE.match(line), PC_ROLL_BARE.match(lines[j + 1])
                if (b1 and b2 and b1.group(1).lower() in CODE_MAP
                        and b2.group(1).lower() in CODE_MAP
                        and canon(b1.group(2)) and canon(b2.group(2))):
                    in_roll = True
            if in_roll:
                bm = PC_ROLL_BARE.match(line)
                if bm and bm.group(1).lower() in CODE_MAP:
                    nm = canon(bm.group(2))
                    if nm:
                        b = CODE_MAP[bm.group(1).lower()]
                        if nm not in buckets[b]:
                            buckets[b].append(nm)
                    j += 1
                    continue

            rr = match_result(line)
            if not rr and j + 1 < n:
                rr = match_result(line + " " + lines[j + 1])
                if rr:
                    result, _ = rr
                    result_line = j + 1
                    break
            if rr:
                result, _ = rr
                result_line = j
                break

            if not in_roll and j > idx and len(motion_parts) < 10:
                motion_parts.append(line)
            j += 1

        named = any(buckets[b] for b in buckets)
        if result is None:
            if named:
                result = f"{len(buckets['Aye'])}-{len(buckets['Nay'])}"
            else:
                continue  # no recorded verdict near this move-verb -> not a real vote

        motion_text = clean_motion(motion_parts)
        votes.append({
            "motion": motion_text,
            "motion_type": classify_motion(motion_text),
            "result": result,
            "mover": mover or "",
            "seconder": seconder or "",
            "names_recorded": named,
            "aye": buckets["Aye"], "nay": buckets["Nay"],
            "abstain": buckets["Abstain"], "absent": buckets["Absent"],
            "excused": buckets["Excused"], "recuse": buckets["Recuse"],
        })
        if result_line is not None:
            consumed_until = result_line

    for no, v in enumerate(votes, 1):
        v["motion_no"] = no
    return votes


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def json_path_for(rel_path, year):
    parts = rel_path.split("/")
    return VOTES_DIR / str(year) / parts[-2] / parts[-1].replace(".md", ".json")


def main():
    rows = list(csv.DictReader(INDEX.open(encoding="utf-8")))
    VOTES_DIR.mkdir(exist_ok=True)
    processed = skipped = 0
    for r in rows:
        path = ROOT / r["path"]
        if not path.exists():
            print("MISSING", r["path"], file=sys.stderr)
            continue
        jp = json_path_for(r["path"], r["year"])
        if jp.exists() and not FORCE:
            skipped += 1
            continue
        jp.parent.mkdir(parents=True, exist_ok=True)
        votes = parse_meeting(load_lines(path))
        payload = {"date": r["date"], "year": int(r["year"]), "title": r["title"],
                   "body": BODY, "source": r["path"], "votes": votes}
        jp.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON (skipped {skipped})")
    rebuild_csv(rows)
    build_roster(rows)


def rebuild_csv(rows):
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]
    nrows = 0
    with ALL_VOTES.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            jp = json_path_for(r["path"], r["year"])
            if not jp.exists():
                continue
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], data.get("body", BODY),
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover", ""), v.get("seconder", "")]
                emitted = False
                for key, lab in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                 ("absent", "Absent"), ("excused", "Excused"),
                                 ("recuse", "Recuse")):
                    for mem in v.get(key, []):
                        w.writerow(base + [mem, lab, data["source"]])
                        nrows += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    nrows += 1
    print(f"Wrote {ALL_VOTES} ({nrows} rows)")


def build_roster(rows):
    seen = {}
    for r in rows:
        jp = json_path_for(r["path"], r["year"])
        if not jp.exists():
            continue
        data = json.loads(jp.read_text())
        date = data["date"]
        for v in data["votes"]:
            people = set()
            for k in ("aye", "nay", "abstain", "absent", "excused", "recuse"):
                people.update(v.get(k, []))
            for p in people:
                d = seen.setdefault(p, {"first": date, "last": date, "n": 0})
                d["first"] = min(d["first"], date)
                d["last"] = max(d["last"], date)
                d["n"] += 1
    with ROSTER.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["member", "first_seen", "last_seen", "n_votes"])
        for nm in sorted(seen, key=lambda n: (seen[n]["first"], n)):
            d = seen[nm]
            w.writerow([nm, d["first"], d["last"], d["n"]])
    print(f"Wrote {ROSTER} ({len(seen)} members)")


if __name__ == "__main__":
    main()
