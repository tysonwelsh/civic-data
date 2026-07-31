#!/usr/bin/env python3
"""
Extract IN-PERSON public-comment SPEAKERS from Nephi (UT) council meeting minutes.

IMPORTANT: these are clerk PARAPHRASES of in-person speakers recorded in the
meeting minutes -- MEETING-RECORD NOTES, not genuine public-submitted written
comments. They do NOT belong in all_comments_clean.csv (which stays header-only
for Nephi -- the city publishes no genuine written/online public comments; see
AVAILABILITY.md). This script produces public_comments/minutes_speaker_log.csv only.

Nephi minutes format (verified on the born-digital 2020-2025 minutes .md files):
  - Section headers are FLUSH-LEFT ALL-CAPS lines ending in ":", e.g.
    "PUBLIC COMMENT:", "BRYCE'S LANDING COMMERCIAL SUBDIVISION FINAL PLAT TABLED:".
  - Inside "PUBLIC COMMENT:" each speaker is an INDENTED paragraph; wrapped
    continuation lines are flush-left mixed-case prose.
  - Most meetings record "NO PUBLIC COMMENT" or "There was no public comment." -> 0 rows.
  - Some comments appear inline under a hearing: "Mayor X opened the meeting up for
    public comment. <Name> addressed the council about ..." -> handled via inline trigger.
  - City staff/council responses inside the section (City Attorney/Recorder/
    Administrator, Mayor, Councilor ...) are EXCLUDED -- only members of the public.

Method (deterministic, verbatim, no fabrication):
  1. Walk lines; ALL-CAPS ":" lines are section headers and set the current section.
     Indented lines start a new paragraph; flush-left mixed-case lines continue it.
  2. A paragraph is "public-comment context" if it is under a PUBLIC COMMENT/HEARING/
     INPUT header, OR it contains an inline "...public comment" trigger (in which case
     the text after the trigger is processed).
  3. Emit a row only when the paragraph STARTS with a clearly-named member of the
     public (2-3 capitalized words, not a staff/council title) AND the remainder shows
     a speaking verb or residency phrase. comment = the paragraph verbatim.
  4. date_normalized parsed from the file path (YYYY-MM-DD).
"""
import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MIN_DIR = BASE / "meeting_minutes" / "minutes"
OUT = Path(__file__).resolve().parent / "minutes_speaker_log.csv"

# FLUSH-LEFT ALL-CAPS header line (no colon, whole line is the header).
CAPS_HEADER = re.compile(r"^[A-Z0-9][A-Z0-9 ,'’/&\-\(\)\.\$]{3,}\s*$")
# Inline header: an ALL-CAPS phrase ending in ":" possibly followed by body text on
# the same line (the PDF->md flatten sometimes joins "PLEDGE OF ALLEGIANCE: Jodie Cox
# led ..." or "PUBLIC COMMENT: <name> ..."). Group 1 = header, group 2 = trailing body.
INLINE_HEADER = re.compile(r"^\s*([A-Z0-9][A-Z0-9 ,'’/&\-\(\)\.\$]{2,}?):\s*(.*)$")
PC_HEADER = re.compile(r"PUBLIC\s+(COMMENT|HEARING|INPUT)")

# Inline trigger: "(re)opened/opened the meeting up/floor to|for|up for public comment"
INLINE_TRIGGER = re.compile(
    r"(?:open(?:ed)?|reopen(?:ed)?|turn(?:ed)?|time)\b[^.]*?public\s+comment[\.\:]\s*",
    re.I)

NO_COMMENT = re.compile(
    r"no public comment|there (?:were|was) no public comment|no one (?:came forward|"
    r"spoke|wished|was present)|hearing none|no comments? (?:were|was) (?:given|made|"
    r"received|offered)|no one signed up|received no public comment", re.I)

# Name = 2-3 capitalized words (allows a middle initial like "Justin D. Seely",
# initials like "JR Johnson", hyphen/apostrophe surnames).
NAME = r"[A-Z][A-Za-z’'\-]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][A-Za-z’'\-]+){1,2}"

# A speaking verb or residency phrase that confirms the leading name is a speaker.
SPEAK = re.compile(
    r"\b(commented|stated|expressed|asked|spoke|said|inquired|thanked|requested|"
    r"raised|noted|shared|introduced|addressed|mentioned|voiced|presented|wanted|"
    r"encouraged|described|read|provided|approached|complained|objected|opposed|"
    r"supported|urged|explained|reported|told|wondered|questioned|suggested|"
    r"recommended|felt|believe[sd]?|came\s+forward|stepped\s+forward|representing|"
    r"is\s+a\s+resident|who\s+is\s+a\s+resident|resident\s+of|residing|living\s+(?:at|in|on)|"
    r"on\s+behalf\s+of)\b", re.I)

# First word (lowercased) of a paragraph that means it is NOT a member of the public
# speaking during comment -- titles, body officials, sentence-lead pronouns, and the
# leading word of common non-speaker lines. Checked case-insensitively.
STOP_FIRST = {w.lower() for w in {
    "Mayor", "Council", "Councilor", "Councilmember", "Councilwoman", "Councilman",
    "Public", "City", "Nephi", "Motion", "Staff", "Page", "Mr", "Ms", "Mrs", "Dr",
    "The", "Administrator", "Recorder", "Attorney", "Chief", "Sergeant", "Sgt",
    "Lieutenant", "Lt", "Captain", "Officer", "Detective", "Director", "County",
    "There", "All", "Those", "Guests", "Pledge", "It", "He", "She", "They", "We",
    "Recreation", "Library", "Police", "Fire", "Finance", "Power", "Water", "Sewer",
    "Building", "Planning", "Treasurer", "Engineer", "Superintendent", "Deputy",
    "Representative", "Senator", "Sheriff", "Judge", "Reverend", "Pastor", "Bishop",
    "Coordinator", "Manager", "Supervisor", "Foreman", "Clerk", "Juab", "School",
    "Principal", "Commissioner", "Commission", "President", "Vice", "Board", "State",
}}

# Exact full names that are city staff/officials (they regularly appear name-first,
# without a title, presenting staff business -- not public commenters). Excluded.
STAFF_NAMES = {n.lower() for n in {
    "Seth Atkinson",        # City Administrator
    "Glenn Greenhalgh",     # Planning Administrator
    "Kasey Wright",         # City Attorney
    "Lisa Brough",          # City Recorder
}}


def parse_date(path: Path):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(path))
    return m.group(1) if m else ""


def iter_context_paragraphs(text):
    """Yield (paragraph_text, in_pc_section) across the document."""
    cur, in_pc = [], False
    section_is_pc = False

    def flush():
        nonlocal cur
        if cur:
            p = " ".join(s.strip() for s in cur).strip()
            cur = []
            if p:
                return p
        cur = []
        return None

    for raw in text.splitlines():
        line = raw.rstrip()
        if line.strip() == "":
            p = flush()
            if p:
                yield p, section_is_pc
            continue
        if re.match(r"^\s*Page \d+ of", line):
            continue
        # Pure flush-left ALL-CAPS header (no colon, whole line is the header).
        if CAPS_HEADER.match(line) and len(line.strip()) >= 4:
            p = flush()
            if p:
                yield p, section_is_pc
            section_is_pc = bool(PC_HEADER.search(line))
            continue
        # Inline header "ALLCAPS: body" -> set section from the header, then treat any
        # trailing body as a fresh paragraph in the NEW section context.
        hm = INLINE_HEADER.match(line)
        if hm and len(hm.group(1).strip()) >= 3:
            p = flush()
            if p:
                yield p, section_is_pc
            section_is_pc = bool(PC_HEADER.search(hm.group(1)))
            body = hm.group(2).strip()
            if body:
                cur = [body]
            continue
        if re.match(r"^\s+\S", line):           # indented -> new paragraph
            p = flush()
            if p:
                yield p, section_is_pc
            cur = [line]
        else:                                     # flush-left prose -> continuation
            cur.append(line)
    p = flush()
    if p:
        yield p, section_is_pc


# Abbreviation/initial periods to neutralize so they don't look like sentence ends.
ABBR = re.compile(r"\b(Jr|Sr|Dr|Mr|Mrs|Ms|St|Ave|Inc|Co|Rd|[A-Z])\.")


def first_sentence(rest):
    r = rest.lstrip(" .,-—\t")
    r = ABBR.sub(lambda m: m.group(1), r)      # drop abbreviation periods
    m = re.search(r"[.!?]", r)
    return r[:m.start()] if m else r


def speaker_from(para):
    m = re.match(r"\s*(" + NAME + r")\b", para)
    if not m:
        return None
    name = m.group(1).strip().rstrip(",.").strip()
    parts = name.split()
    if not parts or len(parts) < 2:
        return None
    if parts[0].lower() in STOP_FIRST:
        return None
    if name.lower() in STAFF_NAMES:
        return None
    # The speaking verb / residency phrase must appear in the speaker's OWN first
    # sentence -- not in a later sentence about someone else (avoids capturing a
    # council member whose name leads a paragraph that quotes a verb downstream).
    if not SPEAK.search(first_sentence(para[m.end():])):
        return None
    return name


def main():
    if not MIN_DIR.exists():
        print(f"NOTE: {MIN_DIR} missing -- minutes not acquired; speaker log left header-only.")
        return
    files = sorted(MIN_DIR.glob("**/*.md"))
    rows = []
    for f in files:
        text = f.read_text(errors="ignore")
        date = parse_date(f)
        rel = str(f.relative_to(BASE))
        seen = set()
        for para, in_pc in iter_context_paragraphs(text):
            candidates = []
            if in_pc:
                candidates.append(para)
            for tm in INLINE_TRIGGER.finditer(para):
                tail = para[tm.end():].strip()
                if tail:
                    candidates.append(tail)
            for cand in candidates:
                if NO_COMMENT.search(cand) and len(cand) < 200:
                    continue
                nm = speaker_from(cand)
                if not nm:
                    continue
                key = (date, nm.lower())
                if key in seen:
                    continue
                seen.add(key)
                topic = cand[:120].rstrip()
                rows.append({
                    "date_normalized": date,
                    "contact_name": nm,
                    "subject": topic,
                    "topic": topic,
                    "comment": cand.strip(),
                    "source": "in_person_minutes",
                    "source_file": rel,
                    "quality_flag": "clerk_paraphrase_not_written_comment",
                })

    rows.sort(key=lambda r: (r["date_normalized"], r["contact_name"]))

    with OUT.open("w", newline="") as fh:
        fh.write("# MEETING-RECORD NOTES, NOT public-submitted written comments. "
                 "These rows are clerk PARAPHRASES of in-person speakers recorded in "
                 "the Nephi council minutes (NOT residents' own published text). They "
                 "are kept separate from all_comments_clean.csv per extraction_standards.md.\n")
        w = csv.DictWriter(fh, fieldnames=[
            "date_normalized", "contact_name", "subject", "topic",
            "comment", "source", "source_file", "quality_flag"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"files scanned: {len(files)}")
    print(f"speaker rows extracted: {len(rows)}")


if __name__ == "__main__":
    main()
