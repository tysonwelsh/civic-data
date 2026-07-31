#!/usr/bin/env python3
"""Parse the Midvale ordinance-archive + public-notices HTML (saved to scratchpad)
and emit ordinances/_sources.csv: label, ord_no, year, kind, url, name.

kind: 'ordinance' = signed ordinance from the Midvale City Ordinances folder;
      'publication' = Recorder publication/notice PDF from public_notices.php.
No network. Regenerable input to the fetch step (mv_harvest_links.py --print for a
url,name batch on stdout)."""
import re, sys, html, csv, os
from urllib.parse import quote

HOST = "https://www.midvale.utah.gov/"

def anchors(path):
    h = open(path, encoding='utf-8', errors='replace').read()
    out = []
    for m in re.finditer(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
        href = m.group(1)
        txt = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
        out.append((txt, href))
    return out

def _fin(yr, letter, num):
    # Revize appends a doc-revision suffix "001" to many filenames
    # (2021O16001.pdf == 2021-O-16; 2023O10001 == 2023-O-10). Strip trailing 001.
    if len(num) >= 4 and num.endswith('001'):
        num = num[:-3]
    return f"{yr}-{letter}-{int(num):02d}"

def norm_num(s):
    # normalize a Midvale ordinance token to canonical YYYY-{O|R}-NN.
    s = s.upper().split('?')[0]  # drop any ?t=<timestamp> cache-buster (contains stray years)
    # 1. YYYY <sep> O|R|0 <sep> NN   (the modern lettered form)
    m = re.search(r'(20\d{2})\s*[-\s]?\s*([OR0])\s*[-\s]?\s*(\d{1,5})', s)
    if m:
        return _fin(m.group(1), 'O' if m.group(2) in ('O', '0') else 'R', m.group(3))
    # 2. YYYY-NN  (hyphen, no letter — the 2012 archive label form "2012-10")
    m = re.search(r'(20\d{2})-(\d{1,3})(?!\d)', s)
    if m:
        return _fin(m.group(1), 'O', m.group(2))
    # 3. bare 6-digit YYYYNN (filename form 201210)
    m = re.search(r'\b(20\d{2})(\d{2})\b', s)
    if m:
        return _fin(m.group(1), 'O', m.group(2))
    return ""

def resolve(href):
    href = href.strip()
    if href.startswith('http'):
        url = href
    else:
        url = HOST + href.lstrip('/')
    # URL-encode spaces and & in the path portion only (keep ?t= query)
    if '?' in url:
        base, q = url.split('?', 1)
        q = '?' + q
    else:
        base, q = url, ''
    # re-encode: split scheme://host from path
    m = re.match(r'(https?://[^/]+)(/.*)', base)
    if m:
        base = m.group(1) + quote(m.group(2))
    return base + q

def main():
    sp = sys.argv[1]  # scratchpad dir
    rows = []
    seen_url = set()
    # 1. signed ordinances
    for txt, href in anchors(os.path.join(sp, 'mv_ords.html')):
        if 'Midvale City Ordinances' not in href:
            continue
        ym = re.search(r'Midvale City Ordinances/(\d{4})/', href)
        year = ym.group(1) if ym else ''
        num = norm_num(txt) or norm_num(href.split('/')[-1])
        url = resolve(href)
        if url in seen_url:
            continue
        seen_url.add(url)
        rows.append(dict(label=txt, ord_no=num, year=year, kind='ordinance',
                         url=url, fname=href.split('/')[-1].split('?')[0]))
    # 2. publication notices (only ones citing an ordinance number)
    for txt, href in anchors(os.path.join(sp, 'mv_pubnotices.html')):
        if 'ordinance' not in href.lower() and 'ordinance' not in txt.lower():
            continue
        if not href.lower().endswith(('.pdf', '.doc', '.docx')) and '.pdf?' not in href.lower() and '.doc?' not in href.lower():
            continue
        num = norm_num(txt)
        if not num:
            continue
        ym = re.search(r'/(\d{4})/', href)
        year = ym.group(1) if ym else num[:4]
        url = resolve(href)
        if url in seen_url:
            continue
        seen_url.add(url)
        rows.append(dict(label=txt, ord_no=num, year=year, kind='publication',
                         url=url, fname=href.split('/')[-1].split('?')[0]))
    rows.sort(key=lambda r: (r['kind'] != 'ordinance', r['ord_no'], r['url']))

    signed_nums = {r['ord_no'] for r in rows if r['kind'] == 'ordinance' and r['ord_no']}
    # fetch: every signed ordinance; a publication ONLY if it fills a gap (no signed PDF)
    ext = {}
    for r in rows:
        if r['kind'] == 'ordinance':
            r['fetch'] = 'yes'
        else:
            r['fetch'] = 'yes' if (r['ord_no'] and r['ord_no'] not in signed_nums) else 'no'
    # assign unique on-disk names
    used = {}
    for r in rows:
        if r['fetch'] != 'yes':
            r['name'] = ''
            continue
        base = r['ord_no'] if r['ord_no'] else os.path.splitext(r['fname'])[0]
        if r['kind'] == 'publication':
            base += '_pub'
        e = os.path.splitext(r['fname'])[1].lower() or '.pdf'
        if e not in ('.pdf', '.doc', '.docx'):
            e = '.pdf'
        n = base + e
        if n in used:
            used[n] += 1
            n = f"{base}_{chr(ord('a')+used[n]-1)}{e}"
        else:
            used[n] = 1
        r['name'] = n

    with open(os.path.join(os.path.dirname(__file__), '_sources.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['ord_no', 'year', 'kind', 'fetch', 'name', 'label', 'fname', 'url'])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in w.fieldnames})
    if '--print-batch' in sys.argv:
        for r in rows:
            if r['fetch'] == 'yes':
                print(f"{r['url']},{r['name']}")
        return
    nf = sum(1 for r in rows if r['fetch'] == 'yes')
    print(f"wrote {len(rows)} rows ({sum(1 for r in rows if r['kind']=='ordinance')} ordinances, "
          f"{sum(1 for r in rows if r['kind']=='publication')} publications); {nf} to fetch")

if __name__ == '__main__':
    main()
