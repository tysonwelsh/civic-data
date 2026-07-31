#!/usr/bin/env python3
"""
Cottonwood Heights vote-extraction core (PURE deterministic — no LLM, no network).
Shared by meeting_minutes/extract_votes.py (Council) and
planning_commission/extract_votes.py.

CH vote grammar — a NAMED per-member INLINE roll call, two printed variants:
  * PDF-era (2024+):  "Vote on Motion: Council Member Holton - No, Council Member
                       Hyland - Yes, ... Mayor Weichers - Yes. The motion passed 3-to-2."
  * DOCX/PMN-era:     "Vote on Motion:  Council Member Holton-Aye; Council Member
                       Bracken-Aye; ... Mayor Weichers-Aye.  The motion passed unanimously."
  (separator , or ; ; dash - or –/— with optional spaces; token Aye/Yes/Nay/No/
   Abstain(ed)/Absent/Recuse/Excused.)
Procedural motions (adjourn / open-closed-meeting / approve minutes) print NO names:
  "The motion passed with the unanimous consent of the Council." -> tally-only placeholder.
Died: "The motion failed for lack of a second."

THE MAYOR VOTES (max Council roll = 5 = 4 districts + a separately-elected voting Mayor)
— confirmed on a contested 3-2 (2024-01-16, Ord 407). A `Mayor <Name>` roll entry is a
REAL vote and IS counted; validate flags mayor-vote rows for audit but they are ordinary.
"""
import csv
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
VOTE_MAP = {
    "yes": "aye", "aye": "aye", "aay": "aye", "ayes": "aye",
    "no": "nay", "nay": "nay", "nae": "nay",
    "abstain": "abstain", "abstained": "abstain", "abstention": "abstain",
    "absent": "absent", "excused": "absent",
    "recuse": "recuse", "recused": "recuse",
}
_ROLE = r"(?:Council\s*Members?|Board\s*Members?|Commission(?:ers?)?|Vice[-\s]?Chair|Chair|Mayor(?:\s*Pro\s*Tem(?:pore|p)?)?)"

# a single roll-call pair inside a "Vote on Motion:" block. The role token is
# OPTIONAL (2026-07-17): some clerk-era rolls print bare "Firstname Lastname-Aye"
# (PC 2020-01-08 / 2020-07-15 / 2021-03-03) or drop the title mid-roll
# ("…, Anderson-Aye, …"). Precision holds because parse_roll only accepts a pair
# whose name resolves against the meeting-body ROSTER, only scans Vote-on-Motion
# blocks (or the guarded >=2-member blockless fallback), and the token must be a
# vote word — prose like "Ordinance Enforcement – No" resolves no roster name.
PAIR_RE = re.compile(
    r"(?:" + _ROLE + r"\.?\s+)?([A-Za-z][A-Za-z.'\-]*(?:\s+[A-Z]\.?)?(?:\s+[A-Za-z.'\-]+)??)"
    r"\s*[-–—]\s*(Aye|Aay|Ayes|Nay|Nae|Yes|No|Abstain(?:ed)?|Abstention|Absent|Excused|Recuse[d]?)\b", re.I)

VOTE_BLOCK_RE = re.compile(r"Vote\s+on\s+(?:the\s+)?Motion\s*:?(.*)$", re.I | re.S)

MOTION_START_RE = re.compile(
    r"(?:MOTION\s*:?\s*)?" + _ROLE +
    r"\.?\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z.'\-]+){0,2}?)\s+"
    r"(?:moved|made\s+a(?:\s+\w+)?\s+motion|motioned)\b", re.I)
SECONDER_RE = re.compile(
    r"seconded\s+by\s+" + _ROLE + r"\.?\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z.'\-]+){0,2}?)\b"
    r"|" + _ROLE + r"\.?\s+([A-Z][A-Za-z.'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z.'\-]+){0,2}?)\s+seconded\b",
    re.I)

# result phrases (each is ONE recorded outcome; parser anchors on these).
# "The" is OPTIONAL for the terse pass forms (consent/tally/unanimous — some CDRA /
# special / retreat minutes write just "Motion passed unanimously."). The died/failed
# branches REQUIRE the "The motion" adjacency, so an intervening "The substitute motion
# failed for lack of a second" does NOT spawn a phantom result (which would misattribute
# the real vote that follows — e.g. Ord 407, 2024-01-16).
RESULT_RE = re.compile(
    r"(?P<consent>(?:[Tt]he\s+)?[Mm]otion\s+(?:passed|carried)\s+with\s+(?:the\s+)?"
    r"unanimous\s+consent[^.]*)\."
    r"|(?P<died>[Tt]he\s+(?:main\s+|original\s+)?motion\s+(?:failed|died)\s+(?:for\s+)?"
    r"(?:due\s+to\s+)?lack\s+of\s+a?\s*second[^.]*)\."
    r"|(?P<tally>(?:[Tt]he\s+)?[Mm]otion\s+(?:passed|carried|failed)\s+(?:by\s+|with\s+)?"
    r"(?:a\s+vote\s+of\s+)?(?P<a>\d+)\s*[-\s]?to[-\s]?\s*(?P<b>\d+)[^.]*)\."
    r"|(?P<unanim>(?:[Tt]he\s+)?[Mm]otion\s+(?:passed|carried)\s+unanimously[^.]*)\."
    r"|(?P<failed>[Tt]he\s+(?:main\s+|original\s+)?motion\s+failed[^.]*)\.", re.I)

FOOTER_LINE = re.compile(
    r"^\s*(?:Cottonwood\s+Heights.*(?:Meeting\s+Minutes|Approved\s*:).*|"
    r"Approved\s*:.*|Page\s+\d+.*|\d{1,3})\s*$", re.I)

# A running footer that, once the page break is collapsed away, lands INSIDE a roll-call
# block and splits e.g. "Council | <footer> | Member Bracken-Nay" (dropping Bracken).
# Word order varies ("City Council Meeting Minutes for <date> Cottonwood Heights Approved:
# <date>"), so scrub the whole phrase from the collapsed text regardless of line breaks.
_BODY = (r"(?:City\s+Council|Planning\s+Commission|CDRA|"
         r"Community\s+Development(?:\s+and\s+Renewal)?\s+Agency|Board\s+of\s+Canvassers)")
_DATE = r"[A-Z][a-z]+\.?\s+\d{1,2},?\s+\d{4}"
FOOTER_SCRUB = re.compile(
    r"\.?\s*(?:Cottonwood\s+Heights\s+)?(?:" + _BODY + r"\s+)?"
    r"(?:"
    r"Meeting\s+Minutes\s+for\s+" + _DATE +
    r"(?:\s+Cottonwood\s+Heights)?(?:\s+Approved\s*:\s*" + _DATE + r")?"
    r"|"
    r"Approved\s*:\s*" + _DATE +
    r")", re.I)


def load_text(md_path):
    """Read a minutes .md, drop the provenance header + running footers, return the
    body as ONE whitespace-collapsed string (motions/roll-calls span page breaks)."""
    raw = md_path.read_text(encoding="utf-8", errors="replace")
    # strip provenance header up to and including the first '---' fence
    if "\n---\n" in raw:
        raw = raw.split("\n---\n", 1)[1]
    kept = [ln for ln in raw.split("\n") if not FOOTER_LINE.match(ln.strip())]
    collapsed = re.sub(r"\s+", " ", " ".join(kept)).strip()
    text = FOOTER_SCRUB.sub(" ", collapsed)
    # repair page-number bleeds that land between two result-phrase words and break the
    # result regex ("The 19 motion passed", "motion 7 passed", "unanimous 18 consent").
    for _ in range(2):
        text = re.sub(
            r"\b(the|motion|unanimous|consent|passed|carried|failed|with)\s+\d{1,3}\s+"
            r"(motion|passed|carried|failed|consent|unanimously|with|the|of)\b",
            r"\1 \2", text, flags=re.I)
    return text


# ---------------------------------------------------------------------------
def classify_motion(text):
    t = text.lower()
    if re.search(r"rezon|zoning|zone change|\bzone\b|annex|subdivision|\bplat\b|"
                 r"conditional use|land use|general plan|master plan|development agreement|"
                 r"overlay|site plan|future land use|cdra|community development and renewal|"
                 r"redevelopment|project area|planned development|preliminary|final plat|"
                 r"lot line|design review", t):
        return "Land-Use/Zoning"
    if re.search(r"budget amendment|amend.*budget|tentative budget|final budget|"
                 r"adopt.*budget|budget for|appropriat", t):
        return "Budget Amendment"
    if re.search(r"interlocal|inter-local|cooperation agreement", t):
        return "Interlocal"
    if re.search(r"\bgrant\b", t) and "grant the" not in t:
        return "Grant-Funding"
    if re.search(r"appoint|reappoint|mayor pro tem|liaison|ratify.*(?:results|canvass|"
                 r"assignment)|committee assignment", t):
        return "Appointment"
    if re.search(r"\bcontract\b|purchase|procurement|award the bid|award.*contract|"
                 r"professional services|franchise|agreement with|services agreement|"
                 r"enter into an agreement|bid", t):
        return "Contract/Purchase"
    if re.search(r"\bordinance\b", t):
        return "Ordinance"
    if re.search(r"\bresolution\b", t):
        return "Resolution"
    if re.search(r"public hearing", t):
        return "Public Hearing Action"
    if re.search(r"proclamation|recognition|recognize|honor|commend|ceremonial|badge|"
                 r"retire", t):
        return "Ceremonial"
    if re.search(r"recess|adjourn|convene|reconvene|closed (?:meeting|session)|"
                 r"executive session|approve the (?:consent|agenda|minutes|order)|"
                 r"approve.*minutes|\btable\b|continue|postpone|amend the agenda|"
                 r"open a closed", t):
        return "Procedural/Administrative"
    return "Other"


class Parser:
    def __init__(self, roster_map, mayor_tokens, default_body, body_for_path=None):
        self.roster = roster_map          # surname token -> canonical full name
        self.mayor_tokens = mayor_tokens  # surnames that are the (voting) Mayor
        self.default_body = default_body
        self.body_for_path = body_for_path or (lambda slug: default_body)

    def find_member(self, phrase):
        toks = re.findall(r"[A-Za-z']+", phrase.lower())
        for t in toks:
            if t in self.roster:
                return self.roster[t], (t in self.mayor_tokens)
        return None, False

    def parse_roll(self, block):
        """Return (buckets, mayor_voted, roll_names) from a Vote-on-Motion block."""
        # a roll-call block holds ONLY names + vote tokens; bare 1-3 digit runs are
        # page-number bleeds injected mid-block (esp. PMN/DOCX) that split
        # "Commissioner 18 Allen-Aye" / "Coutts- 19 Aye" -> strip them.
        block = re.sub(r"(?<![-\w])\d{1,3}(?![-\w])", " ", block)
        buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
        mayor_voted = False
        seen = set()
        for m in PAIR_RE.finditer(block):
            name_phrase, tok = m.group(1), m.group(2).lower()
            nm, is_mayor = self.find_member(m.group(0))
            if nm is None or nm in seen:
                continue
            seen.add(nm)
            bkt = VOTE_MAP.get(tok, VOTE_MAP.get(tok[:6], "aye"))
            buckets[bkt].append(nm)
            if is_mayor:
                mayor_voted = True
        return buckets, mayor_voted, seen

    def parse_meeting(self, text, slug=""):
        body = self.body_for_path(slug)
        votes = []
        prev_end = 0
        for rm in RESULT_RE.finditer(text):
            window = text[prev_end:rm.start()]
            result_full = rm.group(0)
            # ---- motion text + mover: nearest preceding motion-start in the window.
            # If the last start is a SUBSTITUTE motion that then failed for lack of a
            # second (recorded as prose, not a "The motion..." result), the vote below
            # belongs to the ORIGINAL motion -> step back one start. ----
            starts = list(MOTION_START_RE.finditer(window))
            if starts:
                ms = starts[-1]
                if (re.search(r"substitut", ms.group(0), re.I) and len(starts) >= 2
                        and re.search(r"lack of a second|failed|died",
                                      window[ms.start():], re.I)):
                    ms = starts[-2]
                motion_text = window[ms.start():].strip()
                mover, _ = self.find_member(ms.group(0))
            else:
                motion_text = window.strip()[-600:]
                mover = None
            # Pleading-paper (PMN/DOCX) minutes carry a numbered left-margin gutter; once
            # load_text collapses the page each line-start number lands MID-TEXT and can
            # split the seconder attribution -> "Commissioner 7 Ebbeler seconded" leaves a
            # blank seconder. parse_roll already scrubs these bare line-numbers inside
            # Vote-on-Motion blocks; do the same for the SECONDER pass. The scrub feeds
            # ONLY the name match (SECONDER_RE.group(0) -> find_member); the STORED motion
            # prose is the un-scrubbed `motion_text`, so no prose is lost. The MOTION_START
            # / mover pass stays on the un-scrubbed window (the gutter digit there actually
            # guards against a spurious earlier "...Commission. <n> Commissioner X moved"
            # boundary match — removing it would drift the motion start).
            seconder = None
            motion_scrub = re.sub(r"(?<![-\w])\d{1,3}(?![-\w])", " ", motion_text)
            sm = SECONDER_RE.search(motion_scrub)
            if sm:
                seconder, _ = self.find_member(sm.group(0))

            # ---- CDRA / board body detection (council dataset) ----
            mbody = body
            if self.default_body == "Council":
                if re.search(r"\bCDRA\b|community development and renewal|"
                             r"redevelopment agency", motion_text, re.I) or \
                   re.search(r"Board\s+Member\s+\w+\s*[-–—]", motion_text, re.I):
                    mbody = "CDRA"

            # ---- outcome ----
            buckets = {"aye": [], "nay": [], "abstain": [], "absent": [], "recuse": []}
            mayor_voted = False
            names_recorded = False
            printed_tally = None

            if rm.group("consent"):
                result = "Passed (unanimous consent)"
            elif rm.group("died"):
                result = "Failed (no second)"
            else:
                # find a Vote-on-Motion block between the motion start and the result
                vb = None
                vm = VOTE_BLOCK_RE.search(motion_text)
                if vm:
                    vb = vm.group(1)[:vm.group(1).find(result_full) if result_full in vm.group(1) else None]
                if vb:
                    buckets, mayor_voted, roll = self.parse_roll(vb)
                    if len(roll) >= 2:
                        names_recorded = True
                else:
                    # blockless inline roll (rare clerk form — PC 2020-01-08: the
                    # roll follows the seconder sentence with NO "Vote on Motion:"
                    # label). Guard: accept ONLY if >=2 DISTINCT roster members
                    # resolve — prose never prints multiple Name-VoteWord pairs.
                    b2, mv2, roll2 = self.parse_roll(motion_text[-500:])
                    if len(roll2) >= 2:
                        buckets, mayor_voted = b2, mv2
                        names_recorded = True
                if rm.group("tally"):
                    a, b = int(rm.group("a")), int(rm.group("b"))
                    printed_tally = [a, b]
                    passed = bool(re.search(r"passed|carried", rm.group("tally"), re.I))
                    result = f"{'Passed' if passed else 'Failed'} {a}-to-{b}"
                elif rm.group("unanim"):
                    tail = rm.group("unanim")
                    extra = ""
                    am = re.search(r"with\s+(one|two|three|\d+)\s+abstention", tail, re.I)
                    if am:
                        extra = f" (with {am.group(1)} abstention)"
                    result = "Passed unanimously" + extra
                else:  # generic failed
                    result = "Failed"

            votes.append({
                "body": mbody,
                "motion": re.sub(r"\s+", " ", motion_text)[:600].strip(" .;,"),
                "motion_type": classify_motion(motion_text),
                "result": result,
                "mover": mover,
                "seconder": seconder,
                "aye": buckets["aye"], "nay": buckets["nay"],
                "abstain": buckets["abstain"], "absent": buckets["absent"],
                "recuse": buckets["recuse"],
                "names_recorded": names_recorded,
                "printed_tally": printed_tally,
                "mayor_voted": mayor_voted,
            })
            prev_end = rm.end()
        return votes


# ---------------------------------------------------------------------------
def run(ds_dir, parser, force=False, provenance_for=None):
    """provenance_for: optional callable(index_row) -> provenance string
    ('minutes' = audited primary; 'pmn_minutes' = PMN-backfill-recovered doc promoted
    into the audited layer — the documented trailing-14th-column convention). When
    given, the per-meeting JSON carries `provenance` and all_votes.csv gains the
    trailing `provenance` column; when omitted the 13-col standard is unchanged."""
    ds_dir = Path(ds_dir)
    index = ds_dir / "minutes_index.csv"
    votes_dir = ds_dir / "votes"
    rows = list(csv.DictReader(index.open()))
    processed = skipped = 0
    for r in rows:
        path = ds_dir / r["path"]
        if not path.exists():
            print(f"MISSING: {r['path']}", file=sys.stderr)
            continue
        week = Path(r["path"]).parent.name
        year = r["year"]
        slug = Path(r["path"]).stem
        out_dir = votes_dir / year / week
        out_json = out_dir / f"{slug}.json"
        if out_json.exists() and not force:
            skipped += 1
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        vlist = parser.parse_meeting(load_text(path), slug=slug)
        for k, v in enumerate(vlist, 1):
            v["motion_no"] = k
        payload = {"date": r["date"], "year": int(year), "title": r["title"],
                   "source": r["path"], "votes": vlist}
        if provenance_for is not None:
            payload["provenance"] = provenance_for(r)
        out_json.write_text(json.dumps(payload, indent=1, ensure_ascii=False))
        processed += 1
    print(f"Processed {processed} meetings -> JSON (skipped {skipped})")
    build_all_votes(ds_dir, with_provenance=provenance_for is not None)


def build_all_votes(ds_dir, with_provenance=False):
    ds_dir = Path(ds_dir)
    votes_dir = ds_dir / "votes"
    out = ds_dir / "all_votes.csv"
    fields = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
              "result", "mover", "seconder", "member", "vote", "source"]
    if with_provenance:
        fields = fields + ["provenance"]
    n = 0
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for jp in sorted(votes_dir.rglob("*.json")):
            if jp.name.startswith("_"):
                continue
            data = json.loads(jp.read_text())
            prov = [data.get("provenance") or "minutes"] if with_provenance else []
            for v in data["votes"]:
                base = [data["date"], data["year"], data["title"], v["body"],
                        v["motion_no"], v["motion"], v["motion_type"], v["result"],
                        v.get("mover") or "", v.get("seconder") or ""]
                emitted = False
                for key, label in (("aye", "Aye"), ("nay", "Nay"), ("abstain", "Abstain"),
                                   ("absent", "Absent"), ("recuse", "Recuse")):
                    for mbr in v.get(key, []):
                        w.writerow(base + [mbr, label, data["source"]] + prov)
                        n += 1
                        emitted = True
                if not emitted:
                    w.writerow(base + ["", "", data["source"]] + prov)
                    n += 1
    print(f"Wrote {out} with {n} data rows")
