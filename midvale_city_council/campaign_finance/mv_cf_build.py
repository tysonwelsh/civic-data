#!/usr/bin/env python3
"""Midvale campaign_finance builder (acquisition-only). Session helper — kept in-dataset.

Stages:
  parse   -> read the saved disclosures page, emit mv_cf_filings.tsv (metadata) + mv_cf_batch.csv (url,name)
  index   -> after fetch, determine format per PDF (pdftotext) and write index.csv

Election roster is read from ../election_results/midvale_results_by_candidate.csv for
office/district + in_election_results matching (never fabricated).
"""
import csv, re, html, os, sys, subprocess, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "scratch_disclosures.html", "disclosures_page.html")
ROSTER = os.path.join(HERE, "..", "election_results", "midvale_results_by_candidate.csv")
BASE = "https://www.midvale.utah.gov/"

def norm(name):
    n = re.sub(r"\([^)]*\)", " ", name)
    n = n.upper().replace(".", " ").replace("-", " ")
    n = re.sub(r"[^A-Z ]", " ", n)
    toks = [t for t in n.split() if len(t) > 1]  # drop middle initials
    # drop common single-letter middles already gone; use first+last token
    if len(toks) >= 2:
        return (toks[0], toks[-1])
    return (toks[0], "") if toks else ("", "")

def load_roster():
    m = {}  # (year, (first,last)) -> (office, district)
    allc = {}  # year -> set of (first,last)
    with open(ROSTER) as f:
        for r in csv.DictReader(f):
            y = r["year"]
            key = norm(r["candidate"])
            if key[0] in ("WRITE", ""):
                continue
            m.setdefault((y, key), (r["office"], r["district"]))
            allc.setdefault(y, {})[key] = (r["office"], r["district"])
    return m, allc

def parse_anchors():
    h = open(PAGE, encoding="utf-8", errors="replace").read()
    out = []
    for href, text in re.findall(r'<a\b[^>]*?href="([^"]+)"[^>]*>(.*?)</a>', h, re.S | re.I):
        if not re.search(r"\.pdf|\.doc|\.xls", href, re.I):
            continue
        in_cf = re.search(r"Campaign Financial Disclosures/(\d{4})", href)
        in_elec25 = re.search(r"Recorders Office/Elections/2025", href)
        flat_bart = href.startswith("Document Center/Bart Benson Financial Disclosure")
        if not (in_cf or in_elec25 or flat_bart):
            continue
        txt = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text))).strip()
        if in_cf:
            year = in_cf.group(1)
        elif in_elec25 or flat_bart:
            year = "2025" if in_elec25 else "2023"
        out.append((year, txt, href))
    return out

# --- candidate name + period extraction from label ---
# href-substring -> clean candidate name (fixes messy anchor labels)
CAND_OVERRIDE = {
    "2025/Brandee Boyer Oct 7": "Brandee Boyer",
    "122StevensonDisclosure": "Marcus Stevenson",
    "2021 Campaign Finance Disc.pdf": "Dustin Gettel",
    "Quinn Sperryn October 2019": "Quinn Sperry",
    "Sophia 2017 Campaign Octob": "Sophia Hawes-Tingey",
    "Jamie Steverson financial disclosure 10-7-25": "Jamie Steverson",
    "Gettel 10.07.25": "Dustin Gettel",
    "David Fair Oct 7th": "David Fair",
    "Denece Mikolash Oct 7th": "Denece Mikolash",
    "Bryant Brown October 7th": "Bryant Brown",
    "Rainer Lilbok Financial Disclosure 10-7-25": "Rainer Lilbok",
    "Campaign Financial Disclos.pdf": "Bryant Brown",       # 2021 (October 2021) label
    "Campaign Finance Disclosur.pdf": "Dustin Gettel",
    "Campaign Finance Disclosur 5": "Robert Hale",
    "Campaign Finance Disclosur 6": "Amanda Hollingsworth",
    "Campaign Finance Disclosur 7": "Wayne Sharp",
    "Campaign Financial Disclos 8": "Marcus Stevenson",
    "Andrew Stoddar.pdf": "Andrew Stoddard",
    "Wayne L Shar.pdf": "Wayne L. Sharp",
    "20170829 Mont Millerberg": "Mont Millerberg",
    "20171030 Dustin Gettel": "Dustin Gettel",
    "October 2017 Bryant Brown": "Bryant Brown",
    "October 2017 Robert Hale": "Robert Hale",
    "October 2017 Stephen Brown": "Stephen Brown",
    "Sophia Hawes  Tingey.pdf": "Sophia Hawes-Tingey",
    "Alan Anderson October 2019": "Alan Anderson",
    "Bart Benson October 2019": "Bart Benson",
    "Eric Chamberlain Campaign": "Eric Chamberlain",
    "Eric Chamberlain September": "Eric Chamberlain",
    "Heidi Robinson October 201": "Heidi Robinson",
    "Paul Glover Campaign Finan": "Paul Glover",
    "Paul Glover October 2019": "Paul Glover",
    "Quinn Sperry Campaign Fina": "Quinn Sperry",
    "Sophia Hawes Tingey Campai (1)": "Sophia Hawes-Tingey",
    "Sophia Hawes Tingey Campai.pdf": "Sophia Hawes-Tingey",
}

def override_candidate(href):
    for frag, name in CAND_OVERRIDE.items():
        if frag in href:
            return name
    return None

def extract_candidate(txt):
    t = txt
    t = re.sub(r"\bcampaign\b.*", "", t, flags=re.I)
    t = re.sub(r"\bfinancial disclosure\b.*", "", t, flags=re.I)
    t = re.sub(r"\bdisclosure\b.*", "", t, flags=re.I)
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"\d[\d/\.\-]*", "", t)  # dates
    t = re.sub(r"\b(october|november|december|august|september|report|oct|nov|dec)\b", "", t, flags=re.I)
    t = re.sub(r"\breport\b", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip(" -_.")
    return t

def classify(year, txt, href):
    low = (txt + " " + href).lower()
    # reporting period label (verbatim-ish)
    period = ""
    filing_type = ""
    # explicit dates in label
    md = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", txt)
    dmatch = re.search(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*\d{0,2},?\s*\d{4}", txt, re.I)
    ymd = re.search(r"\b(20\d{2})(\d{2})(\d{2})\b", txt)  # 20171030 compact
    if md:
        period = md.group(1)
    elif dmatch:
        period = dmatch.group(0)
    elif ymd:
        period = f"{ymd.group(1)}-{ymd.group(2)}-{ymd.group(3)}"
        low += " interimdate"
    # filing_type heuristic
    if re.search(r"12/2\d/2023|december|12\.2stevenson|dec\b", low) and year in ("2021", "2023", "2025"):
        # December filing = year-end/final summary for the recent cycles
        if "december" in low or re.search(r"12/\d", low) or "dec" in low or "122stevenson" in low or "12.2" in low:
            filing_type = "summary"
    if not filing_type:
        if re.search(r"august|september|october|november|11/1\d|10/2\d|oct\b|nov\b|interimdate", low):
            filing_type = "interim"
    # 2025 explicit: Dec 4 = summary, Oct = interim
    if year == "2025":
        if re.search(r"december 4|12/4|dec", low):
            filing_type = "summary"
        else:
            filing_type = "interim"
    return filing_type, period

def build_url(href):
    # split query
    if "?" in href:
        path, q = href.split("?", 1)
        q = "?" + q
    else:
        path, q = href, ""
    enc = urllib.parse.quote(path, safe="/")
    return BASE + enc + q

def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-")

def cmd_parse():
    roster, allc = load_roster()
    anchors = parse_anchors()
    rows = []
    seq = {}
    for year, txt, href in anchors:
        cand = override_candidate(href) or extract_candidate(txt)
        key = norm(cand)
        office, district = "", ""
        in_er = "no"
        if (year, key) in roster:
            office, district = roster[(year, key)]
            in_er = "yes"
        else:
            # try matching last name only within the year
            cands_y = allc.get(year, {})
            hits = [v for (f, l), v in cands_y.items() if l == key[1] and key[1]]
            if len(hits) == 1:
                office, district = hits[0]
                in_er = "yes"
        filing_type, period = classify(year, txt, href)
        t = re.search(r"[?&]t=(\d{6})", href)
        yyyymm = t.group(1) if t else year + "00"
        seq[year] = seq.get(year, 0) + 1
        fname = f"{year}_{seq[year]:02d}_{slug(cand)}.pdf"
        url = build_url(href)
        rows.append(dict(year=year, candidate=cand.strip(), office=office, district=district,
                         in_er=in_er, filing_type=filing_type, period=period, label=txt,
                         href=href, url=url, fname=fname, upload=yyyymm))
    # write metadata tsv
    with open(os.path.join(HERE, "mv_cf_filings.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader(); w.writerows(rows)
    # write batch
    with open(os.path.join(HERE, "mv_cf_batch.csv"), "w", newline="") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow([r["url"], r["fname"]])
    # report unmatched
    print(f"parsed {len(rows)} filings")
    un = [r for r in rows if r["in_er"] == "no"]
    print(f"unmatched to election roster: {len(un)}")
    for r in un:
        print("  ", r["year"], "|", r["candidate"], "|", r["label"])
    # per year counts
    from collections import Counter
    print("by year:", dict(Counter(r["year"] for r in rows)))

MONTHS = {m: i for i, m in enumerate(
    ["january","february","march","april","may","june","july","august",
     "september","october","november","december"], 1)}

def derive_date(year, period):
    p = period.strip()
    m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})$", p)
    if m:
        return f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}", "page_stated"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", p)
    if m:
        return p, "page_stated"
    m = re.match(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})$", p)
    if m and m.group(1).lower() in MONTHS:
        return f"{m.group(3)}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}", "page_stated"
    m = re.match(r"([A-Za-z]+)\s+(\d{4})$", p)
    if m and m.group(1).lower() in MONTHS:
        return f"{m.group(2)}-{MONTHS[m.group(1).lower()]:02d}-01", "label_month"
    return f"{year}-11-01", "cycle_inferred"

def roster_upper(year, key):
    with open(ROSTER) as f:
        for r in csv.DictReader(f):
            if r["year"] == year and norm(r["candidate"]) == key:
                return r["candidate"]
    return ""

def pdf_format(path):
    try:
        txt = subprocess.run(["pdftotext", "-layout", path, "-"],
                             capture_output=True, timeout=120).stdout.decode("utf-8", "replace")
    except Exception:
        txt = ""
    real = re.sub(r"\s", "", txt)
    npages = ""
    try:
        info = subprocess.run(["pdfinfo", path], capture_output=True, timeout=60).stdout.decode("utf-8","replace")
        mm = re.search(r"Pages:\s+(\d+)", info)
        if mm: npages = mm.group(1)
    except Exception:
        pass
    # heuristic: born-digital if it yields a reasonable amount of selectable text per page
    per_page = len(real) / max(int(npages or 1), 1)
    fmt = "text" if len(real) >= 200 and per_page >= 80 else "scanned"
    return fmt, npages, len(real)

def cmd_index():
    rows = list(csv.DictReader(open(os.path.join(HERE, "mv_cf_filings.tsv"), newline=""), delimiter="\t"))
    out = []
    for r in rows:
        year = r["year"]; key = norm(override_candidate(r["href"]) or r["candidate"])
        path = os.path.join("raw", r["fname"])
        fmt, npages, nchars = pdf_format(os.path.join(HERE, path))
        date, precision = derive_date(year, r["period"])
        matched = roster_upper(year, key)
        rp = r["period"].strip()
        # normalize reporting_period wording
        if rp:
            reporting = rp
        elif r["filing_type"] == "summary":
            reporting = "Year-end / final"
        else:
            reporting = ""  # not stated on page
        cand = (override_candidate(r["href"]) or r["candidate"]).strip()
        ftlabel = {"interim": "interim", "summary": "final/year-end", "": "period not stated"}[r["filing_type"]]
        title = f"{cand} — {year} Midvale campaign financial disclosure ({reporting or ftlabel})"
        emeth = "none (acquisition-only; born-digital text PDF)" if fmt == "text" \
                else "none (acquisition-only; scanned image PDF, OCR/vision deferred)"
        note = []
        b = os.path.basename(r["href"]).lower()
        if "redacted" in b: note.append("city-posted redacted version (donor detail redacted)")
        if ".docx.pdf" in b: note.append("re-saved from docx (server filename *.pdf.docx.pdf)")
        if "(1)" in b: note.append("duplicate upload (page lists two identical-titled files)")
        if "elections/2025" in r["href"].lower(): note.append("hosted in Recorders Office/Elections/2025 folder")
        if r["href"].startswith("Document Center/Bart Benson"): note.append("hosted at flat Document Center root (not the year folder)")
        out.append({
            "date": date, "candidate": cand, "office": r["office"],
            "election_year": year, "filing_type": r["filing_type"],
            "reporting_period": reporting, "title": title, "source_url": r["url"],
            "retrieved_date": "2026-07-13", "format": fmt, "extraction_method": emeth,
            "path": path, "district": r["district"], "source": "city_cf_page",
            "in_election_results": r["in_er"],
            "matched_election_candidate": matched, "join_confidence": "exact" if r["in_er"] == "yes" else "none",
            "date_precision": precision, "filing_label_verbatim": r["label"],
            "pages": npages, "note": "; ".join(note),
        })
    # stable sort: year, office, candidate, date
    out.sort(key=lambda x: (x["election_year"], x["office"], x["candidate"], x["date"]))
    cols = ["date","candidate","office","election_year","filing_type","reporting_period",
            "title","source_url","retrieved_date","format","extraction_method","path",
            "district","source","in_election_results","matched_election_candidate",
            "join_confidence","date_precision","filing_label_verbatim","pages","note"]
    with open(os.path.join(HERE, "index.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader(); w.writerows(out)
    from collections import Counter
    print(f"wrote index.csv: {len(out)} rows")
    print("format:", dict(Counter(x["format"] for x in out)))
    print("by year:", dict(Counter(x["election_year"] for x in out)))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "parse"
    if cmd == "parse":
        cmd_parse()
    elif cmd == "index":
        cmd_index()
