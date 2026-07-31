#!/usr/bin/env python3
"""
extract_packet_true_comments.py — genuine resident comments from the LARGE ?packet=true
Planning-Commission land-use packets (fetched + text-extracted by harvest_packet_true.py
into raw/packet_true_txt/; binaries discarded per SCHEMA_SPEC §9).

These packets differ from the retained Minutes-view PDFs: their staff reports append a
"Public Comments from Residents" section carrying standalone resident LETTERS (not the
From:/Sent: forwarded-email format), interleaved with developer "letters of intent",
Community-Council recommendations, consultant memos, and staff reports.  The bar is
unchanged (Provo/SLC): keep ONLY genuine public-submitted written comments by a RESIDENT;
exclude every applicant / developer / staff / consultant / agency / community-council
author.  Verbatim; never fabricate; honest exclusions logged to the dropped audit.

Two channels, both gated hard and logged:
  A. EMAIL blocks — From: + a real Sent:/Date: timestamp (staff-report "From:/To:/Meeting
     Date:" memo headers have NO Sent: line, so they are excluded structurally).
  B. LETTER blocks — signature-anchored: a sign-off (Sincerely/Regards/Thank you…) with a
     recoverable PERSON signer, bounded back to the nearest salutation/page-break.

Positive gate (must be present): a first-person RESIDENT dwelling self-identification
(RESIDENT_INCL_RE — "I live in", "my husband and I have been residents", "as a homeowner",
"our neighborhood", …).  Negative gate (must be ABSENT in body AND signer): org/role
markers (ROLE_EXCL_RE — Director/Corporation/Developer/Realtor/AICP/PE/Planner/LLC/…) and
staff/applicant document markers (DOC_EXCL_RE — "letter of intent", "STAFF REPORT",
"respectfully submits", "on behalf of", "Meeting Date:", …).

Output: all_comments_packet_true.csv (SLC 14-col) + all_comments_packet_true_dropped.csv.
The merge into the canonical all_comments_clean.csv (dedup vs the retained-set 9) is done
by build_comments.py.  NO network.
"""
import csv, os, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
RAW_TXT = os.path.join(HERE, "raw", "packet_true_txt")
OUT = os.path.join(HERE, "all_comments_packet_true.csv")
DROPPED = os.path.join(HERE, "all_comments_packet_true_dropped.csv")

SLC_COLS = ['date', 'contact_name', 'subject', 'topic', 'comment', 'district', 'source',
            'has_attachment', 'source_file', 'page_numbers', 'period_start', 'period_end',
            'date_normalized', 'quality_flag']

MAX_CHARS = 6_000_000   # guard against pdftotext blowups (2019-09-18 = 191M chars garbage)

# ---- gates -----------------------------------------------------------------
# A first-person RESIDENT dwelling self-identification (the positive signal).
RESIDENT_INCL_RE = re.compile(
    r'\b('
    r'I (?:live|have lived|reside|am living)\b(?:[^.\n]{0,20}?\b(?:in|at|on|near|across|adjacent|next)\b)?|'
    r"I(?:'ve| have)? ?(?:am|have been)?\s*(?:a|an)?\s*(?:\d+[\s-]*year[\s-]*)?resident\b|"
    r'I am a (?:resident|homeowner|neighbor|home ?owner)\b|'
    r'my (?:husband|wife|family|spouse|partner) and I (?:have )?(?:been residents|live|reside|own|bought|have lived|moved)|'
    r'we (?:live|have lived|reside|moved here|are residents|are homeowners|own our|bought our|are newcomers)|'
    r'I (?:own|have owned|bought|purchased) (?:a |my |our )?(?:home|house|condo|property|residence|unit)|'
    r'as a (?:resident|homeowner|neighbor|home ?owner|nearby resident|long[\s-]?time resident|concerned resident)|'
    r'our (?:home|house|condo|neighborhood|property|street|community|units?|HOA|yard|backyard|homes)\b|'
    r'in (?:my|our) neighborhood|across the street from|down the street|in my back ?yard|'
    r'(?:I|we) (?:have )?live[d]? (?:here|nearby|next to|adjacent)|homeowner in|'
    r'a resident (?:of|in|who|and)|residents? (?:of|in) (?:Millcreek|Lexington|Old Farm|the|our|this)'
    r')', re.I)

# org / professional-role markers — an author with any of these is NOT a resident commenter.
ROLE_EXCL_RE = re.compile(
    r'\b('
    r'director|executive|president|vice[\s-]?president|\bceo\b|\bcfo\b|\bcoo\b|founder|'
    r'realtor|broker|corporation|\bcorp\b|\bllc\b|\bl\.?l\.?c\b|\binc\b|\bl\.?p\.?\b|company|'
    r'develop(?:er|ment)|consultant|consulting|architect|engineer(?:ing)?|\bp\.?e\.?\b|\baicp\b|'
    r'\bplanner\b|planning (?:division|manager|director)|attorney|\besq\b|law (?:office|firm)|'
    r'\bmanager\b|coordinator|administrator|superintendent|principal|\bassociate[s]?\b|'
    r'\bpartners?\b|realty|properties|holdings|\bgroup\b|community council|chamber of commerce|'
    r'on behalf of|the applicant|our client|our (?:business|firm|company)|city staff'
    r')\b', re.I)

# staff/applicant DOCUMENT markers — the block is a staff report / letter of intent /
# applicant application / official body recommendation, not a resident comment.
DOC_EXCL_RE = re.compile(
    r'(letter of intent|staff report|synopsis and scope|scope of decision|'
    r'respectfully submits|meeting date:|file ?no\.?:|prepared by:|report of action|'
    r'planning commission staff|recommend(?:s|ed|ing)? approval|we are recommending|'
    r'motion:\s|findings:|justification for rezoning|project description:|'
    r'conditions of approval|on behalf of (?:the |our )?(?:applicant|property owner|owner|'
    r'[A-Z]|client)|(?:is |are )?pleased to submit|please find (?:attached|enclosed) (?:our|the) '
    r'(?:application|request)|(?:rezone|rezoning|subdivision|conditional use permit|cup) '
    r'(?:request|application)(?: is)?|we (?:propose|are proposing|request approval|seek approval)|'
    r'this (?:letter of intent|application) )', re.I)

STAFF_SENDER_RE = re.compile(
    r'(@millcreek\.us|@millcreekut\.gov|@millcreek\.com|planning\s+commission|planning\s+division|'
    r'city\s+recorder|community\s+development|city\s+attorney|\baicp\b|\bpe\b|\bplanner\b|'
    r'engineer|director|coordinator|administrator|no-?reply|noreply|notification|staff|department)', re.I)

# tokens that prove a "name" is really an org / body / title / form-field, not a person.
NON_PERSON_TOKENS = {
    'city', 'council', 'commission', 'committee', 'board', 'department', 'planning', 'public',
    'comment', 'comments', 'form', 'online', 'submittal', 'meeting', 'millcreek', 'community',
    'agency', 'corporation', 'common', 'development', 'associates', 'partners', 'realty',
    'properties', 'holdings', 'group', 'staff', 'mayor', 'director', 'llc', 'inc', 'company',
    'name', 'address', 'subject', 'date', 'sent', 'from', 'zone', 'zoning', 'petition',
    'hoa', 'management', 'district', 'the', 'dear', 'sincerely', 'regards', 'hello', 'thank',
}

NAME_BLOCKLIST = {
    'elyse sullivan', 'carlos estudillo', 'shawn lamar', 'brad sanderson', 'francis lilly',
    'sean murray', 'roger dudley', 'blaine gehring', 'seishi yamagata', 'aimee mcconkie',
    'aimee s mcconkie', 'jeff silvestrini', 'jeffrey silvestrini',
}

MONTHS = {m.lower(): i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
     'September', 'October', 'November', 'December'], 1)}

SIGNOFF_RE = re.compile(
    r'^[ \t]*(Sincerely(?: yours)?|Regards|Best regards|Warm(?:est)? regards|Kind regards|'
    r'Respectfully(?: submitted| yours)?|Thank you[^\n]{0,70}|Thanks(?: again| so much| you)?|'
    r'Cordially|With regards|With gratitude|Gratefully|Yours truly|Very truly yours|'
    r'Best,?|Warmly)[ \t]*[,\.]?[ \t]*$', re.I | re.M)

# An INLINE sign-off that carries the signer on the same line ("Best, Gail Richards (Ave)").
SIGNOFF_INLINE_RE = re.compile(
    r'^[ \t]*(?:Sincerely(?: yours)?|Regards|Best regards|Best|Warm(?:est)? regards|'
    r'Kind regards|Respectfully|Cordially|Warmly|Gratefully|Thanks|Thank you)[,][ \t]+'
    r"[A-Z][A-Za-z'\.\-]+(?:[ \t]+[A-Z][A-Za-z'\.\-]+){0,3}[ \t]*(?:\([^)]*\))?[ \t]*$", re.M)

# A block that merely FORWARDS someone else's message (the From: sender is a router, and the
# real author is signed inside) — attributing it to the forwarder would misattribute; drop it.
FORWARD_WRAPPER_RE = re.compile(
    r'^\W{0,20}(?:can you (?:please )?forward|please forward this|forwarding this|'
    r'see (?:below|attached|the below)|fyi\b|fwd\b|here is|passing (?:this )?along).{0,80}?'
    r'(?:begin forwarded message|from:|\bfw\b|below)', re.I | re.S)

SALUT_RE = re.compile(
    r'^[ \t]*(Dear [^\n]{0,60}|Hi,? [A-Z][^\n]{0,40}|Hello[^\n]{0,40}|'
    r'To whom it may concern|Mayor[^\n]{0,40},|Members of [^\n]{0,50},|'
    r'(?:Millcreek )?(?:City )?Planning Commission[^\n]{0,25},?|'
    r'Millcreek (?:City )?Council[^\n]{0,25},?|'
    r'Commissioners?[ ,]|Council( ?[Mm]embers?)?[ ,]|'
    r'Greetings[^\n]{0,30})[ \t]*$', re.M)

NAMELINE_RE = re.compile(r"^[ \t]*([A-Z][A-Za-z'\.\-]+(?:[ \t]+[A-Z][A-Za-z'\.\-]+){0,3})[ \t]*$")
ADDR_PHONE_RE = re.compile(r'(\d{3,}|@|\bUT\b|\bUtah\b|street|\bave\b|\bdr\b|\brd\b|\bln\b|\bblvd\b|\bapt\b|\bunit\b)', re.I)

EMAIL_BLOCK_RE = re.compile(
    r'^[ \t\x0c]*From:[ \t]*(?P<from>[A-Za-z][^\n]*?)\n'
    r'(?P<mid>(?:[ \t\x0c]*(?:Sent|To|Cc|Subject|Date|Re):[^\n]*\n)+)', re.M)


def norm_date(s):
    if not s:
        return ''
    m = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', s)
    if m and m.group(1).lower() in MONTHS:
        return f"{int(m.group(3)):04d}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}"
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', s)
    if m:
        y = int(m.group(3))
        y = y + 2000 if y < 100 else y
        return f"{y:04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
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


def is_person_name(nm):
    if not nm or len(nm) < 4:
        return False
    if ROLE_EXCL_RE.search(nm) or nm.lower() in NAME_BLOCKLIST:
        return False
    toks = nm.split()
    if not (2 <= len(toks) <= 4):
        return False
    if any(t.lower().strip(".,'-") in NON_PERSON_TOKENS for t in toks):
        return False
    return all(re.match(r"^[A-Z][A-Za-z'\.\-]+$", t) for t in toks)


def body_gate(body, author_ctx):
    """Drop-reason if body/author isn't a genuine resident comment, else ''.
    ROLE_EXCL is applied ONLY to the author context (signer + signature/letterhead lines),
    never the whole body — residents routinely discuss 'the developer', 'the architect',
    'our HOA', etc.  The body itself is screened for STAFF/APPLICANT DOCUMENT markers only."""
    if author_ctx and ROLE_EXCL_RE.search(author_ctx):
        return 'author_org_or_professional_role'
    if DOC_EXCL_RE.search(body):
        return 'staff_or_applicant_document'
    if not RESIDENT_INCL_RE.search(body):
        return 'no_resident_self_identification'
    return ''


def scrub(s):
    s = re.sub(r'CAUTION:.*?(safe\.)', '', s, flags=re.S | re.I)
    s = re.sub(r'^\s*Page \d+ of \d+\s*$', '', s, flags=re.M)
    lines = [ln.strip(' \t\x0c') for ln in s.splitlines()]
    lines = [ln for ln in lines if ln]
    return re.sub(r'\s+', ' ', ' '.join(lines)).strip()


def find_signer(text, so_start, so_end):
    """Recover the signer name for a sign-off, WITHOUT bleeding into the next letter
    (stop at the first form-feed).  Handles inline 'Best, Jane Doe' and 'Name (Location)'."""
    # inline sign-off: the sign-off line itself carries the name ("Best, Gail Richards (…)")
    soff_line = text[so_start:so_end]
    mi = re.match(r"^[ \t]*(?:Sincerely|Regards|Best(?: regards)?|Thanks|Thank you|"
                  r"Respectfully|Cordially|Warmly|Gratefully)[,\.]?[ \t]+"
                  r"([A-Z][A-Za-z'\.\-]+(?:[ \t]+[A-Z][A-Za-z'\.\-]+){0,3})",
                  soff_line, re.I)
    if mi:
        nm = re.sub(r'\s+', ' ', mi.group(1)).strip()
        if is_person_name(nm):
            return nm
    seg = text[so_end:so_end + 300]
    ff = seg.find('\x0c')
    if ff != -1:
        seg = seg[:ff]
    seen = 0
    for ln in seg.splitlines():
        if not ln.strip():
            continue
        seen += 1
        if seen > 6:
            break
        cand = re.sub(r'\s*\([^)]*\)\s*$', '', ln).strip()   # drop trailing "(Evergreen Ave)"
        m = NAMELINE_RE.match(cand)
        if m and is_person_name(m.group(1).strip()) and not ADDR_PHONE_RE.search(cand):
            return m.group(1).strip()
    return ''


def channel_letters(text, packet_date, bn, rows, dropped):
    """Signature-anchored resident letters (channel B)."""
    signoffs = sorted(list(SIGNOFF_RE.finditer(text)) + list(SIGNOFF_INLINE_RE.finditer(text)),
                      key=lambda m: m.start())
    saluts = [m.start() for m in SALUT_RE.finditer(text)]
    pagebreaks = [m.start() for m in re.finditer(r'\x0c', text)]
    prev_end = 0
    for so in signoffs:
        so_start, so_end = so.start(), so.end()
        signer = find_signer(text, so_start, so_end)
        # letter start: nearest salutation before the sign-off, bounded by prev letter end
        cands = [s for s in saluts if prev_end <= s < so_start]
        if cands:
            start = cands[-1]
        else:
            pbs = [p for p in pagebreaks if prev_end <= p < so_start]
            start = max(prev_end, (pbs[-1] if pbs else so_start - 6000))
        body_raw = text[start:so_start]
        body = scrub(body_raw)
        prev_end = so_end
        # regions dominated by email/form headers belong to channels A / C, not here.
        if ('Online Form Submittal' in body_raw or 'noreply' in body_raw.lower()
                or len(re.findall(r'^[ \t]*Sent:', body_raw, re.M)) >= 1
                or '@millcreek' in body_raw.lower()):
            continue
        if not signer:
            if (RESIDENT_INCL_RE.search(body) and not DOC_EXCL_RE.search(body)
                    and len(body) >= 60):
                dropped.append(dict(date='', contact_name='', comment=body[:140],
                                    source_file=bn, _drop_reason='no_recoverable_signer'))
            continue
        # author context = signer + the signature block (sign-off + following title/company
        # lines), STOPPING at the first form-feed so it never bleeds into the next letter's
        # header (which for a Millcreek packet is often 'Sean Murray, Planner').
        sig_seg = text[so_end:so_end + 260]
        ff = sig_seg.find('\x0c')
        if ff != -1:
            sig_seg = sig_seg[:ff]
        author_ctx = signer + ' ' + text[so_start:so_end] + ' ' + sig_seg
        reason = body_gate(body, author_ctx)
        if reason:
            dropped.append(dict(date='', contact_name=signer, comment=body[:140],
                                source_file=bn, _drop_reason=reason))
            continue
        if len(body) < 60:
            dropped.append(dict(date='', contact_name=signer, comment=body,
                                source_file=bn, _drop_reason='too_short_or_ocr_unreadable'))
            continue
        # date: a date line in the first ~600 chars of the letter, else packet date
        flag = []
        head = text[start:start + 700]
        date_iso = ''
        for ln in head.splitlines():
            date_iso = norm_date(ln)
            if date_iso:
                break
        if not date_iso:
            date_iso = packet_date
            flag.append('date_from_filename')
        msub = re.search(r'^[ \t]*RE:[ \t]*([^\n]+)', head, re.I | re.M)
        subject = re.sub(r'\s+', ' ', msub.group(1)).strip()[:120] if msub else ''
        garble = sum(1 for c in body if not (c.isalnum() or c.isspace() or c in ".,!?'\"-()"))
        if body and garble / len(body) > 0.12:
            flag.append('ocr_garbled')
        flag.append('letter_appendix')
        if len(body) > 20000:
            body = body[:20000].rsplit(' ', 1)[0] + ' …[truncated]'
            flag.append('truncated_long')
        rows.append({'date': date_iso, 'contact_name': signer, 'subject': subject, 'topic': '',
                     'comment': body, 'district': '', 'source': 'agenda_packet',
                     'has_attachment': 'True', 'source_file': 'public_comments/' + bn,
                     'page_numbers': '', 'period_start': '', 'period_end': '',
                     'date_normalized': date_iso, 'quality_flag': ';'.join(flag)})


def channel_emails(text, packet_date, bn, rows, dropped):
    """Forwarded resident EMAIL blocks with a real Sent:/Date: timestamp (channel A)."""
    starts = list(EMAIL_BLOCK_RE.finditer(text))
    for i, m in enumerate(starts):
        mid = m.group('mid')
        # require a real Sent: / Date: header (staff-report memos have none)
        sm = re.search(r'(?:Sent|Date):[ \t]*([^\n]+)', mid)
        if not sm:
            continue
        sent = sm.group(1).strip()
        if not norm_date(sent) and not re.search(r'\d{1,2}[:/]\d', sent):
            continue
        frm = clean_name(m.group('from'))
        msub = re.search(r'Subject:[ \t]*([^\n]+)', mid)
        subject = re.sub(r'\s+', ' ', msub.group(1)).strip()[:120] if msub else ''
        end = starts[i + 1].start() if i + 1 < len(starts) else min(len(text), m.end() + 6000)
        body = scrub(text[m.end():end])
        if STAFF_SENDER_RE.search(m.group('from')) or (frm and ROLE_EXCL_RE.search(frm)):
            dropped.append(dict(date='', contact_name=frm, comment=body[:140],
                                source_file=bn, _drop_reason='city_staff_or_role_sender'))
            continue
        if FORWARD_WRAPPER_RE.match(body):
            dropped.append(dict(date='', contact_name=frm, comment=body[:140],
                                source_file=bn, _drop_reason='forwarder_wrapper_real_author_inside'))
            continue
        if not is_person_name(frm):
            dropped.append(dict(date='', contact_name=frm, comment=body[:140],
                                source_file=bn, _drop_reason='sender_not_person_name'))
            continue
        reason = body_gate(body, frm)
        if reason:
            dropped.append(dict(date='', contact_name=frm, comment=body[:140],
                                source_file=bn, _drop_reason=reason))
            continue
        if len(body) < 60:
            dropped.append(dict(date='', contact_name=frm, comment=body,
                                source_file=bn, _drop_reason='too_short_or_ocr_unreadable'))
            continue
        flag = ['email_block']
        date_iso = norm_date(sent) or packet_date
        if not norm_date(sent):
            flag.append('date_from_filename')
        garble = sum(1 for c in body if not (c.isalnum() or c.isspace() or c in ".,!?'\"-()"))
        if body and garble / len(body) > 0.12:
            flag.append('ocr_garbled')
        if len(body) > 20000:
            body = body[:20000].rsplit(' ', 1)[0] + ' …[truncated]'
            flag.append('truncated_long')
        rows.append({'date': date_iso, 'contact_name': frm, 'subject': subject, 'topic': '',
                     'comment': body, 'district': '', 'source': 'agenda_packet',
                     'has_attachment': 'True', 'source_file': 'public_comments/' + bn,
                     'page_numbers': '', 'period_start': '', 'period_end': '',
                     'date_normalized': date_iso, 'quality_flag': ';'.join(flag)})


# Millcreek FormCenter "Public Comments" web-form submissions, emailed to staff and bundled
# into the packet (Subject: "Online Form Submittal: Public Comments").  Structured fields —
# the cleanest, most unambiguous genuine-resident channel (the city's own comment form).
FORM_ANCHOR_RE = re.compile(r'Online Form Submittal:\s*Public Comments')


# A CivicPlus form email renders each field as "<Label><2+ spaces><value>" on one line, the
# value wrapping with deep indentation.  A value ends at the next field-label line, a blank
# gap, "Supporting Documents", or the next form submittal.
_NEXT_FIELD_RE = (r'(?=\n[ \t]*(?:First Name|Last Name|Address|City|State|Zip Code|'
                  r'Phone Number|Email Address|Public Meeting|Meeting Date|Comment Subject|'
                  r'Public Comment|Supporting Documents|Online Form Submittal|Field not completed)'
                  r'\b|\n[ \t]*\n[ \t]*\n|\Z)')


def _form_field(block, label):
    # label followed by >=2 spaces (distinguishes the "Public Comment" FIELD from the
    # "Public Comments" section title, which stands alone on its line).
    m = re.search(r'(?<!\S)' + re.escape(label) + r'[ \t]{2,}(.+?)' + _NEXT_FIELD_RE,
                  block, re.S)
    if not m:
        return ''
    val = re.sub(r'\s+', ' ', m.group(1)).strip()
    return '' if val.lower().startswith('field not completed') else val


def channel_form(text, packet_date, bn, rows, dropped):
    anchors = [m.start() for m in FORM_ANCHOR_RE.finditer(text)]
    for i, a in enumerate(anchors):
        end = anchors[i + 1] if i + 1 < len(anchors) else min(len(text), a + 6000)
        block = text[a:end]
        # the email Date: header just above the anchor gives the submission timestamp
        pre = text[max(0, a - 200):a]
        dm = re.search(r'Date:[ \t]*([^\n]+)', pre)
        fn = _form_field(block, 'First Name')
        ln = _form_field(block, 'Last Name')
        addr = _form_field(block, 'Address')
        city = _form_field(block, 'City')
        mdate = _form_field(block, 'Meeting Date')
        subj = _form_field(block, 'Comment Subject')
        comment = _form_field(block, 'Public Comment')
        name = re.sub(r'\s+', ' ', f'{fn} {ln}').strip()
        if not name or not is_person_name(name):
            if comment and len(comment) >= 40:
                dropped.append(dict(date='', contact_name=name, comment=comment[:140],
                                    source_file=bn, _drop_reason='form_no_person_name'))
            continue
        if len(comment) < 40:
            dropped.append(dict(date='', contact_name=name, comment=comment,
                                source_file=bn, _drop_reason='form_comment_too_short'))
            continue
        flag = ['web_form']
        date_iso = norm_date(mdate) or norm_date(dm.group(1) if dm else '') or packet_date
        if not (norm_date(mdate) or (dm and norm_date(dm.group(1)))):
            flag.append('date_from_filename')
        garble = sum(1 for c in comment if not (c.isalnum() or c.isspace() or c in ".,!?'\"-()"))
        if comment and garble / len(comment) > 0.12:
            flag.append('ocr_garbled')
        if len(comment) > 20000:
            comment = comment[:20000].rsplit(' ', 1)[0] + ' …[truncated]'
            flag.append('truncated_long')
        district = ''
        rows.append({'date': date_iso, 'contact_name': name, 'subject': subj, 'topic': '',
                     'comment': comment, 'district': district, 'source': 'agenda_packet',
                     'has_attachment': 'True', 'source_file': 'public_comments/' + bn,
                     'page_numbers': '', 'period_start': '', 'period_end': '',
                     'date_normalized': date_iso, 'quality_flag': ';'.join(flag)})


def parse_packet(path, rows, dropped):
    bn = 'raw/packet_true_txt/' + os.path.basename(path)
    md = re.search(r'packet_(\d{4}-\d{2}-\d{2})', os.path.basename(path))
    packet_date = md.group(1) if md else ''
    text = open(path, encoding='utf-8', errors='replace').read()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]   # pdftotext-blowup guard (flagged in fetch log via text_chars)
    channel_form(text, packet_date, bn, rows, dropped)
    channel_emails(text, packet_date, bn, rows, dropped)
    channel_letters(text, packet_date, bn, rows, dropped)


def main():
    rows, dropped = [], []
    for path in sorted(glob.glob(os.path.join(RAW_TXT, 'packet_*.txt'))):
        before = len(rows)
        parse_packet(path, rows, dropped)
        if len(rows) > before:
            print(f"{os.path.basename(path)}: +{len(rows)-before} kept")
    # in-file dedup
    seen, dedup = set(), []
    for r in rows:
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
    print(f"\npacket=true kept: {len(dedup)}  dropped(audit): {len(dropped)}")
    print("kept by year:", dict(Counter((r['date_normalized'] or '?')[:4] for r in dedup)))
    print("drop reasons:", dict(Counter(d['_drop_reason'] for d in dropped)))


if __name__ == '__main__':
    main()
