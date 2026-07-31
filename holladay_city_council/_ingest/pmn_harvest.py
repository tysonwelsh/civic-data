#!/usr/bin/env python3
"""Enumerate Holladay PMN notices (entity=Holladay) via windowed search.html POSTs
(<=25 rows/window, no broken pagination), collect notice ids/body/date/title, then
for Council/PC/RDA/LBA notices fetch the detail page and grab any 'Meeting Minutes'
category attachment PDF. Pure stdlib. Idempotent: writes a JSON manifest."""
import http.cookiejar, urllib.request, urllib.parse, re, json, sys, time, html as htmlmod
from datetime import date, timedelta

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BASE = "https://www.utah.gov"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [("User-Agent", UA)]

def get(url):
    return opener.open(url, timeout=60).read().decode("utf-8", "replace")

def get_bytes(url):
    return opener.open(url, timeout=120).read()

def post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    return opener.open(req, timeout=60).read().decode("utf-8", "replace")

def csrf():
    h = get(BASE + "/pmn/search.html")
    return re.search(r'name="_csrf" value="([^"]+)"', h).group(1)

ROW_RE = re.compile(r'<tr[^>]*>(.*?)</tr>', re.S)

def parse_rows(html):
    out = []
    for m in ROW_RE.finditer(html):
        row = m.group(1)
        a = re.search(r'/pmn/(?:sitemap/)?notice/(\d+)\.html', row)
        if not a:
            continue
        title = re.search(r'notice/\d+\.html">([^<]+)</a>', row)
        tds = re.findall(r'<td>(.*?)</td>', row, re.S)
        def clean(x):
            return htmlmod.unescape(re.sub(r'<[^>]+>', ' ', x)).strip()
        cols = [clean(t) for t in tds]
        out.append({
            "notice_id": a.group(1),
            "title": htmlmod.unescape(title.group(1)).strip() if title else "",
            "event_date": cols[1] if len(cols) > 1 else "",
            "public_body": cols[2] if len(cols) > 2 else "",
        })
    return out

def search_window(token, start_date, end_date):
    data = {
        "_csrf": token, "searchType": "entity",
        "entityName": "Holladay", "publicBodyName": "", "title": "",
        "agenda": "", "tags": "", "startDate": start_date, "endDate": end_date,
        "deadlineDate": "", "createdDate": "", "sortColumn": "", "sortOrder": "",
    }
    html = post(BASE + "/pmn/search.html", data)
    rows = parse_rows(html)
    return rows

def windows(start, end, days=45):
    d = start
    while d <= end:
        w_end = min(d + timedelta(days=days - 1), end)
        yield d.isoformat(), w_end.isoformat()
        d = w_end + timedelta(days=1)

def enumerate_all(start, end):
    token = csrf()
    seen, rows = set(), []
    for ws, we in windows(start, end):
        got = search_window(token, ws, we)
        if len(got) >= 25:
            # window too big; split in half recursively
            got = []
            mid = date.fromisoformat(ws) + (date.fromisoformat(we) - date.fromisoformat(ws)) // 2
            for s2, e2 in [(ws, mid.isoformat()),
                           ((mid + timedelta(days=1)).isoformat(), we)]:
                sub = search_window(token, s2, e2)
                got.extend(sub)
                time.sleep(0.2)
        for r in got:
            if r["notice_id"] not in seen:
                seen.add(r["notice_id"])
                rows.append(r)
        print(f"  {ws}..{we}: {len(got)} rows (cum {len(rows)})", file=sys.stderr)
        time.sleep(0.25)
    return rows

FILE_RE = re.compile(r'<tr><td><a href="/pmn/files/(\d+)\.pdf"[^>]*aria-label="Download ([^"]*?) \(opens', re.S)

def parse_notice_html(html):
    """Return (attachments, pb_id, start_dt) from a notice detail page HTML."""
    out = []
    for m in re.finditer(
        r'<a href="/pmn/files/(\d+)\.pdf"[^>]*>([^<]*)</a>\s*</td>\s*<td>(.*?)</td>\s*<td>',
        html, re.S):
        fid = m.group(1)
        name = htmlmod.unescape(m.group(2)).strip()
        cat = htmlmod.unescape(re.sub(r'<[^>]+>', ' ', m.group(3))).strip()
        out.append({"file_id": fid, "name": name, "category": cat})
    pb = re.search(r'id="publicBodyId"[^>]*>(\d+)<', html)
    start = re.search(r'Event Start Date[^<]*</dt>\s*<dd>(.*?)</dd>', html, re.S)
    st = htmlmod.unescape(re.sub(r'<[^>]+>', ' ', start.group(1))).strip() if start else ""
    return out, (pb.group(1) if pb else ""), st

def notice_attachments(notice_id):
    html = get(f"{BASE}/pmn/sitemap/notice/{notice_id}.html")
    return parse_notice_html(html)

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "enum":
        rows = enumerate_all(date(2020, 1, 1), date(2026, 7, 12))
        json.dump(rows, open(sys.argv[2], "w"), indent=1)
        from collections import Counter
        print(f"TOTAL {len(rows)}")
        print(Counter(r["public_body"] for r in rows))
