#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Copperton packets/index.csv.

PRIMARY_DOCS_ROLLOUT.md row 7 (Bucket A-lite, classify-in-place). Deterministic +
rerunnable: reads index.csv, classifies the in-scope rows into the four
attachment-borne primary-document classes, and rewrites index.csv in place with the
pilot extension columns `doc_class, fetch_status, text_path, text_chars` (the `sha256`
extension column already exists in Copperton's index and is preserved). Blank
doc_class = honestly unclassified — NEVER force-bucketed.

Copperton is a ~800-pop town with tiny land-use volume; small honest counts are CORRECT.

SCOPE: only `supporting_docs` + `staff_report` packet_kind rows are scanned. The
`full_packet`/`agenda_packet` containers are skipped (their whole-meeting text already
feeds fts_packet; none names an in-scope primary doc — verified). Text comes from the
existing `text/<stem>.txt` sidecars (pdftotext -layout); a classified office-doc
(.docx/.doc) without a sidecar gets one converted on demand via `textutil` (macOS) and
its extraction_method is updated — unclassified office-docs are NEVER bulk-converted.

Classes (first match wins):
  staff_report          land-use staff reports — the MSD "Planning Commission Staff
                        Report" / "REZONE SUMMARY AND RECOMMENDATION" / "Ordinance
                        Summary and Recommendation" template (Meeting/Public Body +
                        File #/OAM|REZ case key + Planner/Recommendation), scoped to a
                        land-use matter. Copperton 2019-2026: 6.
  member_memo           council-member proposal memos / amendment text. Copperton: 0 —
                        the ~4 councilmember/memo title hits are all administrative
                        (board-appointment resolutions, an interlocal redline, a park
                        proposal, a subdivision redline), none a member-authored memo.
  plan_amendment        GP / land-use-MAP amendment exhibits. Copperton: 0 — see the
                        Annexation Policy Plan boundary note below.
  development_agreement DA / MDA instruments. Copperton: 0 — the ~15 "agreement"/annex
                        title hits are all interlocal / franchise / annexation
                        instruments, none a private land-development agreement.

BOUNDARY DECISIONS (documented, not bugs):
  - The 2025-08-20 packet_kind=staff_report rows (UFA Q2 report, EOC training, Hazard
    Mitigation Plan annex) are OPERATIONAL reports, NOT land-use staff reports — blank.
    packet_kind=staff_report != doc_class=staff_report; the class is land-use scoped.
  - Draft Title 18/19 subdivision/zoning CODE-text amendments and the "Phase 1 Package"
    staff cover MEMO are land-use-adjacent but are code drafts / a staff memo not titled
    "staff report" — blank (Sandy precedent excludes non-"staff report" staff memos;
    enacted ordinances live in ordinances/). Their text still feeds fts_packet.
  - The DRAFT Copperton Annexation Policy Plan (2022) is a distinct STATUTORY land-use
    policy plan (Utah Code 10-2-401.5), NOT a general-plan amendment and NOT a
    land-use-map amendment exhibit — it is left BLANK to keep plan_amendment precise.
    Its text remains FTS-searchable via the full pdftotext sidecar layer.

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXTDIR = os.path.join(HERE, "text")

IN_SCOPE_KINDS = {"supporting_docs", "staff_report"}
EXT_COLS = ["doc_class", "fetch_status", "text_path", "text_chars"]

# --- title-level candidate test (staff_report only non-empty class) --------
RE_SR_TITLE = re.compile(r"staff[\s_]*report|summary\s+and\s+recommendation", re.I)
# --- land-use scope confirmed in the document TEXT -------------------------
RE_LANDUSE = re.compile(
    r"\b(OAM|REZ|CUP|VAR|RWD)\d*[-\s]?\d"          # MSD land-use case key
    r"|rezone|zoning|subdivision|land\s*use|title\s*1[89]|annex|general\s+plan"
    r"|parking\s+revis|\bplanner\b", re.I)
# --- MSD staff-report template markers in TEXT ----------------------------
RE_SR_TEMPLATE = re.compile(
    r"summary\s+and\s+recommendation|staff\s+recommend"
    r"|(?:meeting|public)\s+body\s*:|\bplanner\b\s*:?", re.I)

# member_memo: a council-member-authored proposal memo. Copperton council surnames
# (township + town eras). Kept for determinism/rerun; yields 0 for Copperton.
SURNAMES = (r"pazell|patrick|sorensen|olsen|severson|clayton|stitzer|bailey|"
            r"mccalmon|pratt")
RE_MEMBER_MEMO = re.compile(
    r"(?:" + SURNAMES + r")\b[^,\n]*\b(?:memo(?:randum)?|proposal)\b"
    r"|\b(?:memo(?:randum)?|proposal)\b[^,\n]*\b(?:" + SURNAMES + r")", re.I)
RE_MEMBER_EXCL = re.compile(r"resolution|appointing|redline|interlocal|park", re.I)

# plan_amendment: a GP / land-use-MAP amendment EXHIBIT (proposed element / Exhibit A).
# Excludes code amendments and the standalone annexation policy plan (boundary note).
RE_PA_INCLUDE = re.compile(
    r"(?:general\s+plan|land\s+use\s+map)[^\n]*\bamend", re.I)
RE_PA_EXCLUDE = re.compile(
    r"annexation\s+policy\s+plan|title\s*1[89]|code|notice|presentation|minutes", re.I)

# development_agreement: the instrument itself, not annexation/interlocal/franchise.
RE_DA_INSTRUMENT = re.compile(r"(?:master\s+)?development\s+agreement|\bMDA\b", re.I)
RE_DA_NOT = re.compile(r"annex|interlocal|franchise|presentation|memo|minutes|notice", re.I)


def sidecar_path(row_path):
    stem = os.path.splitext(os.path.basename(row_path))[0]
    return os.path.join(TEXTDIR, stem + ".txt")


def is_office_doc(row):
    return os.path.splitext(row["path"])[1].lower() in (".docx", ".doc")


def get_text(row):
    """Return the row's text WITHOUT writing anything. Reads the existing
    text/<stem>.txt sidecar if present; else, for an office-doc, converts via
    textutil in-memory (no file written). Empty string if neither works."""
    sc = sidecar_path(row["path"])
    if os.path.exists(sc):
        return open(sc, errors="replace").read()
    if is_office_doc(row):
        raw = os.path.join(HERE, row["path"])
        if os.path.exists(raw):
            try:
                return subprocess.run(
                    ["textutil", "-convert", "txt", "-stdout", raw],
                    capture_output=True, text=True, check=True).stdout or ""
            except Exception:
                return ""
    return ""


def ensure_sidecar(row, text):
    """For a CLASSIFIED office-doc with no sidecar, write the textutil sidecar so
    its text feeds fts_packet. Returns the dataset-relative sidecar path if one
    exists/was written, else ''. Never touches unclassified rows."""
    sc = sidecar_path(row["path"])
    rel = os.path.relpath(sc, HERE)
    if os.path.exists(sc):
        return rel
    if is_office_doc(row) and len((text or "").strip()) >= 200:
        os.makedirs(TEXTDIR, exist_ok=True)
        with open(sc, "w") as f:
            f.write(text)
        return rel
    return ""


def classify_staff_report(title, text):
    if not RE_SR_TITLE.search(title):
        return False
    head = text[:2500]
    return bool(RE_SR_TEMPLATE.search(head) and RE_LANDUSE.search(head))


def classify(row):
    """Return doc_class ('' = unclassified). staff_report needs a text confirm,
    so it is resolved in main() where text is loaded; here handle the empty classes."""
    t = row["title"] or ""
    if RE_MEMBER_MEMO.search(t) and not RE_MEMBER_EXCL.search(t):
        return "member_memo"
    if RE_PA_INCLUDE.search(t) and not RE_PA_EXCLUDE.search(t):
        return "plan_amendment"
    if RE_DA_INSTRUMENT.search(t) and not RE_DA_NOT.search(t):
        return "development_agreement"
    return ""


def main():
    dry = "--dry-run" in sys.argv
    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in EXT_COLS:
        if col not in fields:
            fields.append(col)

    counts, status = {}, {}
    discard_preserved = 0
    for r in rows:
        for col in EXT_COLS:
            r.setdefault(col, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored='no' row that ALREADY carries a
        # populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; its §9 columns are maintained IN-FILE with no on-disk binary/sidecar
        # to re-derive from). PRESERVE it verbatim — the reset below would blank its
        # doc_class/fetch_status/text_path/text_chars on every rerun. Guard runs BEFORE the
        # reset. Copperton has 0 such rows today (classify-in-place, no `stored` column —
        # every row retains its raw), so this is dormant hardening; matches the defect CLASS
        # fixed in draper packets/link_text_sidecars.py "DISCARD-ROW SAFETY".
        if r.get("stored") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        r["doc_class"] = ""
        r["fetch_status"] = ""
        r["text_path"] = ""
        r["text_chars"] = ""
        if r["packet_kind"] not in IN_SCOPE_KINDS:
            continue

        text = get_text(r)
        dc = classify(r)
        # staff_report — title candidate + land-use text confirm
        if not dc and RE_SR_TITLE.search(r["title"] or "") \
                and classify_staff_report(r["title"], text):
            dc = "staff_report"
        if not dc:
            continue

        r["doc_class"] = dc
        counts[dc] = counts.get(dc, 0) + 1
        # populate the text layer for the classified row (side effects only here)
        if r["format"] == "scanned":
            r["fetch_status"] = "needs_ocr"
        elif len(text.strip()) >= 200:
            rel = ensure_sidecar(r, text) if not dry else \
                os.path.relpath(sidecar_path(r["path"]), HERE)
            if is_office_doc(r) and rel:
                r["extraction_method"] = "textutil (docx->txt)"
            r["fetch_status"] = "ok"
            r["text_path"] = rel
            r["text_chars"] = str(len(text))
        else:
            r["fetch_status"] = "needs_ocr"
        status[r["fetch_status"]] = status.get(r["fetch_status"], 0) + 1

    nscope = sum(1 for r in rows if r["packet_kind"] in IN_SCOPE_KINDS)
    nclass = sum(counts.values())
    print(f"in-scope rows: {nscope}  classified: {nclass}  unclassified: {nscope - nclass}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print("fetch_status:", dict(sorted(status.items())))
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
