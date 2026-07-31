#!/usr/bin/env python3
"""Parse the cached billlist.jsp pages -> one row per bill, apply the classifier,
write bills_all.csv (every bill, with relevance) and bills.csv (the land-use/housing
subset, relevance != '').

billlist.jsp <LI> row:
  <A HREF=".../~2022/bills/static/HB0001.html" class="billlink">H.B. 1 First Substitute</A>
   -- <B>Public Education Base Budget Amendments</B> <I>(Rep. Eliason, S.)</I>
Pages are cp1252-encoded.
"""
import csv, os, re, glob
from classify import classify

HERE = os.path.dirname(os.path.abspath(__file__))
LISTS = os.path.join(HERE, "raw", "billlists")

LI_RE = re.compile(
    r'HREF="(?P<url>[^"]*?/~(?P<yr>\d{4})/bills/static/(?P<bill>[HS][BJC]R?\d{4})\.html)"'
    r'[^>]*class="billlink"[^>]*>(?P<label>[^<]*)</A>\s*--\s*<B>(?P<title>.*?)</B>'
    r'\s*(?:<I>\((?P<sponsor>[^)]*)\)</I>)?',
    re.I | re.S)


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def parse_file(path):
    session = os.path.basename(path).replace(".html", "")
    html = open(path, "rb").read().decode("cp1252", errors="replace")
    seen = {}
    for m in LI_RE.finditer(html):
        bill = m.group("bill").upper()
        title = norm(m.group("title"))
        sponsor = norm(m.group("sponsor"))
        url = m.group("url")
        # keep first-seen title/sponsor per bill (substitutes repeat the bill)
        if bill not in seen:
            seen[bill] = dict(session=session, bill_no=bill, title=title,
                              sponsor=sponsor, bill_url=url)
    return session, seen


def main():
    all_rows, subset = [], []
    for path in sorted(glob.glob(os.path.join(LISTS, "*.html"))):
        session, bills = parse_file(path)
        for bill in sorted(bills):
            r = bills[bill]
            r["relevance"] = classify(session, bill, r["title"])
            all_rows.append(r)
            if r["relevance"]:
                subset.append(r)
        print("%s  parsed=%d  subset=%d" % (session, len(bills),
              sum(1 for b in bills if classify(session, b, bills[b]["title"]))))

    cols = ["session", "bill_no", "title", "sponsor", "relevance", "bill_url"]
    with open(os.path.join(HERE, "bills_all.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in all_rows:
            w.writerow({k: r.get(k, "") for k in cols})
    print("\nTOTAL bills across sessions: %d" % len(all_rows))
    print("Land-use/housing subset: %d" % len(subset))
    # relevance-tag distribution
    from collections import Counter
    c = Counter()
    for r in subset:
        for tag in r["relevance"].split(","):
            c[tag] += 1
    print("Tag distribution:", dict(c.most_common()))


if __name__ == "__main__":
    main()
