#!/usr/bin/env python3
"""
Build minutes_speaker_log.csv from Ogden City Council meeting minutes.

IMPORTANT: These rows are MEETING-RECORD NOTES — the City Recorder's third-person
paraphrase of people who spoke in person during the general "Public Comments"
period of a council meeting. They are NOT public-submitted written comments and
must never be presented as the public-comments dataset (all_comments_clean.csv).
See extraction_standards.md "What counts as a public comment".

Resumable / deterministic: re-running regenerates the CSV from minutes/ markdown.
"""
import csv
import re
import sys
from pathlib import Path

MIN_DIR = Path(__file__).resolve().parent.parent / "meeting_minutes" / "minutes"
OUT = Path(__file__).resolve().parent / "minutes_speaker_log.csv"

# Heading that opens the general public-comment period.
PC_HEADING = re.compile(r"^\s*Public Comment(?:s| Period)?\s*$", re.IGNORECASE)

# Headings that CLOSE the public-comment section.
END_HEADING = re.compile(
    r"^\s*("
    r"Mayor'?s? Comments?"
    r"|Council ?[Mm]ember Comments?"
    r"|Administrative"
    r"|Public Hearing"
    r"|Unfinished Business"
    r"|New Business"
    r"|Consent"
    r"|Reports?"
    r"|Recess"
    r"|Adjourn"
    r"|RESOLUTION"
    r"|ORDINANCE"
    r")\b",
    re.IGNORECASE,
)

# A new speaker paragraph begins with a Capitalized personal name (2-4 tokens),
# optionally with a middle initial / hyphen / apostrophe, then a verb/phrase.
# e.g. "Brian Janroy stated ...", "Robert Hunter discussed ...",
#      "Mary Jo St. Clair-Lopez addressed ..."
NAME_LEAD = re.compile(
    r"^(?P<name>(?:[A-Z][A-Za-z.'\-]+)(?:\s+[A-Z][A-Za-z.'\-]+){1,3})\s+"
    r"(?P<rest>(?:stated|said|discussed|addressed|asked|shared|spoke|expressed|"
    r"thanked|noted|commented|talked|introduced|explained|presented|requested|"
    r"voiced|raised|read|gave|wished|mentioned|inquired|encouraged|urged|"
    r"described|reported|opposed|supported|questioned|complained|appeared|came|"
    r"approached|provided|offered|reiterated|emphasized|recommended|representing|"
    r"is\b|was\b|introduced|of\b|with\b|on behalf).*)$"
)

# Things that are NOT a public speaker (council/staff titles + place/org words +
# pronouns that signal a mid-paragraph sentence was mis-split as a new speaker).
NOT_SPEAKER = re.compile(
    r"\b(Council|Chair|Mayor|Vice|Member|Director|Recorder|Attorney|Chief|"
    r"Manager|Officer|Commissioner|Staff|Administration|"
    r"City|County|State|Department|Committee|Company|Program|University|"
    r"Street|Avenue|Boulevard|Drive|Lane|Road|Canyon|House|America|Register|"
    r"They|He|She|This|There|It|We|One|Comments?)\b",
    re.IGNORECASE,
)

# A token that is a pronoun/contraction (e.g. trailing ". He") -> not a real name.
PRONOUN_LAST = re.compile(
    r"\b(He|She|They|It|This|There|We|One|His|Her|Their)$"
)


def date_from_path(p: Path):
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", p.name)
    if m:
        return m.group(0)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", str(p))
    return m.group(0) if m else ""


def title_from_path(p: Path):
    stem = p.stem  # e.g. 2025-07-15_city-council-meeting
    t = re.sub(r"^\d{4}-\d{2}-\d{2}_", "", stem).replace("-", " ").strip()
    return t.title() if t else "City Council Meeting"


def extract_section(lines):
    """Return list of raw lines inside the Public Comments section, or []."""
    start = None
    for i, ln in enumerate(lines):
        if PC_HEADING.match(ln):
            start = i + 1
            break
    if start is None:
        return []
    out = []
    for ln in lines[start:]:
        if END_HEADING.match(ln):
            break
        out.append(ln)
    return out


def split_speakers(section_lines):
    """Group wrapped lines into paragraphs, then detect speaker entries."""
    # Re-join wrapped text into logical paragraphs: a new paragraph starts when a
    # line (after lstrip) begins with a capitalized name-lead.
    paras = []
    cur = []
    for raw in section_lines:
        s = raw.strip()
        if not s:
            continue
        if NAME_LEAD.match(s) and cur:
            paras.append(" ".join(cur))
            cur = [s]
        elif NAME_LEAD.match(s):
            cur = [s]
        else:
            if cur:
                cur.append(s)
            # else: leading prose before first named speaker -> ignore
    if cur:
        paras.append(" ".join(cur))

    def is_real_name(name):
        if NOT_SPEAKER.search(name):
            return False
        if PRONOUN_LAST.search(name):
            return False
        # A name token ending in a period that's not a known abbreviation
        # (Jr./Sr./St./Mr./Ms./Mrs./Dr./single-letter initials) signals a
        # sentence-boundary mis-split (e.g. "Station." / "Plan.").
        for tok in name.split():
            if tok.endswith("."):
                base = tok[:-1]
                if base in ("Jr", "Sr", "St", "Mr", "Ms", "Mrs", "Dr"):
                    continue
                if re.fullmatch(r"[A-Z](\.[A-Z])*", base):  # initials: A, D.S
                    continue
                return False
        return True

    entries = []  # list of [name, topic, comment_parts]
    for para in paras:
        para = re.sub(r"\s+", " ", para).strip()
        m = NAME_LEAD.match(para)
        name = m.group("name").strip() if m else ""
        if m and is_real_name(name):
            topic = m.group("rest").strip()[:120].rstrip()
            entries.append([name, topic, para])
        else:
            # Mis-split sentence (place/pronoun lead) — append back to the
            # previous real speaker so no paraphrase text is lost.
            if entries:
                entries[-1][2] += " " + para

    out = []
    for name, topic, comment in entries:
        comment = comment.strip()
        flags = []
        if len(comment) < 60:
            flags.append("short_comment")
        out.append((name, topic, comment, "|".join(flags)))
    return out


def main():
    rows = []
    files = sorted(MIN_DIR.rglob("*.md"))
    files_with_pc = 0
    for f in files:
        # General public-comment period appears in regular council meetings.
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        section = extract_section(lines)
        if not section:
            continue
        entries = split_speakers(section)
        if not entries:
            continue
        files_with_pc += 1
        date = date_from_path(f)
        title = title_from_path(f)
        src = str(f.relative_to(MIN_DIR.parent.parent))
        for name, topic, comment, flag in entries:
            rows.append(
                {
                    "date_normalized": date,
                    "contact_name": name,
                    "subject": topic,
                    "comment": comment,
                    "source_file": src,
                    "quality_flag": flag,
                }
            )

    rows.sort(key=lambda r: (r["date_normalized"], r["contact_name"]))

    header_note = (
        "# NOTE: These rows are MEETING-RECORD NOTES — the City Recorder's "
        "third-person paraphrase of people who spoke IN PERSON during the general "
        "'Public Comments' period of an Ogden City Council meeting. They are NOT "
        "public-submitted written/online comments and must NOT be treated as the "
        "public-comments dataset (all_comments_clean.csv). See "
        "references extraction_standards.md 'What counts as a public comment'."
    )

    with OUT.open("w", newline="", encoding="utf-8") as fh:
        fh.write(header_note + "\n")
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "date_normalized",
                "contact_name",
                "subject",
                "comment",
                "source_file",
                "quality_flag",
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"files scanned: {len(files)}")
    print(f"files with public-comment speakers: {files_with_pc}")
    print(f"speaker rows: {len(rows)}")


if __name__ == "__main__":
    main()
