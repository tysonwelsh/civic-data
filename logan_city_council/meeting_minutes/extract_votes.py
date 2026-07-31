#!/usr/bin/env python3
"""
extract_votes.py — Logan (Utah) Municipal Council / RDA vote extractor.

Reads minutes markdown listed in meeting_minutes/minutes_index.csv, extracts each
recorded motion + roll-call vote, writes one JSON per meeting under
meeting_minutes/votes/<year>/<week>/<date>_<slug>.json, then rebuilds
meeting_minutes/all_votes.csv (long format, one row per member-vote, WITH `body`).

LOGAN FORMAT (verified)
-----------------------
    ACTION. Motion by Councilmember Bradfield seconded by Councilmember M. Bradfield
    to approve Resolution 20-04 as presented. Motion carried by roll call vote.
       A. Anderson: Aye
       M. Anderson: Aye
       Bradfield: Aye
       Jensen: Aye
       Simmonds: Aye
Also "Motion carried unanimously." (sometimes followed by a named block, sometimes
tally-only with no names -> names_recorded:false), and split votes with `Name: Nay` /
`Name: Abstained` / `Name: Absent` / `Name: Excused`, plus a numeric tally `(4-1)`.

PITFALLS HANDLED
----------------
1. PAGE-FOOTER lines interleave mid-roll-call: `N | Page`, the running footer
   `Logan Municipal Council Minutes ~ Logan, Utah ~ <date>`, an optional `DRAFT`
   watermark prefix, and the top-of-page running header. These are STRIPPED from the
   whole document first so the `Name: Vote` sequence stays contiguous (the Sandy bug).
2. SAME-SURNAME members: two Andersons — `A. Anderson` = Amy Z. Anderson,
   `M. Anderson` = Mark A. Anderson. The roster is keyed on initial+surname; the two
   are NEVER collapsed. A BARE "Anderson" (no initial) is treated as unresolvable
   rather than guessed.
3. Aye/Nay/Abstain/Absent captured across line wraps; comma- AND "and"-separated mover
   lists accepted; bare "carried unanimously" with no names -> names_recorded:false
   (never invented).
4. MAYOR DOES NOT VOTE (separately elected, veto). The mayor never appears in a Logan
   roll-call block, so named votes never leak the mayor. Mark A. Anderson VOTES as a
   councilmember 2019-2025 but is MAYOR (non-voting) from Jan 2026 — in 2026 he simply
   stops appearing in roll-calls (his seat went to the new chair). validate_votes.py
   confirms NO mayor leak per year.

body: slug `city-council-meeting` -> Council; slug `redevelopment-agency-meeting` ->
RDA. (Acquisition already split RDA recesses into their own files.)
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent          # meeting_minutes/
REPO = ROOT.parent
MIN_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
OUT_CSV = ROOT / "all_votes.csv"

# ---------------------------------------------------------------------------
# Member roster.  Canonical display name keyed on initial+surname.
# The two Andersons are DISTINCT and must never be collapsed.
# ---------------------------------------------------------------------------
# Each entry: lowercase lookup key -> canonical display name.
NAME_MAP = {
    "a. anderson": "Amy Z. Anderson", "a anderson": "Amy Z. Anderson",
    "amy z. anderson": "Amy Z. Anderson", "amy anderson": "Amy Z. Anderson",
    "m. anderson": "Mark A. Anderson", "m anderson": "Mark A. Anderson",
    "mark a. anderson": "Mark A. Anderson", "mark anderson": "Mark A. Anderson",
    "simmonds": "Jeannie F. Simmonds", "jeannie f. simmonds": "Jeannie F. Simmonds",
    "jeannie simmonds": "Jeannie F. Simmonds",
    "jensen": "Tom Jensen", "tom jensen": "Tom Jensen",
    "bradfield": "Jess W. Bradfield", "jess w. bradfield": "Jess W. Bradfield",
    "jess bradfield": "Jess W. Bradfield", "m. bradfield": "Jess W. Bradfield",
    "lopez": "Ernesto López", "lópez": "Ernesto López",
    "ernesto lopez": "Ernesto López", "ernesto lópez": "Ernesto López",
    "johnson": "Mike Johnson", "mike johnson": "Mike Johnson",
    "lee-koven": "Katie Lee-Koven", "koven": "Katie Lee-Koven",
    "katie lee-koven": "Katie Lee-Koven", "lee koven": "Katie Lee-Koven",
    "dahle": "Melissa Dahle", "melissa dahle": "Melissa Dahle",
}
# Mayor (NON-VOTING) per year, for the validation leak check.
MAYOR = {2020: "Holly H. Daines", 2021: "Holly H. Daines", 2022: "Holly H. Daines",
         2023: "Holly H. Daines", 2024: "Holly H. Daines", 2025: "Holly H. Daines",
         2026: "Mark A. Anderson"}

# Role words to strip from mover/seconder/name fragments.
ROLE_RE = re.compile(
    r"\b(council\s*members?|councilmembers?|councilmember’s|vice\s*chair|acting\s*chair|"
    r"chairman|chairwoman|chair|mayor|board\s*members?|agency\s*members?|member|council)\b",
    re.I)


def canon(token):
    """Map a name fragment (possibly role-prefixed, possibly accented) to a roster
    display name, or None if it can't be resolved (e.g. bare 'Anderson')."""
    if not token:
        return None
    t = ROLE_RE.sub(" ", token)
    t = t.replace("&", " ").strip().strip(".,;:")
    t = re.sub(r"\s+", " ", t).lower()
    if not t:
        return None
    if t in NAME_MAP:
        return NAME_MAP[t]
    # try just the trailing surname token (with optional leading initial)
    m = re.search(r"([a-záéíóúñ]\.\s*)?([a-záéíóúñ-]+)$", t)
    if m:
        cand = (m.group(1) or "") + m.group(2)
        cand = re.sub(r"\s+", " ", cand).strip()
        if cand in NAME_MAP:
            return NAME_MAP[cand]
        sur = m.group(2)
        # bare 'anderson' is ambiguous -> unresolved
        if sur == "anderson":
            return None
        if sur in NAME_MAP:
            return NAME_MAP[sur]
    return None


# ---------------------------------------------------------------------------
# Footer / header stripping  (pitfall #1)
# ---------------------------------------------------------------------------
FOOTER_PATTERNS = [
    re.compile(r"^\s*\d+\s*\|\s*Page\s*$", re.I),                       # "12 | Page"
    re.compile(r"^\s*(DRAFT\s+)?Logan (Municipal Council|Redevelopment Agency)"
               r".*Minutes\s*~", re.I),                                  # running footer (+DRAFT)
    re.compile(r"^\s*Logan Municipal Council\s{2,}Logan,\s*Utah", re.I), # top running header
    re.compile(r"^\s*DRAFT\s*$", re.I),                                  # bare DRAFT watermark
    re.compile(r"^\s*Page\s*$", re.I),
]


def strip_footers(text):
    out = []
    for ln in text.splitlines():
        if any(p.match(ln) for p in FOOTER_PATTERNS):
            continue
        out.append(ln)
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Motion typing (fixed 12-category taxonomy)
# ---------------------------------------------------------------------------
def motion_type(text, context=""):
    t = (context + " " + text).upper()
    mt = text.upper()
    if re.search(r"\bADJOURN", mt) and "CLOSED" not in mt:
        return "Procedural/Administrative"
    if "CLOSED SESSION" in mt or "EXECUTIVE SESSION" in mt:
        return "Procedural/Administrative"
    if re.search(r"\bRECESS|RECONVENE|\bTABLE\b|CONTINUE|POSTPONE|CANCEL|AMEND.*AGENDA|"
                 r"APPROVE.*AGENDA|AMEND TONIGHT", mt):
        return "Procedural/Administrative"
    if re.search(r"\bMINUTES\b", mt) and "RESOLUTION" not in mt and "ORDINANCE" not in mt:
        return "Procedural/Administrative"
    if re.search(r"PUBLIC HEARING.*(CLOSE|OPEN)|CLOSE THE PUBLIC HEARING|OPEN THE PUBLIC HEARING", mt):
        return "Public Hearing Action"
    if re.search(r"PROCLAMATION|RECOGNI|CEREMON|HONOR\b|RETIREMENT", mt):
        return "Ceremonial"
    if re.search(r"BUDGET AMENDMENT|AMEND.*BUDGET|BUDGET ADJUSTMENT", t):
        return "Budget Amendment"
    if re.search(r"APPOINT|REAPPOINT|RATIFY THE APPOINTMENT|NOMINATE|ELECT\b.*(CHAIR|VICE)", t):
        return "Appointment"
    if "INTERLOCAL" in t or "COOPERATIVE AGREEMENT" in t:
        return "Interlocal"
    if re.search(r"REZON|ZONING MAP|RECLASSIF|STREET VACATION|VACAT|ANNEX|CONDITIONAL USE|"
                 r"\bPLAT\b|SUBDIVI|GENERAL PLAN|LAND (USE|DEVELOPMENT) CODE|OVERLAY ZONE|"
                 r"DESIGN REVIEW|PLANNED (UNIT |)DEVELOPMENT", t):
        return "Land-Use/Zoning"
    if "ORDINANCE" in mt:
        return "Ordinance"
    if "RESOLUTION" in mt:
        return "Resolution"
    if re.search(r"\bGRANT\b|CDBG|HOME FUNDS|\bAWARD\b|FUNDING", t):
        return "Grant-Funding"
    if re.search(r"CONTRACT|PURCHASE|\bBID\b|PROPOSAL|\bLEASE\b|CONVEY|SALE\b|ACQUI|"
                 r"AGREEMENT", t):
        return "Contract/Purchase"
    return "Other"


# ---------------------------------------------------------------------------
# Vote-block parsing
# ---------------------------------------------------------------------------
VOTE_NORM = {
    "aye": "Aye", "yes": "Aye", "yea": "Aye",
    "nay": "Nay", "no": "Nay",
    "abstain": "Abstain", "abstained": "Abstain",
    "absent": "Absent", "excused": "Absent",
}
NAME_LINE = re.compile(
    r"^\s*([A-Za-zÁÉÍÓÚáéíóúñ][A-Za-zÁÉÍÓÚáéíóúñ.\-' ]{0,28}?)\s*:\s*"
    r"(Aye|Yes|Yea|Nay|No|Abstain|Abstained|Absent|Excused)\s*\.?\s*$", re.I)

# Motion anchor.
ANCHOR = re.compile(r"\bMotion(?:\s+made)?\s+by\b", re.I)
ANCHOR2 = re.compile(r"\bA?\s*[Mm]otion was made(?:\s+and seconded)?\s+to\b")
# ANCHOR3: clerk-dropped "Motion by" form — the minutes read
#   "ACTION. <mover> seconded by <seconder> to <action>. Motion carried ..."
# with no leading "Motion by". Anchor on the "ACTION." token when a "seconded by"
# clause follows ON THE SAME LINE and it is NOT the normal "ACTION. Motion by ..."
# or "ACTION. A motion was made ..." form. 5 motions across 2023-05-02 (incl.
# Ordinance 23-15, the Tempki easement vacation) and 2025-04-01. See CLAUDE.md.
ANCHOR3 = re.compile(
    r"\bACTION\.\s+(?!(?:A\s+)?[Mm]otion\b)(?=[^\n]*?\bseconded\s+by\b)", re.I)
# ANCHOR4: WORD-SCRAMBLED adoption form. The clerk transposed the mover-name,
# "by", seconder-name and "seconded by" tokens so neither "Motion by" (ANCHOR)
# nor the ACTION.-led dropped-"Motion by" form (ANCHOR3, which excludes lines
# that DO start "ACTION. Motion") fires. Sole verified instance: 2025-12-02
# Ord 25-21 — "ACTION. Motion Councilmember A. Anderson by Vice Chair Johnson
# seconded by to adopt Ordinance 25-21 as presented. Motion carried ... (4-0)".
# Anchor on "ACTION. Motion" that is NOT the normal "Motion by"/"Motion made by"
# opener yet carries a "seconded by" clause on the same line. ATTRIBUTION is
# deliberately NOT reconstructed here: the scramble leaves the two names in a
# genuinely ambiguous mover/seconder order (position heuristic → mover
# A. Anderson; the "...by Vice Chair Johnson" preposition → mover Johnson), so
# the mover/seconder resolvers below find no confident "by <mover> seconded by
# <seconder>" span and BOTH stay blank (never guessed). The (4-0) roll call is
# captured verbatim. See CLAUDE.md.
ANCHOR4 = re.compile(
    r"\bACTION\.\s+Motion\b(?!\s+(?:made\s+)?by\b)(?=[^\n]*?\bseconded\s+by\b)", re.I)

# Outcome phrase: "Motion carried ...", "Motion failed ...", etc.  Group 2 captures the
# rest of the outcome clause on that line ("by roll call vote", "unanimously",
# "(4-1)", ...) so we keep the literal descriptor and any numeric tally.
OUTCOME = re.compile(
    r"\bMotion\s+(carried|failed|did not carry|was withdrawn|passed)\b([^.\n]*)", re.I)
TALLY = re.compile(r"\(?\b(\d+)\s*-\s*(\d+)\b\)?")


def parse_name_block(region):
    """Parse the contiguous `Name: Vote` lines that follow the outcome phrase.
    Returns dict of vote->list[canonical] and a list of raw unresolved names."""
    res = {"Aye": [], "Nay": [], "Abstain": [], "Absent": []}
    unresolved = []
    started = False
    # The outcome phrase ("... Motion carried by roll call vote.") may leave a trailing
    # prose tail on the lines before the names; skip leading prose lines until the FIRST
    # `Name: Vote` line, then treat a blank/prose line as the end of the contiguous block.
    # (Footers are already stripped, so within one motion-anchor block the only such
    # lines belong to THIS motion.)
    for i, ln in enumerate(region.splitlines()):
        s = ln.strip()
        m = NAME_LINE.match(ln)
        if m:
            started = True
            nm = canon(m.group(1))
            vote = VOTE_NORM[m.group(2).lower()]
            if nm:
                if nm not in res[vote]:
                    res[vote].append(nm)
            else:
                unresolved.append(s)
            continue
        if not s:
            if started:
                break
            continue
        if s.upper() in ("VACANT", "VACANT SEAT"):
            continue
        if started:
            break          # prose after the block -> done
        if i > 40:
            break          # never found a name block within range -> tally-only
        # else: still scanning leading prose before the names
    return res, unresolved


def parse_inline_dissent(sentence):
    """For older (2020-2021) prose form: '... (Councilmember Jensen & Chairman M.
    Anderson voted nay)' / '... A. Anderson and Chair Simmonds voted nay.'
    Returns list of canonical nay names (explicitly stated; no fabrication)."""
    names = []
    for m in re.finditer(r"([A-Za-zÁÉÍÓÚáéíóúñ.,&\s'-]{3,80}?)\s+voted?\s+nay", sentence, re.I):
        frag = m.group(1)
        frag = re.sub(r"^.*?[)(]", "", frag)  # drop anything before a paren
        for part in re.split(r",|&|\band\b", frag):
            nm = canon(part)
            if nm and nm not in names:
                names.append(nm)
    return names


def find_motions(text, year, default_body):
    clean = strip_footers(text)
    motions = []

    # collect anchor positions (primary + the rare "A motion was made to" form)
    anchors = [m.start() for m in ANCHOR.finditer(clean)]
    anchors += [m.start() for m in ANCHOR2.finditer(clean)]
    anchors += [m.start() for m in ANCHOR3.finditer(clean)]
    anchors += [m.start() for m in ANCHOR4.finditer(clean)]
    anchors = sorted(set(anchors))

    for ai, start in enumerate(anchors):
        nxt = anchors[ai + 1] if ai + 1 < len(anchors) else len(clean)
        block = clean[start:nxt]
        context = clean[max(0, start - 400):start]

        # locate outcome phrase within the block
        om = OUTCOME.search(block)
        if not om:
            continue  # a "Motion by" with no recorded outcome -> not a decided vote
        outcome_word = om.group(1).lower()
        carried = outcome_word in ("carried", "passed")
        outcome = "Pass" if carried else "Fail"
        descriptor = om.group(2) or ""
        tm_t = TALLY.search(descriptor)
        tally_a = int(tm_t.group(1)) if tm_t else None
        tally_b = int(tm_t.group(2)) if tm_t else None
        sentence = re.sub(r"\s+", " ", block[:om.end()]).strip()

        # mover / seconder from the flattened sentence
        mover = seconder = None
        mm = re.search(r"Motion(?:\s+made)?\s+by\s+(.+?)\s+seconded\s+by\s+(.+?)\s+to\s",
                       sentence, re.I)
        if mm:
            mover = canon(mm.group(1))
            seconder = canon(mm.group(2))
        else:
            # ANCHOR3 (dropped "Motion by"): "ACTION. <mover> seconded by <seconder> to ..."
            mm3 = re.search(r"ACTION\.\s+(.+?)\s+seconded\s+by\s+(.+?)\s+to\s",
                            sentence, re.I)
            if mm3:
                mover = canon(mm3.group(1))
                seconder = canon(mm3.group(2))

        # motion text = from "to <...>" up to the outcome phrase
        mt = None
        tm = re.search(r"\bto\s+(.+?)\s+Motion\s+(?:carried|failed|did not|was withdrawn|passed)",
                       sentence, re.I)
        if tm:
            mt = tm.group(1)
        else:
            # fall back: strip leading "(ACTION.) Motion by ... to"
            mt = re.sub(r"^.*?\bseconded\s+by\s+.+?\s+to\s+", "", sentence, flags=re.I)
            mt = re.split(r"\bMotion\s+(?:carried|failed|did not|was withdrawn|passed)",
                          mt, flags=re.I)[0]
        mt = re.sub(r"\s+", " ", mt).strip().rstrip(". ")
        mt = mt[:600] if mt else sentence[:600]

        # named roll-call block follows the outcome phrase
        region = block[om.end():]
        votes, unresolved = parse_name_block(region)
        aye, nay = votes["Aye"], votes["Nay"]
        abstain, absent = votes["Abstain"], votes["Absent"]
        nvotes = len(aye) + len(nay) + len(abstain)

        names_recorded = nvotes > 0  # at least one Aye/Nay/Abstain recorded by name
        if names_recorded:
            ab = len(abstain)
            result = f"{len(aye)}-{len(nay)}" + (f"-{ab}abs" if ab else "") + f" {outcome}"
        else:
            # no per-member block -> tally-only / prose.  Capture explicit dissent
            # names if the clerk wrote "<names> voted nay" (no aye fabrication).
            inline_nay = parse_inline_dissent(sentence)
            if inline_nay:
                nay = inline_nay
            if tally_a is not None:
                result = f"{tally_a}-{tally_b} {outcome} (no names)"
            elif re.search(r"unanimous", descriptor, re.I):
                result = "Carried unanimously (no names)"
            elif "lack of a second" in descriptor.lower():
                result = "Failed (no second)"
            elif not carried:
                result = "Failed (no names)"
            else:
                result = "Carried (no names)"

        motions.append({
            "body": default_body,
            "motion": mt,
            "motion_type": motion_type(mt, context),
            "result": result,
            "mover": mover,
            "seconder": seconder,
            "aye": aye, "nay": nay, "abstain": abstain, "absent": absent,
            "recuse": [],
            "names_recorded": names_recorded,
            "tally_text": (f"{tally_a}-{tally_b}" if tally_a is not None else ""),
            "unresolved_names": unresolved,
        })

    for i, mo in enumerate(motions, 1):
        mo["motion_no"] = i
    return motions


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def body_from_slug(slug):
    if "redevelopment-agency" in slug:
        return "RDA"
    return "Council"


def load_index():
    with open(INDEX, newline="") as f:
        return list(csv.DictReader(f))


def json_path_for(rel):
    jrel = rel.replace("meeting_minutes/minutes/", "", 1)
    return (VOTES_DIR / jrel).with_suffix(".json")


def main(rebuild_only=False):
    rows = load_index()
    processed = 0
    for r in rows:
        path = REPO / r["path"]
        if not path.exists():
            continue
        year = int(r["year"])
        slug = r["slug"]
        default_body = body_from_slug(slug)
        jpath = json_path_for(r["path"])
        if rebuild_only and jpath.exists():
            processed += 1
            continue
        text = path.read_text(errors="replace")
        motions = find_motions(text, year, default_body)
        jpath.parent.mkdir(parents=True, exist_ok=True)
        obj = {
            "date": r["date"], "year": year, "title": r["title"],
            "slug": slug, "body_default": default_body, "source": r["path"],
            "votes": motions,
        }
        jpath.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
        processed += 1
    rebuild_csv(rows)
    return processed


def rebuild_csv(rows):
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    out = []
    for r in rows:
        jpath = json_path_for(r["path"])
        if not jpath.exists():
            continue
        obj = json.loads(jpath.read_text())
        for mo in obj["votes"]:
            base = [obj["date"], obj["year"], obj["title"], mo["body"], mo["motion_no"],
                    mo["motion"], mo["motion_type"], mo["result"],
                    mo.get("mover") or "", mo.get("seconder") or ""]
            members = ([(m, "Aye") for m in mo["aye"]] +
                       [(m, "Nay") for m in mo["nay"]] +
                       [(m, "Abstain") for m in mo["abstain"]] +
                       [(m, "Absent") for m in mo["absent"]] +
                       [(m, "Recuse") for m in mo.get("recuse", [])])
            if members:
                for mem, v in members:
                    out.append(base + [mem, v, obj["source"]])
            else:
                out.append(base + ["", "", obj["source"]])
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        w.writerows(out)
    return len(out)


if __name__ == "__main__":
    n = main(rebuild_only="--rebuild" in sys.argv)
    print(f"processed {n} meetings -> {OUT_CSV}")
