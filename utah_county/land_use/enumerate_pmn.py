#!/usr/bin/env python3
"""Enumerate Utah County Planning Commission notices from PMN (body 1711) via the
keyword search, windowed per year. Emits notices.csv: one row per (notice, attachment)."""
import re, csv, time, html, urllib.parse, urllib.request, http.cookiejar, sys

BASE = "https://www.utah.gov/pmn/"
UA = "Mozilla/5.0 (civic-data/1.0)"

def opener():
    cj = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(op, url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return op.open(req, timeout=60).read().decode("utf-8", "replace")

def post(op, url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, headers={"User-Agent": UA,
        "Content-Type": "application/x-www-form-urlencoded"})
    return op.open(req, timeout=90).read().decode("utf-8", "replace")

def csrf(page):
    m = re.search(r'name="_csrf" value="([0-9a-f-]{36})"', page)
    return m.group(1) if m else ""

ROW_RE = re.compile(r'<tr class="(?:on|off)">(.*?)</tr>', re.S)
def parse_rows(page):
    out = []
    for block in ROW_RE.findall(page):
        tds = re.findall(r'<td>(.*?)</td>', block, re.S)
        if len(tds) < 5:
            continue
        title_m = re.search(r'notice/(\d+)\.html">(.*?)</a>', tds[0], re.S)
        notice_id = title_m.group(1) if title_m else ""
        title = html.unescape(re.sub(r'\s+', ' ', title_m.group(2)).strip()) if title_m else ""
        evtdate = re.sub(r'<.*?>', '', tds[1]).strip()
        body = re.sub(r'<.*?>', '', tds[2]).strip()
        entity = re.sub(r'<.*?>', '', tds[3]).strip()
        atts = re.findall(r'<a href="(/pmn/files/(\d+)\.pdf)"[^>]*>(.*?)</a>', tds[4], re.S)
        if not atts:
            out.append((notice_id, title, evtdate, body, entity, "", "", ""))
        for url, fid, label in atts:
            out.append((notice_id, title, evtdate, body, entity,
                        "https://www.utah.gov" + url, fid,
                        html.unescape(re.sub(r'\s+', ' ', label).strip())))
    return out

def main():
    op = opener()
    all_rows = []
    for year in range(2015, 2027):
        page = get(op, BASE + "search.html")
        tok = csrf(page)
        data = {"_csrf": tok, "searchType": "body",
                "publicBodyName": "Utah County Planning Commission",
                "entityName": "", "title": "", "agenda": "", "tags": "",
                "startDate": f"{year}-01-01", "endDate": f"{year}-12-31",
                "deadlineDate": "", "createdDate": "",
                "sortColumn": "", "sortOrder": ""}
        try:
            res = post(op, BASE + "search.html", data)
        except Exception as e:
            print(f"  ! {year} failed: {e!r}", file=sys.stderr); continue
        rows = parse_rows(res)
        all_rows += rows
        notices = len({r[0] for r in rows if r[0]})
        print(f"{year}: {notices} notices, {len(rows)} attachment-rows")
        time.sleep(0.4)
    with open("notices.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["notice_id","title","event_date","body","entity","file_url","file_id","label"])
        w.writerows(all_rows)
    print("wrote notices.csv:", len(all_rows), "rows")

if __name__ == "__main__":
    main()
