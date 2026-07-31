#!/usr/bin/env python3
"""Build ordinances/index.csv (SCHEMA_SPEC §9 contract) for Cottonwood Heights.

Enumerates every adopted ordinance 2020-present by unioning:
  (a) ordinance numbers cited in PASSED approve/adopt motions in
      meeting_minutes/all_votes.csv (the within-source backbone), and
  (b) real ordinance PDFs recovered from MunicipalCodeOnline S3 (s3_documents.csv)
      and Utah Public Notice council body 2147 (pmn_documents.csv).

Linkage confidence vs all_votes.csv:
  high         = an independent ordinance PDF exists AND a passed council motion on
                 the adoption date cites that ordinance NUMBER (date+number).
  medium       = a PDF exists, matched to a motion by date+subject (number not cited).
  low          = a PDF exists, matched to a motion by date only.
  none         = a PDF exists but no motion match (e.g. adopted at a meeting outside
                 the vote layer, or a consent-agenda ordinance not itemized).
  within_source= NO independent PDF; the row is derived from the motion citation
                 itself, so the number/date/subject are self-consistent by
                 construction, NOT independently corroborated.

Idempotent, no network. Reads all_votes.csv + motions_std.csv + the two doc catalogs
+ text/_extraction_log.csv. Writes index.csv, unrecovered.csv, citations_map.csv.
"""
import csv
import os
import re
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
VOTES = os.path.join(HERE, "..", "meeting_minutes", "all_votes.csv")
STD = os.path.join(HERE, "..", "meeting_minutes", "motions_std.csv")
MINUTES_IDX = os.path.join(HERE, "..", "meeting_minutes", "minutes_index.csv")
CODE_HOST = "https://cottonwoodheights.municipalcodeonline.com/book?type=ordinances"
RETRIEVED = "2026-07-13"
FLOOR = "2020-01-01"

LAND_USE_RE = re.compile(
    r'\b(rezone|re-zone|zoning|zone\b|general plan|gpa\b|subdivision|plat\b|'
    r'annex|land use|land-use|pdd\b|planned development|r-1|r-2|rr-1|'
    r'setback|density|dwelling|adu\b|accessory dwelling|conditional use|'
    r'site plan|design review|overlay|short-term rental|title 19|chapter 19|'
    r'development agreement|master plan|project area)\b', re.I)

# 3-digit sequential ordinance; (?!\d) stops it grabbing "202" out of a year "2024".
ORD_CITE_RE = re.compile(
    r'[Oo]rd(?:inance)?\.?\s*(?:No\.?\s*)?(?<!\d)(\d{3})(?!\d)(-?[A-Za-z])?')
ORD_YEAR_RE = re.compile(r'[Oo]rdinance\s+(20\d{2}-\d{2})\b')
VERB_RE = re.compile(
    r'moved\s+to\s+(approve|adopt|continue|table|deny|reject|withdraw|'
    r'accept|acknowledge|ratify|amend)', re.I)


def base(num):
    """Strip a trailing single-letter draft variant (336-A, 379-D); keep YYYY-NN whole."""
    m = re.match(r'^(\d{3})-[A-Za-z]$', num)
    return m.group(1) if m else num


MONTHS = {m.lower(): i for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
     'September', 'October', 'November', 'December'], 1)}


def read_sidecar(saved_name):
    p = os.path.join(HERE, 'text', os.path.splitext(saved_name)[0] + '.txt')
    if os.path.exists(p):
        return open(p, encoding='utf-8', errors='replace').read()
    return ''


def sidecar_ord_no(saved_name):
    """Parse 'ORDINANCE NO. NNN' from the OCR/text sidecar of an unnumbered PDF."""
    txt = read_sidecar(saved_name)
    m = re.search(r'ORDINANCE\s+N[O0]\.?\s*(\d{3})', txt[:2000], re.I)
    return m.group(1) if m else ''


def sidecar_adoption_date(saved_name):
    """Parse the adoption date from the signed-ordinance text.

    Handles OCR-mangled ordinals: 'PASSED AND APPROVED this 3" day of October 2023.'
    Falls back to 'regular session on D Month YYYY'. Returns YYYY-MM-DD or ''.
    """
    txt = read_sidecar(saved_name)
    if not txt:
        return ''
    pats = [
        r'(?:PASSED\s+AND\s+APPROVED|ADOPTED|APPROVED\s+AND\s+ADOPTED)\b[^\n]{0,40}?'
        r'this\s+(\d{1,2})[^\n]{0,6}?day\s+of\s+([A-Za-z]+)[,\s]+(20\d{2})',
        r'regular\s+session\s+on\s+(?:the\s+)?(\d{1,2})[^\n]{0,6}?(?:day\s+of\s+)?([A-Za-z]+)[,\s]+(20\d{2})',
        r'this\s+(\d{1,2})[^\n]{0,6}?day\s+of\s+([A-Za-z]+)[,\s]+(20\d{2})',
    ]
    for pat in pats:
        m = re.search(pat, txt, re.I)
        if m:
            day, mon, yr = m.group(1), m.group(2).lower(), m.group(3)
            if mon in MONTHS:
                return f"{yr}-{MONTHS[mon]:02d}-{int(day):02d}"
    return ''


def load_motions():
    """Return list of motion dicts (one per distinct motion), enriched with std cols."""
    std = {}
    with open(STD) as f:
        for r in csv.DictReader(f):
            std[(r['date'], r['motion_no'], r['body'])] = r
    motions = collections.OrderedDict()
    with open(VOTES) as f:
        for r in csv.DictReader(f):
            k = (r['date'], r['motion_no'], r['body'])
            if k not in motions:
                m = dict(r)
                s = std.get(k, {})
                m['outcome'] = s.get('outcome', '')
                m['action_class'] = s.get('action_class', '')
                m['land_use_type'] = s.get('land_use_type', '')
                m['motion_type_std'] = s.get('motion_type_std', '')
                motions[k] = m
    return list(motions.values())


def cited_numbers(text):
    """Yield (ordinance_no, variant_suffix) cited in a motion's text."""
    out = []
    for m in ORD_CITE_RE.finditer(text or ''):
        suf = (m.group(2) or '').lstrip('-').upper()
        out.append((m.group(1), suf))
    for m in ORD_YEAR_RE.finditer(text or ''):
        out.append((m.group(1), ''))
    return out


def classify_doc(saved):
    """Read the sidecar head: return (is_resolution, body_ordinance_no).

    Some PMN attachments are titled 'Ordinance <YYYY-NN>' but the document body is a
    RESOLUTION (e.g. Resolution 2024-09 'Approving a Bank Account') — those are NOT
    ordinances and are dropped. The 'ORDINANCE NO. NNN' in the body is authoritative
    over a filename-derived number.
    """
    head = read_sidecar(saved)[:1200]
    # OCR mangles punctuation ("ORDINANCE NO," "NO."), so match loosely + use the
    # "AN ORDINANCE" / "A RESOLUTION" preamble markers.
    has_ord = re.search(r'\bAN\s+ORDINANCE\b', head, re.I) or \
        re.search(r'\bORDINANCE\s+N[O0]\b', head, re.I)
    has_res = re.search(r'\bA\s+RESOLUTION\b', head, re.I) or \
        re.search(r'\bRESOLUTION\s+N[O0]\b', head, re.I)
    is_res = bool(has_res and not has_ord)
    is_ord_body = bool(re.search(r'\bAN\s+ORDINANCE\b', head, re.I))
    body_no = ''
    m = re.search(r'\bORDINANCE\s+N[O0][.,\s]+(\d{3})\b', head, re.I)
    if m:
        body_no = m.group(1)
    return is_res, body_no, is_ord_body


DROPPED_RESOLUTIONS = []


def load_doc_catalog():
    """number(base) -> list of doc dicts from S3 + PMN, with extraction metadata."""
    log = {}
    lp = os.path.join(HERE, "text", "_extraction_log.csv")
    if os.path.exists(lp):
        for r in csv.DictReader(open(lp)):
            log[r['file']] = r
    docs = collections.defaultdict(list)

    s3p = os.path.join(HERE, "s3_documents.csv")
    if os.path.exists(s3p):
        for r in csv.DictReader(open(s3p)):
            num = r['ord_num'] or ''
            # recover leading-number filenames (e.g. "331 (Amending...")
            if not num:
                mm = re.search(r'_(\d{3})[\s(-]', r['filename']) or \
                     re.search(r'_(\d{3})', r['filename'])
                if mm and mm.group(1) not in ('202', '304'):
                    num = mm.group(1)
            fn = f"s3_{r['key'].split('/')[-1].split('_')[0]}_Ord{num or 'X'}.pdf"
            # actual saved name pattern:
            saved = find_saved(r, 's3')
            if not saved:
                continue
            is_res, body_no, is_ord_body = classify_doc(saved)
            if is_res:
                DROPPED_RESOLUTIONS.append(saved)
                continue
            if body_no:                       # document body is authoritative
                num = body_no
            elif not num:                     # ZTA / ORDINA~1 truncated names
                num = sidecar_ord_no(saved)
            lg = log.get(saved, {})
            docs[base(num)].append({
                'ord_num': num, 'doc_source': 's3', 'path': f"raw/{saved}",
                'source_url': r['url'], 'format': lg.get('format', ''),
                'extraction_method': lg.get('extraction_method', ''),
                'chars': int(lg.get('chars', 0) or 0),
                'filename': r['filename'], 'notice_id': '', 'notice_url': '',
                'event_date': '', 'last_modified': r['last_modified'],
                'is_ord_body': is_ord_body,
            })

    pp = os.path.join(HERE, "pmn_documents.csv")
    if os.path.exists(pp):
        for r in csv.DictReader(open(pp)):
            num = r['ord_num'] or ''
            saved = r['name']
            if not os.path.exists(os.path.join(HERE, 'raw', saved)):
                continue  # e.g. the 404 (Ord 304)
            is_res, body_no, is_ord_body = classify_doc(saved)
            if is_res:
                DROPPED_RESOLUTIONS.append(saved)
                continue
            if body_no:                       # document body is authoritative
                num = body_no
            lg = log.get(saved, {})
            edate = ''
            m = re.match(r'(\d{4})/(\d{2})/(\d{2})', r['event_date'])
            if m:
                edate = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
            docs[base(num)].append({
                'ord_num': num, 'doc_source': 'pmn', 'path': f"raw/{saved}",
                'source_url': r['url'], 'format': lg.get('format', ''),
                'extraction_method': lg.get('extraction_method', ''),
                'chars': int(lg.get('chars', 0) or 0),
                'filename': r['filename'],
                'notice_id': r['notice_id'],
                'notice_url': f"https://www.utah.gov/pmn/sitemap/notice/{r['notice_id']}.html",
                'event_date': edate, 'last_modified': '',
                'is_ord_body': is_ord_body,
            })
    return docs


def find_saved(r, prefix):
    ts = r['key'].split('/')[-1].split('_')[0]
    raw = os.path.join(HERE, 'raw')
    for f in os.listdir(raw):
        if f.startswith(f"{prefix}_{ts}") and f.endswith('.pdf'):
            return f
    return None


def best_doc(doclist):
    """Prefer born-digital (format=text); then most chars; then S3 over PMN."""
    if not doclist:
        return None
    def score(d):
        is_notice = bool(re.search(r'notice|posting', d['filename'], re.I))
        return (1 if d.get('is_ord_body') else 0,  # a real ordinance body beats a posting notice
                0 if is_notice else 1,
                1 if d['format'] == 'text' else 0, d['chars'],
                1 if d['doc_source'] == 's3' else 0)
    return sorted(doclist, key=score, reverse=True)[0]


def load_minutes_urls():
    """date -> a minutes source_url (prefer a business/regular meeting doc)."""
    urls = {}
    if not os.path.exists(MINUTES_IDX):
        return urls
    for r in csv.DictReader(open(MINUTES_IDX)):
        d, u = r['date'], r.get('source_url', '')
        if not u:
            continue
        if d not in urls or 'business' in (r.get('title', '') or '').lower():
            urls[d] = u
    return urls


def main():
    motions = load_motions()
    docs = load_doc_catalog()
    minutes_urls = load_minutes_urls()

    # ordinance -> adoption info from motions
    ord_motions = collections.defaultdict(list)   # base -> list of (motion, variant, verb, is_adopt)
    cite_rows = []
    for m in motions:
        for num, suf in cited_numbers(m['motion']):
            vm = VERB_RE.search(m['motion'] or '')
            verb = vm.group(1).lower() if vm else ''
            passed = m['outcome'] == 'pass'
            is_adopt = passed and verb in ('approve', 'adopt') and \
                m['action_class'] == 'final-action'
            ord_motions[base(num)].append((m, suf, verb, is_adopt))
            cite_rows.append({'ordinance_no': num, 'variant': suf, 'date': m['date'],
                              'motion_no': m['motion_no'], 'body': m['body'],
                              'verb': verb, 'outcome': m['outcome'],
                              'is_adoption': is_adopt, 'motion': m['motion'][:160]})

    all_nums = set(ord_motions) | set(docs)
    rows = []
    unrec = []
    for num in sorted(all_nums, key=lambda x: (len(x), x)):
        mlist = ord_motions.get(num, [])
        adopts = [t for t in mlist if t[3]]
        doclist = docs.get(num, [])
        doc = best_doc(doclist)

        # pick adoption motion: last passed approve/adopt; else last passed reference
        chosen = None
        if adopts:
            chosen = sorted(adopts, key=lambda t: t[0]['date'])[-1]
        matched_date = matched_no = ''
        title = ''
        result = ''
        land = 'no'
        variant = ''
        if chosen:
            m, suf, verb, _ = chosen
            matched_date, matched_no = m['date'], m['motion_no']
            title = squash(m['motion'])
            result = m['result']
            variant = suf
            if m['land_use_type'] or LAND_USE_RE.search(m['motion'] or ''):
                land = 'yes'

        # adoption date + provenance
        if matched_date:
            adoption = matched_date
            adsrc = 'motion'
        elif doc and sidecar_adoption_date(os.path.basename(doc['path'])):
            adoption = sidecar_adoption_date(os.path.basename(doc['path']))
            adsrc = 'pdf'
        elif doc and doc['event_date']:
            adoption = doc['event_date']
            adsrc = 'pmn_event'
        else:
            adoption = ''
            adsrc = ''

        # land-use from doc title if not already flagged
        if land == 'no' and doc and LAND_USE_RE.search(doc['filename']):
            land = 'yes'

        # title fallback from doc filename
        if not title and doc:
            title = clean_docname(doc['filename'])
        if not title:
            title = f"Ordinance {num}"

        # linkage confidence
        if doc:
            if chosen:
                conf = 'high'            # PDF + motion cites number on adoption date
            else:
                # PDF but no number-citing adoption motion: try date match
                conf = date_match(doc, motions, adoption)
        else:
            conf = 'within_source' if chosen else 'none'

        # window filter: adoption in 2020+; keep doc-only with unknown date if not clearly pre-floor
        if adoption and adoption < FLOOR:
            continue
        if not adoption and not doc:
            continue

        if doc:
            src_url = doc['source_url']
        elif matched_date and minutes_urls.get(matched_date):
            src_url = minutes_urls[matched_date]   # within_source: the minutes doc
        else:
            src_url = CODE_HOST
        fmt = doc['format'] if doc else 'na'
        ext_method = doc['extraction_method'] if doc else ''
        path = doc['path'] if doc else ''

        rows.append({
            'ordinance_no': num, 'adoption_date': adoption, 'date': adoption,
            'title': title, 'source_url': src_url, 'retrieved_date': RETRIEVED,
            'format': fmt, 'extraction_method': ext_method, 'path': path,
            'land_use': land, 'result': result,
            'matched_motion_date': matched_date, 'matched_motion_no': matched_no,
            'match_confidence': conf,
            'doc_source': doc['doc_source'] if doc else '',
            'variant_adopted': variant,
            'pmn_notice_id': doc['notice_id'] if doc else '',
            'pmn_notice_url': doc['notice_url'] if doc else '',
            'adoption_date_source': adsrc,
            'n_docs': len(doclist),
            'linkage_note': linkage_note(num, chosen, doc, doclist),
        })

    hdr = ['ordinance_no', 'adoption_date', 'date', 'title', 'source_url',
           'retrieved_date', 'format', 'extraction_method', 'path', 'land_use',
           'result', 'matched_motion_date', 'matched_motion_no', 'match_confidence',
           'doc_source', 'variant_adopted', 'pmn_notice_id', 'pmn_notice_url',
           'adoption_date_source', 'n_docs', 'linkage_note']
    with open(os.path.join(HERE, 'index.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in hdr})

    with open(os.path.join(HERE, 'citations_map.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['ordinance_no', 'variant', 'date',
                                          'motion_no', 'body', 'verb', 'outcome',
                                          'is_adoption', 'motion'])
        w.writeheader()
        w.writerows(cite_rows)

    # unrecovered.csv — honest gap log
    indexed = set(r['ordinance_no'] for r in rows)
    seqnums = sorted(int(r['ordinance_no']) for r in rows if r['ordinance_no'].isdigit())
    unrec = [{
        'item': 'ordinance_pdf', 'ordinance_no': '304', 'window': 'pre-floor (2018)',
        'reason': 'PMN attachment file 419895.pdf returned HTTP 404',
        'checked': 'PMN body 2147; MunicipalCodeOnline S3',
        'note': 'Ord 304 adopted 2018 — outside the 2020 floor; not pursued further.'}]
    for n in range(seqnums[0], seqnums[-1] + 1):
        if str(n) in indexed:
            continue
        if str(n) == '464':
            note = ('the motion to APPROVE Ordinance 464 (Community Clean Energy '
                    'Program) FAILED 4-to-2 on 2026-05-19 — not adopted; correctly absent')
            reason = 'not adopted (approve motion failed)'
        else:
            note = ('no ordinance record found — number may be unused/reserved, or '
                    'adopted at a meeting absent from the vote layer')
            reason = 'no motion citation and no published PDF'
        unrec.append({'item': 'ordinance_number', 'ordinance_no': str(n),
                      'window': 'in-window gap',
                      'reason': reason,
                      'checked': "all_votes.csv motions; PMN body 2147; MunicipalCodeOnline S3",
                      'note': note})
    with open(os.path.join(HERE, 'unrecovered.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['item', 'ordinance_no', 'window', 'reason',
                                          'checked', 'note'])
        w.writeheader()
        w.writerows(unrec)

    # stats
    conf_c = collections.Counter(r['match_confidence'] for r in rows)
    src_c = collections.Counter(r['doc_source'] or 'none' for r in rows)
    fmt_c = collections.Counter(r['format'] for r in rows)
    lu = sum(1 for r in rows if r['land_use'] == 'yes')
    print(f"index rows: {len(rows)}")
    print(f"window: {min(r['adoption_date'] for r in rows if r['adoption_date'])}"
          f" .. {max(r['adoption_date'] for r in rows if r['adoption_date'])}")
    print(f"match_confidence: {dict(conf_c)}")
    print(f"doc_source: {dict(src_c)}")
    print(f"format: {dict(fmt_c)}")
    print(f"land_use=yes: {lu}")


def squash(s):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s[:200]


def clean_docname(fn):
    fn = re.sub(r'\.pdf$', '', fn, flags=re.I)
    fn = re.sub(r'^\d+_', '', fn)
    return re.sub(r'\s+', ' ', fn).strip()[:200]


def matched_url(chosen):
    return ''


def date_match(doc, motions, adoption=''):
    """Doc with no number-citing motion: try date+subject / date-only."""
    d = adoption or doc['event_date']
    if not d:
        return 'none'
    same = [m for m in motions if m['date'] == d and m['action_class'] == 'final-action']
    if not same:
        return 'none'
    # subject overlap between doc filename and any motion on that date
    key = set(re.findall(r'[a-z]{4,}', doc['filename'].lower()))
    for m in same:
        mk = set(re.findall(r'[a-z]{4,}', (m['motion'] or '').lower()))
        if len(key & mk) >= 3:
            return 'medium'
    return 'low'


def linkage_note(num, chosen, doc, doclist):
    parts = []
    if chosen:
        m, suf, verb, _ = chosen
        parts.append(f"adopted via {verb} motion {m['motion_no']} on {m['date']}")
        if suf:
            parts.append(f"variant {num}-{suf}")
    if len(doclist) > 1:
        srcs = ','.join(sorted(set(d['doc_source'] for d in doclist)))
        parts.append(f"{len(doclist)} PDFs ({srcs})")
    if not chosen and doc:
        parts.append("PDF present but no number-citing adoption motion")
    return '; '.join(parts)


if __name__ == '__main__':
    main()
