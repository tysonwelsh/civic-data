#!/usr/bin/env python3
"""
Extract in-person public comments from St. George City Council REGULAR minutes.

IMPORTANT — St. George minutes do NOT transcribe the body of in-person public comments.
The "COMMENTS FROM THE PUBLIC" section records, per speaker, a line of the form:

    Link to comments made by resident <Name> [regarding <topic>]
    [, including comments from <Mayor/staff>]: <HH:MM:SS> [Recording N]

i.e. the speaker's NAME and (sometimes) a TOPIC, plus a video timestamp — but no
verbatim comment text. This script therefore extracts speaker name + topic + meeting
date as `source=in_person_minutes` rows. The `comment` field carries the available
descriptive text (the topic, when present) and the row is flagged so downstream analysis
knows the actual spoken content lives only in the recording.

Output: prints JSON rows to stdout (the assembler `build_clean_csv.py` consumes this) and,
if run directly, writes `comments_json/_in_person_minutes.json`.
"""
import re, glob, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the st_george_city_council repo root
MIN_DIR = os.path.join(REPO, "meeting_minutes")

HEADERS = re.compile(
    r'^[ \t]*(COMMENTS FROM THE PUBLIC|COMMENT FROM THE PUBLIC|PUBLIC COMMENTS?)\s*:?\s*$',
    re.M)
# Headers that mark the end of the public-comment section
NEXT = re.compile(
    r'^[ \t]*(CONSENT CALENDAR|PUBLIC HEARING|MAYOR|REGULAR AGENDA|REPORTS|ADJOURN|'
    r'RECOGNITION|PRESENTATION|ORDINANCE|RESOLUTION|APPOINT|ITEMS OF|CALL TO ORDER|'
    r'NEW BUSINESS|UNFINISHED|STAFF REPORTS|CITY MANAGER|COUNCIL REPORTS|REQUEST|'
    r'CITY COUNCIL|DEPARTMENT|SET A PUBLIC HEARING|MINUTES|AWARD)', re.M)

MONTHS = {m: i for i, m in enumerate(
    ['january','february','march','april','may','june','july','august',
     'september','october','november','december'], 1)}

# "Link to comments [made] by|from [resident] <Name> [regarding ...] [, including ...]: TS"
LINK_RE = re.compile(
    r'[Ll]ink to (?:the )?comments?(?:\s+made)?\s+(?:by|from)\s+'
    r'(?:residents?\s+|Residents?\s+)?'
    r'(?P<rest>.*?)'
    r'(?::\s*\d{2}:\d{2}(?::\d{2})?|\[Recording\s*\d+\]|$)', re.S)

# names that are not public commenters (council/staff procedural lines)
NON_PUBLIC = re.compile(
    r'^(Mayor|Mayor Pro Tem|Councilmember|City Manager|City Attorney|City Recorder|'
    r'Public Works|Community|Energy|Planner|Assistant|Director|Staff)\b', re.I)


def date_from_filename(path):
    # .../minutes/<year>/<weekfolder>/<YYYY-MM-DD>_city-council-regular-meeting.md
    base = os.path.basename(path)
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})_', base)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return None


def date_from_header(txt):
    # First line "# City Council Regular Meeting — February 6, 2025"
    m = re.search(r'—\s*([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})', txt[:300])
    if m:
        mo = MONTHS.get(m.group(1).lower())
        if mo:
            return f"{m.group(3)}-{mo:02d}-{int(m.group(2)):02d}"
    return None


def get_section(txt):
    m = HEADERS.search(txt)
    if not m:
        return None
    rest = txt[m.end():]
    m2 = NEXT.search(rest)
    return (rest[:m2.start()] if m2 else rest[:2000])


def strip_footer(s):
    # remove running page footers: "St. George City Council Minutes / <date> / Page X"
    s = re.sub(r'St\.?\s*George.*?Minutes?', ' ', s, flags=re.I)
    s = re.sub(r'St\.?\s*George\s+(?:City\s+)?Council\s+Meeting', ' ', s, flags=re.I)
    s = re.sub(r'Page\s+(One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|\d+)', ' ', s, flags=re.I)
    s = re.sub(r'[A-Z][a-z]+ \d{1,2}, 20\d\d', ' ', s)  # date footer
    return s


def parse_speakers(section):
    flat = re.sub(r'\s+', ' ', strip_footer(section)).strip()
    rows = []
    if not flat:
        return rows
    # No comments
    low = flat.lower()
    if re.search(r'no (public )?comments? (were )?(given|received|made|provided)', low) and \
       'link to comments by' not in low:
        return rows  # genuinely empty window -> no rows
    for m in LINK_RE.finditer(flat):
        rest = m.group('rest').strip(" ,.;")
        if not rest:
            continue
        # skip pure procedural/staff lines (e.g. "Mayor Randall outlining the rules")
        if NON_PUBLIC.match(rest):
            continue
        if re.search(r'outlining the rules|thanking those|other forms received|'
                     r'rules for speaking|noting that', rest, re.I):
            continue
        # Split name from topic. Topic intro markers:
        #   "<Name> regarding <topic>"  /  "<Name> about <topic>"  /  "<Name>, including ..."
        name = rest
        topic = ""
        mtop = re.search(r'\b(regarding|about|concerning|on the topic of|on)\b', rest, re.I)
        minc = re.search(r',\s*including\b', rest, re.I)
        cut = len(rest)
        if mtop:
            cut = min(cut, mtop.start())
        if minc:
            cut = min(cut, minc.start())
        name = rest[:cut].strip(" ,.;")
        if mtop and mtop.start() < (minc.start() if minc else len(rest)):
            # topic runs from after 'regarding' to the 'including' marker or end
            tend = minc.start() if (minc and minc.start() > mtop.end()) else len(rest)
            topic = rest[mtop.end():tend].strip(" ,.;")
        # clean name: drop trailing role words / stray
        name = re.sub(r'\s+', ' ', name).strip()
        # plausibility: a name is 1-5 capitalized tokens
        if not name or len(name) > 60:
            continue
        if NON_PUBLIC.match(name):
            continue
        rows.append({"contact_name": name, "topic": topic})
    return rows


def main():
    files = sorted(glob.glob(os.path.join(MIN_DIR, "minutes/*/*/*regular*.md")))
    out = []
    for f in files:
        txt = open(f, encoding="utf-8", errors="replace").read()
        sec = get_section(txt)
        if sec is None:
            continue
        d = date_from_header(txt) or date_from_filename(f)
        speakers = parse_speakers(sec)
        relpath = os.path.relpath(f, REPO)
        for sp in speakers:
            topic = sp["topic"]
            comment = (topic if topic else
                       "In-person public comment given at the meeting; "
                       "verbatim text not transcribed in the minutes (see meeting recording).")
            out.append({
                "contact_name": sp["contact_name"],
                "date_normalized": d,
                "date": d,
                "subject": topic if topic else "In-person public comment",
                "topic": topic,
                "comment": comment,
                "has_attachment": False,
                "source_file": relpath,
                "pages": "",
                "_minutes_pointer_no_text": (topic == ""),
            })
    return out


if __name__ == "__main__":
    rows = main()
    os.makedirs(os.path.join(REPO, "public_comments", "comments_json"), exist_ok=True)
    dest = os.path.join(REPO, "public_comments", "comments_json", "_in_person_minutes.json")
    json.dump({"comments": rows}, open(dest, "w"), indent=1)
    print(f"in_person_minutes rows: {len(rows)} -> {dest}", file=sys.stderr)
    print(json.dumps(rows[:5], indent=1))
