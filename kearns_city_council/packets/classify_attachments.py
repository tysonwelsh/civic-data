#!/usr/bin/env python3
"""classify_attachments.py — doc_class layer for Kearns packets/index.csv.

PRIMARY_DOCS_ROLLOUT Source 7. Kearns is Bucket A-lite / CLASSIFY-IN-PLACE: the raw
PDFs are already STORED on disk with born-digital text sidecars under text/, so this
script only ADDS the SCHEMA_SPEC §9 columns (doc_class, fetch_status, sha256,
text_path, text_chars) — it fetches nothing. Deterministic + rerunnable: reads
index.csv, verifies each broken-out staff-report row against its sidecar's MSD
staff-report TEMPLATE HEADER (Meeting Body / Meeting Date / Planner / File Number &
Project Type / Staff Recommendation), assigns doc_class, and rewrites index.csv in
place. Existing columns are preserved.

Scope (orchestrator ruling, 2026-07-16): classify ONLY the broken-out per-item
staff reports (packet_kind=staff_report). The full_packet CONTAINERS stay UNLABELED
— a container is not a staff_report even when its content is mostly one MSD staff
report; its full-packet text already serves FTS. The one documented EXCEPTION is the
RECALL-GATE catch: a full_packet row whose sidecar is decisively a single standalone
MSD staff report, mis-shelved by a "…packet" filename (currently OAM2025-001330,
2025-03-03 — one "Meeting Body:", header in the first lines, no agenda/roll-call
markers). It is re-detected deterministically here, not hard-coded.

doc_class values used: staff_report | '' (blank = honestly unclassified / a
container). member_memo, plan_amendment, development_agreement are HONEST EMPTIES —
no broken-out instances exist (verified title + sidecar-head sweep 2026-07-16; the
DA mentions in the corpus are all inside full_packet containers, not standalone
instruments).

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXTDIR = os.path.join(HERE, "text")

# §9 extension columns this layer owns.
EXT_COLS = ["doc_class", "fetch_status", "sha256", "text_path", "text_chars"]

# MSD "Meeting Minute Summary" / staff-report template header — the whole-class
# ground truth for a genuine land-use staff report (all Kearns SRs are MSD-staffed
# and land-use by definition: OAM/REZ/CUP/VAR case keys or Title 18/19 zoning code).
RE_MSD_BODY = re.compile(r"Meeting\s+Body:", re.I)
RE_MSD_DATE = re.compile(r"Meeting\s+Date:", re.I)
# staff-report token: the "…Staff Report" banner or the "Staff Recommendation:" field.
# (The "Planner:" field is NOT used — pdftotext's two-column layout renders it as
# "Planners:" / split lines on some MSD reports, e.g. OAM2025-001330.)
RE_MSD_STAFFREC = re.compile(r"Staff\s+Recommendation:|Staff\s+Report", re.I)
# agenda / bundled-packet markers — their presence means a CONTAINER, not a
# standalone staff report (used only on the full_packet recall path).
RE_AGENDA_MARKERS = re.compile(
    r"call\s+to\s+order|roll\s+call|approval\s+of\s+(?:the\s+)?minutes|"
    r"pledge\s+of\s+allegiance|adjourn", re.I)


def sidecar_stem(path: str) -> str:
    """text/<stem>.txt for a raw path like raw/<date>/<stem>.pdf."""
    return os.path.splitext(os.path.basename(path))[0]


def read_sidecar(stem: str):
    p = os.path.join(TEXTDIR, stem + ".txt")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def has_msd_header(text: str) -> bool:
    """A genuine MSD land-use staff report carries the template header:
    Meeting Body + Meeting Date + a Staff Report / Staff Recommendation field."""
    return bool(RE_MSD_BODY.search(text)
                and RE_MSD_DATE.search(text)
                and RE_MSD_STAFFREC.search(text))


def is_mis_shelved_standalone_sr(text: str) -> bool:
    """RECALL-GATE catch: a full_packet row that is really a single standalone MSD
    staff report (mislabeled by its filename). Decisive, tight test:
      - the MSD header appears near the TOP (within the first ~5 non-blank lines),
      - exactly ONE 'Meeting Body:' occurrence (one report, not a bundle),
      - NO agenda / roll-call markers (i.e. no meeting bundled around it)."""
    if not has_msd_header(text):
        return False
    if len(RE_MSD_BODY.findall(text)) != 1:
        return False
    if RE_AGENDA_MARKERS.search(text):
        return False
    nonblank = [ln for ln in text.splitlines() if ln.strip()]
    head = "\n".join(nonblank[:5])
    return bool(RE_MSD_BODY.search(head))


def sha256_of(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dry = "--dry-run" in sys.argv

    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for c in EXT_COLS:
        if c not in fields:
            fields.append(c)

    counts, recall_hits, warnings = {}, [], []
    discard_preserved = 0
    for r in rows:
        for c in EXT_COLS:
            r.setdefault(c, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored_locally='no' row that ALREADY carries
        # a populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; its §9 columns are maintained IN-FILE with no on-disk binary/sidecar to
        # re-derive from). PRESERVE it verbatim — the reset below would blank its
        # doc_class/fetch_status/sha256/text_path/text_chars on every rerun. Guard runs
        # BEFORE the reset. Kearns has 0 such rows today (only fetched-ok rows enter
        # index.csv — stored_locally='yes' throughout; 404-purged files live in
        # unrecovered.csv), so this is dormant hardening; matches the defect CLASS fixed in
        # draper packets/link_text_sidecars.py "DISCARD-ROW SAFETY".
        if r.get("stored_locally") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        # default: honestly unclassified
        r["doc_class"] = ""
        r["fetch_status"] = ""
        r["sha256"] = ""
        r["text_path"] = ""
        r["text_chars"] = ""

        kind = r.get("packet_kind", "")
        stem = sidecar_stem(r.get("path", ""))
        text = read_sidecar(stem)

        dc = ""
        if kind == "staff_report":
            if text is not None and has_msd_header(text):
                dc = "staff_report"
            else:
                warnings.append(
                    f"packet_kind=staff_report but sidecar lacks MSD header "
                    f"(stays blank): {r.get('title')}")
        elif kind == "full_packet":
            if text is not None and is_mis_shelved_standalone_sr(text):
                dc = "staff_report"
                recall_hits.append(r.get("title"))

        if dc:
            r["doc_class"] = dc
            r["fetch_status"] = "ok"       # text already extracted (STORED on disk)
            r["text_path"] = "text/" + stem + ".txt"
            r["text_chars"] = str(len(text))
            raw_abs = os.path.join(HERE, r["path"])
            r["sha256"] = sha256_of(raw_abs)
            counts[dc] = counts.get(dc, 0) + 1

    nsr = sum(1 for r in rows if r["packet_kind"] == "staff_report")
    print(f"rows: {len(rows)}  staff_report kind: {nsr}  classified: {sum(counts.values())}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print(f"§9 discard rows preserved verbatim: {discard_preserved}")
    if recall_hits:
        print("recall-gate catches (full_packet -> standalone staff_report):")
        for t in recall_hits:
            print("  " + t)
    for w in warnings:
        print("WARN " + w)

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
