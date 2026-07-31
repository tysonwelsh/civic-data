#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Alta packets/index.csv.

PRIMARY_DOCS_PILOT_SPEC.md §5 / SKILL.md Source 7. Deterministic + rerunnable:
reads index.csv, classifies each packet attachment into the four content-bearing
primary-document classes, and rewrites index.csv in place with the SCHEMA_SPEC §9
trailing columns (doc_class, fetch_status, sha256, text_path, text_chars). Blank
doc_class = honestly unclassified — NEVER force-bucketed.

Alta specifics (vs the Sandy Legistar reference impl):
  * No matter/agenda metadata table exists. Classification is TITLE tokens +
    the born-digital TEXT SIDECAR HEAD (text/<stem>.txt, first 1500 chars) —
    the deterministic script may read the sidecar to disambiguate opaque titles
    (e.g. "2023-7-Conex-CUP-Materials", "JG memo to TC last issue").
  * The packets are STORED on disk (not index-only), so sha256 is computed from
    the retained raw PDF and text_path links the existing sidecar. No fetching.
  * Staff analysis is split across packet_kind = staff_report AND supporting_doc
    (and rarely agenda_packet); full_packet bundles are container docs and are
    skipped. All kinds except full_packet are scanned.

Classes (Alta 2020-2026 result — see CLAUDE.md for the metrics/gates):
  staff_report          land-use staff reports/memos (CUP, variance, subdivision
                        ordinance, zoning map/amendment, site-plan/PUD, land-use
                        appeal). The ONLY populated class for Alta.
  member_memo           council-member proposal/amendment memos. HONEST EMPTY
                        (Alta council memos are staff-authored; the one surname
                        hit is a fire-authority memo TO the mayor, not a proposal).
  plan_amendment        GP / land-use-map amendment exhibits. HONEST EMPTY (the
                        General Plan lives in housing_plans/; no map-amendment
                        exhibit rides the packet corpus).
  development_agreement DA/MDA instruments. HONEST EMPTY (none exist 2020-2026).

Land-use SCOPING is intentionally narrow (Sandy convention): business-license /
STR, parking/traffic (Title 6), noise, budget/capital-projects, fire, water/sewer
rates, audits, town-manager, EIS, and PC-governance (member appointment/term) docs
are NOT land-use and stay unclassified even when titled "Staff Report". Presentations
/ slide decks are excluded (not staff reports) — this drops the Shallow Shaft rezone
PRESENTATIONS (image/slide decks; no separate staff report was posted for them).

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, re, sys, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
TEXTDIR = os.path.join(HERE, "text")

HEAD_CHARS = 1500  # sidecar prefix scanned for body-level signals

# --- STRONG land-use phrases (multi-word / unambiguous — single tokens like
# "subdivision", "hillside", "annex", "zone" are deliberately NOT here because
# they appear incidentally in waterline/capital/hazard reports). Matched in the
# title OR the sidecar head. --------------------------------------------------
RE_LANDUSE_STRONG = re.compile(
    r"zoning\s+map|zone\s+change|\brezon|"
    r"conditional\s+use\s+permit|\bCUP\b|conditional\s+use\b|"
    r"variance\s+request|\bvariance\s+to\b|slopes?\s+over\s+30|"
    r"site\s+plan\s+agreement|planned\s+unit\s+development|\bPUD\b|"
    r"subdivision\s+ordinance|"
    r"land\s+use\s+appeal|appeal\s+authority|"       # Alta's Appeal Authority = the Land Use Appeal Authority
    r"general\s+plan\s+amendment|zoning\s+amendment|land\s+use\s+amendment",
    re.I)

# --- analysis-document signals ------------------------------------------------
# in the TITLE:
RE_ANALYSIS_TITLE = re.compile(
    r"staff\s*report|staff\s*rpt|staff\s*memo|staff\s*review|"
    r"\bmemo\b|memorandum|\breport\b|\brpt\b|\breview\b", re.I)
# in the sidecar HEAD (catches opaque titles like "...-Materials" / "...Update"
# whose body opens "Staff Report / To: Town Council / Re: ... CUP"):
RE_ANALYSIS_BODY = re.compile(
    r"staff\s+(?:report|memo)|"
    r"memo(?:randum)?\s+to\s+the\s+(?:town\s+council|alta|planning)|"
    r"recommendation\s+to\s+(?:the\s+)?(?:town|alta|planning|appeal)", re.I)

# --- exclusions ---------------------------------------------------------------
RE_EXCL_TITLE = re.compile(r"presentation|\bslides\b", re.I)  # not staff reports

# --- member_memo (council-member proposal memos) — HONEST EMPTY for Alta.
# Conservative: a council-member surname as the memo AUTHOR ("From: <member>")
# with a proposal/amendment. Staff authors (McLean, Guldner, Platt, Cawley) and
# memos merely ADDRESSED TO a member do not qualify.
COUNCIL_SURNAMES = r"(?:bourke|morgan|anctil|byrne|schilling|heimark|curry|sondak|moxley|davis)"
RE_MEMBER_AUTHOR = re.compile(
    r"from:\s*(?:council\s*member\s+)?" + COUNCIL_SURNAMES, re.I)
RE_MEMBER_PROPOSAL = re.compile(r"\bproposal\b|proposed\s+amendment|\bmy\s+amendment", re.I)

# --- plan_amendment (GP / land-use-MAP amendment EXHIBIT) — HONEST EMPTY.
# The instrument/exhibit itself (proposed map / GP element), not the staff report
# about it, and NOT a zoning-code amendment (that is a code edit, not a plan).
RE_PA_INSTRUMENT = re.compile(
    r"future\s+land\s+use\s+map|general\s+plan\s+(?:element|exhibit|map)|"
    r"proposed\s+(?:land\s+use|general\s+plan)\s+map", re.I)
RE_PA_EXCLUDE = re.compile(r"staff\s*report|staff\s*memo|minutes|notice|agenda", re.I)

# --- development_agreement — HONEST EMPTY (none exist).
RE_DA_INSTRUMENT = re.compile(r"(?:master\s+)?development\s+agreement|\bMDA\b|\bDDA\b", re.I)
RE_DA_NOT = re.compile(r"presentation|briefing|staff\s*report|\bmemo\b|minutes|agenda", re.I)


def sidecar_stem(path: str) -> str:
    base = os.path.basename(path)
    return base[:-4] if base.lower().endswith(".pdf") else base


def read_head(stem: str) -> str:
    p = os.path.join(TEXTDIR, stem + ".txt")
    if not os.path.exists(p):
        return ""
    with open(p, errors="replace") as f:
        return f.read(HEAD_CHARS)


def classify(title: str, head: str) -> str:
    t = title or ""
    # development_agreement (instrument, not a briefing about one)
    if RE_DA_INSTRUMENT.search(t) and not RE_DA_NOT.search(t):
        return "development_agreement"
    # member_memo — member is the memo author + a proposal (body-confirmed)
    if RE_MEMBER_AUTHOR.search(head) and RE_MEMBER_PROPOSAL.search(head):
        return "member_memo"
    # plan_amendment — GP/land-use-map amendment exhibit (not the staff report)
    if RE_PA_INSTRUMENT.search(t) and not RE_PA_EXCLUDE.search(t):
        return "plan_amendment"
    # staff_report — land-use staff analysis (the populated class)
    if RE_EXCL_TITLE.search(t):
        return ""
    strong = RE_LANDUSE_STRONG.search(t) or RE_LANDUSE_STRONG.search(head)
    analysis = RE_ANALYSIS_TITLE.search(t) or RE_ANALYSIS_BODY.search(head)
    if strong and analysis:
        return "staff_report"
    return ""


def sha256_file(path: str) -> str:
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
    for col in ("doc_class", "fetch_status", "sha256", "text_path", "text_chars"):
        if col not in fields:
            fields.append(col)

    counts, statuses = {}, {}
    discard_preserved = 0
    for r in rows:
        for col in ("doc_class", "fetch_status", "sha256", "text_path", "text_chars"):
            r.setdefault(col, "")
        # SCHEMA_SPEC §9 discard-binary rows: a stored='no' row that ALREADY carries a
        # populated text_path is a §9 discard row (binary fetched/hashed/extracted then
        # DISCARDED; its §9 columns are maintained IN-FILE with no on-disk binary/sidecar
        # to re-derive from). PRESERVE it verbatim — the reset below would blank its
        # text_path/text_chars/sha256 and mis-set fetch_status on every rerun. Guard runs
        # BEFORE the reset. Alta has 0 such rows today (classify-in-place, no `stored`
        # column — every row retains its raw), so this is dormant hardening; matches the
        # defect CLASS fixed in draper packets/link_text_sidecars.py "DISCARD-ROW SAFETY".
        if r.get("stored") == "no" and (r.get("text_path") or "").strip():
            discard_preserved += 1
            continue
        # reset the §9 columns each run (idempotent)
        r["doc_class"] = r["fetch_status"] = r["sha256"] = r["text_path"] = r["text_chars"] = ""
        if r["packet_kind"] == "full_packet":
            continue  # container docs — out of scope
        stem = sidecar_stem(r["path"])
        head = read_head(stem)
        dc = classify(r["title"], head)
        if not dc:
            continue
        r["doc_class"] = dc
        counts[dc] = counts.get(dc, 0) + 1
        # populate §9 provenance for classified rows
        rawpath = os.path.join(HERE, r["path"])
        if os.path.exists(rawpath):
            r["sha256"] = sha256_file(rawpath)
        sidecar = os.path.join(TEXTDIR, stem + ".txt")
        if os.path.exists(sidecar):
            with open(sidecar, errors="replace") as f:
                txt = f.read()
            r["fetch_status"] = "ok"
            r["text_path"] = os.path.join("text", stem + ".txt")
            r["text_chars"] = str(len(txt))
        else:
            # classified but no sidecar => image-only scan, honest OCR floor
            r["fetch_status"] = "needs_ocr"
        statuses[r["fetch_status"]] = statuses.get(r["fetch_status"], 0) + 1

    scanned = sum(1 for r in rows if r["packet_kind"] != "full_packet")
    nclass = sum(counts.values())
    print(f"rows: {len(rows)}  in-scope(non-full_packet): {scanned}  "
          f"classified: {nclass}  unclassified: {scanned - nclass}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
    print("fetch_status:", dict(sorted(statuses.items())))
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
