#!/usr/bin/env python3
"""
extract_votes.py — Logan (Utah) Planning Commission vote extractor.

Reads minutes markdown listed in planning_commission/minutes_index.csv, extracts
each recorded PC motion + roll-call vote, writes one JSON per meeting under
planning_commission/votes/<year>/<week-monday>/<date>_planning-commission-meeting.json,
then rebuilds planning_commission/all_votes.csv (long format, one row per
member-vote; body="PlanningCommission", title="Planning Commission" on EVERY row).

LOGAN PC FORMAT (verified)
--------------------------
    MOTION: Commissioner Newman moved to recommend approval to the City Council for a
    zone change as outlined in PC 20-014. Commissioner Croshaw seconded the motion.
    ...(CONDITIONS / FINDINGS)...
    Moved: D. Newman  Seconded: R. Croshaw  Approved: 5-1
    Yea: Croshaw, Dickinson, Lucero, Newman, Ortiz  Nay: Nielson  Abstain:

The "Moved:/Seconded:/Approved:|Denied:|failed:" summary line is the primary anchor
(mover, seconder, numeric tally). The following "Yea:/Nay:/Abstain:" line carries the
per-member roll call (surnames). Procedural votes (minutes approval, adjournment) appear
as inline prose "Commissioner X moved to ... The motion was approved unanimously." with
NO summary line and NO names -> names_recorded=false (never invented).

KEY RULES
---------
* NEVER fabricate. yea/nay/abstain counts are derived from the NAMED Yea:/Nay:/Abstain:
  lists when present (authoritative), NOT from the numeric tally, because the "Denied: a-b"
  tally orientation is inconsistent in the source (sometimes nay-first, sometimes yea-first).
  The numeric tally is kept as `tally_text` and cross-checked in validate_votes.py.
* RECOMMENDATION vs FINAL ACTION encoded in `result`:
    - motion text has "recommend"/"forward" -> recommendation
        "Positive recommendation N:N" / "Negative recommendation N:N"
    - else -> final action
        "N:N Approved (Final Action)" / "N:N Denied (Final Action)"
    - procedural (continue/table/minutes/elect/adjourn/recess/withdraw/agenda)
        "N:N Pass" (or "Pass (unanimous)" when unanimous w/ no tally)
  Direction uses the XOR of (motion proposes approval) and (motion passed), so a FAILED
  "recommend approval" -> Negative recommendation, and a CARRIED "deny" -> Denied/Negative.
  Pass/fail is taken from named counts (yea>nay) when present, else from the outcome word.
* OCR (52/130 files, mostly 2023-2026): names fuzzy/initial-matched to the roster surname
  set; OCR digit/letter confusion in tallies tolerated (O->0, l/I->1). If a roll call is too
  garbled to resolve, the named member is dropped (unresolved) rather than guessed.
"""
import csv, json, re, sys, difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent           # planning_commission/
REPO = ROOT.parent                               # logan_city_council/
MIN_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
OUT_CSV = ROOT / "all_votes.csv"

BODY = "PlanningCommission"
TITLE = "Planning Commission"

# ---------------------------------------------------------------------------
# Roster.  surname(lower) -> canonical display name.  Built from the per-meeting
# "Commissioners Present" headers (see roster.csv).  Variant/OCR spellings folded.
# ---------------------------------------------------------------------------
SURNAME_MAP = {
    "croshaw": "Roylan Croshaw",
    "dickinson": "Regina Dickinson",
    "goodlander": "Sandi Goodlander",
    "lucero": "Jessica Lucero",
    "newman": "Dave Newman",
    "nielson": "Tony Nielson",
    "ortiz": "Eduardo Ortiz",
    "heare": "Ken Heare",
    "guth": "Jordy Guth",
    "lewis": "David Lewis",
    "peterson": "Eldon Peterson",
    "doutre": "Sara Doutre",
    "mcnamara": "Sarah McNamara",
    "duncan": "Jennifer Duncan",
    "maughan": "Craig Maughan",
}
# First-name -> canonical (for OCR cases where only a given name survives, e.g. "Jordy").
FIRST_MAP = {
    "roylan": "Roylan Croshaw", "royland": "Roylan Croshaw",
    "regina": "Regina Dickinson",
    "sandi": "Sandi Goodlander", "sandy": "Sandi Goodlander",
    "jessica": "Jessica Lucero", "jess": "Jessica Lucero",
    "dave": "Dave Newman",
    "tony": "Tony Nielson",
    "eduardo": "Eduardo Ortiz",
    "ken": "Ken Heare",
    "jordy": "Jordy Guth",
    "david": "David Lewis", "daivd": "David Lewis",
    "eldon": "Eldon Peterson",
    "sara": "Sara Doutre",
    "sarah": "Sarah McNamara",
    "jennifer": "Jennifer Duncan",
    "craig": "Craig Maughan",
}
SURNAMES = list(SURNAME_MAP.keys())

ROLE_RE = re.compile(
    r"\b(commissioners?|commissioner’s|vice\s*chair|acting\s*chair|chairman|chairwoman|"
    r"chairperson|chair|mayor|staff|councilmembers?|council)\b", re.I)


def canon(token):
    """Map a name fragment to a roster display name, or None if unresolvable."""
    if not token:
        return None
    t = ROLE_RE.sub(" ", token)
    t = re.sub(r"[^A-Za-z.\- ]", " ", t)        # drop stray OCR chars |, =, digits
    t = re.sub(r"\s+", " ", t).strip().strip(".-")
    if not t:
        return None
    words = [w.strip(".-").lower() for w in t.split() if w.strip(".-")]
    if not words:
        return None
    # direct surname (last word), then first word, then any word
    for w in [words[-1]] + words:
        if len(w) <= 1:
            continue
        if w in SURNAME_MAP:
            return SURNAME_MAP[w]
        if w in FIRST_MAP:
            return FIRST_MAP[w]
    # fuzzy surname match (OCR: crowshaw->croshaw, petersen->peterson, here->heare)
    for w in [words[-1]] + words:
        if len(w) < 3:
            continue
        m = difflib.get_close_matches(w, SURNAMES, n=1, cutoff=0.8)
        if m:
            return SURNAME_MAP[m[0]]
    return None


# ---------------------------------------------------------------------------
# Footer / noise stripping (kept light; the Moved:/Yea: pairs are single lines)
# ---------------------------------------------------------------------------
FOOTER_PATTERNS = [
    re.compile(r"^\s*\d+\s*\|\s*Page\s*$", re.I),
    re.compile(r"^\s*Page\s*\d*\s*$", re.I),
    re.compile(r"^\s*www\.loganutah\.org\s*$", re.I),
    re.compile(r"^\s*Logan City Council Chambers", re.I),
]


def strip_footers(text):
    return "\n".join(ln for ln in text.splitlines()
                     if not any(p.match(ln) for p in FOOTER_PATTERNS))


# ---------------------------------------------------------------------------
# Motion typing (reuse council taxonomy, PC-weighted)
# ---------------------------------------------------------------------------
def motion_type(text, context=""):
    t = (context + " " + text).upper()
    mt = text.upper()
    if re.search(r"\bADJOURN", mt):
        return "Procedural/Administrative"
    if re.search(r"\bRECESS|RECONVENE|\bTABLE\b|CONTINUE|POSTPONE|CANCEL|"
                 r"AMEND.*AGENDA|APPROVE.*AGENDA", mt):
        return "Procedural/Administrative"
    if re.search(r"\bMINUTES\b", mt) and "RESOLUTION" not in mt and "ORDINANCE" not in mt:
        return "Procedural/Administrative"
    if re.search(r"APPOINT|REAPPOINT|NOMINATE|ELECT\b.*(CHAIR|VICE)|"
                 r"(CHAIR|VICE\s*CHAIR).*(ELECT|NOMINAT)", t):
        return "Appointment"
    if re.search(r"REZON|ZONE CHANGE|ZONING MAP|RECLASSIF|STREET VACATION|VACAT|ANNEX|"
                 r"CONDITIONAL USE|\bCUP\b|\bPLAT\b|SUBDIVI|GENERAL PLAN|"
                 r"LAND (USE|DEVELOPMENT) CODE|\bLDC\b|OVERLAY|DESIGN REVIEW|"
                 r"PLANNED (UNIT |)DEVELOPMENT|\bPUD\b|SITE PLAN|LOT LINE|"
                 r"PRELIMINARY|FINAL PLAT|VARIANCE|SIGN\b", t):
        return "Land-Use/Zoning"
    if "ORDINANCE" in mt:
        return "Ordinance"
    if "RESOLUTION" in mt:
        return "Resolution"
    return "Other"


# ---------------------------------------------------------------------------
# Anchors / parsers
# ---------------------------------------------------------------------------
MOVED_RE = re.compile(
    r"\bMoved\s*:\s*(?P<mover>.+?)\s+Second(?:ed)?\s*:\s*(?P<sec>.+?)\s+"
    r"(?:Motion\s+for\s+\w+\s+)?(?P<outcome>Approved|Denied|Fail\w*|Continu\w*|Tabl\w*|"
    r"Withdraw\w*|Pass\w*)\s*:?\s*(?P<a>[0-9OolI]+)\s*[-–—]\s*(?P<b>[0-9OolI]+)",
    re.I)

ROLL_RE = re.compile(
    r"\bYe[as]\s*:(?P<yea>.*?)\bNa[ys]\s*:(?P<nay>.*?)(?:\bAbstain\w*\s*:(?P<abs>.*?))?$",
    re.I)

MOTION_HDR_RE = re.compile(r"\bMOTION\s*:", re.I)
MOVED_VERB = r"(?:moved\s+to|made\s+a\s+motion\s+to)"
PROSE_MOVED_RE = re.compile(r"Commissioner\s+\w+.{0,80}?\b" + MOVED_VERB + r"\b", re.I)


def ocr_int(s):
    s = s.translate(str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "|": "1"}))
    try:
        return int(s)
    except ValueError:
        return None


def split_names(seg):
    """Split a Yea:/Nay:/Abstain: segment into canonical names. Handles OCR cases
    where the comma is dropped and two surnames are space-merged ('Lewis Peterson')
    by scanning every whole word against the roster before falling back to fuzzy."""
    out = []
    if not seg:
        return out
    for part in re.split(r"[,/&]| and ", seg):
        matched = []
        for w in re.split(r"\s+", part.strip()):
            wl = re.sub(r"[^A-Za-z]", "", w).lower()
            if len(wl) < 2:
                continue
            if wl in SURNAME_MAP:
                matched.append(SURNAME_MAP[wl])
            elif wl in FIRST_MAP:
                matched.append(FIRST_MAP[wl])
        if not matched:                     # no exact whole-word hit -> fuzzy on whole part
            nm = canon(part)
            if nm:
                matched.append(nm)
        for nm in matched:
            if nm not in out:
                out.append(nm)
    return out


def extract_motion_text(lines, idx):
    """Walk backward from the Moved: line (lines[idx]) to the nearest MOTION: header
    (or 'Commissioner X moved to' prose); return (motion_text, used_header)."""
    start = None
    for j in range(idx - 1, -1, -1):
        if j != idx and MOVED_RE.search(lines[j]):
            break          # crossed into the previous motion's block
        if MOTION_HDR_RE.search(lines[j]):
            start = j
            break
    used = start is not None
    if start is None:
        for j in range(idx - 1, max(-1, idx - 40), -1):
            if MOVED_RE.search(lines[j]):
                break
            if PROSE_MOVED_RE.search(lines[j]):
                start = j
                break
    if start is None:
        return "", False
    buf = []
    for k in range(start, idx):
        s = lines[k].strip()
        if not s:
            if buf:
                break
            continue
        if re.match(r"^(CONDITIONS|FINDINGS|STAFF|PROPONENT|PUBLIC|COMMISSION)\b", s, re.I):
            break
        buf.append(s)
        if re.search(r"seconded the motion|second(ed)? the motion|"
                     r"motion (was|carried|failed|seconded)", s, re.I):
            break
    txt = re.sub(r"\s+", " ", " ".join(buf)).strip()
    txt = re.sub(r"^MOTION\s*:\s*", "", txt, flags=re.I)
    return txt[:600], used


def classify(motion, yea_n, nay_n, outcome, names_recorded):
    """Return (result_string, motion_kind)."""
    m = motion.lower()
    procedural = bool(re.search(
        r"\bminutes\b|continue|continuance|\btable\b|postpone|adjourn|recess|"
        r"withdraw|amend the agenda|approve the agenda|elect|nominat|"
        r"chair|vice[ -]?chair", m))
    is_rec = bool(re.search(r"recommend|forward", m))
    proposes_denial = bool(re.search(r"\bden(y|ial|ied)\b", m))
    proposes_approval = bool(re.search(r"approv|grant", m)) and not proposes_denial

    ow = (outcome or "").lower()
    if names_recorded:
        passed = yea_n > nay_n
    else:
        passed = ow.startswith("approv") or ow.startswith("pass") or ow.startswith("continu") or ow.startswith("tabl")

    if names_recorded:
        tally = f"{yea_n}:{nay_n}"
    else:
        tally = None

    if procedural and not is_rec:
        if tally:
            return f"{tally} Pass" if passed else f"{tally} Fail", "procedural"
        return ("Pass (unanimous)" if passed else "Fail"), "procedural"

    # net positive disposition for the applicant
    if proposes_denial:
        net_positive = not passed
    elif proposes_approval:
        net_positive = passed
    else:
        net_positive = passed  # default: a carried motion is "positive"

    tally = tally or (outcome and "n/a") or "n/a"
    if is_rec:
        dirn = "Positive" if net_positive else "Negative"
        return f"{dirn} recommendation {tally}", "recommendation"
    # final action
    disp = "Approved" if net_positive else "Denied"
    return f"{tally} {disp} (Final Action)", "final_action"


def find_motions(text):
    clean = strip_footers(text)
    lines = clean.split("\n")
    motions = []
    used_moved_idx = set()

    for i, ln in enumerate(lines):
        m = MOVED_RE.search(ln)
        if not m:
            continue
        used_moved_idx.add(i)
        mover = canon(m.group("mover"))
        seconder = canon(m.group("sec"))
        outcome = m.group("outcome")
        ta, tb = ocr_int(m.group("a")), ocr_int(m.group("b"))
        tally_text = f"{ta}-{tb}" if ta is not None and tb is not None else ""

        # roll call on the next non-blank line(s)
        yea = nay = abstain = []
        for k in range(i + 1, min(i + 4, len(lines))):
            rm = ROLL_RE.search(lines[k])
            if rm:
                yea = split_names(rm.group("yea"))
                nay = split_names(rm.group("nay"))
                abstain = split_names(rm.group("abs"))
                break
            if lines[k].strip() and not re.match(r"^\s*Ye", lines[k], re.I):
                # only look just past the moved line; stop at substantive prose
                if k > i + 1:
                    break
        names_recorded = bool(yea or nay or abstain)
        yea_n, nay_n, ab_n = len(yea), len(nay), len(abstain)

        motion_text, _ = extract_motion_text(lines, i)
        if not motion_text:
            motion_text = re.sub(r"\s+", " ", ln).strip()[:300]

        result, kind = classify(motion_text, yea_n, nay_n, outcome, names_recorded)

        motions.append({
            "body": BODY,
            "motion": motion_text,
            "motion_type": motion_type(motion_text),
            "result": result,
            "kind": kind,
            "mover": mover,
            "seconder": seconder,
            "aye": yea, "nay": nay, "abstain": abstain,
            "absent": [], "recuse": [],
            "names_recorded": names_recorded,
            "tally_text": tally_text,
            "outcome_word": outcome,
        })

    # --- procedural prose motions (minutes approval, adjournment) with NO summary line
    for i, ln in enumerate(lines):
        if i in used_moved_idx:
            continue
        if not re.search(r"\b" + MOVED_VERB + r"\b", ln, re.I):
            continue
        # skip if a structured Moved: line is within +/-2 (already captured)
        if any(j in used_moved_idx for j in range(max(0, i - 1), min(len(lines), i + 6))):
            continue
        window = " ".join(lines[i:i + 6])
        window = re.sub(r"\s+", " ", window)
        om = re.search(r"\b(approved unanimously|unanimous|motion (?:was )?"
                       r"(?:approved|carried|passed)|motion (?:was )?(?:denied|failed))\b",
                       window, re.I)
        if not om:
            continue
        # only keep clearly-procedural prose motions (avoid duplicating item motions)
        if not re.search(r"\bminutes\b|adjourn|approve the agenda|amend the agenda|"
                         r"elect|nominat", window, re.I):
            continue
        failed = bool(re.search(r"den(y|ied)|fail", om.group(0), re.I))
        mm = re.search(r"Commissioner\s+([A-Za-z.\-]+)\s+" + MOVED_VERB + r"\s+(.+?)"
                       r"(?:\.|Motion seconded|seconded the motion|The motion)",
                       window, re.I)
        mover = canon(mm.group(1)) if mm else None
        mtext = re.sub(r"\s+", " ", (mm.group(2) if mm else window)).strip()[:300]
        sm = re.search(r"seconded by Commissioner\s+([A-Za-z.\-]+)|"
                       r"Commissioner\s+([A-Za-z.\-]+)\s+seconded", window, re.I)
        seconder = canon(sm.group(1) or sm.group(2)) if sm else None
        result = "Pass (unanimous)" if not failed else "Fail"
        motions.append({
            "body": BODY,
            "motion": mtext,
            "motion_type": motion_type(mtext),
            "result": result,
            "kind": "procedural",
            "mover": mover, "seconder": seconder,
            "aye": [], "nay": [], "abstain": [], "absent": [], "recuse": [],
            "names_recorded": False,
            "tally_text": "",
            "outcome_word": "",
        })

    for n, mo in enumerate(motions, 1):
        mo["motion_no"] = n
    return motions


# ---------------------------------------------------------------------------
# Attendance (for roster.csv)
# ---------------------------------------------------------------------------
PRESENT_RE = re.compile(r"Commissioners?\s+Present\s*:", re.I)
STOP_RE = re.compile(r"\b(Staff|Excused|Others\b|Absent|Minutes|Public Hearing|"
                     r"Council liaison)\b", re.I)


def parse_present(text):
    lines = strip_footers(text).split("\n")
    present = []
    for i, ln in enumerate(lines):
        if PRESENT_RE.search(ln):
            buf = ln.split(":", 1)[1]
            j = i + 1
            while j < len(lines) and lines[j].strip() and "," in lines[j] \
                    and not STOP_RE.search(lines[j]) and len(lines[j]) < 120:
                buf += " " + lines[j]
                j += 1
            for part in re.split(r"[,/]| and ", buf):
                nm = canon(part)
                if nm and nm not in present:
                    present.append(nm)
            break
    return present


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------
def load_index():
    with open(INDEX, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in list(r):
            if r[k] is not None:
                r[k] = r[k].replace("\r", "").strip()
    return rows


def json_path_for(rel):
    jrel = rel.replace("planning_commission/minutes/", "", 1)
    return (VOTES_DIR / jrel).with_suffix(".json")


def main(force=False):
    rows = load_index()
    processed = 0
    for r in rows:
        path = REPO / r["path"]
        if not path.exists():
            continue
        jpath = json_path_for(r["path"])
        if jpath.exists() and not force:
            processed += 1
            continue
        text = path.read_text(errors="replace").replace("\r", "")
        motions = find_motions(text)
        present = parse_present(text)
        jpath.parent.mkdir(parents=True, exist_ok=True)
        obj = {
            "date": r["date"], "year": int(r["year"]), "title": TITLE,
            "body": BODY, "slug": r["slug"], "format": r.get("format", ""),
            "source": r["path"], "present": present, "votes": motions,
        }
        jpath.write_text(json.dumps(obj, indent=1, ensure_ascii=False))
        processed += 1
    rebuild_csv(rows)
    build_roster(rows)
    return processed


def build_roster(rows):
    """commissioner, first_seen, last_seen, n_meetings — from per-meeting attendance
    (present headers), unioned with anyone who moved/seconded/voted that meeting."""
    seen = {}  # name -> {dates:set}
    for r in rows:
        jpath = json_path_for(r["path"])
        if not jpath.exists():
            continue
        obj = json.loads(jpath.read_text())
        date = obj["date"]
        people = set(obj.get("present", []))
        for mo in obj["votes"]:
            for k in ("mover", "seconder"):
                if mo.get(k):
                    people.add(mo[k])
            for k in ("aye", "nay", "abstain", "absent", "recuse"):
                people.update(mo.get(k, []))
        for p in people:
            seen.setdefault(p, set()).add(date)
    out = []
    for name, dates in seen.items():
        ds = sorted(dates)
        out.append((name, ds[0], ds[-1], len(ds)))
    out.sort(key=lambda x: (x[1], x[0]))
    with open(ROOT / "roster.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["commissioner", "first_seen", "last_seen", "n_meetings"])
        w.writerows(out)
    return len(out)


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
            base = [obj["date"], obj["year"], TITLE, mo["body"], mo["motion_no"],
                    mo["motion"], mo["motion_type"], mo["result"],
                    mo.get("mover") or "", mo.get("seconder") or ""]
            members = ([(m, "Aye") for m in mo["aye"]] +
                       [(m, "Nay") for m in mo["nay"]] +
                       [(m, "Abstain") for m in mo["abstain"]] +
                       [(m, "Absent") for m in mo.get("absent", [])] +
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
    n = main(force="--force" in sys.argv)
    print(f"processed {n} meetings -> {OUT_CSV}")
