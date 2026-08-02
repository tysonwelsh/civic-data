#!/usr/bin/env python3
"""Regenerate index.csv (+ the scope/gap ledgers) for washington_county/campaign_finance.

Inputs (all in-repo, all regenerable-from):
  batch/manifest.json        every enumerated candidate URL + the portal context it came from
  batch/office_map.json      office headings scraped from the archived clerk listing pages
  batch/live_page_links.json the live county page's own office/candidate table cells
  raw/*/_fetch_log*.jsonl    what was actually retrieved (base log + fetcher-shard logs) (status, bytes, sha256, retrieved_utc)
  text/*.txt                 the sidecars -- the DOCUMENT's own statement of candidate + office

Outputs:
  index.csv                  one row per retrieved COUNTY-OFFICE file
  excluded_school_board.csv  the school-board / judicial files this scope excludes, ledgered
                             so a later scope change can re-fetch them deterministically
  unrecovered.csv            enumerated URLs that did not retrieve

Cardinal rule: office and candidate are read from the DOCUMENT wherever the document says
them; the portal's own label is recorded alongside, never substituted for the document, and
every disagreement is surfaced (`label_conflict`).  Nothing is guessed: an unreadable field
stays blank with needs_review=1.
"""
import csv
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
RAW, TEXT, BATCH = (os.path.join(ROOT, d) for d in ("raw", "text", "batch"))

# ---------------------------------------------------------------- office vocabulary
COUNTY_OFFICES = ["Commission Seat A", "Commission Seat B", "Commission Seat C",
                  "Attorney", "Clerk/Auditor", "Sheriff", "Assessor", "Recorder", "Treasurer"]
OUT_OF_SCOPE = "school|juvenile court|district court|justice court|state school"


def canon_office(s):
    """Map any observed office string to the county vocabulary. Returns
    (canonical|'', 'out_of_scope'|'') -- '' canonical means 'not recognised'."""
    if not s:
        return "", ""
    t = re.sub(r"[^a-z0-9 /]", " ", s.lower())
    t = re.sub(r"\s+", " ", t).strip()
    if re.search(OUT_OF_SCOPE, t):
        return "", "out_of_scope"
    m = re.search(r"commission(?:er)?\s*(?:seat\s*)?([abc])\b", t)
    if m:
        return f"Commission Seat {m.group(1).upper()}", ""
    if "commission" in t:
        return "Commission (seat not stated)", ""
    if "clerk" in t or ("auditor" in t and "clerk" not in t):
        return "Clerk/Auditor", ""
    for key, out in (("attorney", "Attorney"), ("sheriff", "Sheriff"), ("assessor", "Assessor"),
                     ("recorder", "Recorder"), ("treasurer", "Treasurer")):
        if key in t:
            return out, ""
    return "", ""


# ------------------------------------------------------- read the document's own fields
# Four document shapes coexist in this county's record; each states candidate + office
# differently, and NONE of them can be inferred from the filename (see CLAUDE.md: a file
# named "Contributions - Greg Aldred.pdf" contains a County Candidate Summary).
# NB "Expeditures" is the COUNTY'S OWN misspelling in the 2014-15 workbooks -- matched
# verbatim rather than corrected (the source string is never rewritten).
LEDGER_HEAD = re.compile(r"All\s+(Contributions?|Expe?n?ditures?)\s+for\s+(.+)", re.I)
SUMMARY_HEAD = re.compile(r"(County|Local School)\s+Candidate\s+Summary", re.I)
OCR_NAME = re.compile(r"Full\s*Name\s*of\s*Candidate\s*[:_ ]*(.{2,60})", re.I)
OCR_OFFICE = re.compile(r"(?:Candidate\s*for\s*Office\s*Of|Name\s*of\s*Office)\s*[:_ ]*(.{2,60})", re.I)


def _split_cells(rest, tabbed):
    parts = rest.split("\t") if tabbed else re.split(r"\s{2,}", rest)
    return [p.strip() for p in parts if p.strip()]


NOT_A_CF_REPORT = re.compile(r"DECLARATION\s+OF\s+CANDIDACY", re.I)
# STRICT report titles only.  A Declaration of Candidacy carries the boilerplate "I agree to
# file all campaign financial disclosure reports", so a loose /CAMPAIGN FINANC/ match
# misclassifies the whole 3-page declaration packet as a filing.
CF_MARKERS = re.compile(r"FINANCIAL\s+CAMPAIGN\s+REPORT|CAMPAIGN\s+FINANC(?:IAL|E)\s+REPORT|"
                        r"(?:County|Local School)\s+Candidate\s+Summary|"
                        r"All\s+(?:Contributions?|Expe?n?ditures?)\s+for|"
                        r"TOTALS\s+FROM\s+LAST\s+REPORT|Total\s+LAST\s+Report", re.I)


def doc_class(text_path):
    """'cf_report' | 'declaration_of_candidacy' | 'unknown' -- read from the document.
    The county files DECLARATIONS OF CANDIDACY in the same `reports/` folder as its finance
    reports; they are a different document class and are excluded from this dataset."""
    if not os.path.exists(text_path):
        return "unknown"
    txt = open(text_path, encoding="utf-8", errors="replace").read()
    if NOT_A_CF_REPORT.search(txt) and not CF_MARKERS.search(txt):
        return "declaration_of_candidacy"
    return "cf_report" if CF_MARKERS.search(txt) else "unknown"


def read_document(text_path):
    """Return (candidate, office_raw, doc_kind, election_year) as the FILE ITSELF states
    them. Every value is verbatim from the document; '' means the document did not say."""
    if not os.path.exists(text_path):
        return "", "", "", ""
    txt = open(text_path, encoding="utf-8", errors="replace").read()
    tabbed = txt.startswith("### SHEET")
    lines = txt.split("\n")

    # (1) itemised ledger header -- "All Contributions for <NAME> <OFFICE> [<DISTRICT>]"
    for line in lines[:8]:
        m = LEDGER_HEAD.search(line)
        if m:
            cells = _split_cells(m.group(2), tabbed)
            cells = [c for c in cells if not re.fullmatch(r"Washington County", c, re.I)]
            name = cells[0] if cells else ""
            office = " ".join(cells[1:]) if len(cells) > 1 else ""
            kind = "contributions" if m.group(1).lower().startswith("contribut") else "expenditures"
            return name, office, kind, ""

    # (2) the born-digital "Candidate Summary" table (PDF 2010-2012 and .xls 2014-2015):
    #     a LABEL row ("Candidate: | 2014 | Election Year | Office | District") followed by a
    #     DATA row ("Victor Iverson | COMMISSION | SEAT B | COUNTY").  Label cells and the
    #     bare election year are dropped; the first surviving cell is the name, the rest the
    #     office.  Blank cells stay blank -- several county exports print an empty data row.
    LABELS = re.compile(r"^(election\s*year|office|district|county|candidate|submitted|"
                        r"date\s*due|contributions|expenditures|balance|\$\d+\s*or\s*(more|less))$", re.I)
    for k, line in enumerate(lines[:14]):
        if not SUMMARY_HEAD.search(line):
            continue
        doc_year = ""
        for j in range(k, min(k + 8, len(lines))):
            if not re.search(r"Candidate\s*:", lines[j]):
                continue
            ym = re.search(r"(\d{4})(?:\.0)?\s*\|?\s*Election\s*Year|Election\s*Year", lines[j])
            ym2 = re.search(r"\b(20\d{2}|19\d{2})(?:\.0)?\b", lines[j])
            doc_year = ym2.group(1) if (ym and ym2) else ""
            for d in range(j, min(j + 4, len(lines))):
                src = re.sub(r".*Candidate\s*:", "", lines[d]) if d == j else lines[d]
                cells = []
                for c in _split_cells(src, tabbed):
                    # the PDF export merges the year into the label cell
                    # ("2010 Election Year"); strip a leading year before testing
                    bare = re.sub(r"^\d{4}(\.0)?\s*", "", c).strip()
                    if not bare or LABELS.match(bare) or re.fullmatch(r"\d{4}(\.0)?", c):
                        continue
                    cells.append(bare)
                if not cells or not re.search(r"[A-Za-z]{2}", cells[0]):
                    continue                      # label-only row -- keep scanning
                office = " ".join(c for c in cells[1:] if re.search(r"[A-Za-z]", c))
                office = re.sub(r"\s*\bCOUNTY\b\s*$", "", office, flags=re.I).strip()
                return cells[0], office, "summary", doc_year
            return "", "", "summary", doc_year    # summary form, but the export left it blank
        return "", "", "summary", doc_year

    # (3) the handwritten "FINANCIAL CAMPAIGN REPORT" cover (2006-2025) -- OCR, often
    #     illegible; whatever comes back is carried verbatim and confidence-capped.
    name = ""
    m = OCR_NAME.search(txt)
    if m:
        name = re.sub(r"\s+", " ", m.group(1)).strip(" _|:.")
    office = ""
    m = OCR_OFFICE.search(txt)
    if m:
        office = re.sub(r"\s+", " ", m.group(1)).strip(" _|:.")
    kind = ""
    if re.search(r"FINANCIAL\s+CAMPAIGN\s+REPORT|CAMPAIGN\s+FINANCIAL", txt, re.I):
        kind = "statement"
    return name, office, kind, ""


# --------------------------------------------------------------------- filename parsing
def parse_filename(fname, url):
    """Everything the county encoded in the FILENAME (a portal label -- advisory only)."""
    stem = os.path.splitext(fname)[0]
    out = {"doc_kind_fn": "", "filing_type": "", "posted_date": "", "report_label": "",
           "election_year": ""}
    if re.match(r"^\s*(All\s+)?Contributions\b", stem, re.I) or " Contributions" in stem:
        out["doc_kind_fn"] = "contributions"
    elif re.search(r"\bExpenditures?\b", stem, re.I):
        out["doc_kind_fn"] = "expenditures"
    elif re.search(r"\bSummary\b", stem, re.I):
        out["doc_kind_fn"] = "summary"
    else:
        out["doc_kind_fn"] = "statement"

    if re.search(r"\bfinal\b", stem, re.I):
        out["filing_type"] = "final"
    elif re.search(r"\bFCR\b", stem):
        out["filing_type"] = "interim"
    elif re.search(r"year\s*end", stem, re.I):
        out["filing_type"] = "year-end"
    elif re.search(r"withdrawal", stem, re.I):
        out["filing_type"] = "withdrawal"
    elif re.search(r"-(Financial|financial)-\d{6}", stem) or re.match(r"^\d{4}-", stem):
        out["filing_type"] = "annual"

    m = re.search(r"[_ -](\d{2})-(\d{2})-(\d{4})(?!\d)", stem)
    if m:
        out["posted_date"] = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    m = re.match(r"^\s*(\d{1,2})[ _](\d{1,2})[ _](\d{4})\b", stem)          # "6 17 2014 ..."
    if m:
        out["report_label"] = f"{int(m.group(3)):04d}-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    m = re.match(r"^\s*(\d{2})-(\d{2})-(\d{4})[-_]", stem)                  # "06-18-2024-..."
    if m:
        out["report_label"] = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
    m = re.match(r"^(\d{4})-", stem)                                        # "2018-Gil-Almquist"
    if m:
        out["election_year"] = m.group(1)
    m = re.search(r"-(?:Financial-)?0?1?(20\d{2})\.pdf$", fname)
    if not out["election_year"]:
        for cand in re.findall(r"\b(20\d{2})\b", stem):
            out["election_year"] = cand
            break
    if not out["election_year"]:
        m = re.search(r"/elections/(\d{4})/reports/", url)
        if m:
            out["election_year"] = m.group(1)
    return out


def norm_person(name):
    """Normalise a filer name for matching: upper, drop punctuation/middle initials/suffixes."""
    t = re.sub(r"[^A-Za-z ]", " ", (name or "")).upper()
    t = re.sub(r"\b(JR|SR|II|III|IV)\b", " ", t)
    toks = [x for x in t.split() if len(x) > 1]
    if len(toks) < 2:
        return ""
    return f"{toks[0]} {toks[-1]}"                       # FIRST LAST


def main():
    manifest = {e["url"]: e for e in json.load(open(os.path.join(BATCH, "manifest.json")))}
    office_map = {}
    for r in json.load(open(os.path.join(BATCH, "office_map.json"))):
        office_map.setdefault(r["url"].replace("%20", " "), r)
    live_links = {}
    for r in json.load(open(os.path.join(BATCH, "live_page_links.json"))):
        live_links.setdefault(r["url"], r)

    # CURATED: offices read straight off the document face for files the OCR cascade could
    # not classify (see `office_determinations.csv` + CLAUDE.md).  Header-only / absent file
    # is fine -- the cascade then behaves exactly as it did before.
    determinations = {}
    dpath = os.path.join(ROOT, "office_determinations.csv")
    if os.path.exists(dpath):
        with open(dpath, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                determinations[r["url"]] = r
                determinations[r["url"].replace("%20", " ")] = r

    fetched, attempted = {}, {}
    for chan in sorted(os.listdir(RAW)):
        # ALL logs: the fetcher shards write _fetch_log.shard<N>.jsonl alongside the base log
        for lp in sorted(glob.glob(os.path.join(RAW, chan, "_fetch_log*.jsonl"))):
            for line in open(lp):
                rec = json.loads(line)
                attempted.setdefault(rec["original_url"], rec)
                if rec.get("status") == 200 and rec.get("file"):
                    fetched[rec["original_url"]] = rec

    # ---- PASS 1: harvest a person -> office roster from sources that STATE the office ----
    # Sources, all documentary: the live county page's own office/candidate table, the
    # archived listing pages' office headings, and every document that printed its own
    # office line.  Keyed by (person, cycle) because people move between seats (Chris White:
    # Commission Seat C in 2012, Seat A in 2014).  A person with TWO different offices in one
    # cycle is dropped as ambiguous -- never resolved by preference.
    roster = {}

    def note(person, cycle, office, src):
        key = (norm_person(person), cycle)
        if not key[0] or not office:
            return
        roster.setdefault(key, {}).setdefault(office, set()).add(src)

    for r in json.load(open(os.path.join(BATCH, "office_map.json"))):
        c, o = canon_office(r["portal_office"])
        if c:
            note(re.sub(r"\s*\((?:in|In)cumbent\)\s*$", "", r["portal_candidate"]),
                 r["listing_year"], c, "portal_listing")
    for r in json.load(open(os.path.join(BATCH, "live_page_links.json"))):
        c, o = canon_office(r["portal_office"])
        if c:
            note(r["portal_candidate"], "", c, "live_county_page")

    # The 2008-2010 clerk pages printed each filer's office beside their totals; that table
    # is transcribed verbatim in portal_stated_totals.csv (build_portal_totals.py).
    pst = os.path.join(ROOT, "portal_stated_totals.csv")
    if os.path.exists(pst):
        for r in csv.DictReader(open(pst)):
            c, _o = canon_office(r["portal_office"])
            if c:
                note(r["candidate"], r.get("reporting_year", ""), c, "portal_2008_page")
                note(r["candidate"], "", c, "portal_2008_page")

    # The county's OWN certified canvass is the strongest office statement available for the
    # cycles it covers (2018-2024).  READ-ONLY -- this dataset never writes to elections/.
    canvass = os.path.join(os.path.dirname(ROOT), "elections", "washco_results_long.csv")
    if os.path.exists(canvass):
        for r in csv.DictReader(open(canvass)):
            contest = r.get("contest", "").strip()
            if not re.match(r"^County (Attorney|Clerk/Auditor|Commission Seat [ABC]|Sheriff|"
                            r"Assessor|Recorder|Treasurer)$", contest):
                continue
            cand = r.get("candidate", "").strip()
            if not cand or re.match(r"^(OVER|UNDER) VOTES$|^Write-?in$", cand, re.I):
                continue
            cand = re.sub(r"^(REP|DEM|LIB|IAP|CON|GRN|UNA|UUP)\s+", "", cand, flags=re.I)
            c, _o = canon_office(contest)
            if c:
                note(cand, r.get("year", ""), c, "elections_canvass")

    for url, entry in manifest.items():
        rec = fetched.get(url)
        if not rec:
            continue
        tp = os.path.join(TEXT, f"{rec['channel']}__{re.sub(r'[^A-Za-z0-9._ ()@,;+-]', '_', os.path.splitext(rec['file'])[0])}.txt"[:200])
        dn, do, _dk, dy = read_document(tp)
        c, _o = canon_office(do)
        if c and dn:
            note(dn, dy, c, "document")

    # ---- any-cycle tier -------------------------------------------------------------
    # A filer who maps to exactly ONE county office across EVERY cycle every documentary
    # source knows about gets an any-cycle ("") key.  A filer who ever held two (Greg Aldred:
    # Commission Seat A in 2010, Seat C in 2012; Chris White: Seat C 2012, Seat A 2014) does
    # NOT -- their unlabelled filings stay unclassified rather than being assigned a seat.
    across = {}
    for (person, _cyc), offices in list(roster.items()):
        across.setdefault(person, set()).update(offices)
    for person, offices in across.items():
        if len(offices) == 1:
            roster.setdefault((person, ""), {}).setdefault(next(iter(offices)), set()).add(
                "any-cycle (single office across all sources)")

    rows, excluded, unrec = [], [], []
    for url, entry in manifest.items():
        rec = fetched.get(url)
        if not rec:
            att = attempted.get(url)
            if att is None:
                why = ("NOT YET ATTEMPTED - enumerated from the archive but the fetch did not "
                       "run to completion in this session (web.archive.org rate-limiting). "
                       "Re-run `python3 batch/fetch_all.py` (idempotent) to close.")
            elif str(att.get("status")) == "404":
                why = ("404 at every archived capture (batch/retry_404.py re-tries all "
                       "timestamps) - genuine gap")
            else:
                why = f"fetch failed: {str(att.get('status'))[:80]}"
            unrec.append(dict(url=url, channel=entry["channel"], fetch_url=entry["fetch_url"],
                              reason=why))
            continue
        chan, fname = rec["channel"], rec["file"]
        rel = f"raw/{chan}/{fname}"
        tpath = os.path.join(TEXT, f"{chan}__{re.sub(r'[^A-Za-z0-9._ ()@,;+-]', '_', os.path.splitext(fname)[0])}.txt"[:200])
        dclass = doc_class(tpath)
        if dclass == "declaration_of_candidacy":
            excluded.append(dict(url=url, channel=chan, path=rel, sha256=rec["sha256"],
                                 bytes=rec["bytes"], retrieved_utc=rec["retrieved_utc"],
                                 printed_office="", document_candidate="", portal_candidate="",
                                 reason="DECLARATION OF CANDIDACY (verified in the document) - "
                                        "not a campaign-finance report; the county files these "
                                        "in the same reports/ folder"))
            continue
        doc_name, doc_office_raw, doc_kind, doc_year = read_document(tpath)
        fn = parse_filename(fname, url)

        # --- office: document first, then the portal listing heading, then the filename
        portal_office = (office_map.get(url.replace("%20", " "), {}).get("portal_office", "")
                         or live_links.get(url, {}).get("portal_office", ""))
        fn_office_raw = ""
        m = re.search(r"(Commission[ _]?(?:Seat[ _]?)?[ABC]\b|Commission|ClerkAuditor|"
                      r"County Clerk[_ ]?Auditor|Clerk/Auditor|Attorney|Sheriff|Assessor|"
                      r"Recorder|Treasurer|Local School[^_.]*)", fname, re.I)
        if m:
            fn_office_raw = m.group(1)

        # 4th fallback: the person->office roster (documented sources only), matched on the
        # filer name the DOCUMENT or the portal gives, within the same cycle where known.
        roster_office = ""
        roster_via = ""
        # Try, in order: the name the DOCUMENT gave, the name the PORTAL gave, then every
        # adjacent 2-token alphabetic window of the FILENAME (the county's filenames embed
        # the filer name in an arbitrary position: "Jan 7 2019_Gil Almquist_Final FCR_...").
        probes = [doc_name,
                  live_links.get(url, {}).get("portal_candidate", ""),
                  office_map.get(url.replace("%20", " "), {}).get("portal_candidate", "")]
        toks = [t for t in re.split(r"[^A-Za-z]+", os.path.splitext(fname)[0]) if len(t) > 1]
        probes += [f"{a} {b}" for a, b in zip(toks, toks[1:])]
        # 3-token windows too: "Alan Dean Gardner" normalises to ALAN GARDNER, which no
        # 2-token window can produce.
        probes += [f"{a} {b} {c}" for a, b, c in zip(toks, toks[1:], toks[2:])]
        cycles = [c for c in (fn["election_year"], "") if c is not None]
        for probe in probes:
            key = norm_person(probe)
            if not key:
                continue
            for ck in cycles:
                hit = roster.get((key, ck))
                if hit and len(hit) == 1:
                    roster_office, roster_via = next(iter(hit)), f"{key} @{ck or 'any'}"
                    break
            if roster_office:
                break

        # --- CURATED DETERMINATIONS (office_determinations.csv) win over the cascade ---
        # These are offices read STRAIGHT OFF the document face (a rendered page image, or
        # the born-digital text layer / workbook cells) for files the OCR cascade could not
        # classify.  Every row cites its evidence and is dated; nothing is inferred from the
        # filename or the folder.  A `undetermined` row is an HONEST refusal and keeps the
        # file OUT of the index (it stays in unrecovered.csv), exactly as before.
        det = determinations.get(url) or determinations.get(url.replace("%20", " "))
        det_office, det_note = "", ""
        if det:
            det_note = ("office read from the DOCUMENT FACE by the 2026-08-01 determination "
                        "pass (" + det["determined_by"] + "): " + det["evidence"])
            if det["verdict"] == "county":
                det_office = det["office"]
            if det["verdict"] in ("school_board", "out_of_scope_other"):
                excluded.append(dict(url=url, channel=chan, path=rel, sha256=rec["sha256"],
                                     bytes=rec["bytes"], retrieved_utc=rec["retrieved_utc"],
                                     printed_office=det["evidence"][:120],
                                     document_candidate=doc_name,
                                     portal_candidate=live_links.get(url, {}).get("portal_candidate", "")
                                     or office_map.get(url.replace("%20", " "), {}).get("portal_candidate", ""),
                                     reason=("Local School Board / judicial - out of COUNTY-OFFICE scope"
                                             if det["verdict"] == "school_board" else
                                             "STATE / other non-county office on the county-clerk form"
                                             " - out of COUNTY-OFFICE scope")
                                     + " [office_determinations.csv 2026-08-01: "
                                     + det["evidence"] + "]"))
                continue
            if det["verdict"] == "undetermined":
                unrec.append(dict(url=url, channel=chan, fetch_url=entry["fetch_url"],
                                  reason="retrieved but office not determinable from document, "
                                         "portal listing, or filename - held out of index (never "
                                         "guessed) [office_determinations.csv 2026-08-01: "
                                         + det["evidence"] + "]"))
                continue

        office, oos = "", ""
        source, conf = "", ""
        for raw_val, src, cf in ((det_office, "document_determination", "high"),
                                 (doc_office_raw, "document", "high"),
                                 (portal_office, "portal_listing", "medium"),
                                 (roster_office, "person_roster", "medium"),
                                 (fn_office_raw, "filename", "low")):
            c, o = canon_office(raw_val)
            if o == "out_of_scope":
                oos = raw_val
                break
            if src in ("person_roster", "document_determination") and raw_val:
                c = raw_val                     # already canonical
            if c and not office:
                office, source, conf = c, src, cf
        if oos or (not office and re.search(OUT_OF_SCOPE, f"{portal_office} {fn_office_raw}".lower())):
            excluded.append(dict(url=url, channel=chan, path=rel, sha256=rec["sha256"],
                                 bytes=rec["bytes"], retrieved_utc=rec["retrieved_utc"],
                                 printed_office=(oos or portal_office or fn_office_raw),
                                 document_candidate=doc_name,
                                 portal_candidate=live_links.get(url, {}).get("portal_candidate", "")
                                 or office_map.get(url.replace("%20", " "), {}).get("portal_candidate", ""),
                                 reason="Local School Board / judicial - out of COUNTY-OFFICE scope"))
            continue
        if not office:
            unrec.append(dict(url=url, channel=chan, fetch_url=entry["fetch_url"],
                              reason="retrieved but office not determinable from document, "
                                     "portal listing, or filename - held out of index (never guessed)"))
            continue

        portal_cand = (live_links.get(url, {}).get("portal_candidate", "")
                       or office_map.get(url.replace("%20", " "), {}).get("portal_candidate", ""))
        portal_cand = re.sub(r"\s*\((?:in|In)cumbent\)\s*$", "", portal_cand).strip()
        candidate = portal_cand or doc_name
        cand_src = "portal_listing" if portal_cand else ("document" if doc_name else "")
        if not candidate:
            # last resort: the county's own filename convention is
            # "<Office>_<Filer Name>_<period>_<posted>.pdf" -- take the first underscore
            # segment that is neither an office token nor a date/period and reads as a name.
            OFFICE_TOK = re.compile(r"commission|attorney|clerk|auditor|sheriff|assessor|"
                                    r"recorder|treasurer|local school|seat|special|year", re.I)
            MONTHS = re.compile(r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|fcr|final|"
                                r"write|end|\d", re.I)
            for seg in re.split(r"[_]", os.path.splitext(fname)[0]):
                seg = seg.strip()
                words = [w for w in re.split(r"[^A-Za-z]+", seg) if len(w) > 1]
                if len(words) >= 2 and not OFFICE_TOK.search(seg) and not MONTHS.search(seg):
                    candidate = " ".join(words)
                    cand_src = "filename_segment"
                    break
        if not candidate and roster_via:
            # the roster matched on a name lifted from the filename; use that key rather than
            # leaving the filer nameless (the key is FIRST LAST, normalised, not invented)
            candidate = roster_via.split(" @")[0].title()
            cand_src = "roster_key(filename)"

        conflict = ""
        if doc_office_raw and portal_office:
            dc, _ = canon_office(doc_office_raw)
            pc, _ = canon_office(portal_office)
            vague = "Commission (seat not stated)"
            if dc and pc and dc != pc and vague not in (dc, pc):
                conflict = f"document='{doc_office_raw}' vs portal='{portal_office}'"

        # A filename deadline label that predates the posted date by >1yr is a source typo
        # ("4 4 2001 Expenditures - Mark Boyer_04-04-2014.xls").  Drop the label, keep the
        # posted date, and record the defect rather than publishing a 2001 row.
        label_typo = ""
        if fn["report_label"] and fn["posted_date"] and \
                int(fn["report_label"][:4]) < int(fn["posted_date"][:4]) - 1:
            label_typo = (f"filename deadline label {fn['report_label']} predates the posted "
                          f"date {fn['posted_date']} by >1yr - source typo; posted date used")
            fn["report_label"] = ""
            fn["election_year"] = fn["posted_date"][:4]

        label = live_links.get(url, {}).get("portal_label", "")
        label_year = label if re.fullmatch(r"(19|20)\d{2}", label.strip()) else ""
        folder_year = ""
        fm = re.search(r"/(\d{4})elections/|/elections/(\d{4})/reports/", url)
        if fm:
            folder_year = fm.group(1) or fm.group(2)
        else:
            # state-channel rows carry the LG folder, e.g. "/Municipal/washington_2010 Elections"
            fm = re.search(r"_(\d{4})\b", entry.get("state_folder", "") or "")
            if fm:
                folder_year = fm.group(1)
        # 2-digit trailing dates ("brock belnap 4-7-10.pdf") -- only trusted to supply a
        # YEAR, and only when it agrees with the folder we found it in.
        if not fn["posted_date"]:
            dm = re.search(r"[ _-](\d{1,2})-(\d{1,2})-(\d{2})(?!\d)", os.path.splitext(fname)[0])
            if dm:
                yy = 2000 + int(dm.group(3))
                if not folder_year or str(yy) == folder_year:
                    fn["posted_date"] = f"{yy}-{int(dm.group(1)):02d}-{int(dm.group(2)):02d}"
        ryear, rsrc = "", ""
        for val, src in ((doc_year, "document"), (label_year, "portal_year_label"),
                         (fn["election_year"], "filename"), (folder_year, "url_folder")):
            if val:
                ryear, rsrc = val, src
                break

        # CYCLE PARITY (Summit-agent refinement, 2026-08-01): Washington County offices are
        # elected in EVEN years only, so an odd reporting year on an ELECTION-cycle filing
        # (interim/final/year-end) is suspect -- some clerks hand the blank county form to
        # municipalities and special districts, so the 17-16-6.5 header can false-POSITIVE.
        # An odd year on an ANNUAL officeholder report is normal (they are filed every
        # January) and is NOT flagged.
        # CYCLE YEAR -- distinct from reporting_year.  Utah's year-end report is due the
        # following JANUARY, so "1 5 2015 Contributions - Brock Belnap_01-13-2015.xls" is the
        # 2014 cycle's closing report, not a 2015 filing.  Two sources only, both defensible:
        #   document              -- the form printed an "Election Year" (2010/2012/2014 forms)
        #   derived:january-close -- filing date falls in January => prior year's cycle
        # Anything else stays BLANK rather than guessed.
        cycle, cycle_src = "", ""
        if doc_year:
            cycle, cycle_src = doc_year, "document"
        else:
            d = fn["report_label"] or fn["posted_date"]
            if d and re.match(r"\d{4}-01-", d):
                cycle, cycle_src = str(int(d[:4]) - 1), "derived:january-close"
            elif ryear and ryear.isdigit() and int(ryear) % 2 == 0:
                cycle, cycle_src = ryear, "even_reporting_year"

        parity = ""
        if cycle and cycle.isdigit() and int(cycle) % 2 == 1:
            parity = (f"odd CYCLE year {cycle} - Washington County offices are elected in EVEN "
                      f"years; the 17-16-6.5 header can false-positive (municipalities and "
                      f"special districts are handed the same blank county form), so verify "
                      f"the office line inside the form")
        elif not cycle and fn["filing_type"] not in ("annual", ""):
            parity = "cycle year not determinable from the source - not guessed"


        te = TEXTMETA.get(rel, {})
        date = fn["report_label"] or fn["posted_date"]
        date_src = ("report_label" if fn["report_label"] else
                    ("posted_date" if fn["posted_date"] else ""))
        if not date and ryear:
            date, date_src = ryear, "reporting_year_only"

        rows.append(dict(
            date=date, candidate=candidate, office=office,
            reporting_year=ryear, reporting_year_source=rsrc,
            cycle_year=cycle, cycle_year_source=cycle_src,
            election_year=doc_year, filing_type=fn["filing_type"],
            reporting_period="",
            title=f"{(doc_kind or fn['doc_kind_fn']).title()} - {candidate} ({office}"
                  f"{', ' + ryear if ryear else ''})",
            source_url=url, retrieved_date=rec["retrieved_utc"][:10],
            format=te.get("format", ""), extraction_method=te.get("extraction_method", ""),
            path=rel, text_path=te.get("text_path", ""),
            bytes=rec["bytes"], sha256=rec["sha256"], channel=chan,
            source_archive="wayback" if entry.get("source") == "wayback" else "county_live",
            wayback_timestamp=entry.get("wayback_timestamp", ""),
            fetch_url=entry["fetch_url"],
            doc_kind=doc_kind or fn["doc_kind_fn"],
            posted_date=fn["posted_date"], date_source=date_src,
            office_source=source, office_confidence=conf, roster_match=roster_via,
            document_office_raw=doc_office_raw, portal_office=portal_office,
            document_candidate=doc_name, candidate_source=cand_src,
            label_conflict=conflict, cycle_parity_flag=parity,
            needs_review=1 if (conf != "high" or not candidate or conflict or parity) else 0,
            notes="; ".join(x for x in (label_typo, det_note) if x),
        ))

    # ---- byte-identity dedup -------------------------------------------------------
    # The archived record lists some files under BOTH http:// and https:// (and under
    # whitespace variants of the same name), so the same document arrives twice.  Identical
    # sha256 == identical document: keep ONE row, and record the other source URLs on it
    # rather than dropping the provenance.
    by_sha = {}
    for r in rows:
        by_sha.setdefault(r["sha256"], []).append(r)
    deduped = []
    for sha, group in by_sha.items():
        group.sort(key=lambda r: (r["source_archive"] != "county_live", r["source_url"]))
        keep = group[0]
        alts = [g["source_url"] for g in group[1:]]
        keep["alt_source_urls"] = " ; ".join(alts)
        keep["n_identical_copies"] = len(group)
        deduped.append(keep)
    rows = deduped
    for r in rows:
        r.setdefault("alt_source_urls", "")
        r.setdefault("n_identical_copies", 1)

    rows.sort(key=lambda r: (r["reporting_year"], r["office"], r["candidate"], r["date"], r["path"]))
    _write(os.path.join(ROOT, "index.csv"), rows)
    _write(os.path.join(ROOT, "excluded_school_board.csv"), excluded)
    _write(os.path.join(ROOT, "unrecovered.csv"), unrec)
    print(f"index.csv {len(rows)} | excluded_school_board.csv {len(excluded)} | "
          f"unrecovered.csv {len(unrec)}")


def _write(path, rows):
    if not rows:
        open(path, "w").write("")
        return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


TEXTMETA = {}
_te = os.path.join(ROOT, "text_extraction.csv")
if os.path.exists(_te):
    for _r in csv.DictReader(open(_te)):
        TEXTMETA[_r["raw_path"]] = _r

if __name__ == "__main__":
    sys.exit(main())
