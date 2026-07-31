#!/usr/bin/env python3
"""
Taylorsville City Council vote extractor  (PURE deterministic — no LLM, no network).

Reads the council-meeting markdown under meeting_minutes/minutes/<year>/<week>/, parses
every recorded motion, tags the governing `body` (Council default; RDA for the separate
Redevelopment Agency Board meeting docs), normalizes member names, and emits:
  - one JSON per meeting under meeting_minutes/votes/<year>/<week>/<slug>.json  (resumable)
  - meeting_minutes/all_votes.csv   (13-col long format, one row per member-vote, w/ body)

Taylorsville's vote grammar — THREE named forms + a narrative tally-only form:
  * MOTION anchor: "MOTION: Councilmember X moved to <action>. The motion was seconded by
    Councilmember Y."   (RDA docs: "Board Member X MOVED ... Board Member Y SECONDED.")
  * FORM A — TABULAR per-member roll call (the modern form; unanimous AND contested):
        Council Member Burgess     Yes
        Chair Harker               Yes
        Council Member Cochran     No
        The motion passed 4-1
    -> one row per named member; names_recorded=true.
  * FORM B — INLINE roll call (the 2020-2021 form, and all RDA docs):
        "...called for a roll call vote. The vote was as follows: Burgess-yes,
         Armstrong-yes, Harker-yes, Christopherson-yes, and Cochran-yes. All City
         Council members voted in favor and the motion passed unanimously."
    -> parse each "Surname-yes|no" pair; names_recorded=true.
  * FORM C — NARRATIVE tally-only (no per-member names):
        "...seconded by Council Member Knudsen and passed unanimously." /
        "The motion passed 5-0"  (no member block)   -> names_recorded=false, tally-only.

MAYOR: Mayor Kristie Overson PRESIDES and gives executive updates only — she NEVER
moves/seconds/votes. The presiding "Chair" is ONE OF THE 5 COUNCIL MEMBERS (the chair
rotates: "Chair Barbieri" = Barbieri, "Chair Harker" = Harker, ...), mapped to that
councilmember — never to the Mayor. MAX ordinary tally = 5. If the Mayor is ever recorded
casting a vote it is captured FAITHFULLY and flagged `mayor_voted:true` (a real event that
validate_votes.py surfaces) — never invented, never assumed.

Roster (canon; only these surnames map to a vote):
  D1 Ernest Burgess, D2 Curt Cochran, D3 Anna Barbieri, D4 Meredith Harker,
  D5 Bob Knudsen (2022+).  Former members who really voted in 2020-2021:
  Dan Armstrong (former D5, 2020-2021) and Brad Christopherson (former D3, 2020).
Light difflib fuzzy-match repairs OCR-garbled surnames ("Barbier/", "Merdith") to the
roster; an unrecoverable name is left BLANK, never guessed.
"""
import csv
import difflib
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
    "burgess": "Ernest Burgess",
    "cochran": "Curt Cochran",
    "barbieri": "Anna Barbieri",
    "harker": "Meredith Harker",
    "knudsen": "Bob Knudsen",
    "armstrong": "Dan Armstrong",
    "christopherson": "Brad Christopherson",
}
ROSTER_KEYS = list(ROSTER_MAP.keys())
MAYOR_NAME = "Kristie Overson"
MAYOR_TOKENS = {"overson"}

# First-name index for the SAFE full-name gate (memory: prefer-full-name-vote-resolution):
# a surname fold is rejected ONLY when the token immediately preceding the surname names a
# DIFFERENT roster member. LATENT hardening — all seven surnames AND first names are
# currently unique, so the gate never fires (proven by byte-identical all_votes.csv); it
# exists to guard a FUTURE second same-surname member (the Provo Deborah/Lisa Jensen
# failure mode), never to alter today's output.
_FIRST_TO_FULL = {full.split()[0].lower(): full for full in ROSTER_MAP.values()}


def _reject_surname_fold(pfx, cand):
    """True iff the preceding token `pfx` names a DIFFERENT roster member (block the fold).
    Folds through nicknames (pfx not a known first name) and the member's own first name."""
    if not pfx:
        return False
    pfx = re.sub(r"[^a-z]", "", pfx.lower())
    if len(pfx) < 2:
        return False
    cand_first = cand.split()[0].lower()
    if pfx == cand_first:                 # this member's own first name -> fold
        return False
    if cand_first.startswith(pfx):        # a nickname/prefix of the own first name -> fold
        return False
    mapped = _FIRST_TO_FULL.get(pfx)
    return mapped is not None and mapped != cand   # a known OTHER member -> reject the fold

# role prefixes the minutes use for a councilmember (incl. board / chair / pro-tem forms).
# CASE-INSENSITIVE role word: the corpus mixes "Councilmember" (lower m, dominant 2020-21)
# and "Council Member" (capital M). Wrapped in (?i:...) at each use so ONLY the role token
# is case-folded — vote tokens (Yes/No) stay case-sensitive to avoid matching lowercase prose.
ROLE_PREFIX = (r"(?i:Council\s*Members?|Board\s*Members?|Board\s*Chair|Council\s*Chair|"
               r"Vice[\s-]*Chair|Chair|Mayor\s+Pro\s+Tem(?:pore)?)")


def _fuzzy_surname(tok):
    """Return a roster key for a (possibly OCR-garbled) surname token, else None."""
    t = re.sub(r"[^a-z]", "", tok.lower())
    if len(t) < 4:
        return None
    if t in ROSTER_MAP:
        return t
    # prefix repair for a dropped trailing char ("barbier" -> "barbieri")
    for k in ROSTER_KEYS:
        if k.startswith(t) or t.startswith(k):
            if abs(len(k) - len(t)) <= 2:
                return k
    m = difflib.get_close_matches(t, ROSTER_KEYS, n=1, cutoff=0.82)
    return m[0] if m else None


def find_member(phrase):
    """Scan a name phrase for a roster surname. Return (canonical_name, is_mayor).

    Council surnames win over the mayor token so a "Chair <Surname>" always resolves to
    the councilmember. Returns (None, False) when no recognizable member is present."""
    toks = re.findall(r"[A-Za-z/'\.]+", phrase)
    for i, t in enumerate(toks):
        k = _fuzzy_surname(t)
        if k:
            cand = ROSTER_MAP[k]
            if _reject_surname_fold(toks[i - 1] if i > 0 else None, cand):
                continue
            return cand, False
    for t in toks:
        if re.sub(r"[^a-z]", "", t.lower()) in MAYOR_TOKENS:
            return MAYOR_NAME, True
    return None, False


# ---------------------------------------------------------------------------
# Motion-type taxonomy (fixed 12 categories) — land-use checked FIRST.
# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|"
                 r"development agreement|floating zone|overlay|site plan|"
                 r"future land use|planned development|redevelopment|"
                 r"project area|station area plan|\bcda\b", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend(?:ing)? the (?:fiscal|fy)?\s*.*budget|"
                 r"tentative budget|final budget|adopt.*budget|budget for|"
                 r"appropriat", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|liaison|ratify the (?:results|canvass)|"
                 r"board chair|vice chair", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award the contract|"
                 r"professional services|franchise agreement|agreement with|"
                 r"services agreement|enter into an agreement|task order", t):
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
                 r"approve the (?:consent|agenda|minutes|order)|approve the .*minutes|"
                 r"minutes of|minutes for|minutes from|\btable\b|continue|postpone|"
                 r"amend the agenda|approve the meeting minutes", t):
        return "Procedural/Administrative"
    return "Other"


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------
# Motion mover:  "(role) <Name> moved|MOVED to|that ..."
MOVE_RE = re.compile(
    ROLE_PREFIX + r"\s+([A-Z][A-Za-z.'\-/]+(?:\s+[A-Z][A-Za-z.'\-/]+){0,2}?)\s+"
    r"(?:moved|MOVED)\s+(?:to|that)\b")
# Seconder — two shapes:  "seconded by (role) <Name>"  |  "(role) <Name> SECONDED"
SECOND_BY_RE = re.compile(
    r"second(?:ed)?\s+by\s+(?:" + ROLE_PREFIX + r")?\.?\s*"
    r"([A-Z][A-Za-z.'\-/]+(?:\s+[A-Z][A-Za-z.'\-/]+){0,2}?)\b", re.I)
SECOND_VERB_RE = re.compile(
    ROLE_PREFIX + r"\s+([A-Z][A-Za-z.'\-/]+(?:\s+[A-Z][A-Za-z.'\-/]+){0,2}?)\s+"
    r"(?:SECONDED|seconded the motion)\b")

# FORM A — tabular per-member vote line (anchored, whole-line; tolerates a leading OCR
# gutter line-number like "23   Councilmember Burgess   Yes")
TAB_RE = re.compile(
    r"^\s*(?:\d{1,3}\s+)?(?i:(Council\s*Members?|Board\s*Members?|Board\s*Chair|"
    r"Council\s*Chair|Vice[\s-]*Chair|Chair|Mayor\s+Pro\s+Tem(?:pore)?|Mayor))\s+"
    r"([A-Z][A-Za-z.'\-/]+(?:\s+[A-Z][A-Za-z.'\-/]+){0,2}?)\s+"
    r"(?:[a-z][.a-z']{0,2}\s+)?"  # tolerate a short OCR artifact e.g. "Cochran i. Yes"
    r"(Yes|No|Aye|Nay|Abstain(?:ed)?|Absent|Excused|Recuse[d]?)"
    r"(?:\s*\([^)]*\))?\s*\.?\s*$")  # tolerate a trailing note e.g. "Yes (via text)"

# FORM B — inline roll call:  "Surname-yes,"  /  "Barbier/-yes"
INLINE_PAIR_RE = re.compile(
    r"([A-Za-z][A-Za-z/'\-]{2,})\s*[-–—]\s*"
    r"(yes|no|aye|nay|abstain(?:ed)?|absent|recuse[d]?)\b", re.I)
INLINE_HEADER_RE = re.compile(r"vote was as follows", re.I)

VOTE_MAP = {
    "yes": "aye", "aye": "aye",
    "no": "nay", "nay": "nay",
    "abstain": "abstain", "abstained": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}

# Result / tally
TALLY_RE = re.compile(
    r"(?:motion\s+(?:passed|failed|carried|denied)|passed|failed|carried|denied)\s+"
    r"(\d{1,2})\s*[-–]\s*(\d{1,2})", re.I)
UNANIMOUS_RE = re.compile(r"passed\s+unanimously|carried\s+unanimously|"
                          r"unanimous(?:ly)?\s+in\s+favor|approved\s+unanimously", re.I)
FAIL_RE = re.compile(r"\bfailed\b|\bdenied\b|did not (?:pass|carry)|"
                     r"motion (?:was )?(?:denied|defeated)", re.I)
DEATH_RE = re.compile(r"lack of (?:a )?second|no second|died for lack|"
                      r"failed for (?:a )?lack of (?:a )?second|there was no second", re.I)
# lines merely discussing another body's action — never a council result anchor
NOT_RESULT = re.compile(r"planning commission|recommend", re.I)

# ---------------------------------------------------------------------------
# Footer / running-header stripping (flatten roll-call blocks across page breaks)
# ---------------------------------------------------------------------------
FOOTER_RE = re.compile(
    r"^\s*(?:"
    r"Taylorsville City Council Minutes|"
    r"Redevelopment Agency of Taylorsville City(?: Minutes)?|"
    r"City of Taylorsville|"
    r"CITY COUNCIL MEETING|BOARD MEETING MINUTES|"
    r"Click\s?for\s?Audio.*|"
    r"Page\s+\d{1,3}"
    r")\s*$", re.I)
FOOTER_DATE_RE = re.compile(
    r"^\s*(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+\d{4}\s*$", re.I)
PAGENUM_RE = re.compile(r"^\s*\d{1,3}\s*$")


def load_lines(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if FOOTER_RE.match(s) or FOOTER_DATE_RE.match(s) or PAGENUM_RE.match(s):
            continue
        out.append(ln.rstrip())
    return out


# ---------------------------------------------------------------------------
# Body: RDA for the separate Redevelopment-Agency docs, else Council.
# (No Taylorsville council file records substantive RDA motions inline — the in-meeting
#  RDA business is either held in a separate RDA doc or recessed with no recorded motion.)
# ---------------------------------------------------------------------------
def meeting_body(title, slug):
    s = (title + " " + slug).lower()
    if re.search(r"redevelopment|rda", s):
        return "RDA"
    if re.search(r"municipal building authority|\bmba\b", s):
        return "MBA"
    return "Council"


# ---------------------------------------------------------------------------
# Parse one meeting
# ---------------------------------------------------------------------------
def parse_meeting(lines, body):
    n = len(lines)
    # motion-start line indices (where a "<role> <name> moved/MOVED to|that" begins)
    starts = [i for i, ln in enumerate(lines) if MOVE_RE.search(ln)]
    votes = []
    for mi, s in enumerate(starts):
        end = starts[mi + 1] if mi + 1 < len(starts) else n
        block = lines[s:end]
        joined = re.sub(r"\s+", " ", " ".join(block)).strip()

        mv = MOVE_RE.search(joined)
        mover, _ = find_member(mv.group(0)) if mv else (None, False)

        # seconder
        seconder = None
        sm = SECOND_BY_RE.search(joined) or SECOND_VERB_RE.search(joined)
        if sm:
            seconder, _ = find_member(sm.group(0))

        # motion text: object of the motion, from after the verb 'moved' up to the seconder
        # clause / vote block. Split points terminate the object.
        SPLIT = (r"The motion was seconded|SECONDED the motion|\bseconded by\b|\bSECONDED\b|"
                 r"The vote was as follows|called for a roll call|"
                 r"The motion (?:passed|failed|carried)|declared (?:it|the meeting)")
        mtext = joined[mv.end():] if mv else joined
        parts = re.split(SPLIT, mtext, flags=re.I)
        obj = parts[0].strip(" .;,:")
        if len(re.sub(r"[^A-Za-z]", "", obj)) < 3 and len(parts) > 1:
            # OCR reordered the object AFTER the seconder boilerplate ("moved to  The motion
            # was seconded by  adjourn.") — recover it from the residual (still source text).
            tail = " ".join(parts[1:])
            tail = re.split(SPLIT + r"|Council Member|Councilmember|Board Member",
                            tail, flags=re.I)[0]
            if len(re.sub(r"[^A-Za-z]", "", tail)) >= 3:
                obj = tail.strip(" .;,:")
        motion_text = re.sub(r"\s+", " ", ("moved " + obj)).strip(" .;,")

        # ---- locate the result TERMINATOR line (first tally / unanimous / death) so the
        # vote region can't bleed into the NEXT agenda item's discussion (the block runs to
        # the next 'moved', which often includes the following item). ----
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        mayor_voted, mayor = False, None
        names_recorded = False
        printed_tally = None
        result_str = None

        term_idx = None          # index within `block` of the LAST result line (window end)
        term = None              # ("death"|"tally"|"unanimous", ...)
        for j in range(len(block)):
            for span in (1, 2, 3):
                # a result phrase can WRAP across page-broken lines; the window END is the
                # true terminator (so a same-window later tally can't truncate the roll call)
                seg = " ".join(x.strip() for x in block[j:j + span])
                if DEATH_RE.search(seg):
                    term, term_idx = ("death",), j + span - 1
                    break
                tm2 = TALLY_RE.search(seg)
                if tm2 and not NOT_RESULT.search(seg):
                    outcome = "Fail" if (FAIL_RE.search(seg) or
                                         int(tm2.group(2)) > int(tm2.group(1))) else "Pass"
                    term, term_idx = ("tally", int(tm2.group(1)), int(tm2.group(2)),
                                      outcome), j + span - 1
                    break
                if UNANIMOUS_RE.search(seg) and not NOT_RESULT.search(seg):
                    term, term_idx = ("unanimous",), j + span - 1
                    break
            if term_idx is not None:
                break

        # vote region = motion body up to and including the terminator line
        region = block[:(term_idx + 1) if term_idx is not None else len(block)]
        region_join = re.sub(r"\s+", " ", " ".join(region))

        # FORM A: tabular per-member vote lines within the region
        tab = []
        for wl in region:
            tm = TAB_RE.match(wl)
            if not tm:
                continue
            role, namephrase, vlabel = tm.group(1), tm.group(2), tm.group(3).lower()
            is_mayor_role = role.lower().startswith("mayor") and "pro tem" not in role.lower()
            nm, _m = find_member(namephrase)
            vkey = re.sub(r"ed$|d$", "", vlabel) if vlabel not in VOTE_MAP else vlabel
            bkt = VOTE_MAP.get(vlabel, VOTE_MAP.get(vkey, "aye"))
            if is_mayor_role and nm is None:
                nm = MAYOR_NAME
            if nm is None:
                continue
            tab.append((nm, bkt, nm == MAYOR_NAME))

        # FORM B: inline "Surname-yes" roll call (only after a roll-call header)
        inline = []
        if INLINE_HEADER_RE.search(region_join):
            seg = region_join[INLINE_HEADER_RE.search(region_join).end():]
            seg = re.split(r"All (?:City Council|Board) [Mm]embers|"
                           r"The motion (?:passed|failed|carried)", seg)[0]
            for pm in INLINE_PAIR_RE.finditer(seg):
                nm, _m = find_member(pm.group(1))
                if nm is None:
                    continue
                vl = pm.group(2).lower()
                inline.append((nm, VOTE_MAP.get(vl, VOTE_MAP.get(re.sub(r"ed$|d$", "", vl),
                               "aye")), nm == MAYOR_NAME))

        recorded = tab if len(tab) >= 2 else (inline if len(inline) >= 2 else [])
        if recorded:
            seen = set()
            for nm, bkt, is_m in recorded:
                if nm in seen:
                    continue
                seen.add(nm)
                buckets[bkt].append(nm)
                if is_m:
                    mayor_voted, mayor = True, MAYOR_NAME
            names_recorded = True

        # ---- outcome from the terminator ----
        if term and term[0] == "death":
            result_str = "Died (no second)"
        elif term and term[0] == "tally":
            a, b = term[1], term[2]
            printed_tally = (a, b)
            result_str = f"{a}-{b} {term[3]}"
        elif term and term[0] == "unanimous":
            if names_recorded:
                a = len(buckets["aye"])
                result_str = f"{a}-0 Pass" if a else "Unanimous Pass"
            else:
                result_str = "Unanimous Pass"
        elif recorded:
            a, b = len(buckets["aye"]), len(buckets["nay"])
            result_str = f"{a}-{b} {'Fail' if b > a else 'Pass'}"
        else:
            # a motion with no recoverable result (recess/reconvene noted elsewhere, or a
            # parse gap) — record it visibly so validation can surface it, never dropped.
            result_str = ""

        votes.append({
            "body": body,
            "motion": motion_text[:600],
            "motion_type": classify_motion(motion_text),
            "result": result_str,
            "mover": mover,
            "seconder": seconder,
            "aye": buckets["aye"],
            "nay": buckets["nay"],
            "abstain": buckets["abstain"],
            "absent": buckets["absent"],
            "recuse": buckets["recuse"],
            "names_recorded": names_recorded,
            "printed_tally": list(printed_tally) if printed_tally else None,
            "mayor_voted": mayor_voted,
            "mayor": mayor,
        })
    return votes


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

        body = meeting_body(r["title"], slug)
        votes = parse_meeting(load_lines(path), body)
        for k, v in enumerate(votes, start=1):
            v["motion_no"] = k
        payload = {
            "date": r["date"],
            "year": int(year),
            "title": r["title"],
            "source": rel,
            "body": body,
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
