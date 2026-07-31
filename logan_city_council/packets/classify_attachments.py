#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for Logan packets/index.csv.

PRIMARY_DOCS_ROLLOUT + expand-city-sources SKILL Source 7 + SCHEMA_SPEC §9.
Adapted from sandy_city_council/packets/classify_attachments.py. Logan has NO
matter metadata — classification is TITLE-ONLY (Logan's human-typed filenames
carry the instrument number + subject + a WORKSHOP/ACTION stage suffix, e.g.
"Ord 22-04 Code Amendments Short Term Rentals - WORKSHOP"). Deterministic +
rerunnable: reads index.csv, rewrites it in place with a doc_class column
(blank = honestly unclassified — NEVER force-bucketed). Existing pipeline
columns (fetch_status, sha256, text_path, text_chars) are preserved.

Only rows with packet_kind == 'staff_report' are eligible (agendas, notices,
proclamations stay blank). The taxonomy is LAND-USE-PRIMARY: budget/admin/
finance resolutions (Budget Adjustments, URS retirement, wages, fees, power
sales contracts, CDBG action plans, fireworks) are NOT in class — they stay
honestly unclassified. Classes (first match wins):

  staff_report           land-use primary docs — rezone/downzone, LDC/Title-17
                         code amendments, annexation/boundary/disconnect,
                         subdivision, ROW/easement vacations, overlays (PDO,
                         critical-lands, historic, gateway), ADU/home-occupation/
                         STR, site/concept plans, neighborhood plans, moderate
                         income housing code, flood-damage prevention, infill/
                         flag-lot, land-use moratorium.
  plan_amendment         General Plan adoption/draft/amendment exhibits (the GP
                         text riding the packet corpus).
  development_agreement  DA / MDA instruments only (Logan 2022-26: none — honest
                         empty class, see AVAILABILITY.md).
  member_memo            council-member proposal/amendment memos (Logan: none —
                         honest empty class).

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, re, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")

# --- council-member surnames (from db/civic.db person; pinned for determinism).
# member_memo requires a surname AND an explicit memo/proposal token, so this
# set cannot false-fire on land-use project names.
SURNAMES = (r"(?:simmonds|daines|anderson|l.?pez|nielson|jensen|bradfield|"
            r"lee.?koven|goodlander|guth|duncan|ortiz|mcnamara|heare)")

# --- land-use tokens (case-insensitive). Each is individually high-precision
# for Logan land-use primary documents.
RE_LANDUSE = re.compile(
    r"rezone|downzone|"                                   # zoning map changes
    r"\bLDC\b|land\s+dev(?:elopment)?\s+code|"            # Land Development Code
    r"\b17\.\d|chapter\s+17\b|title\s+17\b|"              # LDC Title 17 chapters
    r"annex|\bdisconnect\b|\bboundar|"                    # annexation/boundary
    r"subdivision|"                                        # subdivisions
    r"vacat|\bPUE\b|easement|"                            # ROW / easement vacations
                                                           # (bare "right of way" omitted:
                                                           #  it caught ROW-permit FEE resns;
                                                           #  every real ROW vacation carries
                                                           #  "vacat")
    r"overlay|planned\s+development|"                     # overlays / PDO
    r"\bplat\b|site\s+plan|concept\s+plan|"              # plats / site plans
    r"conditional\s+use|\bCUP\b|variance|"               # CUP / variance
    r"accessory\s+dwelling|\bADU\b|home\s+occupation|"   # ADU / home occupations
    r"short\s+term\s+rental|"                             # STR
    r"moderate\s+income\s+housing|"                       # MIH code
    r"critical\s+lands|historic\s+district|"             # named overlays
    r"historic\s+project\s+area|gateway\s+overlay|"
    r"neighborhood\s+plan|"                               # small-area plans
    r"flood\s+damage\s+prevention|"                       # floodplain regs
    r"infill|flag\s+lot|"                                 # infill / flag-lot
    r"public\s+zones|homeless\s+shelter|"                # zoning use amendments
    r"self\s+storage|climate\s+controlled|"              # storage use amendments
    r"land\s+use\s+ordinance|moratorium",                # LU moratorium
    re.I)

# General Plan exhibits (plan_amendment). Requires GP + an amendment/adoption/
# draft verb so the "General Plan Grant Application" and bare "General Plan
# Workshop" presentation rows do NOT bucket here.
RE_GP = re.compile(r"general\s+plan", re.I)
RE_GP_VERB = re.compile(r"draft|approv|adopt|amend|element|update|\bfinal\b", re.I)
RE_GP_EXCLUDE = re.compile(r"grant\s+application", re.I)

# Development agreement instruments (not interlocal/franchise/power/pooling
# agreements, not RDA project-area plans).
RE_DA = re.compile(r"(?:master\s+)?development\s+agreement|\bMDA\b", re.I)

# Administrative FEE resolutions are out of the land-use taxonomy even when they
# reference a land-use process (e.g. a fee schedule for annexation applications).
RE_FEE_ADMIN = re.compile(r"fee\s+schedule|permit\s+fee", re.I)

# member_memo — surname + memo/proposal token.
RE_MEMBER = re.compile(
    r"\b" + SURNAMES + r"\b.*(?:\bmemo(?:randum)?\b|\bproposal\b)|"
    r"(?:\bmemo(?:randum)?\b|\bproposal\b).*\b" + SURNAMES + r"\b", re.I)


def classify(title: str) -> str:
    t = title or ""
    # 1. member_memo (Logan: expected empty)
    if RE_MEMBER.search(t):
        return "member_memo"
    # 2. plan_amendment — GP adoption/draft/amendment exhibits
    if RE_GP.search(t) and RE_GP_VERB.search(t) and not RE_GP_EXCLUDE.search(t):
        return "plan_amendment"
    # 3. development_agreement — the instrument itself (Logan: expected empty)
    if RE_DA.search(t):
        return "development_agreement"
    # 4. staff_report — land-use primary document (admin fee resolutions excluded)
    if RE_LANDUSE.search(t) and not RE_FEE_ADMIN.search(t):
        return "staff_report"
    return ""


def main():
    dry = "--dry-run" in sys.argv
    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in ("doc_class", "fetch_status", "sha256", "text_path", "text_chars"):
        if col not in fields:
            fields.append(col)

    counts = {}
    for r in rows:
        for col in ("doc_class", "fetch_status", "sha256", "text_path", "text_chars"):
            r.setdefault(col, "")
        if r["packet_kind"] != "staff_report":
            r["doc_class"] = ""
            continue
        r["doc_class"] = classify(r["title"])
        if r["doc_class"]:
            counts[r["doc_class"]] = counts.get(r["doc_class"], 0) + 1

    nsr = sum(1 for r in rows if r["packet_kind"] == "staff_report")
    nclass = sum(counts.values())
    print(f"staff_report rows: {nsr}  classified: {nclass}  unclassified: {nsr - nclass}")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")
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
