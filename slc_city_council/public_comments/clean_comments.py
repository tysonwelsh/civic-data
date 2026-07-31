#!/usr/bin/env python3
"""
Phase 3: Produce a cleaned comments dataset from the raw Vision API JSON.

Reads progress/raw/{year}/*.json (the immutable source of truth) and writes the
cleaned dataset as all_comments_clean.csv, per-year CSVs, and comments_clean.json
(structured, with typed fields). The raw JSON and all_comments_vision.csv are NOT
modified. A merged multi-part comment carries every source page it spans in
page_numbers (a list in JSON, a ";"-joined string in CSV). Each row also carries
period_start/period_end -- the council-week window (Wed -> Tue) read from the
source filename, with four known filename typos corrected (see PERIOD_OVERRIDES).

Cleaning steps:
  1. Route out non-comment tables (petition / sign-on sheets, sign-in lists).
     These are detected structurally: the page's detected columns contain no
     comment/description/message column. All their rows are dropped.
  2. Re-stitch continuation rows (e.g. "Tiffany 1/2" + "Tiffany 2/2") into a
     single comment. Pieces are grouped by (file, person) and ordered by part
     number, so parts interleaved with other comments still reunite; embedded
     "*Continued Below/Above*" / "N of M" markers are scrubbed from the text.
  3. Drop non-substantive comments (empty/placeholder, "Live Public Comment",
     bare attachment pointers, staff-written phone/voicemail summaries) and all
     voicemail content (voicemail files + source=Voicemail rows) -- rows that are
     not the commenter's own analyzable written text.
  4. Normalize the mixed date formats into an ISO date_normalized column
     (YYYY-MM-DD). The original date string is preserved untouched.
  5. Flag (do not drop) suspicious rows in a quality_flag column for review.
  6. Drop exact duplicates (same name + comment + date), which arise from
     overlapping file periods, so weekly bins on date_normalized don't double-count.

Dropped rows (non-comment tables + non-substantive comments + duplicates) are
written to all_comments_dropped.csv with a _drop_reason for audit.

Usage:
    python3 clean_comments.py            # write all_comments_clean.csv
    python3 clean_comments.py --report   # also print a cleaning report
"""

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

from config import RAW_DIR, BASE_DIR, UNIFIED_COLUMNS

OUTPUT_CSV = BASE_DIR / "all_comments_clean.csv"
OUTPUT_JSON = BASE_DIR / "comments_clean.json"        # structured cleaned export
DROPPED_CSV = BASE_DIR / "all_comments_dropped.csv"  # audit trail of removed rows
BY_YEAR_DIR = BASE_DIR / "by_year"                   # one cleaned CSV per year

# A page is a real comment table only if one of its columns is the comment body.
COMMENT_COLUMN_TOKENS = ("comment", "description", "message")

# Output schema: unified columns (page_number -> page_numbers) + derived columns.
OUTPUT_COLUMNS = [("page_numbers" if c == "page_number" else c)
                  for c in UNIFIED_COLUMNS] + [
    "period_start", "period_end", "date_normalized", "quality_flag"]


def clean_text(text):
    """Normalize whitespace."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())


# ---------------------------------------------------------------------------
# Load + flatten
# ---------------------------------------------------------------------------

def load_all_raw_json():
    """Load all raw JSON files in reading order (year, then filename)."""
    all_data = []
    for year_dir in sorted(RAW_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        for json_file in sorted(year_dir.glob("*.json")):
            with open(json_file) as f:
                all_data.append(json.load(f))
    return all_data


def is_comment_table(page):
    """A page is a comment table if a detected column is the comment body."""
    cols = " | ".join(page.get("columns_detected", [])).lower()
    return any(tok in cols for tok in COMMENT_COLUMN_TOKENS)


def flatten(all_data):
    """
    Flatten page results into an ordered list of row dicts.

    Returns (kept_rows, dropped_rows). Rows from non-comment tables (petitions,
    sign-in sheets) are routed into dropped_rows. Continuation flags/markers are
    preserved on kept rows for the stitching step.
    """
    kept, dropped = [], []
    for pdf_data in all_data:
        source_file = pdf_data["source_file"]
        for page_key in sorted(pdf_data.get("pages", {}).keys(), key=int):
            page = pdf_data["pages"][page_key]
            if page.get("page_type") != "table":
                continue

            page_num = int(page_key) + 1
            comment_table = is_comment_table(page)

            for c in page.get("comments", []):
                row = {
                    "date": clean_text(c.get("date", "")),
                    "contact_name": clean_text(c.get("contact_name", "")),
                    "subject": clean_text(c.get("subject", "")),
                    "topic": clean_text(c.get("topic", "")),
                    "comment": clean_text(c.get("comment", "")),
                    "district": clean_text(c.get("district", "")),
                    "source": clean_text(c.get("source", "")),
                    "has_attachment": "TRUE" if c.get("has_attachment") else "",
                    "source_file": source_file,
                    "page_number": str(page_num),
                    "_is_continuation": bool(c.get("is_continuation", False)),
                    "_marker": clean_text(c.get("continuation_marker", "")),
                }
                if comment_table:
                    kept.append(row)
                else:
                    row["_drop_reason"] = "non_comment_table"
                    dropped.append(row)
    return kept, dropped


# ---------------------------------------------------------------------------
# Continuation re-stitching
# ---------------------------------------------------------------------------

PART_RE = re.compile(r"(\d+)\s*(?:/|of)\s*(\d+)")
NAME_SUFFIX_RE = re.compile(r"^(.*?)[\s,]*\(?\b(\d+)\s*(?:/|of)\s*(\d+)\)?\s*$")
SUBJECT_CONTINUED_RE = re.compile(r"^\s*CONTINUED[!]*\s*", re.IGNORECASE)
# Continuation markers embedded in the comment body (2020-style files set no flag).
EMBED_RE = re.compile(r"continue[d]?\s+(?:below|above|from\s+above)", re.IGNORECASE)

# Regexes to scrub continuation markers out of the assembled comment text.
MARKER_STRIP_RES = [
    # Asterisk-delimited "...continued..." marker: *Continued 1/4*, *continued 2/2*,
    # *Continued Below 1 of 5*, * continued 2/2*. Only marker-shaped content (direction
    # word + part numbers) is allowed between the asterisks, so prose is never eaten.
    re.compile(r"\*+\s*continue[d]?\s*(?:below|above|from\s+above)?\s*"
               r"\d*\s*(?:/|of)?\s*\d*\s*\*+", re.IGNORECASE),
    # Asterisk-led directional marker with no closing asterisk: **Continued from above
    re.compile(r"\*+\s*continue[d]?\s+(?:below|above|from\s+above)\b"
               r"\s*\d*\s*(?:of|/)?\s*\d*", re.IGNORECASE),
    # Bare directional marker: Continued Below / Continue Above / Continued from above
    re.compile(r"continue[d]?\s+(?:below|above|from\s+above)\b", re.IGNORECASE),
    re.compile(r"CONTINUED!+", re.IGNORECASE),
    re.compile(r"^\s*\d+\s+of\s+\d+\b\.?\s*"),                  # leading "2 of 5"
    re.compile(r"\s*\b\d+\s+of\s+\d+\b\s*\**\s*$"),             # trailing "1 of 5"
    re.compile(r"\*{2,}"),                                       # leftover ** markers
]


def base_name(name):
    """Drop a trailing 'X/Y' or 'X of Y' part marker from a contact name."""
    m = NAME_SUFFIX_RE.match(name)
    return (m.group(1) if m else name).strip()


def name_key(name):
    """Normalize a name to letters-only for grouping across part-row typos."""
    return re.sub(r"[^a-z]", "", base_name(name).lower())


def part_number(row):
    """
    Best-guess part number if this row is a piece of a multi-part comment, else None.

    Checks (in order): the continuation_marker field, a 'Name X/Y' suffix, then
    markers embedded in the comment text. Embedded part numbers are only trusted
    when a continuation context (flag, marker word, or 'Continued Below/Above')
    is present, so ordinary comments that happen to contain 'N of M' aren't caught.
    """
    marker = row.get("_marker", "")
    m = PART_RE.search(marker)
    if m:
        return int(m.group(1))

    nm = NAME_SUFFIX_RE.match(row.get("contact_name", ""))
    if nm:
        return int(nm.group(2))

    comment = row.get("comment", "")
    has_context = bool(EMBED_RE.search(comment)) or row.get("_is_continuation") or marker
    if has_context:
        edge = comment[:40] + " " + comment[-40:]
        m2 = PART_RE.search(edge)
        if m2:
            return int(m2.group(1))
        if re.search(r"continue[d]?\s+(?:above|from\s+above)", comment, re.IGNORECASE) \
                or "above" in marker.lower():
            return 2
        return 1
    return None


def strip_markers(text):
    """Remove embedded continuation markers from a comment body."""
    for rx in MARKER_STRIP_RES:
        text = rx.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def names_compatible(a, b):
    """
    Whether two contact names can belong to the same multi-part comment.

    Continuation parts frequently carry an EMPTY name (the PDF prints the name
    only on the first part), so an empty name is treated as a wildcard. Non-empty
    names match on equality, containment, or a shared 5-char prefix (typo-tolerant).
    """
    ka, kb = name_key(a), name_key(b)
    if not ka or not kb:
        return True
    return ka == kb or ka in kb or kb in ka or ka[:5] == kb[:5]


def page_numbers(chain):
    """Sorted, de-duplicated list of source page numbers a chain spans."""
    pages = {int(r["page_number"]) for r in chain if r.get("page_number", "").isdigit()}
    return sorted(pages)


def assemble_chain(chain):
    """Merge an ordered list of part-rows into one comment row."""
    head = dict(chain[0])
    for row in chain:
        if row.get("contact_name"):
            head["contact_name"] = base_name(row["contact_name"])
            break

    bodies = [strip_markers(r.get("comment", "")) for r in chain]
    head["comment"] = clean_text(" ".join(b for b in bodies if b))

    subjects = []
    for r in chain:
        s = SUBJECT_CONTINUED_RE.sub("", r.get("subject", "")).strip()
        if s and s not in subjects:
            subjects.append(s)
    head["subject"] = clean_text(" ".join(subjects))

    if any(r.get("has_attachment") == "TRUE" for r in chain):
        head["has_attachment"] = "TRUE"
    head["page_numbers"] = page_numbers(chain)
    return head


def restitch_continuations(rows):
    """
    Merge every piece of a multi-part comment into one row.

    Walks rows in reading order and greedily chains consecutive continuation
    parts: a piece joins the open chain when it is in the same file, its part
    number does not go backwards, and its name is compatible (an empty name
    counts as a match, since later parts are usually unnamed). Non-continuation
    rows (part_number is None) break the chain and pass through untouched, so two
    separate signed letters by the same person are never merged. A lone tail part
    (part > 1 with no siblings) is kept standalone and flagged as an orphan.
    """
    result = []
    stats = {"groups": 0, "merged": 0, "orphans": 0}
    i, n = 0, len(rows)

    while i < n:
        part = part_number(rows[i])
        if part is None:
            rows[i]["page_numbers"] = page_numbers([rows[i]])
            result.append(rows[i])
            i += 1
            continue

        chain = [rows[i]]
        last_part = part
        j = i + 1
        while j < n:
            npart = part_number(rows[j])
            if npart is None or rows[j]["source_file"] != rows[i]["source_file"]:
                break
            if npart < last_part:                       # a new chain is starting
                break
            if not names_compatible(rows[i]["contact_name"], rows[j]["contact_name"]):
                break
            chain.append(rows[j])
            last_part = npart
            j += 1

        if len(chain) > 1:
            merged = assemble_chain(chain)
            stats["groups"] += 1
            stats["merged"] += len(chain) - 1
            result.append(merged)
        else:
            row = assemble_chain(chain)              # still scrub markers off a lone part
            if part > 1:
                row["_orphan"] = True
                stats["orphans"] += 1
            result.append(row)
        i = j

    return result, stats


# ---------------------------------------------------------------------------
# Date normalization
# ---------------------------------------------------------------------------

DATE_PATTERNS = [
    (re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"), ("y", "m", "d")),       # 2020-12-08
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b"), ("m", "d", "y")),       # 1/10/2024
    (re.compile(r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b"), ("m", "d", "y")),       # 1-10-2024
    (re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2})\b"), ("m", "d", "yy")),      # 12/29/21
]

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], start=1)}
MONTH_NAME_RE = re.compile(r"\b([A-Za-z]+)\.?\s+(\d{1,2}),?\s+(\d{4})\b")  # May 19, 2020

# Source-type values that sometimes land in the date column (not real dates).
SOURCE_WORDS_RE = re.compile(
    r"email|voicemail|virtual comment|phone call|live public comment|letter",
    re.IGNORECASE)


def _iso(y, mo, d):
    """Validate (y, mo, d) and return ISO string, or '' if out of range."""
    if 1 <= mo <= 12 and 1 <= d <= 31 and 2015 <= y <= 2030:
        return f"{y:04d}-{mo:02d}-{d:02d}"
    return ""


def normalize_date(raw):
    """Extract an ISO date (YYYY-MM-DD) from a messy date string, or ''."""
    if not raw:
        return ""

    mn = MONTH_NAME_RE.search(raw)
    if mn and mn.group(1).lower() in MONTHS:
        return _iso(int(mn.group(3)), MONTHS[mn.group(1).lower()], int(mn.group(2)))

    for rx, order in DATE_PATTERNS:
        m = rx.search(raw)
        if not m:
            continue
        parts = dict(zip(order, m.groups()))
        y = int(parts["yy"]) + 2000 if "yy" in parts else int(parts["y"])
        iso = _iso(y, int(parts["m"]), int(parts["d"]))
        if iso:
            return iso
    return ""


FILENAME_DATE_RE = re.compile(r"(\d{7,8})")  # leading MMDDYYYY or MDDYYYY


def filename_date(source_file):
    """
    Infer the meeting/period date from the filename's leading digits, or ''.

    Filenames start with the period's first date, e.g. 06022020_FileB... ->
    2020-06-02, 01102024_01162024 -> 2024-01-10, 7182020_... -> 2020-07-18.
    """
    stem = Path(source_file).name
    m = FILENAME_DATE_RE.match(stem)
    if not m:
        return ""
    digits = m.group(1)
    year = int(digits[-4:])
    md = digits[:-4]            # 3 or 4 digits of month+day
    if len(md) == 4:
        mo, d = int(md[:2]), int(md[2:])
    else:                       # 3 digits -> single-digit month
        mo, d = int(md[:1]), int(md[1:])
    return _iso(year, mo, d)


# Each PDF covers a council "week" (Wed -> the following Tue). The period is read
# from the filename's two date tokens. These four filenames have typos that yield
# nonsense ranges; the corrections are confirmed against the comment dates inside
# each file. (Files are not renamed, to keep the source_file linkage intact.)
PERIOD_OVERRIDES = {
    "10212020_1152020.pdf":  ("2020-10-21", "2020-11-05"),  # "1152020" missing a digit
    "01012021_01082020.pdf": ("2021-01-01", "2021-01-08"),  # end year typo (2020 -> 2021)
    "1082025_10212025.pdf":  ("2025-10-08", "2025-10-21"),  # "1082025" dropped leading 1
    "0911204_09172024.pdf":  ("2024-09-11", "2024-09-17"),  # "0911204" malformed start
}

DIGIT_RUN_RE = re.compile(r"\d{7,8}")


def _token_to_iso(tok):
    """Parse an MMDDYYYY / MDDYYYY filename token to an ISO date, or ''."""
    year = int(tok[-4:])
    md = tok[:-4]
    mo, d = (int(md[:2]), int(md[2:])) if len(md) == 4 else (int(md[:1]), int(md[1:]))
    return _iso(year, mo, d)


def period_for(source_file):
    """
    Return (period_start, period_end) ISO dates for a file's coverage window.

    Uses the two date tokens in the filename (start, end); single-date files
    (early-2020 per-meeting PDFs) get start == end. Known typos are corrected
    via PERIOD_OVERRIDES.
    """
    name = Path(source_file).name
    if name in PERIOD_OVERRIDES:
        return PERIOD_OVERRIDES[name]
    isos = [iso for iso in (_token_to_iso(t) for t in DIGIT_RUN_RE.findall(name)) if iso]
    if not isos:
        return "", ""
    return isos[0], (isos[1] if len(isos) > 1 else isos[0])


# ---------------------------------------------------------------------------
# Non-substantive comments (placeholders, not the commenter's own analyzable text)
# ---------------------------------------------------------------------------

# Exact (case-folded) values that carry no analyzable content.
NONSUB_EXACT = {"", "no comment", "none", "n/a", "na", "no", "--", "."}

# "Live Public Comment" placeholder (the person spoke aloud; nothing was transcribed).
LIVE_RE = re.compile(r"^\W*live public comment\b", re.IGNORECASE)
# A bare pointer to an attachment/letter, with no comment text of its own.
ATTACH_ONLY_RE = re.compile(r"^\W*see corresponding (?:letter|attachment)\b.{0,40}$",
                            re.IGNORECASE)
# Staff-written third-person records of phone/voicemail comments, e.g.
# "Constituent called in to express support for the mask mandate." These are not
# the commenter's own written words. "Constituent"/"Caller" are unambiguous staff
# openers (a first-person comment never refers to its author this way), so they
# match alone; more generic openers also require a reporting verb to avoid
# catching real sentences like "Resident parking permits should...".
STAFF_STRONG_RE = re.compile(r"^\W*(?:constituent|caller)\b", re.IGNORECASE)
_STAFF_SUBJ = (r"(?:resident|citizen|community member|an? individual|"
               r"anonymous(?: constituent)?|member of the public)")
_STAFF_VERB = (r"(?:called|phoned|wrote|emailed|e-mailed|left (?:a )?(?:voice ?mail|message)|"
               r"wants?|has|had|believes?|feels?|thinks?|hopes?|wonders?|is|was|"
               r"does not want|expressed|stated|reported|requested|asked|concerned|"
               r"would like|supports?|opposes?|in support|in opposition|"
               r"voiced|conveyed|indicated|inquired|complained)")
STAFF_RE = re.compile(rf"^\W*{_STAFF_SUBJ}\b[^.]{{0,40}}?\b{_STAFF_VERB}\b", re.IGNORECASE)


def non_substantive_reason(comment):
    """Classify a comment as non-substantive, returning a drop reason or None."""
    c = comment.strip()
    if c.lower() in NONSUB_EXACT:
        return "empty_or_placeholder"
    if LIVE_RE.match(c):
        return "live_public_comment"
    if ATTACH_ONLY_RE.match(c):
        return "attachment_pointer"
    if STAFF_STRONG_RE.match(c) or STAFF_RE.search(c):
        return "staff_summary"
    return None


def is_voicemail(row):
    """True if a row is voicemail content (a voicemail file, or source=Voicemail)."""
    blob = " ".join((row.get("source_file", ""), row.get("source", ""),
                     row.get("date", ""))).lower()
    return "voicemail" in blob


# ---------------------------------------------------------------------------
# Quality flags
# ---------------------------------------------------------------------------

def quality_flags(row):
    """Return a |-joined string of quality flags for a row (may be empty)."""
    flags = []
    comment = row.get("comment", "")
    if not comment:
        flags.append("empty_comment")
    elif len(comment) < 15:
        flags.append("short_comment")
    if not row.get("date_normalized") and row.get("date"):
        flags.append("unparsed_date")
    if row.pop("_date_inferred", False):
        flags.append("date_from_filename")
    if row.pop("_orphan", False):
        flags.append("orphan_continuation")
    if not row.get("contact_name"):
        flags.append("no_name")
    return "|".join(flags)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def write_csv(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            # Flatten list-valued cells (e.g. page_numbers) to "4;5;6" for CSV.
            w.writerow({k: (";".join(map(str, v)) if isinstance(v, list) else v)
                        for k, v in row.items()})


def write_json(path, rows):
    """Write the structured cleaned export: one typed object per comment."""
    records = []
    for row in rows:
        records.append({
            "date": row.get("date", ""),
            "date_normalized": row.get("date_normalized", ""),
            "contact_name": row.get("contact_name", ""),
            "subject": row.get("subject", ""),
            "topic": row.get("topic", ""),
            "comment": row.get("comment", ""),
            "district": row.get("district", ""),
            "source": row.get("source", ""),
            "has_attachment": row.get("has_attachment") == "TRUE",
            "source_file": row.get("source_file", ""),
            "page_numbers": row.get("page_numbers", []),
            "period_start": row.get("period_start", ""),
            "period_end": row.get("period_end", ""),
            "quality_flags": [f for f in row.get("quality_flag", "").split("|") if f],
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def write_by_year(rows, columns):
    """Split rows into one CSV per year (by normalized date) under by_year/."""
    BY_YEAR_DIR.mkdir(exist_ok=True)
    by_year = {}
    for row in rows:
        year = row["date_normalized"][:4] or "undated"
        by_year.setdefault(year, []).append(row)
    for year in sorted(by_year):
        path = BY_YEAR_DIR / f"comments_{year}.csv"
        write_csv(path, by_year[year], columns)
        print(f"  {path.relative_to(BASE_DIR)}: {len(by_year[year])} rows")
    return by_year


def main():
    ap = argparse.ArgumentParser(description="Clean the extracted comments dataset")
    ap.add_argument("--report", action="store_true", help="Print a cleaning report")
    args = ap.parse_args()

    print("Loading raw JSON...")
    all_data = load_all_raw_json()
    print(f"  {len(all_data)} PDF result files")

    kept, dropped = flatten(all_data)
    print(f"Flattened: {len(kept)} comment-table rows, "
          f"{len(dropped)} non-comment rows routed out")

    print("Re-stitching continuations...")
    before = len(kept)
    kept, stats = restitch_continuations(kept)
    print(f"  {before} -> {len(kept)} rows "
          f"({stats['merged']} parts merged, {stats['orphans']} orphans flagged)")

    print("Dropping non-substantive comments...")
    before = len(kept)
    substantive = []
    nonsub_counts = Counter()
    for row in kept:
        reason = "voicemail" if is_voicemail(row) else non_substantive_reason(row.get("comment", ""))
        if reason:
            row["_drop_reason"] = reason
            nonsub_counts[reason] += 1
            dropped.append(row)
        else:
            substantive.append(row)
    kept = substantive
    print(f"  {before} -> {len(kept)} rows ({sum(nonsub_counts.values())} dropped: "
          f"{dict(nonsub_counts)})")

    print("Normalizing dates + flagging...")
    flag_counts = Counter()
    for row in kept:
        raw_date = row.get("date", "")

        # A source-type value (Email, Voicemail, ...) sometimes lands in the
        # date column. Move it to source if source is empty, and clear the date.
        if raw_date and not normalize_date(raw_date) and SOURCE_WORDS_RE.search(raw_date):
            if not row.get("source"):
                row["source"] = raw_date
            row["date"] = raw_date = ""

        iso = normalize_date(raw_date)
        if not iso:
            # Fall back to the meeting/period date from the filename.
            iso = filename_date(row["source_file"])
            if iso:
                row["_date_inferred"] = True
        row["date_normalized"] = iso
        row["period_start"], row["period_end"] = period_for(row["source_file"])
        row["quality_flag"] = quality_flags(row)
        for fl in row["quality_flag"].split("|"):
            if fl:
                flag_counts[fl] += 1

    # Drop exact duplicates: same person + same comment text + same date. These
    # come from overlapping file periods (a comment on the overlap day appears in
    # both files) and occasional in-file repeats. Keyed on date so a person who
    # resubmits the same comment to a later meeting is kept (it bins in its own
    # week), and mass form-letters (different names) are untouched.
    print("Deduplicating same-date duplicates...")
    before = len(kept)
    seen = set()
    deduped = []
    for row in kept:
        key = (row["contact_name"].strip().lower(), row["comment"].strip(),
               row["date_normalized"])
        if row["comment"].strip() and key in seen:
            row["_drop_reason"] = "duplicate"
            dropped.append(row)
            continue
        seen.add(key)
        deduped.append(row)
    kept = deduped
    print(f"  {before} -> {len(kept)} rows ({before - len(kept)} duplicates removed)")

    write_csv(OUTPUT_CSV, kept, OUTPUT_COLUMNS)
    write_json(OUTPUT_JSON, kept)
    write_csv(DROPPED_CSV, dropped, UNIFIED_COLUMNS + ["_drop_reason"])
    print(f"\nWrote {len(kept)} rows -> {OUTPUT_CSV.name}")
    print(f"Wrote {len(kept)} records -> {OUTPUT_JSON.name} (structured)")
    print(f"Wrote {len(dropped)} dropped rows -> {DROPPED_CSV.name} (audit trail)")
    print(f"Writing per-year CSVs -> {BY_YEAR_DIR.name}/")
    write_by_year(kept, OUTPUT_COLUMNS)

    if args.report:
        print("\n=== Cleaning report ===")
        print(f"Quality flags ({sum(flag_counts.values())} flagged rows):")
        for fl, n in flag_counts.most_common():
            print(f"  {fl:22s} {n:5d}")
        parsed = sum(1 for r in kept if r["date_normalized"])
        print(f"\nDates parsed to ISO: {parsed}/{len(kept)} "
              f"({parsed/len(kept)*100:.1f}%)")
        years = Counter(r["date_normalized"][:4] for r in kept if r["date_normalized"])
        print("Rows per normalized year:")
        for y, n in sorted(years.items()):
            print(f"  {y}: {n}")


if __name__ == "__main__":
    main()
