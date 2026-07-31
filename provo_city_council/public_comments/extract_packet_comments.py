#!/usr/bin/env python3
"""
Extract GENUINE written public comments from Provo agenda-packet PDFs (documentType=5).

Source: agenda packets bundle resident-submitted emails/letters (forwarded to the
Planning Commission / Council on land-use & other items). These are the public's OWN
words -- the SLC-style "written public comment" target. They appear as email blocks:

    From: <Resident Name> [<email>]
    Sent: <date>
    To: <city staff / DS Public Hearings / council>
    Subject: <subject>
    <body ...>

This parser reads the pdftotext -layout output in raw/packet_txt/packet_<date>.txt,
splits out each email block, drops city-staff / vendor / applicant senders and
boilerplate, scrubs the security-banner + signature noise, and emits SLC-schema rows
with source=agenda_packet.

FULL HARVEST: raw/packet_txt/ now holds one .txt for EVERY Regular-Meeting packet that
contained >=1 genuine comment (26 of 138 packets; the rest carried no attached resident
emails and were not retained -- see packets_scanned.csv for full coverage). The packets
were downloaded + scanned by harvest_packets.py. This script rebuilds all_comments_clean.csv
deterministically from those kept .txt files.
"""
import csv, re, glob, os, sys

RAW_TXT = os.path.join(os.path.dirname(__file__), 'raw', 'packet_txt')
OUT = os.path.join(os.path.dirname(__file__), 'all_comments_clean.csv')
DROPPED = os.path.join(os.path.dirname(__file__), 'all_comments_dropped.csv')

SLC_COLS = ['date','contact_name','subject','topic','comment','district','source',
            'has_attachment','source_file','page_numbers','period_start','period_end',
            'date_normalized','quality_flag']

# Senders that are city staff / internal, not public commenters -> exclude
STAFF_SENDER_RE = re.compile(
    r'(development services|council policy analyst|provo city|planning division|'
    r'city attorney|deputy|public hearings|staff|department|councilor|mayor|'
    r'administrator|@provo\.org|@provo\.gov|no-?reply|notification|'
    r'operations manager|director|coordinator|legal department|inside sales)', re.I)

# Specific non-public senders identified by review of the full harvest:
#   - city staff who reply to residents inside the threads (their replies are not
#     public comment; the residents' originals are kept separately)
#   - vendors / billing / newspaper legal-ad reps
#   - the project APPLICANT / landowner (a party to the application, not the public)
NAME_BLOCKLIST = {
    'gary mcginn',        # Provo Community & Neighborhood Services director (staff)
    'kristal howarth',    # internal city staff (vendor-billing thread)
    'zagster billing',    # vendor
    'adam greenstein',    # vendor (Zagster micro-mobility director)
    'jamie rivera',       # Standard-Examiner legal-ad sales rep
    'laramie gonzales',   # Provo staff (Business Operations Manager)
    'j gordon',           # project landowner/applicant (East Bay storage), not public
    'bruce nelson',       # landowner consenting to annexation (party to J Gordon app)
    'david mortensen',    # Provo Finance Budget Officer (newspaper ad proof/invoice)
    'david sewell',       # Council Sign Committee member reply (electeds/committee)
}
# Junk / unparseable placeholder names whose comment text is still genuine public input
JUNK_NAME_RE = re.compile(r'^(lolalola|test|anonymous|n/?a|none|unknown)\b', re.I)

CAUTION_RE = re.compile(r'CAUTION:.*?(safe\.)', re.S | re.I)

MONTHS = {m.lower(): i for i, m in enumerate(
    ['January','February','March','April','May','June','July','August',
     'September','October','November','December'], 1)}

def norm_date(sent_line):
    """Parse a 'Sent: Monday, October 5, 2020 10:13 AM' style date -> ISO."""
    if not sent_line:
        return ''
    # Month DD, YYYY
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', sent_line)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    # MM/DD/YYYY
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', sent_line)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ''

def clean_name(raw):
    raw = re.sub(r'<[^>]*>', '', raw)            # strip <email>
    raw = re.sub(r'\[[^\]]*\]', '', raw)         # strip [mailto:...] leftovers
    raw = re.sub(r'\b[\w.\-]+@[\w.\-]+\b', '', raw)  # strip bare email
    raw = re.sub(r'\s+', ' ', raw).strip(' ,;')
    # "Mullins, Linda" -> "Linda Mullins" (Outlook last,first export form)
    m = re.match(r'^([A-Z][a-z]+),\s+([A-Z][a-z]+)$', raw)
    if m:
        raw = f'{m.group(2)} {m.group(1)}'
    return raw

# Strong document-section markers that signal the email body has ended and
# unrelated packet content (staff report / ordinance / agenda boilerplate) begins.
END_MARKER_RE = re.compile(
    r'\n[ \t\x0c]*(STAFF REPORT|REPORT OF ACTION|ORDINANCE \d|RESOLUTION \d|'
    r'COMMUNITY DEVELOPMENT|PLANNING COMMISSION STAFF|NEIGHBORHOOD AND PUBLIC COMMENT|'
    r'ATTACHMENTS?:|EXHIBIT [A-Z]\b|AGENDA ITEM|See Key Land Use Policies)', re.I)

# --- Page-continuation join (2026-07-02 fix) -------------------------------
# The old logic cut every letter at the first form-feed past 200 chars. That
# guaranteed zero cross-commenter bleed but silently TRUNCATED every multi-page
# letter mid-sentence (~12 of 81 rows; e.g. McCoard, Steed, Bogdin — confirmed
# against raw/packet_txt/). The replacement walks the letter page by page and
# joins a page only when it is a continuation of the SAME letter, using signals
# derived from the raw packet text (all 26 packets' page boundaries reviewed):
#
#   STOP  - blank page (letters never contain fully blank pages; unrelated
#           attachments / the next document follow),
#   STOP  - page opens like a NEW DOCUMENT: another email header (From:/Sent:/
#           To:/Subject:/Date:, incl. lowercase-address From: lines the block
#           regex can't match), a staff report / ordinance / resolution / memo
#           header, an OpenGov "opentownhall" comment-export page, a PLxx
#           case-number heading (eComment exports), or a "Timestamp Name ..."
#           multi-commenter eComment TABLE (the original bleed hazard),
#   JOIN  - page opens mid-sentence (lowercase word, opening bracket/quote, or
#           bullet) -> unambiguous continuation of the same letter,
#   else  - page opens with capitalized prose (new sentence/caption): JOIN only
#           if the letter so far does NOT already end in the sender's signature
#           (sender's first/last name in the last 8 non-blank lines); a signed
#           letter is finished, whatever follows is other packet content.
#
# Both original guarantees re-verified after the change: 0 cross-commenter
# bleed in all rows AND multi-page letters complete through their signatures.

NEW_DOC_LINE_RE = re.compile(
    r'^(?:(?:From|Sent|To|Cc|Subject|Date|Re):\s|'
    r'PROVO MUNICIPAL COUNCIL\b|'
    r'.*\bSTAFF REPORT\b|.*\bStaff Report\b|'
    r'.*\bORDINANCE\s+\d{4}|^ORDINANCE\b|^RESOLUTION\b|'
    r'Memo\b|'
    r'Timestamp\s+Name\b|'
    r'.*\bPL[A-Z]{2}\d{6,}|'
    r'.*(?:opentownhall\.com|Created with OpenGov))')

CONTINUATION_START_RE = re.compile(r'^[a-z(\[•\-–—"\'‘“]')

def _page_is_new_document(page_lines):
    """True if the page's opening lines look like another document/email."""
    for ln in page_lines[:3]:
        if NEW_DOC_LINE_RE.match(ln):
            return True
    return False

def _letter_ended(page, frm):
    """True if the page already ends in the sender's signature."""
    lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
    parts = [p for p in re.split(r'[\s,]+', frm) if len(p) >= 3]
    for ln in lines[-8:]:
        for p in parts:
            if re.search(r'\b' + re.escape(p) + r'\b', ln, re.I):
                return True
    return False

def scrub_body(body, frm=''):
    body = CAUTION_RE.sub('', body)
    # Walk the letter across page breaks: join genuine continuation pages,
    # stop at the first page that belongs to another document / commenter.
    pages = body.split('\x0c')
    kept = [pages[0]]
    for pg in pages[1:]:
        plines = [ln.strip() for ln in pg.splitlines() if ln.strip()]
        if not plines:
            break                                   # blank page = boundary
        if _page_is_new_document(plines):
            break                                   # next document begins
        if not CONTINUATION_START_RE.match(plines[0]) and _letter_ended(kept[-1], frm):
            break                                   # letter already signed off
        kept.append(pg)
    body = '\n'.join(kept)
    # cut at the first strong section marker (unrelated packet content)
    mend = END_MARKER_RE.search(body)
    if mend and mend.start() > 60:
        body = body[:mend.start()]
    lines = [ln.strip(' \t\x0c') for ln in body.splitlines()]
    lines = [ln for ln in lines if ln]
    txt = ' '.join(lines)
    txt = re.sub(r'\s+', ' ', txt).strip()
    return txt

# Email block: a From: line (capitalized, real name/email), through to the next From:
BLOCK_RE = re.compile(
    r'^[ \t\x0c]*From:[ \t]+(?P<from>[A-Z][^\n]*?)\n'
    r'(?P<mid>(?:[ \t\x0c]*(?:Sent|To|Cc|Subject|Date|Re):[^\n]*\n)+)',
    re.M)

def parse_packet(path, dropped):
    text = open(path, encoding='utf-8', errors='replace').read()
    rows = []
    # find all From: block starts
    starts = [m for m in BLOCK_RE.finditer(text)]
    for i, m in enumerate(starts):
        frm = clean_name(m.group('from'))
        mid = m.group('mid')
        sent = ''
        subject = ''
        ms = re.search(r'Sent:[ \t]*([^\n]+)', mid)
        if ms: sent = ms.group(1).strip()
        if not sent:
            md = re.search(r'Date:[ \t]*([^\n]+)', mid)
            if md: sent = md.group(1).strip()
        msub = re.search(r'Subject:[ \t]*([^\n]+)', mid)
        if msub: subject = re.sub(r'\s+',' ',msub.group(1)).strip()
        # body = from end of header block to next block start (or +6000 chars)
        body_start = m.end()
        body_end = starts[i+1].start() if i+1 < len(starts) else min(len(text), body_start+8000)
        body = text[body_start:body_end]
        comment = scrub_body(body, frm)
        # Drop staff senders / internal routing
        sender_raw = m.group('from')
        bn = os.path.basename(path)
        if STAFF_SENDER_RE.search(sender_raw) or STAFF_SENDER_RE.search(frm):
            dropped.append({'date':'', 'contact_name':frm, 'comment':comment[:120],
                            'source_file':bn, '_drop_reason':'city_staff_or_internal_sender'})
            continue
        # Known non-public senders (staff replies / vendors / applicant) by name
        nlow = frm.lower()
        if any(b in nlow for b in NAME_BLOCKLIST):
            dropped.append({'date':'', 'contact_name':frm, 'comment':comment[:120],
                            'source_file':bn, '_drop_reason':'staff_vendor_or_applicant'})
            continue
        if not frm or len(frm) < 3:
            dropped.append({'date':'', 'contact_name':frm, 'comment':comment[:120],
                            'source_file':bn, '_drop_reason':'no_name'})
            continue
        if len(comment) < 40:
            dropped.append({'date':'', 'contact_name':frm, 'comment':comment,
                            'source_file':bn, '_drop_reason':'too_short_non_substantive'})
            continue
        date_iso = norm_date(sent)
        # fall back to packet/meeting date from filename
        flag = []
        if not date_iso:
            mdate = re.search(r'packet_(\d{4}-\d{2}-\d{2})', os.path.basename(path))
            if mdate:
                date_iso = mdate.group(1)
                flag.append('date_from_filename')
        # genuine comment but with a junk/placeholder sender name -> keep, flag it
        if JUNK_NAME_RE.match(frm) or re.match(r'^(\w+)\s+\1$', frm, re.I):
            flag.append('name_unreliable')
        # Backstop cap only (2026-07-02: raised 6000 -> 20000 so the page-join fix
        # can emit complete multi-page letters; longest genuine submission is
        # ~20k chars incl. its quoted-policy attachment; no row hits the cap).
        if len(comment) > 20000:
            comment = comment[:20000].rsplit(' ', 1)[0] + ' …[truncated]'
            flag.append('truncated_long')
        rows.append({
            'date': date_iso,
            'contact_name': frm,
            'subject': subject,
            'topic': '',
            'comment': comment,
            'district': '',
            'source': 'agenda_packet',
            'has_attachment': 'True',
            'source_file': 'public_comments/raw/packet_txt/' + os.path.basename(path),
            'page_numbers': '',
            'period_start': '',
            'period_end': '',
            'date_normalized': date_iso,
            'quality_flag': ';'.join(flag),
        })
    return rows

def main():
    all_rows = []
    dropped = []
    for path in sorted(glob.glob(os.path.join(RAW_TXT, 'packet_*.txt'))):
        rows = parse_packet(path, dropped)
        if rows:
            print(f"{os.path.basename(path)}: {len(rows)} genuine written comments")
        all_rows.extend(rows)
    # de-dup on (name, date, first 80 chars)
    seen = set(); dedup = []
    for r in all_rows:
        key = (r['contact_name'].lower(), r['date_normalized'], r['comment'][:80].lower())
        if key in seen: continue
        seen.add(key); dedup.append(r)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=SLC_COLS)
        w.writeheader()
        for r in dedup:
            w.writerow(r)
    with open(DROPPED, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['date','contact_name','comment','source_file','_drop_reason'])
        w.writeheader()
        for r in dropped:
            w.writerow(r)
    print(f"\nTotal genuine written comments written: {len(dedup)}")
    print(f"Dropped (audit): {len(dropped)}")
    from collections import Counter
    print("By year:", dict(Counter((r['date_normalized'] or '?')[:4] for r in dedup)))

if __name__ == '__main__':
    main()
