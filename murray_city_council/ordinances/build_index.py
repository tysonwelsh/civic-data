#!/usr/bin/env python3
"""Build murray_city_council/ordinances/index.csv (SCHEMA_SPEC §9 contract).

Inputs (all in this directory / sibling datasets — no network):
  pmn_notices.csv   PMN body 7321 ("Public Notices & Ordinances") notice metadata,
                    crawled 2026-07-13 (notice_id, title, event, posted, desc, files).
  raw/              the fetched adopted-ordinance PDFs (one per PMN attachment),
                    named <OrdNo>_n<noticeId>_f<fileId>.<ext>.
  text/             extracted text sidecars (tesseract OCR for the scanned majority;
                    pdftotext -layout for the 3 born-digital files).
  ../meeting_minutes/all_votes.csv + minutes/  — the audited council vote layer,
                    used ONLY to compute the motion linkage (never modified).

Adoption date resolution (per file):
  1. Parse "PASSED/ADOPTED ... this <day> day of <Month>, <YYYY>" from the sidecar.
     OCR mangles ordinal day tokens ('20"', '1S‘', '215''), so the day reading is
     validated against the set of actual council meeting dates in all_votes for
     that month+year (prefer the 2-digit reading, then 1-digit).
  2. If the sidecar date is unparseable/ambiguous, fall back to the PMN notice
     "Event Start Date & Time" (observed to be the 6:30 PM council meeting for
     meeting-linked notices; early-2021 notices sometimes carry a posting date —
     those fall through honestly to no meeting match).

Motion linkage (match_confidence):
  Murray council motions NEVER cite ordinance numbers ("moved to adopt the
  Ordinance"), and the minutes never print them, so the rubric's `high`
  (date + number both cited in the motion) is structurally unattainable here.
  - medium : adoption date has minutes AND the PMN subject tokens clearly select
             one motion's minutes context (best score >= 2 and > runner-up).
  - low    : date has minutes + ordinance-adopting motions, but subject evidence
             is weak/tied — matched_motion_date is set; matched_motion_no only
             when exactly one candidate motion exists on that date.
  - none   : no council meeting/minutes on the adoption date (e.g. the 2023 TMM
             minutes gap). Match fields left empty.
  motion_no ↔ document order was verified (movers align, 2021-06-15).
"""
import csv, os, re, datetime, collections, sys, importlib.util, pathlib

HERE = os.path.dirname(os.path.abspath(__file__))
MM = os.path.join(HERE, '..', 'meeting_minutes')

# reuse the audited vote extractor's own motion grammar (read-only import)
_spec = importlib.util.spec_from_file_location(
    'murray_extract_votes', os.path.join(MM, 'extract_votes.py'))
EV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(EV)
RETRIEVED = '2026-07-13'
MONTHS = {m: i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
     'September', 'October', 'November', 'December'], 1)}
MONTH_RE = '|'.join(MONTHS)

STOP = set('''an ordinance the of to and a in for by on at with relating related re
amending amend amends enacting enact enacts adopting adopt adopts repealing repeal
section sections chapter chapters title murray city municipal code mcc utah
approving approve providing pdf s no number ord'''.split())

# Source defects verified against the raw bytes (sha256): notices whose PMN
# attachment is the WRONG document. The file is retained verbatim, but its text
# must not represent this ordinance (sidecar suppressed, subject tokens taken
# from the notice title/desc only); the ordinance's own text goes to unrecovered.
WRONG_ATTACHMENT = {
    '1088829': 'PMN posted the wrong attachment: file f1448515 is byte-identical '
               '(sha256 48edf564…) to O26-14\'s signed document; O26-15\'s own '
               'signed text is unrecovered',
}

# applied to the notice title + PMN description (curated, short text)
LAND_USE_PAT = re.compile(
    r'zoning|\bzones?\b|land.?use|general plan|subdivision|\bannex\w*|vacat\w+|'
    r'easement|right.?of.?way|alleyway|station area plan|master plan|'
    r'\b1[67]\.\d|title 1[67]\b|chapter 1[67]\b|conditional use|overlay|setback|'
    r'accessory dwelling|\bplats?\b', re.I)
# applied to the (noisy OCR) document body — strong phrases only
LAND_USE_DOC_PAT = re.compile(
    r'zoning map|zoning (?:code|ordinance|district)|general plan|land.?use|'
    r'subdivision|annexing|station area plan|accessory dwelling|'
    r'vacat\w+ [^\n]{0,40}(?:easement|street|alley|right.?of.?way)', re.I)


def tokens(s):
    return [w for w in re.findall(r'[a-z0-9.]+', s.lower()) if w not in STOP and len(w) > 2]


def load_votes():
    """(date -> [minutes source paths]), (date, source, motion_no) -> vote row.
    One date (2025-01-21) has TWO minutes documents with overlapping motion_no
    spaces, so motions must be keyed per source file, not per date."""
    src, motions = collections.defaultdict(list), collections.OrderedDict()
    with open(os.path.join(MM, 'all_votes.csv')) as f:
        for r in csv.DictReader(f):
            if r['source'] not in src[r['date']]:
                src[r['date']].append(r['source'])
            motions.setdefault((r['date'], r['source'], int(r['motion_no'])), r)
    return src, motions


def _intro_anchors(lines):
    """Line indexes that the extractor's motion grammar would anchor on, with
    the post-verb motion-text head for alignment (mirrors parse_meeting.scan_intro)."""
    out = []
    for i, line in enumerate(lines):
        m = EV.INTRO_RE.search(line)
        if m and (m.group(1) or EV.canon(m.group(2))):
            out.append((i, line[m.end():]))
            continue
        vl = EV.VERB_LEAD.match(line)
        if vl and i > 0:
            m2 = EV.INTRO_RE.search(lines[i - 1].rstrip() + ' ' + vl.group(1))
            if m2 and EV.canon(m2.group(2)):
                out.append((i, vl.group(2)))
    return out


def _norm(s):
    return re.sub(r'[^a-z0-9 ]', '', s.lower()).split()


def motion_contexts(date, source, motions, cache={}):
    """[(motion_no, context_text)] for one meeting document. Motions from all_votes
    are aligned to the extractor-grammar intro anchor lines by motion-text head
    match; context = the minutes text from the previous motion's anchor to this one."""
    key = (date, source)
    if key in cache:
        return cache[key]
    lines = EV.load_lines(pathlib.Path(os.path.join(MM, source)))
    anchors = _intro_anchors(lines)
    mrows = sorted([(no, r) for (d, s, no), r in motions.items()
                    if d == date and s == source])
    out, ai = [], 0
    prev_anchor = 0
    for no, r in mrows:
        want = _norm(r['motion'])[:6]
        hit = None
        for k in range(ai, len(anchors)):
            head = _norm(anchors[k][1])[:10]
            if want and head[:len(want)] and want[:3] == head[:3]:
                hit = k
                break
        if hit is None:   # fall back: next unused anchor, else whole-file context
            hit = ai if ai < len(anchors) else None
        if hit is None:
            out.append((no, '\n'.join(lines)))
            continue
        i = anchors[hit][0]
        out.append((no, '\n'.join(lines[prev_anchor:i + 2])))
        prev_anchor = i
        ai = hit + 1
    cache[key] = out
    return out


def parse_pmn_event(s):
    m = re.match(r'(\w+) (\d+), (\d{4})', s or '')
    if not m or m.group(1) not in MONTHS:
        return ''
    return f'{m.group(3)}-{MONTHS[m.group(1)]:02d}-{int(m.group(2)):02d}'


def sidecar_adoption_date(text, meeting_days_by_month):
    """Parse the signed adoption date; validate garbled OCR day tokens against
    the council meeting calendar for that month+year. Returns (iso_date, method)."""
    pat = re.compile(r'this\s+(?:the\s+)?(\S{1,6})\s*day\s+of\s+(' + MONTH_RE + r')[,.]?\s*(\d{4})',
                     re.I)
    hits = list(pat.finditer(text))
    if not hits:
        return '', ''
    # prefer the phrase anchored to the adoption clause (docs also carry
    # transmittal/publication date phrases)
    m = next((h for h in hits
              if re.search(r'PASSED|ADOPTED|APPROVED', text[max(0, h.start() - 150):h.start()], re.I)),
             hits[0])
    tok, month, year = m.group(1), m.group(2).title(), int(m.group(3))
    digits = re.sub(r'\D', '', tok)
    cands = []
    for d in (digits[:2], digits[:1]):
        if d and 1 <= int(d) <= 31:
            cands.append(int(d))
    known = meeting_days_by_month.get((year, MONTHS[month]), set())
    for c in cands:                       # prefer a day that is a real meeting day
        if c in known:
            return f'{year}-{MONTHS[month]:02d}-{c:02d}', 'pdf+calendar'
    if cands:                             # unvalidated but parseable
        return f'{year}-{MONTHS[month]:02d}-{cands[0]:02d}', 'pdf-only'
    return '', ''


def main():
    src, motions = load_votes()
    meeting_days = collections.defaultdict(set)
    for d in src:
        dt = datetime.date.fromisoformat(d)
        meeting_days[(dt.year, dt.month)].add(dt.day)

    notices = list(csv.DictReader(open(os.path.join(HERE, 'pmn_notices.csv'))))
    raw_files = {f for f in os.listdir(os.path.join(HERE, 'raw')) if f != '_fetch_log.jsonl'}

    rows = []
    claimed = {}   # (date, motion_no) -> ordinance key, to avoid double-claiming
    for r in notices:
        m = re.search(r'O(\d{2})[-.](\d{1,3})', r['title'])
        onum_title = f'O{m.group(1)}-{int(m.group(2)):02d}' if m else ''
        files = [f for f in r['files'].split(';') if f]
        if not files:
            continue  # logged in unrecovered.csv (O22-02)
        for f in files:
            fid, ext = f.split('.')
            base = onum_title if onum_title else f'UNNUM-{r["notice_id"]}'
            fname = next((x for x in raw_files
                          if x.startswith(f'{base}_n{r["notice_id"]}_f{fid}.')), None)
            if not fname:
                raise SystemExit(f'raw file missing for notice {r["notice_id"]} file {fid}')
            stem = re.sub(r'\.pdf$', '', fname, flags=re.I)
            sidecar = os.path.join(HERE, 'text', stem + '.txt')
            wrong = WRONG_ATTACHMENT.get(r['notice_id'], '')
            if wrong and os.path.exists(sidecar):
                os.remove(sidecar)   # the text belongs to a different instrument
            text = ('' if wrong else
                    (open(sidecar, errors='replace').read() if os.path.exists(sidecar) else ''))

            # ordinance number as printed in the signed document (OCR), for the
            # unnumbered/mislabeled notices — recorded via linkage_note only.
            doc_num = ''
            dm = re.search(r'ORDINANCE\s+(?:NO\.?|NUMBER)?\s*[#:]?\s*(\d{2}\s*[-–.]\s*\d{1,3})',
                           text[:2500], re.I)
            if dm:
                doc_num = 'O' + re.sub(r'\s', '', dm.group(1)).replace('.', '-').replace('–', '-')

            pdf_date, method = sidecar_adoption_date(text, meeting_days)
            pmn_date = parse_pmn_event(r['event'])
            adoption = pdf_date or pmn_date
            date_src = method if pdf_date else ('pmn-event' if pmn_date else '')

            # ---- motion linkage ----
            conf, mdate, mno, result, note = 'none', '', '', '', ''
            link_date = ''
            for cand in (adoption, pmn_date):
                if cand and cand in src:
                    link_date = cand
                    break
            if link_date:
                cands = []   # (motion_no, context, source)
                for source in src[link_date]:
                    for n, c in motion_contexts(link_date, source, motions):
                        if re.search(r'ordinance', c, re.I):
                            cands.append((n, c, source))
                # subject = notice title + PMN description + the signed document's
                # own printed title block (OCR head) — the early-2021 notices carry
                # no subject in the title/desc at all
                tt = set(tokens(r['title'] + ' ' + r['desc'] + ' ' + text[:450]))
                scored = sorted(((len(tt & set(tokens(c))), n, s) for n, c, s in cands),
                                reverse=True)
                msrc = ''
                if scored:
                    best_s, best_n, best_src = scored[0]
                    second = scored[1][0] if len(scored) > 1 else 0
                    # a motion may be claimed once per ORDINANCE (sibling attachments
                    # of the same ordinance share its linkage), never across ordinances
                    if best_s >= 2 and best_s > second and \
                            claimed.get((link_date, best_src, best_n), base) == base:
                        conf, mdate, mno, msrc = 'medium', link_date, best_n, best_src
                        claimed[(link_date, best_src, best_n)] = base
                    else:
                        conf, mdate = 'low', link_date
                        if len(cands) == 1 and \
                                claimed.get((link_date, cands[0][2], cands[0][0]), base) == base:
                            mno, msrc = cands[0][0], cands[0][2]
                            claimed[(link_date, msrc, mno)] = base
                else:
                    # minutes exist on the date but no ordinance-adopting motion
                    # context matched — a date-level association only
                    conf, mdate = 'low', link_date
                if mno != '':
                    result = motions[(link_date, msrc, int(mno))]['result']
                    if len(src[link_date]) > 1:
                        note = f'date has {len(src[link_date])} minutes documents; motion_no is in {msrc}'
                if adoption and link_date != adoption:
                    note = (note + '; ' if note else '') + \
                        f'linked via PMN event date {pmn_date}; sidecar date {adoption}'
            ord_no = onum_title or doc_num
            if not onum_title:
                note = (note + '; ' if note else '') + \
                    f'no number in PMN notice title; signed document prints {doc_num or "no legible number"}'
            elif doc_num and doc_num != onum_title:
                # trust the signed document over the notice-title label when the
                # document's number is consistent with the adoption year (clerk
                # typo in the PMN title, e.g. "O24-07" wrapping ORDINANCE NO. 25-07)
                adopt_yy = (adoption or pmn_date)[2:4]
                if doc_num[1:3] == adopt_yy and onum_title[1:3] != adopt_yy:
                    ord_no = doc_num
                    note = (note + '; ' if note else '') + \
                        f'PMN notice title mislabels this as {onum_title}; signed document prints ORDINANCE NO. {doc_num[1:]} (adoption year {adoption or pmn_date}) - document number used'
                else:
                    note = (note + '; ' if note else '') + \
                        f'PMN title says {onum_title} but signed document prints {doc_num} (title number kept; OCR read unverified)'

            fmt = 'text' if stem in BORN_DIGITAL else 'scanned'
            if wrong:
                extraction = 'none (wrong attachment posted by the city - see linkage_note)'
                note = (note + '; ' if note else '') + wrong
            else:
                extraction = ('pdftotext -layout (born-digital PDF)' if fmt == 'text'
                              else ('tesseract 5 OCR @300dpi (200dpi CCITT scanned PDF)'
                                    if text else 'none (image-only PDF, OCR failed/absent)'))
            land = 'yes' if (LAND_USE_PAT.search(r['title'] + ' ' + r['desc'])
                             or LAND_USE_DOC_PAT.search(text[:2000])) else 'no'
            rows.append({
                'ordinance_no': ord_no,
                'adoption_date': adoption,
                'date': adoption,
                'title': r['title'],
                'source_url': f'https://www.utah.gov/pmn/files/{f}',
                'retrieved_date': RETRIEVED,
                'format': fmt,
                'extraction_method': extraction,
                'path': f'raw/{fname}',
                'land_use': land,
                'result': result,
                'matched_motion_date': mdate,
                'matched_motion_no': mno,
                'match_confidence': conf,
                'pmn_notice_id': r['notice_id'],
                'pmn_notice_url': f'https://www.utah.gov/pmn/sitemap/notice/{r["notice_id"]}.html',
                'pmn_event_date': pmn_date,
                'adoption_date_source': date_src,
                'linkage_note': note,
            })

    rows.sort(key=lambda x: (x['adoption_date'] or '9999', x['ordinance_no']))
    cols = ['ordinance_no', 'adoption_date', 'date', 'title', 'source_url', 'retrieved_date',
            'format', 'extraction_method', 'path', 'land_use', 'result',
            'matched_motion_date', 'matched_motion_no', 'match_confidence',
            'pmn_notice_id', 'pmn_notice_url', 'pmn_event_date', 'adoption_date_source',
            'linkage_note']
    with open(os.path.join(HERE, 'index.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    cc = collections.Counter(r['match_confidence'] for r in rows)
    lu = collections.Counter(r['land_use'] for r in rows)
    print(f'{len(rows)} rows; confidence {dict(cc)}; land_use {dict(lu)}')

    # ---- unrecovered.csv (honest gaps; see AVAILABILITY.md) ----
    covered_nums = {r['ordinance_no'] for r in rows}
    first_covered = min(r['adoption_date'] for r in rows if r['adoption_date'])
    unrec = []
    # (a) ordinance-adopting motions BEFORE the PMN coverage floor: the minutes
    # prove an ordinance was adopted, but no text was ever published (AMID=95 is
    # publicly empty; PMN body 7321 begins at O21-10 / 2021-04-20).
    for (d, s, no), r in sorted(motions.items()):
        if r['motion_type'] == 'Ordinance' and d < first_covered:
            unrec.append({
                'ordinance_no': '', 'adoption_date': d, 'motion_no': no,
                'evidence': f"council minutes motion ({r['result']})",
                'reason': 'adopted per minutes; ordinance number+text never published '
                          '(pre-dates PMN body 7321; CivicPlus AMID=95 archive publicly empty)',
                'checked_date': RETRIEVED})
    # (b) known number-series holes inside the covered window
    holes = {'O22-02': 'PMN notice 727827 exists but carries no attachment',
             'O22-30': 'number absent from the PMN series (adoption unverified)',
             'O22-33': 'number absent from the PMN series (adoption unverified)',
             'O23-14': 'number absent from the PMN series (adoption unverified)',
             'O26-15': 'adoption documented (PMN notice 1088829) but the posted '
                       'attachment is byte-identical to O26-14\'s document — the '
                       'signed O26-15 text was never published'}
    always = {'O22-02', 'O26-15'}   # gap rows that coexist with/without an index row
    for num, why in sorted(holes.items()):
        if num in covered_nums and num not in always:
            continue  # resolved (e.g. the unnumbered notice turned out to be this one)
        unrec.append({'ordinance_no': num, 'adoption_date': '', 'motion_no': '',
                      'evidence': 'PMN number series', 'reason': why,
                      'checked_date': RETRIEVED})
    with open(os.path.join(HERE, 'unrecovered.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=['ordinance_no', 'adoption_date', 'motion_no',
                                           'evidence', 'reason', 'checked_date'])
        w.writeheader()
        w.writerows(unrec)
    print(f'{len(unrec)} unrecovered rows (coverage floor {first_covered})')


BORN_DIGITAL = {'O21-26_n709815_f771473', 'O23-07_n842281_f993391', 'O24-22_n941141_f1171969'}

if __name__ == '__main__':
    main()
