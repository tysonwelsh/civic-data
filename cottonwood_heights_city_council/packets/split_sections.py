#!/usr/bin/env python3
"""
split_sections.py — Cottonwood Heights Bucket-B packet SECTION splitter (Source 7,
primary-documents rollout). DETERMINISTIC + rerunnable.

WHAT IT DOES
------------
The 12 CH *council* work-session packets from 2025-08-19 through 2026-02-17 carry an
explicit machine-readable appendix manifest:

    Appendix 3 - Staff Report/Planning Department Land Use Amendment and Rezone at 3425 E.
    Appendix 4 - Staff Report/Employee Handbook Training ...
    ...

followed, later in the SAME sidecar, by indented body "divider" cover-pages:

               Appendix 3
             STAFF REPORT
    <the staff report text>
    ...
        Appendix 4          <- next section starts here

This script parses the TOC, locates each appendix's body divider, and cuts the text of
each IN-SCOPE (land-use) appendix into text/sections/<stem>__appx<N>_<slug>.txt, adding
one additive index row per cut (packet_kind='packet_section'). The parent full_packet
rows and their raw PDFs are NEVER modified.

SCOPE / SEPARABILITY (see packets/CLAUDE.md + AVAILABILITY.md):
  * ONLY the 12 TOC-era council packets are section-cut (high-confidence manifest).
  * PC packets (32) and the 8 newer agenda-outline council packets (2026-03+) have NO
    appendix manifest -> NOT section-cut (their full-packet sidecar already serves FTS).
  * Within a TOC packet, only appendices carrying a positive LAND-USE signal are cut
    (doc_class in staff_report / plan_amendment / general_plan / development_agreement).
    Non-land-use work-session memos (personnel, tax, curfew, events, Action Items) are
    left UNCUT (blank doc_class = honestly unclassified, never force-bucketed).
  * A TOC appendix with NO matching body divider is SKIPPED (boundary unlocatable) and
    logged. (Known: 10625 Appendix 6, 10845 Appendix 3.)

USAGE
  python3 split_sections.py            # DRY-RUN (read-only): prints the cut plan + census
  python3 split_sections.py --write    # emit section text files + append index rows

This file is the ONLY artifact created in Phase 1. --write is Phase 2 (orchestrator-gated).
"""
import csv, os, re, sys, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
TEXT = os.path.join(HERE, "text")
SECT = os.path.join(TEXT, "sections")
INDEX = os.path.join(HERE, "index.csv")

# ---- the exact existing §9 contract header + CH extras, then the additive columns ----
BASE_COLS = ["date", "title", "body", "meeting_type", "packet_kind", "source_url",
             "retrieved_date", "format", "extraction_method", "path",
             "size_mb", "stored_locally", "docid"]
NEW_COLS = ["doc_class", "fetch_status", "sha256", "text_path", "text_chars",
            "parent_path", "appendix_no", "case_key"]
ALL_COLS = BASE_COLS + NEW_COLS

THIN_FLOOR = 200          # chars; below this a section is a presentation/image placeholder
CASE_RE = re.compile(r'\b(?:Z[MT]A|CUP|SUB|OAM|PLNPCM)-\d{2}-\d{2,}\b')

# TOC line, tolerant of OCR "I"->1, hyphen/en-dash/em-dash, missing space after num:
TOC_RE  = re.compile(r'^Appendix\s+([0-9IlO]+)\s*[-–—]\s*(.*)$')
# body divider: indented line that is ONLY "Appendix N" (no trailing " - title"):
DIV_RE  = re.compile(r'^\s+Appendix\s+([0-9IlO]+)\s*$')

LANDUSE_KW = [
    "rezone", "land use", "land-use", "zoning", "zone change", "subdivision", "plat",
    "annex", "site plan", "accessory", "pergola", "gazebo", "chicken", "coop",
    "general plan", "water element", "wui", "wildland", "canyon", "road access",
    "street segment", "udot", "setback", "density", "dwelling", "adu", "old mill",
    "conditional use", "development agreement", "master development", "overlay",
]
# titles that are explicitly OUT even if a keyword grazes them:
EXCLUDE_KW = ["action items", "employee handbook", "flash vote", "curfew",
              "telecom tax", "fraud risk", "butlerville", "interfaith",
              "committee assignments", "employee appeals", "arts district",
              "bike safety", "renewable communities", "blue sky", "pet licensing",
              "emergency management", "city hall hours", "legislative priorities"]


def norm_num(s):
    return s.replace("I", "1").replace("l", "1").replace("O", "0")


def classify(title, body_text):
    """Return (doc_class, case_key) or (None, '') if out of scope."""
    t = title.lower()
    if any(k in t for k in EXCLUDE_KW):
        # still allow if a hard land-use case key is in the body (rare)
        if not CASE_RE.search(body_text):
            return None, ""
    ck = ""
    m = CASE_RE.search(body_text) or CASE_RE.search(title)
    if m:
        ck = m.group(0)
    hit = any(k in t for k in LANDUSE_KW) or bool(ck)
    if not hit:
        return None, ""
    if "development agreement" in t or "master development" in t:
        return "development_agreement", ck
    # a draft GP element exhibit embedded in the section -> general_plan/plan_amendment
    if "general plan" in t and re.search(r'DRAFT[^\n]{0,40}ELEMENT', body_text):
        return "general_plan", ck
    return "staff_report", ck


def slugify(s):
    s = re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')
    return s[:50] or "section"


def load_index():
    with open(INDEX, newline='') as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def parse_packet(row):
    """Return list of planned cuts for one council packet row, plus skip notes."""
    stem = os.path.splitext(os.path.basename(row["path"]))[0]
    tpath = os.path.join(TEXT, stem + ".txt")
    if not os.path.exists(tpath):
        return [], [f"{stem}: no sidecar"]
    lines = open(tpath, encoding='utf-8', errors='replace').read().split("\n")

    # 1) parse TOC titles (first contiguous block of "Appendix N - title")
    toc = {}          # num(int) -> title (verbatim, single line)
    for ln in lines:
        m = TOC_RE.match(ln)
        if m:
            n = int(norm_num(m.group(1)))
            if n not in toc:
                toc[n] = ln.rstrip()
    if not toc:
        return [], [f"{stem}: no appendix TOC"]

    # 2) find body dividers (indented "Appendix N", after the TOC region)
    divs = []         # (num, line_idx)
    for i, ln in enumerate(lines):
        m = DIV_RE.match(ln)
        if m:
            divs.append((int(norm_num(m.group(1))), i))
    # keep only the FIRST divider occurrence per number (the cover page)
    seen = {}
    for n, i in divs:
        if n not in seen:
            seen[n] = i
    # ordered divider list by line position
    ordered = sorted(seen.items(), key=lambda kv: kv[1])   # [(num, idx), ...]

    # Top-level "Attachment N" ordinance cover-pages start AFTER the last appendix.
    # NOTE: an appendix's OWN exhibits can also print "Attachment N" cover-pages
    # nested inside it (e.g. 10491's WUI report bundles HB48 / Draft Ordinance / WUI
    # Map as Attachment 1/2/3). Those are section CONTENT, not boundaries — so a
    # section is terminated by the next APPENDIX divider, and only the FINAL appendix
    # falls through to the first Attachment divider (the top-level ordinance zone).
    att = [i for i, ln in enumerate(lines)
           if re.match(r'^\s+Attachment\s+[0-9IlO]+\s*$', ln)]

    cuts, skips = [], []
    div_idx_by_num = dict(ordered)
    appx_positions = sorted(i for (_, i) in ordered)
    for num, title in sorted(toc.items()):
        if num in (1, 2):
            continue                      # Agendas / Minutes — never in scope
        if num not in div_idx_by_num:
            skips.append(f"{stem} Appendix {num}: TOC present but NO body divider -> skip")
            continue
        start = div_idx_by_num[num]
        appx_after = [i for i in appx_positions if i > start]
        if appx_after:
            end = appx_after[0]           # next appendix divider terminates the section
        else:                             # final appendix -> top-level attachment zone / EOF
            att_after = [i for i in att if i > start]
            end = min(att_after) if att_after else len(lines)
        body = "\n".join(lines[start:end])
        dc, ck = classify(title, body)
        if dc is None:
            continue                      # out of scope: leave uncut, blank doc_class
        text_chars = len(body.strip())
        # sub-floor sections are image-only staff reports (no usable text layer);
        # use the CLOSED §9 vocabulary value 'needs_ocr' (fetched/located, no text),
        # never a new status token. No sidecar is written for these.
        status = "ok" if text_chars >= THIN_FLOOR else "needs_ocr"
        cuts.append(dict(num=num, title=title, start=start, end=end,
                         doc_class=dc, case_key=ck, text=body,
                         text_chars=text_chars, fetch_status=status, stem=stem))
    return cuts, skips


def main():
    write = "--write" in sys.argv
    _, rows = load_index()
    # only the stored full_packet council containers are section-cut (never re-cut
    # our own packet_section rows — keeps --write idempotent)
    council = [r for r in rows
               if r["body"] == "Council" and r["packet_kind"] == "full_packet"]

    all_cuts, all_skips = [], []
    for r in council:
        cuts, skips = parse_packet(r)
        for c in cuts:
            c["row"] = r
        all_cuts += cuts
        all_skips += skips

    # census
    by_class = {}
    thin = 0
    for c in all_cuts:
        by_class[c["doc_class"]] = by_class.get(c["doc_class"], 0) + 1
        if c["fetch_status"] != "ok":
            thin += 1
    print(f"[{'WRITE' if write else 'DRY-RUN'}] council packets scanned: {len(council)}")
    print(f"planned section cuts: {len(all_cuts)}  (thin/<{THIN_FLOOR}c: {thin})")
    for k in sorted(by_class):
        print(f"  doc_class={k}: {by_class[k]}")
    print(f"skipped appendices (TOC/body disagree or unlocatable): {len(all_skips)}")
    for s in all_skips:
        print("   " + s)
    if not write:
        print("\nPer-cut plan:")
        for c in all_cuts:
            print(f"  {c['stem']} A{c['num']} [{c['doc_class']}"
                  f"{'/'+c['case_key'] if c['case_key'] else ''}] "
                  f"{c['text_chars']}c :: {c['title'][:70]}")
        print("\n(dry-run: no files written, index untouched)")
        return

    # ---- WRITE MODE (Phase 2 only) ----
    os.makedirs(SECT, exist_ok=True)
    new_rows = []
    for c in all_cuts:
        r = c["row"]
        fname = f"{c['stem']}__appx{c['num']:02d}_{slugify(c['title'].split('/')[-1])}.txt"
        rel = f"text/sections/{fname}"
        if c["fetch_status"] == "ok":
            with open(os.path.join(SECT, fname), "w", encoding='utf-8') as f:
                f.write(c["text"])
            tp = rel
        else:
            tp = ""            # thin: no sidecar, honest flag only
        new_rows.append({
            "date": r["date"], "title": c["title"], "body": r["body"],
            "meeting_type": r["meeting_type"], "packet_kind": "packet_section",
            "source_url": r["source_url"], "retrieved_date": r["retrieved_date"],
            "format": "text", "extraction_method": "pdftotext-layout",
            "path": "", "size_mb": "", "stored_locally": "no",
            "docid": r["docid"], "doc_class": c["doc_class"],
            "fetch_status": c["fetch_status"], "sha256": "", "text_path": tp,
            "text_chars": c["text_chars"], "parent_path": r["path"],
            "appendix_no": c["num"], "case_key": c["case_key"],
        })

    # rewrite index.csv with the widened header; existing rows get blank new cols.
    # Drop any prior packet_section rows first so re-running --write regenerates
    # them rather than duplicating (idempotent).
    _, existing = load_index()
    existing = [r for r in existing if r.get("packet_kind") != "packet_section"]
    with open(INDEX, "w", newline='') as f:
        w = csv.DictWriter(f, fieldnames=ALL_COLS, extrasaction="ignore")
        w.writeheader()
        for r in existing:
            for k in NEW_COLS:
                r.setdefault(k, "")
            w.writerow(r)
        for r in new_rows:
            w.writerow(r)
    print(f"WROTE {len(new_rows)} section rows + {sum(1 for c in all_cuts if c['fetch_status']=='ok')} text files")


if __name__ == "__main__":
    main()
