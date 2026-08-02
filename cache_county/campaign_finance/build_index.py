#!/usr/bin/env python3
"""Regenerate index.csv + excluded.csv + unrecovered.csv for cache_county/campaign_finance.

Inputs (never modified):
  raw/_fetch_log.jsonl   one JSON row per attempted URL (url, sha256, bytes, http_status, …)
  raw/<year>/*.pdf       the retained filings, verbatim
  text/*.txt             the text sidecar for each retained PDF
  ../elections/cache_county_office_results_long.csv   office<->candidate evidence (2020/2022/2026)

Outputs (DERIVED — regenerate, never hand-edit):
  index.csv        one row per RETAINED, IN-SCOPE county-office filing
  excluded.csv     one row per acquired file classified OUT of scope (school board, etc.)
  unrecovered.csv  one row per listed filing whose bytes could not be retrieved

  vision/<key>.json      CURATED vision transcriptions of the cover page (schema
                         cache_cf_totals_v1). THE MOST AUTHORITATIVE OFFICE SOURCE — see
                         "The vision office layer" below and CLAUDE.md.

Classification discipline (see CLAUDE.md "How a filing is classified"):
  * a VISION READ of the office line on the rendered page image outranks everything else —
    it is the only channel that can read handwriting;
  * otherwise the PRINTED form header is read from the text sidecar — never the filename or
    portal label;
  * the stated "Office" line decides scope when the form prints one legibly;
  * the county form header alone is supporting evidence, NOT proof of a county office;
  * cycle parity (county offices are elected in EVEN years) is a cross-check, never a source;
  * nothing is guessed: an illegible office stays blank with needs_review=1.

The vision office layer
-----------------------
`vision/<sha1(canonical_path)[:8]>.json` is written ONCE per DISTINCT DOCUMENT (sha256) under
the lexicographically first of that document's index paths, and its `applies_to` list names
every index row the transcription covers — so the cross-channel byte-identical duplicates are
transcribed once and applied to each of their rows. Its `office_determination` block carries:
  scope       = county | out_of_scope | undetermined     (what the page itself establishes)
  office_std  = the normalized office, or '' when the page establishes none
  evidence    = a QUOTE of the page line the determination rests on
A `scope='out_of_scope'` read moves the row to excluded.csv carrying that quoted evidence in
`exclusion_reason` — a re-classification is recorded, never silently dropped.
"""
import csv, glob, json, os, re, unicodedata, collections, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
VISION = os.path.join(HERE, 'vision')
RAW_LOG = os.path.join(HERE, 'raw', '_fetch_log.jsonl')
ELECT = os.path.join(HERE, '..', 'elections', 'cache_county_office_results_long.csv')
LABELS = os.path.join(HERE, 'listing_labels.csv')   # archived listing rows: name + printed date

# ---------------------------------------------------------------- form families
# Printed (never handwritten) discriminators, in priority order. The statutory citation is
# the strongest: the county instrument cites 17-16-6.5, the school-board instrument cites
# 20A-11-1301..1305. Both survive OCR far better than the handwritten fields do.
COMBINED = re.compile(r'for\s+County\s+Offices?\s*(and|an d)?\s*(Local\s+)?School\s+Board', re.I)
SCHOOLHDR = re.compile(r'SCHOOL\s*BOARD\s*CANDIDATE', re.I)
SCHOOLCITE = re.compile(r'20A[\s\-–.]?4?11[\s\-–.]?13\d\d', re.I)
COUNTYCITE = re.compile(r'17[\s\-–.]?16[\s\-–.]?6\.?5', re.I)
CODE221 = re.compile(r'Cache\s+County\s+Code\s+2\.?2\s?1', re.I)
NAMEOFOFFICE = re.compile(r'Name\s+of\s+Office', re.I)
CAMPRPT = re.compile(r'F[EI1lI]?NANCIAL[\s.]*CA[MRNIÍ]{1,3}PAIGN[\s.]*RE?PORT', re.I)


def form_family(t):
    head = t[:1800]
    if COMBINED.search(head):
        return 'cache_cfd_combined'          # 2022+ "Candidate Financial Disclosure"
    if SCHOOLHDR.search(head) or SCHOOLCITE.search(head):
        return 'carr_school_board'           # pre-2022 school-board instrument (20A-11-1301..1305)
    if COUNTYCITE.search(head) or NAMEOFOFFICE.search(head) or \
            (CODE221.search(head) and not SCHOOLHDR.search(head)):
        return 'carr_county'                 # pre-2022 county instrument (17-16-6.5 / Code 2.21)
    if re.search(r'dissolution', t, re.I):
        return 'statement_of_dissolution'
    if CAMPRPT.search(head):
        return 'campaign_report_variant_unread'   # header legible, instrument variant is not
    return 'unclassified'


# ------------------------------------------------------- typed field extraction
STAMP = re.compile(r"(CLERK\s*[-/]|REC'?D|RECEIVED|ELECTIONS?\s+DIVISION|^Cache\s+County$|"
                   r'^\W*$|Document ID|Financial Campaign Report|Candidate Financial Disclosure|'
                   r'^(Cache\s+County\s+)?CLERK\s*/?\s*AUDITOR)', re.I)


def typed_office(t):
    """The Office field, ONLY where the form actually printed it as text.

    Two accepted shapes, both born-digital or near-born-digital:
      (a) the labelled block  `Office\\n…\\nType of Report`  (2025/2026 AcroForm exports);
      (b) an OCR line carrying an office phrase immediately followed by the filer's email
          (the 2025 scanned exports collapse the Office/Email columns onto one line).
    Everything else — clerk received-stamps, the form title, the statutory blurb — is
    rejected. A handwritten Office field yields '' (never a guess).
    """
    OFF = (r'\b(County\s+(Executive|Council|Attorney|Clerk|Auditor|Assessor|Recorder|Treasurer|'
           r'Surveyor|Sheriff)|Sheriff\S*\s+Office|School\s+Board|County\s+Commission)\b')
    m = re.search(r'^[ \t]*Office\b[^\n]*$(.{0,700}?)^\s*Type of Report', t, re.S | re.M)
    if m:
        for line in m.group(1).splitlines():
            s = re.sub(r'\s{2,}.*$', '', line).strip(' .:_|')
            if not s or len(s) > 70 or '@' in s or STAMP.search(s):
                continue
            if re.match(r'^\W*(Cache\s+|Interim\s+)?' + OFF, s, re.I) and len(s.split()) <= 8:
                return s
    for line in t.splitlines():                                   # shape (b)
        if '@' in line and not STAMP.search(line):
            s = re.split(r'\s{2,}|(?=\S+@)', line.strip())[0].strip(' .:_|')
            if s and len(s) <= 70 and len(s.split()) <= 8 and \
                    re.match(r'^\W*(Cache\s+|Interim\s+)?' + OFF, s, re.I):
                return s
    return ''


NAMEISH = re.compile(r"^[A-Z][A-Za-z.'\-]+(?:\s+[A-Z][A-Za-z.'\-]*\.?){1,3}$")


def typed_candidate(t, born_digital):
    """The candidate name ONLY where the form printed it as real text.

    Handwriting OCR produces name-shaped garbage ("City State Zip Code", "kK 2 ay"), so
    this is gated on the sidecar being born-digital and on a strict name shape. Scanned
    filings fall back to the clerk's own file label, which is far more reliable.
    """
    if not born_digital:
        return ''
    for rx in (r'Name of Candidate\s*\n+\s*([^\n]{2,60})',
               r"^\s*I,\s+([^\n]{3,50}?)\s*$"):
        m = re.search(rx, t, re.M)
        if not m:
            continue
        s = re.sub(r'\s{2,}.*$', '', m.group(1)).strip(' _.|')
        if NAMEISH.match(s) and not re.match(r'^(Address|Office|City|State|Zip)\b', s, re.I):
            return s
    return ''


# --------------------------------------------------------------- office mapping
COUNTY_OFFICES = [
    (r'\bcounty\s*(executive|mayor)\b', 'County Executive'),
    (r'\bcounty\s*council\b|\bcouncil\s*(seat|dist)', 'County Council'),
    (r'\bcounty\s*commission', 'County Commission'),
    (r'\bsheriff', 'Sheriff'),
    (r'\battorney', 'County Attorney'),
    (r'\bclerk\s*/?\s*auditor|\bclerk\b|\bauditor\b', 'Clerk/Auditor'),
    (r'\bassessor', 'Assessor'),
    (r'\brecorder', 'Recorder'),
    (r'\btreasurer', 'Treasurer'),
    (r'\bsurveyor', 'Surveyor'),
]
OUT_OFFICES = [
    (r'school\s*board|school\s*dist', 'School Board'),
    (r'water\s*(conserv|dist)', 'Water District Board'),
    (r'\b(city|town)\s*council\b|\bmayor of\b', 'Municipal'),
]


def map_office(s):
    if not s:
        return '', ''
    for rx, lab in OUT_OFFICES:
        if re.search(rx, s, re.I):
            return lab, 'out'
    for rx, lab in COUNTY_OFFICES:
        if re.search(rx, s, re.I):
            return lab, 'county'
    return '', ''


def council_seat(s):
    m = re.search(r'(north\s*east|south\s*east|north\s*west|south\s*west|northeast|southeast|'
                  r'northwest|southwest|north|south|east|west|at[- ]large|logan\s*\d|\bdistrict\s*\d|\bseat\s*\d|\b\d\b)',
                  s, re.I)
    return re.sub(r'\s+', ' ', m.group(1)).title() if m else ''


# --------------------------------------------------------------- name utilities
def norm(n):
    n = unicodedata.normalize('NFKD', n or '').encode('ascii', 'ignore').decode()
    n = re.sub(r'\b(jr|sr|ii|iii|iv)\b\.?', ' ', n, flags=re.I)
    n = re.sub(r'[^A-Za-z ]', ' ', n)
    return re.sub(r'\s+', ' ', n).strip().upper()


def firstlast(n):
    p = norm(n).split()
    return (p[0], p[-1]) if len(p) >= 2 else ('', p[0] if p else '')


# ------------------------------------------------- election-results office join
PARTY = re.compile(r'^(REP|DEM|LIB|IAP|UUP|CON|GRN|UNA|UTP|NPA)\s+|^Write[- ]In:?\s*', re.I)


def load_election_office():
    """normalised name -> {(year, office_label, kind, contest)} from the audited canvass.

    The canvass prints party prefixes ("REP JOHN D. LUTHY") and write-in wrappers; both are
    stripped so a filer name can join. Aggregate rows ("Write-In Totals", "Not Assigned")
    are not people and are dropped.
    """
    idx = collections.defaultdict(set)
    if not os.path.exists(ELECT):
        return idx
    for r in csv.DictReader(open(ELECT)):
        contest = (r.get('contest') or '').strip()
        cand = PARTY.sub('', (r.get('candidate') or '').strip())
        yr = (r.get('year') or '').strip()
        if not cand or not contest:
            continue
        if re.search(r'write[- ]in|not assigned|totals|overvote|undervote', cand, re.I):
            continue
        lab, kind = map_office(contest)
        if not kind:
            continue
        idx[norm(cand)].add((yr, lab, kind, contest))
        p = norm(cand).split()
        if len(p) >= 2:                      # first-initial + surname key, for "D. Chad Jensen"
            idx['%s|%s' % (p[0][0], p[-1])].add((yr, lab, kind, contest))
    return idx


# ----------------------------------------------------------------- date parsing
MON = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])}


def parse_dates(orig, label, listing_date, year, url_path='', archive_date=''):
    """-> (date, precision, source). Never invents a day."""
    if archive_date:
        return (archive_date, 'exact', 'archived_listing_row')
    m = re.search(r'\((\d{2})[.\-/](\d{2})[.\-/](\d{2})\)', label or '')      # "(06.17.08)"
    if m:
        return ('20%s-%s-%s' % (m.group(3), m.group(1), m.group(2)), 'exact', 'archive_label')
    m = re.search(r'(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})', orig)                # "10-28-14"
    if m:
        mm, dd, yy = int(m.group(1)), int(m.group(2)), m.group(3)
        yy = int(yy) + 2000 if len(yy) == 2 else int(yy)
        if 1 <= mm <= 12 and 1 <= dd <= 31 and 2005 <= yy <= 2030:
            return ('%04d-%02d-%02d' % (yy, mm, dd), 'exact', 'filename')
    m = re.search(r'([A-Z][a-z]{2,8})\.?\s+(\d{1,2}),?\s*(\d{4})', orig)       # "Dec 4, 2014"
    if m and m.group(1)[:3].lower() in MON:
        return ('%s-%02d-%02d' % (m.group(3), MON[m.group(1)[:3].lower()], int(m.group(2))),
                'exact', 'filename')
    m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*(\d{1,2})\b', orig)
    if m:
        return ('%s-%02d-%02d' % (year, MON[m.group(1).lower()], int(m.group(2))), 'exact', 'filename')
    m = re.search(r'/(June|July|August|October|December|January|September|November)/',
                  url_path or orig, re.I)
    if m:
        return ('%s-%02d' % (year, MON[m.group(1)[:3].lower()]), 'month', 'source_folder')
    if listing_date and re.match(r'\d{2}-\d{2}-\d{4}', listing_date):
        mm, dd, yy = listing_date.split('-')
        # The CMS posting date is only a usable proxy when the CMS posted the file in its
        # own cycle. Cache re-uploaded its whole 2022 set on 2025-07-29 during a site
        # migration, so a posting date outside [cycle, cycle+1] says nothing about filing
        # and is NOT promoted to `date` (it stays in listing_posted_date).
        if int(year) <= int(yy) <= int(year) + 1:
            return ('%s-%s-%s' % (yy, mm, dd), 'exact', 'cms_posting_date')
    return (year, 'year', 'cycle_only')


PERIOD = [
    (r'\bprecon\b|convention', 'Pre-Convention'),
    (r'\bprimary\b|\b22P\b', 'Pre-Primary'),
    (r'\b(22G|general)\b', 'Pre-General'),
    (r'final|dissolution|year[- ]?end|yr[- ]?end|summary', 'Final / Year-End Summary'),
]


def period_of(orig, label, date):
    blob = (orig + ' ' + (label or ''))
    for rx, lab in PERIOD:
        if re.search(rx, blob, re.I):
            return lab
    mm = date[5:7] if len(date) >= 7 else ''
    return {'06': 'Pre-Primary', '07': 'Pre-Primary', '08': 'Pre-Primary',
            '10': 'Pre-General', '11': 'Post-General',
            '12': 'Final / Year-End Summary', '01': 'Final / Year-End Summary'}.get(mm, '')


def name_from_filename(orig, year):
    s = re.sub(r'\.pdf$', '', orig, flags=re.I)
    s = re.sub(r"^([A-Za-z'\-]+),\s*(.+)$", r'\2 \1', s.strip())   # "Geary, Ann" -> "Ann Geary"
    s = re.sub(r'[_\-,/]+', ' ', s)                 # normalise separators FIRST so \b works
    s = re.sub(r'^\d{4}\s*', '', s)
    s = re.sub(r'\d{1,2}[-.\s]\d{1,2}[-.\s]\d{2,4}', ' ', s)
    s = re.sub(r'(?i)\b(jan|feb|mar|apr|may|jun|june|jul|july|aug|sep|sept|oct|nov|dec)\.?\s*\d{1,2}\b', ' ', s)
    s = re.sub(r'(?i)\b(precon|22G|22P)\b', ' ', s)
    s = re.sub(r'\b\d+\b', ' ', s)
    s = re.sub(r'(?i)\b(financial|finance|campaign|report|disclosure|general|primary|precon|'
               r'final|summary|yr|year|end|docusign|statement|of|dissolution|scan|22G|22P|'
               r'jan|feb|mar|apr|may|jun|june|jul|july|aug|sep|oct|nov|dec|december|august|'
               r'october|november|january|september)\b', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


# ------------------------------------------------------------------------ build
def load_vision():
    """vision/*.json keyed to EVERY index path each transcription applies to (see module
    docstring). Returns {path: record}. Missing/unreadable dir = empty dict (the layer is
    additive; build_index runs fine without it)."""
    out = {}
    for fn in sorted(glob.glob(os.path.join(VISION, '*.json'))):
        try:
            j = json.load(open(fn))
        except (ValueError, OSError):
            continue
        j['_key'] = os.path.basename(fn)[:-5]
        for p in (j.get('applies_to') or [j.get('canonical_path')]):
            if p:
                out[p] = j
    return out


VISION_OFFICE_STD = {
    # county elective offices, the only values that make a row county_confirmed
    'County Council': 'county', 'County Executive': 'county', 'County Commission': 'county',
    'Sheriff': 'county', 'County Attorney': 'county', 'Clerk/Auditor': 'county',
    'Assessor': 'county', 'Recorder': 'county', 'Treasurer': 'county', 'Surveyor': 'county',
    'Recorder/Surveyor': 'county',
}


def main():
    rows = [json.loads(l) for l in open(RAW_LOG)]
    vision = load_vision()
    eidx = load_election_office()
    labels = {}
    if os.path.exists(LABELS):
        for L in csv.DictReader(open(LABELS)):
            labels[L['source_url']] = L
    by_sha = collections.defaultdict(list)
    index, excluded, unrec, allrecs = [], [], [], []

    for r in rows:
        if r['status'] != 'ok':
            unrec.append(dict(
                year=r['year'], candidate_label=r.get('listing_label') or r['orig'],
                source_url=r.get('original_url') or r['url'], listing_page=r['listing_page'],
                http_status=r['http_status'], attempted_utc=r['fetched_utc'],
                reason='never archived (Wayback has no capture of these bytes)'
                       if str(r['http_status']) == '404' else 'fetch failed after 4 attempts'))
            continue
        p = os.path.join(HERE, r['path'])
        tp = 'text/' + os.path.basename(r['path'])[:-4] + '.txt'
        t = open(os.path.join(HERE, tp), errors='replace').read() if os.path.exists(os.path.join(HERE, tp)) else ''
        fam = form_family(t)
        born = len(t.strip()) > 1200 and 'Schedule A' in t
        toff = typed_office(t)
        tcand = typed_candidate(t, born)
        year = r['year']

        # --- candidate. Two independent attributions exist: the value the DOCUMENT prints
        #     and the label the CLERK gave the file. Neither is trusted blindly (a portal
        #     label once carried the wrong candidate's report — riverton precedent), so they
        #     are cross-checked on surname; a disagreement is flagged, never silently picked.
        label = r.get('listing_label') if r['channel'] == 'wayback_cachecounty_org' else ''
        lcand = name_from_filename(label or '', year) or name_from_filename(r['orig'], year)
        lcand = re.sub(r"^([A-Za-z'\-]+),\s*(.+)$", r'\2 \1', lcand).strip()
        mismatch = ''
        rec_cand_src = ''
        if tcand and lcand and firstlast(tcand)[1] != firstlast(lcand)[1]:
            mismatch = ('document prints %r but the clerk filed it as %r — clerk label used, '
                        'document value kept in candidate_stated' % (tcand, lcand))
            cand = lcand
        else:
            cand = tcand or lcand

        # --- office resolution, most-authoritative first
        url = r.get('url') or ''
        office, kind, basis = '', '', ''
        vz = vision.get(r['path'])
        vev, vseat, vision_blank = '', '', False
        if vz:
            od = vz.get('office_determination') or {}
            sc, ostd = od.get('scope', ''), (od.get('office_std') or '').strip()
            vev, vseat = od.get('evidence', ''), od.get('seat', '')
            vconf = od.get('confidence', '') or 'high'
            if sc == 'county' and ostd in VISION_OFFICE_STD:
                office, kind = ostd, 'county'
                basis = 'vision_form_field (office line read from the rendered page image; ' \
                        'confidence %s)' % vconf
            elif sc == 'out_of_scope':
                office, kind = (ostd or 'Non-county office'), 'out'
                basis = 'vision_form_field (office line names a NON-county office)'
            else:
                vision_blank = True
        if not office and toff:
            office, kind = map_office(toff)
            basis = 'form_field_typed' if office else ''
        if not office and fam == 'carr_school_board':
            office, kind, basis = 'School Board', 'out', 'form_header (school-board instrument, 20A-11-1301)'
        if not office:
            nc = norm(cand)
            key = nc if nc in eidx else ('%s|%s' % (nc.split()[0][0], nc.split()[-1])
                                         if len(nc.split()) >= 2 else nc)
            hits = {(y, lab, k) for (y, lab, k, _c) in eidx.get(key, set())}
            same = {h for h in hits if h[0] == year}
            pool = same or hits
            labs = {h[1] for h in pool}
            if len(labs) == 1:
                office = labs.pop()
                kind = {h[2] for h in pool}.pop()
                basis = 'election_canvass_join' + ('' if same else ' (other cycle)')
        if not office and '/SchoolBoardCandidates/' in url:
            office, kind, basis = 'School Board', 'out', 'source_folder (SchoolBoardCandidates/)'
        if not office and fam == 'carr_county':
            kind, basis = 'county_form', 'form_header (county instrument 17-16-6.5 / Code 2.21; office handwritten)'
        if not kind and '/CountyOffices/' in url:
            kind, basis = 'county_form', 'source_folder (CountyOffices/)'
        if vision_blank:
            # the page WAS read and the office line is blank/illegible on the document itself.
            # That is a stronger, dated statement than "OCR could not read it" — record it,
            # but it still does NOT confirm a county office.
            basis = (basis + '; ' if basis else '') + \
                'vision_no_office_printed (page image read 2026-08-01; the office line is ' \
                'blank or illegible on the document itself)'
        # honest conflict flag: the clerk's folder and the printed instrument disagree
        if '/SchoolBoardCandidates/' in url and fam == 'carr_county':
            rec_conflict = 'folder says SchoolBoardCandidates/ but the printed instrument is the ' \
                           'COUNTY form (17-16-6.5) — retained as school board per the clerk\'s own filing folder'
        elif '/CountyOffices/' in url and fam == 'carr_school_board':
            rec_conflict = 'folder says CountyOffices/ but the printed instrument is the ' \
                           'SCHOOL-BOARD form (20A-11-1301) — instrument wins'
        else:
            rec_conflict = ''

        # --- cycle parity cross-check (county offices are even-year only)
        parity = 'even' if int(year) % 2 == 0 else 'odd'
        cycle = year
        if parity == 'odd':                    # odd-year filings are early filings for the next cycle
            cycle = str(int(year) + 1)

        lab = labels.get(r.get('original_url') or r['url'], {})
        if lab.get('candidate_label'):
            r['listing_label'] = lab['candidate_label']
            label = lab['candidate_label'] if r['channel'] == 'wayback_cachecounty_org' else label
            lc = re.sub(r"^([A-Za-z'\-]+),\s*(.+)$", r'\2 \1',
                        name_from_filename(lab['candidate_label'], year)).strip()
            if lc and not tcand:
                cand = lc
                rec_cand_src = 'archived_listing_row'
        date, prec, dsrc = parse_dates(r['orig'], r.get('listing_label'), r.get('listing_date'),
                                       year, urllib.parse.unquote(r.get('original_url') or r['url']),
                                       lab.get('printed_filing_date', ''))
        rec = dict(
            date=date, candidate=cand, office=office,
            council_seat=(council_seat(toff) or vseat) if office == 'County Council' else '',
            vision_key=(vz or {}).get('_key', ''), office_evidence=vev,
            election_year=cycle, filing_type='c_and_e_report' if fam != 'statement_of_dissolution'
            else 'statement_of_dissolution',
            reporting_period=period_of(r['orig'], r.get('listing_label'), date),
            title='%s — Cache County candidate financial campaign report (%s)' % (cand or r['orig'], year),
            source_url=r.get('original_url') or r['url'],
            retrieved_date=r['fetched_utc'][:10], fetched_utc=r['fetched_utc'],
            format='text' if born else 'scanned',
            extraction_method='', path=r['path'], text_path=tp,
            channel=r['channel'], wayback_url=r['url'] if 'web.archive.org' in r['url'] else '',
            listing_page=r['listing_page'], listing_posted_date=r.get('listing_date') or '',
            form_family=fam, office_stated=toff, candidate_stated=tcand,
            office_basis=basis, cycle_parity=parity,
            date_precision=prec, date_source=dsrc,
            bytes=r['bytes'], sha256=r['sha256'], text_chars=len(t.strip()),
            scope_status='', needs_review='',
            notes='; '.join(x for x in (rec_conflict, mismatch) if x))
        by_sha[r['sha256']].append(rec)
        rec['_kind'] = kind
        allrecs.append(rec)

    # --- sibling propagation: a filer's OWN other filing in the SAME cycle, on the county's
    #     own form, is evidence of the office when this copy's Office box did not render.
    groups = collections.defaultdict(list)
    for rec in allrecs:
        if rec['candidate']:
            groups[(norm(rec['candidate']), rec['election_year'])].append(rec)
    for (nm, _yr), g in groups.items():
        known = {(x['office'], x['_kind']) for x in g
                 if x['office'] and (x['office_basis'].startswith('form_field')
                                     or x['office_basis'].startswith('vision_form_field')
                                     or x['office_basis'].startswith('election_canvass')
                                     or x['office_basis'].startswith('form_header (school'))}
        if len(known) != 1:
            continue
        off, knd = known.pop()
        for x in g:
            if not x['office']:
                x['office'], x['_kind'] = off, knd
                x['office_basis'] = 'sibling_filing_same_cycle (same filer, same cycle)'

    for rec in allrecs:
        kind, office, basis = rec['_kind'], rec['office'], rec['office_basis']
        if kind == 'out':
            rec['scope_status'] = 'out_of_scope'
            if rec['office_basis'].startswith('vision_form_field'):
                rec['exclusion_reason'] = (
                    'RE-CLASSIFIED OUT by a vision read of the page (2026-08-01): %s — not a '
                    'Cache County elective office. Page evidence: %s'
                    % (office, rec.get('office_evidence') or ''))
            else:
                rec['exclusion_reason'] = ('school-board candidate — out of package scope'
                                           if office == 'School Board' else
                                           '%s — not a county office' % office)
            rec['needs_review'] = '0'
            excluded.append(rec)
        elif kind in ('county', 'county_form'):
            confirmed = bool(office) and (basis.startswith('form_field') or
                                          basis.startswith('vision_form_field') or
                                          basis.startswith('election_canvass') or
                                          basis.startswith('sibling_filing'))
            rec['scope_status'] = 'county_confirmed' if confirmed else 'county_office_illegible'
            rec['needs_review'] = '0' if confirmed else '1'
            index.append(rec)
        else:
            rec['scope_status'] = 'undetermined'
            rec['needs_review'] = '1'
            rec['notes'] = (rec['notes'] + '; ' if rec['notes'] else '') + \
                'neither the printed instrument nor a canvass match identifies the office — ' \
                'scope undetermined, queued for the vision pass'
            index.append(rec)

    # --- cross-channel duplicate marking (identical bytes served by >1 channel)
    for sha, group in by_sha.items():
        if len(group) > 1:
            keep = sorted(group, key=lambda g: {'county_site': 0, 'state_disclosures': 1,
                                                'wayback_cachecounty_org': 2}[g['channel']])[0]
            for g in group:
                if g is not keep:
                    g['notes'] = (g['notes'] + '; ' if g['notes'] else '') + \
                        'byte-identical duplicate of %s (%s)' % (keep['path'], keep['channel'])

    for rec in index + excluded:
        rec['extraction_method'] = ('pdftotext -layout' if rec['format'] == 'text'
                                    else 'tesseract OCR (pdftoppm 250dpi)')

    def emit(fn, recs, cols):
        recs.sort(key=lambda r: (r['election_year'], r['date'], r['candidate'], r['path']))
        with open(os.path.join(HERE, fn), 'w', newline='') as fh:
            w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
            w.writeheader()
            w.writerows(recs)
        print(fn, len(recs))

    COLS = ['date', 'candidate', 'office', 'council_seat', 'election_year', 'filing_type',
            'reporting_period', 'title', 'source_url', 'retrieved_date', 'format',
            'extraction_method', 'path', 'text_path', 'channel', 'wayback_url', 'listing_page',
            'listing_posted_date', 'form_family', 'office_stated', 'candidate_stated',
            'office_basis', 'office_evidence', 'vision_key', 'cycle_parity', 'date_precision',
            'date_source', 'bytes', 'sha256',
            'text_chars', 'fetched_utc', 'scope_status', 'needs_review', 'notes']
    emit('index.csv', index, COLS)
    emit('excluded.csv', excluded, COLS + ['exclusion_reason'])
    with open(os.path.join(HERE, 'unrecovered.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['year', 'candidate_label', 'source_url', 'listing_page',
                                           'http_status', 'attempted_utc', 'reason'])
        w.writeheader()
        w.writerows(unrec)
    print('unrecovered.csv', len(unrec))


if __name__ == '__main__':
    main()
