#!/usr/bin/env python3
"""
Build minutes_speaker_log.csv: IN-PERSON public-comment SPEAKERS paraphrased by the
clerk in Lehi City Council minutes' "Citizen Input" sections (2020-present).

THESE ARE NOT THE COMMENTS DATASET. They are MEETING-RECORD NOTES -- the clerk's
third-person PARAPHRASE of who spoke and on what topic ("Casey Glade expressed
concerns with ..."). Per extraction_standards.md they are kept strictly separate
from all_comments_clean.csv (which holds residents' OWN verbatim written/online
text). Do not move these rows into all_comments_clean.csv.

Method (deterministic, no fabrication):
  1. Isolate each minutes file's "Citizen Input" block: from the line naming
     "Citizen Input" to the next numbered section header.
  2. Split into paragraphs; emit a row only when a paragraph is clearly introduced
     by a named speaker (Capitalized first+last name followed by a reporting verb,
     or "Name and Name ... verb"). No speaker named -> no row.
  3. "No one ... / hearing none" style blocks yield zero rows.
"""
import csv
import re
from pathlib import Path

BASE = Path("/Users/tysonwelsh/civic-data/lehi_city_council")
MIN_DIR = BASE / "meeting_minutes" / "minutes"
OUT = Path(__file__).resolve().parent / "minutes_speaker_log.csv"

CI_HEADER = re.compile(r'citizen\s+input', re.I)
SEC_HEADER = re.compile(r'^\s*\d+\.\s+[A-Z]')  # next numbered agenda section
FOOTER = re.compile(r'^\s*Lehi City Council Meeting\b|^\s*Page \d+\b|^\s*\f')
NO_COMMENT = re.compile(
    r'no (?:one|public comment|citizen|comments?)\b|hearing none|'
    r'there (?:were|was) no\b|no one (?:came forward|spoke|wished)', re.I)

NAME = (r"[A-Z][a-zA-Z'’.\-]+\s+(?:(?:and|&)\s+)?[A-Z][a-zA-Z'’.\-]+"
        r"(?:\s+[A-Z][a-zA-Z'’.\-]+){0,2}")
VERB = (r"(?:thank(?:s|ed)?|encourage[ds]?|express(?:ed|es)?|concern(?:ed|s)?|"
        r"state[ds]?|ask(?:ed|s)?|spoke|sa[iy]d|inquir(?:ed|es)?|request(?:ed|s)?|"
        r"rais(?:ed|es)?|note[ds]?|shar(?:ed|es)?|address(?:ed|es)?|mention(?:ed|s)?|"
        r"voic(?:ed|es)?|present(?:ed|s)?|want(?:ed|s)?|describ(?:ed|es)?|"
        r"read|gave|comment(?:ed|s)?|complain(?:ed|s)?|suggest(?:ed|s)?|"
        r"discuss(?:ed|es)?|appreciat(?:ed|es)?|oppos(?:ed|es)?|support(?:ed|s)?|"
        r"urg(?:ed|es)?|propos(?:ed|es)?|explain(?:ed|s)?|introduc(?:ed|es)?)")
SPEAKER = re.compile(r'^\s*(' + NAME + r')\s+' + VERB + r'\b')

STOP = {"Mayor", "Council", "Councilor", "Councilmember", "City", "Lehi", "Motion",
        "Staff", "Page", "Mr", "Ms", "Mrs", "Dr", "The", "Roll", "Public", "Consent",
        "Chief", "Director", "Captain", "Sergeant", "Officer"}


def parse_date(p):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', p.name)
    return m.group(1) if m else ""


def ci_block(text):
    lines = text.splitlines()
    out, capturing = [], False
    for ln in lines:
        if not capturing:
            if CI_HEADER.search(ln):
                capturing = True
            continue
        if SEC_HEADER.match(ln):
            break
        out.append(ln)
    return out


def paragraphs(lines):
    paras, cur = [], []
    for ln in lines:
        if FOOTER.match(ln):
            continue
        if not ln.strip():
            if cur:
                paras.append(" ".join(s.strip() for s in cur)); cur = []
        else:
            cur.append(ln)
    if cur:
        paras.append(" ".join(s.strip() for s in cur))
    return [p for p in paras if p.strip()]


def clean_name(n):
    n = re.sub(r'\s+', ' ', n).strip().rstrip(',.').strip()
    if n.split()[0] in STOP:
        return None
    return n


def main():
    rows = []
    files = sorted(MIN_DIR.glob("*/*/*city-council*.md"))
    n_files = n_with_ci = 0
    for f in files:
        n_files += 1
        text = f.read_text(errors="ignore")
        block = ci_block(text)
        if not block:
            continue
        n_with_ci += 1
        date = parse_date(f)
        rel = str(f.relative_to(BASE))
        seen = set()
        for p in paragraphs(block):
            if NO_COMMENT.search(p) and len(p) < 120:
                continue
            m = SPEAKER.match(p)
            if not m:
                continue
            nm = clean_name(m.group(1))
            if not nm or len(nm.split()) < 2:
                continue
            key = (date, nm.lower())
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "date_normalized": date, "contact_name": nm,
                "subject": p[:120].rstrip(), "topic": p[:120].rstrip(),
                "comment": p.strip(), "source": "in_person_citizen_input",
                "source_file": rel,
                "quality_flag": "clerk_paraphrase_not_written_comment"})

    rows.sort(key=lambda r: (r["date_normalized"], r["contact_name"]))
    with OUT.open("w", newline="") as fh:
        fh.write("# MEETING-RECORD NOTES, NOT public-submitted written comments. "
                 "Clerk PARAPHRASES of in-person speakers in the Lehi council minutes' "
                 "Citizen Input sections (NOT residents' own published text). Kept "
                 "separate from all_comments_clean.csv per extraction_standards.md.\n")
        w = csv.DictWriter(fh, fieldnames=[
            "date_normalized", "contact_name", "subject", "topic",
            "comment", "source", "source_file", "quality_flag"])
        w.writeheader()
        w.writerows(rows)

    print(f"council files: {n_files} | with Citizen Input section: {n_with_ci}")
    print(f"speaker rows: {len(rows)}")


if __name__ == "__main__":
    main()
