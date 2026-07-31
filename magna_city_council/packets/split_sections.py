#!/usr/bin/env python3
"""split_sections.py — deterministic MSD staff-report section splitter for Magna packets.

PHASE-1 DESIGN ARTIFACT (PRIMARY_DOCS_ROLLOUT, magna row 11, Bucket-B SEPARABLE).

Magna's PMN packet PDFs (and the township-era PMN council packets) bundle one MSD
"Summary and Recommendation" staff report per land-use agenda item, each rendered from
the same Greater-Salt-Lake-MSD template. Every staff-report block opens with the same
metadata cluster:

    Planning and Development Services         <- MSD address boilerplate (page header)
    2001 S. State Street N3-600 ...
    ... msd.utah.gov
    File(s) # <CASE>                          <- REZ/SUB/OAM/CUP/VAR/RWD<YYYY>-<NNNNNN>
                                                 (or bare 'File # NNNNN' in the 2018-19 era)
    <Type> Summary and Recommendation         <- section heading (Rezone/Subdivision/CUP/...)
    Public Body: Magna ... [Council|Planning] <- THE ANCHOR (confirmed by a nearby
    Meeting Date: <date>                          Planner:/Recommendation:/Meeting Date:)
    Parcel ID: ...  Current Zone: ...
    Property Address: ...
    Planner: ...
    Planning Staff Recommendation: ...
    Applicant Name: ...
    PROJECT DESCRIPTION ...

A section spans from its header cluster to the START of the next section's header
cluster (or EOF), so the maps/plats/exhibits that trail a staff report ride with it.

Each cut becomes ONE ADDITIVE index row (packet_kind='packet_section', doc_class=
'staff_report') pointing at a new sidecar under text/sections/<parent_stem>__<seq>_<case>.txt;
the parent full_packet row is left untouched.

USAGE:
    python3 split_sections.py                 # dry-run census: sections per file, totals
    python3 split_sections.py --sample STEM   # verbatim boundary dump for one packet
    python3 split_sections.py --write         # (PHASE 2 ONLY — writes sidecars + rows.csv)

Phase 1: run only the default / --sample modes. --write is a stub that refuses to run
until the orchestrator authorizes Phase 2.
"""
import csv, re, os, sys, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXTDIR = os.path.join(HERE, "text")

# --- anchor / boundary regexes -------------------------------------------------
RE_ANCHOR  = re.compile(r'(?:Public Body|Meeting Body)\s*:\s*Magna', re.I)
RE_CONFIRM = re.compile(r'(Planner\s*:|Planning Staff Recommendation\s*:|'
                        r'Staff Recommendation\s*:|Meeting Date\s*:)', re.I)
RE_FILENO  = re.compile(r'^\s*Files?\s*#', re.I)
RE_HEAD    = re.compile(r'Summary(?:\s+and\s+Recommendation)?\s*$', re.I)
RE_MSDADDR = re.compile(r'Planning and Development Services\s*$', re.I)
RE_CASE    = re.compile(r'\b(REZ|SUB|OAM|CUP|VAR|RWD)\s?(\d{4})[- ]?(\d{6})\b')
RE_BAREFILE= re.compile(r'\bFiles?\s*#\s*(\d{4,6})\b')

MIN_ANCHOR_GAP = 5   # dedup two-column duplicate anchor lines
BACKUP_LINES   = 16  # how far above an anchor to hunt for the header cluster


def stem_of(row):
    return os.path.splitext(os.path.basename(row["path"]))[0]


def load_rows():
    with open(INDEX, newline="") as f:
        return list(csv.DictReader(f))


def find_anchors(lines):
    """Return deduped, confirmed anchor line indices."""
    out, last = [], -999
    for i, l in enumerate(lines):
        if RE_ANCHOR.search(l):
            window = "\n".join(lines[i:i + 14])
            if RE_CONFIRM.search(window) and (i - last) > MIN_ANCHOR_GAP:
                out.append(i)
                last = i
    return out


def section_start(lines, anchor, floor):
    """Line where the section header cluster begins (>= floor, < anchor).

    Preference order, scanning the window [max(floor,anchor-BACKUP_LINES), anchor):
      1. the MSD address boilerplate line ('Planning and Development Services'),
      2. else the earliest 'File(s) #' line,
      3. else the earliest '<Type> Summary...' heading line,
      4. else the anchor line itself.
    """
    lo = max(floor, anchor - BACKUP_LINES)
    win = range(lo, anchor)
    addr = [j for j in win if RE_MSDADDR.search(lines[j])]
    if addr:
        return addr[-1]                       # nearest address block above anchor
    files = [j for j in win if RE_FILENO.search(lines[j])]
    if files:
        return files[0]
    heads = [j for j in win if RE_HEAD.search(lines[j])]
    if heads:
        return heads[0]
    return anchor


def case_key(lines, start, anchor):
    """Best case key for naming: first REZ/SUB/... token in the header cluster,
    else a bare 'File # NNNNN', else ''."""
    blob = "\n".join(lines[start:anchor + 8])
    m = RE_CASE.search(blob)
    if m:
        return f"{m.group(1)}{m.group(2)}-{m.group(3)}"
    m = RE_BAREFILE.search(blob)
    if m:
        return f"FILE{m.group(1)}"
    return ""


def split_file(lines):
    """Return list of dicts: {seq, start, end, anchor, case}. end is exclusive."""
    anchors = find_anchors(lines)
    if not anchors:
        return []
    starts, floor = [], 0
    for a in anchors:
        s = section_start(lines, a, floor)
        starts.append((s, a))
        floor = a + 1
    secs = []
    for k, (s, a) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        secs.append({"seq": k + 1, "start": s, "end": end, "anchor": a,
                     "case": case_key(lines, s, a)})
    return secs


def read_lines(row):
    tp = os.path.join(TEXTDIR, stem_of(row) + ".txt")
    if not os.path.exists(tp):
        return None
    return open(tp, encoding="utf-8", errors="replace").read().split("\n")


# --- modes ---------------------------------------------------------------------
def mode_census(rows):
    from collections import Counter
    by_body, files_by_body, total = Counter(), Counter(), 0
    per_year = Counter()
    zero_scope = []
    for r in rows:
        lines = read_lines(r)
        if lines is None:
            continue
        secs = split_file(lines)
        if secs:
            by_body[r["body"]] += len(secs)
            files_by_body[r["body"]] += 1
            total += len(secs)
            per_year[r["date"][:4]] += len(secs)
        else:
            zero_scope.append(r)
    print("TOTAL staff-report sections:", total)
    print("  by body:", dict(by_body))
    print("  files with >=1 section by body:", dict(files_by_body))
    print("  sections by year:", dict(sorted(per_year.items())))
    print("  files with ZERO in-scope sections:", len(zero_scope))


def mode_sample(rows, stem):
    row = next((r for r in rows if stem_of(r) == stem), None)
    if not row:
        print("no such stem:", stem); return
    lines = read_lines(row)
    secs = split_file(lines)
    print(f"### {row['date']} {row['body']} {row['source']} {stem} "
          f"({row['size_mb']} MB) -> {len(secs)} section(s)")
    for s in secs:
        st, en, a = s["start"], s["end"], s["anchor"]
        body_first = [lines[st + k] for k in range(0, min(6, en - st))]
        body_first = [x for x in body_first if x.strip()][:3]
        tail = [lines[j] for j in range(st, en) if lines[j].strip()][-3:]
        after = [lines[en + k] for k in range(0, 6) if en + k < len(lines)]
        after = [x for x in after if x.strip()][:2]
        print(f"\n-- SECTION {s['seq']}  case={s['case'] or '(none)'}  "
              f"lines[{st}:{en}]  anchor L{a}: {lines[a].strip()[:60]!r}")
        print("   FIRST 3:")
        for x in body_first: print("     |", x.strip()[:88])
        print("   LAST 3:")
        for x in tail: print("     |", x.strip()[:88])
        print("   NEXT (first 2 after section):")
        for x in after: print("     >", x.strip()[:88])


# --- Phase-2 write scheme (orchestrator-reconciled 2026-07-16) --------------------
NEW_COLS = ["doc_class", "fetch_status", "sha256", "text_path", "text_chars",
            "parent_path", "section_seq", "case_key"]
SECTIONS_DIR = os.path.join(TEXTDIR, "sections")


def section_title(lines, start, anchor, case):
    heads = [lines[j].strip() for j in range(start, min(anchor + 2, len(lines)))
             if RE_HEAD.search(lines[j]) and not RE_ANCHOR.search(lines[j])]
    head = heads[0] if heads else ""
    if case and head:
        return f"{case} — {head}"
    if case:
        return f"{case} — staff report"
    if head:
        return head
    return "Staff report (unkeyed section)"


def mode_write(rows):
    fieldnames = list(rows[0].keys())
    for c in NEW_COLS:
        if c not in fieldnames:
            fieldnames.append(c)

    # idempotent reset: drop any prior packet_section rows + wipe text/sections/
    parents = [r for r in rows if r.get("packet_kind") != "packet_section"]
    if os.path.isdir(SECTIONS_DIR):
        for f in os.listdir(SECTIONS_DIR):
            if f.endswith(".txt"):
                os.remove(os.path.join(SECTIONS_DIR, f))
    os.makedirs(SECTIONS_DIR, exist_ok=True)

    section_rows, n_files, total_chars = [], 0, 0
    for r in parents:
        lines = read_lines(r)
        if lines is None:
            continue
        secs = split_file(lines)
        if not secs:
            continue
        n_files += 1
        pstem = stem_of(r)
        for s in secs:
            text = "\n".join(lines[s["start"]:s["end"]])
            total_chars += len(text)
            suffix = f"__{s['seq']:02d}" + (f"_{s['case']}" if s["case"] else "")
            fname = f"{pstem}{suffix}.txt"
            with open(os.path.join(SECTIONS_DIR, fname), "w", encoding="utf-8") as f:
                f.write(text)
            row = {k: "" for k in fieldnames}
            # inherit parent context
            row.update({
                "date": r["date"], "body": r["body"],
                "meeting_type": r.get("meeting_type", ""),
                "source_url": r["source_url"],
                "retrieved_date": r.get("retrieved_date", ""),
                "source": r.get("source", ""),
                "pmn_notice_id": r.get("pmn_notice_id", ""),
                "pmn_filename": r.get("pmn_filename", ""),
                "path": r["path"],            # binary lives in the parent PDF (exists on disk)
            })
            row.update({
                "title": section_title(lines, s["start"], s["anchor"], s["case"]),
                "packet_kind": "packet_section",
                "format": "text",
                "extraction_method": "section_split",
                "content_length_bytes": "", "size_mb": "",
                "stored_locally": "no",       # describes the binary (no standalone binary)
                "doc_class": "staff_report",
                "fetch_status": "ok",
                "sha256": "",                 # BLANK — §9: sha256 = binary hash; slice has none
                "text_path": f"text/sections/{fname}",
                "text_chars": str(len(text)),
                "parent_path": r["path"],
                "section_seq": str(s["seq"]),
                "case_key": s["case"],
            })
            section_rows.append(row)

    out = parents + section_rows
    with open(INDEX, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "") for k in fieldnames})

    print(f"WROTE {len(section_rows)} packet_section rows from {n_files} parent packets")
    print(f"  total section chars: {total_chars:,}")
    print(f"  index.csv now: {len(out)} data rows ({len(parents)} parents + "
          f"{len(section_rows)} sections)")


if __name__ == "__main__":
    rows = load_rows()
    if "--write" in sys.argv:
        mode_write(rows)
    elif "--sample" in sys.argv:
        mode_sample(rows, sys.argv[sys.argv.index("--sample") + 1])
    else:
        mode_census(rows)
