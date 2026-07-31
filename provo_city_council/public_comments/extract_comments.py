#!/usr/bin/env python3
"""
Extract public comments from Provo Municipal Council Regular Meeting minutes.

PRIMARY (and effectively only available) source: source #1 in recon.md ---
"in_person_minutes": the public-comment portion of each Council Regular Meeting
is transcribed/summarized by speaker in the OnBase minutes PDFs (already on disk
as markdown). These are STAFF SUMMARIES of in-person/online verbal comment, not
verbatim resident text. Set source = "in_person_minutes".

source #2 (OpenGov Open City Hall, portal slug "provout") returned HTTP 404 /
"Server Error" to every access pattern tried (plain fetch, browser UA, the
opentownhall.com + OpenCityHall.provo.org aliases, /api/, /topics, /embed/);
it is a JS SPA whose backend rejects the slug without a headless browser
session. No rows obtained -- documented in CLAUDE.md.

source #3 (agenda-packet PDFs, documentType=5) -- not downloaded here (the
packets are remote URLs only; packet_url column points to agendas.provo.gov).
Best-effort secondary, out of scope for this pass; noted as a gap.

Output (SLC schema):
  public_comments/all_comments_clean.csv
  public_comments/all_comments_dropped.csv  (every removed row + _drop_reason)

Resumable in spirit: deterministic, re-runnable over the same minutes tree.
"""

import csv
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # the provo_city_council repo root
MIN_DIR = REPO / "meeting_minutes" / "minutes"
OUT_CLEAN = REPO / "public_comments" / "all_comments_clean.csv"
OUT_DROP = REPO / "public_comments" / "all_comments_dropped.csv"

FIELDS = [
    "date", "contact_name", "subject", "topic", "comment", "district",
    "source", "has_attachment", "source_file", "page_numbers",
    "period_start", "period_end", "date_normalized", "quality_flag",
]

# ---- Known council members / titles to EXCLUDE as speakers (council & staff) ----
# Built from rosters appearing in 2020-2026 Provo minutes. Used to drop
# council/staff dialogue paragraphs that resemble a comment paragraph.
COUNCIL_SURNAMES = {
    "ellsworth", "fillmore", "handley", "harding", "hoban", "sewell",
    "shipley", "mackay", "whipple", "kaufusi", "christensen", "garrett",
    "bogdin", "whitlock", "sawyer", "stewart", "winterton",
}
# Common staff / officer names + titles seen introducing items
STAFF_TITLE_HINTS = (
    "council attorney", "executive director", "chief administrative",
    "deputy", "city engineer", "city recorder", "budget officer",
    "neighborhood program", "council staff", "assistant", "director of",
    "planner", "fire chief", "police chief", "city attorney",
    "community development", "public works", "finance",
)

LINE_TITLE_PREFIXES = (
    "chair ", "vice-chair ", "vice chair ", "mayor ", "councilor ",
    "council chair", "council vice", "mr. ", "ms. ", "mrs. ", "dr. ",
)

# Page-footer / boilerplate noise to ignore entirely
NOISE_RE = re.compile(
    r"(provo city .*council meeting|provo city municipal council|please note|"
    r"electronic version of minutes|page \d+ of \d+|opening ceremony|roll call|"
    r"pledge of allegiance|prayer\b|moment of silence)",
    re.I,
)

# Section / boundary markers that END a public-comment block
END_BLOCK_RE = re.compile(
    r"(closed (the )?public comment|closed public comment|"
    r"invited (a )?council discussion|brought the discussion back|"
    r"called for a vote|with (no|none)|there were no other comments|"
    r"there were no (further |other )?public comments|"
    r"^\s*motion:|^\s*vote:|^\s*action agenda|^\s*adjournment|"
    r"^\s*\d+\.\s|^\s*redevelopment agency|council discussion resumed|"
    r"resumed the council discussion|continued the council discussion)",
    re.I,
)

# Lines that OPEN a public-comment block
OPEN_RE = re.compile(
    r"(opened (the )?public comment|opened public comment|"
    r"opened the item for public comment|"
    r"read the public comment preamble|read the preamble for public comment)",
    re.I,
)

# Non-person leading words that mark agenda-section headers, not speaker names.
SECTION_STOPWORDS = {
    "public", "presentations", "proclamations", "approval", "action",
    "agenda", "redevelopment", "neighborhood", "spotlight", "minutes",
    "consent", "business", "adjournment", "recess", "opening", "ceremony",
    "roll", "prayer", "pledge", "motion", "vote", "resolution", "ordinance",
    "an", "the", "a", "council", "mayor", "chair", "councilor",
}

# A speaker-comment paragraph: "Name, <loc/org>, <text>" or "Name of <loc/org> <text>"
# Name = 1-4 capitalized tokens (allowing hyphen/apostrophe), then a connector.
SPEAKER_RE = re.compile(
    r"^(?P<name>[A-Z][A-Za-z'\.\-]+(?:\s+[A-Z][A-Za-z'\.\-]+){0,3})"
    r"(?P<conn>\s*,\s*|\s+of\s+|\s+from\s+)"
    r"(?P<rest>.+)$",
    re.S,
)

# Connectors that signal council/staff procedural narration rather than a comment
NARRATION_VERBS = re.compile(
    r"^(said|asked|noted|explained|stated|opened|closed|called|read|"
    r"invited|brought|presented|provided|thanked the council|made a motion|"
    r"seconded|nominated|responded|answered|reviewed|deliberated|wondered|"
    r"reiterated|addressed|appreciated|discussed|inquired|acknowledged|"
    r"pointed out|jokingly|later|argued|agreed|shared his vision)",
    re.I,
)


def normalize_ws(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_council_or_staff(name: str, rest: str) -> bool:
    toks = re.findall(r"[A-Za-z'\-]+", name.lower())
    if not toks:
        return True
    surname = toks[-1]
    if surname in COUNCIL_SURNAMES:
        return True
    # leading "Councilor/Chair/Mayor" already stripped by prefix filter, but
    # double-check title-cased single-name council refs
    if len(toks) == 1 and toks[0] in COUNCIL_SURNAMES:
        return True
    low = (name + " " + rest).lower()
    if any(h in low for h in STAFF_TITLE_HINTS):
        return True
    return False


def split_location(rest: str):
    """From the post-name portion, peel off a short location/org then comment."""
    rest = rest.strip()
    # Strip a leading connector left over from "Name, of Provo, ..." / "Name, from ..."
    rest = re.sub(r"^(of|from|representing|a resident of|with)\s+", "", rest,
                  flags=re.I).strip()
    # If "of Provo, said ..." -> location 'Provo'
    m = re.match(r"^(?P<loc>[A-Z][A-Za-z'\.\- ]{0,40}?)\s*,\s*(?P<txt>.+)$",
                 rest, re.S)
    if m and len(m.group("loc")) <= 45:
        return normalize_ws(m.group("loc")), normalize_ws(m.group("txt"))
    # "Provo said ..." (of/from connector case): grab first 1-4 words as loc
    words = rest.split()
    # take up to first verb as location
    loc_words = []
    txt_words = list(words)
    for i, w in enumerate(words):
        if NARRATION_VERBS.match(w) or w[0].islower():
            txt_words = words[i:]
            break
        loc_words.append(w)
        if len(loc_words) >= 5:
            txt_words = words[i + 1:]
            break
    loc = normalize_ws(" ".join(loc_words))
    txt = normalize_ws(" ".join(txt_words))
    if not txt:  # everything got eaten as loc -> treat all as comment
        return "", normalize_ws(rest)
    return loc, txt


DISTRICT_RE = re.compile(r"\bdistrict\s+(\d)\b", re.I)


def extract_district(text: str):
    m = DISTRICT_RE.search(text)
    return m.group(1) if m else ""


# strip trailing video timestamp like "(0:24:53)" or "0:24:53"
TS_RE = re.compile(r"\(?\b\d{1,2}:\d{2}:\d{2}\b\)?\.?\s*$")


def clean_comment_text(text: str) -> str:
    text = TS_RE.sub("", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_file(path: Path, rows: list, dropped: list):
    raw = path.read_text(encoding="utf-8", errors="replace")
    # meeting date from filename: YYYY-MM-DD_...
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", path.name)
    date_iso = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
    source_file = str(path.relative_to(REPO))

    # Split into paragraphs (blank-line separated), preserving order.
    # First de-hyphenate page-break boilerplate by dropping noise lines.
    lines = raw.split("\n")
    paras = []
    buf = []
    for ln in lines:
        if ln.strip() == "":
            if buf:
                paras.append(" ".join(buf).strip())
                buf = []
            continue
        if NOISE_RE.search(ln):
            # boilerplate footer -> paragraph break, skip the line
            if buf:
                paras.append(" ".join(buf).strip())
                buf = []
            continue
        buf.append(ln.strip())
    if buf:
        paras.append(" ".join(buf).strip())

    in_block = False
    current_subject = ""  # nearest preceding agenda item text
    item_re = re.compile(r"^\s*(\d+)\.\s+(.*)$")

    for para in paras:
        if not para:
            continue
        # Track agenda item headers to use as 'subject'
        im = item_re.match(para)
        if im:
            current_subject = normalize_ws(im.group(2))[:200]

        if OPEN_RE.search(para):
            in_block = True
            # the open line itself is not a comment
            continue

        if not in_block:
            continue

        # End the block?
        if END_BLOCK_RE.search(para):
            in_block = False
            continue

        # Inside a block: is this a resident comment paragraph?
        # Drop council/staff narration up front.
        low_start = para.lower()
        if low_start.startswith(LINE_TITLE_PREFIXES):
            continue

        sm = SPEAKER_RE.match(para)
        if not sm:
            # not a recognizable speaker para; likely narration -> skip silently
            continue

        name = normalize_ws(sm.group("name"))
        rest = sm.group("rest")

        # Reject agenda-section headers masquerading as "Name, rest"
        # (e.g. "Public Comment from Neighborhood Chairs:", "Approval of Minutes",
        # "Presentations, Proclamations, and Awards").
        first_word = re.split(r"[\s,]", name.lower(), 1)[0]
        if first_word in SECTION_STOPWORDS:
            continue
        if rest.rstrip().endswith(":"):
            continue

        # If the "rest" begins with a narration verb right after name+comma,
        # this is council/staff narration ("Mr. Harding asked ...") -> skip.
        if NARRATION_VERBS.match(rest.strip()):
            continue

        if is_council_or_staff(name, rest):
            continue

        loc, comment = split_location(rest)
        comment = clean_comment_text(comment)
        loc = re.sub(r"[,\.]$", "", loc).strip()

        district = extract_district(loc) or extract_district(comment)

        if not comment:
            dropped.append({
                "date": date_iso, "contact_name": name, "comment": "",
                "source_file": source_file, "_drop_reason": "empty_comment",
            })
            continue

        # quality flags
        flags = []
        if len(comment) < 25:
            flags.append("short_comment")
        if not name or len(name.split()) < 2:
            flags.append("no_name")

        rows.append({
            "date": date_iso,
            "contact_name": name,
            "subject": current_subject,
            "topic": "",
            "comment": comment,
            "district": district,
            "source": "in_person_minutes",
            "has_attachment": "False",
            "source_file": source_file,
            "page_numbers": "",
            "period_start": date_iso,
            "period_end": date_iso,
            "date_normalized": date_iso,
            "quality_flag": "|".join(flags),
        })


def main():
    reg_files = sorted(MIN_DIR.glob("**/*regular*.md"))
    rows, dropped = [], []
    meetings_with = set()
    for f in reg_files:
        before = len(rows)
        parse_file(f, rows, dropped)
        if len(rows) > before:
            meetings_with.add(f.name)

    # de-dup exact (date, name, comment)
    seen = set()
    deduped = []
    for r in rows:
        key = (r["date"], r["contact_name"].lower(), r["comment"][:120].lower())
        if key in seen:
            dropped.append({
                "date": r["date"], "contact_name": r["contact_name"],
                "comment": r["comment"], "source_file": r["source_file"],
                "_drop_reason": "duplicate",
            })
            continue
        seen.add(key)
        deduped.append(r)
    rows = deduped

    with OUT_CLEAN.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    drop_fields = ["date", "contact_name", "comment", "source_file", "_drop_reason"]
    with OUT_DROP.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=drop_fields)
        w.writeheader()
        for d in dropped:
            w.writerow({k: d.get(k, "") for k in drop_fields})

    by_year = {}
    for r in rows:
        y = r["date"][:4]
        by_year[y] = by_year.get(y, 0) + 1

    print(f"regular_meetings_scanned={len(reg_files)}")
    print(f"comments={len(rows)}")
    print(f"meetings_with_comments={len(meetings_with)}")
    print(f"dropped={len(dropped)}")
    print(f"by_year={dict(sorted(by_year.items()))}")


if __name__ == "__main__":
    sys.exit(main())
