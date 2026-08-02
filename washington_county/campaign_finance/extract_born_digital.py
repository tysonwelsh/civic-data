#!/usr/bin/env python3
"""Washington County campaign finance — BORN-DIGITAL half of the stated-totals cache.

Writes `vision/<key>.json` for every filing whose figures are machine-readable, so that
NO vision (and no OCR guessing) is spent where the county published real cells or a real
text layer:

  * 2014-2015 `.xls` "County Candidate Summary" workbooks  -> xlrd cell read
  * 2010-2013 born-digital "County Candidate Summary" PDFs -> pdftotext -layout re-read

The scanned/handwritten filings (2006, 2016-2025) are NOT touched here — their cache files
are hand-written by the vision pass (`"transcribed_by": "vision-transcribed(...)"`).

Cache format: see `CLAUDE.md` -> "The stated-totals cache (`vision/*.json`)".
Idempotent; safe to re-run. Consumed by `build_finance.py`.

CARDINAL RULES honored here:
  - every figure is carried VERBATIM as the source printed it (the `$`/comma forms of the
    PDF era are kept in `*_printed`; the numeric twin is a straight strtod, never a repair);
  - a cell the source left EMPTY stays empty and lands in `blank_fields` — never a zero;
  - the county's own arithmetic is never corrected (several summaries do not foot).
"""
import csv
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda *p: os.path.join(HERE, *p)

TRANSCRIBED_BY = ("born-digital-read(pdftotext -layout / xlrd cell read; "
                  "2026-08-01 totals tranche)")

# ---------------------------------------------------------------- filing grouping
# Washington splits ONE logical filing across up to three published files
# (`County Candidate Summary` + `Contributions` + `Expenditures`).  The filing key is
#   (channel, report_label, candidate-from-filename)
# where report_label is the deadline the county stamped on the filename -- either a
# leading `M D YYYY` / `M-D-YYYY`, an inline one, or the trailing `_MM-DD-YYYY` posting
# date.  Self-contained `statement` files (the whole 2006/2016-2025 cover-form era, plus a
# handful of born-digital ones) are ALWAYS their own filing: key = ("FILE", path).
KIND_RE = re.compile(r"(county candidate summary|summary|contributions?|expenditures?)", re.I)
MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")

# Two published filenames misspell the filer, which would otherwise split one filing in two.
# Both verified against the workbook's own Candidate cell.  Verbatim strings stay in the
# cache `cover`/`files`; only the GROUPING key is normalized.
NAME_ALIASES = {
    "NATHAN GRERGG CAPLIN": "NATHAN GREGG CAPLIN",   # `4 4 2014 Contributions - Nathan Grergg Caplin`
    "DAVID STIRLING": "DAVID STIRLAND",              # 2018 forms spell it both ways
}
# Channels the county publishes ONE-FILE-PER-FILING (annual re-posts / state scans): never
# grouped across files, even when the filenames share a filer.
FILE_PER_FILING_CHANNELS = {"live_wp", "state_disclosures", "live_outpost"}
# The 2008 HB-29 channel publishes every filing as a `Detailed Contribution Report` +
# `Detailed Expenditures Report` PAIR and NEVER as a self-contained statement, so it is
# always grouped by (channel, label, name).  Without this, one 2008 filing splits in two:
# `Gregory Aldred Contribution.pdf` (singular "Contribution") matches no doc_kind filename
# rule and lands in index.csv as doc_kind='statement', which the shortcut below would
# otherwise treat as its own filing.
ALWAYS_GROUPED_CHANNELS = {"wayback_clerkpdf2008"}


def parse_filename(fn):
    stem = os.path.splitext(fn)[0]
    stem = re.sub(r"~\d+$", "", stem)
    label = ""
    m = re.match(r"^\s*(\d{1,2})[ .-](\d{1,2})[ .-](\d{4})\s*[-]?\s*", stem)
    if m:
        label = "%04d-%02d-%02d" % (int(m.group(3)), int(m.group(1)), int(m.group(2)))
        stem = stem[m.end():]
    posted = ""
    m = re.search(r"_(\d{2})-(\d{2})-(\d{4})$", stem)
    if m:
        posted = "%s-%s-%s" % (m.group(3), m.group(1), m.group(2))
        stem = stem[:m.start()]
    rest = KIND_RE.sub(" ", stem)
    inline = ""
    m = re.search(r"(\d{1,2})\s+(\d{1,2})\s+(\d{4})", rest)
    if m:
        inline = "%04d-%02d-%02d" % (int(m.group(3)), int(m.group(1)), int(m.group(2)))
        rest = rest[:m.start()] + rest[m.end():]
    m = re.search(r"(%s)\s+(\d{1,2})\s+(\d{4})" % MONTHS, rest, re.I)
    if m:
        inline = m.group(0)
        rest = rest[:m.start()] + rest[m.end():]
    name = re.sub(r"[^A-Za-z. ]", " ", rest)
    name = re.sub(r"\s+", " ", name).strip(" .-")
    return label, posted, inline, name


def filing_key(row):
    """Returns (key_tuple, report_label). `key_tuple` is hashed into the cache filename."""
    fn = os.path.basename(row["path"])
    if row["channel"] not in ALWAYS_GROUPED_CHANNELS and (
            row["doc_kind"] == "statement" or row["channel"] in FILE_PER_FILING_CHANNELS):
        return ("FILE", row["path"]), ""
    label, posted, inline, name = parse_filename(fn)
    # `4 4 2001 … _04-04-2014.xls` — a source typo AVAILABILITY.md §5 already records.
    # The POSTED date governs: when the stamped deadline's year is more than a year off the
    # posting year, keep the stamped month/day and take the year from the posting.
    if label and posted and abs(int(label[:4]) - int(posted[:4])) > 1:
        label = posted[:4] + label[4:]
    lab = label or inline or posted
    name = NAME_ALIASES.get(name.upper(), name.upper())
    return (row["channel"], lab, name), lab


def cache_key(key_tuple):
    return hashlib.sha1("|".join(key_tuple).encode("utf-8")).hexdigest()[:8]


def group_index(index_rows):
    groups = {}
    for r in index_rows:
        k, lab = filing_key(r)
        g = groups.setdefault(k, {"key": k, "label": lab, "rows": []})
        g["rows"].append(r)
    for g in groups.values():
        g["rows"].sort(key=lambda r: (r["doc_kind"] != "summary", r["path"]))
    return groups


# ---------------------------------------------------------------- value helpers
def money_pair(printed):
    """('$1,234.56' | 1234.56 | '') -> (printed_verbatim, numeric_string_or_'')."""
    if printed is None:
        return "", ""
    s = str(printed).strip()
    if s == "":
        return "", ""
    num = s.replace("$", "").replace(",", "").strip()
    neg = False
    if num.startswith("(") and num.endswith(")"):
        neg, num = True, num[1:-1]
    if num.startswith("-"):
        neg, num = True, num[1:]
    try:
        v = float(num)
    except ValueError:
        return s, ""
    if neg:
        v = -v
    return s, ("%g" % v if v == int(v) and abs(v) < 1e15 else "%.2f" % v)


def xl_date(v, datemode=0):
    try:
        import xlrd
        y, mo, d, *_ = xlrd.xldate_as_tuple(float(v), datemode)
        return "%04d-%02d-%02d" % (y, mo, d)
    except Exception:
        return str(v)


# ---------------------------------------------------------------- .xls summary
def read_xls_summary(path):
    import xlrd
    bk = xlrd.open_workbook(path)
    sh = bk.sheet_by_index(0)
    cover = {"candidate": "", "office": "", "district": "", "election_year": ""}
    rows = []
    split_cols = False
    header_row = None
    for ri in range(sh.nrows):
        vals = [c.value for c in sh.row(ri)]
        txt = [str(v).strip() for v in vals]
        joined = " ".join(t for t in txt if t)
        if joined.lower().startswith("candidate:"):
            for c in sh.row(ri):
                if c.ctype == 2 and 1990 < float(c.value) < 2100:
                    cover["election_year"] = str(int(c.value))
            nxt = [str(c.value).strip() for c in sh.row(ri + 1) if str(c.value).strip()]
            if nxt:
                cover["candidate"] = nxt[0]
                tail = nxt[1:]
                if tail and re.fullmatch(r"(WASHINGTON\s+)?COUNTY", tail[-1], re.I):
                    cover["district"] = tail[-1]
                    tail = tail[:-1]
                cover["office"] = " ".join(tail)
        if joined.lower().startswith("submitted"):
            header_row = ri
        if "$51 OR MORE" in joined.upper():
            split_cols = True
        if header_row is not None and ri > header_row:
            cells = sh.row(ri)
            if cells[0].ctype in (2, 3) and str(cells[0].value).strip() != "":
                nums = [c for c in cells if c.ctype == 2]
                dates = [c for c in cells if c.ctype == 3]
                sub = xl_date(dates[0].value, bk.datemode) if dates else ""
                due = xl_date(dates[1].value, bk.datemode) if len(dates) > 1 else ""
                row = {"submitted": sub, "date_due": due}
                if split_cols:
                    order = ["contrib_gt50", "contrib_le50", "expenses", "balance"]
                else:
                    order = ["contrib_gt50", "expenses", "balance"]
                for i, name in enumerate(order):
                    row[name] = str(nums[i].value) if i < len(nums) else ""
                rows.append(row)
    return cover, rows, split_cols


# ---------------------------------------------------------------- born-digital PDF summary
# The PDF era prints negatives BOTH ways -- `-$375.00` and the accounting form `(375.00)`
# (no dollar sign).  Both are matched, and both are kept verbatim in `*_printed`.
MONEY = r"\(\$?[\d,]+\.\d{2}\)|-?\$[\d,]+\.\d{2}|-?\$[\d,]+"
DATE = r"\d{1,2}/\d{1,2}/\d{4}"

# A handful of postings BUNDLE all three sheets into ONE PDF (the live_wp annual re-posts
# `2010-David-Whitehead.pdf` / `2011-David-Whitehead.pdf`: contributions ledger + County
# Candidate Summary + expenditures ledger, in one file).  The summary parse must be
# NARROWED to the summary section, or the itemised ledger lines below it -- which also
# carry a date and a dollar amount -- are read as extra summary rows.
SUMMARY_SECTION = re.compile(r"County\s+Candidate\s+Summary", re.I)
LEDGER_SECTION = re.compile(r"^\s*All\s+(Contributions?|Expe\w*)\s+for\b", re.I)


def pdf_text(path):
    return subprocess.run(["pdftotext", "-layout", path, "-"],
                          capture_output=True, text=True).stdout


def read_pdf_summary(path):
    txt = pdf_text(path)
    lines = txt.splitlines()
    # Narrow to the County Candidate Summary section when the file bundles other sheets.
    # No-op for a summary-only export (the header is the first line and no ledger follows).
    starts = [i for i, l in enumerate(lines) if SUMMARY_SECTION.search(l)]
    if starts:
        s = starts[0]
        e = len(lines)
        for j in range(s + 1, len(lines)):
            if LEDGER_SECTION.search(lines[j]):
                e = j
                break
        lines = lines[s:e]
    cover = {"candidate": "", "office": "", "district": "", "election_year": ""}
    split_cols = any("$51 OR MORE" in l.upper() for l in lines)
    for i, l in enumerate(lines):
        if l.strip().lower().startswith("candidate:"):
            m = re.search(r"(\d{4})\s+Election Year", l)
            if m:
                cover["election_year"] = m.group(1)
            for j in range(i + 1, min(i + 3, len(lines))):
                seg = [s.strip() for s in re.split(r"\s{2,}", lines[j].strip()) if s.strip()]
                if seg:
                    cover["candidate"] = seg[0]
                    tail = seg[1:]
                    if tail:
                        last = tail[-1]
                        if re.fullmatch(r"(Washington\s+)?County", last, re.I):
                            cover["district"] = last
                            tail = tail[:-1]
                        elif re.search(r"\sCounty$", last, re.I):
                            cover["district"] = "County"
                            tail = tail[:-1] + [re.sub(r"\s+County$", "", last, flags=re.I)]
                    cover["office"] = " ".join(tail)
                    break
            break
    rows = []
    for l in lines:
        d = re.findall(DATE, l)
        mny = re.findall(MONEY, l)
        if not d or not mny:
            continue
        row = {"submitted": d[0] if len(d) > 1 else "",
               "date_due": d[1] if len(d) > 1 else d[0]}
        order = (["contrib_gt50", "contrib_le50", "expenses", "balance"] if split_cols
                 else ["contrib_gt50", "expenses", "balance"])
        for i, name in enumerate(order):
            row[name] = mny[i] if i < len(mny) else ""
        rows.append(row)
    return cover, rows, split_cols


# ---------------------------------------------------------------- build one cache file
def which_row(rows, label):
    """The printed summary row THIS posting reports. Match the filename's stamped deadline
    against the printed Date Due; else fall back to the LAST printed row that carries any
    figure. Returns (index, basis) -- basis is recorded in the cache, never hidden."""
    def norm(d):
        m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", str(d))
        if m:
            return "%04d-%02d-%02d" % (int(m.group(3)), int(m.group(1)), int(m.group(2)))
        return str(d)
    if label:
        for i, r in enumerate(rows):
            if norm(r.get("date_due", "")) == label or norm(r.get("submitted", "")) == label:
                return i, "date_due matches the deadline stamped on the filename"
    for i in range(len(rows) - 1, -1, -1):
        if any(str(rows[i].get(k, "")).strip() not in ("", "0", "0.0")
               for k in ("contrib_gt50", "contrib_le50", "expenses", "balance")):
            return i, "last printed row carrying a figure (no deadline on the filename)"
    return (len(rows) - 1, "last printed row") if rows else (-1, "no printed rows")


def build_cache(group, index_by_path):
    rows = group["rows"]
    primary = None
    for r in rows:
        if r["doc_kind"] == "summary" and "summary" in os.path.basename(r["path"]).lower():
            primary = r
            break
    if primary is None:
        for r in rows:
            if r["doc_kind"] == "summary":
                primary = r
                break
    bundled = False
    if primary is None:
        # BUNDLED single file: the posting staples the three sheets together, so the index's
        # doc_kind (read off the file's FIRST header, a ledger) says `contributions` while
        # the file also carries the County Candidate Summary.  Decided by CONTENT.
        for r in rows:
            if r["format"] == "text" and SUMMARY_SECTION.search(pdf_text(D(r["path"]))):
                primary, bundled = r, True
                break
    if primary is None:
        return build_ledger_only_cache(group)

    path = primary["path"]
    if primary["format"] == "spreadsheet":
        cover, printed, split_cols = read_xls_summary(D(path))
        method = "xls_cells(xlrd)"
    else:
        cover, printed, split_cols = read_pdf_summary(D(path))
        method = "pdftotext_layout"

    idx, basis = which_row(printed, group["label"])
    prow = printed[idx] if idx >= 0 else {}
    prev = printed[idx - 1] if idx > 0 else {}

    rep = {"report_no": 1, "pages": "",
           "submitted": prow.get("submitted", ""), "date_due": prow.get("date_due", ""),
           "period_start": "", "period_end": "",
           "row_index": idx, "row_basis": basis}
    blanks = []
    for fld in ("contrib_gt50", "contrib_le50", "expenses"):
        pr, num = money_pair(prow.get(fld, ""))
        rep[fld + "_this_printed"], rep[fld + "_this"] = pr, num
        rep[fld + "_last_printed"], rep[fld + "_last"] = "", ""
        rep[fld + "_cum_printed"], rep[fld + "_cum"] = "", ""
        if pr == "" and not (fld == "contrib_le50" and not split_cols):
            blanks.append(fld + "_this")
    pr, num = money_pair(prow.get("balance", ""))
    rep["balance_end_printed"], rep["balance_end"] = pr, num
    pr, num = money_pair(prev.get("balance", ""))
    rep["balance_last_printed"], rep["balance_last"] = pr, num
    rep["conf"] = {f: ("high" if rep.get(f + "_this", "") != "" else "")
                   for f in ("contrib_gt50", "contrib_le50", "expenses")}
    rep["conf"]["balance"] = "high" if rep["balance_end"] != "" else ""
    rep["blank_fields"] = blanks
    rep["notes"] = ""

    return {
        "filing_key": "|".join(group["key"]),
        "channel": primary["channel"],
        "sheet_type": "summary_sheet",
        "is_incremental": True,
        "regime_note": ("County Candidate Summary sheet: the Contributions / Expenditures "
                        "columns are PER-PERIOD increments; the Balance column is the "
                        "running cumulative balance. The companion Contributions / "
                        "Expenditures ledgers restate the whole cycle to date."),
        "primary_path": path,
        "primary_doc_kind": primary["doc_kind"],
        "files": [{"path": r["path"], "doc_kind": r["doc_kind"], "sha256": r["sha256"],
                   "format": r["format"]} for r in rows],
        "transcribed_by": TRANSCRIBED_BY,
        "extract_method": method,
        "contrib_columns_split": split_cols,
        "cover": cover,
        "cover_conf": {k: ("high" if v else "") for k, v in cover.items()},
        "index_office": primary["office"],
        "index_office_source": primary["office_source"],
        "index_office_confidence": primary["office_confidence"],
        "index_candidate": primary["candidate"],
        "index_reporting_year": primary["reporting_year"],
        "index_cycle_year": primary["cycle_year"],
        "index_filing_type": primary["filing_type"],
        "printed_rows": printed,
        "reports": [rep],
        "unreadable": [],
        "notes": ("the posting BUNDLES all three sheets in one PDF; the summary block was "
                  "read from its own section, the itemised ledger lines below it ignored"
                  if bundled else ""),
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# ---------------------------------------------------------------- ledger-only filings
# Two born-digital generations publish a filing as ITEMISED LEDGERS WITH NO SUMMARY SHEET:
#   * `wayback_clerkpdf2008` -- the original HB-29 "Detailed Contribution Report:" /
#     "Detailed Expenditures Report:" pair (Date | Name | Amount).  The county printed the
#     matching TOTALS on its own web page instead, which is what `portal_stated_totals.csv`
#     holds -- so these filings have a stated total, just not inside the file.
#   * a 2011 `financialreports` pair (Cory Pulsipher) whose summary was never posted.
# The cache records stated totals as BLANK (the file states none -- never invent one from
# the portal, and never promote a counted sum into a stated field).
LEDGER_HEAD_2008 = re.compile(
    r"^\s*(?P<name>.+?)\s+(?P<office>(County|Local\s+School|Board\s+of)\b.*?)\s{2,}"
    r"(?P<year>(19|20)\d{2})\s*$")
LEDGER_HEAD_ALL = re.compile(
    r"^\s*All\s+(Contributions?|Expe\w*)\s+for\s{2,}(?P<rest>.+?)\s*$")
DETAIL_HEAD = re.compile(r"Detailed\s+(Contribution|Expenditure)s?\s+Report", re.I)
# 2008 ledger data line: a long-form date, then a single money column at the end.
LEDGER_2008_ROW = re.compile(
    r"^\s*[A-Z][a-z]+\.?\s+\d{1,2},\s+(19|20)\d{2}\b.*?(?P<amt>\$[\d,]+(?:\.\d{2})?)\s*$")


def read_ledger_header(path):
    """Cover facts a ledger-only filing states in its OWN header. '' where it says nothing."""
    lines = pdf_text(path).splitlines()
    cover = {"candidate": "", "office": "", "district": "", "election_year": ""}
    detail_form = any(DETAIL_HEAD.search(l) for l in lines[:8])
    for l in lines[:6]:
        if not l.strip():
            continue
        m = LEDGER_HEAD_ALL.match(l)
        if m:
            cells = [c.strip() for c in re.split(r"\s{2,}", m.group("rest")) if c.strip()]
            if cells:
                cover["candidate"] = cells[0]
                cover["office"] = " ".join(cells[1:])
            break
        m = LEDGER_HEAD_2008.match(l)
        if m and detail_form:
            cover["candidate"] = m.group("name").strip()
            cover["office"] = m.group("office").strip()
            cover["election_year"] = m.group("year")
            break
    return cover


MONEY_TOKEN = re.compile(r"-?\$-?[\d,]+(?:\.\d{2})?")


def count_2008_ledger(path):
    """COUNTED (not stated) sum of the 2008 `Detailed … Report:` table -- one money column,
    so a complete parse is unambiguous. Used ONLY to score against the county's own
    portal-printed totals (`portal_stated_totals.csv`); never written to a stated field.

    GATED ON PROVABLE COMPLETENESS. Some 2008 ledgers are clean one-line-per-entry tables
    (Gregory Aldred); others wrap an entry over two lines, date an entry "Various" instead
    of a calendar date, run the date into the payee with no space, or carry a negative
    adjustment (Lin Alder; Gardner's two undated "Sept 2008" rows). A row regex silently
    UNDER-counts those. So every money token in the body is counted independently, and a
    sum is returned ONLY when the matched rows consume every one of them. Otherwise the
    sum is withheld with the shortfall recorded -- a partial sum presented as a ledger
    total would be worse than no sum at all.

    Returns (n_rows, total, complete, n_money_tokens)."""
    lines = pdf_text(path).splitlines()
    body = []
    seen_header = False
    for l in lines:
        if not seen_header:
            # the column header line ("Date: … Amount:") ends the preamble
            if re.search(r"Date\s*:", l) and re.search(r"Amount\s*:", l):
                seen_header = True
            continue
        if re.fullmatch(r"\s*\d{0,3}\s*", l):
            continue                        # page-number / blank line
        body.append(l)
    n = 0
    total = 0.0
    for l in body:
        m = LEDGER_2008_ROW.match(l)
        if m:
            n += 1
            total += float(m.group("amt").replace("$", "").replace(",", ""))
    tokens = sum(len(MONEY_TOKEN.findall(l)) for l in body)
    return n, round(total, 2), (n == tokens and n > 0), tokens


def build_ledger_only_cache(group):
    rows = group["rows"]
    primary = rows[0]
    cover = read_ledger_header(D(primary["path"]))
    for r in rows:                       # fill blanks from the sibling sheet's header
        if all(cover.values()):
            break
        for k, v in read_ledger_header(D(r["path"])).items():
            if v and not cover[k]:
                cover[k] = v

    money_fields = []
    for side in ("contrib_gt50", "contrib_le50", "expenses"):
        for col in ("last", "this", "cum"):
            money_fields.append(f"{side}_{col}")
    money_fields += ["balance_last", "balance_this", "balance_end"]
    rep = {"report_no": 1, "pages": "", "submitted": "", "date_due": "",
           "period_start": "", "period_end": "", "row_index": "",
           "row_basis": "no summary sheet published with this filing"}
    for f in money_fields:
        rep[f + "_printed"], rep[f] = "", ""
    rep["conf"] = {"contrib_gt50": "", "contrib_le50": "", "expenses": "", "balance": ""}
    rep["blank_fields"] = money_fields
    rep["notes"] = ("LEDGER-ONLY filing: the county published the itemised "
                    "contribution/expenditure sheets without the County Candidate Summary, "
                    "so the filing states NO totals. Left blank, never inferred.")

    counted = None
    if primary["channel"] == "wayback_clerkpdf2008":
        counted = {"method": "counted rows of the 2008 `Detailed … Report:` single-money-"
                             "column table (DERIVED, not a stated total); withheld unless "
                             "the matched rows consume every money token in the body"}
        for r in rows:
            n, tot, complete, tokens = count_2008_ledger(D(r["path"]))
            side = "contrib" if r["doc_kind"] != "expenditures" else "expend"
            counted[f"{side}_path"] = r["path"]
            counted[f"n_{side}_rows"] = n
            counted[f"{side}_money_tokens"] = tokens
            counted[f"{side}_complete"] = complete
            counted[f"{side}_sum"] = ("%.2f" % tot) if complete else ""
            if not complete:
                counted[f"{side}_withheld_reason"] = (
                    "%d money tokens in the body vs %d parsed rows -- wrapped entries, "
                    "'Various'-dated entries and/or run-together date+payee lines are not "
                    "captured one-per-row, so no sum is published" % (tokens, n))

    return {
        "filing_key": "|".join(group["key"]),
        "channel": primary["channel"],
        "sheet_type": "ledger_only",
        "is_incremental": False,
        "regime_note": ("Itemised ledger restating the whole cycle to date (the 2008 "
                        "`Detailed … Report` and the 2011 `All … for` sheets both run from "
                        "the first transaction of the cycle), so a cycle total is the "
                        "LATEST filing, never a sum of filings. No totals are printed."),
        "primary_path": primary["path"],
        "primary_doc_kind": primary["doc_kind"],
        "files": [{"path": r["path"], "doc_kind": r["doc_kind"], "sha256": r["sha256"],
                   "format": r["format"]} for r in rows],
        "transcribed_by": TRANSCRIBED_BY,
        "extract_method": "pdftotext_layout(ledger header)",
        "contrib_columns_split": False,
        "cover": cover,
        "cover_conf": {k: ("high" if v else "") for k, v in cover.items()},
        "index_office": primary["office"],
        "index_office_source": primary["office_source"],
        "index_office_confidence": primary["office_confidence"],
        "index_candidate": primary["candidate"],
        "index_reporting_year": primary["reporting_year"],
        "index_cycle_year": primary["cycle_year"],
        "index_filing_type": primary["filing_type"],
        "printed_rows": [],
        "reports": [rep],
        "ledger_counted": counted,
        "unreadable": [],
        "notes": ("no summary sheet in this filing; stated totals are honestly BLANK"
                  + ("" if counted else ". The itemised rows are COLUMN-POSITIONAL "
                     "(Amount / In Kind / Loan share the line), so they are not counted "
                     "here -- a mis-columned sum would be worse than no sum")),
        "generated_utc": datetime.datetime.now(datetime.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def main():
    index_rows = list(csv.DictReader(open(D("index.csv"), newline="", encoding="utf-8")))
    by_path = {r["path"]: r for r in index_rows}
    groups = group_index(index_rows)
    os.makedirs(D("vision"), exist_ok=True)
    written = skipped = vision_owned = 0
    for k, g in sorted(groups.items()):
        out = D("vision", cache_key(k) + ".json")
        fmts = {r["format"] for r in g["rows"]}
        if fmts & {"scanned"}:
            skipped += 1
            continue  # vision pass owns these
        # HARD GUARD (2026-08-02): a cache already written by the VISION pass is never
        # overwritten by this pass.  `format` is an index classification and it is
        # sometimes wrong in the direction that matters -- several county PDFs carry a
        # text layer holding nothing but a stamped transmittal note while the report
        # faces are images (`Ryan Sullivan` 2024, `Gil Almquist` 2016, `Dean J. Cox`
        # 2016).  Vision read those pages; a text-layer re-read would silently replace a
        # good transcription with an empty one.  The cache's own `transcribed_by` is the
        # authority on who owns it, never the index's `format`.
        if os.path.exists(out):
            try:
                if json.load(open(out, encoding="utf-8")).get(
                        "transcribed_by", "").startswith("vision-"):
                    vision_owned += 1
                    continue
            except (ValueError, OSError):
                pass  # unreadable cache -> regenerate it
        cache = build_cache(g, by_path)
        if cache is None:
            skipped += 1
            continue
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        written += 1
    print("born-digital caches written: %d   (skipped %d scanned/unparseable, "
          "%d already vision-transcribed)" % (written, skipped, vision_owned))


if __name__ == "__main__":
    main()
