#!/usr/bin/env python3
"""
Extract GENUINE public-submitted WRITTEN/ONLINE comments that Lehi City PUBLISHED
verbatim inside its COVID-era (2020) council MINUTES PDFs.

WHY THESE COUNT (and minutes paraphrases of in-person speakers do NOT):
  During the 2020 virtual-meeting period Lehi reproduced, *verbatim*, the written
  public comments residents submitted online / by email / by eComment as an
  appendix to (or inline in) the meeting minutes. That reproduced text is the
  public's OWN words that the city published somewhere public -> it is a genuine
  written/online comment and belongs in all_comments_clean.csv.
  Clerk PARAPHRASES of in-person speakers are a different thing and live in
  minutes_speaker_log.csv (see extract_speaker_log.py). Do not conflate them.

This script copies comment text VERBATIM out of the minutes .md files (it never
re-types or invents text) and best-effort attributes a name from an email
"From:" header or a sign-off signature. Where no signature is present the name is
left blank (anonymous) -- that is honest, not a gap.

Sources (verified to contain reproduced written comments):
  2020-03-30  large "Comments for the March 31st City Council Meeting" appendix
  2020-04-13  forwarded-email appendix (From/To/Subject/Date headers)
  2020-06-08  inline online comment (Steve Moulton)
  2020-06-22  inline eComment (Ray Worthen)
"""
import csv
import re
from pathlib import Path

MIN = Path("/Users/tysonwelsh/civic-data/lehi_city_council/meeting_minutes/minutes")
HERE = Path(__file__).resolve().parent

FIELDS = ["date", "contact_name", "subject", "topic", "comment", "district",
          "source", "has_attachment", "source_file", "page_numbers",
          "period_start", "period_end", "date_normalized", "quality_flag"]

FOOTER = re.compile(
    r'^\s*(Lehi City Council Meeting\b.*|Comments for the .*|'
    r'Dancing Moose Montessori School, Item.*|Public Comments? (are|for) .*|'
    r'Page \d+ of .*)\s*$')
SEP = re.compile(r'^\s*-{2,}\s*$|^\s*\f\s*$')

SIGNOFF = re.compile(
    r'^\s*(Sincerely(?: yours)?|Best regards|Best|Warm(?:est)? regards|'
    r'Kind regards|Regards|Respectfully(?: submitted| yours)?|Thank you(?: so much)?|'
    r'Thanks(?: so much| again)?|Cheers|V/r|Gratefully|With (?:gratitude|respect|appreciation))'
    r'[ ,.!]*$', re.I)

SALUT = re.compile(
    r'^\s*(Dear\b|To the\b|To The\b|Hello\b|Hi\b|Good morning\b|Good afternoon\b|'
    r'Good evening\b|Greetings\b|Ms\.?\s+Wilson\b|Mayor Johnson,|Members of\b|'
    r'To whom\b|Please pass this along\b)', re.I)

H_FROM = re.compile(r'^\s*From:\s*(.+?)\s*$')
H_SUBJ = re.compile(r'^\s*Subject:\s*(.+?)\s*$')
H_DATE = re.compile(r'^\s*Date:\s*(.+?)\s*$')
H_OTHER = re.compile(r'^\s*(To|Cc|Bcc|Sent|Importance|Reply-To):\s*', re.I)

BAD_NAME = re.compile(
    r'lehi city|city council|planning|commission|mayor\b|recorder|^\s*$|'
    r'@|http|^\d|councilmember', re.I)


def clean_name(raw):
    if raw is None:
        return ""
    n = raw.strip().strip(',').strip()
    n = re.sub(r'\s*<[^>]*>\s*', '', n)          # drop <email>
    n = re.sub(r'\s*\(.*?\)\s*', ' ', n).strip()  # drop (parenthetical)
    # cut off trailing address/role after a comma or digits
    n = re.split(r',|\d', n)[0].strip()
    if not n or BAD_NAME.search(n):
        return ""
    # plausible person name: 1-4 words, each capitalized-ish
    if len(n.split()) > 5:
        return ""
    return n


def flush(block, rows, src, date):
    body = "\n".join(block["body"])
    # collapse 3+ newlines, trim
    body = re.sub(r'\n{3,}', '\n\n', body).strip()
    # join hard-wrapped lines within a paragraph into readable text but keep verbatim words
    if len(re.sub(r'\s', '', body)) < 40:
        return
    if re.match(r'^no (public )?comments? (were|was)', body, re.I):
        return
    rows.append({
        "date": date, "contact_name": block["name"],
        "subject": block["subject"] or "Written public comment (published in minutes)",
        "topic": block["topic"],
        "comment": body, "district": "",
        "source": block["source"], "has_attachment": block["has_attachment"],
        "source_file": src, "page_numbers": "",
        "period_start": "", "period_end": "",
        "date_normalized": date,
        "quality_flag": "verbatim_written_comment_published_in_minutes" +
                        ("" if block["name"] else "; anonymous_no_signature"),
    })


def new_block(source, topic):
    return {"body": [], "name": "", "subject": "", "topic": topic,
            "has_attachment": "false", "source": source}


def parse_appendix(lines, src, date, topic, source_tag):
    rows = []
    blk = new_block(source_tag, topic)
    expect_name = False
    for ln in lines:
        if FOOTER.match(ln) or SEP.match(ln):
            continue
        m = H_FROM.match(ln)
        if m:
            # new email block
            flush(blk, rows, src, date)
            blk = new_block(source_tag, topic)
            blk["name"] = clean_name(m.group(1))
            expect_name = False
            continue
        if H_SUBJ.match(ln):
            blk["subject"] = H_SUBJ.match(ln).group(1).strip()
            continue
        if H_DATE.match(ln) or H_OTHER.match(ln):
            continue
        if expect_name:
            if ln.strip():
                if not blk["name"]:
                    blk["name"] = clean_name(ln)
                flush(blk, rows, src, date)
                blk = new_block(source_tag, topic)
                expect_name = False
                # if this line is itself a salutation, it begins next comment
                if SALUT.match(ln):
                    blk["body"].append(ln.rstrip())
                continue
            else:
                continue  # skip blanks while waiting for name
        if SIGNOFF.match(ln):
            if "attach" in "\n".join(blk["body"]).lower():
                blk["has_attachment"] = "true"
            expect_name = True
            continue
        if SALUT.match(ln) and len(re.sub(r'\s', '', "\n".join(blk["body"]))) > 40:
            flush(blk, rows, src, date)
            blk = new_block(source_tag, topic)
            blk["body"].append(ln.rstrip())
            continue
        blk["body"].append(ln.rstrip())
    flush(blk, rows, src, date)
    return rows


def grab(path, a, b):
    return path.read_text(errors="ignore").splitlines()[a - 1:b]


def main():
    rows = []

    f0330 = MIN / "2020/2020-03-30/2020-03-31_city-council-meeting.md"
    rows += parse_appendix(
        grab(f0330, 614, 1946), str(f0330.relative_to(MIN.parent.parent)),
        "2020-03-30",
        "Dancing Moose Montessori daycare / Thanksgiving Point Area Plan",
        "online_written_comment_published_in_minutes")

    f0413 = MIN / "2020/2020-04-13/2020-04-14_city-council-meeting.md"
    rows += parse_appendix(
        grab(f0413, 416, 1095), str(f0413.relative_to(MIN.parent.parent)),
        "2020-04-13",
        "Bull River Road rezoning (proposed daycare/learning academy)",
        "online_written_comment_published_in_minutes")

    # Inline single comments (trim at the clerk-narrative line that follows)
    f0608 = MIN / "2020/2020-06-08/2020-06-09_city-council-meeting.md"
    body = "\n".join(grab(f0608, 224, 260))
    body = body.split("submitted online by Steve Moulton:", 1)[-1]
    body = re.split(r'\n\s*(?:Mayor Johnson|Motion:|Councilor |\d+\.\s+Consideration)', body)[0].strip()
    rows.append({
        "date": "2020-06-08", "contact_name": "Steve Moulton",
        "subject": "Online comment re Ord. #34-2020 (storage containers on residential property)",
        "topic": "Development Code amendment - container/storage sheds",
        "comment": body, "district": "",
        "source": "online_written_comment_published_in_minutes", "has_attachment": "false",
        "source_file": str(f0608.relative_to(MIN.parent.parent)), "page_numbers": "",
        "period_start": "", "period_end": "", "date_normalized": "2020-06-08",
        "quality_flag": "verbatim_written_comment_published_in_minutes"})

    f0622 = MIN / "2020/2020-06-22/2020-06-23_city-council-meeting.md"
    body = "\n".join(grab(f0622, 236, 258))
    body = body.split("Hello, My name is Ray Worthen", 1)
    body = ("Hello, My name is Ray Worthen" + body[1]) if len(body) > 1 else body[0]
    body = re.split(r'\n\s*Mayor Johnson stated', body)[0].strip()
    rows.append({
        "date": "2020-06-22", "contact_name": "Ray Worthen",
        "subject": "eComment re Res. #2020-49 (TOD rezone application suspension)",
        "topic": "Transit Oriented Development Zone moratorium - Utah Refractories site",
        "comment": body, "district": "",
        "source": "online_written_comment_published_in_minutes", "has_attachment": "false",
        "source_file": str(f0622.relative_to(MIN.parent.parent)), "page_numbers": "",
        "period_start": "", "period_end": "", "date_normalized": "2020-06-22",
        "quality_flag": "verbatim_written_comment_published_in_minutes"})

    # ---- post-clean: strip leading email-timestamp lines; route junk to dropped ----
    TS = re.compile(
        r'^\s*((Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s+\w+\s+\d{1,2}(,\s*\d{4})?'
        r'[, ]+\d{1,2}:\d{2}\s*(AM|PM)?|'
        r'\w+\s+\d{1,2},\s*\d{4}(,?\s*\d{1,2}:\d{2}\s*(AM|PM)?)?)\s*$', re.I)
    clean, dropped = [], []
    for r in rows:
        lines = r["comment"].split("\n")
        while lines and TS.match(lines[0]):
            lines.pop(0)
        r["comment"] = "\n".join(lines).strip()
        reason = None
        if re.match(r'^\s*Approved:', r["comment"]):
            reason = "minutes_attest_block_not_a_comment"
        elif not r["contact_name"] and len(re.sub(r'\s', '', r["comment"])) < 200:
            reason = "short_anonymous_fragment_or_signature_tail"
        if reason:
            d = dict(r); d["_drop_reason"] = reason
            dropped.append(d)
        else:
            clean.append(r)

    out = HERE / "all_comments_clean.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(clean)
    with (HERE / "all_comments_dropped.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS + ["_drop_reason"])
        w.writeheader()
        w.writerows(dropped)

    named = sum(1 for r in clean if r["contact_name"])
    print(f"clean rows: {len(clean)}  (named: {named}, anonymous: {len(clean)-named}) | dropped: {len(dropped)}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
