#!/usr/bin/env python3
"""
Assemble public_comments/all_comments_clean.csv (SLC schema) for St. George, UT
from two sources:
  1. written_published  — per-PDF JSON in comments_json/<basename>.json
     (produced by reading the city's "Public Comments Received" PDFs)
  2. in_person_minutes  — comments_json/_in_person_minutes.json
     (produced by extract_comments.py from the Regular-meeting minutes)

Outputs:
  all_comments_clean.csv     — cleaned, deduped rows
  all_comments_dropped.csv   — every removed row + _drop_reason

Schema (identical to SLC):
  date,contact_name,subject,topic,comment,district,source,has_attachment,
  source_file,page_numbers,period_start,period_end,date_normalized,quality_flag
"""
import os, json, glob, csv, re, datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the st_george_city_council repo root
JDIR = os.path.join(REPO, "public_comments", "comments_json")
OUT_CLEAN = os.path.join(REPO, "public_comments", "all_comments_clean.csv")
OUT_DROP = os.path.join(REPO, "public_comments", "all_comments_dropped.csv")

COLUMNS = ["date", "contact_name", "subject", "topic", "comment", "district",
           "source", "has_attachment", "source_file", "page_numbers",
           "period_start", "period_end", "date_normalized", "quality_flag"]

SHORT_LEN = 40  # comments shorter than this flagged short_comment

# names that indicate a non-public (staff) author -> drop
STAFF_NAME = re.compile(r'\b(City Recorder|City Manager|City Attorney|City of St)\b', re.I)


def norm_date(s, fallback):
    """Return ISO date. s may be a raw date string or already ISO; fall back to window end."""
    if s and re.match(r'^\d{4}-\d{2}-\d{2}$', s.strip()):
        return s.strip(), False
    if s:
        # try a few formats
        for fmt in ("%a, %b %d, %Y", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%m/%d/%y"):
            try:
                d = datetime.datetime.strptime(re.sub(r'\s+at.*$', '', s).strip(), fmt)
                return d.strftime("%Y-%m-%d"), False
            except ValueError:
                continue
    return (fallback, True) if fallback else ("", True)


def clean_comment(c):
    if not c:
        return ""
    c = c.replace("\r\n", "\n")
    # common OCR / forwarding artifacts
    c = re.sub(r'sgcity\.\s+org', 'sgcity.org', c)
    c = re.sub(r'public-?comments?@sgcity\.\s*org', '', c)
    c = re.sub(r'noreply@jotform\.\s*com', '', c)
    # collapse >2 blank lines
    c = re.sub(r'\n{3,}', '\n\n', c).strip()
    return c


def gist(c):
    w = re.sub(r'[^a-z0-9 ]', '', (c or '').lower())
    return ' '.join(w.split()[:12])


def load_written():
    rows = []
    dropped = []
    for jf in sorted(glob.glob(os.path.join(JDIR, "*.json"))):
        if os.path.basename(jf).startswith("_"):
            continue
        d = json.load(open(jf))
        src = d.get("source_file", "")
        ps = d.get("period_start", "") or ""
        pe = d.get("period_end", "") or ""
        for c in d.get("comments", []):
            comment = clean_comment(c.get("comment", ""))
            name = (c.get("contact_name") or "").strip()
            dn, from_fn = norm_date(c.get("date_normalized") or c.get("date") or "", pe)
            flags = []
            if from_fn:
                flags.append("date_from_filename")
            if not name:
                flags.append("no_name")
            if len(comment) < SHORT_LEN:
                flags.append("short_comment")
            rows.append({
                "date": dn, "contact_name": name,
                "subject": (c.get("subject") or "").strip(),
                "topic": (c.get("topic") or "").strip(),
                "comment": comment, "district": "",
                "source": "written_published",
                "has_attachment": bool(c.get("has_attachment")),
                "source_file": src,
                "page_numbers": (c.get("pages") or "").strip(),
                "period_start": ps, "period_end": pe,
                "date_normalized": dn,
                "quality_flag": "|".join(flags),
            })
        for dr in d.get("dropped", []):
            dropped.append({
                "date": "", "contact_name": "", "subject": "", "topic": "",
                "comment": dr.get("note", ""), "district": "",
                "source": "written_published", "has_attachment": "",
                "source_file": src, "page_numbers": dr.get("pages", ""),
                "period_start": ps, "period_end": pe, "date_normalized": "",
                "quality_flag": "", "_drop_reason": dr.get("reason", "dropped"),
            })
    return rows, dropped


def load_in_person():
    rows = []
    jf = os.path.join(JDIR, "_in_person_minutes.json")
    if not os.path.exists(jf):
        return rows
    d = json.load(open(jf))
    for c in d.get("comments", []):
        name = (c.get("contact_name") or "").strip()
        topic = (c.get("topic") or "").strip()
        comment = (c.get("comment") or "").strip()
        dn = c.get("date_normalized") or ""
        flags = ["minutes_pointer_no_text"] if c.get("_minutes_pointer_no_text") else []
        if not name:
            flags.append("no_name")
        if len(comment) < SHORT_LEN:
            flags.append("short_comment")
        rows.append({
            "date": dn, "contact_name": name,
            "subject": (c.get("subject") or "").strip(),
            "topic": topic, "comment": comment, "district": "",
            "source": "in_person_minutes", "has_attachment": False,
            "source_file": c.get("source_file", ""), "page_numbers": "",
            "period_start": "", "period_end": "", "date_normalized": dn,
            "quality_flag": "|".join(flags),
        })
    return rows


def main():
    written, dropped = load_written()
    inperson = load_in_person()

    # ---- drop staff-authored / empty written rows ----
    keep = []
    for r in written:
        if not r["comment"]:
            r2 = dict(r); r2["_drop_reason"] = "empty_comment"; dropped.append(r2); continue
        if STAFF_NAME.search(r["contact_name"]):
            r2 = dict(r); r2["_drop_reason"] = "staff_author"; dropped.append(r2); continue
        keep.append(r)
    written = keep

    # ---- dedup WITHIN written (same name+date+gist from overlapping windows) ----
    seen = {}
    dedup_w = []
    for r in written:
        key = (r["contact_name"].lower(), r["date_normalized"], gist(r["comment"]))
        if key in seen and r["contact_name"]:
            r2 = dict(r); r2["_drop_reason"] = "dup_within_written"; dropped.append(r2); continue
        seen[key] = True
        dedup_w.append(r)
    written = dedup_w

    # ---- dedup ACROSS sources: in-person row whose (name+date) matches a written
    #      row (same gist/topic) -> drop the in-person pointer, keep written full text ----
    written_keys = {}
    for r in written:
        written_keys.setdefault((r["contact_name"].lower(), r["date_normalized"]), []).append(r)
    inperson_keep = []
    dedup_removed = 0
    for r in inperson:
        cand = written_keys.get((r["contact_name"].lower(), r["date_normalized"]))
        if cand:
            r2 = dict(r); r2["_drop_reason"] = "dup_in_person_has_written"
            dropped.append(r2); dedup_removed += 1; continue
        inperson_keep.append(r)
    inperson = inperson_keep

    all_rows = written + inperson
    # stable sort by date
    all_rows.sort(key=lambda r: (r["date_normalized"] or "9999", r["source"], r["contact_name"]))

    with open(OUT_CLEAN, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in all_rows:
            r["has_attachment"] = "true" if r["has_attachment"] else "false"
            w.writerow(r)

    with open(OUT_DROP, "w", newline="") as f:
        cols = COLUMNS + ["_drop_reason"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in dropped:
            if isinstance(r.get("has_attachment"), bool):
                r["has_attachment"] = "true" if r["has_attachment"] else "false"
            w.writerow(r)

    # ---- stats ----
    import collections
    by_year = collections.Counter(r["date_normalized"][:4] for r in all_rows if r["date_normalized"])
    by_source = collections.Counter(r["source"] for r in all_rows)
    print("clean rows:", len(all_rows))
    print("  written_published:", by_source.get("written_published", 0))
    print("  in_person_minutes:", by_source.get("in_person_minutes", 0))
    print("  by year:", dict(sorted(by_year.items())))
    print("dropped rows:", len(dropped))
    print("dedup across-source removed:", dedup_removed)
    return all_rows, dropped, dedup_removed


if __name__ == "__main__":
    main()
