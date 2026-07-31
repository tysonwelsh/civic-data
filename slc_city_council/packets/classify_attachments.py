#!/usr/bin/env python3
"""classify_attachments.py — doc_class classifier for SLC packets/index.csv.

PRIMARY_DOCS_PILOT_SPEC.md §5 / SKILL Source 7. Deterministic + rerunnable.
SLC is the **A-lite** case: the only per-item, separable, on-disk primary
documents are the Planning Commission 2026 slice on slcdocs.com. The Council
side is monolithic PrimeGov `Meeting Materials` bundles (index-only, 15-30 GB,
vision/OCR-heavy) and is NOT separable/extractable for this rollout — see
AVAILABILITY.md ("Council portal — classes not separable" §).

Scope of this classifier (the only target class present on disk):
  staff_report   Planning Commission land-use staff reports (rezone / zoning-map
                 & text amendment / alley- & street-vacation / planned-development
                 extension / petition-initiation / conditional-use analysis that
                 makes a recommendation to the Commission and/or City Council).

Only the ELEVEN PC staff_report rows that are stored on disk (stored_locally=yes,
format=text, with a text/ sidecar) can be VERIFIED against their own extracted
text and given the §9 text-layer columns. The THIRTEEN PC staff_report rows that
are >10 MB map/plat-heavy exhibits were never fetched (store-cap, index-only,
format=na) — there is no on-disk text to verify and no stored binary to hash, so
they stay doc_class='' (honestly unclassified / not in the text layer). This is
the same >10 MB index-only exhibit set already logged in AVAILABILITY.md.

motion_sheet / agenda / (Council) full_packet / agenda_only rows are NOT target
classes and stay doc_class='' by design.

The content gate below is a whole-class verifier: a stored staff_report row is
only labeled if its sidecar text carries the SLC Planning Division staff-report
signature (Planning Commission recipient + a land-use action token). Any stored
row that fails the gate stays blank and is reported as a MISS — never
force-bucketed.

Run:  python3 classify_attachments.py            # classify + rewrite index.csv
      python3 classify_attachments.py --dry-run  # report counts, write nothing
"""
import csv, hashlib, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
INDEX = os.path.join(HERE, "index.csv")
NEW_COLS = ["doc_class", "fetch_status", "sha256", "text_path", "text_chars"]

# --- staff-report content gate (verified whole-class against the 11 sidecars) --
# (a) SLC Planning Commission is the report's recipient.
RE_PC_RECIPIENT = re.compile(r"salt\s+lake\s+city\s+planning\s+commission", re.I)
# (b) SLC Planning Division staff-report letterhead.
RE_PLANNING_DIVISION = re.compile(r"planning\s+division", re.I)
# (c) at least one land-use action the staff report analyzes / recommends on.
RE_LANDUSE_ACTION = re.compile(
    r"zoning\s+map\s+amendment|zone\s+change|rezone|text\s+amendment|"
    r"alley\s+vacation|street\s+vacation|planned\s+development|conditional\s+use|"
    r"subdivision|\bplat\b|petition\s+initiation|land\s+use|master\s+plan|"
    r"general\s+plan|community\s+plan|small\s+area\s+plan|time\s+extension", re.I)


def is_landuse_staff_report(text: str) -> bool:
    """Whole-class verifier: the sidecar reads as an SLC Planning Division
    land-use staff report (or planning memorandum serving as one)."""
    return bool(RE_PC_RECIPIENT.search(text)
                and RE_PLANNING_DIVISION.search(text)
                and RE_LANDUSE_ACTION.search(text))


def sidecar_for(path: str) -> str:
    """Dataset-relative text sidecar for a stored raw PDF path."""
    base = os.path.basename(path)
    if base.lower().endswith(".pdf"):
        base = base[:-4] + ".txt"
    return os.path.join("text", base)


def sha256_of(abspath: str) -> str:
    h = hashlib.sha256()
    with open(abspath, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dry = "--dry-run" in sys.argv

    with open(INDEX, newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames)
        rows = list(reader)
    for col in NEW_COLS:
        if col not in fields:
            fields.append(col)

    verified, index_only, missing, miss_gate = [], [], [], []
    for r in rows:
        for col in NEW_COLS:
            r.setdefault(col, "")
        # Only the PC staff_report kind is a candidate target class.
        if not (r["body"] == "PlanningCommission" and r["packet_kind"] == "staff_report"):
            r["doc_class"] = ""  # never a target class here
            continue
        # Index-only large exhibits (>10 MB store-cap): no stored binary / text.
        if r["stored_locally"] != "yes" or not r["path"]:
            index_only.append(r)
            continue
        raw_abs = os.path.join(HERE, r["path"])
        side_rel = sidecar_for(r["path"])
        side_abs = os.path.join(HERE, side_rel)
        if not (os.path.exists(raw_abs) and os.path.exists(side_abs)):
            missing.append(r)
            continue
        with open(side_abs, encoding="utf-8", errors="replace") as tf:
            text = tf.read()
        if not is_landuse_staff_report(text):
            miss_gate.append(r)  # stored but not a land-use staff report — blank + note
            continue
        r["doc_class"] = "staff_report"
        r["fetch_status"] = "ok"
        r["sha256"] = sha256_of(raw_abs)
        r["text_path"] = side_rel
        r["text_chars"] = str(len(text))
        verified.append(r)

    ntarget = len(verified) + len(index_only) + len(missing) + len(miss_gate)
    print(f"PC staff_report rows (target class): {ntarget}")
    print(f"  classified staff_report (verified on-disk text): {len(verified)}")
    print(f"  index-only >10MB exhibits (blank, no on-disk text): {len(index_only)}")
    print(f"  stored but failed content gate (blank + note):     {len(miss_gate)}")
    print(f"  stored but file missing (blank + note):            {len(missing)}")
    for label, bucket in (("index-only", index_only), ("gate-miss", miss_gate),
                          ("missing", missing)):
        for r in bucket:
            print(f"    [{label}] {r['date']} {r['title']} ({r['size_mb']} MB)")

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
