#!/usr/bin/env python3
"""Build ordinances/index.csv (+ within_source rows + unrecovered.csv) for Midvale.

No network. Regenerable from:
  _sources.csv                 (documents harvested from the city portal; mv_harvest_links.py)
  raw/_fetch_log.jsonl         (sha256 / retrieved_utc per file)
  text/*.txt + _extraction_log.csv (sidecar text + format/method)
  ../meeting_minutes/all_votes.csv + minutes_index.csv  (the motion-linkage backbone)

Row model: one row per retained document (signed ordinance from the city's
"Midvale City Ordinances" folder, or a publication-notice gap-filler), PLUS
`within_source` rows for ordinance numbers a council motion adopted but for which the
city posts no PDF. Follows SCHEMA_SPEC.md §9 (ordinances contract header) + city extras.

Linkage (matched_motion_*, match_confidence), per the skill rubric:
  high        = ordinance number is cited in a council motion (date + number both present;
                the signed PDF independently corroborates the motion)
  medium      = number not cited, but a same-date subject-matching adopting motion exists
  low         = adoption date has adopting motions, but subject evidence is weak/ambiguous
  none        = no adopting motion found on the adoption date (never forced)
  within_source = derived ONLY from a motion citation, no independent document on disk

Adoption date: parsed from the signed PDF's "PASSED/ADOPTED ... this Nth day of Month,
YYYY" clause where legible (adoption_date_source=pdf); else the cited motion's date
(minutes-motion); else blank. Mayor votes only to break ties (max ordinary roll 5) — the
linkage never assumes the mayor is a routine voter.
"""
import csv, glob, json, os, re, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
TXT = os.path.join(HERE, 'text')
MIN = os.path.join(HERE, '..', 'meeting_minutes')
RETRIEVED = '2026-07-13'

MONTHS = {m.lower(): i for i, m in enumerate(
    ['', 'January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'])}
# A motion's ordinance citation: YYYY <sep> {O|o|0|00(OCR)} or {R|r} <sep> NN. BOTH
# separators are mandatory and the letter slot is only O/0 chars (1-2, OCR renders "O" as
# "0" and sometimes "00") or R — so a bare date "2020-01-07" (two-digit month, digit not in
# the letter class after the first) can never match. Verified zero date FPs on all_votes.csv.
# The YEAR slot and the LEADING ZERO of the serial tolerate the same OCR O/0 confusion
# the letter slot already did: the scanned minutes print "2O23-O-O1" for 2023-O-01.
# Requiring literal digits there silently lost the enacting motion and let a consent-
# agenda row (whose extracted text bleeds into the NEXT agenda heading) claim the number
# instead — see cited_nums (found 2026-07-29). A bare date still cannot match: both
# separators remain mandatory and "2020-01-07" fails at the letter slot ("0" then "1").
ORD_RE = re.compile(
    r'\b(2[0Oo]\d{2})\s*[-–.]\s*([Oo0]{1,2}|[Rr])\s*[-–.]\s*[0Oo]*(\d{1,3})\b')

# The citation is only an ENACTMENT when an adopting verb governs it. A consent-agenda
# motion whose extracted text bleeds into the next agenda heading ("... VII. ACTION
# ITEMS A. CONSIDER RESOLUTION NO. 2023-0-01 ...") cites the number without enacting it.
ADOPT_VERB = r'(?:approv\w*|adopt\w*|enact\w*|pass\w*|ratif\w*)'


def cited_nums(text, adopting_only=False):
    """Normalized ordinance/resolution numbers cited in `text`. With adopting_only,
    keep only the citations governed by an adopting verb (an enactment), not the ones
    that merely NAME the item (a bled agenda heading, "consider", "table"). The verb
    must reach the number without crossing a sentence boundary; the "No."/"Nos."
    abbreviation is normalized first so it is not read as one."""
    out = set()
    for m in ORD_RE.finditer(text or ''):
        yr = m.group(1).upper().replace('O', '0')
        L = 'R' if m.group(2).upper() == 'R' else 'O'
        num = f"{yr}-{L}-{int(m.group(3)):02d}"
        if adopting_only:
            head = (text or '')[max(0, m.start() - 90):m.start()]
            head = re.sub(r'\bN[Oo][Ss]?\.', 'No', head)
            if not re.search(ADOPT_VERB + r'[^.;]{0,60}$', head, re.I):
                continue
        out.add(num)
    return out
STOP = set('the a an of and or to in for on at by with be as is an this that shall '
           'city midvale ordinance ordinances amending amend section chapter title code '
           'municipal an no adopt adopting approve approving relating providing establish '
           'establishing enacting enact repealing repeal 20 utah council'.split())


def norm_num(s):
    m = re.search(r'(20\d{2})\s*[-\s]?\s*([OR0])\s*[-\s]?\s*(\d{1,5})', (s or '').upper())
    if not m:
        return ''
    num = m.group(3)
    if len(num) >= 4 and num.endswith('001'):
        num = num[:-3]
    return f"{m.group(1)}-{'O' if m.group(2) in 'O0' else 'R'}-{int(num):02d}"


def load_extraction():
    d = {}
    p = os.path.join(TXT, '_extraction_log.csv')
    if os.path.exists(p):
        for r in csv.DictReader(open(p)):
            d[r['file']] = r
    return d


def load_shas():
    d = {}
    p = os.path.join(RAW, '_fetch_log.jsonl')
    if os.path.exists(p):
        for line in open(p):
            j = json.loads(line)
            name = j.get('saved_as') or ''
            d[os.path.basename(name)] = j
    return d


def _month(tok):
    tok = tok.lower().lstrip('_ ')
    for name, i in MONTHS.items():
        if i and tok[:3] == name[:3]:
            return i
    return 0


def parse_adoption(text, meeting_dates=None):
    """Parse the signed PDF's adoption clause. OCR garbles the day/ordinal token
    ('21* day', '16" day', 'GUCday'), so tolerate junk between the day digits and
    'day of'. Returns (iso_date, source):
      pdf                    - full day+month+year read from the clause
      pdf-monthyear+calendar - day illegible but month+year read; resolved to the
                               unique council meeting in that month+year
      '' / ''                - not recoverable (never forced)."""
    if not text:
        return '', ''
    # 1. full day + month + year. Tolerate the ordinal suffix ('27th') AND OCR junk
    # ('21* day', '16" day') between the day number and 'day of' — any non-digit run <=6.
    for m in re.finditer(
            r'(?:PASSED|ADOPTED|APPROVED|ENACTED)[^.]{0,80}?this\s+(\d{1,2})[^\d\n]{0,6}?'
            r'day\s+of\s+([_A-Za-z]+)\s*,?\s*(20\d{2})', text, re.I):
        day, mo, yr = int(m.group(1)), _month(m.group(2)), int(m.group(3))
        if mo and 1 <= day <= 31:
            try:
                return date(yr, mo, day).isoformat(), 'pdf'
            except ValueError:
                pass
    # 2. day illegible -> month + year only, resolved against the council calendar
    if meeting_dates:
        for m in re.finditer(
                r'(?:PASSED|ADOPTED|APPROVED|ENACTED)[^.]{0,80}?day\s+of\s+([_A-Za-z]+)\s*,?\s*(20\d{2})',
                text, re.I):
            mo, yr = _month(m.group(1)), int(m.group(2))
            if mo:
                pref = f'{yr:04d}-{mo:02d}-'
                hits = sorted(d for d in meeting_dates if d.startswith(pref))
                if len(hits) == 1:
                    return hits[0], 'pdf-monthyear+calendar'
    return '', ''


def kw(s):
    return {w for w in re.findall(r'[a-z0-9]+', (s or '').lower()) if len(w) > 3 and w not in STOP}


LAND_POS = re.compile(
    r'\b(zon|rezon|zoning|land\s*use|general\s+plan|subdivis|plat|annex|vacat|'
    r'setback|overlay|conditional\s+use|density|dwelling|accessory|adu|'
    r'mixed[\s-]*use|title\s*17|17-\d|17\.\d|parcel|development\s+agreement|'
    r'moderate\s+income\s+housing|design\s+review|site\s+plan)\b', re.I)
LAND_NEG = re.compile(r'\b(budget|appropriat|fee\s+schedule|salary|compensation|franchise|'
                      r'business\s+license|utility\s+rate|bond|tax|purchas)\b', re.I)


def is_land_use(*parts):
    blob = ' '.join(p for p in parts if p)
    if LAND_POS.search(blob):
        return 'yes'
    if LAND_NEG.search(blob):
        return 'no'
    return 'no'


def main():
    # --- motions backbone ---
    votes = list(csv.DictReader(open(os.path.join(MIN, 'all_votes.csv'))))
    midx = {r['date']: r for r in csv.DictReader(open(os.path.join(MIN, 'minutes_index.csv')))}
    motions = {}  # (date, motion_no) -> dict
    for r in votes:
        key = (r['date'], r['motion_no'])
        if key not in motions:
            motions[key] = dict(date=r['date'], motion_no=r['motion_no'], body=r['body'],
                                motion=r['motion'] or '', motion_type=r['motion_type'],
                                result=r['result'], mover=r['mover'])
    by_num = {}       # ord_no -> [motion keys citing it]
    by_date = {}      # date -> [motion keys]
    by_num_adopting = {}   # ord_no -> [motion keys whose citation is an ENACTMENT]
    for key, mo in motions.items():
        by_date.setdefault(mo['date'], []).append(key)
        for n in cited_nums(mo['motion']):
            by_num.setdefault(n, []).append(key)
        for n in cited_nums(mo['motion'], adopting_only=True):
            by_num_adopting.setdefault(n, []).append(key)
    meeting_dates = set(by_date)  # every council/RDA meeting date on record

    NONADOPT = re.compile(r'\b(table|tabl|deny|denied|reject|repeal|reconsider|rescind|'
                          r'continue|continu|withdraw|fail|postpone)\b', re.I)

    def is_repeal(mo):
        return bool(NONADOPT.search(mo['motion']))

    def is_adopting(mo):
        """A genuine adoption: the motion PASSED and is not a table/deny/continue/repeal."""
        return ('pass' in (mo['result'] or '').lower()) and not NONADOPT.search(mo['motion'])

    def choose_adopting(cands, ordno=None):
        """The earliest genuine adopting motion, or None (never a table/deny/repeal).
        A motion whose citation is governed by an adopting verb outranks one that only
        NAMES the number (a bled agenda heading), whatever the order on the day.
        NOTE the standing limitation: linkage keys on the NUMBER, and Midvale has
        genuine number collisions (two unrelated documents both numbered 2022-O-03) —
        both rows then get the same, earliest, adopting motion."""
        ad = [k for k in cands if is_adopting(motions[k])]
        if not ad:
            return None
        strong = [k for k in ad if k in set(by_num_adopting.get(ordno, []))] if ordno else []
        pool = strong or ad
        return sorted(pool, key=lambda k: (motions[k]['date'], int(motions[k]['motion_no'] or 0)))[0]

    extraction = load_extraction()
    shas = load_shas()

    src = list(csv.DictReader(open(os.path.join(HERE, '_sources.csv'))))
    doc_rows = [r for r in src if r['fetch'] == 'yes']

    rows = []
    doc_nums = set()
    for s in doc_rows:
        name = s['name']
        stem = os.path.splitext(name)[0]
        ordno = s['ord_no']
        doc_nums.add(ordno)
        sidecar = os.path.join(TXT, stem + '.txt')
        text = open(sidecar, encoding='utf-8', errors='replace').read() if os.path.exists(sidecar) else ''
        ex = extraction.get(name, {})
        fmt = ex.get('format', 'text')
        method = ex.get('extraction_method', '')
        adoption, adoption_src = parse_adoption(text, meeting_dates)

        mdate = mno = result = ''
        conf = 'none'
        note = ''
        cands = by_num.get(ordno, [])
        k = choose_adopting(cands, ordno) if cands else None
        if k is not None:
            mo = motions[k]
            mdate, mno, result = mo['date'], mo['motion_no'], mo['result']
            conf = 'high'
            if len(set(motions[c]['date'] for c in cands)) > 1:
                note = f'{len(cands)} motions cite this number; linked the adopting one'
            if not adoption:
                adoption, adoption_src = mdate, 'minutes-motion'
        elif cands and not adoption:
            # the number is cited only in table/deny/continue motions and the adoption
            # clause didn't parse — record the citing motion at low, never as an adoption
            mo = motions[sorted(cands, key=lambda c: motions[c]['date'])[-1]]
            mdate, mno, result, conf = mo['date'], mo['motion_no'], mo['result'], 'low'
            note = 'signed ordinance on file; the only motion citing its number is a ' \
                   'table/deny/continue action (adoption motion not identified)'
        elif adoption and adoption in by_date:
            # same-date subject match
            oref = kw(s['label']) | kw(text[:1500])
            scored = []
            for k in by_date[adoption]:
                mo = motions[k]
                if is_repeal(mo):
                    continue
                # guard: a motion that cites a DIFFERENT specific ordinance number is that
                # ordinance's motion, not this one — don't let the subject matcher steal it.
                cited = cited_nums(mo['motion'])
                if cited and ordno not in cited:
                    continue
                sc = len(oref & kw(mo['motion']))
                scored.append((sc, k))
            scored.sort(reverse=True, key=lambda x: (x[0], -int(motions[x[1]]['motion_no'] or 0)))
            if scored and scored[0][0] >= 2 and (len(scored) == 1 or scored[0][0] > scored[1][0]):
                k = scored[0][1]
                mo = motions[k]
                mdate, mno, result, conf = mo['date'], mo['motion_no'], mo['result'], 'medium'
            elif scored:
                # date has adopting-eligible motions but weak subject -> low
                mdate = adoption
                if len([k for k in by_date[adoption]]) == 1:
                    mno = motions[by_date[adoption][0]]['motion_no']
                conf = 'low'
        # else: no adoption date or no motions that day -> none

        # `date` is the dataset index date (§9). Prefer the parsed adoption date, then a
        # linked motion date; if neither is known, fall back to the ordinance number's YEAR
        # as a coarse YYYY-01-01 (the year is certain; month/day are a placeholder and the
        # authoritative adoption_date stays BLANK — flagged adoption_date_source=year-only).
        idate = adoption or mdate
        if not idate:
            idate = f'{ordno[:4]}-01-01'
            adoption_src = 'year-only'
        source_url = s['url']
        rows.append(dict(
            ordinance_no=ordno, adoption_date=adoption, date=idate,
            title=s['label'], source_url=source_url, retrieved_date=RETRIEVED,
            format=fmt, extraction_method=method, path=f'raw/{name}',
            land_use=is_land_use(s['label'], text[:2000]), result=result,
            matched_motion_date=mdate, matched_motion_no=mno, match_confidence=conf,
            kind=s['kind'], adoption_date_source=adoption_src,
            sha256=shas.get(name, {}).get('sha256', ''), linkage_note=note))

    # --- within_source rows: motion-cited numbers with no document ---
    ws = []
    for ordno, cands in sorted(by_num.items()):
        if ordno in doc_nums:
            continue
        if '-O-' not in ordno:  # within_source is ordinances only (resolutions out of scope)
            continue
        if ordno.endswith('-O-00'):  # spurious "2020-O-0X" truncation
            continue
        k = choose_adopting(cands, ordno)
        if k is None:   # cited only in table/deny/continue motions -> never adopted, not a gap
            continue
        mo = motions[k]
        mu = midx.get(mo['date'], {})
        # a short title from the motion text
        t = re.sub(r'\s+', ' ', mo['motion']).strip()
        t = (t[:140] + '…') if len(t) > 140 else t
        ws.append(dict(
            ordinance_no=ordno, adoption_date=mo['date'], date=mo['date'],
            title=t, source_url=mu.get('source_url', ''), retrieved_date=RETRIEVED,
            format='na', extraction_method='', path='',
            land_use=is_land_use(mo['motion']), result=mo['result'],
            matched_motion_date=mo['date'], matched_motion_no=mo['motion_no'],
            match_confidence='within_source', kind='motion-only',
            adoption_date_source='minutes-motion', sha256='',
            linkage_note='no signed PDF posted by the city; derived from the adopting motion'))

    rows.extend(ws)
    rows.sort(key=lambda r: (r['ordinance_no'], r['kind'] != 'ordinance', r['path']))

    fieldnames = ['ordinance_no', 'adoption_date', 'date', 'title', 'source_url',
                  'retrieved_date', 'format', 'extraction_method', 'path', 'land_use',
                  'result', 'matched_motion_date', 'matched_motion_no', 'match_confidence',
                  'kind', 'adoption_date_source', 'sha256', 'linkage_note']
    with open(os.path.join(HERE, 'index.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    # unrecovered.csv: the motion-only ordinances (city posts no PDF)
    with open(os.path.join(HERE, 'unrecovered.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ordinance_no', 'adoption_date', 'motion_no', 'reason', 'source_minutes_url'])
        for r in ws:
            w.writerow([r['ordinance_no'], r['adoption_date'], r['matched_motion_no'],
                        'adopted by council motion; no signed ordinance PDF posted on city portal',
                        r['source_url']])

    from collections import Counter
    c = Counter(r['match_confidence'] for r in rows)
    lu = sum(1 for r in rows if r['land_use'] == 'yes')
    fm = Counter(r['format'] for r in rows)
    print(f'index.csv: {len(rows)} rows ({len(doc_rows)} documents + {len(ws)} within_source)')
    print(f'  confidence: {dict(c)}')
    print(f'  land_use=yes: {lu}   format: {dict(fm)}')
    print(f'  ordinance window: {min(r["ordinance_no"] for r in rows)} .. {max(r["ordinance_no"] for r in rows)}')


if __name__ == '__main__':
    main()
