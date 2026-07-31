#!/usr/bin/env python3
"""classify_attachments.py — doc_class primary-document classifier for Riverton packets/index.csv.

PRIMARY_DOCS_ROLLOUT.md (Bucket A, classify-in-place) + SKILL.md Source 7 + the Sandy
reference (sandy_city_council/packets/classify_attachments.py, ADAPTED). Deterministic +
rerunnable: reads index.csv, classifies the staff_report+exhibit candidate pool into the
primary-document classes, and rewrites index.csv in place with the §9 columns
(doc_class, fetch_status, sha256, text_path, text_chars). Blank doc_class = honestly
unclassified — NEVER force-bucketed.

RIVERTON QUIRK (its packets/CLAUDE.md): `packet_kind` staff_report-vs-exhibit is a
FILENAME HEURISTIC over one-level flat Granicus /URI links, NOT structural — so BOTH
staff_report and exhibit rows are scanned together as one candidate pool. Riverton has
NO matter table; classification is title-token only (no db join). Land-use scoping for
staff_report is kept per the spec, though Riverton's entire "...Staff Report"/"...PC
Report"/"...CC Report" corpus is land-use in practice (0 of 521 hit the non-land-use
exclusion).

Classes (first match wins):
  member_memo           council-member proposal memos / amendment text (EMPTY for Riverton
                        2020-26 — the packet corpus carries staff/MOU/training/proclamation
                        memos only, no council-member proposal memos; honest empty class)
  staff_report          land-use staff/PC/CC reports (rezone / text & code amendment / ZTC /
                        subdivision / plat / CUP / site plan / GP amendment / DA staff report)
  plan_amendment        GP / land-use-map amendment substance exhibits (EMPTY for Riverton —
                        GP amendments here are either enacting ordinances, which live in
                        ordinances/, or "...Staff Report" docs, which classify as
                        staff_report; honest empty class)
  development_agreement DA / MDA instruments + their amendments/drafts (NOT staff reports
                        ABOUT a DA, NOT the enacting ordinance/resolution, NOT fee schedules)

Fetch/text columns (classify-in-place — text sidecars already exist on disk):
  fetch_status='ok'         classified + stored born-digital PDF with a text/ sidecar
  fetch_status='needs_ocr'  classified + stored but image-only (format=scanned, no sidecar)
  fetch_status=''  (blank)  classified but index-only (oversize-capped or 403 — no binary)
  sha256                    of the stored raw binary; falls back to the row's
                            raw/<date>/_fetch_log.jsonl entry; blank if neither exists
  text_path / text_chars    the text/ sidecar (dataset-relative) and its character count

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, re, sys, os, json, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")

# The candidate pool: staff_report + exhibit are ONE pool (packet_kind here is a filename
# heuristic, not structural — Riverton's CLAUDE.md caveat).
CANDIDATE_KINDS = ("staff_report", "exhibit")

# --- token regexes (all case-insensitive) ---------------------------------

# Explicit staff-analysis report token. Riverton labels its staff analysis
# "... Staff Report", "... PC Report", "... PC Staff Report", "... CC Report",
# "... CC Staff Report". Bare "Report" is NOT used (that catches Monthly Manager /
# Annual / YTD / Compliance / Title reports, which are not land-use staff analysis).
RE_STAFF_REPORT = re.compile(
    r"staff\s*report"                       # "Staff Report" / "PC Staff Report" / "CC Staff Report"
    r"|\bpc\s+(?:staff\s+)?report\d*\b"     # "PC Report" (+ "PC Report1" digit-suffix variant)
    r"|\bcc\s+(?:staff\s+)?report\d*\b",    # "CC Report"
    re.I)

# Non-land-use exclusion for staff_report (honors the spec's "a tax-rate report is not
# in-class"). In practice this removes 0 of Riverton's 521 explicit reports — its staff
# analysis is entirely planning/land-use; budget/finance items use "Issue Paper"/
# resolution titles, not "Staff Report". Kept as a guard for future refreshes.
RE_STAFF_NONLU = re.compile(
    r"\bbudget\b|financ|\baudit\b|personnel|salary|compensation|"
    r"property\s+tax|tax\s+increase|impact\s+fee\s+(?:schedule|analysis)", re.I)

# Council-member proposal memo (the Sharkey class). Riverton files none in its packet
# corpus (the only "memo" titles are staff/MOU/OPMA-training/proclamation), so this is
# an honest EMPTY class. Kept narrow to guarantee zero false positives.
RE_MEMBER_MEMO = re.compile(
    r"council\s*member\b[^.]*\b(?:memo(?:randum)?|proposal|amendment)\b"
    r"|\b(?:memo(?:randum)?|proposal)\b[^.]*\bcouncil\s*member\b", re.I)

# GP / land-use-map amendment SUBSTANCE exhibit (proposed map/element). Riverton's GP is a
# single land-use map; its GP-amendment docs are enacting ordinances (-> ordinances/) or
# "... Staff Report" (-> staff_report), so this is an honest EMPTY class. Detector kept
# for symmetry / future refreshes.
RE_PA_MATTER = re.compile(
    r"general\s+plan\s+amendment|land\s+use\s+map\s+amendment|future\s+land\s+use", re.I)
RE_PA_INCLUDE = re.compile(r"exhibit|proposed|\belement\b|\bmap\b|\bdraft\b", re.I)
RE_PA_EXCLUDE = re.compile(
    r"\bordinance\b|\bresolution\b|staff\s*report|\bpc\s+report\b|\bcc\s+report\b|"
    r"minutes|notice|presentation", re.I)

# Development-agreement INSTRUMENT (the agreement itself / its amendment / its draft),
# NOT a staff report about a DA, NOT the enacting ordinance/resolution, NOT a fee schedule.
RE_DA_INSTRUMENT = re.compile(r"(?:master\s+)?development\s+agreement|\bMDA\b", re.I)
RE_DA_NOT_INSTRUMENT = re.compile(
    r"report|staff|presentation|briefing|\bmemo\b|minutes|ecomment|"
    r"\bordinance\b|\bresolution\b|impact\s+fee|fee\s+schedule", re.I)

# Portal artifacts that are links, not documents.
RE_NEVER = re.compile(r"ecomment", re.I)


def classify(title: str) -> str:
    t = title or ""
    if RE_NEVER.search(t):
        return ""
    # 1. member_memo — council-member proposal memos (empty for Riverton)
    if RE_MEMBER_MEMO.search(t):
        return "member_memo"
    # 2. staff_report — land-use staff/PC/CC reports
    if RE_STAFF_REPORT.search(t) and not RE_STAFF_NONLU.search(t):
        return "staff_report"
    # 3. plan_amendment — GP / LU-map amendment substance exhibits (empty for Riverton)
    if RE_PA_MATTER.search(t) and RE_PA_INCLUDE.search(t) and not RE_PA_EXCLUDE.search(t):
        return "plan_amendment"
    # 4. development_agreement — the instrument itself
    if RE_DA_INSTRUMENT.search(t) and not RE_DA_NOT_INSTRUMENT.search(t):
        return "development_agreement"
    return ""


# --- fetch_status / sha256 / text_path helpers -----------------------------

_LOG_CACHE = {}


def sha256_from_log(raw_relpath: str, source_url: str) -> str:
    """Fall back to the row's raw/<date>/_fetch_log.jsonl entry for a sha256 (keyed by
    url or saved filename). Returns '' if the folder/log/entry is absent."""
    if not raw_relpath:
        return ""
    date_dir = os.path.dirname(os.path.join(HERE, raw_relpath))
    log = os.path.join(date_dir, "_fetch_log.jsonl")
    if log not in _LOG_CACHE:
        entries = []
        if os.path.exists(log):
            with open(log, errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        _LOG_CACHE[log] = entries
    base = os.path.basename(raw_relpath)
    for e in _LOG_CACHE[log]:
        if e.get("saved_as") == base or e.get("url") == source_url or e.get("final_url") == source_url:
            if e.get("sha256"):
                return e["sha256"]
    return ""


def sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_text(r: dict):
    """Return (fetch_status, text_path, text_chars, sha256) for a classified row."""
    raw_rel = r.get("path") or ""
    raw_abs = os.path.join(HERE, raw_rel) if raw_rel else ""
    stem = os.path.splitext(os.path.basename(raw_rel))[0] if raw_rel else ""
    sidecar_rel = os.path.join("text", stem + ".txt") if stem else ""
    sidecar_abs = os.path.join(HERE, sidecar_rel) if sidecar_rel else ""

    # sha256: prefer the stored binary, else the fetch log
    sha = ""
    if raw_abs and os.path.exists(raw_abs):
        sha = sha256_of_file(raw_abs)
    else:
        sha = sha256_from_log(raw_rel, r.get("source_url", ""))

    if sidecar_rel and os.path.exists(sidecar_abs):
        with open(sidecar_abs, errors="replace") as f:
            chars = len(f.read())
        return "ok", sidecar_rel, str(chars), sha
    # stored but image-only (format=scanned, no sidecar) -> needs OCR
    if r.get("stored") == "yes" and raw_abs and os.path.exists(raw_abs):
        return "needs_ocr", "", "", sha
    # classified but index-only (oversize-capped / 403) -> honest blank fetch_status
    return "", "", "", sha


NEW_COLS = ("doc_class", "fetch_status", "sha256", "text_path", "text_chars")


def main():
    dry = "--dry-run" in sys.argv
    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in NEW_COLS:
        if col not in fields:
            fields.append(col)

    counts = {}
    status = {}
    discard_preserved = 0
    for r in rows:
        for col in NEW_COLS:
            r.setdefault(col, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored='no' row that ALREADY carries a
        # populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; its §9 columns are maintained IN-FILE with no on-disk binary/sidecar to
        # re-derive from). PRESERVE it verbatim — resolve_text() below would blank its
        # text_path/text_chars (the absent raw fails os.path.exists, and stored!='yes' takes
        # the index-only branch) on every rerun. Guard runs BEFORE classification. Riverton's
        # 402 stored='no' rows today are all never-fetched index-only rows (blank text_path),
        # NOT discard rows, so this is dormant hardening; matches the defect CLASS fixed in
        # draper packets/link_text_sidecars.py "DISCARD-ROW SAFETY".
        if r.get("stored") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        if r["packet_kind"] not in CANDIDATE_KINDS:
            r["doc_class"] = ""
            r["fetch_status"] = ""
            continue
        cls = classify(r["title"])
        r["doc_class"] = cls
        if not cls:
            r["fetch_status"] = ""
            continue
        counts[cls] = counts.get(cls, 0) + 1
        fs, tp, tc, sha = resolve_text(r)
        r["fetch_status"], r["text_path"], r["text_chars"], r["sha256"] = fs, tp, tc, sha
        status[fs or "index_only"] = status.get(fs or "index_only", 0) + 1

    npool = sum(1 for r in rows if r["packet_kind"] in CANDIDATE_KINDS)
    nclass = sum(counts.values())
    print(f"candidate pool (staff_report+exhibit): {npool}  classified: {nclass}  "
          f"unclassified: {npool - nclass}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print("fetch_status of classified:")
    for k in sorted(status):
        print(f"  {k}: {status[k]}")
    print(f"§9 discard rows preserved verbatim: {discard_preserved}")
    if dry:
        print("(dry run — index.csv not written)")
        return
    tmp = INDEX + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, INDEX)
    print(f"wrote {INDEX} ({len(rows)} rows, {len(fields)} cols)")


if __name__ == "__main__":
    main()
