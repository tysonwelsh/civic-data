#!/usr/bin/env python3
"""Harvest the land-use/housing subset from the le.utah.gov PUBLIC website (no account).

Channel (verified 2026-07-20, recon.md):
  * bill static page  le.utah.gov/~<YEAR>/bills/static/<BILL>.html
      -> status, effective date, session-law chapter, bill-text URL, and the
         Bill Status action table. Each action row = (date, "chamber/ action",
         actor, LINK). LINK text is a "Y N A" tally (RECORDED roll call) or
         "Voice vote" (no names).
  * floor roll call   le.utah.gov/DynaBill/svotes.jsp?sessionid=<S>&voteid=<N>&house=<H>
      -> "Yeas - N" / "Nays - N" / "Absent or not voting - N", names "Last, F."
  * committee vote    le.utah.gov/mtgvotes.jsp?voteid=<N>
      -> committee proper name; Yeas/Nays/Absent counts; names in count order.

The le.utah.gov API (glen.le.utah.gov) has bill metadata but NO votes and needs a
LOGIN-GATED developer token (owner-gated) — see recon.md. LegiScan is the gated
alternative. This scraper needs neither.

Writes: bills.csv (subset, enriched), rollcalls.csv, votes.csv.
Resumable: cached raw pages are reused. cp1252-safe. Catch-all + throttle.
"""
import csv, os, re, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
BILLPAGES = os.path.join(HERE, "raw", "billpages")
VOTEPAGES = os.path.join(HERE, "raw", "votepages")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
BASE = "https://le.utah.gov"


def fetch(url, cache_path, force=False):
    """GET url (browser UA), cache raw bytes, return cp1252-decoded text. Resumable."""
    if not force and os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
        return open(cache_path, "rb").read().decode("cp1252", errors="replace")
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA,
                                                       "Accept": "text/html"})
            data = urllib.request.urlopen(req, timeout=30).read()
            if b"Request Rejected" in data:
                raise RuntimeError("WAF reject")
            with open(cache_path, "wb") as f:
                f.write(data)
            time.sleep(0.15)
            return data.decode("cp1252", errors="replace")
        except Exception as e:
            if attempt == 3:
                print("  FETCH FAIL %s :: %s" % (url, e))
                return ""
            time.sleep(0.8 * (attempt + 1))
    return ""


def strip(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


# a legislator name line. Two forms:
#   comma:    "Albrecht, C." / "King, Brian S." / "Van Tassell, E." / "Dailey-Provost, J."
#             (surname may contain spaces/hyphens — the comma+initial anchors it)
#   no-comma: "Strong M.A."  (the site drops the comma for a few members)
NAME_RE = re.compile(r"[A-Z][A-Za-z.'\- ]+,\s*[A-Z]"
                     r"|[A-Z][A-Za-z.'\-]+\s+[A-Z]\.[A-Z]?\.?\s*$")


# ---- bill static page parsing ----------------------------------------------
# LINEAR row parse (a single mega-regex with several .*? over a 500KB page
# backtracks catastrophically): split into <TR> chunks, and within each chunk
# that carries a vote link, pull the <TD> cell texts.
VOTE_LINK = re.compile(r'href="([^"]*(?:svotes|mtgvotes)\.jsp[^"]*)"[^>]*>([^<]*)</a>', re.I)
TD_CELL = re.compile(r"<td\b[^>]*>(.*?)</td>", re.I | re.S)


def parse_bill_page(html):
    # CRITICAL: strip HTML comments first. The 2025GS/2026GS static pages are JS-injected
    # SHELLS whose served HTML carries COMMENTED-OUT placeholder rows (stale 2024 sample
    # votes). Without stripping, the parser would extract those as fabricated roll calls
    # (e.g. a single 2024 committee vote wrongly attached to dozens of 2026 bills). Real
    # 2025/2026 votes are recovered separately via the direct svotes voteid crawl.
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    d = {}
    m = re.search(r"Effective Date:\s*(?:</B>)?\s*([^<]+)", html)
    d["effective_date"] = strip(m.group(1)) if m else ""
    mc = re.search(r"Session Law Chapter:\s*(?:</B>)?\s*(\d+)", html)
    d["chapter"] = mc.group(1) if mc else ""
    # status = the action portion of "Last Action: <date>, <action>" (real disposition:
    # "Governor Signed", "House/ filed", "Senate/ dead", ...). last_location too.
    ma = re.search(r"Last Action:\s*(?:</B>)?\s*(?:\d{1,2} \w+ \d{4},\s*)?([^<]+)", html)
    d["status"] = strip(ma.group(1)) if ma else ""
    ml = re.search(r"Last Location:\s*(?:</B>)?\s*([^<]+)", html)
    d["last_location"] = strip(ml.group(1)) if ml else ""
    # action rows with vote links — one TR chunk at a time (linear)
    rows = []
    for tr in re.split(r"(?i)<tr\b", html):
        m = VOTE_LINK.search(tr)
        if not m:
            continue
        cells = [strip(c) for c in TD_CELL.findall(tr)]
        rows.append(dict(date=cells[0] if len(cells) > 0 else "",
                         action=cells[1] if len(cells) > 1 else "",
                         actor=cells[2] if len(cells) > 2 else "",
                         href=m.group(1).strip(), linktext=strip(m.group(2))))
    d["action_rows"] = rows
    return d


# ---- vote page parsing ------------------------------------------------------
def parse_svotes(html):
    """Floor roll call. Returns (chamber, motion, yeas,nays,absent counts, name-lists)."""
    lines = [l.strip() for l in re.sub(r"<[^>]+>", "\n", html).split("\n") if l.strip()]
    # header tally line: House prints "Yeas 56 Nays 18 N/V 1", Senate "Yeas 24 Nays 3 Abs 2"
    y = n = a = None
    for l in lines:
        mm = re.match(r"Yeas\s+(\d+)\s+Nays\s+(\d+)\s+(?:N/V|Abs|Absent)\s+(\d+)", l)
        if mm:
            y, n, a = int(mm.group(1)), int(mm.group(2)), int(mm.group(3)); break
    # motion: the lines just before the tally header often name the reading/action
    motion = ""
    for l in lines:
        if re.search(r"Reading|Final Passage|Concurrence|Substitut|Amendment|Motion|Suspension|Adopt", l, re.I):
            motion = l; break
    # chamber
    chamber = "House" if re.search(r"\bHB\b|HB\d|House", html) else ""
    if re.search(r"\bSB\b|SB\d|Senate", html) and "Senate" in html:
        pass
    # name sections
    def names_between(a_hdr, b_hdr):
        out = []
        try:
            i = next(i for i, l in enumerate(lines) if re.match(a_hdr, l))
        except StopIteration:
            return out
        for l in lines[i + 1:]:
            if b_hdr and re.match(b_hdr, l):
                break
            if re.match(r"(Yeas|Nays|Absent|Abs|N/V)\b", l):
                break
            if NAME_RE.match(l):
                out.append(l)
        return out
    yea = names_between(r"Yeas\s*-\s*\d+", r"Nays\s*-\s*\d+")
    nay = names_between(r"Nays\s*-\s*\d+", r"(?:Absent|Abs)\b")
    absent = names_between(r"(?:Absent(?: or not voting)?|Abs)\s*-\s*\d+", None)
    # fallback: if the tally header wasn't found but names were parsed, derive counts
    # from the name lists so a recorded roll call is never mislabeled a voice vote.
    if y is None and (yea or nay or absent):
        y, n, a = len(yea), len(nay), len(absent)
    return dict(motion=motion, yeas=y, nays=n, absent=a, yea=yea, nay=nay, absent_n=absent)


def parse_mtgvotes(html):
    """Committee vote. Names listed in count order: yeas, then nays, then absent."""
    mcomm = re.search(r"<b><center>(.*?)</b>", html, re.I | re.S)
    committee = strip(mcomm.group(1)) if mcomm else ""
    mdate = re.search(r"(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}:\d{2}\s*[AP]M", html)
    mtg_date = mdate.group(1) if mdate else ""
    mrep = re.search(r"(?:Favorable Recommendation|Unfavorable|Report[^<]*)", html)
    lines = [l.strip() for l in re.sub(r"<[^>]+>", "\n", html).split("\n")
             if l.strip() and l.strip() not in ("&nbsp;&nbsp;&nbsp;&nbsp;",)]
    def cnt(label):
        for i, l in enumerate(lines):
            if l == label:
                mm = re.match(r"-\s*(\d+)", lines[i + 1]) if i + 1 < len(lines) else None
                return int(mm.group(1)) if mm else None
        return None
    y, n, a = cnt("Yeas"), cnt("Nays"), cnt("Absent")
    # names: contiguous "Last, F." lines after the Absent count
    names = []
    started = False
    for l in lines:
        if re.match(r"Absent$", l):
            started = True; continue
        if started:
            if NAME_RE.match(l):
                names.append(l)
            elif names:
                break
    yv = y or 0; nv = n or 0
    action = ""
    mm = re.search(r"(Favorable Recommendation|Unfavorable Recommendation|[A-Za-z ]*- PASSED|[A-Za-z ]*- FAILED)", html)
    if mm:
        action = strip(mm.group(1))
    return dict(committee=committee, action=action, date=mtg_date, yeas=y, nays=n, absent=a,
                yea=names[:yv], nay=names[yv:yv + nv], absent_n=names[yv + nv:])


def main():
    subset = [r for r in csv.DictReader(open(os.path.join(HERE, "bills_all.csv")))
              if r["relevance"]]
    print("Subset bills: %d" % len(subset))

    bill_out, rc_out, v_out = [], [], []
    rc_id = 0
    for bi, b in enumerate(subset, 1):
        session, bill = b["session"], b["bill_no"]
        cache = os.path.join(BILLPAGES, "%s_%s.html" % (session, bill))
        html = fetch(BASE + b["bill_url"] if b["bill_url"].startswith("/") else b["bill_url"], cache)
        pd = parse_bill_page(html) if html else {"action_rows": []}
        # bill text lives at a DETERMINISTIC URL (the static page's own text links are
        # JS-injected and absent from the served HTML). Introduced version always exists;
        # enrolled exists for passed bills.
        yr = re.search(r"~(\d{4})/", b["bill_url"])
        yr = yr.group(1) if yr else session[:4]
        cc = "h" if bill.startswith("H") else "s"
        text_url = "%s/~%s/bills/%sbillint/%s.htm" % (BASE, yr, cc, bill)
        enrolled_url = "%s/~%s/bills/%sbillenr/%s.htm" % (BASE, yr, cc, bill)
        b2 = dict(b)
        b2.update(status=pd.get("status", ""), effective_date=pd.get("effective_date", ""),
                  chapter=pd.get("chapter", ""), last_location=pd.get("last_location", ""),
                  text_url=text_url, enrolled_url=enrolled_url, n_rollcalls=0, n_recorded=0)

        for row in pd.get("action_rows", []):
            href = row["href"]
            if not href.startswith("http"):
                href = BASE + (href if href.startswith("/") else "/" + href)
            is_committee = "mtgvotes" in href
            linktext = row["linktext"]
            recorded = bool(re.match(r"\d+\s+\d+\s+\d+", linktext))
            rc_id += 1
            b2["n_rollcalls"] += 1
            # chamber from "House/ ..." action text
            chamber = "House" if row["action"].startswith("House") else (
                      "Senate" if row["action"].startswith("Senate") else "")
            rec = dict(rollcall_id=rc_id, session=session, bill_no=bill,
                       date=row["date"], chamber=chamber, committee="",
                       body_name=(chamber or "Committee"),
                       action=row["action"], motion_desc=row["action"],
                       result="", yeas="", nays="", absent="",
                       vote_type="committee" if is_committee else "floor",
                       recorded=1 if recorded else 0, source_url=href)
            if not recorded:
                # voice vote — honest tally-only, no names
                rc_out.append(rec)
                continue
            b2["n_recorded"] += 1
            vcache = os.path.join(VOTEPAGES,
                     ("mtg_%s.html" % re.search(r"voteid=(\d+)", href).group(1)) if is_committee
                     else ("s_%s_%s.html" % (session, re.search(r"voteid=(\d+)", href).group(1))))
            vhtml = fetch(href, vcache)
            if not vhtml:
                rc_out.append(rec); continue
            if is_committee:
                p = parse_mtgvotes(vhtml)
                rec["committee"] = p["committee"]
                rec["body_name"] = p["committee"] or (chamber + " Committee")
                if p["action"]:
                    rec["motion_desc"] = p["action"]
                if not rec["date"] and p.get("date"):
                    rec["date"] = p["date"]
                if not rec["chamber"] and p["committee"]:
                    rec["chamber"] = ("House" if p["committee"].startswith("House")
                                      else "Senate" if p["committee"].startswith("Senate") else "")
            else:
                p = parse_svotes(vhtml)
                if p["motion"]:
                    rec["motion_desc"] = p["motion"]
                rec["body_name"] = chamber or rec["body_name"]
            rec["yeas"], rec["nays"], rec["absent"] = p["yeas"], p["nays"], p["absent"]
            rec["result"] = ("Pass" if (p["yeas"] or 0) > (p["nays"] or 0) else "Fail")
            rc_out.append(rec)
            for val, lst in (("Yea", p["yea"]), ("Nay", p["nay"]), ("Absent", p["absent_n"])):
                for nm in lst:
                    v_out.append(dict(rollcall_id=rc_id, session=session, bill_no=bill,
                                      legislator_verbatim=nm, chamber=rec["chamber"],
                                      district="", party="", vote_value=val))
        bill_out.append(b2)
        if bi % 25 == 0:
            print("  ...%d/%d bills, %d rollcalls, %d votes" %
                  (bi, len(subset), len(rc_out), len(v_out)))

    # write outputs
    with open(os.path.join(HERE, "bills.csv"), "w", newline="") as f:
        cols = ["session", "bill_no", "title", "sponsor", "relevance", "status",
                "last_location", "effective_date", "chapter", "n_rollcalls", "n_recorded",
                "bill_url", "text_url", "enrolled_url"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in bill_out:
            if not r["bill_url"].startswith("http"):
                r["bill_url"] = BASE + r["bill_url"]
            w.writerow(r)
    with open(os.path.join(HERE, "rollcalls.csv"), "w", newline="") as f:
        cols = ["rollcall_id", "session", "bill_no", "date", "chamber", "committee",
                "body_name", "vote_type", "motion_desc", "action", "result",
                "yeas", "nays", "absent", "recorded", "source_url"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for r in rc_out:
            w.writerow(r)
    with open(os.path.join(HERE, "votes.csv"), "w", newline="") as f:
        cols = ["rollcall_id", "session", "bill_no", "legislator_verbatim",
                "chamber", "district", "party", "vote_value"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for r in v_out:
            w.writerow(r)

    rec_rc = sum(1 for r in rc_out if r["recorded"])
    print("\nDONE  bills=%d  rollcalls=%d (recorded=%d, voice=%d)  votes=%d" %
          (len(bill_out), len(rc_out), rec_rc, len(rc_out) - rec_rc, len(v_out)))


if __name__ == "__main__":
    main()
