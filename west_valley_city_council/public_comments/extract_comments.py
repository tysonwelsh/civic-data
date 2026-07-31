#!/usr/bin/env python3
"""
Extract public comments from West Valley City council Regular meeting minutes.

WVC does NOT publish a separate public-comment dataset. Instead, the City
Recorder transcribes/summarizes each in-person speaker by name inside the
"PUBLIC COMMENT PERIOD" (newer minutes) or "COMMENT PERIOD / A. PUBLIC COMMENTS"
(older minutes) section of every Regular meeting's minutes.

This script slices that section out of every Regular-meeting markdown file and
emits one row per named public speaker, mirroring the SLC all_comments_clean.csv
schema.

Outputs (written next to this script):
  all_comments_clean.csv   - the cleaned comment rows
  all_comments_dropped.csv - audit trail of dropped paragraphs (+ _drop_reason)

Run:  python3 public_comments/extract_comments.py   (from repo root)
"""

import csv
import os
import re
import glob
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MINUTES_GLOB = os.path.join(REPO, "meeting_minutes", "minutes", "*", "*", "*regular*.md")

CLEAN_OUT = os.path.join(HERE, "all_comments_clean.csv")
DROPPED_OUT = os.path.join(HERE, "all_comments_dropped.csv")

SCHEMA = [
    "date", "contact_name", "subject", "topic", "comment", "district",
    "source", "has_attachment", "source_file", "page_numbers",
    "period_start", "period_end", "date_normalized", "quality_flag",
]

SOURCE = "in_person_minutes"

# ----------------------------------------------------------------------------
# Section boundary detection
# ----------------------------------------------------------------------------

# Start of the public-comment section. Two layouts seen across 2020-2026:
#   newer:  a bare line "PUBLIC COMMENT PERIOD"
#   older:  "COMMENT PERIOD" then "A.  PUBLIC COMMENTS"
RE_START_NEW = re.compile(r"^\s*PUBLIC COMMENT PERIOD\s*$")
RE_START_OLD = re.compile(r"^\s*[A-Z]\.\s+PUBLIC COMMENTS\s*$")

# These end the comment section. Generic all-caps section header, or one of the
# explicit next-section markers. NB: "ACCEPT PUBLIC COMMENT REGARDING ..." is a
# public *hearing* item, not the general comment period, so it also ends it.
RE_END = re.compile(
    r"^\s*("
    r"[A-Z]\.\s+CITY MANAGER COMMENT"
    r"|[A-Z]\.\s+CITY COUNCIL COMMENT"
    r"|CITY MANAGER COMMENT"
    r"|CITY COUNCIL COMMENT"
    r"|PUBLIC HEARING"
    r"|CONSENT (AGENDA|ITEMS)"
    r"|UNFINISHED BUSINESS"
    r"|NEW BUSINESS"
    r"|ADOPTION OF"
    r"|ACTION:"
    r"|RESOLUTION \d"
    r"|ORDINANCE \d"
    r"|MOTION TO ADJOURN"
    r"|REPORTS?"
    r"|[A-Z]\.\s+ACCEPT PUBLIC"
    r"|ACCEPT PUBLIC (COMMENT|INPUT)"
    r"|PUBLIC INTERVIEW"
    r"|PRESENTATION"
    r"|PROCLAMATION"
    r"|SWEARING[- ]IN"
    r"|OATH OF OFFICE"
    r")"
)

# Page-break / running-header artifacts to discard inside a section.
RE_PAGE_HEADER = re.compile(r"^\s*MINUTES OF COUNCIL", re.I)
RE_PAGE_NUM = re.compile(r"^\s*-?\s*\d+\s*-?\s*$")
RE_DASH_PAGE = re.compile(r"^\s*-\d+-\s*$")

# ----------------------------------------------------------------------------
# Speaker detection
# ----------------------------------------------------------------------------

# A paragraph that starts a new speaker's comment begins with a personal name.
# Names look like:  "Jim Vesock stated ...", "Cheryl Soderborg, a resident, ...",
# "Mike Rigdon expressed ...", "Lance, a longtime resident ...".
# Capture the leading name (1-4 capitalized tokens), allowing a trailing comma
# clause or a reporting verb.
NAME_TOKEN = r"[A-Z][A-Za-z'\.\-]+"
RE_SPEAKER = re.compile(
    r"^(?P<name>" + NAME_TOKEN + r"(?:\s+" + NAME_TOKEN + r"){0,3})"
    r"(?P<rest>(?:,| ).*)$",
    re.S,
)

# Reporting verbs that confirm the leading tokens are a speaker name (used to
# validate a one-word name like "Lance ...").
REPORT_VERBS = (
    "stated", "expressed", "asked", "addressed", "spoke", "requested",
    "encouraged", "commented", "provided", "introduced", "thanked", "said",
    "noted", "raised", "discussed", "shared", "explained", "indicated",
    "congratulated", "informed", "reported", "presented", "wanted", "voiced",
    "questioned", "urged", "suggested", "described", "mentioned", "complained",
    "read", "gave", "began", "approached", "came", "appeared", "representing",
)

# Speakers who are NOT public (council / mayor / staff). Drop these even though
# they appear inside the section (the newer layout interleaves council/staff
# responses with no sub-heading).
RE_OFFICIAL_PREFIX = re.compile(
    r"^(Mayor|Councilmember|Councilman|Councilwoman|Council Member|"
    r"Mayor Pro Tem|Vice Mayor|County Councilmember|"
    r"City Manager|City Recorder|City Attorney|Assistant City Manager|"
    r"Acting City|Deputy City|Police Chief|Fire Chief|Finance Director|"
    r"CED Director|CPD Director|Public Works Director|City Engineer|"
    r"Strategic Communications Director|Representative|Senator|Commissioner)\b",
    re.I,
)
# Staff: "Name, City Manager", "Name, City Attorney", "Name, ... Director", etc.
RE_STAFF_TITLE = re.compile(
    r",\s*(City Manager|City Recorder|City Attorney|Assistant City Manager|"
    r"Acting [A-Z]|General Counsel|Police Chief|Fire Chief|Finance Director|"
    r"CED Director|CPD Director|Public Works Director|"
    r"Parks and Recreation Director|Strategic Communications Director|"
    r"IT Director|Deputy City|Director of|City Engineer|Budget Officer|"
    r"Human Resources)",
)

EMPTY_MARKERS = {"n/a", "na", "none", "-", ""}

# Org / place words that, when they appear inside a candidate "name", mark it as
# a continuation fragment (e.g. "Valley Performing Arts Center") rather than a
# person.
NON_PERSON_WORDS = {
    "center", "city", "arts", "department", "performing", "council",
    "committee", "board", "commission", "association", "school", "church",
    "company", "llc", "inc", "district", "valley", "county", "state",
    "office", "division", "library", "academy", "university", "college",
    "foundation", "coalition", "corporation", "services", "authority",
    "boulevard", "street", "avenue", "road", "drive", "lane", "circle",
    "way", "court", "place", "blvd", "neighborhood",
}

# Anonymous public speaker openers (minutes sometimes don't name the speaker).
RE_ANON_SPEAKER = re.compile(
    r"^(A resident|An? unidentified [a-z]+|A speaker|A member of the public|"
    r"A citizen|A community member|Speaker\s*\d+|An? individual)\b",
    re.I,
)
# But "The speaker"/"The comments" mid-thread is a continuation, not a new one,
# unless it's clearly the very first paragraph (handled by adjacency below).

# ----------------------------------------------------------------------------


def normalize_ws(text):
    """Collapse internal whitespace/newlines into single spaces, trim."""
    return re.sub(r"\s+", " ", text).strip()


def meeting_date_from_path(path):
    """Filename is <date>_<slug>.md; date is the meeting date (ISO)."""
    base = os.path.basename(path)
    m = re.match(r"(\d{4}-\d{2}-\d{2})_", base)
    return m.group(1) if m else ""


def extract_section(lines):
    """Return the list of raw lines that make up the public-comment section,
    or None if no section found."""
    start = None
    mode = None
    for i, ln in enumerate(lines):
        if RE_START_NEW.match(ln):
            start = i + 1
            mode = "new"
            break
        if RE_START_OLD.match(ln):
            start = i + 1
            mode = "old"
            break
    if start is None:
        return None, None

    # If a sub-header line (e.g. "A.  PUBLIC COMMENTS") immediately follows the
    # "PUBLIC COMMENT PERIOD" line, skip it so its text doesn't leak into the
    # first speaker paragraph.
    while start < len(lines):
        s = lines[start]
        if s.strip() == "" or RE_START_OLD.match(s) or RE_START_NEW.match(s):
            start += 1
        else:
            break

    body = []
    for ln in lines[start:]:
        if RE_END.match(ln):
            break
        body.append(ln)
    return body, mode


def clean_section_lines(body):
    """Strip page headers/numbers, return cleaned lines."""
    out = []
    for ln in body:
        if RE_PAGE_HEADER.match(ln):
            continue
        if RE_DASH_PAGE.match(ln):
            continue
        if RE_PAGE_NUM.match(ln):
            continue
        out.append(ln.rstrip())
    return out


def split_paragraphs(lines):
    """Split section lines into paragraphs on blank lines."""
    paras = []
    cur = []
    for ln in lines:
        if ln.strip() == "":
            if cur:
                paras.append("\n".join(cur))
                cur = []
        else:
            cur.append(ln)
    if cur:
        paras.append("\n".join(cur))
    return paras


def is_official(name, para_norm):
    if RE_OFFICIAL_PREFIX.match(name):
        return True
    # staff title appears right after the name
    head = para_norm[:120]
    if RE_STAFF_TITLE.search(head):
        return True
    return False


def looks_like_speaker(name, rest):
    """Validate a candidate name. Accept multi-word capitalized names, or a
    single-word name immediately followed by a recognized reporting verb /
    descriptive comma-clause."""
    tokens = name.split()
    rest_l = rest.lstrip(", ").lower()
    first_word = rest_l.split()[0] if rest_l.split() else ""
    starts_with_verb = first_word in REPORT_VERBS
    starts_with_clause = rest.lstrip().startswith(",")  # "Lance, a resident,"
    if len(tokens) >= 2:
        # Two+ capitalized tokens: a name. Require either a verb, a comma
        # clause, or 'of'/'a'/'an'/'with' (address/affiliation) to avoid
        # catching stray ALL-CAPS-ish phrases.
        if starts_with_verb or starts_with_clause or first_word in (
            "of", "a", "an", "with", "from", "who", "and"
        ):
            return True
        # Otherwise still accept a clean 2-3 token name + space + lowercase word
        return first_word.islower()
    # single token name -> require a verb or descriptive comma clause
    return starts_with_verb or starts_with_clause


def detect_district(text):
    m = re.search(r"\bDistrict\s+([1-4])\b", text)
    return f"District {m.group(1)}" if m else ""


def parse_file(path):
    """Return (rows, dropped, had_section) for one minutes file."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()
    lines = raw.splitlines()

    body, mode = extract_section(lines)
    rel = os.path.relpath(path, REPO)
    if body is None:
        return [], [], False

    cleaned = clean_section_lines(body)
    paras = split_paragraphs(cleaned)

    mdate = meeting_date_from_path(path)
    rows = []
    dropped = []
    last_row = None        # the most recent accepted public-comment row
    last_was_official = False  # last paragraph was a council/staff speaker

    for para in paras:
        norm = normalize_ws(para)
        if not norm:
            continue
        low = norm.lower()

        # empty / placeholder markers
        if low in EMPTY_MARKERS or low.rstrip(".") in EMPTY_MARKERS:
            dropped.append((mdate, "", norm, rel, "empty_placeholder"))
            continue
        # procedural "no comments" statements for the period as a whole
        if re.match(
            r"^(there (were|was)\s+no|no (public )?comment|none (were|was)|"
            r"no one (came|appeared|signed|wished|was present|spoke)|"
            r"upon inquiry,? there (were|was) no (members|one)|"
            r"upon inquiry,? no (members|one))",
            low,
        ):
            dropped.append((mdate, "", norm, rel, "no_comments_procedural"))
            last_row = None
            last_was_official = False
            continue

        # anonymous public speaker (no name given in minutes)
        anon = RE_ANON_SPEAKER.match(norm)

        m = RE_SPEAKER.match(norm)
        valid_speaker = False
        name = ""
        if anon and not (last_row is not None and not last_was_official
                         and re.match(r"^The (speaker|comments|remarks)\b",
                                      norm, re.I)):
            # Emit as a named-but-anonymous public comment.
            district = detect_district(norm)
            flags = ["no_name"]
            if len(norm) < 60:
                flags.append("short_comment")
            row = {
                "date": mdate, "contact_name": "", "subject": "", "topic": "",
                "comment": norm, "district": district, "source": SOURCE,
                "has_attachment": "False", "source_file": rel,
                "page_numbers": "", "period_start": mdate, "period_end": mdate,
                "date_normalized": mdate, "quality_flag": "|".join(flags),
            }
            rows.append(row)
            last_row = row
            last_was_official = False
            continue

        if m:
            name = m.group("name").strip().rstrip(",")
            rest = m.group("rest")
            ntoks = name.split()
            non_name = ntoks[0] in (
                "The", "He", "She", "It", "They", "Mr", "Mrs", "Ms", "Dr",
                "Upon", "Following", "After", "A", "An", "There", "This",
                "These", "Members", "With", "Although", "While", "When",
                "As", "In", "On", "At", "Several", "Many", "Other", "Their",
                "His", "Her", "Both", "One", "Each", "Some", "All",
            )
            # A token ending in a period that isn't a short initial
            # (e.g. "Way.", "Blvd.", "Street.") signals a mid-sentence
            # continuation split by a page break, not a real name.
            mid_sentence = any(
                t.endswith(".") and len(t.rstrip(".")) >= 3
                for t in ntoks
            )
            non_person = any(
                t.lower().strip(".,") in NON_PERSON_WORDS for t in ntoks
            )
            valid_speaker = (not non_name and not mid_sentence
                             and not non_person
                             and looks_like_speaker(name, rest))

        if not valid_speaker:
            # Not a new speaker. Treat as a continuation of the previous
            # paragraph (page break split a speaker's comment). Append it to
            # the last accepted row; if the previous paragraph was an official
            # /staff speaker, the continuation belongs to them -> drop it.
            if last_row is not None and not last_was_official:
                last_row["comment"] = last_row["comment"] + " " + norm
                d = detect_district(norm)
                if d and not last_row["district"]:
                    last_row["district"] = d
            else:
                reason = "official_continuation" if last_was_official \
                    else "orphan_continuation"
                dropped.append((mdate, name, norm, rel, reason))
            continue

        # We have a new, validated speaker. Is it council / mayor / staff?
        if is_official(name, norm):
            dropped.append((mdate, name, norm, rel, "official_or_staff"))
            last_row = None
            last_was_official = True
            continue

        district = detect_district(norm)
        flags = []
        if len(norm) < 60:
            flags.append("short_comment")

        row = {
            "date": mdate,
            "contact_name": name,
            "subject": "",
            "topic": "",
            "comment": norm,
            "district": district,
            "source": SOURCE,
            "has_attachment": "False",
            "source_file": rel,
            "page_numbers": "",
            "period_start": mdate,
            "period_end": mdate,
            "date_normalized": mdate,
            "quality_flag": "|".join(flags),
        }
        rows.append(row)
        last_row = row
        last_was_official = False

    # finalize short-comment flag after continuation merges (preserve others)
    for r in rows:
        flags = [f for f in r["quality_flag"].split("|")
                 if f and f != "short_comment"]
        if len(r["comment"]) < 60:
            flags.append("short_comment")
        r["quality_flag"] = "|".join(flags)

    return rows, dropped, True


def main():
    files = sorted(glob.glob(MINUTES_GLOB))
    all_rows = []
    all_dropped = []
    meetings_scanned = 0
    meetings_with_section = 0
    meetings_with_comments = set()

    for path in files:
        meetings_scanned += 1
        rows, dropped, had = parse_file(path)
        if had:
            meetings_with_section += 1
        if rows:
            meetings_with_comments.add(path)
        all_rows.extend(rows)
        all_dropped.extend(dropped)

    # write clean
    with open(CLEAN_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=SCHEMA)
        w.writeheader()
        for r in all_rows:
            w.writerow(r)

    # write dropped
    with open(DROPPED_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "contact_name", "comment", "source_file", "_drop_reason"])
        for d in all_dropped:
            w.writerow(d)

    # summary to stdout
    by_year = {}
    total_len = 0
    for r in all_rows:
        y = r["date"][:4]
        by_year[y] = by_year.get(y, 0) + 1
        total_len += len(r["comment"])
    avg_len = round(total_len / len(all_rows), 1) if all_rows else 0

    print(f"meetings_scanned: {meetings_scanned}")
    print(f"meetings_with_comment_section: {meetings_with_section}")
    print(f"meetings_with_comments: {len(meetings_with_comments)}")
    print(f"comments_extracted: {len(all_rows)}")
    print(f"dropped_rows: {len(all_dropped)}")
    print(f"avg_comment_len: {avg_len}")
    print(f"by_year: {dict(sorted(by_year.items()))}")
    drop_reasons = {}
    for d in all_dropped:
        drop_reasons[d[4]] = drop_reasons.get(d[4], 0) + 1
    print(f"drop_reasons: {dict(sorted(drop_reasons.items()))}")


if __name__ == "__main__":
    main()
