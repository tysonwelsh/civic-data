#!/usr/bin/env python3
"""
build_speaker_log.py — Logan Municipal Council

Regenerates minutes_speaker_log.csv: the City Recorder's third-person PARAPHRASE of
people who spoke IN PERSON during a Logan council meeting, under
"QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL" and in PUBLIC HEARING sections.

These are MEETING-RECORD NOTES, NOT public-submitted written/online comments.
They must NEVER be merged into all_comments_clean.csv (see
references/extraction_standards.md, "What counts as a public comment"). Logan has no
online eComment portal and publishes no verbatim resident-submitted text, so
all_comments_clean.csv is header-only by design.

Source preference:
  1. ../meeting_minutes/minutes/**/*.md   (populated by the minutes agent — preferred)
  2. public_comments/raw/*.txt            (seed: pdftotext -layout of sampled minutes PDFs)

Deterministic / idempotent.
"""
import os, re, csv, glob

HERE = os.path.dirname(os.path.abspath(__file__))
MIN_DIR = os.path.normpath(os.path.join(HERE, "..", "meeting_minutes", "minutes"))
RAW_DIR = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "minutes_speaker_log.csv")

NOTE = ("# MEETING-RECORD NOTES, NOT public-submitted comments. Clerk third-person "
        "PARAPHRASES of people who spoke IN PERSON during a Logan Municipal Council "
        "meeting's 'QUESTIONS AND COMMENTS FOR MAYOR AND COUNCIL' and PUBLIC HEARING "
        "sections. NOT residents' own published text and NOT a public-comments dataset; "
        "kept separate from all_comments_clean.csv per extraction_standards.md.")

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"])}

# Format A (2020-2025 minutes): "Name, a resident of Logan ..."
SPEAKER = re.compile(
    r"^([A-Z][A-Za-z.’'\-]+(?:\s+[A-Z][A-Za-z.’'\-]+){0,3}),\s+"
    r"(a\s+resident of [A-Za-z .]+|a\s+Logan resident|resident of [A-Za-z .]+|"
    r"representing [A-Za-z].*|a\s+member of .*|with [A-Z].*)")
# Format B (2026 minutes): "Logan resident Name addressed the Council ..."
SPEAKER_B = re.compile(
    r"^(?:Logan|North Logan|Cache(?: County)?|Nibley|Providence|Hyrum|Smithfield|River Heights)"
    r"\s+resident\s+([A-Z][A-Za-z.’'\-]+(?:\s+[A-Z][A-Za-z.’'\-]+){0,3})\b(.*)")

RESPONSE = re.compile(r"^(Councilmember|Council Member|Council member|Mayor|Vice Chair|"
                      r"Chairman|Chair |Mr\.|Ms\.|Mrs\.|Director|City |Staff|"
                      r"Finance Director|Attorney|Police Chief|Chief |Community )")
FOOTER = re.compile(r"\d+\s*\|\s*Page|Logan Municipal Council Minutes|^[#>*\-\s]*$")


def parse_date_from_name(fname):
    m = re.match(r"(\d{2})([A-Za-z]+)(\d{1,2})", fname)
    if m:
        return f"20{m.group(1)}-{MONTHS[m.group(2)]:02d}-{int(m.group(3)):02d}"
    m = re.search(r"(20\d{2})[-_]?(\d{2})[-_]?(\d{2})", fname)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def match_speaker(s):
    if RESPONSE.match(s):
        return None
    m = SPEAKER.match(s)
    if m:
        return clean(m.group(1)), clean(m.group(2))
    b = SPEAKER_B.match(s)
    if b:
        return clean(b.group(1)), "a resident of Logan"
    return None


def find_sections(lines):
    n = len(lines)
    secs = []
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if re.match(r"QUESTIONS AND COMMENTS FOR (THE )?MAYOR AND COUNCIL", s, re.I) or \
           re.match(r"Questions and Comments for the Mayor and Council", s):
            end = n
            for k in range(idx + 1, n):
                t = lines[k].strip()
                if re.match(r"(MAYOR/STAFF REPORTS|ACTION ITEMS|WORKSHOP ITEMS|"
                            r"PUBLIC HEARING|COMMITTEE REPORTS|COUNCIL BUSINESS|ADJOURN)",
                            t, re.I):
                    end = k
                    break
            secs.append((idx, end, "Questions & Comments"))
    opens = [i for i, l in enumerate(lines)
             if re.search(r"opened the (meeting to a |)public hearing", l, re.I)]
    closes = [i for i, l in enumerate(lines)
              if re.search(r"closed the public hearing", l, re.I)]
    for o in opens:
        c = next((x for x in closes if x > o), min(o + 120, n))
        secs.append((o, c, "Public Hearing"))
    return secs


def extract(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        ms = match_speaker(lines[i].strip())
        if ms:
            name, _aff = ms
            buf = [lines[i].strip()]
            j = i + 1
            while j < n:
                nxt = lines[j].strip()
                if match_speaker(nxt) or RESPONSE.match(nxt):
                    break
                if re.match(r"There (were|was) no (further |)comments", nxt):
                    break
                if FOOTER.match(nxt):
                    j += 1
                    continue
                if nxt == "":
                    break
                buf.append(nxt)
                j += 1
                if len(" ".join(buf)) > 700:
                    break
            out.append((name, clean(" ".join(buf))))
            i = j
        else:
            i += 1
    return out


def source_files():
    md = sorted(glob.glob(os.path.join(MIN_DIR, "**", "*.md"), recursive=True))
    if md:
        return [(p, os.path.relpath(p, os.path.join(HERE, "..")), parse_date_from_name(os.path.basename(p)))
                for p in md]
    txt = sorted(glob.glob(os.path.join(RAW_DIR, "*.txt")))
    return [(p, os.path.relpath(p, HERE), parse_date_from_name(os.path.basename(p)))
            for p in txt]


def main():
    rows = []
    srcs = source_files()
    for path, rel, date in srcs:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for start, end, _kind in find_sections(lines):
            for name, comment in extract(lines[start:end]):
                subject = comment[:120]
                rows.append({
                    "date_normalized": date,
                    "contact_name": name,
                    "subject": subject,
                    "comment": comment,
                    "source_file": rel,
                    "quality_flag": "ok" if len(comment) > len(name) + 5 else "name_only",
                })
    # dedupe
    seen, final = set(), []
    for r in rows:
        k = (r["date_normalized"], r["contact_name"], r["comment"][:80])
        if k in seen:
            continue
        seen.add(k)
        final.append(r)
    final.sort(key=lambda x: (x["date_normalized"], x["contact_name"]))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        f.write(NOTE + "\n")
        w = csv.DictWriter(f, fieldnames=["date_normalized", "contact_name", "subject",
                                          "comment", "source_file", "quality_flag"])
        w.writeheader()
        w.writerows(final)

    print(f"source files: {len(srcs)} | speaker rows: {len(final)}")
    from collections import Counter
    print("by date:", dict(Counter(r["date_normalized"] for r in final)))


if __name__ == "__main__":
    main()
