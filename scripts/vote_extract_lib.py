#!/usr/bin/env python3
"""
vote_extract_lib.py — shared skeleton for city vote extractors (REMEDIATION_PLAN.md 3.5).

THE MANDATORY STARTING POINT FOR EVERY NEW CITY. A new `extract_votes.py`
(council or planning commission) imports this module for everything that is NOT
city-specific — file walking, header stripping, roll-call helpers, name matching,
outcome-stop scanning, the 13-column CSV writer, the per-meeting JSON writer, and
the pre-write sanity checks — and supplies only the city's own parsing profile
(the clerk's motion/roll-call phrasing, the city motion-type taxonomy, body
detection, roster canon). The 13 existing extractors predate this module and are
NOT migrated wholesale (they migrate only when touched); this module is the
distillation of their shared anatomy and of the fleet's hard-won lessons:

  * CASE-SENSITIVE result/label regexes           (park_city, `make_label_re`)
  * full-name-first voter matching                (slc PC,    `NameMatcher`)
  * stop the roll-call scan at the outcome
    declaration                                   (nephi PC,  `truncate_at_outcome`)
  * never guess voters: tally-only motions emit
    ONE blank-member placeholder row              (SCHEMA_SPEC §2, `motion_rows`)
  * capture the agenda subject/heading when the
    recorded motion text is boilerplate           (ogden's 428 subject-less
                                                   adoption motions; see the build
                                                   skill's extraction_standards.md)

Everything stdlib-only and deterministic. Outputs conform to SCHEMA_SPEC.md §2
(all_votes.csv) and the per-meeting votes JSON used across the repo. After
extraction, install + run the shared validator (scripts/validate_votes_template.py
→ <dataset>/validate_votes.py) and `scripts/validate_city.py <city>`; the
`basic_checks()` hook here is the extractor's own pre-write gate, not a
replacement for those.

Typical skeleton for a new city:

    from vote_extract_lib import (walk_minutes, read_minutes, make_label_re,
                                  truncate_at_outcome, NameMatcher, Motion,
                                  motion_rows, basic_checks,
                                  write_all_votes_csv, write_meeting_json)

    for mf in walk_minutes(DATASET_DIR):
        title, body_text = read_minutes(mf.path)
        motions = parse_city_specific(body_text)      # the only bespoke part
        write_meeting_json(DATASET_DIR, mf, title, motions)
    rows = [r for mf, title, motions in meetings
              for m in motions for r in motion_rows(mf, title, m)]
    problems = basic_checks(rows)                     # fail loud, fix, re-run
    write_all_votes_csv(DATASET_DIR / "all_votes.csv", rows)
"""
from __future__ import annotations

import csv
import dataclasses
import datetime
import json
import os
import re
from typing import Iterable, Iterator, List, Optional, Sequence

# --------------------------------------------------------------------------- schema
# SCHEMA_SPEC.md §2 — long format, one row per member-vote (or one placeholder
# row per tally-only motion). Column order is normative.
STD_COLS = ["date", "year", "title", "body", "motion_no", "motion", "motion_type",
            "result", "mover", "seconder", "member", "vote", "source"]

# SCHEMA_SPEC.md §4 controlled vote vocabulary. Documented per-city extensions
# (e.g. sandy "Excused") are passed to basic_checks(), never silently invented.
VOTE_VOCAB = {"Aye", "Nay", "Abstain", "Recuse", "Absent", "Excused"}

# JSON bucket name -> CSV vote value.
BUCKETS = {"aye": "Aye", "nay": "Nay", "abstain": "Abstain",
           "recuse": "Recuse", "absent": "Absent"}


# --------------------------------------------------------------------------- files
@dataclasses.dataclass(frozen=True)
class MinutesFile:
    """One minutes document under <dataset>/minutes/<YYYY>/<week-start>/<date>_<slug>.md"""
    date: str          # ISO YYYY-MM-DD, from the filename
    year: int
    week: str          # the <week-start> directory name
    slug: str
    path: str          # absolute path
    relpath: str       # path relative to the dataset dir ("minutes/...") — the
                       # standard `source` column value (SCHEMA_SPEC §2)


_FNAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_(.+)\.md$")


def walk_minutes(dataset_dir: str, subdir: str = "minutes") -> Iterator[MinutesFile]:
    """Yield every minutes markdown file in the standard tree, in deterministic
    (date, slug) order. Files not matching <date>_<slug>.md are skipped —
    the tree must contain ONLY minutes documents (SCHEMA_SPEC §1)."""
    root = os.path.join(dataset_dir, subdir)
    out: List[MinutesFile] = []
    for year in sorted(d for d in os.listdir(root)
                       if re.fullmatch(r"\d{4}", d) and os.path.isdir(os.path.join(root, d))):
        ydir = os.path.join(root, year)
        for week in sorted(os.listdir(ydir)):
            wdir = os.path.join(ydir, week)
            if not os.path.isdir(wdir):
                continue
            for fn in sorted(os.listdir(wdir)):
                m = _FNAME_RE.match(fn)
                if not m:
                    continue
                date, slug = m.groups()
                datetime.date.fromisoformat(date)   # fail loud on malformed names
                out.append(MinutesFile(
                    date=date, year=int(date[:4]), week=week, slug=slug,
                    path=os.path.join(wdir, fn),
                    relpath="/".join([subdir, year, week, fn])))
    return iter(sorted(out, key=lambda f: (f.date, f.slug)))


_HEADER_RE = re.compile(r"^#\s+(?P<title>.*?)(?:\s+[—-]+\s+\d{4}-\d{2}-\d{2})?\s*$")


def read_minutes(path: str) -> tuple:
    """Read a minutes markdown file; strip the repo-generated provenance header
    (the leading '# <Title> — YYYY-MM-DD' H1 added at conversion time — it is OUR
    header, not clerk text, and must never be parsed as minutes content).
    Returns (title_or_None, body_text)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    title = None
    if i < len(lines) and lines[i].startswith("# "):
        m = _HEADER_RE.match(lines[i])
        if m:
            title = m.group("title").strip()
            i += 1
    return title, "\n".join(lines[i:]).lstrip("\n")


# --------------------------------------------------------------------------- roll-call helpers
def make_label_re(labels: Sequence[str], case_sensitive: bool = True,
                  allow_line_number_noise: bool = True) -> re.Pattern:
    """Compile a start-of-line result/roll-call label matcher, e.g.
    make_label_re(["AYES?", "NAYS?", "ABSTAINED?", "ABSENT", "EXCUSED", "RECUSED?"]).

    CASE-SENSITIVE BY DEFAULT — the park_city lesson (2026-07-02): its clerk's
    result blocks are ALWAYS uppercase (all 1,524 in the corpus), and a
    case-insensitive match fabricated 10 spurious motions out of wrapped lowercase
    prose — a public comment continuing "...as a\\nresult: https://www.orlando.gov/..."
    became a motion, and a commenter's OPINION that a member should recuse became a
    fabricated Recuse vote row. Measure the clerk's literal casing in YOUR corpus
    first; only pass case_sensitive=False with corpus evidence that the clerk
    genuinely mixes case, and then anchor the block shape some other way."""
    body = "|".join(labels)
    noise = r"\d*\s*" if allow_line_number_noise else ""
    return re.compile(rf"^\s*{noise}({body})\s*[:.]?\s*(.*)$",
                      0 if case_sensitive else re.IGNORECASE)


DEFAULT_OUTCOME_RE = re.compile(
    r"\bMotion\s+(?:is\s+|was\s+)?"
    r"(?:approved|adopted|passes|passed|carried|carries|denied|failed|fails)\b",
    re.IGNORECASE)


def truncate_at_outcome(block: str, outcome_re: re.Pattern = DEFAULT_OUTCOME_RE) -> str:
    """Cut a roll-call scan region at the first outcome DECLARATION — the nephi
    lesson (plan 3.1): real vote lists always PRECEDE 'Motion Passes'/'Motion is
    approved', while the prose after it can re-mention a member ("Motion Passes,
    Chairman Ann Peterson will serve for the 2024 year") — reading a vote out of
    that prose fabricated a duplicate Peterson=Absent row (nephi PC 2024-01-10).
    Roll calls printed inside an Outcome block still end before the declaration,
    so they survive the cut."""
    return outcome_re.split(block)[0]


# --------------------------------------------------------------------------- name matching
class NameMatcher:
    """Resolve voter mentions in a text span to canonical full names,
    FULL-NAME-FIRST — the slc PC Christensen lesson (plan 3.1): two attendees
    shared the surname Christensen (Mike vs McCall); a bare surname->name map
    collapsed every 'Christensen' to whichever full name won the map, silently
    misattributing (and dropping) McCall's votes. So: pass 0 matches EXACT full
    names (whitespace-tolerant, so line-wrapped names work) and CONSUMES those
    spans; only then are bare surnames resolved, and a surname shared by two
    known attendees is NEVER resolved from the surname alone (returns no match
    rather than a guess).

    `known` is the meeting's attendee canon (full names, presence order kept).
    Titles (Council Member / Commissioner / Chair ...) in the text are the city
    extractor's business to strip or tolerate — this class matches names only."""

    def __init__(self, known: Sequence[str]):
        self.known = list(dict.fromkeys(known))
        self._full_res = [(re.compile(r"\b" + r"\s+".join(map(re.escape, n.split())) + r"\b"), n)
                          for n in self.known]
        surn = {}
        for n in self.known:
            surn.setdefault(n.split()[-1].lower(), []).append(n)
        self._surnames = surn

    def scan(self, blob: str) -> List[str]:
        """Full names found in blob, ordered by first position, each attendee at
        most once. Exact full-name matches consume their spans first; bare
        surnames then resolve ONLY when exactly one known attendee holds them."""
        hits = []   # (pos, name)
        consumed = []
        for rex, name in self._full_res:
            m = rex.search(blob)
            if m:
                hits.append((m.start(), name))
                consumed.append((m.start(), m.end()))
        taken = {n for _, n in hits}
        for surname, holders in self._surnames.items():
            if len(holders) != 1 or holders[0] in taken:
                continue   # shared surname: full-name match or nothing — never guess
            for m in re.finditer(r"\b" + re.escape(surname) + r"\b", blob, re.IGNORECASE):
                if any(a <= m.start() < b for a, b in consumed):
                    continue
                hits.append((m.start(), holders[0]))
                break
        seen, out = set(), []
        for _, name in sorted(hits):
            if name not in seen:
                seen.add(name)
                out.append(name)
        return out


# --------------------------------------------------------------------------- motions → rows
@dataclasses.dataclass
class Motion:
    motion_no: int
    motion: str                    # verbatim (whitespace-normalized) motion text.
                                   # If the recorded motion is boilerplate ("ORDINANCE
                                   # WAS PASSED AND ADOPTED AS ORDINANCE 20xx-N"), the
                                   # extractor MUST pull the agenda heading / long-title
                                   # into this text or the title field (ogden lesson).
    motion_type: str               # city-native taxonomy (crosswalked later, never here)
    result: str                    # VERBATIM outcome string as printed
    mover: str = ""
    seconder: str = ""
    body: str = "Council"          # Council / PlanningCommission / RDA / CRA / ...
    aye: List[str] = dataclasses.field(default_factory=list)
    nay: List[str] = dataclasses.field(default_factory=list)
    abstain: List[str] = dataclasses.field(default_factory=list)
    recuse: List[str] = dataclasses.field(default_factory=list)
    absent: List[str] = dataclasses.field(default_factory=list)

    @property
    def names_recorded(self) -> bool:
        return bool(self.aye or self.nay or self.abstain or self.recuse or self.absent)


def motion_rows(mf: MinutesFile, title: str, m: Motion,
                source_prefix: str = "") -> List[dict]:
    """13-column rows for one motion. Tally-only motions (no names printed in the
    source) emit exactly ONE placeholder row with member and vote blank — voters
    are NEVER guessed from 'unanimous' (SCHEMA_SPEC §2)."""
    src = source_prefix + mf.relpath
    base = {"date": mf.date, "year": mf.year, "title": title or "", "body": m.body,
            "motion_no": m.motion_no, "motion": m.motion, "motion_type": m.motion_type,
            "result": m.result, "mover": m.mover or "", "seconder": m.seconder or "",
            "source": src}
    if not m.names_recorded:
        return [dict(base, member="", vote="")]
    rows = []
    for bucket, value in BUCKETS.items():
        for name in getattr(m, bucket):
            rows.append(dict(base, member=name, vote=value))
    return rows


# --------------------------------------------------------------------------- writers
def write_all_votes_csv(path: str, rows: Iterable[dict]) -> int:
    """Write all_votes.csv in the normative column order. Returns row count."""
    rows = list(rows)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=STD_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in STD_COLS})
    return len(rows)


def write_meeting_json(dataset_dir: str, mf: MinutesFile, title: str,
                       motions: Sequence[Motion], body_default: str = "Council",
                       source_prefix: str = "") -> str:
    """Write the per-meeting structured intermediate under
    <dataset>/votes/<year>/<week>/<date>_<slug>.json (tree mirrors minutes/).
    Extractors are resumable by skipping meetings whose JSON already exists."""
    out_dir = os.path.join(dataset_dir, "votes", str(mf.year), mf.week)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{mf.date}_{mf.slug}.json")
    doc = {
        "date": mf.date, "year": mf.year, "title": title or "",
        "body_default": body_default,
        "source": source_prefix + mf.relpath,
        "votes": [{
            "motion_no": m.motion_no, "motion": m.motion, "body": m.body,
            "motion_type": m.motion_type, "result": m.result,
            "mover": m.mover or None, "seconder": m.seconder or None,
            "names_recorded": m.names_recorded,
            "aye": m.aye, "nay": m.nay, "abstain": m.abstain,
            "absent": m.absent, "recuse": m.recuse,
        } for m in motions],
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    return out_path


# --------------------------------------------------------------------------- validation hooks
def basic_checks(rows: Iterable[dict],
                 vote_value_extensions: Optional[set] = None) -> List[str]:
    """The extractor's own pre-write gate (NOT a replacement for the shared
    validator). Returns a list of problem strings — the caller should print them
    and refuse to ship a CSV until they're fixed or documented:
      - date parses + year column matches
      - vote values within vocabulary (+ documented extensions)
      - tally-only convention: per (source, motion_no) either all rows named or
        exactly one blank placeholder — never mixed
      - no member voting twice on one motion (source clerk contradictions are
        kept verbatim but must be KNOWN — resolve them in db/vote_overrides.csv)

    After writing, ALWAYS run the shared per-dataset validator (install
    scripts/validate_votes_template.py as <dataset>/validate_votes.py) and
    `python3 scripts/validate_city.py <city_dir>` — 0 FAIL before declaring done."""
    vocab = VOTE_VOCAB | (vote_value_extensions or set())
    problems: List[str] = []
    groups = {}
    for i, r in enumerate(rows):
        try:
            d = datetime.date.fromisoformat(r["date"])
            if str(d.year) != str(r["year"]):
                problems.append(f"row {i}: year {r['year']} != date {r['date']}")
        except (ValueError, KeyError):
            problems.append(f"row {i}: bad date {r.get('date')!r}")
        if r.get("member"):
            if r.get("vote") not in vocab:
                problems.append(f"row {i}: vote {r.get('vote')!r} outside vocabulary")
        elif r.get("vote"):
            problems.append(f"row {i}: vote without member")
        groups.setdefault((r.get("source"), r.get("motion_no")), []).append(r)
    for key, g in groups.items():
        named = [r for r in g if r.get("member")]
        blank = [r for r in g if not r.get("member")]
        if named and blank:
            problems.append(f"motion {key}: mixed named + placeholder rows")
        if not named and len(blank) != 1:
            problems.append(f"motion {key}: {len(blank)} placeholder rows (want 1)")
        seen = {}
        for r in named:
            if r["member"] in seen:
                problems.append(f"motion {key}: {r['member']} votes twice "
                                f"({seen[r['member']]} + {r['vote']}) — verify vs source; "
                                "if a real clerk contradiction, keep verbatim and resolve "
                                "in db/vote_overrides.csv")
            seen[r["member"]] = r["vote"]
    return problems
