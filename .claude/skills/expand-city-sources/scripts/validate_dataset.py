#!/usr/bin/env python3
"""Enforce the expand-city-sources non-negotiable rules on a new dataset directory.

A dataset is "done" only when it passes this. Run it before you declare any of the six
source types complete. It checks the invariants that were learned the hard way in this
repo (see _audits/2026-07-02/report.md): raw retained, machine-readable provenance,
gaps recorded rather than faked.

Checks (per <dataset_dir>, e.g. lehi_city_council/packets):
  1. raw/ exists.
  2. index.csv exists AND — when the dataset dir is one of the six standard source
     types — begins with that type's EXACT contract header (SCHEMA_SPEC.md §9,
     adopted 2026-07-06). City-specific extra columns are allowed only AFTER the
     contract columns. Non-standard dataset dirs fall back to the original minimum
     column check (date,title,source_url,retrieved_date,format,extraction_method).
  3. Every non-empty index row has a date, a source_url, and a format value from the
     allowed vocab {text, scanned, html, json, xml, video, caption, na}.
  4. If index.csv has zero data rows, an AVAILABILITY.md (or unrecovered.csv) must exist
     — an honest empty dataset is valid, a silent empty one is not.
  5. Every local path referenced by a `path` column (if present) exists on disk.
  6. raw/ is non-empty UNLESS AVAILABILITY.md explains why (source published nothing).

Exit non-zero if any rule fails. Prints a checklist. This is a linter, not a judge of
content quality — run screen_corpus.py on any extracted TEXT corpus separately.

Usage:
    python3 validate_dataset.py <dataset_dir> [<dataset_dir> ...]
"""
import csv, os, sys

REQUIRED_COLS = ["date", "title", "source_url", "retrieved_date", "format", "extraction_method"]
FORMAT_VOCAB = {"text", "scanned", "html", "json", "xml", "video", "caption", "na", ""}

# SCHEMA_SPEC.md §9 — exact ordered contract header per standard source type.
# index.csv must START with these columns in this order; extras follow.
CONTRACTS = {
    "packets": ["date", "title", "body", "meeting_type", "packet_kind",
                "source_url", "retrieved_date", "format", "extraction_method",
                "path"],
    "housing_plans": ["date", "title", "doc_type", "source_url", "retrieved_date",
                      "format", "extraction_method", "path", "pages", "repository",
                      "notes"],
    "ordinances": ["ordinance_no", "adoption_date", "date", "title", "source_url",
                   "retrieved_date", "format", "extraction_method", "path",
                   "land_use", "result", "matched_motion_date",
                   "matched_motion_no", "match_confidence"],
    "pmn_backfill": ["date", "year", "title", "slug", "body", "path", "source",
                     "source_url", "notice_url", "pmn_body_id", "pmn_file_id",
                     "retrieved_date", "format", "extraction_method"],
    "transcripts": ["date", "title", "body", "video_url", "video_id",
                    "caption_type", "source_url", "retrieved_date", "format",
                    "extraction_method", "path"],
    "campaign_finance": ["date", "candidate", "office", "election_year",
                         "filing_type", "reporting_period", "title", "source_url",
                         "retrieved_date", "format", "extraction_method", "path"],
}


def check(ds):
    problems, notes = [], []
    ok = lambda c: notes.append("  ok   " + c)

    if not os.path.isdir(ds):
        return [f"{ds}: not a directory"], []

    raw = os.path.join(ds, "raw")
    if os.path.isdir(raw):
        ok("raw/ exists")
    else:
        problems.append("raw/ missing (RETAIN EVERY RAW ORIGINAL)")

    avail = any(os.path.exists(os.path.join(ds, f))
                for f in ("AVAILABILITY.md", "unrecovered.csv"))

    idx = os.path.join(ds, "index.csv")
    rows = []
    if not os.path.exists(idx):
        problems.append("index.csv missing (MACHINE-READABLE PROVENANCE)")
    else:
        ok("index.csv exists")
        with open(idx, newline="") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            contract = CONTRACTS.get(os.path.basename(os.path.normpath(ds)))
            if contract:
                if header[:len(contract)] == contract:
                    ok("index.csv matches the SCHEMA_SPEC §9 contract header")
                else:
                    problems.append(
                        "index.csv does not START with the SCHEMA_SPEC §9 contract "
                        f"header for this source type; expected {contract}, "
                        f"got {header[:len(contract)]}")
            else:
                missing = [c for c in REQUIRED_COLS if c not in header]
                if missing:
                    problems.append(f"index.csv missing required columns: {missing}")
                else:
                    ok("index.csv has all required columns")
            rows = [r for r in reader if any((v or "").strip() for v in r.values())]

        for i, r in enumerate(rows, 1):
            if not (r.get("date") or "").strip():
                problems.append(f"index.csv row {i}: empty date")
            if not (r.get("source_url") or "").strip():
                problems.append(f"index.csv row {i}: empty source_url")
            fmt = (r.get("format") or "").strip().lower()
            if fmt not in FORMAT_VOCAB:
                problems.append(f"index.csv row {i}: format '{fmt}' not in {sorted(FORMAT_VOCAB)}")
            p = (r.get("path") or "").strip()
            if p:
                # path may be dataset-relative, city-root-relative (e.g. millcreek
                # packets retained under meeting_minutes/raw/), or repo-relative.
                cand = [os.path.join(ds, p), os.path.join(ds, os.path.basename(p))]
                city_root = os.path.abspath(os.path.join(ds, ".."))
                repo_root = os.path.abspath(os.path.join(ds, "..", ".."))
                cand.append(os.path.join(city_root, p))
                cand.append(os.path.join(repo_root, p))
                if not any(os.path.exists(c) for c in cand):
                    problems.append(f"index.csv row {i}: path not found on disk: {p}")

    if not rows:
        if avail:
            ok("empty index but AVAILABILITY.md/unrecovered.csv present (honest empty — valid)")
        else:
            problems.append("index.csv has 0 data rows AND no AVAILABILITY.md/unrecovered.csv "
                            "(GAPS ARE DATA — record what you checked)")

    raw_files = []
    if os.path.isdir(raw):
        raw_files = [f for f in os.listdir(raw) if not f.startswith("_") and not f.startswith(".")]
    if rows and not raw_files:
        if avail:
            ok("no raw files but AVAILABILITY.md explains (e.g. link-only source)")
        else:
            problems.append("index has rows but raw/ is empty (did you discard originals?)")

    return problems, notes


def main():
    dirs = sys.argv[1:]
    if not dirs:
        sys.exit(__doc__)
    failed = 0
    for ds in dirs:
        problems, notes = check(ds)
        print(f"\n=== {ds} ===")
        for n in notes:
            print(n)
        for p in problems:
            print("  FAIL " + p)
        if problems:
            failed += 1
        else:
            print("  PASS — dataset satisfies the non-negotiable rules")
    print()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
