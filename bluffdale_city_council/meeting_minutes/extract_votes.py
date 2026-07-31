#!/usr/bin/env python3
"""Bluffdale vote extractor — PURE deterministic (no LLM, no network), resumable.

One file, dropped into BOTH meeting_minutes/ (dataset=council) and planning_commission/
(dataset=pc); it auto-detects the dataset from its own directory name and carries both
rosters.

Bluffdale prints FULL NAMED roll calls, so votes are read directly from the bounded
  "Vote on [Mm]otion: <name>-<Yes/No/...>; ... The motion passed/failed <N-to-M|unanimously>."
clause (result-anchored parsing). It also uses a names-less
  "The motion passed with the unanimous consent of the Council/Board."
form (tally-only -> one placeholder row, names_recorded:false).

COUNCIL body facts (from real roll calls):
  * 5 at-large Council Members + a NON-voting Mayor -> max council-MEMBER tally = 5.
  * The council recesses IN-SESSION as the Redevelopment Agency (RDA) and Local Building
    Authority (LBA); in THOSE bodies the Mayor votes as Chair/Board Member (max 6). A
    per-line body state machine tags each motion body in {Council, RDA, LBA}.
  * On the rare genuine COUNCIL tie-break the Mayor is named in a Council tally; captured
    FAITHFULLY and flagged mayor_voted:true (never fabricated, never dropped).
  Mayors: Derk Timothy (2020-2021), Natalie Hall (2022+). City Recorder "Tami Timothy" is
  staff and never appears in a vote clause, so surname Timothy in a tally = Mayor Timothy.

PC: Chair + Commissioners all vote (the Chair votes, unlike the council Mayor). Legislative
  items carry POSITIVE/NEGATIVE recommendation-to-Council language (kept verbatim in motion).
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATASET = "pc" if ROOT.name == "planning_commission" else "council"
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
DEFAULT_BODY = "PlanningCommission" if DATASET == "pc" else "Council"

# --------------------------------------------------------------------------- rosters
# surname (lowercase, OCR-normalized) -> (canonical full name, is_mayor)
COUNCIL_ROSTER = {
    "aston": ("Wendy Aston", False), "austin": ("Steve Austin", False),
    "lord": ("Alan Lord", False), "wilding": ("Greg Wilding", False),
    "crockett": ("Traci Crockett", False), "smith": ("Mackey Smith", False),
    "kallas": ("Dave Kallas", False), "hales": ("Mark Hales", False),
    "gaston": ("Jeff Gaston", False),
    "hall": ("Natalie Hall", True), "timothy": ("Derk Timothy", True),
}
PC_ROSTER = {
    "cragun": ("Debbie Cragun", False), "luker": ("Kori Luker", False),
    "flynn": ("Ulises Flynn", False), "swanson": ("Erik Swanson", False),
    "griffis": ("Tina Griffis", False), "kraupp": ("Michael Kraupp", False),
    "walston": ("Stephen Walston", False), "brown": ("Holly Brown", False),
    "woodruff": ("Joel Woodruff", False), "loomis": ("Johnny Loomis Jr", False),
}
ROSTER = PC_ROSTER if DATASET == "pc" else COUNCIL_ROSTER

# OCR surname fixups -> canonical surname key
OCR_SURNAME = {
    "kauas": "kallas", "kaus": "kallas", "auston": "austin",
    "wuding": "wilding", "woding": "wilding", "hau": "hall", "rockett": "crockett",
    "fynn": "flynn", "fiynn": "flynn", "griffls": "griffis", "valston": "walston",
    "alston": "walston", "loumis": "loomis",
}
ROLE_WORDS = {"council", "member", "members", "board", "trustee", "commissioner", "chair",
              "chairman", "chairperson", "chairwoman", "mayor", "acting", "vice", "pro",
              "tem", "tempore", "the", "city", "and", "councilmember"}
SUFFIX = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv"}

VOTE_MAP = {"yes": "aye", "aye": "aye", "no": "nay", "nay": "nay",
            "abstain": "abstain", "abstained": "abstain", "abstention": "abstain",
            "absent": "absent", "excused": "absent",
            "recuse": "recuse", "recused": "recuse"}


def norm_surname(name):
    """A raw name phrase -> canonical roster key or None (drops role words + suffixes)."""
    toks = [t.strip(".,") for t in re.split(r"\s+", name.strip())]
    toks = [t for t in toks if t and t.lower() not in ROLE_WORDS and t.lower() not in SUFFIX]
    if not toks:
        return None
    sur = toks[-1].lower()
    sur = OCR_SURNAME.get(sur, sur)
    return sur if sur in ROSTER else None


# --------------------------------------------------------------------------- cleaning
def clean_text(raw):
    t = raw.split("---\n\n", 1)[-1]
    t = re.sub(r"Counc\w{1,3}\s+Member", "Council Member", t)   # CouncU Member -> Council Member
    # drop a name suffix ("Johnny Loomis, Jr.-Aye" -> "Johnny Loomis-Aye") so the comma+suffix
    # can't sever the surname from its vote token.
    t = re.sub(r",?\s+(?:Jr|Sr|II|III|IV)\.?(?=\s*[-–—\s])", "", t, flags=re.I)
    return t


# --------------------------------------------------------------------------- body state machine (council only)
LBA_HDR = re.compile(r"LOCAL BUILDING AUTHORITY.*BOARD MEETING", re.I)
RDA_HDR = re.compile(r"REDEVELOPMENT AGENCY BOARD MEETING", re.I)
CC_HDR = re.compile(r"CITY COUNCIL\s+(?:REGULAR|BUSINESS|WORK|SPECIAL|ELECTRONIC)", re.I)


def collapse(clean):
    return re.sub(r"\s+", " ", clean)


# body is decided per-motion (RDA/LBA keywords or mover role); no marker layer needed.
class _NoMark:
    def sub(self, repl, s):
        return s


BODY_MARK = _NoMark()


# --------------------------------------------------------------------------- motion / result grammar
MOTION_INTRO = re.compile(
    r"(Council Member|Board Member|Trustee|Commissioner|Vice[- ]?Chair|Chair(?:man)?|"
    r"Acting Chair|Mayor(?:\s+Pro\s+Tem\w*)?)\s+([A-Z][A-Za-z'\.\-]+)\s+"
    r"(?:moved|made\s+a\s+motion)\b", re.I)
SECONDER = re.compile(
    r"seconded(?:\s+the\s+motion)?\s+by\s+(?:Council Member|Board Member|Trustee|"
    r"Commissioner|Vice[- ]?Chair|Chair(?:man)?|Mayor(?:\s+Pro\s+Tem\w*)?)?\s*"
    r"([A-Z][A-Za-z'\.\-]+)", re.I)
RESULT = re.compile(r"[Tt]he motion\s+(passed|failed|carried|died)([^.]*?)\.", re.I)
VOTE_CLAUSE = re.compile(r"[Vv]ote on [Mm]otion:", re.I)
TALLY_TOK = re.compile(
    r"([A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+){0,2}?)\s*[-–—]\s*"
    r"(Yes|No|Aye|Nay|Abstain(?:ed|tion)?|Absent|Excused|Recuse[d]?)\b", re.I)
DEATH = re.compile(r"lack of a second|no second", re.I)
TALLY_NUM = re.compile(r"(\d)\s*(?:-\s*)?to(?:\s*-)?\s*(\d)|(\d)\s*[-–]\s*(\d)", re.I)


def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development agreement|"
                 r"overlay|site plan|preliminary|final plat|concept plan|lot line|"
                 r"redevelopment|project area|planned (?:unit )?development|\bpud\b", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|tentative budget|final budget|adopt.*budget|"
                 r"amend(?:ing)? the .*budget|\bcertified tax rate\b", t):
        return "Budget"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"appoint|reappoint|mayor pro tem|ratify the (?:results|canvass)|\bcanvass\b", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the (?:bid|contract)|"
                 r"professional services|agreement with|enter into an agreement", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed|executive session|"
                 r"approve the (?:consent|agenda|minutes)|\btable\b|continue|postpone|"
                 r"amend the agenda|approve the .*minutes", t):
        return "Procedural/Administrative"
    return "Other"


def token_role(phrase):
    low = phrase.lower()
    if "trustee" in low:
        return "trustee"
    if "board" in low:
        return "board"
    if "council" in low:
        return "council"
    return "none"


def extract_tally(segment):
    """segment = text from 'Vote on Motion:' to the result.
    -> ordered [(fullname, bucket, is_mayor, token_role)]"""
    out, seen = [], set()
    for m in TALLY_TOK.finditer(segment):
        key = norm_surname(m.group(1))
        if key is None or key in seen:
            continue
        seen.add(key)
        full, is_mayor = ROSTER[key]
        out.append((full, VOTE_MAP.get(m.group(2).lower(), "aye"), is_mayor,
                    token_role(m.group(1))))
    return out


def parse_meeting(raw):
    clean = clean_text(raw)
    text = collapse(clean)
    votes = []
    prev_end = 0
    for rm in RESULT.finditer(text):
        rs, re_ = rm.start(), rm.end()
        verb = rm.group(1).lower()
        tail = rm.group(2)
        outcome = "Pass" if verb in ("passed", "carried") else "Fail"
        result_str = re.sub(r"\s+", " ", ("The motion " + rm.group(1) + tail)).strip()
        # motion span: from the last motion-intro before this result (after prev result)
        back = text[prev_end:rs]
        intros = list(MOTION_INTRO.finditer(back))
        mover = None
        mover_role = ""
        motion_start = prev_end
        if intros:
            last = intros[-1]
            mover_key = norm_surname(last.group(0))
            mover = ROSTER[mover_key][0] if mover_key else last.group(2)
            mover_role = last.group(1).lower()
            motion_start = prev_end + last.start()
        motion_region = text[motion_start:rs]
        motion_region = BODY_MARK.sub(" ", motion_region)
        # seconder
        sm = SECONDER.search(motion_region)
        seconder = None
        if sm:
            sk = norm_surname(sm.group(0))
            seconder = ROSTER[sk][0] if sk else sm.group(1)
        # motion text = intro .. up to Vote on Motion / seconder
        mtext = motion_region
        vc = VOTE_CLAUSE.search(mtext)
        cut = vc.start() if vc else (sm.start() if sm else len(mtext))
        motion_text = re.sub(r"\s+", " ", mtext[:cut]).strip(" .;,")

        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        names_recorded = False
        mayor_in_tally = False
        printed_tally = None
        tally_roles = set()

        # tally clause between the (last) Vote-on-Motion in the motion region and the result
        vlast = None
        for v in VOTE_CLAUSE.finditer(text[motion_start:rs]):
            vlast = v
        tally = []
        if vlast:
            seg = text[motion_start + vlast.end():rs]
            tally = extract_tally(seg)
            for full, bkt, is_mayor, trole in tally:
                buckets[bkt].append(full)
                if is_mayor:
                    mayor_in_tally = True
                elif trole != "none":
                    tally_roles.add(trole)
            if tally:
                names_recorded = True

        # body: the council sits IN-SESSION as the Redevelopment Agency (RDA; "Board Member"
        # voters) and the Local Building Authority (LBA; "Trustee" voters); the Mayor votes in
        # those (max 6). Decide from RELIABLE per-motion signals — the tally token roles, the
        # mover role, the "unanimous consent of the {Council|Board|RDA|LBA}" phrase, and mayor
        # participation — NOT letterhead keywords (the combined-meeting letterhead names all
        # three bodies on every page). Council is the default; the Mayor is non-voting there,
        # so a Mayor named in a Council tally is a genuine faithful mayor vote (tie-break).
        if DATASET == "pc":
            body = "PlanningCommission"
        else:
            cm = re.search(r"consent of (?:the )?(\w+)", tail, re.I)
            consent = cm.group(1).lower() if cm else ""
            if "trustee" in tally_roles or mover_role == "trustee" or consent == "lba":
                body = "LBA"
            elif "board" in tally_roles or mover_role == "board member" or consent == "rda":
                body = "RDA"
            elif "council" in tally_roles or mover_role == "council member" \
                    or consent in ("council", "city"):
                body = "Council"
            elif consent == "board" or mover_role.startswith("mayor") or mayor_in_tally:
                body = "RDA"          # a board action with no LBA-specific marker
            else:
                body = "Council"
        mayor_voted = mayor_in_tally and body == "Council"

        # printed numeric tally from the result phrase
        nm = TALLY_NUM.search(tail)
        if nm:
            g = [x for x in nm.groups() if x is not None]
            printed_tally = [int(g[0]), int(g[1])]

        if DEATH.search(tail) or (verb == "died"):
            names_recorded = False
            buckets = {k: [] for k in buckets}

        votes.append({
            "body": body,
            "motion": motion_text[:600],
            "motion_type": classify_motion(motion_text),
            "result": result_str[:120],
            "mover": mover,
            "seconder": seconder,
            "aye": buckets["aye"], "nay": buckets["nay"], "abstain": buckets["abstain"],
            "absent": buckets["absent"], "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "printed_tally": printed_tally,
            "mayor_voted": mayor_voted,
        })
        prev_end = re_
    return votes


# --------------------------------------------------------------------------- driver
def main():
    force = "--force" in sys.argv
    rows = list(csv.DictReader(INDEX.open()))
    processed = skipped = 0
    for r in rows:
        path = ROOT / r["path"]
        if not path.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        week = Path(r["path"]).parent.name
        year = r["year"]
        slug = r["slug"]
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
             "source": r["path"], "votes": votes}, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON (skipped {skipped})")
    build_all_votes()


def build_all_votes():
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    n = 0
    with ALL_VOTES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(VOTES_DIR.rglob("*.json")):
            data = json.loads(jp.read_text())
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                   ("absent", "Absent"), ("recuse", "Recuse")):
                    for mem in v.get(key, []):
                        w.writerow(base + [mem, label, data["source"]])
                        n += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]])
                    n += 1
    print(f"Wrote {ALL_VOTES} with {n} data rows")


if __name__ == "__main__":
    main()
