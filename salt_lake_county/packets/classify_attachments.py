#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Salt Lake County packets/index.csv.

SCHEMA_SPEC.md §9 primary-document text layer, county adaptation of the Sandy pilot
(sandy_city_council/packets/classify_attachments.py). Deterministic + rerunnable: reads
index.csv, joins each attachment's `matter_id` to the county db (READ-ONLY, uri mode=ro)
for the underlying MOTION TEXT — the county's Legistar matter metadata (EventItemMatterName/
Type) is blank/coarse, so motion text (the agenda action title) is the reliable land-use
signal — assigns `doc_class`, and rewrites index.csv in place, APPENDING the §9 pilot
columns after the county's existing columns (text_path already exists and is preserved).

Blank doc_class = honestly unclassified — NEVER force-bucketed.

Classes (SCHEMA_SPEC §9 controlled vocabulary; only staff_report occurs on the county's
ON-DISK packet corpus — see the honest-empty rationale in CLAUDE.md / AVAILABILITY.md):
  staff_report          LAND-USE staff reports (rezone / zoning-code (Title 9/17/18/19) /
                        annexation / general-plan adoption-amendment / subdivision /
                        conditional-use). County general-government staff reports (budget
                        adjustments, committee appointments) stay BLANK even though the
                        harvest's land-use matter filter pulled a few in (e.g. the "Clark
                        Planetarium Annex" building-remodel budgets — "Annex" false hits).
  member_memo           council-member proposal memos — HONEST EMPTY (county has none; its
                        "Council Briefing Memo" items are STAFF memos, not member proposals).
  plan_amendment        GP / township-plan amendment exhibits — HONEST EMPTY in packets/:
                        the county's GP exhibits are large (13-52 MB) index-only rows and
                        their authoritative text lives in the dedicated `plans/` module.
  development_agreement DA / MDA instruments — HONEST EMPTY in the stored corpus: the sole
                        instrument (matter 6980 Olympia Hills MDA Amendment No. 2) is an
                        index-only row with no on-disk text.

§9 trailing columns populated (only for classified rows; blank elsewhere — matches Sandy):
  fetch_status  'ok' (text extracted on disk) | 'no_extractor' (stored raw exists but the
                PDF-only pipeline produced no text — matter 4700 is an RTF-saved-as-.pdf).
  sha256        sha256 of the stored raw binary (provenance), where a raw is on disk.
  text_chars    char length of the extracted text sidecar, where present.
  text_path     PRESERVED verbatim from the county build (already dataset-relative).

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, hashlib, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
COUNTY = os.path.dirname(HERE)                       # salt_lake_county/
INDEX = os.path.join(HERE, "index.csv")
DB = os.path.join(COUNTY, "db", "salt_lake_county.db")

# The 4 pilot columns appended after the county's existing header (text_path already exists).
PILOT_COLS = ["doc_class", "fetch_status", "sha256", "text_chars"]

# --- land-use signal on the matter's MOTION TEXT (the county agenda action title) --------
RE_LANDUSE = re.compile(
    r"rezone|zoning|zone\s+change|amend\w*\s+title\s+(?:9|17|18|19)|annexation|"
    r"general\s+plan|subdivision|conditional\s+use|planned\s+development|\bplat\b|"
    r"flood\s+control|foothills\s+canyon|mineral\s+extraction|community\s+zone|"
    r"land\s+use|master\s+development", re.I)
# --- general-government EXCLUSION (wins over land-use; blanks the harvest false-positives)-
RE_GENGOV = re.compile(
    r"budget\s+adjustment|steering\s+committee|appointment|budget\s+neutral|\bgasb\b|"
    r"planetarium|remodel|lease\s+expense|naming\s+rights", re.I)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(packet_kind, motion_text):
    """Deterministic doc_class. Only land-use staff reports classify on the county corpus."""
    if packet_kind != "staff_report":
        return ""                                   # agendas + index-only attachments: blank
    if RE_LANDUSE.search(motion_text) and not RE_GENGOV.search(motion_text):
        return "staff_report"
    return ""                                       # general-government staff report: blank


def main():
    dry = "--dry-run" in sys.argv

    con = sqlite3.connect("file:" + os.path.abspath(DB) + "?mode=ro", uri=True)
    motion_text = {}
    for mid, txt in con.execute(
            "SELECT substr(a.app_key,8) AS mid, group_concat(m.motion_text,' || ') "
            "FROM application a JOIN motion m ON m.application_id=a.application_id "
            "WHERE a.app_key LIKE 'matter:%' GROUP BY a.app_key"):
        motion_text[mid] = txt or ""
    con.close()

    with open(INDEX, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in PILOT_COLS:
        if col not in fields:
            fields.append(col)

    counts, status = {}, {}
    discard_preserved = 0
    for r in rows:
        for col in PILOT_COLS:
            r.setdefault(col, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored_locally='no' row that ALREADY carries
        # a populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; its §9 columns are maintained IN-FILE with no on-disk binary/sidecar to
        # re-derive from). PRESERVE it verbatim — the reset/re-derive below would blank its
        # doc_class/fetch_status/sha256/text_chars (sha256 needs the absent raw; text_chars
        # needs the absent sidecar) on every rerun. Guard runs BEFORE classification. The
        # county's 95 stored_locally='no' rows today are all never-fetched index-only matter
        # attachments (blank text_path), NOT discard rows, so this is dormant hardening;
        # matches the defect CLASS fixed in draper packets/link_text_sidecars.py.
        if r.get("stored_locally") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        r["doc_class"] = classify(r["packet_kind"], motion_text.get(r["matter_id"], ""))
        if not r["doc_class"]:
            r["fetch_status"] = r["sha256"] = r["text_chars"] = ""
            continue
        counts[r["doc_class"]] = counts.get(r["doc_class"], 0) + 1
        # sha256 from the stored raw (provenance), where present
        raw = os.path.join(COUNTY, r["path"]) if r["path"] else ""
        r["sha256"] = sha256_of(raw) if raw and os.path.exists(raw) else ""
        # link the EXISTING extracted text; honest text-floor where the pipeline got none
        tp = os.path.join(COUNTY, r["text_path"]) if r["text_path"] else ""
        if tp and os.path.exists(tp):
            r["fetch_status"] = "ok"
            r["text_chars"] = str(len(open(tp, encoding="utf-8").read()))
        else:
            r["fetch_status"] = "no_extractor"      # raw stored, no usable text (RTF-as-.pdf)
            r["text_chars"] = ""
        status[r["fetch_status"]] = status.get(r["fetch_status"], 0) + 1

    nclass = sum(counts.values())
    print(f"rows: {len(rows)}  classified: {nclass}  unclassified: {len(rows)-nclass}")
    for k in sorted(counts):
        print(f"  doc_class {k}: {counts[k]}")
    for k in sorted(status):
        print(f"  fetch_status {k}: {status[k]}")
    print(f"§9 discard rows preserved verbatim: {discard_preserved}")
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
