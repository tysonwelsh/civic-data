#!/usr/bin/env python3
"""
Holladay vote extractor  (PURE deterministic — no LLM, no network, resumable).

Body-agnostic: drop the SAME file in meeting_minutes/ (default body=Council; in-session
Redevelopment Agency / Local Building Authority sections re-tagged via a section walk) and
in planning_commission/ (default body=PlanningCommission). Reads this dir's minutes_index.csv,
parses every recorded motion, and emits:
  - one JSON per meeting under votes/<year>/<week>/<slug>.json          (resumable)
  - all_votes.csv   (13-col long format, one row per member-vote, w/ body)

Holladay grammar (recon.md §2/§3; verified across 2020->2026):

  MODERN (2022+) named roll — the Mayor VOTES (council roll tops out at 6):
    "Council Member Gray moved to APPROVE Ordinance 2025-22 ... Council Member Quinn
     seconded the motion. Vote on Motion: Council Member Gray-Yes; Council Member
     Quinn-Yes; ...; Mayor Dahle-Yes. Ordinance 2025-22 was adopted by a unanimous vote."
    PC: "... Vote on Motion: Commissioner Berndt-Aye; ...; Chair Roach-Aye. The motion
     passed unanimously."   (dissent tokens observed: -Nay, -Recuse)

  LEGACY (2020-2021) prose roll:
    "Council Member Gibbons moved to adopt Ordinance 2020-02. Council Member Petersen
     seconded the motion. The Council roll call vote was as follows: Council Members
     Gibbons, Quinn, Fotheringham, Durham, Petersen and Mayor Dahle in favor. Ordinance
     2020-02 was adopted by a unanimous vote."
    Contested legacy: "... Durham and Mayor Dahle in favor with Council Member
     Fotheringham opposed."  -> favor=Aye, opposed=Nay, abstained=Abstain.

  PC 2020-2021 (wayback-promoted 2026-07-16) uses the modern FULL-NAME roll
  ("Vote on motion: Chris Layton-Aye, Ann Mackin-Aye, ..., Chair Marianne Ricks-Nay.");
  two docs print a clerk-typo period after "Vote on motion" (see ROLL_TRIGGER). BOTH
  real Laytons (Chris + Howard) serve together from 2020-08 — the dual-surname roll
  logic keeps printed first names, exactly as in 2022.

  CONSENT / procedural (tally-only, NO per-member names -> names_recorded:false, blank
  member/vote per the cardinal 'honest gaps are data' rule):
    "The motion passed with the unanimous consent of the Council/Commission."
  DIED: "There was no second." / "for lack of a second."

Roster is OBSERVED (never hard-coded): a first pass harvests surnames from high-confidence
patterns (X moved / X seconded / Name-Vote / Mayor X); the legacy comma-list is then
validated against that observed set so narrative capitalized words are never mistaken for
voters. Members are keyed by surname as printed (the source prints surnames only); a small
alias map folds spelling typos (Petersen/Peterson). vote values are NORMALIZED to the
controlled vocabulary (SCHEMA_SPEC §4: Aye|Nay|Abstain|Recuse|Absent|Excused): the source's
printed "Yes"/"No" tokens (2022+ council) map to Aye/Nay, matching the PC's native Aye/Nay
and the legacy prose favor/opposed. Only `result` (and the derived `motion_type` label) are
city-faithful/verbatim — `vote` is the normalized token (see normalize_vote()).
"""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MINUTES_DIR = ROOT / "minutes"
VOTES_DIR = ROOT / "votes"
INDEX = ROOT / "minutes_index.csv"
ALL_VOTES = ROOT / "all_votes.csv"
DEFAULT_BODY = "PlanningCommission" if ROOT.name == "planning_commission" else "Council"

ROLE = (r"(?:Council\s*Members?|Board\s*Members?|Commissioners?|"
        r"Vice[-\s]*Chair(?:man)?|Chair(?:man)?|Mayor)")
VOTE_TOKENS = r"(?:Yes|No|Aye|Nay|Abstain(?:ed)?|Abstention|Recuse[d]?|Absent)"
SURNAME = r"[A-Z][A-Za-z.'’-]+"

SURNAME_ALIASES = {  # observed spelling-variant / OCR folds (verified same person)
    "peterson": "Petersen", "vilchinski": "Vilchinsky", "gibbon": "Gibbons",
    "bank": "Banks",
}
# Roll trigger: the colon form is the corpus norm; two 2020 wayback-recovered PC docs
# (2020-01-21, 2020-02-04) print a clerk-typo period ("Vote on motion. Troy Holbrook-Aye,
# ...") — the period alternative fires ONLY when a Name-Vote token follows within the
# same sentence, so narrative "…vote on the motion." never triggers (0 hits in the
# audited 2022+ corpus; verified 2026-07-16).
ROLL_TRIGGER = (r"Vote on (?:the\s+)?motion\s*"
                r"(?::|\.(?=[^.]{0,120}-\s*(?:Aye|Nay|Yes|No)\b))")

def norm_surname(s):
    s = s.strip().strip(".,;").replace("’", "'")
    return SURNAME_ALIASES.get(s.lower(), s)

def normalize_vote(tok):
    t = tok.lower()
    if t.startswith("abst"):
        return "Abstain"
    if t.startswith("recus"):
        return "Recuse"
    # §4 vote values are a CONTROLLED vocabulary — "Yes"/"No" normalize to Aye/Nay.
    return {"yes": "Aye", "no": "Nay", "aye": "Aye", "nay": "Nay",
            "absent": "Absent"}.get(t, tok)

# ---- footer / whitespace flattening --------------------------------------
FOOTER_RE = re.compile(
    r"(?im)^\s*(?:Holladay\s+City\s+Council.*Minutes.*|"
    r"Holladay\s+(?:City\s+)?Planning\s+Commission.*Minutes.*|"
    r"Page\s+\d+.*|.*\bPage\s+\d+\s+of\s+\d+.*)$")

def flatten(md_body):
    txt = FOOTER_RE.sub(" ", md_body)
    txt = txt.replace("–", "-").replace("—", "-")
    txt = re.sub(r"\s+", " ", txt)
    return txt

# ---- observed roster discovery -------------------------------------------
def discover_roster(text):
    surnames = {}
    for m in re.finditer(rf"({ROLE})\s+({SURNAME})\s+(?:moved|seconded)", text):
        surnames.setdefault(norm_surname(m.group(2)), m.group(1))
    for m in re.finditer(rf"({SURNAME})\s*-\s*{VOTE_TOKENS}\b", text):
        surnames.setdefault(norm_surname(m.group(1)), "")
    for m in re.finditer(rf"Mayor\s+({SURNAME})", text):
        surnames.setdefault(norm_surname(m.group(1)), "Mayor")
    # drop obvious non-name captures
    STOP = {"The", "City", "Council", "Commission", "Members", "Member", "Meeting",
            "Vote", "Motion", "Ordinance", "Resolution", "Agency", "Redevelopment",
            "Local", "Building", "Authority", "Chair", "And"}
    return {s for s in surnames if s not in STOP and len(s) >= 3}

# ---- motion-type classifier (derived; native minutes print no label) -----
def motion_type(motion):
    t = motion.lower()
    if "ordinance" in t:
        return "Ordinance"
    if "resolution" in t:
        return "Resolution"
    if re.search(r"\bplat\b|subdivision|site (development|plan)|conditional use|"
                 r"rezone|zoning map|amend(ing|ment).*(zon|code)|general plan|"
                 r"land use|setback|variance|lot line", t):
        return "Land-Use/Zoning"
    if "budget" in t or "appropriat" in t or "tax" in t:
        return "Budget/Finance"
    if re.search(r"appoint|nominat|mayor pro tem|ratif", t):
        return "Appointment"
    if re.search(r"agreement|contract|interlocal|purchase|lease|bid|award", t):
        return "Contract/Agreement"
    if re.search(r"\brecess\b|reconvene|adjourn|amend the agenda|reorder|approve the "
                 r"agenda|table|continue|closed session|executive session|minutes", t):
        return "Procedural"
    return "Other"

# ---- section-walk body tagging (in-session RDA/LBA in a council doc) ------
def body_at(text_before, default_body):
    if default_body != "Council":
        return default_body
    # last reconvene/convene marker wins
    markers = list(re.finditer(
        r"(?i)(reconvene|convene|recess).{0,40}?"
        r"(Redevelopment Agency|Local Building Authority|Work Meeting|City Council|Council Meeting)",
        text_before))
    if not markers:
        return "Council"
    tgt = markers[-1].group(2).lower()
    if "redevelopment" in tgt:
        return "RDA"
    if "local building" in tgt:
        return "LBA"
    return "Council"

# ---- outcome / result verbatim -------------------------------------------
OUTCOME_RE = re.compile(
    r"((?:Ordinance|Resolution|The motion|The application|The subdivision|The request|"
    r"Motion|Resolutions|Ordinances)[^.]*?\b(?:adopted|approved|passed|failed|carried|"
    r"denied|tabled|continued|died)\b[^.]*\.)", re.I)

def find_result(block, consent, died):
    if died:
        m = re.search(r"([^.]*\b(?:no second|lack of a? ?second|died)\b[^.]*\.)", block, re.I)
        return (m.group(1).strip() if m else "The motion died for lack of a second.")
    if consent:
        m = re.search(r"(The motion passed with the unanimous consent[^.]*\.)", block, re.I)
        return (m.group(1).strip() if m else "Passed with unanimous consent.")
    m = OUTCOME_RE.search(block)
    return m.group(1).strip() if m else ""

# ---- roll parsers ---------------------------------------------------------
def parse_modern_roll(seg, roster):
    """seg = text after 'Vote on Motion:'. Return list[(name, vote)].

    Names are surnames EXCEPT when one roll contains two members sharing a
    surname (Chair Howard Layton + Commissioner Chris Layton, 2022): those rows
    keep the printed first name so two real people are never collapsed into
    duplicate 'Layton' rows (T3.1 Tier-A, 2026-07-12 — the audit's "dedup" framing
    was wrong; they are distinct voters)."""
    raw = []
    for m in re.finditer(rf"(?:{ROLE}\s+)?(?:([A-Z][a-z]+)\s+)?({SURNAME})\s*-\s*({VOTE_TOKENS})\b", seg):
        sn = norm_surname(m.group(2))
        if sn in roster:
            raw.append((m.group(1) or "", sn, normalize_vote(m.group(3))))
    counts = {}
    for _, sn, _ in raw:
        counts[sn] = counts.get(sn, 0) + 1
    out = []
    for first, sn, v in raw:
        out.append((f"{first} {sn}" if (counts[sn] > 1 and first) else sn, v))
    return out

STOP_TOKENS = {"Council", "Members", "Member", "Mayor", "Commissioners", "Commissioner",
               "Chair", "Vice", "The", "And", "City", "Motion", "Ordinance", "Resolution",
               "Holladay", "Pro", "Tem", "Tempore", "Meeting", "Board", "Directors",
               "Director", "Chairman", "Executive", "Staff"}

def legacy_names(clause):
    """Structurally pull voter surnames from a prose clause like
    'Council Members A, B, C and Mayor Dahle' — NO roster dependency (so a member who
    appears ONLY in the prose list is never dropped)."""
    names = []
    # Mayor is written 'Mayor <Surname>' (or 'Mayor <First> <Surname>' -> take last word)
    for m in re.finditer(r"Mayor\s+((?:[A-Z][A-Za-z.'’-]+\s+)?[A-Z][A-Za-z.'’-]+)\b", clause):
        sn = norm_surname(m.group(1).split()[-1])
        if sn not in names:
            names.append(sn)
    # 'Council Member(s) <list>' up to the next role / vote keyword
    for m in re.finditer(r"(?:Council|Board)\s+Members?\s+(.*?)(?=\band\s+Mayor\b|\bwith\b|"
                         r"\bMayor\b|in favor|oppos|abstain|voted|$)", clause, re.I):
        for tok in re.split(r",|\band\b", m.group(1)):
            tok = norm_surname(tok)
            if re.fullmatch(r"[A-Z][A-Za-z.'’-]+", tok) and tok not in STOP_TOKENS \
                    and tok not in names:
                names.append(tok)
    return names

def parse_legacy_roll(seg, roster=None):
    """seg = text after 'roll call vote was as follows:'. Prose favor/opposed/abstain."""
    out = []
    seg = re.split(r"(?<=\.)\s+[A-Z]", seg, maxsplit=1)[0]  # keep only the roll sentence
    low = seg.lower()
    fi = low.find("in favor")
    favor_clause = seg[:fi] if fi >= 0 else seg
    rest = seg[fi:] if fi >= 0 else ""
    favor = legacy_names(favor_clause)
    seen = set(favor)
    for n in favor:
        out.append((n, "Aye"))
    rl = rest.lower()
    oi = rl.find("oppos")
    ai = rl.find("abstain")
    if oi >= 0:
        for n in legacy_names(rest[:oi]):
            if n not in seen:
                seen.add(n); out.append((n, "Nay"))
    if ai >= 0:
        for n in legacy_names(rest[:ai]):
            if n not in seen:
                seen.add(n); out.append((n, "Abstain"))
    return out

# ---- main motion scan -----------------------------------------------------
# mover: role, optional first name, surname, then 'moved'/'made a motion' (allowing a
# stray comma: 'moved, to approve'), then to/that.
MOVER_RE = re.compile(
    rf"({ROLE})\s+(?:[A-Z][A-Za-z.'’-]+\s+)?({SURNAME})\s+"
    rf"(?:moved|made a motion)[\s,]*(?:to|that)\b", re.I)
SECOND_RE = re.compile(rf"({ROLE})\s+(?:[A-Z][A-Za-z.'’-]+\s+)?({SURNAME})\s+seconded", re.I)

def parse_meeting(text, default_body):
    roster = discover_roster(text)
    # per-doc mayor surname(s): whoever the source prints as "Mayor <Name>" in this doc
    # (handles the Dahle->Fotheringham Jan-2026 seam without any hard-coded roster)
    mayors = {norm_surname(m.group(1)) for m in re.finditer(rf"Mayor\s+({SURNAME})", text)}
    mayors &= roster
    starts = [m.start() for m in MOVER_RE.finditer(text)]
    motions = []
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[s:e]
        mv = MOVER_RE.match(block)
        mover = norm_surname(mv.group(2))
        after = block[mv.end():]
        # motion text = up to the seconder phrase / vote marker (cut the whole
        # "<Role> <Name> seconded" so the seconder never leaks into motion text)
        cut = re.search(rf"{ROLE}\s+(?:[A-Z][A-Za-z.'’-]+\s+)?{SURNAME}\s+seconded|"
                        rf"\bseconded\b|{ROLL_TRIGGER}|"
                        r"roll call vote was as follows:|There was no second|"
                        r"unanimous consent", after, re.I)
        motion_txt = (after[:cut.start()] if cut else after).strip().strip(".; ")
        motion_txt = re.sub(r"\s+", " ", motion_txt)
        sec = SECOND_RE.search(block)
        seconder = norm_surname(sec.group(2)) if sec else ""
        body = body_at(text[:s], default_body)
        rows = []
        consent = died = False
        vm = re.search(rf"{ROLL_TRIGGER}(.*)", block, re.I)
        lg = re.search(r"roll call vote was as follows:(.*)", block, re.I)
        if vm:
            # limit roll segment to before the outcome keywords
            seg = vm.group(1)
            oc = OUTCOME_RE.search(seg)
            seg = seg[:oc.start()] if oc else seg[:400]
            rows = parse_modern_roll(seg, roster)
        elif lg:
            rows = parse_legacy_roll(lg.group(1), roster)
        elif re.search(r"unanimous consent", block, re.I):
            consent = True
        elif re.search(r"(no second|lack of a? ?second|died for)", block, re.I):
            # a clerk-formality "There was no second." can precede an explicit
            # "The motion passed unanimously." (chair procedural motions,
            # PC 2025-12-02) — the outcome sentence wins; only a motion with NO
            # subsequent carry sentence truly dies (T3.1(m) 2026-07-12).
            ns = re.search(r"(no second|lack of a? ?second|died for)", block, re.I)
            if not re.search(r"motion (?:passed|carried)", block[ns.end():], re.I):
                died = True
        result = find_result(block, consent, died)
        motions.append({
            "motion_no": len(motions) + 1, "body": body, "mover": mover,
            "seconder": seconder, "motion": motion_txt, "motion_type": motion_type(motion_txt),
            "result": result, "names_recorded": bool(rows),
            "mayor_voted": any(m in mayors for m, _ in rows),
            "votes": [{"member": m, "vote": v, "is_mayor": m in mayors}
                      for m, v in rows],
        })
    return motions

# ---- driver ---------------------------------------------------------------
def read_index():
    with open(INDEX, newline="") as f:
        return list(csv.DictReader(f))

def main():
    rows = read_index()
    all_rows = []
    n_meetings = n_motions = 0
    for r in rows:
        md = ROOT / r["path"]
        if not md.exists():
            continue
        raw = md.read_text(encoding="utf-8", errors="replace")
        body_txt = raw.split("---", 1)[1] if "---" in raw else raw
        text = flatten(body_txt)
        # provenance: doc-level source channel from minutes_index.csv. 'minutes' =
        # audited PMN spine; 'wayback_minutes' = 2020/2021 PC docs recovered from the
        # former city WordPress site via the Wayback Machine and promoted 2026-07-16
        # (promote_backfill_minutes.py). Filter provenance='minutes' for a clean
        # PMN-audited-only cut, exactly like the pmn_* convention elsewhere.
        provenance = {"pmn": "minutes",
                      "wayback": "wayback_minutes"}.get(r.get("source", ""), "minutes")
        # standalone RDA/LBA board-meeting docs are wholly that body; council regular
        # docs default to Council and let body_at() walk any in-session RDA/LBA recess.
        slug = r.get("slug", "")
        doc_default = ("RDA" if slug == "rda-meeting" else
                       "LBA" if slug == "lba-meeting" else DEFAULT_BODY)
        motions = parse_meeting(text, doc_default)
        # JSON per meeting (resumable path mirrors minutes path)
        jpath = VOTES_DIR / Path(r["path"]).relative_to("minutes").with_suffix(".json")
        jpath.parent.mkdir(parents=True, exist_ok=True)
        jpath.write_text(json.dumps(
            {"date": r["date"], "title": r["title"], "source_url": r["source_url"],
             "path": r["path"], "provenance": provenance, "motions": motions},
            indent=1), encoding="utf-8")
        n_meetings += 1
        for mo in motions:
            n_motions += 1
            base = {"date": r["date"], "year": r["year"], "title": r["title"],
                    "body": mo["body"], "motion_no": mo["motion_no"], "motion": mo["motion"],
                    "motion_type": mo["motion_type"], "result": mo["result"],
                    "mover": mo["mover"], "seconder": mo["seconder"], "source": r["path"],
                    "provenance": provenance}
            if mo["votes"]:
                for v in mo["votes"]:
                    all_rows.append({**base, "member": v["member"], "vote": v["vote"]})
            else:
                all_rows.append({**base, "member": "", "vote": ""})
    # 13-col standard + the documented trailing `provenance` extension (minutes |
    # wayback_minutes) — same pattern as the pmn_%-recovered cities.
    cols = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source", "provenance"]
    all_rows.sort(key=lambda x: (x["date"], x["title"], x["motion_no"]))
    with open(ALL_VOTES, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for row in all_rows:
            w.writerow(row)
    print(f"{DEFAULT_BODY}: {n_meetings} meetings, {n_motions} motions, "
          f"{len(all_rows)} vote rows -> {ALL_VOTES}")

if __name__ == "__main__":
    main()
