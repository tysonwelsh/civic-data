#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Emigration Canyon packets/index.csv.

PRIMARY_DOCS_ROLLOUT.md (row 6, Bucket A-lite) / SKILL.md Source 7. Deterministic +
rerunnable: reads index.csv and the on-disk `text/<stem>.txt` sidecars (NO network, NO
db, NO LLM), assigns a doc_class to the in-scope attachment classes, and rewrites
index.csv in place with the standardized §9 trailing extension columns
(doc_class, fetch_status, text_path, text_chars). The pre-existing `sha256` city-extra
(a 16-char prefix of the full digest of the STORED raw, present for every row) is left
untouched and already serves the §9 sha256 provenance requirement — EC RETAINS raw, so
the binary is not discarded here.

EC is a ~1,600-pop MSD-staffed township-origin town. Small classified counts are the
CORRECT, honest result. Scope: `supporting_docs` + `staff_report` rows only; `full_packet`
container rows are skipped (doc_class blank).

Classes (first match wins; blank = honestly unclassified, NEVER force-bucketed):
  staff_report          land-use / code staff reports. Title says "Staff Report", OR the
                        sidecar head carries the MSD staff-report template (Meeting Body /
                        Meeting Date / File Number & Project Type, >=3 markers) AND the
                        phrase "staff report" — a high-precision in-TEXT detector that
                        catches reports whose title is an opaque case key (e.g. CUP2025-...).
  plan_amendment        GP / land-use-MAP amendment substance attached to a packet: a draft
                        General-Plan-adoption/amendment ordinance, or a zoning/land-use-map
                        CHANGE ordinance. (EC's full draft General Plan documents are class-3
                        general_plan -> housing_plans, OUT of this packets classifier.)
  member_memo           council-member proposal / amendment memos (the Sandy "Sharkey" class):
                        an EC council-member surname + a memo/proposal token. EC's council is
                        narrative-tally (mayor votes) and files no such memos -> EMPTY (0).
                        The 3 packet "memo" titles are MSD staff/legal/agency memos, not
                        member proposals (verified against sidecar heads) -> correctly blank.
  development_agreement DA / MDA INSTRUMENT only. EC has none — the "agreement" titles are
                        interlocal / utility-program agreements, and "EC DA Ordinance" is a
                        DA-ENABLING ordinance (zoning text), not an instrument -> EMPTY (0).

DISCARD-ROW SAFETY (SCHEMA_SPEC §9 discard-binary exception, hardened 2026-07-19):
  This script RESETS the four derived columns (doc_class, fetch_status, text_path,
  text_chars) on every row each run and re-derives them from on-disk state — the
  `text/<stem>.txt` sidecar keyed off the row's `path`. That is safe only while EC
  RETAINS every raw binary (true today). A §9 discard row — a `stored=no` row whose
  binary was fetched, hashed, extracted, then DISCARDED (text-only corpus, re-fetchable
  via source_url) — carries its §9 columns (doc_class/fetch_status/text_path/text_chars)
  DIRECTLY in index.csv with no on-disk binary to re-derive from; its `path` is blank, so
  the reset path would blank text_path/text_chars and mis-set fetch_status to needs_ocr
  (fp=None) on every rerun. EC has 0 such rows TODAY (every row is stored + re-derivable),
  so the hazard is DORMANT. The guard below hardens the classifier BEFORE EC ever gains a
  discard row: a `stored=no` row with a populated `text_path` is a §9 discard row and is
  PRESERVED VERBATIM (no reset, no reclassification), counted as `discard_preserved`. This
  is the same defect CLASS that blanked draper's 243 §9 discard rows — see draper's
  packets/link_text_sidecars.py "DISCARD-ROW SAFETY".

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXT = os.path.join(HERE, "text")

IN_SCOPE = ("supporting_docs", "staff_report")
NEW_COLS = ["doc_class", "fetch_status", "text_path", "text_chars"]

# --- title-token regexes (case-insensitive) -------------------------------
RE_STAFF_REPORT_TITLE = re.compile(r"staf{1,2}\s*_?\s*report", re.I)

# EC council-member surnames (from meeting_minutes/roster.csv; closed roster) — the
# member_memo gate. None of the packet memo titles carry one, so this class is 0.
RE_MEMBER_SURNAME = re.compile(
    r"\b(?:smolka|brems|hawkes|harris|bowen|pinon|paine|hook|griffith)\b", re.I)
RE_MEMO_TOKEN = re.compile(r"\bmemo(?:randum)?\b|\bproposal\b|redline", re.I)

# plan_amendment: GP-amendment ordinance OR zoning/land-use-map change ordinance.
RE_GP_ORD = re.compile(r"general\s+plan", re.I)
RE_ORD_TOKEN = re.compile(r"\bordinance\b", re.I)
RE_MAP_CHANGE = re.compile(r"(?:zoning|land\s*use)\s+map\s+(?:change|amend)", re.I)

# development_agreement INSTRUMENT (not an enabling ordinance / interlocal / memo).
RE_DA_INSTRUMENT = re.compile(r"(?:master\s+)?development\s+agreement\b|\bMDA\b", re.I)
RE_DA_NOT_INSTRUMENT = re.compile(
    r"ordinance|interlocal|utility|memo|slides|presentation|conditional\s+use", re.I)

# --- MSD staff-report template markers (read from the sidecar head) --------
RE_TPL = [re.compile(p, re.I) for p in (
    r"Meeting\s+Body\s*:",
    r"Meeting\s+Date\s*:",
    r"File\s+Number|Project\s+Type",
    r"\bPlanner\b|Applicant\s*:",
)]
RE_SR_PHRASE = re.compile(r"staff\s+report", re.I)


def sidecar_stem(path):
    if not path.lower().endswith(".pdf"):
        return None
    return os.path.splitext(os.path.basename(path))[0]


def sidecar_path(path):
    stem = sidecar_stem(path)
    if not stem:
        return None
    fp = os.path.join(TEXT, stem + ".txt")
    return fp if os.path.exists(fp) else None


def read_head(fp, n=1500):
    try:
        return open(fp, errors="replace").read()[:n]
    except OSError:
        return ""


def is_msd_staff_report(head):
    """MSD staff-report template (>=3 markers) AND the phrase 'staff report'."""
    if not head:
        return False
    markers = sum(bool(rx.search(head)) for rx in RE_TPL)
    return markers >= 3 and bool(RE_SR_PHRASE.search(head))


def classify(title, head):
    t = title or ""
    # 1. member_memo — EC council-member proposal memo (empty class; gate keeps it honest)
    if RE_MEMBER_SURNAME.search(t) and RE_MEMO_TOKEN.search(t):
        return "member_memo"
    # 2. staff_report — title OR MSD in-text template
    if RE_STAFF_REPORT_TITLE.search(t):
        return "staff_report"
    if is_msd_staff_report(head):
        return "staff_report"
    # 3. plan_amendment — GP-amendment ordinance OR zoning/land-use-map change ordinance
    if RE_MAP_CHANGE.search(t):
        return "plan_amendment"
    if RE_GP_ORD.search(t) and RE_ORD_TOKEN.search(t):
        return "plan_amendment"
    # 4. development_agreement — the instrument itself (none in EC)
    if RE_DA_INSTRUMENT.search(t) and not RE_DA_NOT_INSTRUMENT.search(t):
        return "development_agreement"
    return ""


def main():
    dry = "--dry-run" in sys.argv
    with open(INDEX, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for c in NEW_COLS:
        if c not in fields:
            fields.append(c)

    counts, ok, needs_ocr, discard_preserved = {}, 0, 0, 0
    for r in rows:
        for c in NEW_COLS:
            r.setdefault(c, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored='no' row that ALREADY carries a
        # populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; §9 columns maintained IN-FILE with no on-disk binary to re-derive
        # from — path is blank). PRESERVE it verbatim (never reset/reclassify); the guard
        # runs BEFORE the reset below. EC has 0 such rows today (retains every raw), so
        # this is dormant hardening. See module docstring "DISCARD-ROW SAFETY".
        if r.get("stored") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        # reset the derived columns each run (idempotent)
        r["doc_class"] = r["fetch_status"] = r["text_path"] = r["text_chars"] = ""
        if r["packet_kind"] not in IN_SCOPE:
            continue
        fp = sidecar_path(r["path"])
        head = read_head(fp) if fp else ""
        dc = classify(r["title"], head)
        if not dc:
            continue
        r["doc_class"] = dc
        counts[dc] = counts.get(dc, 0) + 1
        if fp:
            r["fetch_status"] = "ok"
            r["text_path"] = os.path.relpath(fp, HERE)
            r["text_chars"] = str(len(open(fp, errors="replace").read()))
            ok += 1
        else:
            # classified but no born-digital sidecar -> scanned/office-doc OCR floor
            r["fetch_status"] = "needs_ocr"
            needs_ocr += 1

    n_scope = sum(1 for r in rows if r["packet_kind"] in IN_SCOPE)
    n_class = sum(counts.values())
    print(f"in-scope rows: {n_scope}  classified: {n_class}  "
          f"unclassified: {n_scope - n_class}  (ok={ok} needs_ocr={needs_ocr})")
    print(f"§9 discard rows preserved verbatim: {discard_preserved}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    if dry:
        print("(dry run — index.csv not written)")
        return
    tmp = INDEX + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, INDEX)
    print(f"wrote {INDEX} ({len(rows)} rows, {len(fields)} cols)")


if __name__ == "__main__":
    main()
