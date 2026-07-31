#!/usr/bin/env python3
"""
Extract IN-PERSON public-comment SPEAKERS from Vineyard council meeting minutes.

IMPORTANT: these are clerk PARAPHRASES of in-person speakers recorded in the
meeting minutes — MEETING-RECORD NOTES, not genuine public-submitted written
comments. They do NOT belong in all_comments_clean.csv (which stays header-only).
This produces public_comments/minutes_speaker_log.csv only.

Method (deterministic, no fabrication):
  1. For each minutes .md, isolate the PUBLIC COMMENT(S) section: from a line that
     is a numbered "N. PUBLIC COMMENT(S)" header to the next numbered section header.
  2. Within that block, split into paragraphs and detect speaker-introducing
     sentences. We only emit a row when a person is clearly named as a speaker.
  3. contact_name = the detected speaker; comment/topic = the paraphrase text of that
     speaker's paragraph (trimmed). subject mirrors a short topic.
  4. date_normalized = the meeting date parsed from the filename (YYYY-MM-DD prefix).

We DO NOT invent speakers. Sections that say "no public comment"/"hearing none" yield
zero rows. Ambiguous prose that names no speaker yields zero rows for that block.
"""
import csv
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MIN_DIR = BASE / "meeting_minutes" / "minutes"
OUT = Path(__file__).resolve().parent / "minutes_speaker_log.csv"

# A numbered section header line, e.g. "3. PUBLIC COMMENTS" or "6.  PUBLIC COMMENT (3 MINUTES)"
SEC_HEADER = re.compile(r'^\s*(\d+)\.\s+([A-Z][A-Z0-9 ,\'’/&\-\(\)\.]+?)\s*$')
PC_HEADER = re.compile(r'^\s*\d+\.\s+PUBLIC\s+COMMENT', re.I)

# "Hearing none" / no-comment markers
NO_COMMENT = re.compile(
    r'hearing none|no public comment|no one (?:came forward|spoke|wished)|'
    r'there (?:were|was) no public comment|no comments? (?:were|was) (?:given|made|received)|'
    r'no one signed up', re.I)

# Speaker-introduction patterns. Each captures a NAME group.
# We require a capitalized first+last name to reduce false positives.
NAME = r"([A-Z][a-zA-Z’'\-]+(?:\s+[A-Z][a-zA-Z’'\-]+){1,2})"
SPEAKER_PATTERNS = [
    # "Resident NAME …" and the compound-title variant "Resident and <Title Words> NAME …"
    # (e.g. "Resident and Alternate Planning Commissioner Amber Rasmussen explained …").
    # The optional middle requires a lowercase "and" + 1–4 Capitalized title words, so it
    # only fires on a genuine "Resident and <role> <Name>" introduction — it cannot match a
    # bare "Resident NAME" differently than before. Anchored at start of a PUBLIC COMMENTS
    # paragraph; no trailing-verb requirement (this pattern is Resident-anchored).
    re.compile(r'^\s*Resident\s+(?:and\s+(?:[A-Z][a-zA-Z]+\s+){1,4})?' + NAME),
    re.compile(r'^\s*' + NAME + r',\s+(?:a\s+resident|resident|living|of\s+the|from)\b', re.I),
    re.compile(r'^\s*During public comment,\s*' + NAME),
    re.compile(r'^\s*' + NAME + r'\s+(?:commented|stated|expressed|asked|spoke|said|inquired|'
                                r'thanked|brought|requested|raised|noted|shared|introduced|'
                                r'addressed|mentioned|voiced|presented|wanted|encouraged|'
                                r'described|acknowledged|read|provided)\b'),
]
# Sentence-internal "Mr./Ms./Mrs./Dr. Lastname" continuation (same speaker) — used only
# to avoid double-counting, not to introduce a new speaker.

# Words that are NOT real surnames / titles to reject as names.
STOP_NAMES = {"Mayor", "Council", "Councilmember", "Public", "City", "Vineyard",
              "Motion", "Staff", "Page", "Mr", "Ms", "Mrs", "Dr", "The"}


def parse_date(path: Path):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', path.name)
    return m.group(1) if m else ""


def extract_pc_block(text):
    lines = text.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if PC_HEADER.match(ln):
            start = i
            break
    if start is None:
        return None
    # find the next numbered section header after start
    end = len(lines)
    for j in range(start + 1, len(lines)):
        h = SEC_HEADER.match(lines[j])
        if h and not PC_HEADER.match(lines[j]):
            # ensure it's a real next section (number > 0); accept any all-caps numbered head
            end = j
            break
    return "\n".join(lines[start + 1:end])


def clean_name(name):
    name = name.strip().rstrip(",.").strip()
    parts = name.split()
    if not parts:
        return None
    if parts[0] in STOP_NAMES:
        return None
    # drop trailing role words accidentally captured
    return name


def split_paragraphs(block):
    # paragraphs separated by blank lines; also merge wrapped lines
    paras = []
    cur = []
    for ln in block.splitlines():
        if ln.strip() == "":
            if cur:
                paras.append(" ".join(s.strip() for s in cur))
                cur = []
        else:
            # skip page-footer lines
            if re.match(r'^\s*Page \d+ of', ln):
                continue
            cur.append(ln)
    if cur:
        paras.append(" ".join(s.strip() for s in cur))
    return [p for p in paras if p.strip()]


def detect_speaker(para):
    for pat in SPEAKER_PATTERNS:
        m = pat.match(para)
        if m:
            nm = clean_name(m.group(1))
            if nm and len(nm.split()) >= 2:
                return nm
    return None


def topic_from(para, name):
    # short topic: text after the name's verb, truncated
    t = para
    # remove a leading "Resident " (+ an "and " connector on the compound-title variant) /
    # "During public comment, ". We stop BEFORE any role words so the full speaker name is
    # retained in the paraphrase (matches the existing "Resident Dean Stonehocker" ->
    # "Dean Stonehocker …" convention). A bare "Resident NAME" intro has no "and", so those
    # rows are unchanged.
    t = re.sub(r'^\s*(Resident\s+(?:and\s+)?|During public comment,\s*)', '', t)
    t = t.strip()
    # cap length for topic
    topic = t[:120].rstrip()
    return topic, t


def main():
    rows = []
    files = sorted(MIN_DIR.glob("*/*/*.md"))
    skipped_no_section = 0
    no_comment_blocks = 0
    for f in files:
        text = f.read_text(errors="ignore")
        block = extract_pc_block(text)
        date = parse_date(f)
        rel = str(f.relative_to(BASE))
        if block is None:
            skipped_no_section += 1
            continue
        if NO_COMMENT.search(block) and len(block.strip()) < 400:
            no_comment_blocks += 1
            continue
        paras = split_paragraphs(block)
        seen = set()
        for p in paras:
            nm = detect_speaker(p)
            if not nm:
                continue
            key = (date, nm.lower())
            if key in seen:
                continue
            seen.add(key)
            topic, comment = topic_from(p, nm)
            rows.append({
                "date_normalized": date,
                "contact_name": nm,
                "subject": topic,
                "topic": topic,
                "comment": comment,
                "source": "in_person_minutes",
                "source_file": rel,
                "quality_flag": "clerk_paraphrase_not_written_comment",
            })

    rows.sort(key=lambda r: (r["date_normalized"], r["contact_name"]))

    with OUT.open("w", newline="") as fh:
        fh.write("# MEETING-RECORD NOTES, NOT public-submitted written comments. "
                 "These rows are clerk PARAPHRASES of in-person speakers recorded in "
                 "the Vineyard council minutes (NOT residents' own published text). "
                 "They are kept separate from all_comments_clean.csv per "
                 "extraction_standards.md.\n")
        w = csv.DictWriter(fh, fieldnames=[
            "date_normalized", "contact_name", "subject", "topic",
            "comment", "source", "source_file", "quality_flag"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"files scanned: {len(files)}")
    print(f"files with no PUBLIC COMMENT section: {skipped_no_section}")
    print(f"blocks explicitly 'no public comment': {no_comment_blocks}")
    print(f"speaker rows extracted: {len(rows)}")


if __name__ == "__main__":
    main()
