#!/usr/bin/env python3
"""
extract_packet_comments.py — Millcreek genuine written public comments from PC packets.

Deterministically rebuilds all_comments_clean.csv from the comment-bearing packet text
kept by harvest_packets.py in raw/packet_txt/packet_<date>.txt.  Millcreek's genuine
written comments are forwarded/attached resident EMAIL blocks bundled into Planning
Commission packets (the public's own words on contentious land-use items — chiefly the
2021 & 2024 digital-billboard fights and a few subdivision/RCOZ items).  Mirrors Provo's
extract_packet_comments.py (same SLC schema, same staff/applicant exclusion discipline):

  * parse each "From: <name>\n(Sent|To|Subject|Date):…" block; one row per block;
  * DROP non-public senders -> all_comments_dropped.csv: city staff / internal routing
    (@millcreek.us|@millcreekut.gov, role regex) + a reviewed name blocklist of the
    staff/chair FORWARDERS (Elyse Sullivan, Carlos Estudillo, Shawn LaMar, Brad
    Sanderson…) and the applicant/consultant side;
  * scrub the OCR/security noise, join a letter across page breaks only when the page is
    a genuine continuation (Provo's rule-based classifier), cut at the next document /
    header;
  * normalize the Sent:/Date: header -> ISO date_normalized (fallback: packet meeting
    date -> quality_flag=date_from_filename);
  * NEVER fabricate: an OCR-unreadable body under 40 chars is dropped (too_short), not
    guessed; garbled sender names are kept but flagged name_unreliable.

NO network.  Run harvest_packets.py first.
"""
import csv, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_TXT = os.path.join(HERE, "raw", "packet_txt")
OUT = os.path.join(HERE, "all_comments_clean.csv")
DROPPED = os.path.join(HERE, "all_comments_dropped.csv")

SLC_COLS = ['date', 'contact_name', 'subject', 'topic', 'comment', 'district', 'source',
            'has_attachment', 'source_file', 'page_numbers', 'period_start', 'period_end',
            'date_normalized', 'quality_flag']

STAFF_SENDER_RE = re.compile(
    r'(@millcreek\.us|@millcreekut\.gov|planning\s+commission|planning\s+division|'
    r'city\s+recorder|community\s+development|city\s+attorney|deputy|staff|department|'
    r'director|coordinator|administrator|no-?reply|notification)', re.I)

# Reviewed non-public senders: the staff/chair who FORWARD resident mail into the packet
# (their wrapper block is not a comment; the resident's inner block is captured on its
# own), plus consultant/applicant-side senders.
NAME_BLOCKLIST = {
    'elyse sullivan', 'carlos estudillo', 'shawn lamar', 'brad sanderson',
    'francis lilly', 'sean murray', 'roger dudley',   # Roger Dudley = applicant's consultant
}
JUNK_NAME_RE = re.compile(r'^(clinicalteam|test|anonymous|n/?a|none|unknown|m\s+m)\b', re.I)

MONTHS = {m.lower(): i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
     'September', 'October', 'November', 'December'], 1)}


def norm_date(sent_line):
    if not sent_line:
        return ''
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', sent_line)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', sent_line)
    if m:
        return f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return ''


def clean_name(raw):
    raw = re.sub(r'<[^>]*>', '', raw)
    raw = re.sub(r'\[[^\]]*\]', '', raw)
    raw = re.sub(r'\b[\w.\-]+@[\w.\-]+\b', '', raw)
    raw = re.sub(r'\s+', ' ', raw).strip(' ,;<>\'"-')
    m = re.match(r'^([A-Z][a-z]+),\s+([A-Z][a-z]+)$', raw)
    if m:
        raw = f'{m.group(2)} {m.group(1)}'
    return raw


# A leading residual email-header / recipient-list line (the inner forwarded block's
# To:/Cc:/Subject:/Sent:/Date: sometimes gets OCR-split away from the From: header the
# BLOCK_RE anchored on, so it lands at the top of the body).  Strip these before the
# real message so the stored `comment` is the resident's own words, not routing headers.
HEADER_LINE_RE = re.compile(
    r'^\s*(To|Cc|Bcc|From|Sent|Date|Subject|Re|Fwd?|Importance|Priority|'
    r'Attachments?|Original Message|On .+wrote)\b', re.I)


def strip_leading_headers(lines):
    """Drop leading header/recipient-list lines until the first line of real prose."""
    out = list(lines)
    # A forwarded inner header block ends at its "Subject:" line; when the recipient
    # list wrapped across lines (incl. a bare surname tail) the generic loop below would
    # stop early on that tail.  So if a "Subject:" echo sits in the first 6 lines AND
    # everything before it is header residue (no sentence punctuation), drop through and
    # including it — the resident's message starts after.
    for k in range(min(6, len(out))):
        if re.search(r'\bSubject:\s', out[k]):
            if all(not re.search(r'[.!?]', out[j]) for j in range(k)):
                out = out[k + 1:]
            break
    while out:
        ln = out[0]
        if not ln.strip():
            out.pop(0)
            continue
        # header at line start, OR a leading line that embeds a "Subject:" echo (OCR
        # merged the recipient tail + Subject onto one line ahead of the message).
        is_header = bool(HEADER_LINE_RE.match(ln)) or bool(re.search(r'\bSubject:\s', ln))
        # recipient-list fragment: an email+semicolon list, a <…>-led line, or a
        # semicolon name list (e.g. "Sieber; Tom Stephens; Shawn LaMar; …") — routing
        # metadata, not the resident's message.
        is_reciplist = (('@' in ln and ';' in ln) or ln.lstrip().startswith('<') or
                        (';' in ln and not re.search(r'[.!?]', ln) and len(ln) < 200))
        if is_header or is_reciplist:
            out.pop(0)
            continue
        break
    return out


END_MARKER_RE = re.compile(
    r'\n[ \t\x0c]*(STAFF REPORT|REPORT OF ACTION|ORDINANCE \d|RESOLUTION \d|'
    r'PLANNING COMMISSION STAFF|ATTACHMENTS?:|EXHIBIT [A-Z]\b|AGENDA ITEM|'
    r'-+\s*Original Message)', re.I)

NEW_DOC_LINE_RE = re.compile(
    r'^(?:(?:From|Sent|To|Cc|Subject|Date|Re):\s|'
    r'.*\bSTAFF REPORT\b|^ORDINANCE\b|^RESOLUTION\b|Memo\b|'
    r'-+\s*Original Message)')
CONTINUATION_START_RE = re.compile(r'^[a-z(\[•\-–—"\'‘“]')


def _page_is_new_document(page_lines):
    for ln in page_lines[:3]:
        if NEW_DOC_LINE_RE.match(ln):
            return True
    return False


def _letter_ended(page, frm):
    lines = [ln.strip() for ln in page.splitlines() if ln.strip()]
    parts = [p for p in re.split(r'[\s,]+', frm) if len(p) >= 3]
    for ln in lines[-8:]:
        for p in parts:
            if re.search(r'\b' + re.escape(p) + r'\b', ln, re.I):
                return True
    return False


def scrub_body(body, frm=''):
    body = re.sub(r'CAUTION:.*?(safe\.)', '', body, flags=re.S | re.I)
    pages = body.split('\x0c')
    kept = [pages[0]]
    for pg in pages[1:]:
        plines = [ln.strip() for ln in pg.splitlines() if ln.strip()]
        if not plines:
            break
        if _page_is_new_document(plines):
            break
        if not CONTINUATION_START_RE.match(plines[0]) and _letter_ended(kept[-1], frm):
            break
        kept.append(pg)
    body = '\n'.join(kept)
    mend = END_MARKER_RE.search(body)
    if mend and mend.start() > 60:
        body = body[:mend.start()]
    lines = [ln.strip(' \t\x0c') for ln in body.splitlines()]
    lines = [ln for ln in lines if ln]
    lines = strip_leading_headers(lines)
    return re.sub(r'\s+', ' ', ' '.join(lines)).strip()


BLOCK_RE = re.compile(
    r'^[ \t\x0c]*From:[ \t]*(?P<from>[A-Z][^\n]*?)\n'
    r'(?P<mid>(?:[ \t\x0c]*(?:Sent|To|Cc|Subject|Date|Re):[^\n]*\n)+)', re.M)


def parse_packet(path, dropped):
    text = open(path, encoding='utf-8', errors='replace').read()
    bn = os.path.basename(path)
    mdate = re.search(r'packet_(\d{4}-\d{2}-\d{2})', bn)
    packet_date = mdate.group(1) if mdate else ''
    rows = []
    starts = list(BLOCK_RE.finditer(text))
    for i, m in enumerate(starts):
        sender_raw = m.group('from')
        frm = clean_name(sender_raw)
        mid = m.group('mid')
        sent = ''
        ms = re.search(r'Sent:[ \t]*([^\n]+)', mid)
        if ms:
            sent = ms.group(1).strip()
        if not sent:
            md = re.search(r'Date:[ \t]*([^\n]+)', mid)
            if md:
                sent = md.group(1).strip()
        msub = re.search(r'Subject:[ \t]*([^\n]+)', mid)
        subject = re.sub(r'\s+', ' ', msub.group(1)).strip() if msub else ''
        body_start = m.end()
        body_end = starts[i + 1].start() if i + 1 < len(starts) else min(len(text), body_start + 8000)
        comment = scrub_body(text[body_start:body_end], frm)

        if STAFF_SENDER_RE.search(sender_raw) or STAFF_SENDER_RE.search(frm):
            dropped.append(dict(date='', contact_name=frm, comment=comment[:120],
                                source_file=bn, _drop_reason='city_staff_or_internal_sender'))
            continue
        if frm.lower() in NAME_BLOCKLIST or any(b in frm.lower() for b in NAME_BLOCKLIST):
            dropped.append(dict(date='', contact_name=frm, comment=comment[:120],
                                source_file=bn, _drop_reason='staff_forwarder_or_applicant'))
            continue
        if not frm or len(frm) < 3:
            dropped.append(dict(date='', contact_name=frm, comment=comment[:120],
                                source_file=bn, _drop_reason='no_name'))
            continue
        if len(comment) < 40:
            dropped.append(dict(date='', contact_name=frm, comment=comment,
                                source_file=bn, _drop_reason='too_short_or_ocr_unreadable'))
            continue

        flag = []
        date_iso = norm_date(sent)
        if not date_iso and packet_date:
            date_iso = packet_date
            flag.append('date_from_filename')
        if JUNK_NAME_RE.match(frm) or re.match(r'^(\w+)\s+\1$', frm, re.I):
            flag.append('name_unreliable')
        # OCR-noise heuristic: a body with a high non-word-character ratio is garbled
        garble = sum(1 for c in comment if not (c.isalnum() or c.isspace() or c in ".,!?'\"-()"))
        if comment and garble / len(comment) > 0.12:
            flag.append('ocr_garbled')
        # honest flag: residual routing metadata still leads the body (OCR-fragmented
        # inner-forward header the stripper could not fully isolate) — text is verbatim,
        # just not perfectly trimmed; never silently reworded.
        if re.match(r'^(<|.{0,60}?(Subject:|@\w))', comment) and '@' in comment[:80]:
            flag.append('header_residue')
        if len(comment) > 20000:
            comment = comment[:20000].rsplit(' ', 1)[0] + ' …[truncated]'
            flag.append('truncated_long')

        rows.append({
            'date': date_iso, 'contact_name': frm, 'subject': subject, 'topic': '',
            'comment': comment, 'district': '', 'source': 'agenda_packet',
            'has_attachment': 'True',
            'source_file': 'public_comments/raw/packet_txt/' + bn,
            'page_numbers': '', 'period_start': '', 'period_end': '',
            'date_normalized': date_iso, 'quality_flag': ';'.join(flag),
        })
    return rows


def main():
    all_rows, dropped = [], []
    for path in sorted(glob.glob(os.path.join(RAW_TXT, 'packet_*.txt'))):
        rows = parse_packet(path, dropped)
        if rows:
            print(f"{os.path.basename(path)}: {len(rows)} genuine written comments")
        all_rows.extend(rows)
    seen, dedup = set(), []
    for r in all_rows:
        key = (r['contact_name'].lower(), r['date_normalized'], r['comment'][:80].lower())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(r)
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=SLC_COLS)
        w.writeheader()
        w.writerows(dedup)
    with open(DROPPED, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=['date', 'contact_name', 'comment', 'source_file', '_drop_reason'])
        w.writeheader()
        w.writerows(dropped)
    from collections import Counter
    print(f"\nGenuine written comments: {len(dedup)}   dropped (audit): {len(dropped)}")
    print("By year:", dict(Counter((r['date_normalized'] or '?')[:4] for r in dedup)))


if __name__ == '__main__':
    main()
