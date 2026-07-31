#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Lehi packets/index.csv.

PRIMARY_DOCS_ROLLOUT (2026-07-16), adapted from sandy_city_council/packets/.
Deterministic + rerunnable: reads index.csv, classifies the 452 `staff_report`
attachment rows (pilot window 2024-2025) into the primary-document classes, and
populates the SCHEMA_SPEC §9 pilot columns (doc_class, fetch_status, sha256,
text_path, text_chars). Rewrites index.csv in place. Blank doc_class = honestly
unclassified — NEVER force-bucketed.

Lehi difference from Sandy: there is NO Legistar matter-metadata join available.
Lehi attachment TITLES are underscore-joined, munged, often truncated (e.g.
"Newbold_1", "Edge_Homes_Main_Street_ZC_1", "Exchange_16_Plat_Amendment_1"), so
the classifier's PRIMARY signal is the TEXT SIDECAR HEAD: Lehi staff reports open
with a banner template ("<CASE NAME> ... PLANNING COMMISSION REPORT" /
"CITY COUNCIL REPORT", Applicant / Meeting Date / Requested Action fields) and
DRC reviews open with "Lehi City Development Review Committee". Reading title +
sidecar-head is still fully deterministic (no LLM, no network).

Classes (first match wins):
  staff_report          land-use staff reports — PC/CC staff reports + Development
                        Review Committee (DRC) staff reviews behind rezone / GPA /
                        plat / subdivision / conditional-use / development-code /
                        area-plan / development-agreement agenda items.
  member_memo           council-member proposal memos / amendment memoranda
                        (Lehi 2024-25: ZERO — honest empty class; Lehi is all
                        at-large and files no member proposal memos in the corpus).
  plan_amendment        GP / land-use-map amendment EXHIBITS (proposed element /
                        Exhibit-A plan text, not the report, not an aerial/map)
                        (Lehi 2024-25: ZERO — the GP-amendment substance appears
                        only as the staff report + the applicant letter + an
                        aerial map; no separable proposed-element exhibit).
  development_agreement DA / MDA INSTRUMENTS (Lehi 2024-25: ZERO readable — the
                        DA-titled born-digital files are the PC staff REPORTS
                        about the DA (-> staff_report); the executed/draft
                        instruments ride the corpus only as scanned "_DA_2"
                        exhibits with no text layer -> needs_ocr, unverifiable,
                        left blank rather than guessed).

Pipeline columns (Sandy-faithful — populated for the pipeline rows only):
  classified row (doc_class set) WITH a text sidecar -> fetch_status=ok,
      text_path=text/<stem>.txt, text_chars=<sidecar length>, sha256=<raw binary>.
  row whose raw PDF has NO usable text layer (image-only / scanned) ->
      fetch_status=needs_ocr, sha256=<raw binary>, blank text_path/text_chars
      (an honest OCR floor; these are all unclassified exhibits — aerials, POs,
      a DRAFT construction agreement, scanned DA_2 exhibits).
  unclassified row WITH a sidecar -> pipeline columns left blank (out of pilot
      scope, exactly as Sandy left its 5,557 unclassified attachments).

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXTDIR = os.path.join(HERE, "text")
PIPELINE_COLS = ("doc_class", "fetch_status", "sha256", "text_path", "text_chars")

# --- sidecar-head report-template detectors (the primary signal) -----------
# The head is uppercased with runs of whitespace collapsed to single spaces.
RE_REPORT_BANNER = re.compile(
    r"PLANNING COMMISSION REPORT"
    r"|CITY COUNCIL REPORT"
    r"|DEVELOPMENT REVIEW COMMITTEE",   # DRC staff review
    re.I)
# the report template's field header (catches banner-wrap variants where the
# literal "... REPORT" string is split across lines): both fields present.
RE_TEMPLATE_REQ = re.compile(r"REQUESTED ACTION", re.I)
RE_TEMPLATE_APP = re.compile(r"\bAPPLICANT\b", re.I)

# --- title-token detectors (fallback / corroboration; underscore-delimited) -
RE_TITLE_STAFF_REPORT = re.compile(r"staff.?report", re.I)  # CC_/PC_Staff_Report_*
RE_TITLE_DRC = re.compile(r"(?:^|_)DRC(?:_|$|\.)", re.I)

# --- member_memo (Lehi: yields 0; kept for rerunnable completeness) ---------
RE_MEMO = re.compile(r"\bMEMORANDUM\b|council\s*member\s+\w+\s+(?:propos|memo)", re.I)
RE_NOT_MEMO = re.compile(r"REPORT|DEVELOPMENT REVIEW COMMITTEE", re.I)


def sidecar_stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]


def read_head(stem: str, n: int = 1500):
    fp = os.path.join(TEXTDIR, stem + ".txt")
    if not os.path.exists(fp):
        return None, fp
    txt = open(fp, errors="replace").read()
    head = " ".join(txt[:n].split()).upper()
    return (head, len(txt)), fp


def classify(title: str, head) -> str:
    """head is None when there is no sidecar (image-only/scanned raw)."""
    if head is None:
        # no usable text layer -> cannot verify content; never guess a class.
        return ""
    t = title or ""
    is_report = bool(
        RE_REPORT_BANNER.search(head)
        or (RE_TEMPLATE_REQ.search(head) and RE_TEMPLATE_APP.search(head))
        or RE_TITLE_STAFF_REPORT.search(t)
        or RE_TITLE_DRC.search(t))
    # 1. member_memo — a councilmember proposal memorandum (not a staff report)
    if RE_MEMO.search(head) and not RE_NOT_MEMO.search(head) and not is_report:
        return "member_memo"
    # 2. staff_report — the dominant land-use staff-analysis class
    if is_report:
        return "staff_report"
    # 3/4. plan_amendment / development_agreement — no separable, verifiable
    #      instances in the Lehi 2024-25 corpus (see module docstring); honest
    #      empties, never force-bucketed.
    return ""


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
    for col in PIPELINE_COLS:
        if col not in fields:
            fields.append(col)

    counts = {}
    fetch = {"ok": 0, "needs_ocr": 0}
    discard_preserved = 0
    for r in rows:
        for col in PIPELINE_COLS:
            r.setdefault(col, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored='no' row that ALREADY carries a
        # populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; its §9 columns are maintained IN-FILE with no on-disk binary/sidecar to
        # re-derive from). PRESERVE it verbatim — the reset/re-derive below would blank its
        # text_path/text_chars and mis-set fetch_status (and sha256_of would fail on the
        # absent raw) on every rerun. Guard runs BEFORE the packet_kind reset. Lehi has 0
        # such rows today (classify-in-place, no `stored` column — raws are RETAINED), so
        # this is dormant hardening; matches the defect CLASS fixed in draper
        # packets/link_text_sidecars.py "DISCARD-ROW SAFETY".
        if r.get("stored") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        if r["packet_kind"] != "staff_report":
            for col in PIPELINE_COLS:
                r[col] = ""
            continue
        stem = sidecar_stem(r["path"])
        info, _fp = read_head(stem)
        head = info[0] if info else None
        r["doc_class"] = classify(r["title"], head)

        # pipeline columns
        if r["doc_class"] and info:                      # classified + has text
            r["fetch_status"] = "ok"
            r["text_path"] = "text/" + stem + ".txt"
            r["text_chars"] = str(info[1])
            r["sha256"] = sha256_of(os.path.join(HERE, r["path"]))
            fetch["ok"] += 1
        elif info is None:                               # no usable text layer
            r["fetch_status"] = "needs_ocr"
            r["text_path"] = ""
            r["text_chars"] = ""
            r["sha256"] = sha256_of(os.path.join(HERE, r["path"]))
            fetch["needs_ocr"] += 1
        else:                                            # unclassified + has text
            for col in ("fetch_status", "sha256", "text_path", "text_chars"):
                r[col] = ""

        if r["doc_class"]:
            counts[r["doc_class"]] = counts.get(r["doc_class"], 0) + 1

    natt = sum(1 for r in rows if r["packet_kind"] == "staff_report")
    nclass = sum(counts.values())
    print(f"staff_report rows: {natt}  classified: {nclass}  unclassified: {natt - nclass}")
    for k in sorted(counts):
        print(f"  doc_class {k}: {counts[k]}")
    print(f"fetch_status ok={fetch['ok']}  needs_ocr={fetch['needs_ocr']}")
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
